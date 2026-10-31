with orders as (
    select * from {{ ref('fct_orders') }}
),

categories as (
    select distinct category from {{ ref('stg_products') }}
),

category_aggregates as (
    select
        product_category as category,
        count(order_id) as total_orders,
        count_if(order_status = 'completed') as completed_orders,
        count_if(order_status = 'pending') as pending_orders,
        count_if(order_status = 'cancelled') as cancelled_orders,
        coalesce(sum(recognized_revenue), 0.00) as total_recognized_revenue,
        coalesce(sum(gross_revenue), 0.00) as total_gross_revenue
    from orders
    group by product_category
),

final as (
    select
        c.category,
        coalesce(ca.total_orders, 0) as total_orders,
        coalesce(ca.completed_orders, 0) as completed_orders,
        coalesce(ca.pending_orders, 0) as pending_orders,
        coalesce(ca.cancelled_orders, 0) as cancelled_orders,
        coalesce(ca.total_recognized_revenue, 0.00) as total_recognized_revenue,
        coalesce(ca.total_gross_revenue, 0.00) as total_gross_revenue,
        current_timestamp() as dbt_updated_at
    from categories c
    left join category_aggregates ca on c.category = ca.category
)

select * from final
