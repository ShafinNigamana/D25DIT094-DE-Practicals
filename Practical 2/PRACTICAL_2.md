# Practical 2: Data Ingestion and Validation Pipeline

## Objective
The objective of this practical is to construct a beginner-friendly data ingestion and validation pipeline. It validates customer dataset files, filters invalid entries into a quarantine directory, and logs runtime events using standard Python logging.

## Technologies Used
- Python 3
- Pandas (data manipulation)
- SQLite3 (database storage)
- Python standard library (`logging`, `os`)

## Folder Structure
```text
Practical 2/
├── data/
│   ├── api.json
│   ├── config.txt
│   └── customer.csv
├── logs/
│   └── execution.log
├── quarantine/
│   └── bad_records.csv
├── api_generate.py
├── customer.db
├── database.py
├── generate_data.py
├── logger.py
├── profile.py
├── validate.py
└── PRACTICAL_2.md
```

## Steps to Run
1. Run `python generate_data.py` to create the mock customer dataset (`data/customer.csv`).
2. Run `python profile.py` to examine the structure, data types, and statistics of the customer file.
3. Run `python validate.py` to run the validation checks, quarantine invalid rows, and log the process.
4. Run `python database.py` to ingest the dataset into the SQLite database (`customer.db`).

## Data Validation Strategy
Records are classified as invalid if they fail any of the following checks:
- **Missing Primary Key**: The `CustomerID` field is empty or null.
- **Missing Email**: The `Email` field is empty or null.
- **Basic Email Format**: The `Email` value does not contain a `@` symbol.

Invalid records are removed from the pipeline and saved separately inside the quarantine directory.

## Output Files
- `quarantine/bad_records.csv`: File containing all records that failed the validation checks.
- `logs/execution.log`: Audit log recording process milestones (start time, invalid counts, file creations, and completion).
- `customer.db`: SQLite database storing customer records.

## Conclusion
This implementation demonstrates how to build basic data quality checks, separate clean data from bad data, and maintain runtime logging in a standard data ingestion workflow.
