
  
    
    

    create  table
      "lakehouse"."main"."dim_stores__dbt_tmp"
  
    as (
      ﻿select distinct
    store_id
from "lakehouse"."main"."stg_sales"
    );
  
  