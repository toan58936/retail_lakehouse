
  
  create view "lakehouse"."main"."stg_sales__dbt_tmp" as (
    select *
from '../data/silver/sales.parquet'
  );
