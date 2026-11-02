"""
ELT (Extract, Load, Transform) Pipeline

This pipeline demonstrates the modern ELT pattern:
1. Extract raw data from CSV
2. Load raw data directly into DuckDB staging table
3. Transform using SQL inside DuckDB

Transformation rules are implemented in SQL.
Raw staging data is preserved for lineage and recovery.
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


def load_raw_data_to_staging(csv_path, db_path, staging_table="staging_retail_sales"):
    """
    Load raw CSV directly into DuckDB staging table WITHOUT transformations.

    This is the key difference from ETL: raw data goes directly to the database.

    Args:
        csv_path: Path to input CSV
        db_path: Path to DuckDB database
        staging_table: Name of staging table

    Returns:
        Tuple of (row_count, load_time)
    """
    print("=" * 60)
    print("ELT PIPELINE - EXTRACT & LOAD PHASE")
    print("=" * 60)

    load_start = time.perf_counter()

    # Read CSV with pandas to check it exists
    print(f"Reading raw data from {csv_path}...")
    # Read all columns as strings to preserve whitespace and format
    df_raw = pd.read_csv(csv_path, dtype=str)
    input_rows = len(df_raw)

    # Connect to DuckDB
    conn = create_duckdb_connection(db_path)

    # Drop existing staging table if it exists
    conn.execute(f"DROP TABLE IF EXISTS {staging_table}")

    # Load raw data directly into staging table
    conn.execute(f"CREATE TABLE {staging_table} AS SELECT * FROM df_raw")

    # Verify load
    staging_count = conn.execute(f"SELECT COUNT(*) FROM {staging_table}").fetchone()[0]

    load_time = time.perf_counter() - load_start

    print(f"[OK] Loaded {staging_count} raw records to DuckDB staging table '{staging_table}'")
    print(f"  Load time: {load_time:.4f} seconds")
    print(f"  Columns: transaction_id, transaction_date, store_code, product_id, quantity, unit_price, customer_id, payment_method")

    conn.close()

    return staging_count, load_time


def transform_in_sql(db_path, transform_sql_path, final_table="retail_sales_clean"):
    """
    Execute SQL transformation script to create final cleaned table.

    Args:
        db_path: Path to DuckDB database
        transform_sql_path: Path to SQL transformation script
        final_table: Name of final table

    Returns:
        Tuple of (output_rows, transform_time)
    """
    print("\n" + "=" * 60)
    print("ELT PIPELINE - SQL TRANSFORMATION PHASE")
    print("=" * 60)

    # Read SQL script
    with open(transform_sql_path, "r") as f:
        sql_script = f.read()

    transform_start = time.perf_counter()

    conn = create_duckdb_connection(db_path)

    # Execute transformation SQL
    conn.execute(sql_script)

    # Get final row count
    final_count = conn.execute(f"SELECT COUNT(*) FROM {final_table}").fetchone()[0]

    transform_time = time.perf_counter() - transform_start

    print(f"[OK] SQL transformation completed")
    print(f"  Output rows: {final_count}")
    print(f"  Transformation time: {transform_time:.4f} seconds")

    # Show sample of transformed data
    print(f"\nTransformed data sample (from DuckDB):")
    sample = conn.execute(f"SELECT * FROM {final_table} LIMIT 3").fetchall()
    columns = [desc[0] for desc in conn.description]
    sample_df = pd.DataFrame(sample, columns=columns)
    print(sample_df.to_string())

    conn.close()

    return final_count, transform_time


def validate_transformed_data(db_path, final_table="retail_sales_clean"):
    """
    Validate transformed data quality using SQL.

    Checks:
    - Required fields are not null
    - Numeric fields are valid
    - total_amount is correctly calculated
    - No legacy store codes in final data

    Args:
        db_path: Path to DuckDB database
        final_table: Name of final table

    Returns:
        bool: True if all validations pass
    """
    print("\n" + "=" * 60)
    print("ELT PIPELINE - VALIDATION PHASE")
    print("=" * 60)

    conn = create_duckdb_connection(db_path)
    issues = []

    # Check 1: transaction_id not null
    null_check = conn.execute(
        f"SELECT COUNT(*) FROM {final_table} WHERE transaction_id IS NULL"
    ).fetchone()[0]
    if null_check > 0:
        issues.append(f"  [FAIL] {null_check} null transaction_ids")
    else:
        print("  [OK] transaction_id: All non-null")

    # Check 2: store_code not null
    null_check = conn.execute(
        f"SELECT COUNT(*) FROM {final_table} WHERE store_code IS NULL"
    ).fetchone()[0]
    if null_check > 0:
        issues.append(f"  [FAIL] {null_check} null store_codes")
    else:
        print("  [OK] store_code: All non-null")

    # Check 3: product_id not null
    null_check = conn.execute(
        f"SELECT COUNT(*) FROM {final_table} WHERE product_id IS NULL"
    ).fetchone()[0]
    if null_check > 0:
        issues.append(f"  [FAIL] {null_check} null product_ids")
    else:
        print("  [OK] product_id: All non-null")

    # Check 4: quantity is positive
    invalid_check = conn.execute(
        f"SELECT COUNT(*) FROM {final_table} WHERE quantity IS NULL OR quantity < 0"
    ).fetchone()[0]
    if invalid_check > 0:
        issues.append(f"  [FAIL] {invalid_check} invalid quantities")
    else:
        print("  [OK] quantity: All valid and positive")

    # Check 5: unit_price is positive
    invalid_check = conn.execute(
        f"SELECT COUNT(*) FROM {final_table} WHERE unit_price IS NULL OR unit_price < 0"
    ).fetchone()[0]
    if invalid_check > 0:
        issues.append(f"  [FAIL] {invalid_check} invalid unit_prices")
    else:
        print("  [OK] unit_price: All valid and positive")

    # Check 6: total_amount is correctly calculated
    incorrect_check = conn.execute(
        f"SELECT COUNT(*) FROM {final_table} WHERE ABS(total_amount - (quantity * unit_price)) > 0.01"
    ).fetchone()[0]
    if incorrect_check > 0:
        issues.append(f"  [FAIL] {incorrect_check} incorrect total_amounts")
    else:
        print("  [OK] total_amount: Correctly calculated")

    # Check 7: No legacy store codes
    legacy_check = conn.execute(
        f"SELECT COUNT(*) FROM {final_table} WHERE store_code LIKE 'LEG%'"
    ).fetchone()[0]
    if legacy_check > 0:
        issues.append(f"  [FAIL] {legacy_check} legacy store codes found (not normalized)")
    else:
        print("  [OK] store_code: All legacy codes normalized")

    conn.close()

    if issues:
        print("\n[FAIL] VALIDATION FAILED:")
        for issue in issues:
            print(issue)
        return False

    print("\n[OK] All validations passed")
    return True


def export_output(db_path, output_path, table_name="retail_sales_clean"):
    """
    Export transformed data from DuckDB to CSV.

    Args:
        db_path: Path to DuckDB database
        output_path: Path to output CSV
        table_name: Name of table to export
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    conn = create_duckdb_connection(db_path)
    conn.execute(f"COPY {table_name} TO '{output_path}' (FORMAT CSV, HEADER TRUE)")
    conn.close()

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
    """Main ELT pipeline execution."""
    parser = argparse.ArgumentParser(description="ELT Pipeline - Extract, Load, Transform")
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
        "--transform-sql",
        type=str,
        default=str(PROJECT_ROOT / "elt" / "transform.sql"),
        help="Path to SQL transformation script",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(PROJECT_ROOT / "output" / "elt_output.csv"),
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

    # Check input files exist
    input_path = Path(args.input)
    sql_path = Path(args.transform_sql)

    if not input_path.exists():
        print(f"[FAIL] Input file not found: {input_path}")
        print("  Run: python data/generate_dataset.py")
        sys.exit(1)

    if not sql_path.exists():
        print(f"[FAIL] SQL file not found: {sql_path}")
        sys.exit(1)

    # Pipeline execution
    total_start = time.perf_counter()

    try:
        # Load raw data to staging
        staging_rows, load_time = load_raw_data_to_staging(input_path, args.db)

        # Transform using SQL
        output_rows, transform_time = transform_in_sql(args.db, sql_path)

        # Validate
        if not validate_transformed_data(args.db):
            sys.exit(1)

        # Export
        if args.export:
            export_output(args.db, args.output)

        # Record performance
        total_time = time.perf_counter() - total_start
        metrics = {
            "pipeline": "ELT",
            "timestamp": pd.Timestamp.now(),
            "input_rows": staging_rows,
            "output_rows": output_rows,
            "raw_load_time_seconds": round(load_time, 4),
            "transformation_time_seconds": round(transform_time, 4),
            "total_time_seconds": round(total_time, 4),
            "latency_ms": round(total_time * 1000.0, 2),
            "throughput_events_per_sec": round(output_rows / total_time if total_time > 0 else 0.0, 2),
        }

        save_performance_record(metrics, args.results)

        # Final summary
        print("\n" + "=" * 60)
        print("ELT PIPELINE - EXECUTION SUMMARY")
        print("=" * 60)
        print(f"Input rows:              {staging_rows}")
        print(f"Output rows:             {output_rows}")
        print(f"Raw load time:           {load_time:.4f}s")
        print(f"SQL transformation time: {transform_time:.4f}s")
        print(f"Total time:              {total_time:.4f}s")
        print("Status:                  [OK] SUCCESS")
        print("=" * 60)

    except Exception as e:
        print(f"\n[FAIL] ELT Pipeline failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
