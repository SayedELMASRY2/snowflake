with source as (
    select * from {{ source('raw', 'orders') }}
),

customers as (
    select customer_id from {{ ref('stg_customers') }}
),

products as (
    select product_id from {{ ref('stg_products') }}
),

ranked_orders as (
    select
        order_id::integer as order_id,
        customer_id::integer as customer_id,
        product_id::integer as product_id,
        try_to_number(quantity::varchar)::integer as quantity,
        order_date::date as order_date,
        lower(trim(status)) as raw_order_status,
        case
            when lower(trim(status)) in ('completed', 'shipped') then 'completed'
            when lower(trim(status)) = 'pending' then 'pending'
            when lower(trim(status)) = 'cancelled' then 'cancelled'
            else 'unknown'
        end as order_status,
        row_number() over (partition by order_id::integer order by order_date::date asc) as rn
    from source
    where order_id is not null
),

valid_orders as (
    select
        r.order_id,
        r.customer_id,
        r.product_id,
        r.quantity,
        r.order_date,
        r.raw_order_status,
        r.order_status
    from ranked_orders r
    inner join customers c on r.customer_id = c.customer_id
    inner join products p on r.product_id = p.product_id
    where r.rn = 1
      and r.quantity is not null
      and r.quantity > 0
      and r.order_status in ('completed', 'pending', 'cancelled')
)

select * from valid_orders
