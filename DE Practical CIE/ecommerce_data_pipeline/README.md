# E-commerce Data Engineering Practical

## 1. Problem definition

This practical demonstrates a simple end-to-end data engineering pipeline for an e-commerce company using local files only. The workflow shows:

Data Generation → Data Ingestion → Storage → Transformation → Data Serving

The project uses:

- CSV data for customer records
- JSON data for transaction records
- Log files for user activity events
- Local storage in the data folder
- Python and pandas for simple processing

## 2. Project structure

```text
ecommerce_data_pipeline/
├── data/
│   ├── customers.csv
│   ├── transactions.json
│   ├── user_activity.log
│   ├── processed_customers.csv
│   └── served_transactions.csv
├── profiling.py
├── batch_ingestion.py
├── streaming_ingestion.py
├── pipeline.py
└── README.md
```

## 3. How to install pandas

Open a terminal in the project folder and run:

```bash
pip install pandas
```

If pandas is already installed, this step is not needed.

## 4. How to run each Python file

From the project folder:

```bash
python profiling.py
python batch_ingestion.py
python streaming_ingestion.py
python pipeline.py
```

## 5. What each file demonstrates

- `profiling.py`: reads the CSV, JSON, and log files; displays data; checks duplicates, missing values, data types, and timestamp formats.
- `batch_ingestion.py`: reads raw customer data, removes duplicates, fills missing email values, and saves cleaned output to `data/processed_customers.csv`.
- `streaming_ingestion.py`: simulates streaming data arrival by reading log events one by one with a short delay.
- `pipeline.py`: shows the full lifecycle from generation to serving and creates a simple serving summary.

## 6. Batch vs streaming comparison

- Batch processing is used for bulk historical data such as customer records.
- Streaming-style processing is used for continuous events such as user activity logs.
- In this project, batch ingestion handles stored files in one pass, while streaming ingestion simulates real-time event arrival.

## 7. Final conclusion

This simple practical demonstrates how a data engineering pipeline can move data through generation, ingestion, storage, transformation, and serving using basic Python tools and local files. It keeps the design beginner-friendly and easy to run in VS Code without advanced infrastructure.
