-- ============================================================
-- analysis_queries.sql
-- Commented SQL queries for the Oxford weather database.
-- Run these against weather.db (e.g. via `sqlite3 weather.db < analysis_queries.sql`
-- or through query_tool.py which wraps them for the CLI).
-- ============================================================


-- 1. AVERAGE TEMPERATURE BY MONTH (across all years on record)
-- Tells us: the typical seasonal temperature curve for the station -
-- e.g. how much warmer July is than January on average.
SELECT
    dt.month,
    ROUND(AVG(wm.tmax_c), 1) AS avg_tmax_c,
    ROUND(AVG(wm.tmin_c), 1) AS avg_tmin_c
FROM observations o
JOIN date_time dt        ON o.date_id = dt.date_id
JOIN weather_metrics wm   ON o.metric_id = wm.metric_id
GROUP BY dt.month
ORDER BY dt.month;


-- 2. TOTAL RAINFALL PER SEASON (summed across all years, then averaged per season)
-- Tells us: which season is wettest on average - useful for spotting
-- whether "British summers are rainy" holds up in the data.
SELECT
    dt.season,
    ROUND(SUM(wm.rain_mm), 1)   AS total_rain_mm_all_years,
    ROUND(AVG(wm.rain_mm), 1)   AS avg_rain_mm_per_month
FROM observations o
JOIN date_time dt        ON o.date_id = dt.date_id
JOIN weather_metrics wm  ON o.metric_id = wm.metric_id
GROUP BY dt.season
ORDER BY total_rain_mm_all_years DESC;


-- 3. HIGHEST TMAX RECORDED (proxy for "extreme heat" - this dataset has no
-- wind speed column, so we use max temperature and air frost days as the
-- extreme-weather indicators available in this station's records)
-- Tells us: the hottest and coldest months on record and when they happened.
SELECT dt.year, dt.month, wm.tmax_c
FROM observations o
JOIN date_time dt       ON o.date_id = dt.date_id
JOIN weather_metrics wm ON o.metric_id = wm.metric_id
WHERE wm.tmax_c IS NOT NULL
ORDER BY wm.tmax_c DESC
LIMIT 10;


-- 3b. MOST AIR FROST DAYS IN A MONTH (cold extreme equivalent)
SELECT dt.year, dt.month, wm.air_frost_days
FROM observations o
JOIN date_time dt       ON o.date_id = dt.date_id
JOIN weather_metrics wm ON o.metric_id = wm.metric_id
WHERE wm.air_frost_days IS NOT NULL
ORDER BY wm.air_frost_days DESC
LIMIT 10;


-- 4. FREQUENCY OF SUNNY VS CLOUDY MONTHS (proxy - no daily sun/cloud flag
-- exists in this monthly dataset, so we classify each month as "sunny" or
-- "cloudy" relative to the long-term average sun_hours for that calendar month)
-- Tells us: how often a given month over- or under-performs its own seasonal norm.
WITH month_avg AS (
    SELECT dt.month, AVG(wm.sun_hours) AS avg_sun
    FROM observations o
    JOIN date_time dt       ON o.date_id = dt.date_id
    JOIN weather_metrics wm ON o.metric_id = wm.metric_id
    WHERE wm.sun_hours IS NOT NULL
    GROUP BY dt.month
)
SELECT
    CASE WHEN wm.sun_hours >= ma.avg_sun THEN 'Sunnier than average'
         ELSE 'Cloudier than average' END AS classification,
    COUNT(*) AS n_months
FROM observations o
JOIN date_time dt       ON o.date_id = dt.date_id
JOIN weather_metrics wm ON o.metric_id = wm.metric_id
JOIN month_avg ma        ON dt.month = ma.month
WHERE wm.sun_hours IS NOT NULL
GROUP BY classification;


-- 5. RAINFALL TREND FOR A GIVEN YEAR (parameterised in query_tool.py)
-- Tells us: month-by-month rainfall for one specific year, e.g. for
-- comparing 2025 against the long-term monthly average.
-- SELECT dt.month, wm.rain_mm FROM observations o
-- JOIN date_time dt ON o.date_id = dt.date_id
-- JOIN weather_metrics wm ON o.metric_id = wm.metric_id
-- WHERE dt.year = :year ORDER BY dt.month;


-- 6. WARMEST AND COOLEST DECADES (long-term climate trend check)
-- Tells us: whether average temperatures have shifted decade to decade,
-- which is the clearest "is it getting warmer" signal this dataset can give.
SELECT
    (dt.year / 10) * 10 AS decade,
    ROUND(AVG(wm.tmax_c), 1) AS avg_tmax_c,
    ROUND(AVG(wm.tmin_c), 1) AS avg_tmin_c,
    ROUND(AVG(wm.rain_mm), 1) AS avg_rain_mm
FROM observations o
JOIN date_time dt       ON o.date_id = dt.date_id
JOIN weather_metrics wm ON o.metric_id = wm.metric_id
GROUP BY decade
ORDER BY decade;
