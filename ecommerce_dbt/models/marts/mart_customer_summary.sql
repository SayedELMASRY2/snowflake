with customers as (
    select * from {{ ref('stg_customers') }}
),

orders as (
    select * from {{ ref('fct_orders') }}
),

customer_orders as (
    select
        customer_id,
        count(order_id) as total_orders,
        count_if(order_status = 'completed') as completed_orders,
        coalesce(sum(recognized_revenue), 0.00) as total_recognized_spending,
        coalesce(sum(gross_revenue), 0.00) as total_gross_spending
    from orders
    group by customer_id
),

final as (
    select
        c.customer_id,
        c.customer_name,
        c.email,
        c.city,
        c.signup_date,
        coalesce(co.total_orders, 0) as total_orders,
        coalesce(co.completed_orders, 0) as completed_orders,
        coalesce(co.total_recognized_spending, 0.00) as total_recognized_spending,
        coalesce(co.total_gross_spending, 0.00) as total_gross_spending,
        current_timestamp() as dbt_updated_at
    from customers c
    left join customer_orders co on c.customer_id = co.customer_id
)

select * from final
