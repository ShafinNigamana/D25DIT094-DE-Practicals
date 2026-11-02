
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select transaction_id
from "retail_sales"."main_marts"."retail_sales_clean"
where transaction_id is null



  
  
      
    ) dbt_internal_test