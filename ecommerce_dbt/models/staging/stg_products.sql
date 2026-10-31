with source as (
    select * from {{ source('raw', 'products') }}
),

cleaned as (
    select
        product_id::integer as product_id,
        trim(product_name) as product_name,
        trim(category) as category,
        price::number(10, 2) as price
    from source
    where product_id is not null
      and price > 0
)

select * from cleaned
