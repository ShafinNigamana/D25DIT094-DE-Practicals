# Practical 4: ETL vs ELT Pipeline Comparison

## Overview

This practical implements and compares two fundamental data pipeline architectures for processing retail sales data:

- **ETL (Extract-Transform-Load)**: Traditional pattern where data is transformed in application memory (Python/Pandas) before loading into the database
- **ELT (Extract-Load-Transform)**: Modern pattern where raw data is loaded directly into the database and transformations are performed using SQL

## Learning Objectives

1. Understand the architectural differences between ETL and ELT paradigms
2. Implement both patterns using the same dataset and equivalent business logic
3. Measure performance differences in a local environment
4. Evaluate trade-offs in data lineage, maintainability, and scalability
5. Understand how cloud infrastructure influences architectural decisions

## Problem Statement

Implement two pipelines processing identical high-volume retail transaction data containing:

- Inconsistent whitespace
- Legacy store codes requiring normalization
- Numeric values in various formats

Compare the pipelines in terms of:

- Execution performance
- Data lineage tracking
- Recovery from transformation bugs
- Maintenance complexity

## Project Structure

```
Practical 4/
├── data/
│   ├── generate_dataset.py          # Synthetic dataset generator
│   └── retail_sales_raw.csv         # Generated dataset (100K+ records)
│
├── etl/
│   └── etl_pipeline.py              # ETL implementation (Pandas transformations)
│
├── elt/
│   ├── elt_pipeline.py              # ELT implementation (SQL transformations)
│   └── transform.sql                # SQL transformation logic
│
├── benchmark/
│   └── compare_results.py           # Performance comparison analysis
│
├── tests/
│   └── test_pipelines.py            # Automated validation tests
│
├── results/
│   └── performance_results.csv      # Performance metrics from both pipelines
│
├── output/
│   ├── etl_output.csv              # ETL cleaned data export
│   └── elt_output.csv              # ELT cleaned data export
│
├── database/
│   └── retail_sales.duckdb         # DuckDB database (created at runtime)
│
├── dbt_project/                     # Supplementary dbt implementation
│   ├── dbt_project.yml
│   ├── profiles.yml
│   ├── schema.yml
│   ├── models/
│   │   ├── staging/
│   │   │   └── stg_retail_sales.sql
│   │   └── marts/
│   │       └── retail_sales_clean.sql
│
├── requirements.txt                 # Python dependencies
└── README.md                        # This file
```

## Dataset

### Generation

The synthetic dataset generator creates 100,000+ retail transaction records with intentional data quality issues:

- **Inconsistent whitespace**: Leading/trailing spaces in string fields
- **Legacy store codes**: LEG001-LEG010 format requiring normalization to STORE_001-STORE_010
- **Numeric as strings**: Quantities and prices stored as text
- **Realistic data**: Random but deterministic transactions over a full year

### Columns

| Column           | Type   | Notes                                     |
| ---------------- | ------ | ----------------------------------------- |
| transaction_id   | String | Unique identifier with whitespace         |
| transaction_date | String | YYYY-MM-DD format                         |
| store_code       | String | Legacy format (LEG\*\*\*) with whitespace |
| product_id       | String | Product code with potential whitespace    |
| quantity         | String | Integer quantity as text                  |
| unit_price       | String | Decimal price as text                     |
| customer_id      | String | Customer identifier                       |
| payment_method   | String | Payment type with whitespace              |

### Generate Dataset

```powershell
cd "C:\College Studies\SEM 5\DE\Github Practicals\Practical 4"
python data/generate_dataset.py
```

Optional: Generate custom record count:

```powershell
python data/generate_dataset.py 50000
```

## Transformation Rules

Both pipelines apply identical business logic:

1. **transaction_id**: Strip whitespace, preserve as identifier
2. **store_code**: Strip whitespace, normalize legacy codes
   - `LEG001` → `STORE_001`
   - `LEG002` → `STORE_002`
   - etc.
3. **product_id**: Strip whitespace
4. **customer_id**: Strip whitespace
5. **quantity**: Convert to integer, validate > 0
6. **unit_price**: Convert to decimal, validate > 0
7. **payment_method**: Strip whitespace, convert to lowercase
8. **transaction_date**: Keep as-is (already normalized)
9. **total_amount**: Calculate as `quantity × unit_price`

### ETL Implementation (Python/Pandas)

```python
# Transformation occurs in application memory
df["store_code"] = df["store_code"].str.strip()
df["store_code"] = df["store_code"].apply(normalize_store_code)
df["quantity"] = pd.to_numeric(df["quantity"].str.strip()).astype("int64")
df["total_amount"] = df["quantity"] * df["unit_price"]
```

### ELT Implementation (DuckDB SQL)

```sql
-- Transformation occurs inside database
SELECT
    TRIM(transaction_id) AS transaction_id,
    CASE
        WHEN TRIM(store_code) LIKE 'LEG%'
        THEN 'STORE_' || SUBSTR(TRIM(store_code), 4)
        ELSE TRIM(store_code)
    END AS store_code,
    CAST(TRIM(quantity) AS INTEGER) AS quantity,
    CAST(TRIM(quantity) AS INTEGER) * CAST(TRIM(unit_price) AS DECIMAL) AS total_amount
FROM staging_retail_sales;
```

## Running the Pipelines

### ETL Pipeline

```powershell
cd "C:\College Studies\SEM 5\DE\Github Practicals\Practical 4"

# Generate dataset first (if not already done)
python data/generate_dataset.py

# Run ETL pipeline
python etl/etl_pipeline.py
```

**Output**:

- Transformed data loaded to DuckDB table: `retail_sales_clean`
- Performance metrics recorded in: `results/performance_results.csv`
- Optionally export cleaned data: `python etl/etl_pipeline.py --export`

### ELT Pipeline

```powershell
cd "C:\College Studies\SEM 5\DE\Github Practicals\Practical 4"

# Generate dataset first (if not already done)
python data/generate_dataset.py

# Run ELT pipeline
python elt/elt_pipeline.py
```

**Output**:

- Raw data loaded to staging: `staging_retail_sales` table
- Transformed data in final table: `retail_sales_clean` table
- Performance metrics appended to: `results/performance_results.csv`
- Optionally export cleaned data: `python elt/elt_pipeline.py --export`

## Performance Comparison

### Run Both Pipelines

```powershell
# ETL execution
python etl/etl_pipeline.py --export

# ELT execution
python elt/elt_pipeline.py --export

# Compare results
python benchmark/compare_results.py
```

### Metrics Recorded

- **pipeline**: Name (ETL or ELT)
- **timestamp**: Execution time
- **input_rows**: Records ingested
- **output_rows**: Records in final table
- **extraction_time_seconds** (ETL): CSV read time
- **transformation_time_seconds**: Processing time
- **load_time_seconds**: Database write time
- **total_time_seconds**: Complete pipeline execution

### Sample Results

```
ETL PIPELINE (Extract -> Transform in Python -> Load)
- Input rows: 100000
- Output rows: 100000
- Extraction time: 0.0234s
- Transformation time: 0.0156s
- Load time: 0.0089s
- Total time: 0.0479s

ELT PIPELINE (Extract -> Load -> Transform in SQL)
- Input rows: 100000
- Output rows: 100000
- Raw load time: 0.0145s
- SQL transformation time: 0.0098s
- Total time: 0.0243s
```

## Testing

### Run All Tests

```powershell
python tests/test_pipelines.py
```

### Tests Performed

1. ✓ Raw dataset exists and is valid
2. ✓ ETL output table created
3. ✓ ELT output table created
4. ✓ Row counts match between pipelines
5. ✓ All required columns present
6. ✓ total_amount calculated correctly
7. ✓ Legacy store codes normalized
8. ✓ No NULL values in key columns
9. ✓ Numeric columns contain valid data
10. ✓ Performance results recorded

## Data Lineage

### ETL Lineage

```
Raw CSV (retail_sales_raw.csv)
    ↓
Pandas DataFrame (in application memory)
    ↓
DuckDB retail_sales_clean table
```

**Lineage Characteristics**:

- Transformation data exists in application memory during processing
- No intermediate raw staging preserved in database
- Full dataset must be re-read if logic requires change

### ELT Lineage

```
Raw CSV (retail_sales_raw.csv)
    ↓
DuckDB staging_retail_sales table (RAW, preserved)
    ↓
DuckDB retail_sales_clean table (TRANSFORMED)
```

**Lineage Characteristics**:

- Raw data fully preserved in staging table
- Transformations tracked in SQL version control
- Can rerun transformations without re-extraction

## Bug Recovery

### ETL Recovery Example

**Scenario**: Transformation logic is incorrect

1. Identify bug in `etl/etl_pipeline.py`
2. Fix the Python code
3. **Delete or regenerate the DuckDB database** (raw data is in CSV)
4. Run ETL pipeline again
5. **Data must be re-extracted and re-transformed from CSV**

### ELT Recovery Example

**Scenario**: SQL transformation logic is incorrect

1. Identify bug in `elt/transform.sql`
2. Fix the SQL script
3. Run: `python elt/elt_pipeline.py`
4. **Raw staging data already in database, no CSV re-read needed**
5. Only SQL transformation is re-executed
6. Raw staging table preserved for verification

## Supplementary: dbt Implementation

The `dbt_project/` directory contains a modular refactoring of the ELT pipeline using dbt (Data Build Tool).

### dbt Project Structure

```
dbt_project/
├── dbt_project.yml          # Project configuration
├── profiles.yml             # DuckDB connection settings
├── schema.yml              # Model definitions and tests
├── models/
│   ├── staging/
│   │   └── stg_retail_sales.sql   # Staging transformations
│   └── marts/
│       └── retail_sales_clean.sql # Final mart transformations
```

### Key dbt Features Demonstrated

1. **Modular Models**: Staging models for data cleaning, marts for business logic
2. **Ref Dependencies**: Models reference each other with `{{ ref() }}`
3. **Source Definition**: Raw tables defined as sources with `{{ source() }}`
4. **Automated Tests**: Column-level tests (not_null, unique, accepted_values)
5. **Schema Documentation**: Comprehensive column descriptions

### Prerequisites for dbt

dbt requires Python 3.7+ and the DuckDB adapter:

```powershell
pip install dbt-duckdb
```

### Running dbt

```powershell
cd dbt_project

# Install dependencies
dbt deps

# Parse project
dbt parse

# Run models
dbt run

# Test models
dbt test

# Generate documentation
dbt docs generate
dbt docs serve
```

### dbt Results

Models will be created in the same DuckDB database:

- `staging.stg_retail_sales`: Staging model
- `marts.retail_sales_clean`: Final transformed data

### Important Notes

- dbt is **supplementary** to the main practical
- The main ETL/ELT pipelines work independently of dbt
- dbt tests are **schema-level assertions**, not row-level validations
- dbt configuration example provided in `profiles.yml`

## Key Insights & Analysis

### Performance Differences

In a **local DuckDB environment**:

- ETL and ELT perform similarly
- No network overhead between application and database
- Both benefit from local SSD storage

In a **cloud environment**:

- **ELT typically advantages**: Reduced data movement, database-native transformations
- **ETL typically disadvantages**: All transformation data traverses network between compute and storage
- **Cost differences**: Computation location affects resource consumption

### Data Lineage & Governance

| Aspect                  | ETL                  | ELT                     |
| ----------------------- | -------------------- | ----------------------- |
| Raw data preservation   | CSV file only        | Staged in database      |
| Transformation location | Application code     | SQL scripts             |
| Lineage complexity      | Simple but opaque    | Complex but traceable   |
| Audit trail             | Code version control | SQL + schema versioning |

### Maintainability

| Aspect                        | ETL                            | ELT                               |
| ----------------------------- | ------------------------------ | --------------------------------- |
| Changing transformation logic | Requires code deployment       | Can modify SQL without deployment |
| Testing transformations       | Unit tests in application code | SQL schema tests                  |
| Debugging                     | Python debugger, logs          | SQL query analysis, staging data  |
| Error recovery                | Must re-read source data       | Can rerun SQL on staged data      |

### Scalability Considerations

| Scenario                 | Better Approach   | Reason                                             |
| ------------------------ | ----------------- | -------------------------------------------------- |
| Small datasets (< 1GB)   | Either works well | No significant difference                          |
| Large datasets (> 100GB) | ELT               | Database-native operations, no memory limits       |
| Complex transformations  | ETL               | Application-level languages offer more flexibility |
| Many transformations     | ELT               | Database can optimize query plans                  |
| Real-time requirements   | ETL               | Lower latency for small batches                    |
| Analytics workloads      | ELT               | Database optimizations for analytical queries      |

### Architecture Decision Framework

**Choose ETL when:**

- Dataset fits in application memory
- Transformations require complex logic (ML, custom algorithms)
- You need immediate error feedback during development
- Team strength is in application development
- Simple, single-hop transformations

**Choose ELT when:**

- Data volumes exceed application memory
- Storage and compute are decoupled (cloud architecture)
- Transformations are primarily SQL-based
- Data governance and lineage are critical
- You need easy recovery from transformation bugs
- Team strength is in SQL and data modeling

## Interpretation Guidelines

**Important**: Do NOT claim general truths from local benchmarks.

**Incorrect**:

> "ELT is always faster than ETL"

**Correct**:

> "In this local DuckDB experiment, ELT completed in 0.024 seconds while ETL took 0.048 seconds. The performance advantage may vary significantly with cloud infrastructure, larger datasets, or different transformation complexity. Network costs and data movement patterns differ between architectures, affecting cloud deployments differently than local environments."

## Troubleshooting

### Dataset Not Found

```
✗ Input file not found: C:\...\data\retail_sales_raw.csv
```

**Solution**:

```powershell
python data/generate_dataset.py
```

### DuckDB Connection Error

**Solution**: Ensure database directory exists:

```powershell
mkdir database
```

### Whitespace Issues in Output

Check that the CSV generator preserves spaces:

- Verify: `df.to_csv(..., quoting=1)` in `generate_dataset.py`
- Verify: `pd.read_csv()` does NOT strip whitespace automatically

### Test Failures

Run tests individually to debug:

```powershell
python -c "from tests.test_pipelines import test_raw_dataset_exists; test_raw_dataset_exists()"
```

## Expected Output Files

After running both pipelines:

```
results/performance_results.csv
├─ Row 1: ETL run 1
├─ Row 2: ELT run 1
├─ Row 3: ETL run 2 (if re-run)
└─ Row 4: ELT run 2 (if re-run)

output/
├─ etl_output.csv (if --export used)
└─ elt_output.csv (if --export used)

database/
└─ retail_sales.duckdb (contains multiple tables)
    ├─ retail_sales_clean (final output from both pipelines)
    └─ staging_retail_sales (ELT raw staging table)
```

## Installation & Setup

### Prerequisites

- Python 3.8+
- Windows PowerShell or Command Prompt
- ~500MB disk space (database + dataset + outputs)

### Install Dependencies

```powershell
cd "C:\College Studies\SEM 5\DE\Github Practicals\Practical 4"
pip install -r requirements.txt
```

### Verify Installation

```powershell
python -c "import pandas; import duckdb; print('✓ Dependencies installed')"
```

## Command Reference

Quick reference for common operations:

```powershell
# Setup
pip install -r requirements.txt

# Generate data
python data/generate_dataset.py

# Run ETL
python etl/etl_pipeline.py --export

# Run ELT
python elt/elt_pipeline.py --export

# Compare results
python benchmark/compare_results.py

# Run tests
python tests/test_pipelines.py

# Run dbt (if installed)
cd dbt_project && dbt run && dbt test
```

## Summary

This practical demonstrates:

1. **Two data pipeline architectures**: ETL (traditional) vs ELT (modern)
2. **Implementation complexity**: Both require careful design and testing
3. **Performance characteristics**: Vary based on infrastructure and data volume
4. **Architectural trade-offs**: Lineage, maintainability, scalability, cost
5. **Real-world decision making**: Architecture choice depends on context

The key takeaway: **There is no universally "better" approach**—success depends on understanding your infrastructure, data volumes, team capabilities, and maintenance requirements.

## References

- DuckDB Documentation: https://duckdb.org/docs/
- Pandas Documentation: https://pandas.pydata.org/docs/
- dbt Documentation: https://docs.getdbt.com/
- Modern Data Warehousing: https://www.fivetran.com/blog/etl-elt-differences

---

**Author**: Data Engineering Practical 4  
**Date**: 2026  
**Institution**: University Computer Science Program  
**Semester**: 5th Semester
