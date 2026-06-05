
  
  create view "lakehouse"."main"."stg_customers__dbt_tmp" as (
    select *
from '../data/silver/customers.parquet'
  );
