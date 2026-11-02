
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select total_amount
from "retail_sales"."main_marts"."retail_sales_clean"
where total_amount is null



  
  
      
    ) dbt_internal_test