
      
  
    
    

    create  table
      "lakehouse"."main"."snp_products"
  
    as (
      
    

    select *,
        md5(coalesce(cast(product_id as varchar ), '')
         || '|' || coalesce(cast(now()::timestamp as varchar ), '')
        ) as dbt_scd_id,
        now()::timestamp as dbt_updated_at,
        now()::timestamp as dbt_valid_from,
        
  
  coalesce(nullif(now()::timestamp, now()::timestamp), null)
  as dbt_valid_to
from (
        



select * from "lakehouse"."main"."stg_products"

    ) sbq



    );
  
  
  