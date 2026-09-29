# Listening Behavior Analytics: Cohort & RFM Segmentation

SQL-first analytics on music listening history. Loads play data into a normalized SQLite schema, computes track-cohort retention and artist-level RFM entirely in SQL, and serves the results through a Flask API and a single-page dashboard.

## Why this exists

Most portfolio analytics projects load one flat CSV into pandas. This one is built around the opposite constraint: the data is split into three related tables, so every metric *requires* joins, correlated subqueries, and date bucketing. The goal was to practice the same cohort-retention pattern used in product analytics (as in my [A/B test engine](https://github.com/anvithaz/ab-test-engine)) on a different kind of behavioral data.

## Data

The repo ships with a generator, not real data. `generate_data.py` produces a synthetic Apple Music-style play history (seeded, reproducible: 9 months, 14 tracks, 5 artists, ~15% skipped/partial plays, three device types). Each track gets a "peak" period so some tracks fade and others are rediscovered, which gives the cohort table something to show.

The column layout mirrors Apple's export (`timestamp, track, artist, album, ms_played, track_length_ms, device`), so a real export can be dropped in at `data/apple_music_history.csv` after mapping its columns. `*.csv` is gitignored so personal listening history never lands in the repo.

## Schema

## What it computes

**Cohort retention** (`cohort_retention()`): a track's cohort is the month of its first play (correlated subquery on `MIN(played_at)`). The result is plays per cohort month x play month, showing whether tracks discovered in a given month keep getting replayed or fade.

**RFM per artist** (`artist_rfm()`): classic RFM adapted to engagement data.

| Metric | Definition here |
|---|---|
| Recency | days between the artist's last play and the newest play in the dataset |
| Frequency | total play count |
| Monetary | total minutes listened (stands in for "value") |

**Top artists** (`top_artists()`): play count and average listen duration per artist.

Each metric is scored 1-3 from its `CUME_DIST()` (3 = best; ties share a score, three bands because the catalog is small), then artists are labelled Champion, Recent, Steady, At Risk, or Lapsed from the R score and the F+M score.

## API

| Endpoint | Returns |
|---|---|
| `GET /` | dashboard |
| `GET /api/top-artists` | play count + avg listen seconds per artist |
| `GET /api/cohort-retention` | cohort month x play month x plays |
| `GET /api/rfm` | recency, frequency, monetary, R/F/M scores, and segment per artist |

## Run it

```bash
git clone https://github.com/anvithaz/listening-behavior-analytics.git
cd listening-behavior-analytics
python -m venv .venv && source .venv/bin/activate
pip install flask

python generate_data.py     # writes data/apple_music_history.csv
python data_loader.py       # builds music.db (artists, tracks, plays)
python app.py               # http://localhost:5002
```

## Project structure

generate_data.py   synthetic play-history generator
data_loader.py     CSV -> normalized SQLite schema
analytics.py       cohort retention, RFM, top artists (pure SQL)
app.py             Flask API + dashboard route
dashboard.html     single-page dashboard
query.py           standalone cohort query for quick terminal checks

## Stack

Python, Flask, SQLite, SQL (joins, correlated subqueries, `strftime` date bucketing, aggregates), vanilla JS.

## Next steps

- Move to five-band scoring once the catalog is large enough
- Pivot the cohort table into a retention matrix with a heatmap
- Swap in a real Apple Music export
- Add tests for the SQL against a tiny fixture database
