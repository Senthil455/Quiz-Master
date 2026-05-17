"""
Run the SQL seed file against your local PostgreSQL database.
Usage:
  Activate your venv, then:
    python run_seed.py

You can override connection settings with environment variables:
  PG_HOST, PG_DB, PG_USER, PG_PASS

This script splits the seed file on semicolons and executes statements one-by-one.
If a statement fails it will be rolled back and the error printed.
"""

import os
import pathlib
import sys
import psycopg2

def main():
    base = pathlib.Path(__file__).parent
    seed_path = base / "seed_data.sql"
    if not seed_path.exists():
        print(f"seed file not found: {seed_path}")
        sys.exit(1)

    sql_text = seed_path.read_text(encoding='utf-8')

    database_url = os.environ.get("DATABASE_URL")

    conn = psycopg2.connect(
        database_url,
        sslmode="require"
    )
    cur = conn.cursor()

    # Naive split by semicolon. Works for simple SQL seed files.
    statements = [s.strip() for s in sql_text.split(';')]
    executed = 0
    for stmt in statements:
        if not stmt:
            continue
        try:
            cur.execute(stmt)
            conn.commit()
            executed += 1
            print(f"OK: executed statement (truncated): {stmt[:60].replace('\n',' ')}...")
        except Exception as e:
            print("ERROR executing statement:", e)
            print("Statement (truncated):", stmt[:200].replace('\n',' '))
            conn.rollback()

    cur.close()
    conn.close()
    print(f"Done. Executed {executed} statements from {seed_path.name}.")

if __name__ == '__main__':
    main()
