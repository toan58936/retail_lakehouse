
  
  create view "lakehouse"."main"."stg_products__dbt_tmp" as (
    select *
from 'D:/retail_lakehouse/data/sample_env/silver/products.parquet'
  );
