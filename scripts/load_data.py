"""
load_data.py
Creates the SQLite database (weather.db) from schema.sql, then loads the
cleaned Oxford CSV data into the normalised tables:
  locations -> date_time -> weather_metrics -> observations

Run after parse_metoffice.py has produced data/oxford_clean.csv.
"""
import sqlite3
from pathlib import Path

import pandas as pd

BASE = Path(__file__).parent.parent
DB_PATH = BASE / "weather.db"
SCHEMA_PATH = Path(__file__).parent / "schema.sql"
CSV_PATH = BASE / "data" / "oxford_clean.csv"

STATION_NAME = "Oxford"
LAT = 51.761
LON = -1.262
ELEVATION_M = 63


def month_to_season(month: int) -> str:
    """Meteorological seasons: Winter=Dec/Jan/Feb, Spring=Mar/Apr/May, etc."""
    if month in (12, 1, 2):
        return "Winter"
    if month in (3, 4, 5):
        return "Spring"
    if month in (6, 7, 8):
        return "Summer"
    return "Autumn"


def build_schema(conn):
    with open(SCHEMA_PATH, "r") as f:
        conn.executescript(f.read())


def load(conn):
    df = pd.read_csv(CSV_PATH)

    # Convert boolean-like string columns to real 0/1 ints
    bool_cols = [c for c in df.columns if c.endswith("_estimated")]
    for c in bool_cols:
        df[c] = df[c].map({"True": 1, "False": 0, True: 1, False: 0}).fillna(0).astype(int)

    cur = conn.cursor()

    # 1. Location (single row for this dataset)
    cur.execute(
        "INSERT INTO locations (name, latitude, longitude, elevation_m) VALUES (?,?,?,?)",
        (STATION_NAME, LAT, LON, ELEVATION_M),
    )
    location_id = cur.lastrowid

    # 2 & 3 & 4. date_time, weather_metrics, observations - one pass per row
    for _, row in df.iterrows():
        season = month_to_season(int(row["month"]))
        cur.execute(
            "INSERT INTO date_time (year, month, season) VALUES (?,?,?)",
            (int(row["year"]), int(row["month"]), season),
        )
        date_id = cur.lastrowid

        cur.execute(
            """INSERT INTO weather_metrics
               (tmax_c, tmax_estimated, tmin_c, tmin_estimated,
                air_frost_days, air_frost_estimated,
                rain_mm, rain_estimated, sun_hours, sun_estimated)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (
                _none_if_nan(row["tmax_c"]), int(row["tmax_estimated"]),
                _none_if_nan(row["tmin_c"]), int(row["tmin_estimated"]),
                _none_if_nan(row["air_frost_days"]), int(row["air_frost_estimated"]),
                _none_if_nan(row["rain_mm"]), int(row["rain_estimated"]),
                _none_if_nan(row["sun_hours"]), int(row["sun_estimated"]),
            ),
        )
        metric_id = cur.lastrowid

        cur.execute(
            "INSERT INTO observations (location_id, date_id, metric_id) VALUES (?,?,?)",
            (location_id, date_id, metric_id),
        )

    conn.commit()


def _none_if_nan(val):
    try:
        if pd.isna(val):
            return None
    except TypeError:
        pass
    return float(val)


def verify(conn):
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM observations")
    n_obs = cur.fetchone()[0]
    cur.execute("SELECT MIN(year), MAX(year) FROM date_time")
    yr_min, yr_max = cur.fetchone()
    cur.execute(
        """SELECT dt.year, dt.month, wm.tmax_c, wm.tmin_c, wm.rain_mm, wm.sun_hours
           FROM observations o
           JOIN date_time dt ON o.date_id = dt.date_id
           JOIN weather_metrics wm ON o.metric_id = wm.metric_id
           ORDER BY dt.year DESC, dt.month DESC LIMIT 3"""
    )
    print(f"Loaded {n_obs} observations, years {yr_min}-{yr_max}")
    print("Most recent rows:")
    for r in cur.fetchall():
        print(" ", r)


def main():
    if DB_PATH.exists():
        DB_PATH.unlink()
    conn = sqlite3.connect(DB_PATH)
    build_schema(conn)
    load(conn)
    verify(conn)
    conn.close()
    print(f"\nDatabase ready at {DB_PATH}")


if __name__ == "__main__":
    main()
