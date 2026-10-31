-- Singular test: Assert that product prices are strictly positive (> 0).
-- Returns records violating this business rule (test fails if any rows returned).

select
    product_id,
    product_name,
    price
from {{ ref('stg_products') }}
where price <= 0 or price is null
