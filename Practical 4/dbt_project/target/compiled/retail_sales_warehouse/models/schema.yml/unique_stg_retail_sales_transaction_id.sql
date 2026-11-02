
    
    

select
    transaction_id as unique_field,
    count(*) as n_records

from "retail_sales"."main_staging"."stg_retail_sales"
where transaction_id is not null
group by transaction_id
having count(*) > 1


