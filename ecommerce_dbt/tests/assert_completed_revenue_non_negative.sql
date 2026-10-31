-- Singular test: Assert that completed order revenue is never negative.
-- Returns records that violate the business rule (test fails if any rows returned).

select
    order_id,
    order_status,
    recognized_revenue
from {{ ref('fct_orders') }}
where order_status = 'completed'
  and recognized_revenue < 0
