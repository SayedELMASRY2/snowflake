with source as (
    select * from {{ source('raw', 'customers') }}
),

cleaned as (
    select
        customer_id::integer as customer_id,
        trim(customer_name) as customer_name,
        lower(trim(nullif(email, ''))) as email,
        trim(nullif(city, '')) as city,
        signup_date::date as signup_date
    from source
    where customer_id is not null
)

select * from cleaned
