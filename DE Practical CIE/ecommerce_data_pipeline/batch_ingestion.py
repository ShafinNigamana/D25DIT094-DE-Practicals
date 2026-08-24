from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
INPUT_PATH = DATA_DIR / "customers.csv"
OUTPUT_PATH = DATA_DIR / "processed_customers.csv"


def main():
    print("\n--- Batch Ingestion ---")
    print("Reading raw customer data from customers.csv")
    df = pd.read_csv(INPUT_PATH)
    print("Original data:")
    print(df)

    print("\nRemoving duplicate records...")
    df = df.drop_duplicates()

    print("Handling missing email values...")
    df["email"] = df["email"].fillna("unknown@email.com")

    print("Saving cleaned data to data/processed_customers.csv")
    df.to_csv(OUTPUT_PATH, index=False)

    print("\nCleaned data:")
    print(df)
    print("\nBatch ingestion completed.")


if __name__ == "__main__":
    main()
