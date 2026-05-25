with WeatherDesc as (
  select * from {{source('DatasetSilver', 'weatherdesc') }}
),

Weather as (
  select * from {{source('DatasetSilver', 'weather') }}
),

Cancel as (
  select * from {{source('DatasetSilver', 'cancel') }}
),

State as (
  select * from {{source('DatasetSilver', 'state') }}
),

City as (
  select * from {{source('DatasetSilver', 'city') }}
),

Flights as (
  select * from {{source('DatasetSilver', 'flights') }}
),

final as (
  select
    f.id_flight,
    f.flight_number,
    f.date_flight,
    f.day_of_week,
    f.day_flight,
    f.month_flight,
    f.year_flight,
    f.dep_crs_time,
    f.dep_time,
    f.dep_delay,
    f.arr_crs_time,
    f.arr_time,
    f.arr_es_time_cor,
    f.arr_delay,
    f.estimated_duration,
    f.final_duration,
    f.carrier_delay,
    f.weather_delay,
    f.nas_delay,
    f.security_delay,
    f.lateaircraft_delay,
    cl.id_cancel,
    cl.name_cancel,
    co.id_city as origin_id_city,
    co.name_city as origin_name_city,
    so.id_state as origin_id_state,
    so.name_state as origin_name_state,
    co.latitude_city as origin_latitude,
    co.longitude_city as origin_longitude,
    cd.id_city as dest_id_city,
    cd.name_city as dest_name_city,
    sd.id_state as dest_id_state,
    sd.name_state as dest_name_state,
    cd.latitude_city as dest_latitude,
    cd.longitude_city as dest_longitude,
    wo.temperature as origin_temperature,
    wo.relative_humidity as origin_relative_humidity,
    wo.dewpoint as origin_dewpoint,
    wo.apparent_temperature as origin_apparent_temperature,
    wo.precipitation as origin_precipitation,
    wo.rain as origin_rain,
    wo.snowfall as origin_snowfall,
    wo.snow_deph as origin_snow_deph,
    wo.wind_speed_10 as origin_wind_speed_10,
    wo.wind_speed_100 as origin_wind_speed_100,
    wo.wind_gusts_10 as origin_wind_gusts_10,
    dso.weather_code as origin_weather_code,
    dso.weather_description as origin_weather_description,
    wd.temperature as dest_temperature,
    wd.relative_humidity as dest_relative_humidity,
    wd.dewpoint as dest_dewpoint,
    wd.apparent_temperature as dest_apparent_temperature,
    wd.precipitation as dest_precipitation,
    wd.rain as dest_rain,
    wd.snowfall as dest_snowfall,
    wd.snow_deph as dest_snow_deph,
    wd.wind_speed_10 as dest_wind_speed_10,
    wd.wind_speed_100 as dest_wind_speed_100,
    wd.wind_gusts_10 as dest_wind_gusts_10,
    dsd.weather_code as dest_weather_code,
    dsd.weather_description as dest_weather_description
  from flights f
    left join weather wo on wo.id_weather = f.id_origin_weather
    left join weather wd on wd.id_weather = f.id_dest_weather
    left join weatherdesc dso on dso.weather_code = wo.weather_code
    left join weatherdesc dsd on dsd.weather_code = wd.weather_code
    left join city co on co.id_city = f.id_origin_city
    left join city cd on cd.id_city = f.id_dest_city
    left join state so on so.id_state = co.id_state
    left join state sd on sd.id_state = co.id_state
    left join cancel cl on cl.id_cancel = f.id_cancel
)

select * from final





