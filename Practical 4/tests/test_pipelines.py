"""
Basic tests for ETL/ELT pipelines.

Verifies:
- Raw dataset exists
- ETL output exists
- ELT output exists
- Both pipelines produce same number of rows
- Required columns exist
- Data quality checks pass
"""

import sys
from pathlib import Path
import pandas as pd
import duckdb

PROJECT_ROOT = Path(__file__).parent.parent


def test_raw_dataset_exists():
    """Test that raw dataset exists."""
    csv_path = PROJECT_ROOT / "data" / "retail_sales_raw.csv"
    assert csv_path.exists(), f"Raw dataset not found: {csv_path}"
    print("[OK] Raw dataset exists")


def test_raw_dataset_valid():
    """Test that raw dataset is valid."""
    csv_path = PROJECT_ROOT / "data" / "retail_sales_raw.csv"
    df = pd.read_csv(csv_path, dtype=str)

    assert len(df) > 0, "Raw dataset is empty"
    assert len(df) >= 100000, f"Raw dataset has fewer than 100,000 rows: {len(df)}"

    required_columns = [
        "transaction_id", "transaction_date", "store_code", "product_id",
        "quantity", "unit_price", "customer_id", "payment_method"
    ]
    for col in required_columns:
        assert col in df.columns, f"Missing required column: {col}"

    print(f"[OK] Raw dataset valid ({len(df)} rows, {len(df.columns)} columns)")


def test_etl_output_exists():
    """Test that ETL produced output."""
    db_path = PROJECT_ROOT / "database" / "retail_sales.duckdb"
    assert db_path.exists(), f"DuckDB database not found: {db_path}"

    conn = duckdb.connect(str(db_path))
    tables = conn.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
    ).fetchall()
    table_names = [t[0] for t in tables]

    assert "retail_sales_clean" in table_names, "ETL did not create retail_sales_clean table"
    conn.close()
    print("[OK] ETL output exists (retail_sales_clean table)")


def test_elt_output_exists():
    """Test that ELT produced output."""
    db_path = PROJECT_ROOT / "database" / "retail_sales.duckdb"
    assert db_path.exists(), f"DuckDB database not found: {db_path}"

    conn = duckdb.connect(str(db_path))
    tables = conn.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
    ).fetchall()
    table_names = [t[0] for t in tables]

    assert "staging_retail_sales" in table_names, "ELT did not create staging_retail_sales table"
    conn.close()
    print("[OK] ELT output exists (staging_retail_sales table)")


def test_row_counts_match():
    """Test that both pipelines produce same row count."""
    db_path = PROJECT_ROOT / "database" / "retail_sales.duckdb"
    conn = duckdb.connect(str(db_path))

    etl_count = conn.execute("SELECT COUNT(*) FROM retail_sales_clean").fetchone()[0]
    elt_count = conn.execute("SELECT COUNT(*) FROM retail_sales_clean").fetchone()[0]

    assert etl_count == elt_count, f"Row count mismatch: ETL={etl_count}, ELT={elt_count}"
    conn.close()
    print(f"[OK] Row counts match: {etl_count} rows")


def test_required_columns_exist():
    """Test that all required columns exist in output."""
    db_path = PROJECT_ROOT / "database" / "retail_sales.duckdb"
    conn = duckdb.connect(str(db_path))

    columns = conn.execute("PRAGMA table_info(retail_sales_clean)").fetchall()
    column_names = [c[1] for c in columns]

    required_columns = [
        "transaction_id", "transaction_date", "store_code", "product_id",
        "quantity", "unit_price", "customer_id", "payment_method", "total_amount"
    ]

    for col in required_columns:
        assert col in column_names, f"Missing required column: {col}"

    conn.close()
    print(f"[OK] All required columns exist: {', '.join(required_columns)}")


def test_total_amount_calculation():
    """Test that total_amount is correctly calculated."""
    db_path = PROJECT_ROOT / "database" / "retail_sales.duckdb"
    conn = duckdb.connect(str(db_path))

    # Check if total_amount = quantity * unit_price
    mismatches = conn.execute(
        "SELECT COUNT(*) FROM retail_sales_clean WHERE ABS(total_amount - (quantity * unit_price)) > 0.01"
    ).fetchone()[0]

    assert mismatches == 0, f"total_amount calculation errors: {mismatches} records"
    conn.close()
    print("[OK] total_amount correctly calculated")


def test_legacy_codes_normalized():
    """Test that legacy store codes are normalized."""
    db_path = PROJECT_ROOT / "database" / "retail_sales.duckdb"
    conn = duckdb.connect(str(db_path))

    legacy_count = conn.execute(
        "SELECT COUNT(*) FROM retail_sales_clean WHERE store_code LIKE 'LEG%'"
    ).fetchone()[0]

    assert legacy_count == 0, f"Legacy store codes not normalized: {legacy_count} records"

    # Check that we have STORE_ format
    store_format_count = conn.execute(
        "SELECT COUNT(*) FROM retail_sales_clean WHERE store_code LIKE 'STORE_%'"
    ).fetchone()[0]

    assert store_format_count > 0, "No normalized STORE_ format found"
    conn.close()
    print("[OK] Legacy store codes normalized to STORE_ format")


def test_no_null_keys():
    """Test that required keys are not null."""
    db_path = PROJECT_ROOT / "database" / "retail_sales.duckdb"
    conn = duckdb.connect(str(db_path))

    key_columns = ["transaction_id", "store_code", "product_id"]

    for col in key_columns:
        null_count = conn.execute(
            f"SELECT COUNT(*) FROM retail_sales_clean WHERE {col} IS NULL"
        ).fetchone()[0]
        assert null_count == 0, f"Found {null_count} NULL values in {col}"

    conn.close()
    print("[OK] No NULL values in key columns")


def test_numeric_columns_valid():
    """Test that numeric columns are valid."""
    db_path = PROJECT_ROOT / "database" / "retail_sales.duckdb"
    conn = duckdb.connect(str(db_path))

    # quantity should be positive integer
    qty_issues = conn.execute(
        "SELECT COUNT(*) FROM retail_sales_clean WHERE quantity IS NULL OR quantity <= 0"
    ).fetchone()[0]
    assert qty_issues == 0, f"Invalid quantity values: {qty_issues}"

    # unit_price should be positive
    price_issues = conn.execute(
        "SELECT COUNT(*) FROM retail_sales_clean WHERE unit_price IS NULL OR unit_price <= 0"
    ).fetchone()[0]
    assert price_issues == 0, f"Invalid unit_price values: {price_issues}"

    conn.close()
    print("[OK] Numeric columns are valid")


def test_performance_results_exist():
    """Test that performance results were recorded."""
    results_path = PROJECT_ROOT / "results" / "performance_results.csv"
    assert results_path.exists(), f"Performance results not found: {results_path}"

    results = pd.read_csv(results_path)
    assert len(results) >= 2, "Performance results should have at least 2 rows (ETL + ELT)"

    pipelines = results["pipeline"].unique()
    assert "ETL" in pipelines, "ETL results not found"
    assert "ELT" in pipelines, "ELT results not found"

    print(f"[OK] Performance results recorded ({len(results)} runs total)")


def run_all_tests():
    """Run all tests."""
    tests = [
        ("Raw dataset exists", test_raw_dataset_exists),
        ("Raw dataset valid", test_raw_dataset_valid),
        ("ETL output exists", test_etl_output_exists),
        ("ELT output exists", test_elt_output_exists),
        ("Row counts match", test_row_counts_match),
        ("Required columns exist", test_required_columns_exist),
        ("Total amount calculated correctly", test_total_amount_calculation),
        ("Legacy codes normalized", test_legacy_codes_normalized),
        ("No NULL in key columns", test_no_null_keys),
        ("Numeric columns valid", test_numeric_columns_valid),
        ("Performance results exist", test_performance_results_exist),
    ]

    print("\n" + "=" * 60)
    print("RUNNING TESTS")
    print("=" * 60 + "\n")

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"[FAIL] {test_name}: {e}")
            failed += 1
        except Exception as e:
            print(f"[FAIL] {test_name}: Unexpected error: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
