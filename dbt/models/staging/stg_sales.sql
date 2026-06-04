select *
from {{ source('silver_source', 'sales') }}