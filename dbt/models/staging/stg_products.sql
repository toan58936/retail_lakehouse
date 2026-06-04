select *
from {{ source('silver_source', 'products') }}