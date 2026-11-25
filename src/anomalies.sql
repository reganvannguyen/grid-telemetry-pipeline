DROP TABLE IF EXISTS grid_anomalies;
DROP TABLE IF EXISTS telemetry_with_baselines;

CREATE TABLE telemetry_with_baselines AS
WITH enriched AS (
    SELECT
        dt_mst,
        region,
        planning_area,
        actload,
        load,
        sysgen,
        temp_celsius,
        CAST(strftime('%m', dt_mst) AS INTEGER) AS month_num,
        CAST(strftime('%H', dt_mst) AS INTEGER) AS hour_of_day,
        CASE
            WHEN strftime('%w', dt_mst) IN ('0', '6') THEN 'WEEKEND'
            ELSE 'WEEKDAY'
        END AS day_type
    FROM clean_grid_telemetry
),
baselines AS (
    SELECT
        planning_area,
        month_num,
        day_type,
        hour_of_day,
        AVG(actload) AS baseline_mean,
        SQRT(MAX(0.0, AVG(actload * actload) - AVG(actload) * AVG(actload))) AS baseline_std,
        COUNT(*) AS sample_count
    FROM enriched
    GROUP BY planning_area, month_num, day_type, hour_of_day
),
scored AS (
    SELECT
        e.dt_mst,
        e.region,
        e.planning_area,
        e.month_num,
        e.day_type,
        e.hour_of_day,
        e.actload,
        e.load,
        e.sysgen,
        e.temp_celsius,
        b.baseline_mean,
        b.baseline_std,
        b.sample_count,
        CASE
            WHEN b.baseline_std > 0 THEN (e.actload - b.baseline_mean) / b.baseline_std
            ELSE 0.0
        END AS z_score
    FROM enriched e
    JOIN baselines b
      ON e.planning_area = b.planning_area
     AND e.month_num = b.month_num
     AND e.day_type = b.day_type
     AND e.hour_of_day = b.hour_of_day
)
SELECT
    *,
    CASE WHEN ABS(z_score) >= 3.0 THEN 1 ELSE 0 END AS is_anomaly,
    CASE
        WHEN z_score >= 3.0 THEN 'SPIKE'
        WHEN z_score <= -3.0 THEN 'DROP'
        ELSE 'NORMAL'
    END AS anomaly_direction,
    CASE
        WHEN temp_celsius <= -25.0 THEN 'EXTREME_COLD'
        WHEN temp_celsius >= 30.0 THEN 'EXTREME_HEAT'
        ELSE 'NORMAL_WEATHER'
    END AS weather_context
FROM scored;

CREATE TABLE grid_anomalies AS
SELECT *
FROM telemetry_with_baselines
WHERE is_anomaly = 1
ORDER BY ABS(z_score) DESC;
