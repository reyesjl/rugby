# Copyright (c) 2025 Biasware LLC
# Proprietary and Confidential. All Rights Reserved.
# This file is the sole property of Biasware LLC.
# Unauthorized use, distribution, or reverse engineering is prohibited.

"""Database administration script (bootstrap + purge) for the vector videos DB.

Renamed from createdb.py per ticket: adds richer CLI and purge support.

Actions:
    purge (default):     Remove schema objects (table + dependent indexes) ONLY.
    bootstrap:           Ensure database objects (extension, table, indexes) exist.

Purging strategy (scope=schema):
  * Drops `videos` table (cascades dependent indexes) if present.
  * Does NOT drop or recreate the database itself.
  * Optional --recreate flag immediately re-runs bootstrap after purge.

Safety:
    * THIS DEFAULT IS DESTRUCTIVE: running with no arguments purges the schema.
    * Use --action bootstrap to create/restore schema.
    * Dry-run always shows intended actions w/o changes.

Env configuration identical to legacy script (DB_* vars, EMBED_DIM, etc.).
Exit codes: 0 success, 1 unexpected error, 2 dimension mismatch abort.
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
from psycopg.errors import DuplicateDatabase, InsufficientPrivilege, UndefinedObject

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DB_USER: str = os.getenv("DB_USER", "postgres")
DB_PASS: str = os.getenv("DB_PASS", "postgres")
DB_NAME: str = os.getenv("DB_NAME", "videos_db")
DB_HOST: str = os.getenv("DB_HOST", "127.0.0.1")
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

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(levelname)s %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger("db_admin")

_VECTOR_DIM_RE = re.compile(r"vector\((\d+)\)")


def connect(dbname: str) -> psycopg.Connection:
    return psycopg.connect(
        dbname=dbname,
        user=DB_USER,
        password=DB_PASS,
        host=DB_HOST,
        port=DB_PORT,
        options="-c client_min_messages=WARNING -c application_name=db_admin",
    )


def ensure_database(db_name: str, dry_run: bool) -> None:
    """Create target database if missing (idempotent)."""
    with connect("postgres") as conn, conn.cursor() as cur:
        conn.autocommit = True
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


def _get_existing_embed_dim(cur: psycopg.Cursor[Any]) -> int | None:
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


def _existing_ivfflat_index_def(cur: psycopg.Cursor[Any]) -> str | None:
    cur.execute(
        """
        SELECT indexdef FROM pg_indexes
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


def ensure_schema(db_name: str, dry_run: bool) -> None:
    """Ensure extension, table, unique index, ivfflat index."""
    with connect(db_name) as conn, conn.cursor() as cur:
        conn.autocommit = True
        try:
            cur.execute("SELECT pg_advisory_lock(hashtext('videos_schema_bootstrap'));")
        except Exception as e:  # pragma: no cover
            log.warning("failed to acquire advisory lock: %s", e)

        # extension
        try:
            if dry_run:
                log.info("(dry-run) would ensure extension: vector")
            else:
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        except InsufficientPrivilege:
            log.warning("privilege issue creating extension vector")
        except Exception as e:  # pragma: no cover
            log.warning("could not create/verify vector extension: %s", e)

        existing_dim = _get_existing_embed_dim(cur)
        if existing_dim is not None and existing_dim != EMBED_DIM:
            log.error(
                "embedding dim mismatch (existing=%s env=%s)", existing_dim, EMBED_DIM
            )
            raise SystemExit(2)

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
            log.info("(dry-run) would ensure table: videos VECTOR(%d)", EMBED_DIM)
        else:
            cur.execute(table_sql)

        if dry_run:
            log.info("(dry-run) would ensure unique index: videos_path_key")
        else:
            cur.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS videos_path_key ON videos (path);"
            )

        # ivfflat
        try:
            existing = _existing_ivfflat_index_def(cur)
            rebuild = existing is None or (
                IVFFLAT_REBUILD and existing and _needs_rebuild(existing)
            )
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
                log.info("ivfflat index unchanged")
            if not dry_run:
                cur.execute("ANALYZE videos;")
        except UndefinedObject:
            log.warning("ivfflat ops class not found; is pgvector installed?")
        except Exception as e:  # pragma: no cover
            log.warning("ivfflat index issue: %s", e)

        log.info("schema ready")


def purge_schema(db_name: str, dry_run: bool) -> None:
    """Drop videos table (and dependent indexes) if present."""
    with connect(db_name) as conn, conn.cursor() as cur:
        conn.autocommit = True
        cur.execute(
            """
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = current_schema() AND table_name = 'videos';
            """
        )
        exists = cur.fetchone() is not None
        if not exists:
            log.info("videos table absent (nothing to purge)")
            return
        if dry_run:
            log.info("(dry-run) would DROP TABLE videos CASCADE")
            return
        cur.execute("DROP TABLE videos CASCADE;")
        log.info("dropped table videos")


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Database admin: purge (default, destructive) or bootstrap schema"
    )
    p.add_argument(
        "--action",
        choices=["bootstrap", "purge"],
        default="purge",
        help="Action to perform (default: purge)",
    )
    p.add_argument("--dry-run", action="store_true", help="Show intended actions only")
    p.add_argument(
        "--recreate",
        action="store_true",
        help="After purge, run bootstrap (ignored if action!=purge)",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    dry_run: bool = args.dry_run
    action: str = args.action
    try:
        ensure_database(DB_NAME, dry_run=dry_run)
        if action == "purge":
            log.warning(
                "Executing PURGE (schema drop). Use --action bootstrap to create schema instead."
            )
            purge_schema(DB_NAME, dry_run=dry_run)
            if args.recreate:
                ensure_schema(DB_NAME, dry_run=dry_run)
        else:  # bootstrap
            ensure_schema(DB_NAME, dry_run=dry_run)
        return 0
    except SystemExit as se:  # dimension mismatch
        return int(se.code) if se.code is not None else 2
    except Exception as e:  # pragma: no cover
        log.exception("db-admin-error: %s", e)
        return 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
