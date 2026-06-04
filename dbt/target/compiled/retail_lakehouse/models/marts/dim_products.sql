select
    product_id,
    product_name,
    category,
    unit_cost,
    dbt_valid_from as valid_from,
    dbt_valid_to as valid_to,
    case when dbt_valid_to is null then true else false end as is_current
from "lakehouse"."main"."snp_products"