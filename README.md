# Rugby Pipeline

A comprehensive Python-based video processing system designed for rugby video analysis and content management.
The pipeline provides end-to-end capabilities for video ingestion, format conversion, AI-powered transcription and indexing, and searchable content generation.

---

## Features

- **Video Ingestion**
  Automated discovery of video files from multiple source types (Linux desktop, Windows desktop, network hosts).
  _Source: `pipeline_models.py:44-49`_

- **Format Conversion**
  Standardization to MP4 format using FFmpeg with configurable quality settings.
  _Source: `pipeline_models.py:112-141`_

- **AI-Powered Indexing**
  Content analysis using OpenAI models for searchable metadata generation.
  _Source: `pipeline_models.py:169-178`_

- **Type-Safe Configuration**
  YAML-based pipeline configuration with Python model validation.
  _Source: `pipeline_models.py:220-234`_

---

## Quick Start

### Installation
```bash
pip install -e .
```

### Postgres & Vector Setup

This project uses PostgreSQL 17 + the `pgvector` extension for embedding similarity search.

#### 1. Install PostgreSQL + pgvector (Ubuntu / Debian)
```bash
sudo /usr/share/postgresql-common/pgdg/apt.postgresql.org.sh   # if not already added
sudo apt update
sudo apt install -y postgresql-17 postgresql-contrib-17 postgresql-17-pgvector postgresql-server-dev-17
```

Ensure cluster is running on port 5432 (adjust if you prefer another port):
```bash
sudo pg_createcluster 17 main --start   # if a 17 cluster not present
pg_lsclusters                            # verify status
```
If you must change the port: edit `/etc/postgresql/17/main/postgresql.conf` (set `port = 5432`) then:
```bash
sudo systemctl restart postgresql
```

#### 2. (Once) Adjust local auth if password login for superuser fails
If you see: `FATAL: password authentication failed for user "postgres"` you may need to switch peer → md5:
```bash
sudo vim /etc/postgresql/17/main/pg_hba.conf
# change:
#   local   all   postgres   peer
# to:
#   local   all   postgres   md5
sudo pg_ctlcluster 17 main restart
sudo -u postgres psql -c '\password postgres'  # set a strong password
```

#### 3. Create your application `.env`
Start from the example (this file contains NO secrets):
```bash
cp .env.example .env
```
Edit `.env` and set a strong random value for `DB_PASS` (do not commit it). The important variables:

| Variable | Purpose |
|----------|---------|
| DB_USER | Application role (non-superuser) |
| DB_PASS | Role password (secret) |
| DB_NAME | Target database name (default `videos_db`) |
| EMBED_DIM | Embedding vector dimension (must match your model) |
| VECTOR_OPS | Distance opclass: `vector_cosine_ops` (default) / `vector_l2_ops` / `vector_ip_ops` |
| IVFFLAT_LISTS | IVF_FLAT index list count (tuning knob) |
| IVFFLAT_REBUILD | Set `1` to force rebuild when params differ |
| IVFFLAT_CONCURRENT | Set `1` to build index CONCURRENTLY (less locking) |

#### 4. Bootstrap the application role (run as superuser, first time only)
Run the SQL script using `psql` variables to avoid hard‑coding secrets:
```bash
export $(grep -E '^(DB_USER|DB_PASS)=' .env | sed 's/#.*//' | xargs)
psql -h 127.0.0.1 -U postgres -d postgres \
   -v app_role="$DB_USER" -v app_pass="$DB_PASS" -v allow_createdb=1 \
   -f ops/bootstrap_role.sql
```
You can later revoke the ability for this role to create databases (after initial bootstrap):
```sql
ALTER ROLE rugby_app NOCREATEDB;
```

#### 5. Bootstrap / verify the database & schema
Use the Python script (idempotent). First do a dry run:
```bash
python ops/createdb.py --dry-run
```
If the plan looks correct, run without `--dry-run`:
```bash
python ops/createdb.py
```
What it does:
1. Creates database if missing (while role still has CREATEDB).
2. Ensures `pgvector` extension.
3. Creates `videos` table with `VECTOR(EMBED_DIM)` column.
4. Creates unique index on `path`.
5. Creates or (optionally) rebuilds IVF_FLAT index (`videos_embedding_ivfflat`).

#### 6. Tuning / rebuilding the IVF_FLAT index
Change lists or operator class, then:
```bash
IVFFLAT_REBUILD=1 IVFFLAT_LISTS=200 python ops/createdb.py
# or change distance metric
VECTOR_OPS=vector_l2_ops IVFFLAT_REBUILD=1 python ops/createdb.py
```
Consider `IVFFLAT_CONCURRENT=1` if the table grows large and you need reduced locking.

#### 7. Post-initial hardening
After the database exists and the index is built:
```sql
ALTER ROLE rugby_app NOCREATEDB;
```
Rotate the password if it was ever shared insecurely.

#### 8. Common troubleshooting
| Issue | Fix |
|-------|-----|
| `permission denied to create extension "vector"` | Install extension as superuser: `CREATE EXTENSION vector;` then rerun script |
| Dimension mismatch error | You changed `EMBED_DIM`; manual migration needed (create new column / table) |
| Want to see actions only | Use `--dry-run` |

#### 9. Partner developer onboarding quick checklist
1. Install Python + clone repo.
2. Create virtual env & install deps: `pip install -e .[dev]`.
3. Copy `.env.example` → `.env`, set `DB_PASS`.
4. Run role bootstrap (only if role not present).
5. `python ops/createdb.py --dry-run` then real run.
6. Insert a test row (optional):
   ```bash
   python - <<'PY'
   import os, psycopg
   conn = psycopg.connect(dbname=os.getenv('DB_NAME'), user=os.getenv('DB_USER'), password=os.getenv('DB_PASS'), host=os.getenv('DB_HOST'), port=os.getenv('DB_PORT'))
   with conn, conn.cursor() as cur:
     cur.execute("INSERT INTO videos(summary,path,embedding) VALUES(%s,%s,%s)", ("test","/tmp/demo.mp4","["+",".join(["0"]*int(os.getenv('EMBED_DIM','384')))+"]"))
   print("Inserted demo row.")
   PY
   ```
7. Run tests: `python ops/run_tests.py`.
8. Start building pipeline configs / running CLI.

---




### Basic Usage
Create a pipeline configuration file (e.g., `pipeline.yaml`):

```yaml
video_processing:
  sources:
    - type: "linux_desktop"
      path: "/path/to/videos"
      watch_patterns: ["mp4", "mpg"]
  conversion:
    ffmpeg:
      video_codec: "libx264"
      crf: 23
      preset: "fast"
    parallel_workers: 1
  indexing:
    ai_provider: "openai"
    model: "gpt-4o-mini"
    batch_size: 10
```

Run the pipeline:

```bash
rugby-cli --config pipeline.yaml
```

---

## CLI Commands

- `rugby-cli --config <path>` → Execute a configured video processing pipeline (`cli.py:19-23`)
- `rugby-cli --version` → Display version information (`cli.py:24-28`)
- `rugby-cli --status` → Show pipeline status and readiness (`cli.py:29-33`)

---

## Architecture

The system follows a modular architecture with clear separation of concerns:

```
rugby/
├── core/           # Core pipeline logic and CLI
├── ingest/         # Video file discovery
├── convert/        # Video conversion utilities
├── indexing/       # Video indexing and search
├── api/            # API endpoints and web interface
├── ops/            # Operations and DevOps utilities
└── storage/        # Data storage and persistence
```

---

## Configuration

The pipeline uses type-safe configuration models that support:

- **Video Sources**
  Multiple source types with configurable watch patterns
  _(`pipeline_models.py:52-80`)_

- **Conversion Settings**
  FFmpeg parameters and parallel processing options
  _(`pipeline_models.py:143-164`)_

- **AI Indexing**
  Provider settings, model selection, and prompt configuration
  _(`pipeline_models.py:169-215`)_

---

## Development

### Requirements
- Python 3.9+ (`pyproject.toml:10`)
- FFmpeg (for video conversion)
- OpenAI API key (for indexing)

### Setup
```bash
# Install with development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests
python ops/run_tests.py

# Code formatting and linting
ruff check .
ruff format .
mypy .
```

### Development Tools
Defined in `pyproject.toml:30-36`:

- **pytest** → Testing framework
- **ruff** → Code formatting and linting
- **mypy** → Static type checking
- **pre-commit** → Git hooks for code quality

---

## Project History

This project evolved from a collection of shell scripts and Python utilities in the `/scripts` directory that handled video ingestion, conversion, and indexing tasks.

The current implementation provides a **unified, type-safe pipeline** with proper configuration management and a CLI interface—replacing the previous ad-hoc script-based approach while maintaining compatibility with existing video processing workflows.

---

## License
This software is proprietary and the sole property of Biasware LLC.
Copyright (c) 2025 Biasware LLC. All rights reserved.

Use of this software is governed by the Biasware LLC Proprietary License.
Unauthorized copying, modification, distribution, or reverse engineering is strictly prohibited.

For licensing inquiries, contact: contact@biasware.com
