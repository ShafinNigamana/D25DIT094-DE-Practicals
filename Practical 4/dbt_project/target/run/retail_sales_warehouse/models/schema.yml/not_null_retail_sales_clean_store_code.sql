
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select store_code
from "retail_sales"."main_marts"."retail_sales_clean"
where store_code is null



  
  
      
    ) dbt_internal_test