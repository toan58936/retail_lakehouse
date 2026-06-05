
  
  create view "lakehouse"."main"."stg_products__dbt_tmp" as (
    select *
from '../data/silver/products.parquet'
  );
