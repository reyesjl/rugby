# Copyright (c) 2025 Biasware LLC
# Proprietary and Confidential. All Rights Reserved.
# This file is the sole property of Biasware LLC.
# Unauthorized use, distribution, or reverse engineering is prohibited.

import psycopg

# ----------------------------
# 1. Create database if not exists
# ----------------------------
conn = psycopg.connect(dbname="postgres", user="postgres", password="postgres", host="localhost", autocommit=True)
cur = conn.cursor()

db_name = "videos_db"
cur.execute(f"SELECT 1 FROM pg_database WHERE datname='{db_name}';")
exists = cur.fetchone()

if not exists:
    cur.execute(f"CREATE DATABASE {db_name};")
    print(f"Database '{db_name}' created.")
else:
    print(f"Database '{db_name}' already exists.")

cur.close()
conn.close()

# ----------------------------
# 2. Connect to the target DB
# ----------------------------
conn = psycopg.connect(dbname=db_name, user="postgres", password="postgres", host="localhost", autocommit=True)
cur = conn.cursor()

# ----------------------------
# 3. Enable pgvector extension
# ----------------------------
cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")

# ----------------------------
# 4. Create table if not exists
# ----------------------------
#TODO: If we ever switch vector models, ensure the selected model is compatible with the size of the embedding
cur.execute("""
CREATE TABLE IF NOT EXISTS videos (
    id SERIAL PRIMARY KEY,
    summary TEXT NOT NULL,
    path TEXT NOT NULL,
    embedding VECTOR(384) NOT NULL
);
""")
print("Table 'videos' ready.")

cur.close()
conn.close()
