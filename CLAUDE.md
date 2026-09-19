# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A static dashboard (GitHub Pages, live at https://jbaris.github.io/grain-price-analyzer/) showing Argentine grain prices (maíz, trigo, soja) in USD since 2018-07-01, with agricultural/political events overlaid. `index.html` is the whole frontend; a numbered set of root-level scripts builds the data files under `data/`. There is no build step, no test suite, and no package manifest beyond `requirements.txt` (`requests`, `lxml`).

## Commands

All scripts use relative `./data/...` paths, so **run them from the repo root**.

```bash
# One-time setup
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt

# Data pipeline (run in order when refreshing data)
bash 01_fetch_prices_ggsa.sh                             # incremental: fetches from last date in prices_ggsa.json, merges new dates only
python3 02_fetch_dolar_bcra.py                           # incremental: appends missing days from BCRA API v4 to dolar_bcra.txt
python3 03_fetch_missing_dolar_exchange.py               # dolar_bcra.txt -> dolar_exchange_complete.json
python3 04_build_prices_csv.py                           # prices_ggsa.json + exchange -> prices.csv
python3 05_sanitize_csv.py                               # prices.csv -> prices_sanitized.csv (prints discarded rows)
python3 06_merge_events.py                               # events_regular.json + events_special.json -> events_all.json

# Fix CRLF that 04/05 may introduce in the CSVs (repo keeps LF; index.html parses CSV with naive split(','))
sed -i '' 's/\r$//' data/prices.csv data/prices_sanitized.csv   # macOS/BSD sed; on Linux drop the '' after -i

# Local preview (needed because index.html fetches data/ via fetch(); file:// won't work)
bash 99_test.sh    # http://localhost:8880

# Commit and push data/ to publish (pushing to master redeploys via .github/workflows/static.yml)
git add data/
git commit -m "Update data to $(date +%Y-%m-%d)"
git push
```

Deploy is automatic: pushing to `master` runs `.github/workflows/static.yml`, which publishes the entire repo root to GitHub Pages. Generated data files are committed, not built in CI, so a data refresh must be committed for the site to update.

## Pipeline architecture

```
GGSA "pizarra" API ──01──> data/prices_ggsa.json ─┐
                                                   ├─04─> data/prices.csv ─05─> data/prices_sanitized.csv ─┐
BCRA API v4 (var. 5) ──02──> data/dolar_bcra.txt ─03─> data/dolar_exchange_complete.json ─┘               ├─> index.html
data/events_regular.json + data/events_special.json ─06─> data/events_all.json ────────────────────────────┘
```

Key behaviors that are easy to get wrong:

- **01_fetch_prices_ggsa.sh** hits `ggsa.com.ar/get_pizarra/pros59/<start>/<today>/` with a hard-coded CSRF cookie/token copied from a browser session (refresh it there if the request starts failing). The response is `{"pizarra": {"YYYY-MM-DD": {"maiz": {"precio", "estimativo"}, ...}}}`. `<start>` is the last date already in `prices_ggsa.json`, and only dates not yet present are merged in: existing dates are never overwritten (GGSA may revise old values, e.g. `estimativo` becoming `precio`, and we deliberately keep what was already computed).
- **02_fetch_dolar_bcra.py** appends only the days after the last date in `dolar_bcra.txt`, from `api.bcra.gob.ar/estadisticas/v4.0/monetarias/5` (wholesale reference rate, Com. A 3500; values match the old manual site export exactly). It writes lines in the file's own `DD/MM/YYYY<TAB>1.442,4148` format and reuses `load_rates_by_date` from 03. Only published business days are appended.
- **03** fills every calendar day (weekends/holidays) with the last published BCRA rate, and parses `18,5500`-style comma decimals. Output is `{"data": [["YYYY-MM-DD", rate], ...]}`.
- **04** hard-codes `START_DATE = '2018-07-01'`, uses `precio` falling back to `estimativo` when `precio` is `0.00`, and **drops any day where any of the three cereals is missing**. Columns: `fecha,maiz_ars,trigo_ars,soja_ars,tipo_cambio_usd,maiz_usd,trigo_usd,soja_usd`.
- **05** removes rows where any numeric column jumps >50% vs. the previous row *unless* the change is sustained in the next 2 rows (so real devaluation steps survive, isolated typos don't). Threshold is `OUTLIER_THRESHOLD_PERCENTAGE`.
- **06** expands `events_regular.json` (keys are `DD-MM`, recurring sowing/harvest dates) across every year 2018..current, then overlays `events_special.json` (keys are `YYYY-MM-DD`, elections etc.). Edit the two source files, never `events_all.json` directly.

## Frontend (`index.html`)

Single self-contained file, UI text in Spanish, Chart.js + date-fns adapter + zoom plugin loaded from jsDelivr (no bundler, no npm). On load it `fetch`es `./data/prices_sanitized.csv` (parsed by naive `split(',')`, so never introduce quoted/comma-containing values into the CSV) and `./data/events_all.json`. Only the `*_usd` and `tipo_cambio_usd` columns are used by the chart/table. A small inline `pricesData` array serves as fallback sample data if the fetch fails. Events are added as a red `scatter` dataset ("Eventos") on the same time axis; a drag-selection overlay on the canvas sets the date filter.
