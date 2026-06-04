
  
    
    

    create  table
      "lakehouse"."main"."fact_sales__dbt_tmp"
  
    as (
      ﻿select
    sale_id,
    sale_date,
    customer_id,
    product_id,
    store_id,
    quantity,
    unit_price,
    quantity * unit_price as revenue
from "lakehouse"."main"."stg_sales"
    );
  
  