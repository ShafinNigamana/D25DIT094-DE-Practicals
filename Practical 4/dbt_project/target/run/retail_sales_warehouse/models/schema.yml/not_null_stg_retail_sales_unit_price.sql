
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select unit_price
from "retail_sales"."main_staging"."stg_retail_sales"
where unit_price is null



  
  
      
    ) dbt_internal_test