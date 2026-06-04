
  
    
    

    create  table
      "lakehouse"."main"."dim_date__dbt_tmp"
  
    as (
      ﻿select distinct
    sale_date as date_key,
    sale_date,
    year(sale_date) as year,
    month(sale_date) as month,
    quarter(sale_date) as quarter,
    dayofweek(sale_date) as day_of_week,
    dayname(sale_date) as day_name,
    monthname(sale_date) as month_name
from "lakehouse"."main"."stg_sales"
order by date_key
    );
  
  