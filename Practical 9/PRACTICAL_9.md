# Practical 9: Data Modeling for Analytics

## Aim / Problem Definition
To design and implement a Kimball Star Schema for an e-commerce transactional dataset (50,000 order line items) using DuckDB, SQL DDL, and surrogate keys. To define the fact table grain, organize denormalized dimensional tables around a central fact table, and implement a supplementary normalized Snowflake schema to evaluate trade-offs in storage footprint and multi-table join performance.

## Tools / Technologies
- Python 3.13
- DuckDB (in-memory analytical database)
- SQL DDL / DML
- Mermaid / dbdiagram.io syntax for Entity-Relationship Diagrams (ERD)

## Step-by-Step
1. **Profile Transactional Workload**: Ingest 50,000 raw transactional order items containing timestamps, customer details, product categories, store locations, pricing, discounts, and order IDs.
2. **Declare Grain**: Explicitly establish the fact table grain as: *one row per individual line-item in an order*.
3. **Design Kimball Star Schema**:
   - Create surrogate keys (`customer_key`, `product_key`, `store_key`, `date_key`) using integer sequences.
   - Denormalize descriptive context into 4 dimension tables: `star_dim_date`, `star_dim_customer`, `star_dim_product`, `star_dim_store`.
   - Build central fact table `star_fact_sales` containing foreign keys and additive numeric measures (`quantity`, `unit_price`, `discount_amount`, `total_amount`).
4. **Build Supplementary Snowflake Schema**:
   - Normalize product hierarchy into: `snow_dim_product` -> `snow_dim_subcategory` -> `snow_dim_category`.
   - Normalize store hierarchy into: `snow_dim_store` -> `snow_dim_city` -> `snow_dim_country`.
5. **Analytical Query & Performance Evaluation**: Run an aggregation query (Total Revenue & Units Sold by Product Category and Country) on both models, measuring query runtime and verifying identical analytical output.
6. **Generate ERD Diagrams**: Export Mermaid ERD diagrams and SQL DDL schemas for both designs.

## Output
### Model Architecture & Performance Comparison:
| Feature / Metric | Kimball Star Schema | Snowflake Schema |
| :--- | :--- | :--- |
| **Fact Table Grain** | One record per order line item | One record per order line item |
| **Number of Tables** | 5 tables (1 Fact, 4 Dims) | 9 tables (1 Fact, 8 Normalized Dims) |
| **Total Model Columns** | 32 columns | 40 columns |
| **Joins in Analytical Query** | **2 joins** | **6 joins** |
| **Query Runtime** | **15.59 ms** | **14.70 ms** |
| **Normalization Level** | Denormalized (1NF/2NF Dims) | Highly Normalized (3NF) |
| **Storage & Redundancy** | Low redundancy; simpler queries | Zero redundancy; complex foreign key chains |

- Logical Equivalence: Analytical outputs match with 100% precision.
- ERD Diagrams exported to `results/star_schema_erd.md` and `results/snowflake_schema_erd.md`.

## Key Questions

### 1. Why are surrogate keys preferred over natural operational keys in dimensional modeling?
Natural keys (such as `customer_id` or `email`) can change over time in source operational systems, get reassigned, or contain messy alphanumeric formatting. Surrogate keys (simple auto-incrementing integers) insulate the data warehouse from operational source changes, improve join performance through compact integer indexing, and enable tracking history via Slowly Changing Dimensions (SCD Type 2).

### 2. Under what business conditions is a Snowflake schema preferred over a Star schema?
A Snowflake schema is preferred when dimension tables have deep, frequently changing hierarchical structures where storage space and update anomalies are a critical concern (e.g., massive product catalogs with thousands of shared subcategories, or master data management systems with strict 3NF normalization rules). However, for analytical querying, Star schema remains the industry standard due to query simplicity and faster performance.

### 3. How do you handle Slowly Changing Dimensions (SCD) in analytical models?
- **SCD Type 1**: Overwrite old attribute values with new values (no history preserved).
- **SCD Type 2**: Insert a new record with a new surrogate key, including `valid_from`, `valid_to`, and `is_current` timestamp flags to preserve full historical accuracy.
- **SCD Type 3**: Add a `previous_value` column to track only the immediate prior state.

## Supplementary Problem: Snowflake Schema Hierarchy Normalization
**Requirement**: Build the supplementary Snowflake version by normalizing a suitable hierarchy, and compare storage size and query runtime.

**Implementation & Result**:
- Successfully normalized:
  1. Product hierarchy: `Product` (10 rows) -> `Subcategory` (8 rows) -> `Category` (3 rows).
  2. Geographic hierarchy: `Store` (5 rows) -> `City` (5 rows) -> `Country` (2 rows).
- Analytical query required **6 joins** in Snowflake versus only **2 joins** in Star schema.
- **Result**: Star schema eliminated multi-hop join complexity, making SQL queries significantly simpler to write and maintain for business analysts.

## Conclusion
Practical 9 demonstrated the implementation of dimensional modeling using DuckDB. The Kimball Star Schema simplifies query construction, minimizes join paths, and optimizes analytical reporting. While the Snowflake schema eliminates dimensional attribute redundancy, the Star schema provides a vastly superior user experience for business intelligence and reporting tools.

## Screenshot List
- **Screenshot 1 – Dataset Ingestion & Star Schema Creation**: Terminal output showing 50,000 transactions loaded and star tables created.  
  *Where to place it*: Under Step-by-Step section.
- **Screenshot 2 – Star Schema ERD Diagram**: Mermaid diagram of Star Schema (`results/star_schema_erd.md`).  
  *Where to place it*: Under Output section.
- **Screenshot 3 – Snowflake Schema ERD Diagram**: Mermaid diagram of Snowflake Schema (`results/snowflake_schema_erd.md`).  
  *Where to place it*: Under Supplementary Problem section.
- **Screenshot 4 – Analytical Join Comparison**: Terminal table comparing Star vs Snowflake query execution and table structures.  
  *Where to place it*: Under Output section.
