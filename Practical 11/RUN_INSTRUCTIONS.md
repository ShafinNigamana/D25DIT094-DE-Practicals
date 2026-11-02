# How to Run Practical 11

## 1. Open Terminal
Navigate to Practical 11 directory:
```powershell
cd "c:\College Studies\SEM 5\DE\Github Practicals\Practical 11"
```

## 2. Run Data Security and Reverse ETL Suite
This command automatically generates the synthetic analytics dataset (if missing), creates the SQLite database, establishes column masking and hashing, creates the analyst-safe view, executes the Reverse ETL operational sync, and performs automated RBAC access control verification:
```powershell
python security_and_reverse_etl.py
```

## 3. Verify Output Files
Check the exported results, database, and security audit log:
```powershell
dir results
dir logs
type logs\security_audit.log
type results\reverse_etl_crm_export.csv
```
You will find:
- `customer_analytics.db` (SQLite database with raw table, safe view, and operational CRM table)
- `results/reverse_etl_crm_export.csv`
- `logs/security_audit.log`

## 4. Screenshots to Capture
1. Terminal output of `python security_and_reverse_etl.py` showing Reverse ETL sync and `[PASS]` on security tests.
2. Contents of `logs/security_audit.log` showing role-based query audits and access denial events.
