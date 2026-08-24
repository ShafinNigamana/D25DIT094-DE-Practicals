from pathlib import Path
import json

import pandas as pd


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"


def read_customers():
    path = DATA_DIR / "customers.csv"
    df = pd.read_csv(path)
    print("\n--- Customer Data (CSV) ---")
    print(df)
    print("\nMissing values by column:")
    print(df.isnull().sum())
    print("Duplicate rows:", int(df.duplicated().sum()))
    print("Data types:")
    print(df.dtypes)
    return df


def read_transactions():
    path = DATA_DIR / "transactions.json"
    with path.open("r", encoding="utf-8") as file:
        records = json.load(file)

    df = pd.DataFrame(records)
    print("\n--- Transaction Data (JSON) ---")
    print(df)
    print("\nMissing values by column:")
    print(df.isnull().sum())
    print("Duplicate rows:", int(df.duplicated().sum()))
    print("Data types:")
    print(df.dtypes)
    return df


def read_activity_log():
    path = DATA_DIR / "user_activity.log"
    rows = []
    bad_timestamps = []

    with path.open("r", encoding="utf-8") as file:
        for line in file:
            cleaned = line.strip()
            if not cleaned:
                continue
            parts = cleaned.split(",")
            if len(parts) == 3:
                timestamp, customer_id, event = parts
                rows.append({
                    "timestamp": timestamp,
                    "customer_id": customer_id,
                    "event": event,
                })

                iso_like = False
                try:
                    pd.to_datetime(timestamp, format="%Y-%m-%d %H:%M:%S")
                    iso_like = True
                except (ValueError, TypeError):
                    pass

                if not iso_like:
                    try:
                        pd.to_datetime(timestamp, format="%Y-%m-%dT%H:%M:%S")
                        iso_like = True
                    except (ValueError, TypeError):
                        pass

                if not iso_like:
                    bad_timestamps.append(timestamp)

    df = pd.DataFrame(rows)
    print("\n--- User Activity Log ---")
    print(df)
    print("\nMissing values by column:")
    print(df.isnull().sum())
    print("Duplicate rows:", int(df.duplicated().sum()))
    print("Data types:")
    print(df.dtypes)
    print("\nInconsistent timestamp formats found:")
    if bad_timestamps:
        print(bad_timestamps)
    else:
        print("No inconsistent timestamp format detected.")
    return df


def main():
    print("Data Engineering Practical - Profiling Step")
    print("This script reads raw source files and checks data quality.")

    customers = read_customers()
    transactions = read_transactions()
    activity = read_activity_log()

    print("\nProfiling summary:")
    print(f"Customers: {len(customers)} rows")
    print(f"Transactions: {len(transactions)} rows")
    print(f"User activity events: {len(activity)} rows")


if __name__ == "__main__":
    main()
