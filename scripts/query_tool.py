"""
query_tool.py

CLI tool for the Oxford weather database. Understands commands like:

    weather in oxford
    average temp by month
    rainfall trend 2025
    rainfall by season
    hottest months
    coldest months
    sunny vs cloudy
    decade trends
    help
    quit

Usage:
    python3 query_tool.py                 # interactive mode
    python3 query_tool.py "average temp by month"   # one-shot mode
"""
import re
import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "weather.db"


def get_conn():
    if not DB_PATH.exists():
        print(f"Database not found at {DB_PATH}. Run load_data.py first.")
        sys.exit(1)
    return sqlite3.connect(DB_PATH)


def print_table(headers, rows):
    if not rows:
        print("  (no data found)")
        return
    widths = [len(h) for h in headers]
    str_rows = []
    for row in rows:
        str_row = [("" if v is None else str(v)) for v in row]
        str_rows.append(str_row)
        for i, val in enumerate(str_row):
            widths[i] = max(widths[i], len(val))

    def fmt_row(vals):
        return "  ".join(v.ljust(widths[i]) for i, v in enumerate(vals))

    print(fmt_row(headers))
    print("  ".join("-" * w for w in widths))
    for r in str_rows:
        print(fmt_row(r))


def cmd_weather_in(conn, location_hint):
    cur = conn.cursor()
    cur.execute("SELECT name, latitude, longitude, elevation_m FROM locations")
    locs = cur.fetchall()
    match = None
    for loc in locs:
        if location_hint.lower() in loc[0].lower():
            match = loc
            break
    if not match:
        names = ", ".join(l[0] for l in locs)
        print(f"No station matching '{location_hint}' in this database.")
        print(f"Available station(s): {names}")
        return
    name, lat, lon, elev = match
    print(f"\nStation: {name}  (lat {lat}, lon {lon}, {elev}m amsl)\n")
    cur.execute(
        """SELECT dt.year, dt.month, wm.tmax_c, wm.tmin_c, wm.rain_mm, wm.sun_hours
           FROM observations o
           JOIN date_time dt ON o.date_id = dt.date_id
           JOIN weather_metrics wm ON o.metric_id = wm.metric_id
           JOIN locations l ON o.location_id = l.location_id
           WHERE l.name = ?
           ORDER BY dt.year DESC, dt.month DESC
           LIMIT 6""",
        (name,),
    )
    rows = cur.fetchall()
    print_table(["Year", "Month", "TMax C", "TMin C", "Rain mm", "Sun hrs"], rows)


def cmd_avg_temp_by_month(conn):
    cur = conn.cursor()
    cur.execute(
        """SELECT dt.month,
                  ROUND(AVG(wm.tmax_c), 1) AS avg_tmax,
                  ROUND(AVG(wm.tmin_c), 1) AS avg_tmin
           FROM observations o
           JOIN date_time dt ON o.date_id = dt.date_id
           JOIN weather_metrics wm ON o.metric_id = wm.metric_id
           GROUP BY dt.month ORDER BY dt.month"""
    )
    rows = cur.fetchall()
    print("\nAverage temperature by calendar month (all years on record):\n")
    print_table(["Month", "Avg TMax C", "Avg TMin C"], rows)



def cmd_rainfall_by_season(conn):
    cur = conn.cursor()
    cur.execute(
        """SELECT dt.season,
                  ROUND(SUM(wm.rain_mm), 1) AS total_rain,
                  ROUND(AVG(wm.rain_mm), 1) AS avg_rain_per_month
           FROM observations o
           JOIN date_time dt ON o.date_id = dt.date_id
           JOIN weather_metrics wm ON o.metric_id = wm.metric_id
           GROUP BY dt.season ORDER BY total_rain DESC"""
    )
    rows = cur.fetchall()
    print("\nTotal & average rainfall by season (all years on record):\n")
    print_table(["Season", "Total Rain mm", "Avg Rain mm/month"], rows)


def cmd_rainfall_trend(conn, year):
    cur = conn.cursor()
    cur.execute(
        """SELECT dt.month, wm.rain_mm
           FROM observations o
           JOIN date_time dt ON o.date_id = dt.date_id
           JOIN weather_metrics wm ON o.metric_id = wm.metric_id
           WHERE dt.year = ? ORDER BY dt.month""",
        (year,),
    )
    rows = cur.fetchall()
    if not rows:
        print(f"No data found for {year}.")
        return
    print(f"\nRainfall trend for {year}:\n")
    print_table(["Month", "Rain mm"], rows)


def cmd_hottest_months(conn, n=10):
    cur = conn.cursor()
    cur.execute(
        """SELECT dt.year, dt.month, wm.tmax_c
           FROM observations o
           JOIN date_time dt ON o.date_id = dt.date_id
           JOIN weather_metrics wm ON o.metric_id = wm.metric_id
           WHERE wm.tmax_c IS NOT NULL
           ORDER BY wm.tmax_c DESC LIMIT ?""",
        (n,),
    )
    rows = cur.fetchall()
    print(f"\nTop {n} hottest months on record (by average max temp):\n")
    print_table(["Year", "Month", "TMax C"], rows)


def cmd_coldest_months(conn, n=10):
    cur = conn.cursor()
    cur.execute(
        """SELECT dt.year, dt.month, wm.air_frost_days
           FROM observations o
           JOIN date_time dt ON o.date_id = dt.date_id
           JOIN weather_metrics wm ON o.metric_id = wm.metric_id
           WHERE wm.air_frost_days IS NOT NULL
           ORDER BY wm.air_frost_days DESC LIMIT ?""",
        (n,),
    )
    rows = cur.fetchall()
    print(f"\nTop {n} coldest months on record (by air frost days):\n")
    print_table(["Year", "Month", "Air Frost Days"], rows)


def cmd_sunny_vs_cloudy(conn):
    cur = conn.cursor()
    cur.execute(
        """WITH month_avg AS (
             SELECT dt.month, AVG(wm.sun_hours) AS avg_sun
             FROM observations o
             JOIN date_time dt ON o.date_id = dt.date_id
             JOIN weather_metrics wm ON o.metric_id = wm.metric_id
             WHERE wm.sun_hours IS NOT NULL GROUP BY dt.month
           )
           SELECT
             CASE WHEN wm.sun_hours >= ma.avg_sun THEN 'Sunnier than average'
                  ELSE 'Cloudier than average' END AS classification,
             COUNT(*) AS n_months
           FROM observations o
           JOIN date_time dt ON o.date_id = dt.date_id
           JOIN weather_metrics wm ON o.metric_id = wm.metric_id
           JOIN month_avg ma ON dt.month = ma.month
           WHERE wm.sun_hours IS NOT NULL
           GROUP BY classification"""
    )
    rows = cur.fetchall()
    print("\nMonths classified vs their own calendar-month sunshine average:\n")
    print("(Note: no raw wind speed or a daily sunny/cloudy flag exists in this")
    print(" monthly Met Office dataset, so months are compared to their own")
    print(" long-term seasonal norm instead.)\n")
    print_table(["Classification", "Number of months"], rows)


def cmd_decade_trends(conn):
    cur = conn.cursor()
    cur.execute(
        """SELECT (dt.year / 10) * 10 AS decade,
                  ROUND(AVG(wm.tmax_c), 1) AS avg_tmax,
                  ROUND(AVG(wm.tmin_c), 1) AS avg_tmin,
                  ROUND(AVG(wm.rain_mm), 1) AS avg_rain
           FROM observations o
           JOIN date_time dt ON o.date_id = dt.date_id
           JOIN weather_metrics wm ON o.metric_id = wm.metric_id
           GROUP BY decade ORDER BY decade"""
    )
    rows = cur.fetchall()
    print("\nDecade-by-decade averages:\n")
    print_table(["Decade", "Avg TMax C", "Avg TMin C", "Avg Rain mm"], rows)


HELP_TEXT = """
Available commands:
  weather in <place>            e.g. "weather in oxford"
  average temp by month
  rainfall by season
  rainfall trend <year>         e.g. "rainfall trend 2025"
  hottest months
  coldest months
  sunny vs cloudy
  decade trends
  help
  quit
"""



def dispatch(conn, command: str):
    cmd = command.strip().lower()

    m = re.match(r"weather in (.+)", cmd)
    if m:
        cmd_weather_in(conn, m.group(1).strip())
        return

    if "average temp" in cmd or "avg temp" in cmd:
        cmd_avg_temp_by_month(conn)
        return

    m = re.match(r"rainfall trend (\d{4})", cmd)
    if m:
        cmd_rainfall_trend(conn, int(m.group(1)))
        return

    if "rainfall" in cmd and "season" in cmd:
        cmd_rainfall_by_season(conn)
        return

    if "hottest" in cmd:
        cmd_hottest_months(conn)
        return

    if "coldest" in cmd:
        cmd_coldest_months(conn)
        return

    if "sunny" in cmd or "cloudy" in cmd:
        cmd_sunny_vs_cloudy(conn)
        return

    if "decade" in cmd:
        cmd_decade_trends(conn)
        return

    if cmd in ("help", "?"):
        print(HELP_TEXT)
        return

    print(f"Command not recognised: '{command}'")
    print(HELP_TEXT)


def main():
    conn = get_conn()

    if len(sys.argv) > 1:
        # One-shot mode: python3 query_tool.py "average temp by month"
        dispatch(conn, " ".join(sys.argv[1:]))
        conn.close()
        return

    print("UK Weather Data Query Tool - Oxford station")
    print("Type 'help' for commands, 'quit' to exit.\n")
    while True:
        try:
            command = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if command.lower() in ("quit", "exit"):
            break
        if not command:
            continue
        dispatch(conn, command)

    conn.close()


if __name__ == "__main__":
    main()
