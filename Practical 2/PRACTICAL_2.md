# Practical 2: Data Sources and Data Generation

## Aim / Problem Definition
To programmatically interface with diverse file-based, API-driven, and relational source database environments. The objective is to simulate transactional workloads, profile incoming files to automatically discover schemas, isolate data quality violations (such as null entry leaks and format divergence) into a quarantine directory, and establish appropriate operational ingestion criteria.

## Tools / Technologies
- Python 3.13
- Pandas (data manipulation and profiling)
- SQLite3 (relational database storage)
- Python standard library (`logging`, `os`, `re`, `json`)

## Step-by-Step
1. **Simulate Data Generation**: Run `generate_data.py` to create a realistic raw customer dataset (`data/customer.csv`) containing both valid and intentionally faulty rows (missing IDs, missing emails, invalid email formats).
2. **Profile Incoming Data**: Run `profile.py` using Pandas to inspect column headers, infer data types, check null counts, and compute descriptive statistics.
3. **Validate and Quarantine**: Run `validate.py` to scan each record against strict quality rules (non-null primary key `CustomerID`, valid `@` in `Email`). Split the dataset into valid rows and quarantine invalid rows into `quarantine/bad_records.csv`.
4. **Log Operational Events**: Use `logger.py` to record every audit milestone (records scanned, valid count, quarantined count, execution timestamp) into `logs/execution.log`.
5. **Ingest Clean Data**: Run `database.py` to create the SQLite table and insert only verified clean records into `customer.db`.

## Output
- `data/customer.csv`: Raw input data containing 20 simulated customer records.
- `quarantine/bad_records.csv`: Quarantined records that failed validation checks.
- `logs/execution.log`: Runtime audit log recording validation decisions.
- `customer.db`: SQLite database storing only clean, validated customer records.

## Key Questions

### 1. Explain the architectural strategies used to manage severe structural schema drift when handling continuous external third-party API inputs.
1. Store raw API responses in an immutable data lake before any parsing or transformation.
2. Implement automated schema profiling that compares incoming payload fields against a baseline registry.
3. Use flexible semi-structured storage (JSON/Parquet with schema evolution enabled) rather than rigid relational tables.
4. Route records with unexpected schema variations into a dead-letter queue (DLQ) or quarantine area.
5. Log schema version changes and set up alerts for unrecognized fields without halting pipeline processing.

### 2. What are the structural benefits and data storage trade-offs of using semi-structured nested JSON objects over heavily normalized SQL database records?
- **Benefits**:
  - Naturally captures hierarchical, 1-to-many relationships without requiring multi-table joins.
  - Highly flexible schema allows adding new fields without modifying database DDL.
  - Direct compatibility with web APIs and modern applications.
- **Trade-offs**:
  - Higher storage overhead due to repeated field keys across every record.
  - Slower complex analytical aggregations and joins compared to columnar or indexed relational tables.
  - Weaker enforcement of ACID constraints and referential integrity.

### 3. How do you validate data quality at the point of ingestion without creating severe processing performance bottlenecks?
1. Perform lightweight vector-based checks (null checking, regex pattern matching, type validation) using high-performance libraries like Pandas or DuckDB.
2. Prioritize primary key integrity and format validation at ingestion, deferring deep business logic to asynchronous downstream stages.
3. Isolate corrupt records to a quarantine destination in memory batches rather than failing row-by-row.
4. Log validation counts asynchronously to avoid blocking the main data stream.

## Supplementary Problem: Automated Quarantine & Log Alerting
**Requirement**: Develop a validation routine that parses a directory of messy user files, auto-quarantines records missing structural primary keys, and sends automated warning alerts to system logs.

**Implementation & Result**:
- Implemented in `validate.py`: The script scans the data folder, checks for missing `CustomerID` primary keys and malformed email addresses.
- Corrupted records are immediately saved to `quarantine/bad_records.csv`.
- An automated warning alert is emitted to `logs/execution.log` noting exact row counts and violations.
- Clean records continue down the pipeline to `customer.db` without interruption.

## Conclusion
Practical 2 demonstrates how to handle raw incoming data from heterogeneous sources safely. By separating data profiling, automated quarantine of corrupt records, and persistent audit logging, the ingestion pipeline guarantees that downstream databases only receive clean, dependable data.

## Screenshot List
- **Screenshot 1 – Data Profiling Output**: Terminal output of `profile.py` displaying column names, datatypes, and summary statistics.  
  *Where to place it*: Under Output section.
- **Screenshot 2 – Validation & Quarantine Execution**: Terminal output of `validate.py` showing bad records detected and saved.  
  *Where to place it*: Under Supplementary Problem section.
- **Screenshot 3 – Execution Log & Quarantined CSV**: Contents of `logs/execution.log` and `quarantine/bad_records.csv`.  
  *Where to place it*: Under Output section.
- **Screenshot 4 – SQLite Clean Records**: Terminal/DB browser query showing clean rows in `customer.db`.  
  *Where to place it*: Under Output section.
