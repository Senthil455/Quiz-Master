Quick run instructions for EduTrack

1) Activate (or create) the virtual environment

PowerShell (recommended if using the included .venv):

```powershell
cd C:\Users\senth\Downloads\Projects\EduTrack\PythonProject
.\.venv\Scripts\Activate.ps1
```

If you don't have a venv yet:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2) Install dependencies

```powershell
pip install -r requirements.txt
```

3) Load seed data

If you have `psql` available (replace path if necessary):

```powershell
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -h localhost -U postgres -d quizdb -f "C:\Users\senth\Downloads\Projects\EduTrack\PythonProject\seed_data.sql"
```

Or use the included Python runner (uses connection env vars or defaults):

```powershell
# optional: override creds via env vars
$env:PG_PASS = '4321'
python run_seed.py
```

4) Run the app

```powershell
python app.py
```

5) Open in browser

http://127.0.0.1:5000/

Notes:
- If any INSERT fails, open `seed_data.sql` and compare column names with your DB schema.
- You can set `PG_HOST`, `PG_DB`, `PG_USER`, `PG_PASS` env vars to change DB connection.
