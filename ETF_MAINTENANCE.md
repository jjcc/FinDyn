# ETF holdings maintenance

FinDyn reads ETF membership from `data/meta/`. Run the updater periodically to
refresh those files from the official State Street and iShares holdings pages
and rebuild `data/meta/symbol_map.json`.

Only securities listed on supported U.S. exchanges are retained. For iShares
global ETFs, foreign-exchange listings such as Tokyo, Hong Kong, and Korea are
excluded even when the provider reports their market value in U.S. dollars.

## Preview an update

Start with a dry run. It downloads and validates current holdings and reports
added and removed symbols, but does not change local files:

```bash
cd /home/jchen/workspaces/FinDyn
.venv/bin/python scripts/update_etf_holdings.py --dry-run
```

## Apply an update

```bash
cd /home/jchen/workspaces/FinDyn
.venv/bin/python scripts/update_etf_holdings.py
```

Each valid CSV is written atomically. A failed download or invalid provider
response leaves that ETF's existing file untouched. The command exits with
status 1 if any ETF fails, making it suitable for monitoring from cron.

As a safety measure, an ETF that suddenly loses more than half of its stored
symbols is rejected. Investigate whether the fund changed strategy, liquidated,
or returned incomplete provider data. After reviewing the dry-run output, an
intentional large reduction can be applied with:

```bash
.venv/bin/python scripts/update_etf_holdings.py --allow-large-removals
```

The Flask application loads `symbol_map.json` at startup. Restart Flask after a
successful update so newly added and removed symbols are reflected everywhere.

## Update one provider family

```bash
.venv/bin/python scripts/update_etf_holdings.py --provider spdr
.venv/bin/python scripts/update_etf_holdings.py --provider ishares
```

The `spdr` option includes Select Sector and SPDR industry ETFs. Provider and
ETF membership are defined in `src/constant.py`. Add a new ETF there before
expecting the updater and web routes to manage it.

## Weekly cron example

This runs every Monday at 06:00 and prevents overlapping updater processes:

```cron
0 6 * * 1 cd /home/jchen/workspaces/FinDyn && /usr/bin/flock -n /tmp/findyn-etf-update.lock .venv/bin/python scripts/update_etf_holdings.py >> log/update_etf_holdings.log 2>&1
```

Review the log for lines in this format:

```text
OK  XLK     75 holdings  +2   -1   data/meta/spdr/index-holdings-xlk.csv
      added:   NEW1, NEW2
      removed: OLD1
```

Removed symbols are removed from ETF membership and `symbol_map.json`. Existing
historical price-cache files are deliberately retained; the updater never
deletes market data automatically.
