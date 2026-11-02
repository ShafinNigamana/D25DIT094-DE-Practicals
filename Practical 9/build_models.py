"""
build_models.py
Practical 9: Data Modeling for Analytics
Implements Kimball Star Schema and Snowflake Schema in DuckDB,
compares storage size and join performance, and exports ERD specifications.
"""

import os
import time
import duckdb
import pandas as pd

def build_data_models():
    csv_file = "raw_transactions.csv"
    if not os.path.exists(csv_file):
        from generate_transactional_data import generate_transactions
        generate_transactions(csv_file, num_records=50000)
        
    os.makedirs("results", exist_ok=True)
    os.makedirs("sql", exist_ok=True)
    
    print("\n==================================================")
    print("PRACTICAL 9: DATA MODELING FOR ANALYTICS")
    print("==================================================")
    
    con = duckdb.connect(database=":memory:")
    
    print(f"\n1. Ingesting raw transactional data ({csv_file})...")
    con.execute(f"CREATE TABLE raw_transactions AS SELECT * FROM read_csv_auto('{csv_file}')")
    raw_count = con.execute("SELECT COUNT(*) FROM raw_transactions").fetchone()[0]
    print(f"[OK] Ingested {raw_count:,} raw transactional records.")
    
    # -------------------------------------------------------------------------
    # PART A: KIMBALL STAR SCHEMA IMPLEMENTATION
    # -------------------------------------------------------------------------
    print("\n--------------------------------------------------")
    print("PART A: Building Kimball Star Schema")
    print("Grain: One row per order line-item")
    print("--------------------------------------------------")
    
    star_ddl = """
    -- 1. Date Dimension
    CREATE TABLE star_dim_date AS
    SELECT DISTINCT
        CAST(strftime(CAST(order_date AS DATE), '%Y%m%d') AS INTEGER) AS date_key,
        CAST(order_date AS DATE) AS full_date,
        EXTRACT(YEAR FROM CAST(order_date AS DATE)) AS year,
        EXTRACT(QUARTER FROM CAST(order_date AS DATE)) AS quarter,
        EXTRACT(MONTH FROM CAST(order_date AS DATE)) AS month,
        strftime(CAST(order_date AS DATE), '%A') AS day_name
    FROM raw_transactions;

    -- 2. Customer Dimension (with Surrogate Key)
    CREATE TABLE star_dim_customer AS
    SELECT 
        ROW_NUMBER() OVER (ORDER BY customer_id) AS customer_key,
        customer_id,
        customer_name,
        customer_segment,
        customer_city,
        customer_country
    FROM (
        SELECT DISTINCT customer_id, customer_name, customer_segment, customer_city, customer_country
        FROM raw_transactions
    );

    -- 3. Product Dimension (with Surrogate Key)
    CREATE TABLE star_dim_product AS
    SELECT 
        ROW_NUMBER() OVER (ORDER BY product_id) AS product_key,
        product_id,
        product_name,
        product_subcategory,
        product_category
    FROM (
        SELECT DISTINCT product_id, product_name, product_subcategory, product_category
        FROM raw_transactions
    );

    -- 4. Store Dimension (with Surrogate Key)
    CREATE TABLE star_dim_store AS
    SELECT 
        ROW_NUMBER() OVER (ORDER BY store_id) AS store_key,
        store_id,
        store_name,
        store_city,
        store_country
    FROM (
        SELECT DISTINCT store_id, store_name, store_city, store_country
        FROM raw_transactions
    );

    -- 5. Fact Sales (Central Fact Table)
    CREATE TABLE star_fact_sales AS
    SELECT 
        r.line_item_id AS sales_key,
        d.date_key,
        c.customer_key,
        p.product_key,
        s.store_key,
        r.order_id,
        r.quantity,
        r.unit_price,
        r.discount_amount,
        r.total_amount
    FROM raw_transactions r
    JOIN star_dim_date d ON CAST(r.order_date AS DATE) = d.full_date
    JOIN star_dim_customer c ON r.customer_id = c.customer_id
    JOIN star_dim_product p ON r.product_id = p.product_id
    JOIN star_dim_store s ON r.store_id = s.store_id;
    """
    
    con.execute(star_ddl)
    with open("sql/star_schema_ddl.sql", "w", encoding="utf-8") as f:
        f.write(star_ddl)
        
    print("[OK] Star Schema created:")
    for tbl in ["star_dim_date", "star_dim_customer", "star_dim_product", "star_dim_store", "star_fact_sales"]:
        cnt = con.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
        print(f"  - {tbl}: {cnt:,} rows")
        
    # -------------------------------------------------------------------------
    # PART B: SUPPLEMENTARY SNOWFLAKE SCHEMA IMPLEMENTATION
    # -------------------------------------------------------------------------
    print("\n--------------------------------------------------")
    print("PART B: Building Supplementary Snowflake Schema")
    print("Normalized hierarchies: Product -> Subcategory -> Category")
    print("                       Store -> City -> Country")
    print("--------------------------------------------------")
    
    snow_ddl = """
    -- 1. Category Dimension (Normalized)
    CREATE TABLE snow_dim_category AS
    SELECT 
        ROW_NUMBER() OVER (ORDER BY product_category) AS category_key,
        product_category AS category_name
    FROM (SELECT DISTINCT product_category FROM raw_transactions);

    -- 2. Subcategory Dimension (FK to Category)
    CREATE TABLE snow_dim_subcategory AS
    SELECT 
        ROW_NUMBER() OVER (ORDER BY s.product_subcategory) AS subcategory_key,
        s.product_subcategory AS subcategory_name,
        c.category_key
    FROM (SELECT DISTINCT product_subcategory, product_category FROM raw_transactions) s
    JOIN snow_dim_category c ON s.product_category = c.category_name;

    -- 3. Product Dimension (FK to Subcategory)
    CREATE TABLE snow_dim_product AS
    SELECT 
        ROW_NUMBER() OVER (ORDER BY p.product_id) AS product_key,
        p.product_id,
        p.product_name,
        sub.subcategory_key
    FROM (SELECT DISTINCT product_id, product_name, product_subcategory FROM raw_transactions) p
    JOIN snow_dim_subcategory sub ON p.product_subcategory = sub.subcategory_name;

    -- 4. Country Dimension
    CREATE TABLE snow_dim_country AS
    SELECT 
        ROW_NUMBER() OVER (ORDER BY store_country) AS country_key,
        store_country AS country_name
    FROM (SELECT DISTINCT store_country FROM raw_transactions);

    -- 5. City Dimension (FK to Country)
    CREATE TABLE snow_dim_city AS
    SELECT 
        ROW_NUMBER() OVER (ORDER BY s.store_city) AS city_key,
        s.store_city AS city_name,
        co.country_key
    FROM (SELECT DISTINCT store_city, store_country FROM raw_transactions) s
    JOIN snow_dim_country co ON s.store_country = co.country_name;

    -- 6. Store Dimension (FK to City)
    CREATE TABLE snow_dim_store AS
    SELECT 
        ROW_NUMBER() OVER (ORDER BY s.store_id) AS store_key,
        s.store_id,
        s.store_name,
        ci.city_key
    FROM (SELECT DISTINCT store_id, store_name, store_city FROM raw_transactions) s
    JOIN snow_dim_city ci ON s.store_city = ci.city_name;

    -- 7. Fact Sales for Snowflake
    CREATE TABLE snow_fact_sales AS
    SELECT 
        sales_key,
        date_key,
        customer_key,
        product_key,
        store_key,
        order_id,
        quantity,
        unit_price,
        discount_amount,
        total_amount
    FROM star_fact_sales;
    """
    
    con.execute(snow_ddl)
    with open("sql/snowflake_schema_ddl.sql", "w", encoding="utf-8") as f:
        f.write(snow_ddl)
        
    print("[OK] Snowflake Schema created:")
    for tbl in ["snow_dim_category", "snow_dim_subcategory", "snow_dim_product", "snow_dim_country", "snow_dim_city", "snow_dim_store", "snow_fact_sales"]:
        cnt = con.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
        print(f"  - {tbl}: {cnt:,} rows")
        
    # -------------------------------------------------------------------------
    # PART C: ANALYTICAL QUERY BENCHMARK & COMPARISON
    # -------------------------------------------------------------------------
    print("\n--------------------------------------------------")
    print("PART C: Analytical Join & Storage Performance Comparison")
    print("Query: Aggregate Revenue & Units Sold by Category and Store Country")
    print("--------------------------------------------------")
    
    # Star Query (Fewer joins: Fact -> Dim Product -> Dim Store)
    star_query = """
    SELECT 
        p.product_category,
        s.store_country,
        COUNT(*) AS total_orders,
        SUM(f.quantity) AS total_units_sold,
        ROUND(SUM(f.total_amount), 2) AS total_revenue
    FROM star_fact_sales f
    JOIN star_dim_product p ON f.product_key = p.product_key
    JOIN star_dim_store s ON f.store_key = s.store_key
    GROUP BY p.product_category, s.store_country
    ORDER BY total_revenue DESC;
    """
    
    # Snowflake Query (More joins due to normalization: Fact -> Product -> Subcategory -> Category -> Store -> City -> Country)
    snow_query = """
    SELECT 
        cat.category_name AS product_category,
        co.country_name AS store_country,
        COUNT(*) AS total_orders,
        SUM(f.quantity) AS total_units_sold,
        ROUND(SUM(f.total_amount), 2) AS total_revenue
    FROM snow_fact_sales f
    JOIN snow_dim_product p ON f.product_key = p.product_key
    JOIN snow_dim_subcategory sub ON p.subcategory_key = sub.subcategory_key
    JOIN snow_dim_category cat ON sub.category_key = cat.category_key
    JOIN snow_dim_store s ON f.store_key = s.store_key
    JOIN snow_dim_city ci ON s.city_key = ci.city_key
    JOIN snow_dim_country co ON ci.country_key = co.country_key
    GROUP BY cat.category_name, co.country_name
    ORDER BY total_revenue DESC;
    """
    
    # Measure Star Schema Query Time
    t0 = time.time()
    res_star = con.execute(star_query).fetchdf()
    t_star = (time.time() - t0) * 1000
    
    # Measure Snowflake Schema Query Time
    t0 = time.time()
    res_snow = con.execute(snow_query).fetchdf()
    t_snow = (time.time() - t0) * 1000
    
    print(f"  -> Star Schema Query Time:      {t_star:.2f} ms (2 joins)")
    print(f"  -> Snowflake Schema Query Time: {t_snow:.2f} ms (6 joins)")
    print(f"  -> Performance Advantage:       Star is {t_snow / t_star:.2f}x faster due to fewer joins")
    
    # Assert logical equivalence
    pd.testing.assert_frame_equal(res_star, res_snow)
    print("  [OK] Analytical results are logically IDENTICAL between Star and Snowflake models.")
    
    # Storage Size Calculation (estimated column storage footprint)
    star_tables = ["star_dim_date", "star_dim_customer", "star_dim_product", "star_dim_store", "star_fact_sales"]
    snow_tables = ["star_dim_date", "star_dim_customer", "snow_dim_category", "snow_dim_subcategory", "snow_dim_product", "snow_dim_country", "snow_dim_city", "snow_dim_store", "snow_fact_sales"]
    
    star_col_count = sum([len(con.execute(f"DESCRIBE {t}").fetchall()) for t in star_tables])
    snow_col_count = sum([len(con.execute(f"DESCRIBE {t}").fetchall()) for t in snow_tables])
    
    comparison_df = pd.DataFrame([
        {
            "Model": "Kimball Star Schema",
            "Table Count": len(star_tables),
            "Total Columns": star_col_count,
            "Joins in Report Query": 2,
            "Query Runtime (ms)": round(t_star, 2),
            "Normalization Level": "Denormalized dimensions (3NF Fact, 2NF/1NF Dims)",
            "Storage & Redundancy": "Slightly higher attribute redundancy; simpler structure"
        },
        {
            "Model": "Snowflake Schema",
            "Table Count": len(snow_tables),
            "Total Columns": snow_col_count,
            "Joins in Report Query": 6,
            "Query Runtime (ms)": round(t_snow, 2),
            "Normalization Level": "Fully normalized dimensions (3NF)",
            "Storage & Redundancy": "Zero attribute redundancy; complex multi-hop joins"
        }
    ])
    
    comparison_df.to_csv("results/schema_comparison.csv", index=False)
    print("\nComparison saved to results/schema_comparison.csv")
    print(comparison_df.to_string(index=False))
    
    # -------------------------------------------------------------------------
    # PART D: EXPORT ERD SPECIFICATIONS (Mermaid & dbdiagram.io)
    # -------------------------------------------------------------------------
    mermaid_star = """```mermaid
erDiagram
    STAR_FACT_SALES ||--o{ STAR_DIM_DATE : "occurs_on (date_key)"
    STAR_FACT_SALES ||--o{ STAR_DIM_CUSTOMER : "purchased_by (customer_key)"
    STAR_FACT_SALES ||--o{ STAR_DIM_PRODUCT : "contains (product_key)"
    STAR_FACT_SALES ||--o{ STAR_DIM_STORE : "fulfilled_by (store_key)"

    STAR_FACT_SALES {
        int sales_key PK
        int date_key FK
        int customer_key FK
        int product_key FK
        int store_key FK
        string order_id
        int quantity
        float unit_price
        float discount_amount
        float total_amount
    }

    STAR_DIM_DATE {
        int date_key PK
        date full_date
        int year
        int quarter
        int month
        string day_name
    }

    STAR_DIM_CUSTOMER {
        int customer_key PK
        string customer_id
        string customer_name
        string customer_segment
        string customer_city
        string customer_country
    }

    STAR_DIM_PRODUCT {
        int product_key PK
        string product_id
        string product_name
        string product_subcategory
        string product_category
    }

    STAR_DIM_STORE {
        int store_key PK
        string store_id
        string store_name
        string store_city
        string store_country
    }
```"""

    mermaid_snow = """```mermaid
erDiagram
    SNOW_FACT_SALES ||--o{ STAR_DIM_DATE : "date_key"
    SNOW_FACT_SALES ||--o{ STAR_DIM_CUSTOMER : "customer_key"
    SNOW_FACT_SALES ||--o{ SNOW_DIM_PRODUCT : "product_key"
    SNOW_FACT_SALES ||--o{ SNOW_DIM_STORE : "store_key"

    SNOW_DIM_PRODUCT ||--o{ SNOW_DIM_SUBCATEGORY : "subcategory_key"
    SNOW_DIM_SUBCATEGORY ||--o{ SNOW_DIM_CATEGORY : "category_key"

    SNOW_DIM_STORE ||--o{ SNOW_DIM_CITY : "city_key"
    SNOW_DIM_CITY ||--o{ SNOW_DIM_COUNTRY : "country_key"

    SNOW_DIM_CATEGORY {
        int category_key PK
        string category_name
    }
    SNOW_DIM_SUBCATEGORY {
        int subcategory_key PK
        string subcategory_name
        int category_key FK
    }
    SNOW_DIM_PRODUCT {
        int product_key PK
        string product_id
        string product_name
        int subcategory_key FK
    }
    SNOW_DIM_COUNTRY {
        int country_key PK
        string country_name
    }
    SNOW_DIM_CITY {
        int city_key PK
        string city_name
        int country_key FK
    }
    SNOW_DIM_STORE {
        int store_key PK
        string store_id
        string store_name
        int city_key FK
    }
```"""

    with open("results/star_schema_erd.md", "w", encoding="utf-8") as f:
        f.write("# Kimball Star Schema ERD\n\n" + mermaid_star)
    with open("results/snowflake_schema_erd.md", "w", encoding="utf-8") as f:
        f.write("# Snowflake Schema ERD\n\n" + mermaid_snow)
        
    print("\n[OK] ERD specifications exported to results/star_schema_erd.md and snowflake_schema_erd.md")
    print("[OK] Practical 9 data modeling completed successfully.")
    con.close()

if __name__ == "__main__":
    build_data_models()
