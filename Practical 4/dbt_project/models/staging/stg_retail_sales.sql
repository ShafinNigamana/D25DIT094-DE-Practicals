-- Staging model: Clean raw retail sales data
-- This model applies basic transformations to staging_retail_sales

{{ config(
    materialized='table',
    schema='staging'
) }}

SELECT
    TRIM(transaction_id) AS transaction_id,
    transaction_date,
    TRIM(store_code) AS store_code_raw,
    TRIM(product_id) AS product_id,
    CAST(TRIM(quantity) AS INTEGER) AS quantity,
    CAST(TRIM(unit_price) AS DECIMAL(10, 2)) AS unit_price,
    TRIM(customer_id) AS customer_id,
    LOWER(TRIM(payment_method)) AS payment_method
FROM {{ source('raw', 'staging_retail_sales') }}
