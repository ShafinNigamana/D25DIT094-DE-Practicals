# How to Run Practical 8

## 1. Open Terminal
Navigate to Practical 8 directory:
```powershell
cd "c:\College Studies\SEM 5\DE\Github Practicals\Practical 8"
```

## 2. Run Query Optimization Benchmark
This single command automatically generates the 500,000-row clickstream dataset (if not already present), loads it into DuckDB, extracts EXPLAIN execution plans, runs both baseline and optimized queries, asserts logical equivalence, and benchmarks the supplementary window function rewrite:
```powershell
python query_optimization.py
```

## 3. Verify Output Files
Check the benchmark table and generated execution plans:
```powershell
dir results
type results\optimization_benchmarks.csv
```
You will find:
- `results/optimization_benchmarks.csv`
- `results/workload1_baseline_plan.txt`
- `results/workload1_optimized_plan.txt`
- `results/supplementary_baseline_plan.txt`
- `results/supplementary_optimized_plan.txt`

## 4. Screenshots to Capture
1. Terminal output of `python query_optimization.py` showing generation, timings, speedup, and `[OK] Logical verification passed`.
2. Benchmark table output in terminal (`results/optimization_benchmarks.csv`).
