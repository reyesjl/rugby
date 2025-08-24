-- bootstrap_role.sql
-- Purpose: One-time creation (or idempotent ensure) of the application role used by
--          ops/createdb.py. Run this as a superuser (e.g. postgres). The Python
--          script will handle creating the database/schema/table/indexes.
--
-- Usage:
--   psql -h 127.0.0.1 -U postgres -d postgres -f ops/bootstrap_role.sql
--
-- After the database is created the first time, you may wish to revoke CREATEDB
-- from the role (ALTER ROLE rugby_app NOCREATEDB;) for least privilege.
--
-- IMPORTANT: Prefer passing role & password via psql variables so this file
--            contains no secrets. Examples:
--
--   # Load env vars (ensure DB_USER / DB_PASS exported securely)
--   export $(grep -E '^(DB_USER|DB_PASS)=' .env | sed 's/#.*//' | xargs)
--   psql -h 127.0.0.1 -U postgres -d postgres \
--        -v app_role="$DB_USER" -v app_pass="$DB_PASS" \
--        -v allow_createdb=1 \
--        -f ops/bootstrap_role.sql
--
-- Variables (psql -v):
--   app_role        : target role/user name (default rugby_app)
--   app_pass        : password (required if creating)
--   allow_createdb  : 1 (default) grants CREATEDB temporarily; 0 for none
--
-- After first database bootstrap you can tighten privileges:
--   ALTER ROLE <role> NOCREATEDB;
--
-- If you prefer to keep a literal password here (NOT recommended), revert to the
-- earlier static version and replace REPLACE_WITH_STRONG_SECRET before running.

-- Default app_role if not provided
\if :{?app_role}
\else
\set app_role rugby_app
\endif

-- Default allow_createdb if not provided
\if :{?allow_createdb}
\else
\set allow_createdb 1
\endif

-- Require app_pass (can't sensibly default a secret)
\if :{?app_pass}
\else
\echo 'ERROR: app_pass variable must be supplied (use -v app_pass=...)'
\quit 3
\endif

-- Echo chosen parameters (avoid printing password)
SELECT :'app_role' AS creating_role, :allow_createdb::int AS allow_createdb_flag;

-- Pass variables into the DO block via custom GUCs (safe lifetime for this session)
SET role.app_role TO :'app_role';
SET role.app_pass TO :'app_pass';
SET role.allow_createdb TO :allow_createdb;

DO $$
DECLARE
    v_role text := current_setting('role.app_role');
    v_pass text := current_setting('role.app_pass');
    v_allow_createdb int := current_setting('role.allow_createdb')::int;
    v_createdb_clause text := CASE WHEN v_allow_createdb = 1 THEN 'CREATEDB' ELSE 'NOCREATEDB' END;
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = v_role) THEN
        EXECUTE format(
            'CREATE ROLE %I LOGIN PASSWORD %L NOSUPERUSER %s NOCREATEROLE NOREPLICATION CONNECTION LIMIT 50',
            v_role, v_pass, v_createdb_clause
        );
        RAISE NOTICE 'Created role % (clause=%)', v_role, v_createdb_clause;
    ELSE
        RAISE NOTICE 'Role % already exists (not modified)', v_role;
    END IF;
END
$$;

-- Optional: After first successful bootstrap (DB created), lock down privileges:
--   ALTER ROLE :app_role NOCREATEDB;
-- (Only run the above AFTER the database exists.)
