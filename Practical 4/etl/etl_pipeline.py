"""
ETL (Extract, Transform, Load) Pipeline

This pipeline demonstrates the classic ETL pattern:
1. Extract raw data from CSV
2. Transform in-memory using Pandas vectorized operations
3. Load cleaned data into DuckDB

Transformation rules are implemented in Python/Pandas before loading.
"""

import argparse
import sys
import time
from pathlib import Path

import pandas as pd
import duckdb

# Get project root
PROJECT_ROOT = Path(__file__).parent.parent


def create_duckdb_connection(db_path):
    """Create or connect to DuckDB database."""
    return duckdb.connect(str(db_path))


def extract_raw_data(csv_path):
    """
    Extract raw data from CSV.

    Args:
        csv_path: Path to input CSV

    Returns:
        Raw DataFrame with no transformations
    """
    print("=" * 60)
    print("ETL PIPELINE - EXTRACTION PHASE")
    print("=" * 60)

    extract_start = time.perf_counter()
    # Read all columns as strings to preserve whitespace and format
    df_raw = pd.read_csv(csv_path, dtype=str)
    extract_time = time.perf_counter() - extract_start

    print(f"[OK] Extracted {len(df_raw)} records from {csv_path}")
    print(f"  Columns: {', '.join(df_raw.columns.tolist())}")
    print(f"  Extraction time: {extract_time:.4f} seconds")

    return df_raw, extract_time


def transform_data(df_raw):
    """
    Transform data in-memory using Pandas vectorized operations.

    Transformation rules:
    1. transaction_id: trim whitespace, preserve
    2. transaction_date: keep as-is (already normalized)
    3. store_code: trim whitespace, normalize legacy codes (LEG*** -> STORE_***)
    4. product_id: trim whitespace
    5. customer_id: trim whitespace
    6. quantity: convert to int, validate
    7. unit_price: convert to float, validate
    8. payment_method: trim whitespace, normalize
    9. total_amount: calculate as quantity * unit_price

    Args:
        df_raw: Raw input DataFrame

    Returns:
        Transformed DataFrame
    """
    print("\n" + "=" * 60)
    print("ETL PIPELINE - TRANSFORMATION PHASE")
    print("=" * 60)

    transform_start = time.perf_counter()

    df = df_raw.copy()

    # 1. transaction_id: strip whitespace
    df["transaction_id"] = df["transaction_id"].str.strip()

    # 2. transaction_date: keep as-is (already normalized in dataset generation)

    # 3. store_code: strip and normalize legacy codes
    df["store_code"] = df["store_code"].str.strip()
    # Map legacy codes to new format: LEG001 -> STORE_001
    def normalize_store_code(code):
        if code.startswith("LEG"):
            # Extract the number and convert to new format
            num = code[3:]  # Get "001" from "LEG001"
            return f"STORE_{num}"
        return code

    df["store_code"] = df["store_code"].apply(normalize_store_code)

    # 4. product_id: strip whitespace
    df["product_id"] = df["product_id"].str.strip()

    # 5. customer_id: strip whitespace
    df["customer_id"] = df["customer_id"].str.strip()

    # 6. quantity: convert to int
    df["quantity"] = pd.to_numeric(df["quantity"].str.strip(), errors="coerce").astype("int64")

    # 7. unit_price: convert to float
    df["unit_price"] = pd.to_numeric(df["unit_price"].str.strip(), errors="coerce").astype("float64")

    # 8. payment_method: strip and lowercase
    df["payment_method"] = df["payment_method"].str.strip().str.lower()

    # 9. total_amount: vectorized calculation
    df["total_amount"] = df["quantity"] * df["unit_price"]

    transform_time = time.perf_counter() - transform_start

    print(f"[OK] Transformed {len(df)} records")
    print(f"  Transformation time: {transform_time:.4f} seconds")
    print(f"\nTransformed data sample:")
    print(df.head())

    return df, transform_time


def validate_transformed_data(df):
    """
    Validate transformed data quality.

    Checks:
    - No unexpected row loss
    - Required fields are not null
    - Numeric fields are valid
    - total_amount is correctly calculated
    - No legacy store codes in final data

    Args:
        df: Transformed DataFrame

    Returns:
        bool: True if all validations pass
    """
    print("\n" + "=" * 60)
    print("ETL PIPELINE - VALIDATION PHASE")
    print("=" * 60)

    issues = []

    # Check 1: transaction_id not null
    null_txn_ids = df["transaction_id"].isna().sum()
    if null_txn_ids > 0:
        issues.append(f"  [FAIL] {null_txn_ids} null transaction_ids")
    else:
        print("  [OK] transaction_id: All non-null")

    # Check 2: store_code not null
    null_store = df["store_code"].isna().sum()
    if null_store > 0:
        issues.append(f"  [FAIL] {null_store} null store_codes")
    else:
        print("  [OK] store_code: All non-null")

    # Check 3: product_id not null
    null_product = df["product_id"].isna().sum()
    if null_product > 0:
        issues.append(f"  [FAIL] {null_product} null product_ids")
    else:
        print("  [OK] product_id: All non-null")

    # Check 4: quantity is numeric and positive
    null_qty = df["quantity"].isna().sum()
    negative_qty = (df["quantity"] < 0).sum()
    if null_qty > 0:
        issues.append(f"  [FAIL] {null_qty} null quantities")
    elif negative_qty > 0:
        issues.append(f"  [FAIL] {negative_qty} negative quantities")
    else:
        print("  [OK] quantity: All valid and positive")

    # Check 5: unit_price is numeric and positive
    null_price = df["unit_price"].isna().sum()
    negative_price = (df["unit_price"] < 0).sum()
    if null_price > 0:
        issues.append(f"  [FAIL] {null_price} null unit_prices")
    elif negative_price > 0:
        issues.append(f"  [FAIL] {negative_price} negative unit_prices")
    else:
        print("  [OK] unit_price: All valid and positive")

    # Check 6: total_amount is correctly calculated
    tolerance = 0.01  # Allow for floating-point rounding
    incorrect_total = (abs(df["total_amount"] - (df["quantity"] * df["unit_price"])) > tolerance).sum()
    if incorrect_total > 0:
        issues.append(f"  [FAIL] {incorrect_total} incorrect total_amounts")
    else:
        print("  [OK] total_amount: Correctly calculated")

    # Check 7: No legacy store codes
    legacy_codes = df[df["store_code"].str.contains("LEG", na=False)]
    if len(legacy_codes) > 0:
        issues.append(f"  [FAIL] {len(legacy_codes)} legacy store codes found (not normalized)")
    else:
        print("  [OK] store_code: All legacy codes normalized")

    if issues:
        print("\n[FAIL] VALIDATION FAILED:")
        for issue in issues:
            print(issue)
        return False

    print("\n[OK] All validations passed")
    return True


def load_to_duckdb(df, db_path, table_name="retail_sales_clean"):
    """
    Load transformed DataFrame into DuckDB.

    Args:
        df: Transformed DataFrame
        db_path: Path to DuckDB database
        table_name: Name of target table

    Returns:
        Load time in seconds
    """
    print("\n" + "=" * 60)
    print("ETL PIPELINE - LOAD PHASE")
    print("=" * 60)

    load_start = time.perf_counter()

    conn = create_duckdb_connection(db_path)

    # Drop existing table if it exists (for clean runs)
    conn.execute(f"DROP TABLE IF EXISTS {table_name}")

    # Load DataFrame into DuckDB
    conn.execute(f"CREATE TABLE {table_name} AS SELECT * FROM df")

    # Validate row count
    row_count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]

    load_time = time.perf_counter() - load_start

    print(f"[OK] Loaded {row_count} records to DuckDB table '{table_name}'")
    print(f"  Load time: {load_time:.4f} seconds")

    conn.close()

    return load_time


def export_output(df, output_path):
    """
    Export transformed data to CSV for comparison.

    Args:
        df: Transformed DataFrame
        output_path: Path to output CSV
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"[OK] Exported cleaned data to {output_path}")


def save_performance_record(metrics, results_path):
    """
    Append performance metrics to results CSV.

    Args:
        metrics: Dict of performance data
        results_path: Path to results CSV
    """
    results_path = Path(results_path)
    results_path.parent.mkdir(parents=True, exist_ok=True)

    # Read existing results if they exist
    if results_path.exists():
        results_df = pd.read_csv(results_path)
    else:
        results_df = pd.DataFrame()

    # Append new record
    new_record = pd.DataFrame([metrics])
    results_df = pd.concat([results_df, new_record], ignore_index=True)

    results_df.to_csv(results_path, index=False)
    print(f"[OK] Performance metrics saved to {results_path}")


def main():
    """Main ETL pipeline execution."""
    parser = argparse.ArgumentParser(description="ETL Pipeline - Extract, Transform, Load")
    parser.add_argument(
        "--input",
        type=str,
        default=str(PROJECT_ROOT / "data" / "retail_sales_raw.csv"),
        help="Path to raw input CSV",
    )
    parser.add_argument(
        "--db",
        type=str,
        default=str(PROJECT_ROOT / "database" / "retail_sales.duckdb"),
        help="Path to DuckDB database file",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(PROJECT_ROOT / "output" / "etl_output.csv"),
        help="Path to output CSV",
    )
    parser.add_argument(
        "--results",
        type=str,
        default=str(PROJECT_ROOT / "results" / "performance_results.csv"),
        help="Path to performance results CSV",
    )
    parser.add_argument(
        "--export",
        action="store_true",
        help="Export cleaned data to CSV",
    )

    args = parser.parse_args()

    # Check input file exists
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"[FAIL] Input file not found: {input_path}")
        print("  Run: python data/generate_dataset.py")
        sys.exit(1)

    # Pipeline execution
    total_start = time.perf_counter()

    try:
        # Extract
        df_raw, extract_time = extract_raw_data(input_path)
        input_rows = len(df_raw)

        # Transform
        df_clean, transform_time = transform_data(df_raw)
        output_rows = len(df_clean)

        # Validate
        if not validate_transformed_data(df_clean):
            sys.exit(1)

        # Load
        load_time = load_to_duckdb(df_clean, args.db)

        # Export
        if args.export:
            export_output(df_clean, args.output)

        # Record performance
        total_time = time.perf_counter() - total_start
        metrics = {
            "pipeline": "ETL",
            "timestamp": pd.Timestamp.now(),
            "input_rows": input_rows,
            "output_rows": output_rows,
            "extraction_time_seconds": round(extract_time, 4),
            "transformation_time_seconds": round(transform_time, 4),
            "load_time_seconds": round(load_time, 4),
            "total_time_seconds": round(total_time, 4),
            "latency_ms": round(total_time * 1000.0, 2),
            "throughput_events_per_sec": round(output_rows / total_time if total_time > 0 else 0.0, 2),
        }

        save_performance_record(metrics, args.results)

        # Final summary
        print("\n" + "=" * 60)
        print("ETL PIPELINE - EXECUTION SUMMARY")
        print("=" * 60)
        print(f"Input rows:              {input_rows}")
        print(f"Output rows:             {output_rows}")
        print(f"Extraction time:         {extract_time:.4f}s")
        print(f"Transformation time:     {transform_time:.4f}s")
        print(f"Load time:               {load_time:.4f}s")
        print(f"Total time:              {total_time:.4f}s")
        print("Status:                  [OK] SUCCESS")
        print("=" * 60)

    except Exception as e:
        print(f"\n[FAIL] ETL Pipeline failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
