
  
  create view "lakehouse"."main"."stg_sales__dbt_tmp" as (
    select *
from 'D:/retail_lakehouse/data/sample_env/silver/sales.parquet'
  );
