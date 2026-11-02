
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select quantity
from "retail_sales"."main_staging"."stg_retail_sales"
where quantity is null



  
  
      
    ) dbt_internal_test