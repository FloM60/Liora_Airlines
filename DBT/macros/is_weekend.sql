{% macro is_weekend(day_of_week) %}
    CASE
      WHEN {{day_of_week}} IN (6, 7) THEN TRUE
      ELSE FALSE
    END
{% endmacro %}