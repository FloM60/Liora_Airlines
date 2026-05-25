WITH final AS (
  SELECT
    *,
    {{ is_weekend('day_of_week') }} AS is_weekend,
    {{ is_delayed('arr_delay') }} AS is_delayed,

    concat(origin_id_city, '_', dest_id_city) as route_code

  FROM {{ ref('ImportDB') }}
)

SELECT * FROM final
