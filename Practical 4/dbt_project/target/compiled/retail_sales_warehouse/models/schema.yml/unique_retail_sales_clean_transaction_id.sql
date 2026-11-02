
    
    

select
    transaction_id as unique_field,
    count(*) as n_records

from "retail_sales"."main_marts"."retail_sales_clean"
where transaction_id is not null
group by transaction_id
having count(*) > 1


