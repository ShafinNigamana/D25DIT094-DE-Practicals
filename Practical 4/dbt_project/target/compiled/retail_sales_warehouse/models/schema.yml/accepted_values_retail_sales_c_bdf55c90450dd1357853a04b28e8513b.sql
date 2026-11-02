
    
    

with all_values as (

    select
        store_code as value_field,
        count(*) as n_records

    from "retail_sales"."main_marts"."retail_sales_clean"
    group by store_code

)

select *
from all_values
where value_field not in (
    'STORE_001','STORE_002','STORE_003','STORE_004','STORE_005','STORE_006','STORE_007','STORE_008','STORE_009','STORE_010'
)


