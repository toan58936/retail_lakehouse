{% snapshot snp_customers %}

{{
    config(
      target_database='lakehouse',
      target_schema='main',
      unique_key='customer_id',
      strategy='check',
      check_cols=['customer_name', 'email', 'region'],
    )
}}

select * from {{ ref('stg_customers') }}

{% endsnapshot %}
