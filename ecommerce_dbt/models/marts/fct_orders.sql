with orders as (
    select * from {{ ref('stg_orders') }}
),

customers as (
    select * from {{ ref('stg_customers') }}
),

products as (
    select * from {{ ref('stg_products') }}
),

joined as (
    select
        o.order_id,
        o.customer_id,
        c.customer_name,
        c.email as customer_email,
        c.city as customer_city,
        c.signup_date as customer_signup_date,
        o.product_id,
        p.product_name,
        p.category as product_category,
        p.price as unit_price,
        o.quantity,
        o.order_date,
        o.raw_order_status,
        o.order_status,
        -- Gross order revenue: theoretical total value of the order
        round(o.quantity * p.price, 2) as gross_revenue,
        -- Recognized revenue: earned revenue only for completed orders (0.00 for pending/cancelled)
        case
            when o.order_status = 'completed' then round(o.quantity * p.price, 2)
            else 0.00
        end as recognized_revenue,
        (o.order_status = 'completed') as is_completed,
        current_timestamp() as dbt_updated_at
    from orders o
    inner join customers c on o.customer_id = c.customer_id
    inner join products p on o.product_id = p.product_id
)

select * from joined
