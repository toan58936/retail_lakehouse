{% snapshot snp_products %}

{{
    config(
      target_database='lakehouse',
      target_schema='main',
      unique_key='product_id',
      strategy='check',
      check_cols=['product_name', 'category', 'unit_cost'],
    )
}}

select * from {{ ref('stg_products') }}

{% endsnapshot %}
