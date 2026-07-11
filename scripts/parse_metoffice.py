"""
parse_metoffice.py
Parses UK Met Office historic station data (the plain-text format downloaded
from metoffice.gov.uk/pub/data/weather/uk/climate/stationdata/) into a clean
CSV ready for loading into SQLite.

Handles:
  - Header/metadata lines (location, lat/lon, notes)
  - Column header lines (yyyy mm tmax tmin af rain sun)
  - Estimated values marked with a trailing '*'
  - Missing values marked as '---'
  - Trailing '#' (sunshine sensor type) and 'Provisional' flags
"""

import csv
import re
import sys
from pathlib import Path

RAW_PATH = Path(__file__).parent.parent / "data" / "oxford_raw.txt"
OUT_PATH = Path(__file__).parent.parent / "data" / "oxford_clean.csv"

# Station metadata pulled from the file header (first few lines)
STATION_NAME = "Oxford"
LAT = 51.761
LON = -1.262
ELEVATION_M = 63


def parse_value(raw):
    """
    Returns (value_or_None, is_estimated_bool) for a single data cell.
    '---' -> (None, False)   missing
    '12.3*' -> (12.3, True)  estimated
    '12.3' -> (12.3, False)  normal
    """
    raw = raw.strip()
    if raw in ("---", ""):
        return None, False
    estimated = raw.endswith("*")
    if estimated:
        raw = raw[:-1]
    try:
        return float(raw), estimated
    except ValueError:
        return None, False


def main():
    rows = []
    with open(RAW_PATH, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.rstrip("\n").rstrip("\r")
            # Data lines start with whitespace then a 4-digit year
            m = re.match(r"^\s*(\d{4})\s+(\d{1,2})\s+(.*)$", line)
            if not m:
                continue
            year, month, rest = m.groups()
            year = int(year)
            month = int(month)

            # Strip trailing "Provisional" flag if present
            rest = rest.replace("Provisional", "").strip()

            # Remaining fields are whitespace separated: tmax tmin af rain sun
            fields = rest.split()
            if len(fields) < 5:
                continue

            tmax_raw, tmin_raw, af_raw, rain_raw, sun_raw = fields[:5]

            tmax, tmax_est = parse_value(tmax_raw)
            tmin, tmin_est = parse_value(tmin_raw)
            af, af_est = parse_value(af_raw)
            rain, rain_est = parse_value(rain_raw)
            # Sunshine sometimes has trailing '#' for sensor type - strip it
            sun_raw = sun_raw.rstrip("#")
            sun, sun_est = parse_value(sun_raw)

            rows.append({
                "year": year,
                "month": month,
                "tmax_c": tmax,
                "tmax_estimated": tmax_est,
                "tmin_c": tmin,
                "tmin_estimated": tmin_est,
                "air_frost_days": af,
                "air_frost_estimated": af_est,
                "rain_mm": rain,
                "rain_estimated": rain_est,
                "sun_hours": sun,
                "sun_estimated": sun_est,
            })

    if not rows:
        print("No data rows parsed - check the raw file format.", file=sys.stderr)
        sys.exit(1)

    fieldnames = list(rows[0].keys())
    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Parsed {len(rows)} monthly records -> {OUT_PATH}")
    print(f"Year range: {rows[0]['year']} to {rows[-1]['year']}")


if __name__ == "__main__":
    main()
