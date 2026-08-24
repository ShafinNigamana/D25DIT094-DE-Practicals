from pathlib import Path
import json

import pandas as pd


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
CUSTOMERS_PATH = DATA_DIR / "customers.csv"
TRANSACTIONS_PATH = DATA_DIR / "transactions.json"
LOG_PATH = DATA_DIR / "user_activity.log"
PROCESSED_PATH = DATA_DIR / "processed_customers.csv"
SERVED_PATH = DATA_DIR / "served_transactions.csv"


def generate_data():
    print("Stage 1: Data Generation")
    print("Customer CSV, transaction JSON, and activity log files are available in the data folder.")


def ingest_data():
    print("\nStage 2: Data Ingestion")
    customers = pd.read_csv(CUSTOMERS_PATH)
    transactions = pd.read_json(TRANSACTIONS_PATH)
    log_lines = []
    with LOG_PATH.open("r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                log_lines.append(line.strip())

    print(f"Loaded {len(customers)} customer records")
    print(f"Loaded {len(transactions)} transaction records")
    print(f"Loaded {len(log_lines)} activity log events")


def store_data():
    print("\nStage 3: Storage")
    print("Data is stored locally in the data folder.")


def transform_data():
    print("\nStage 4: Transformation")
    df = pd.read_csv(CUSTOMERS_PATH)
    cleaned = df.drop_duplicates().copy()
    cleaned["email"] = cleaned["email"].fillna("unknown@email.com")
    cleaned.to_csv(PROCESSED_PATH, index=False)
    print("Removed duplicates and filled missing emails.")
    print(cleaned)


def serve_data():
    print("\nStage 5: Data Serving")
    transactions = pd.read_json(TRANSACTIONS_PATH)
    customer_count = pd.read_csv(PROCESSED_PATH)["customer_id"].nunique()
    activity_count = 0
    with LOG_PATH.open("r", encoding="utf-8") as file:
        activity_count = sum(1 for line in file if line.strip())

    summary = {
        "metric": ["total_transactions", "total_transaction_amount", "number_of_customers", "number_of_user_activity_events"],
        "value": [
            len(transactions),
            round(float(transactions["amount"].sum()), 2),
            customer_count,
            activity_count,
        ],
    }

    summary_df = pd.DataFrame(summary)
    summary_df.to_csv(SERVED_PATH, index=False)

    print(summary_df)
    print("Serving file saved to data/served_transactions.csv")


def main():
    print("E-commerce Data Engineering Pipeline")
    print("Data Generation -> Data Ingestion -> Storage -> Transformation -> Data Serving")

    generate_data()
    ingest_data()
    store_data()
    transform_data()
    serve_data()

    print("\nPipeline demonstration completed.")


if __name__ == "__main__":
    main()
