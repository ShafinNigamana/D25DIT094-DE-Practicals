"""
Performance Comparison and Analysis

Compares ETL vs ELT pipeline execution metrics.
"""

import sys
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).parent.parent


def derive_metrics(row):
    """Calculate derived pipeline metrics from a single measured execution record."""
    result = row.copy()

    total_time = pd.to_numeric(result.get("total_time_seconds"), errors="coerce")
    output_rows = pd.to_numeric(result.get("output_rows"), errors="coerce")

    if "latency_ms" not in result.index:
        result["latency_ms"] = total_time * 1000.0 if pd.notna(total_time) else None
    else:
        latency_value = pd.to_numeric(result.get("latency_ms"), errors="coerce")
        result["latency_ms"] = latency_value if pd.notna(latency_value) else (total_time * 1000.0 if pd.notna(total_time) else None)

    if "throughput_events_per_sec" not in result.index:
        result["throughput_events_per_sec"] = (output_rows / total_time) if pd.notna(total_time) and total_time > 0 else None
    else:
        throughput_value = pd.to_numeric(result.get("throughput_events_per_sec"), errors="coerce")
        if pd.notna(throughput_value):
            result["throughput_events_per_sec"] = throughput_value
        elif pd.notna(total_time) and pd.notna(output_rows) and total_time > 0:
            result["throughput_events_per_sec"] = output_rows / total_time
        else:
            result["throughput_events_per_sec"] = None

    return result


def main():
    """Load and compare performance results."""
    results_path = PROJECT_ROOT / "results" / "performance_results.csv"

    if not results_path.exists():
        print("✗ Results file not found. Run ETL and ELT pipelines first.")
        print(f"  Expected: {results_path}")
        sys.exit(1)

    results = pd.read_csv(results_path)
    if results.empty:
        print("✗ No results found in performance_results.csv")
        sys.exit(1)

    results = results.apply(derive_metrics, axis=1)

    print("\n" + "=" * 80)
    print("PIPELINE PERFORMANCE COMPARISON")
    print("=" * 80)

    etl_results = results[results["pipeline"] == "ETL"].sort_values("timestamp").tail(1)
    elt_results = results[results["pipeline"] == "ELT"].sort_values("timestamp").tail(1)

    if etl_results.empty or elt_results.empty:
        print("✗ Both ETL and ELT results must be available for comparison")
        sys.exit(1)

    etl = etl_results.iloc[0]
    elt = elt_results.iloc[0]

    print("\nETL PIPELINE (Extract -> Transform in Python -> Load)")
    print("-" * 80)
    print(f"  Input rows:                    {int(etl['input_rows']):>10}")
    print(f"  Output rows:                   {int(etl['output_rows']):>10}")
    if "extraction_time_seconds" in etl.index and pd.notna(etl["extraction_time_seconds"]):
        print(f"  Extraction time:               {etl['extraction_time_seconds']:>10.4f} seconds")
    if "transformation_time_seconds" in etl.index and pd.notna(etl["transformation_time_seconds"]):
        print(f"  Transformation time:           {etl['transformation_time_seconds']:>10.4f} seconds")
    if "load_time_seconds" in etl.index and pd.notna(etl["load_time_seconds"]):
        print(f"  Load time:                     {etl['load_time_seconds']:>10.4f} seconds")
    print(f"  Total time:                    {etl['total_time_seconds']:>10.4f} seconds")
    if pd.notna(etl.get("latency_ms")):
        print(f"  Latency:                       {etl['latency_ms']:>10.2f} ms")
    if pd.notna(etl.get("throughput_events_per_sec")):
        print(f"  Throughput:                    {etl['throughput_events_per_sec']:>10.2f} events/sec")

    print("\nELT PIPELINE (Extract -> Load -> Transform in SQL)")
    print("-" * 80)
    print(f"  Input rows:                    {int(elt['input_rows']):>10}")
    print(f"  Output rows:                   {int(elt['output_rows']):>10}")
    if "raw_load_time_seconds" in elt.index and pd.notna(elt["raw_load_time_seconds"]):
        print(f"  Raw load time:                 {elt['raw_load_time_seconds']:>10.4f} seconds")
    if "transformation_time_seconds" in elt.index and pd.notna(elt["transformation_time_seconds"]):
        print(f"  SQL transformation time:       {elt['transformation_time_seconds']:>10.4f} seconds")
    print(f"  Total time:                    {elt['total_time_seconds']:>10.4f} seconds")
    if pd.notna(elt.get("latency_ms")):
        print(f"  Latency:                       {elt['latency_ms']:>10.2f} ms")
    if pd.notna(elt.get("throughput_events_per_sec")):
        print(f"  Throughput:                    {elt['throughput_events_per_sec']:>10.2f} events/sec")

    print("\n" + "=" * 80)
    print("ANALYSIS")
    print("=" * 80)

    etl_total = pd.to_numeric(etl["total_time_seconds"], errors="coerce")
    elt_total = pd.to_numeric(elt["total_time_seconds"], errors="coerce")

    if pd.notna(etl_total) and pd.notna(elt_total) and etl_total > 0 and elt_total > 0:
        if etl_total > elt_total:
            speedup = etl_total / elt_total
            print(f"\n[OK] ELT was {speedup:.2f}x faster than ETL in this local experiment")
            print(f"  ELT total:  {elt_total:.4f}s")
            print(f"  ETL total:  {etl_total:.4f}s")
            print(f"  Difference: {abs(etl_total - elt_total):.4f}s")
        elif elt_total > etl_total:
            slowdown = elt_total / etl_total
            print(f"\n[OK] ETL was {slowdown:.2f}x faster than ELT in this local experiment")
            print(f"  ETL total:  {etl_total:.4f}s")
            print(f"  ELT total:  {elt_total:.4f}s")
            print(f"  Difference: {abs(etl_total - elt_total):.4f}s")
        else:
            print(f"\n[OK] Both pipelines performed similarly")
            print(f"  ETL total:  {etl_total:.4f}s")
            print(f"  ELT total:  {elt_total:.4f}s")

    etl_transform = pd.to_numeric(etl.get("transformation_time_seconds", 0), errors="coerce")
    elt_transform = pd.to_numeric(elt.get("transformation_time_seconds", 0), errors="coerce")

    if pd.notna(etl_transform) and pd.notna(elt_transform) and etl_transform > 0 and elt_transform > 0:
        print(f"\nTransformation Time Comparison:")
        print(f"  ETL (Pandas): {etl_transform:.4f}s")
        print(f"  ELT (SQL):    {elt_transform:.4f}s")
        if etl_transform > elt_transform:
            print(f"  -> SQL transformation was faster by {etl_transform - elt_transform:.4f}s")
        else:
            print(f"  -> Pandas transformation was faster by {elt_transform - etl_transform:.4f}s")

    if int(etl["output_rows"]) == int(elt["output_rows"]):
        print(f"\n[OK] Both pipelines produced identical output row count: {int(etl['output_rows'])}")
    else:
        print(f"\n[FAIL] Row count mismatch: ETL={int(etl['output_rows'])}, ELT={int(elt['output_rows'])}")

    print("\n" + "=" * 80)
    print("KEY INSIGHTS")
    print("=" * 80)

    print("""
1. TRANSFORMATION LOCATION:
   - ETL: Transformations occur in Python/Pandas (application layer)
   - ELT: Transformations occur in DuckDB SQL (storage layer)

2. PERFORMANCE METRICS:
   - Latency = total pipeline execution time for the tested dataset
   - Latency is reported in milliseconds for end-to-end execution latency
   - Throughput = output_rows / total_time_seconds
   - Throughput is reported as events per second

3. DATA LINEAGE:
   - ETL: Transformed data replaces raw data
   - ELT: Raw staging table preserved for full lineage visibility

4. RECOVERY FROM BUGS:
   - ETL: Must re-extract and re-transform from raw CSV
   - ELT: Can rerun SQL transformations on preserved staging data

5. NETWORK COSTS (in cloud):
   - ETL: All transformation data must traverse application-to-database network
   - ELT: Only final results traverse network (reduced data movement)

6. SCALABILITY:
   - ETL: Limited by application memory
   - ELT: Leverages database engine capabilities for large datasets

7. MAINTENANCE:
   - ETL: Changes require code deployment
   - ELT: Changes can be made in SQL without application changes
""")

    print("=" * 80)
    print("\nFor detailed metrics, see: results/performance_results.csv")
    print("=" * 80)


if __name__ == "__main__":
    main()
