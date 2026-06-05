select
    customer_id,
    customer_name,
    email,
    region,
    now() as created_at
from {{ ref('stg_customers') }}