with source as (
    select * from {{ source('raw', 'orders') }}
),

customers as (
    select customer_id from {{ ref('stg_customers') }}
),

products as (
    select product_id from {{ ref('stg_products') }}
),

ranked as (
    select
        order_id,
        customer_id,
        product_id,
        quantity as raw_quantity,
        order_date,
        status as raw_status,
        try_to_number(quantity::varchar) as parsed_qty,
        row_number() over (partition by order_id order by order_date asc) as rn
    from source
),

flagged as (
    select
        r.order_id,
        r.customer_id,
        r.product_id,
        r.raw_quantity,
        r.order_date,
        r.raw_status,
        case
            when r.rn > 1 then 'DUPLICATE_ORDER_ID'
            when r.raw_quantity is null or trim(r.raw_quantity::varchar) = '' then 'NULL_QUANTITY'
            when r.parsed_qty is null then 'NON_NUMERIC_QUANTITY'
            when r.parsed_qty <= 0 then 'NON_POSITIVE_QUANTITY'
            when c.customer_id is null then 'ORPHAN_CUSTOMER_REFERENCE'
            when p.product_id is null then 'ORPHAN_PRODUCT_REFERENCE'
            when lower(trim(r.raw_status)) not in ('completed', 'shipped', 'pending', 'cancelled') then 'INVALID_STATUS'
            else null
        end as rejection_reason
    from ranked r
    left join customers c on try_to_number(r.customer_id::varchar) = c.customer_id
    left join products p on try_to_number(r.product_id::varchar) = p.product_id
)

select *
from flagged
where rejection_reason is not null
