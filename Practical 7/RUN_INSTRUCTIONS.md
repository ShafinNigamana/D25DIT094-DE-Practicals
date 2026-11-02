# How to Run Practical 7

## 1. MANUAL SETUP: Start PostgreSQL
PostgreSQL is required for Practical 7. You can run it either via Docker (recommended) or using your local PostgreSQL service:

### Option A: Using Docker (Recommended)
Make sure Docker Desktop is started, then run:
```powershell
docker run -d --name de-postgres -p 5432:5432 -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=postgres postgres:15
```

### Option B: Using Local Windows PostgreSQL Service
If using your installed local PostgreSQL service, set your password environment variable before running:
```powershell
$env:PG_PASS = "your_postgres_password"
```

## 2. Open Terminal
Navigate to the Practical 7 directory:
```powershell
cd "c:\College Studies\SEM 5\DE\Github Practicals\Practical 7"
```

## 3. Run the CDC Pipeline
This command initializes the tables and PL/pgSQL triggers, generates INSERT/UPDATE/DELETE mutations, captures them into the CDC ledger, tests replication interruption and recovery, verifies version deduplication for out-of-order events, and asserts operational vs analytical consistency:
```powershell
python cdc_pipeline.py
```

## 4. Verify Output Files
```powershell
dir results
type results\analytical_replicated_state.csv
type results\cdc_ledger_history.csv
```
You will find:
- `results/cdc_ledger_history.csv` (Full audit trail of mutations)
- `results/analytical_replicated_state.csv` (Verified replicated destination table)

## 5. Screenshots to Capture
1. Terminal output of `python cdc_pipeline.py` showing mutations captured in CDC ledger.
2. Terminal output showing simulated crash interruption and recovery.
3. Terminal output showing `[PASS] Version protection verified` (out-of-order test).
4. Terminal output showing `[OK] Verification Success: Operational and Analytical tables are 100% IDENTICAL`.
