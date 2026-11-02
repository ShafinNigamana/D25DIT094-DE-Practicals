# How to Run Practical 9

## 1. Open Terminal
Navigate to Practical 9 directory:
```powershell
cd "c:\College Studies\SEM 5\DE\Github Practicals\Practical 9"
```

## 2. Run Data Modeling & Comparison Script
This command generates the raw transactions (if missing), builds the Kimball Star Schema and Snowflake Schema in DuckDB, runs analytical join queries, asserts logical equivalence, and exports ERD diagrams:
```powershell
python build_models.py
```

## 3. Verify Output Files
Check the exported schema comparisons and ERD files:
```powershell
dir results
dir sql
type results\schema_comparison.csv
```
You will find:
- `results/schema_comparison.csv`
- `results/star_schema_erd.md` (Mermaid ERD for Star Schema)
- `results/snowflake_schema_erd.md` (Mermaid ERD for Snowflake Schema)
- `sql/star_schema_ddl.sql`
- `sql/snowflake_schema_ddl.sql`

## 4. Screenshots to Capture
1. Terminal output of `python build_models.py` showing table counts and query comparison.
2. Contents of `results/schema_comparison.csv`.
3. ERD diagram preview of Star Schema (`results/star_schema_erd.md`).
