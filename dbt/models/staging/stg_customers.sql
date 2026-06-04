select *
from {{ source('silver_source', 'customers') }}