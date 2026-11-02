# How to Run Practical 2

## 1. Open Terminal
Navigate to the Practical 2 folder:
```powershell
cd "c:\College Studies\SEM 5\DE\Github Practicals\Practical 2"
```

## 2. Generate Synthetic Customer Data
Run the generator script to create raw data with deliberate quality issues:
```powershell
python generate_data.py
```

## 3. Profile the Dataset
Inspect column types, null values, and summary statistics:
```powershell
python profile.py
```

## 4. Run Validation and Quarantine
Execute the validation routine to separate bad records into quarantine and record warnings in logs:
```powershell
python validate.py
```

## 5. Load Clean Data into SQLite
Ingest the verified clean records into the SQLite database:
```powershell
python database.py
```

## 6. Verify Output Files
Check that all output files and logs exist:
```powershell
dir data
dir quarantine
dir logs
python -c "import sqlite3; conn = sqlite3.connect('customer.db'); print('Total clean records in DB:', conn.execute('SELECT COUNT(*) FROM customers').fetchone()[0]); conn.close()"
```

## 7. Screenshots to Capture
1. Output of `python profile.py` (Profiling statistics).
2. Output of `python validate.py` (Validation & Quarantine execution).
3. Contents of `logs/execution.log` (Audit trail).
4. SQLite table verification query.
