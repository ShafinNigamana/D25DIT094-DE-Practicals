
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select store_code_raw
from "retail_sales"."main_staging"."stg_retail_sales"
where store_code_raw is null



  
  
      
    ) dbt_internal_test