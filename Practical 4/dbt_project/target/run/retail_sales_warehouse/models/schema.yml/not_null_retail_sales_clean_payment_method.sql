
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select payment_method
from "retail_sales"."main_marts"."retail_sales_clean"
where payment_method is null



  
  
      
    ) dbt_internal_test