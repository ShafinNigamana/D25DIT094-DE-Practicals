
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select unit_price
from "retail_sales"."main_marts"."retail_sales_clean"
where unit_price is null



  
  
      
    ) dbt_internal_test