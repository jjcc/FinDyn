#!/usr/bin/env python3
"""Copy a legacy ETF SQLite database into FinDyn and normalize it."""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import Config  # noqa: E402
from src.etl.etf_prices import connect_database  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--destination", type=Path, default=Path(Config.ETF_PRICE_DB))
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    source = args.source.resolve()
    destination = args.destination.resolve()
    if not source.is_file():
        parser.error(f"source database does not exist: {source}")
    if destination.exists() and not args.force:
        parser.error(f"destination exists: {destination}; use --force to replace it")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".importing")
    shutil.copy2(source, temporary)
    try:
        with connect_database(temporary) as connection:
            rows = connection.execute("SELECT COUNT(*) FROM daily_tick").fetchone()[0]
            symbols = connection.execute(
                "SELECT COUNT(DISTINCT Symbol) FROM daily_tick"
            ).fetchone()[0]
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)
    print(f"Migrated {rows} rows for {symbols} symbols to {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
