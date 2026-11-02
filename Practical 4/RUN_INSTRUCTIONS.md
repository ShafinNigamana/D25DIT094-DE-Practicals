# How to Run Practical 4

## 1. Open Terminal
Navigate to Practical 4 directory:
```powershell
cd "c:\College Studies\SEM 5\DE\Github Practicals\Practical 4"
```

## 2. Generate Dataset (if not already present)
```powershell
python data/generate_dataset.py
```

## 3. Run ETL Pipeline
Execute Python-based in-memory transformation:
```powershell
python etl/etl_pipeline.py
```

## 4. Run ELT Pipeline
Execute raw load and DuckDB in-database SQL transformation:
```powershell
python elt/elt_pipeline.py
```

## 5. Run Performance Comparison Benchmark
Compare latency and throughput between ETL and ELT:
```powershell
python benchmark/compare_results.py
```

## 6. Run dbt Core Models and Tests
Execute dbt transformations and verify data tests in DuckDB:
```powershell
dbt run --project-dir dbt_project --profiles-dir dbt_project
dbt test --project-dir dbt_project --profiles-dir dbt_project
```

## 7. Verify Output
```powershell
dir output
dir results
```
- `output/etl_output.csv`
- `output/elt_output.csv`
- `results/performance_results.csv`

## 8. Screenshots to Capture
1. Output of `python benchmark/compare_results.py` (Performance comparison table).
2. Output of `dbt run --project-dir dbt_project --profiles-dir dbt_project`.
3. Output of `dbt test --project-dir dbt_project --profiles-dir dbt_project`.
