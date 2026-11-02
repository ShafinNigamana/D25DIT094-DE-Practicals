-- ELT Pipeline SQL Transformations
-- ===================================
--
-- This SQL script transforms data that has been loaded into the
-- staging_retail_sales table.
--
-- Transformation rules (same as ETL but implemented in SQL):
-- 1. transaction_id: trim whitespace
-- 2. transaction_date: keep as-is
-- 3. store_code: trim whitespace, normalize legacy codes (LEG*** -> STORE_***)
-- 4. product_id: trim whitespace
-- 5. customer_id: trim whitespace
-- 6. quantity: convert to integer
-- 7. unit_price: convert to float/decimal
-- 8. payment_method: trim whitespace, lowercase
-- 9. total_amount: calculate as quantity * unit_price
--
-- Output: retail_sales_clean table

-- Drop existing final table (for clean runs)
DROP TABLE IF EXISTS retail_sales_clean;

-- Create final cleaned table with transformations
CREATE TABLE retail_sales_clean AS
SELECT
    TRIM(transaction_id) AS transaction_id,
    transaction_date,
    CASE
        WHEN TRIM(store_code) LIKE 'LEG%'
        THEN 'STORE_' || SUBSTR(TRIM(store_code), 4)
        ELSE TRIM(store_code)
    END AS store_code,
    TRIM(product_id) AS product_id,
    CAST(TRIM(quantity) AS INTEGER) AS quantity,
    CAST(TRIM(unit_price) AS DECIMAL(10, 2)) AS unit_price,
    TRIM(customer_id) AS customer_id,
    LOWER(TRIM(payment_method)) AS payment_method,
    CAST(TRIM(quantity) AS INTEGER) * CAST(TRIM(unit_price) AS DECIMAL(10, 2)) AS total_amount
FROM staging_retail_sales;

-- Validation: Count records
SELECT COUNT(*) as final_record_count FROM retail_sales_clean;
