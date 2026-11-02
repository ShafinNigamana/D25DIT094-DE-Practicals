"""
Generate a synthetic retail sales dataset with data quality issues.

This script creates a reproducible dataset containing:
- Inconsistent whitespace
- Legacy store codes (LEG001, LEG002, etc.)
- Numeric values as strings
- Realistic retail transaction data

Dataset size: 100,000+ records
"""

import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import sys

# Ensure reproducibility
np.random.seed(42)


def generate_retail_sales_dataset(num_records=100000, output_path=None):
    """
    Generate a synthetic retail sales dataset with intentional data quality issues.

    Args:
        num_records: Number of records to generate (default 100,000)
        output_path: Path to save the CSV file

    Returns:
        DataFrame with raw (un-normalized) data
    """

    # Use project root relative path if not specified
    if output_path is None:
        output_path = Path(__file__).parent / "retail_sales_raw.csv"
    else:
        output_path = Path(output_path)

    print(f"Generating {num_records} retail sales records...")

    # Base date for transactions
    base_date = datetime(2023, 1, 1)

    # Transaction IDs with intentional whitespace issues
    transaction_ids = [f"  TXN{i:08d}  " for i in range(1, num_records + 1)]

    # Transaction dates over 1 year
    dates = [
        (base_date + timedelta(days=int(d))).strftime("%Y-%m-%d")
        for d in np.random.uniform(0, 365, num_records)
    ]

    # Legacy store codes with whitespace issues
    legacy_codes = [f"LEG{i:03d}" for i in range(1, 11)]  # 10 stores
    store_codes_raw = np.random.choice(legacy_codes, num_records)
    # Add whitespace issues
    store_codes = [f" {code} " if np.random.rand() > 0.3 else code for code in store_codes_raw]

    # Product IDs with whitespace
    product_ids = [f" PROD{np.random.randint(100, 999)} " if np.random.rand() > 0.4
                   else f"PROD{np.random.randint(100, 999)}" for _ in range(num_records)]

    # Quantities (mostly as strings with potential whitespace)
    quantities_str = [str(np.random.randint(1, 20)) for _ in range(num_records)]
    quantities = [f"  {q}  " if np.random.rand() > 0.5 else q for q in quantities_str]

    # Unit prices (numeric as strings with whitespace issues)
    unit_prices = [f" {np.random.uniform(5.0, 500.0):.2f} " if np.random.rand() > 0.4
                   else f"{np.random.uniform(5.0, 500.0):.2f}" for _ in range(num_records)]

    # Customer IDs with whitespace
    customer_ids = [f"CUST{np.random.randint(10000, 99999)}" for _ in range(num_records)]
    customer_ids = [f"  {cid}  " if np.random.rand() > 0.6 else cid for cid in customer_ids]

    # Payment methods with whitespace issues
    payment_methods_raw = ["credit_card", "debit_card", "cash", "online_wallet"]
    payment_methods = np.random.choice(payment_methods_raw, num_records)
    payment_methods = [f" {pm} " if np.random.rand() > 0.5 else pm for pm in payment_methods]

    # Create DataFrame
    df = pd.DataFrame({
        "transaction_id": transaction_ids,
        "transaction_date": dates,
        "store_code": store_codes,
        "product_id": product_ids,
        "quantity": quantities,
        "unit_price": unit_prices,
        "customer_id": customer_ids,
        "payment_method": payment_methods,
    })

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save to CSV
    df.to_csv(output_path, index=False, quoting=1)  # quoting=1 preserves spaces

    print(f"✓ Dataset created: {output_path}")
    print(f"  Records: {len(df)}")
    print(f"  Columns: {', '.join(df.columns.tolist())}")
    print(f"\nSample rows (raw data with whitespace issues):")
    print(df.head())

    return df


if __name__ == "__main__":
    # Support command-line arguments
    num_records = 100000
    if len(sys.argv) > 1:
        try:
            num_records = int(sys.argv[1])
        except ValueError:
            print(f"Invalid number of records: {sys.argv[1]}")
            sys.exit(1)

    generate_retail_sales_dataset(num_records)
    print("\n✓ Dataset generation complete")
