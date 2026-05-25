SELECT *
FROM {{ ref('gold_flights') }}
WHERE arr_delay > 15
AND is_delayed = FALSE