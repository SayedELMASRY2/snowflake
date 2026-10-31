-- Singular test: Assert that order quantities are strictly positive (> 0).
-- Returns records violating this business rule (test fails if any rows returned).

select
    order_id,
    customer_id,
    product_id,
    quantity
from {{ ref('stg_orders') }}
where quantity <= 0 or quantity is null
