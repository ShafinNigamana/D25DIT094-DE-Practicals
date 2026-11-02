
    
    

with child as (
    select transaction_id as from_field
    from "retail_sales"."main_marts"."retail_sales_clean"
    where transaction_id is not null
),

parent as (
    select transaction_id as to_field
    from "retail_sales"."main_staging"."stg_retail_sales"
)

select
    from_field

from child
left join parent
    on child.from_field = parent.to_field

where parent.to_field is null


