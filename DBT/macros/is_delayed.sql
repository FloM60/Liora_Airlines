{% macro is_delayed(arr_delay) %}
    CASE
      WHEN COALESCE({{arr_delay}}, 0) > 15 THEN TRUE ELSE FALSE
    END 
{% endmacro %}