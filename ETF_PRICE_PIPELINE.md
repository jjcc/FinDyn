# ETF price and chart pipeline

FinDyn owns both ETF metadata maintenance and ETF-level price charts. The
runtime layout is:

```text
src/etl/etf_prices.py           reusable ingestion/database/chart logic
scripts/update_etf_prices.py    command-line pipeline
scripts/migrate_etf_price_db.py one-time legacy database importer
scripts/cron_etf_prices.sh      working-directory-safe cron entry point
data/etf_prices.sqlite3         runtime database (ignored by Git)
image/sectors/                  generated chart images (ignored by Git)
```

ETF symbols are centralized in `src/constant.py`. Each symbol is updated from
its own latest stored date. Rows are unique by `(Symbol, date)` and repeated
downloads safely update the existing row.

## Configuration

Put the Tiingo credential in the existing untracked `.env` file:

```dotenv
TIINGO_API_TOKEN=your-token
```

Optional settings:

```dotenv
ETF_PRICE_DB=data/etf_prices.sqlite3
ETF_CHART_DIR=image/sectors
```

Credentials are sent as HTTP parameters and are never printed by the pipeline.

## Normal operation

Update all configured ETF prices and regenerate the 111- and 156-session
charts:

```bash
cd /home/jchen/workspaces/FinDyn
.venv/bin/python scripts/update_etf_prices.py
```

Update or redraw one ETF:

```bash
.venv/bin/python scripts/update_etf_prices.py --symbol WOOD
.venv/bin/python scripts/update_etf_prices.py --symbol WOOD --skip-download
```

A failed provider request is reported and processing continues with the other
ETFs. The command exits nonzero after finishing if any download failed. Chart
files are replaced atomically, so Flask never serves a partially written PNG.

## Cron

The wrapper resolves the project directory itself and prevents cron working
directory mistakes. Use `flock` to prevent overlapping runs:

```cron
0 18 * * 1-5 /usr/bin/flock -n /tmp/findyn-etf-prices.lock /home/jchen/workspaces/FinDyn/scripts/cron_etf_prices.sh >> /home/jchen/workspaces/FinDyn/log/cron_etf_prices.log 2>&1
```

Create the untracked log directory once with `mkdir -p log`.

After confirming the new cron job works, remove the old `Finance/cron_etf.sh`
entry. Do not run both pipelines against the new database.
