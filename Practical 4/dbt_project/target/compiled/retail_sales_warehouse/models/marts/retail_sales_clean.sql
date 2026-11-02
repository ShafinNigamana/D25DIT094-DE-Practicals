-- Mart model: Final transformed retail sales data
-- This model applies final business logic transformations



SELECT
    transaction_id,
    transaction_date,
    CASE
        WHEN store_code_raw LIKE 'LEG%'
        THEN 'STORE_' || SUBSTR(store_code_raw, 4)
        ELSE store_code_raw
    END AS store_code,
    product_id,
    quantity,
    unit_price,
    customer_id,
    payment_method,
    CAST(quantity AS DECIMAL(10, 2)) * unit_price AS total_amount
FROM "retail_sales"."main_staging"."stg_retail_sales"