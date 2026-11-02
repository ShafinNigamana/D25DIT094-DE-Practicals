
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
    