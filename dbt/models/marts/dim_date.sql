select distinct
    sale_date::date as date_key,
    sale_date::date as sale_date,
    year(sale_date::date) as year,
    month(sale_date::date) as month,
    quarter(sale_date::date) as quarter,
    dayofweek(sale_date::date) as day_of_week,
    dayname(sale_date::date) as day_name,
    monthname(sale_date::date) as month_name
from {{ ref('stg_sales') }}
order by date_key
