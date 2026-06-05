
      update "lakehouse"."main"."snp_products" as DBT_INTERNAL_TARGET
    set dbt_valid_to = DBT_INTERNAL_SOURCE.dbt_valid_to
    from "snp_products__dbt_tmp20260605070929661772" as DBT_INTERNAL_SOURCE
    where DBT_INTERNAL_SOURCE.dbt_scd_id::text = DBT_INTERNAL_TARGET.dbt_scd_id::text
      and DBT_INTERNAL_SOURCE.dbt_change_type::text in ('update'::text, 'delete'::text)
      
        and DBT_INTERNAL_TARGET.dbt_valid_to is null;
      

    insert into "lakehouse"."main"."snp_products" ("product_id", "product_name", "category", "unit_cost", "_ingested_at", "_source_file", "_load_id", "_ingestion_status", "year", "month", "day", "dbt_updated_at", "dbt_valid_from", "dbt_valid_to", "dbt_scd_id")
    select DBT_INTERNAL_SOURCE."product_id",DBT_INTERNAL_SOURCE."product_name",DBT_INTERNAL_SOURCE."category",DBT_INTERNAL_SOURCE."unit_cost",DBT_INTERNAL_SOURCE."_ingested_at",DBT_INTERNAL_SOURCE."_source_file",DBT_INTERNAL_SOURCE."_load_id",DBT_INTERNAL_SOURCE."_ingestion_status",DBT_INTERNAL_SOURCE."year",DBT_INTERNAL_SOURCE."month",DBT_INTERNAL_SOURCE."day",DBT_INTERNAL_SOURCE."dbt_updated_at",DBT_INTERNAL_SOURCE."dbt_valid_from",DBT_INTERNAL_SOURCE."dbt_valid_to",DBT_INTERNAL_SOURCE."dbt_scd_id"
    from "snp_products__dbt_tmp20260605070929661772" as DBT_INTERNAL_SOURCE
    where DBT_INTERNAL_SOURCE.dbt_change_type::text = 'insert'::text;


  