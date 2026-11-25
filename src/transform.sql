DROP TABLE IF EXISTS clean_grid_telemetry;
CREATE TABLE clean_grid_telemetry AS
WITH region_weather_map AS (
    SELECT 'Calgary'   AS aeso_region, 'CALGARY INTL A'      AS weather_hub UNION ALL
    SELECT 'Edmonton'  AS aeso_region, 'EDMONTON INTL A'     AS weather_hub UNION ALL
    SELECT 'Central'   AS aeso_region, 'RED DEER REGIONAL A' AS weather_hub UNION ALL
    SELECT 'South'     AS aeso_region, 'MEDICINE HAT RCS'    AS weather_hub UNION ALL
    SELECT 'Northeast' AS aeso_region, 'EDMONTON INTL A'     AS weather_hub UNION ALL
    SELECT 'Northwest' AS aeso_region, 'EDMONTON INTL A'     AS weather_hub
)
SELECT
    a.dt_mst,
    a.region,
    a.planning_area,
    a.actload,
    a.load,
    a.sysgen,
    w.temp_celsius
FROM raw_aeso_load a
JOIN region_weather_map m
  ON a.region = m.aeso_region
LEFT JOIN raw_weather w
  ON a.dt_mst = w.dt_lst
 AND m.weather_hub = w.station_name;
