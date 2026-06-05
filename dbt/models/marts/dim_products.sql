select
    product_id,
    product_name,
    category,
    unit_cost,
    now() as created_at
from {{ ref('stg_products') }}
