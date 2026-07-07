"""
visualise.py

Generates PNG charts from weather.db into the output/ folder:
  1. monthly_rainfall.png  - bar chart of average rainfall by calendar month
  2. temperature_trend.png - line chart of average annual tmax/tmin, 1853-present
  3. decade_summary.png    - bar chart of avg tmax by decade (warming trend)
"""

import sqlite3
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = Path(__file__).parent.parent
DB_PATH = BASE / "weather.db"
OUT_DIR = BASE / "output"
OUT_DIR.mkdir(exist_ok=True)

MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def get_conn():
    return sqlite3.connect(DB_PATH)



def chart_monthly_rainfall(conn):
    cur = conn.cursor()
    cur.execute(
        """SELECT dt.month, AVG(wm.rain_mm)
           FROM observations o
           JOIN date_time dt ON o.date_id = dt.date_id
           JOIN weather_metrics wm ON o.metric_id = wm.metric_id
           WHERE wm.rain_mm IS NOT NULL
           GROUP BY dt.month ORDER BY dt.month"""
    )
    rows = cur.fetchall()
    months = [MONTH_NAMES[m - 1] for m, _ in rows]
    values = [v for _, v in rows]

    fig, ax = plt.subplots(figsize=(9, 5))
    bars = ax.bar(months, values, color="#3b82c4")
    ax.set_title("Oxford: Average Monthly Rainfall (1853-2026)", fontsize=13)
    ax.set_ylabel("Rainfall (mm)")
    ax.bar_label(bars, fmt="%.0f", padding=2, fontsize=8)
    fig.tight_layout()
    path = OUT_DIR / "monthly_rainfall.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"Saved {path}")


def chart_temperature_trend(conn):
    cur = conn.cursor()
    cur.execute(
        """SELECT dt.year, AVG(wm.tmax_c), AVG(wm.tmin_c)
           FROM observations o
           JOIN date_time dt ON o.date_id = dt.date_id
           JOIN weather_metrics wm ON o.metric_id = wm.metric_id
           WHERE wm.tmax_c IS NOT NULL AND wm.tmin_c IS NOT NULL
           GROUP BY dt.year
           HAVING COUNT(*) = 12
           ORDER BY dt.year"""
    )
    rows = cur.fetchall()
    years = [r[0] for r in rows]
    tmax = [r[1] for r in rows]
    tmin = [r[2] for r in rows]

    fig, ax = plt.subplots(figsize=(11, 5))
    ax.plot(years, tmax, label="Avg TMax", color="#d9480f", linewidth=1.5)
    ax.plot(years, tmin, label="Avg TMin", color="#1c7ed6", linewidth=1.5)
    ax.set_title("Oxford: Annual Average Temperature Trend (complete years only)", fontsize=13)
    ax.set_xlabel("Year")
    ax.set_ylabel("Temperature (C)")
    ax.legend()
    fig.tight_layout()
    path = OUT_DIR / "temperature_trend.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"Saved {path}")



def chart_decade_summary(conn):
    cur = conn.cursor()
    cur.execute(
        """SELECT (dt.year/10)*10 AS decade, AVG(wm.tmax_c)
           FROM observations o
           JOIN date_time dt ON o.date_id = dt.date_id
           JOIN weather_metrics wm ON o.metric_id = wm.metric_id
           WHERE wm.tmax_c IS NOT NULL
           GROUP BY decade ORDER BY decade"""
    )
    rows = cur.fetchall()
    decades = [str(r[0]) + "s" for r in rows]
    values = [r[1] for r in rows]

    fig, ax = plt.subplots(figsize=(11, 5))
    colors = ["#4c6ef5" if v < 14.5 else "#f76707" for v in values]
    ax.bar(decades, values, color=colors)
    ax.set_title("Oxford: Average Max Temperature by Decade", fontsize=13)
    ax.set_ylabel("Avg TMax (C)")
    ax.set_ylim(min(values) - 1, max(values) + 1)
    plt.xticks(rotation=45)
    fig.tight_layout()
    path = OUT_DIR / "decade_summary.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"Saved {path}")



def main():
    conn = get_conn()
    chart_monthly_rainfall(conn)
    chart_temperature_trend(conn)
    chart_decade_summary(conn)
    conn.close()


if __name__ == "__main__":
    main()
