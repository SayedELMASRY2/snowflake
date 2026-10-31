-- Singular test: Assert that pending and cancelled orders contribute exactly zero recognized revenue.
-- Returns records violating this accounting constraint.

select
    order_id,
    order_status,
    recognized_revenue
from {{ ref('fct_orders') }}
where order_status in ('pending', 'cancelled')
  and recognized_revenue != 0
