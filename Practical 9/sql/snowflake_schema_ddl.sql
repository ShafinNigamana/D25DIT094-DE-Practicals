
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
    