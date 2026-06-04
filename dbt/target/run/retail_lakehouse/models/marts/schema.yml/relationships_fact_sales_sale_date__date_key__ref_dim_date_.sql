
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

with child as (
    select sale_date as from_field
    from "lakehouse"."main"."fact_sales"
    where sale_date is not null
),

parent as (
    select date_key as to_field
    from "lakehouse"."main"."dim_date"
)

select
    from_field

from child
left join parent
    on child.from_field = parent.to_field

where parent.to_field is null



  
  
      
    ) dbt_internal_test