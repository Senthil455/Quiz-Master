import os
import pathlib
import psycopg2

base = pathlib.Path(__file__).parent
schema_path = base / "schema.sql"

sql = schema_path.read_text(encoding="utf-8")

database_url = os.environ.get("DATABASE_URL")

conn = psycopg2.connect(
    database_url,
    sslmode="require"
)

cur = conn.cursor()

cur.execute(sql)

conn.commit()

cur.close()
conn.close()

print("Schema created successfully.")