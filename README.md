# weather-data-analysis

A SQLite-backed weather data pipeline and CLI query tool built on 173 years of
historic Met Office station data for **Oxford** (1853-2026, including
provisional 2026 data), sourced from
[metoffice.gov.uk](https://www.metoffice.gov.uk/pub/data/weather/uk/climate/stationdata/).

> Note: the Oxford station file was the one available to work with. The
> pipeline works for any Met Office station file in the same format — just
> drop a new raw `.txt` file in `data/` and update the station name/lat/lon
> constants in `scripts/load_data.py`.

## What's here

```
weather-data-analysis/
├── data/
│   ├── oxford_raw.txt        # original Met Office fixed-width station data
│   └── oxford_clean.csv      # parsed, tidy CSV (generated)
├── scripts/
│   ├── parse_metoffice.py    # raw text -> clean CSV
│   ├── schema.sql            # SQLite schema (4 normalised tables)
│   ├── load_data.py          # builds weather.db and loads the CSV
│   ├── query_tool.py         # interactive/one-shot CLI query tool
│   └── visualise.py          # matplotlib chart generation
├── queries/
│   └── analysis_queries.sql  # commented standalone SQL queries
├── output/                   # generated PNG charts land here
├── weather.db                # SQLite database (generated)
└── README.md
```

## Database schema

Four normalised tables, matching the brief:

- **locations** — station name, lat/lon, elevation
- **date_time** — year, month, and a derived meteorological `season`
  (Winter/Spring/Summer/Autumn)
- **weather_metrics** — tmax, tmin, air frost days, rainfall, sunshine hours,
  each with an `_estimated` flag (the source data marks some values with `*`
  for estimated, which is preserved rather than discarded)
- **observations** — the join table linking a location + date_time to its
  weather_metrics row

## Setup

```bash
pip install pandas matplotlib --break-system-packages   # if not already installed
python3 scripts/parse_metoffice.py    # data/oxford_raw.txt -> data/oxford_clean.csv
python3 scripts/load_data.py          # builds weather.db from schema.sql + CSV
```

`load_data.py` prints a verification summary (row count, year range, and the
most recent rows) so you can sanity-check the import.

## Using the CLI tool

Interactive mode:

```bash
python3 scripts/query_tool.py
> weather in oxford
> average temp by month
> rainfall trend 2025
> hottest months
> decade trends
> quit
```

One-shot mode (good for scripting):

```bash
python3 scripts/query_tool.py "rainfall by season"
```

Full command list: `help`

| Command | What it does |
|---|---|
| `weather in <place>` | Station info + last 6 months of readings |
| `average temp by month` | Avg tmax/tmin per calendar month, all years |
| `rainfall by season` | Total & average rainfall per meteorological season |
| `rainfall trend <year>` | Month-by-month rainfall for one year |
| `hottest months` | Top 10 hottest months on record (by tmax) |
| `coldest months` | Top 10 coldest months on record (by air frost days) |
| `sunny vs cloudy` | Months classified against their own seasonal sunshine norm |
| `decade trends` | Avg tmax/tmin/rainfall per decade |

**A note on two of the brief's original query ideas:** this Met Office
station file is monthly, not daily, and has no wind speed column. "Highest
wind speeds" and "sunny vs cloudy days" were adapted accordingly —
`coldest months` uses air frost days as the cold-extreme equivalent, and
`sunny vs cloudy` compares each month's sunshine hours against its own
long-term calendar-month average rather than a daily sunny/cloudy flag.

## Visualisations

```bash
python3 scripts/visualise.py
```

Generates three PNGs in `output/`:

- `monthly_rainfall.png` — bar chart, average rainfall by calendar month
- `temperature_trend.png` — line chart, annual avg tmax/tmin, complete years only
- `decade_summary.png` — bar chart, avg tmax by decade (colour-flips above 14.5°C)

## Three insights from the data

1. **Oxford's climate has measurably warmed.** The 1850s averaged 13.6°C max
   / 5.6°C min; the 2020s (so far) average 15.8°C max / 7.6°C min — a rise of
   roughly **2.2°C in average daily maximum** over ~170 years, with the
   warming accelerating noticeably from the 1990s onward (see
   `decade_summary.png`).

2. **Autumn, not winter, is Oxford's wettest season on average** — total
   recorded rainfall by season across the full record is Autumn > Summer >
   Winter > Spring, which cuts against the popular assumption that British
   winters are the rainiest time of year.

3. **Extremes cluster in specific months, not randomly.** All of the top 5
   wettest single months on record fall in September, October or November
   (the wettest being September 2024 at 197.1mm), while all of the top 5
   driest single months fall in March or April (driest: April 2011 at just
   0.5mm) — reinforcing that early autumn is the standout wet period and
   early spring the standout dry spell.

## Data quality notes

- Sunshine hour records only begin in 1929 (earlier months show `---`/missing
  in the source and are stored as `NULL`).
- Values marked with `*` in the source (estimated, not directly measured) are
  preserved and flagged via the `_estimated` columns rather than silently
  treated as exact.
- 2026 data is marked "Provisional" in the source file and included as-is.
