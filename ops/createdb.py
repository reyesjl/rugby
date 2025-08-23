# Copyright (c) 2025 Biasware LLC
# Proprietary and Confidential. All Rights Reserved.
# This file is the sole property of Biasware LLC.
# Unauthorized use, distribution, or reverse engineering is prohibited.

"""Bootstrap Postgres database + vector schema (idempotent).

Creates database (if missing), ensures pgvector extension, `videos` table, unique
path index, and an IVF_FLAT index (optionally rebuilt when parameters change).

Usage (default):
        python ops/createdb.py
Dry run / plan (no writes):
        python ops/createdb.py --dry-run

Environment variables:
        DB_USER / DB_PASS / DB_NAME / DB_HOST / DB_PORT
        EMBED_DIM            : dimension of pgvector embedding column (int > 0)
        VECTOR_OPS           : one of {vector_cosine_ops, vector_ip_ops, vector_l2_ops}
        IVFFLAT_LISTS        : desired list count for ivfflat index (tuning knob)
        IVFFLAT_REBUILD      : if "1", force rebuild ivfflat when params differ
        IVFFLAT_CONCURRENT   : if "1", build/rebuild ivfflat CONCURRENTLY
        LOG_LEVEL            : python logging level (default INFO)

Key behaviors / guarantees:
    * Idempotent: safe to re-run (will rebuild IVF only when requested & differing)
    * Advisory lock: prevents concurrent rebuild races (`videos_schema_bootstrap` key)
    * Dimension safety: aborts if existing embedding dimension != EMBED_DIM
    * Dry-run: reports intended actions without mutating state

Limitations:
    * Not a general migrations system; for evolving schema use Alembic.
    * Changing EMBED_DIM requires manual migration of data / column recreation.
"""

from __future__ import annotations

import argparse
import logging
import os
import re
import sys
from typing import Any

import psycopg
from dotenv import load_dotenv
from psycopg import sql
from psycopg.errors import (
    DuplicateDatabase,
    InsufficientPrivilege,
    UndefinedObject,
)

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration (loaded from env, command line toggles below)
# ---------------------------------------------------------------------------

# Configuration (validated below)
DB_USER: str = os.getenv("DB_USER", "postgres")
DB_PASS: str = os.getenv("DB_PASS", "postgres")
DB_NAME: str = os.getenv("DB_NAME", "videos_db")
DB_HOST: str = os.getenv("DB_HOST", "127.0.0.1")  # force TCP
DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
EMBED_DIM: int = int(os.getenv("EMBED_DIM", "384"))
DIST_OPS: str = os.getenv("VECTOR_OPS", "vector_cosine_ops")
IVFFLAT_LISTS: int = int(os.getenv("IVFFLAT_LISTS", "100"))
IVFFLAT_REBUILD: bool = os.getenv("IVFFLAT_REBUILD", "0") == "1"
IVFFLAT_CONCURRENT: bool = os.getenv("IVFFLAT_CONCURRENT", "0") == "1"
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()

DIST_OPS_ALLOWED = {"vector_cosine_ops", "vector_ip_ops", "vector_l2_ops"}
if DIST_OPS not in DIST_OPS_ALLOWED:
    DIST_OPS = "vector_cosine_ops"

if EMBED_DIM <= 0:
    EMBED_DIM = 384
if IVFFLAT_LISTS <= 0:
    IVFFLAT_LISTS = 100

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(levelname)s %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger("createdb")

_env_vector_ops = os.getenv("VECTOR_OPS")
if _env_vector_ops and _env_vector_ops not in DIST_OPS_ALLOWED:
    log.warning("VECTOR_OPS unrecognized; defaulted to vector_cosine_ops")
_env_embed_dim = os.getenv("EMBED_DIM")
if _env_embed_dim is not None:
    try:
        if int(_env_embed_dim) <= 0:
            log.warning("EMBED_DIM invalid; defaulted to 384")
    except ValueError:
        log.warning("EMBED_DIM non-integer; defaulted to 384")
_env_lists = os.getenv("IVFFLAT_LISTS")
if _env_lists is not None:
    try:
        if int(_env_lists) <= 0:
            log.warning("IVFFLAT_LISTS invalid; defaulted to 100")
    except ValueError:
        log.warning("IVFFLAT_LISTS non-integer; defaulted to 100")


def connect(dbname: str) -> psycopg.Connection:
    """Return a new psycopg connection with lowered client message verbosity."""
    return psycopg.connect(
        dbname=dbname,
        user=DB_USER,
        password=DB_PASS,
        host=DB_HOST,
        port=DB_PORT,
        options="-c client_min_messages=WARNING -c application_name=createdb_bootstrap",
    )


def ensure_database(db_name: str, dry_run: bool) -> None:
    """Create the target database if it does not already exist."""
    with connect("postgres") as conn, conn.cursor() as cur:
        conn.autocommit = True  # CREATE DATABASE must be outside a transaction
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s;", (db_name,))
        if cur.fetchone():
            log.info("database exists: %s", db_name)
            return
        if dry_run:
            log.info("(dry-run) would create database: %s", db_name)
            return
        try:
            cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name)))
            log.info("created database: %s", db_name)
        except DuplicateDatabase:
            log.info("database exists (race): %s", db_name)


def _existing_ivfflat_index_def(cur: psycopg.Cursor[Any]) -> str | None:
    cur.execute(
        """
        SELECT indexdef
        FROM pg_indexes
        WHERE schemaname = current_schema()
          AND tablename = 'videos'
          AND indexname = 'videos_embedding_ivfflat';
        """
    )
    row = cur.fetchone()
    return row[0] if row else None


def _needs_rebuild(indexdef: str) -> bool:
    if f"(embedding {DIST_OPS})" not in indexdef:
        return True
    if f"lists = {IVFFLAT_LISTS}" not in indexdef:
        return True
    return False


_VECTOR_DIM_RE = re.compile(r"vector\((\d+)\)")


def _get_existing_embed_dim(cur: psycopg.Cursor[Any]) -> int | None:
    """Return existing embedding dimension if table+column exist, else None."""
    cur.execute(
        """
        SELECT pg_catalog.format_type(a.atttypid, a.atttypmod)
        FROM pg_attribute a
        JOIN pg_class c ON a.attrelid = c.oid
        JOIN pg_namespace n ON c.relnamespace = n.oid
        WHERE c.relname = 'videos'
          AND a.attname = 'embedding'
          AND a.attnum > 0
          AND NOT a.attisdropped;
        """
    )
    row = cur.fetchone()
    if not row:
        return None
    m = _VECTOR_DIM_RE.search(row[0])
    return int(m.group(1)) if m else None


def ensure_schema(db_name: str, dry_run: bool) -> None:
    """Ensure extension, table, unique + vector indexes exist (with optional ivfflat tuning)."""
    with connect(db_name) as conn, conn.cursor() as cur:
        conn.autocommit = True

        # Acquire advisory lock (prevents concurrent rebuild races).
        try:
            cur.execute("SELECT pg_advisory_lock(hashtext('videos_schema_bootstrap'));")
        except Exception as e:  # lock failures are rare; proceed w/o lock if needed
            log.warning("failed to acquire advisory lock: %s", e)

        # 1) pgvector extension
        try:
            if dry_run:
                log.info("(dry-run) would ensure extension: vector")
            else:
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        except InsufficientPrivilege:
            log.warning(
                "insufficient privilege to CREATE EXTENSION vector; ensure superuser installed it"
            )
        except Exception as e:  # Could be: extension not found
            log.warning("could not create/verify vector extension: %s", e)

        # Detect existing dim if table exists
        existing_dim = _get_existing_embed_dim(cur)
        if existing_dim is not None and existing_dim != EMBED_DIM:
            log.error(
                "embedding dimension mismatch (existing=%s env=%s) - aborting (manual migration required)",
                existing_dim,
                EMBED_DIM,
            )
            raise SystemExit(2)

        # 2) videos table
        table_sql = sql.SQL(
            """
            CREATE TABLE IF NOT EXISTS videos (
                id BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
                summary TEXT NOT NULL,
                path TEXT NOT NULL,
                embedding {embed_type} NOT NULL
            );
            """
        ).format(embed_type=sql.SQL("VECTOR({})").format(sql.Literal(EMBED_DIM)))
        if dry_run:
            log.info("(dry-run) would ensure table: videos (VECTOR(%d))", EMBED_DIM)
        else:
            cur.execute(table_sql)

        # Unique path (fast exact lookup)
        if dry_run:
            log.info("(dry-run) would ensure unique index: videos_path_key (path)")
        else:
            cur.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS videos_path_key ON videos (path);"
            )

        # 3) ivfflat index management
        try:
            existing = _existing_ivfflat_index_def(cur)
            rebuild = False
            if existing is None:
                rebuild = True
            else:
                if IVFFLAT_REBUILD and _needs_rebuild(existing):
                    rebuild = True
            if rebuild:
                action = "rebuilt" if existing else "created"
                if dry_run:
                    log.info(
                        "(dry-run) would %s ivfflat index (ops=%s, lists=%d, concurrent=%s)",
                        action,
                        DIST_OPS,
                        IVFFLAT_LISTS,
                        IVFFLAT_CONCURRENT,
                    )
                else:
                    if existing:
                        cur.execute("DROP INDEX videos_embedding_ivfflat;")
                    concurrent_clause = (
                        sql.SQL(" CONCURRENTLY") if IVFFLAT_CONCURRENT else sql.SQL("")
                    )
                    cur.execute(
                        sql.SQL(
                            """
                            CREATE INDEX{concurrent} videos_embedding_ivfflat
                            ON videos USING ivfflat (embedding {ops})
                            WITH (lists = {lists});
                            """
                        ).format(
                            concurrent=concurrent_clause,
                            ops=sql.Identifier(DIST_OPS),
                            lists=sql.Literal(IVFFLAT_LISTS),
                        )
                    )
                    log.info(
                        "ivfflat index %s (ops=%s, lists=%d, concurrent=%s)",
                        action,
                        DIST_OPS,
                        IVFFLAT_LISTS,
                        IVFFLAT_CONCURRENT,
                    )
            else:
                log.info(
                    "ivfflat index unchanged (IVFFLAT_REBUILD unset or params unchanged)"
                )
                if existing:
                    log.debug("existing indexdef: %s", existing)

            if not dry_run:
                # Keep planner stats fresh (cheap for small tables; adjust if huge)
                cur.execute("ANALYZE videos;")
        except UndefinedObject:
            log.warning("ivfflat ops class not found; is pgvector installed & recent?")
        except Exception as e:
            log.warning("ivfflat index issue: %s", e)

        log.info("schema ready: videos (+vector, ivfflat if available)")


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Bootstrap Postgres vector schema")
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Show intended actions without making changes",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    dry_run = args.dry_run
    try:
        ensure_database(DB_NAME, dry_run=dry_run)
        ensure_schema(DB_NAME, dry_run=dry_run)
        return 0
    except SystemExit as se:  # re-raise explicit aborts (dimension mismatch)
        return int(se.code) if se.code is not None else 2
    except Exception as e:
        log.exception("bootstrap-error: %s", e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
