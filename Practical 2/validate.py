import os
import pandas as pd
import logging
import logger  # Initialises the logging configuration

# 1. Log validation started
logging.info("Validation started.")

data_dir = "data"
quarantine_dir = "quarantine"
os.makedirs(quarantine_dir, exist_ok=True)

# Process CSV files inside data directory (Requirement 4)
csv_files = [os.path.join(data_dir, f) for f in os.listdir(data_dir) if f.endswith(".csv")]

if not csv_files:
    logging.warning("No CSV files found in the data directory.")
    print("No data files to validate.")
else:
    for file_path in csv_files:
        filename = os.path.basename(file_path)
        df = pd.read_csv(file_path)
        
        # Check that required columns exist
        if "CustomerID" not in df.columns or "Email" not in df.columns:
            logging.warning(f"File {filename} is missing required CustomerID or Email columns. Skipping.")
            continue
        
        # Missing primary key (CustomerID)
        missing_id = df["CustomerID"].isnull()
        
        # Missing email
        missing_email = df["Email"].isnull()
        
        # Basic email format check (must contain '@')
        invalid_email_format = df["Email"].apply(lambda x: "@" not in str(x) if pd.notnull(x) else False)
        
        # Combine validation conditions
        bad = df[missing_id | missing_email | invalid_email_format]
        
        # 2. Log number of invalid records found
        logging.info(f"File {filename}: {len(bad)} invalid records found.")
        
        # Save invalid records to quarantine folder only if they exist
        if filename == "customer.csv":
            quarantine_file = os.path.join(quarantine_dir, "bad_records.csv")
        else:
            quarantine_file = os.path.join(quarantine_dir, f"bad_{filename}")
            
        if not bad.empty:
            bad.to_csv(quarantine_file, index=False)
            # 3. Log quarantine file created
            logging.info(f"Quarantine file created: {quarantine_file}")

# 4. Log validation completed
logging.info("Validation completed.")
print("Bad Records Saved")