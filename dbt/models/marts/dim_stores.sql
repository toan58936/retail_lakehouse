select distinct
    store_id
from {{ ref('stg_sales') }}
