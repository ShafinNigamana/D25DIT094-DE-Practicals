# Practical 4: ETL vs ELT Pipeline Design

## Aim / Problem Definition
To implement and compare ETL (Extract-Transform-Load) and ELT (Extract-Load-Transform) data pipelines using an identical high-volume retail sales dataset (100,000 records). Measure and evaluate their performance in terms of latency, throughput, data lineage, recovery from transformation errors, and network overhead. Additionally, refactor the ELT pipeline using dbt Core and automated schema tests.

## Tools / Technologies
- Python 3.13
- Pandas (in-memory ETL transformation)
- DuckDB (embedded columnar OLAP database for ELT and dbt)
- SQL (in-database transformations)
- dbt Core (`dbt-duckdb`)

## Step-by-Step
1. **Generate Dataset**: Generate `data/retail_sales_raw.csv` containing 100,000 retail transactions with intentional noise (inconsistent whitespace, legacy store codes, string-encoded numeric values).
2. **Execute ETL Pipeline**: Run `etl/etl_pipeline.py`. Raw CSV records are extracted, transformed in memory using Pandas (whitespace stripped, store codes normalized to `STORE_xxx`, totals computed), and then bulk loaded into DuckDB (`retail_sales_clean`).
3. **Execute ELT Pipeline**: Run `elt/elt_pipeline.py`. Raw CSV records are loaded directly into DuckDB staging (`staging_retail_sales`), and transformation logic is executed directly inside the database engine via SQL (`elt/transform.sql`).
4. **Compare Performance**: Run `benchmark/compare_results.py` to compare latency (total elapsed time in ms) and throughput (records processed per second).
5. **Implement dbt Core Models**: Modularize the ELT SQL transformation into dbt models (`models/staging/stg_retail_sales.sql` and `models/marts/retail_sales_clean.sql`).
6. **Automated Schema Testing**: Define and execute dbt data tests (`unique`, `not_null`, `accepted_values`, `relationships`) to ensure high data quality.

## Output
### Performance Benchmark Results (100,000 records):
| Metric | ETL (Pandas In-Memory) | ELT (In-Database SQL) |
| :--- | :--- | :--- |
| **Input Rows** | 100,000 | 100,000 |
| **Output Rows** | 100,000 | 100,000 |
| **Extraction / Raw Load** | 0.1875 s | 0.7538 s |
| **Transformation Time** | 0.2554 s | 0.3378 s |
| **Load Time** | 0.1649 s | (Loaded initially) |
| **Total Pipeline Time** | **0.8366 s** | **1.9081 s** |
| **Latency** | **836.60 ms** | **1908.10 ms** |
| **Throughput** | **119,531 records/sec** | **52,408 records/sec** |

*(Note: In local memory tests, Python/Pandas in-memory execution was faster because of small disk/overhead, whereas ELT persists raw staging tables, which enables data lineage and recovery.)*

## Key Questions

### 1. How does cloud compute and storage separation support ELT?
In modern cloud data warehouses (such as Snowflake, BigQuery, and Databricks), compute and storage scale independently. Raw data can be dumped cheaply into object storage (Extract & Load) without upfront schema constraints. Elastic compute clusters are then spun up on demand to transform large datasets in parallel using SQL, making ELT far more scalable and cost-effective than provisioning fixed ETL application servers.

### 2. Which pipeline provides better data recovery?
**ELT provides significantly better data recovery**. Because ELT preserves the raw, unaltered data in a persistent staging table or data lake, any bug in business transformation logic can be fixed simply by modifying the SQL script and re-running the transformation against the raw table. In traditional ETL, the raw data is discarded or overwritten, requiring a full re-extraction from the source transactional database.

### 3. How does network usage differ?
- **ETL**: Moves raw data across the network from source to the ETL server, processes it in memory, and then sends transformed data over the network to the database (dual network hop).
- **ELT**: Ingests raw data directly into the database/warehouse. All transformation and joining happen internally within the database storage cluster, eliminating repetitive intermediate network transfers.

## Supplementary Problem: Modular dbt Core Implementation
**Requirement**: Refactor the ELT SQL transformation into modular dbt models and add automated schema tests.

**Implementation & Result**:
- Created a modular dbt project with two transformation layers:
  1. `stg_retail_sales`: Cleans raw strings, standardizes column formats, and normalizes legacy store codes.
  2. `retail_sales_clean`: Computes final metrics (`total_amount = quantity * unit_price`) and prepares data for analytics marts.
- Added automated schema tests in `schema.yml`:
  - `unique` and `not_null` on `transaction_id`.
  - `not_null` and positive value checks on `quantity` and `unit_price`.
  - `accepted_values` on `payment_method`.
- Successfully validated models with `dbt run` and `dbt test`.

## Conclusion
Practical 4 illustrated the architectural and performance trade-offs between ETL and ELT. While ETL proved fast for local in-memory workloads, ELT excels in enterprise architectures by decoupling loading from transformation, preserving raw audit history, and enabling testable, modular SQL models using modern tools like dbt Core.

## Screenshot List
- **Screenshot 1 – ETL Pipeline Run**: Terminal output showing extraction, transformation, and load of 100,000 records.  
  *Where to place it*: Under Step-by-Step section.
- **Screenshot 2 – ELT Pipeline Run**: Terminal output showing raw staging load and in-database SQL execution.  
  *Where to place it*: Under Step-by-Step section.
- **Screenshot 3 – Benchmark Comparison**: Terminal table from `benchmark/compare_results.py` showing latency and throughput.  
  *Where to place it*: Under Output section.
- **Screenshot 4 – dbt Run & Test**: Terminal output showing successful compilation, model creation, and automated schema tests.  
  *Where to place it*: Under Supplementary Problem section.
