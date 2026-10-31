-- Singular test: Assert that category mart recognized revenue equals fact table recognized revenue.
-- Returns row if absolute difference between fact and mart totals exceeds 0.01.

with fact_total as (
    select coalesce(round(sum(recognized_revenue), 2), 0) as fact_rev
    from {{ ref('fct_orders') }}
),

mart_total as (
    select coalesce(round(sum(total_recognized_revenue), 2), 0) as mart_rev
    from {{ ref('mart_category_sales') }}
)

select
    fact_total.fact_rev,
    mart_total.mart_rev,
    abs(fact_total.fact_rev - mart_total.mart_rev) as diff
from fact_total
cross join mart_total
where abs(fact_total.fact_rev - mart_total.mart_rev) > 0.01
