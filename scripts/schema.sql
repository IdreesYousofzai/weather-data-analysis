-- weather-data-analysis schema
-- Normalised into: locations, date_time, weather_metrics, observations
-- (observations ties a location + date_time to a set of weather_metrics)

DROP TABLE IF EXISTS observations;
DROP TABLE IF EXISTS weather_metrics;
DROP TABLE IF EXISTS date_time;
DROP TABLE IF EXISTS locations;

CREATE TABLE locations (
    location_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL UNIQUE,
    latitude        REAL,
    longitude       REAL,
    elevation_m     REAL
);

CREATE TABLE date_time (
    date_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    year            INTEGER NOT NULL,
    month           INTEGER NOT NULL,
    season          TEXT NOT NULL,   -- Winter / Spring / Summer / Autumn (meteorological)
    UNIQUE(year, month)
);

CREATE TABLE weather_metrics (
    metric_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    tmax_c              REAL,
    tmax_estimated      INTEGER,   -- 0/1 boolean
    tmin_c              REAL,
    tmin_estimated      INTEGER,
    air_frost_days      REAL,
    air_frost_estimated INTEGER,
    rain_mm             REAL,
    rain_estimated      INTEGER,
    sun_hours           REAL,
    sun_estimated       INTEGER
);

CREATE TABLE observations (
    observation_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    location_id     INTEGER NOT NULL REFERENCES locations(location_id),
    date_id         INTEGER NOT NULL REFERENCES date_time(date_id),
    metric_id       INTEGER NOT NULL REFERENCES weather_metrics(metric_id),
    UNIQUE(location_id, date_id)
);

CREATE INDEX idx_date_year_month ON date_time(year, month);
CREATE INDEX idx_obs_location ON observations(location_id);
