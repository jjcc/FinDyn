#!/usr/bin/env python3
"""Incrementally update ETF prices and regenerate sector chart images."""

from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import Config  # noqa: E402
from src.constant import ETF_PRICE_SYMBOLS  # noqa: E402
from src.etl.etf_prices import (  # noqa: E402
    connect_database,
    create_session,
    generate_charts,
    update_symbol,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=Path(Config.ETF_PRICE_DB))
    parser.add_argument(
        "--chart-dir", type=Path, default=Path(Config.ETF_CHART_FOLDER)
    )
    parser.add_argument("--symbol", action="append", dest="symbols")
    parser.add_argument("--through", type=dt.date.fromisoformat, default=dt.date.today())
    parser.add_argument(
        "--default-start",
        type=dt.date.fromisoformat,
        default=dt.date.today() - dt.timedelta(days=225),
    )
    parser.add_argument("--timeout", type=float, default=20)
    parser.add_argument("--skip-download", action="store_true")
    parser.add_argument("--skip-charts", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    symbols = sorted(set(args.symbols or ETF_PRICE_SYMBOLS))
    unknown = set(symbols) - set(ETF_PRICE_SYMBOLS)
    if unknown:
        print(f"Warning: explicitly updating unconfigured symbols: {sorted(unknown)}")
    failures: list[str] = []
    with connect_database(args.db) as connection:
        if not args.skip_download:
            token = Config.TIINGO_API_TOKEN.strip()
            if not token:
                print("TIINGO_API_TOKEN is required for price downloads", file=sys.stderr)
                return 2
            session = create_session()
            for symbol in symbols:
                try:
                    result = update_symbol(
                        connection,
                        session,
                        symbol,
                        token,
                        args.default_start,
                        args.through,
                        args.timeout,
                    )
                    print(
                        f"OK   {symbol:<5} start={result.start_date} rows={result.rows}"
                    )
                except Exception as error:
                    failures.append(symbol)
                    print(f"FAIL {symbol:<5} {error}", file=sys.stderr)
        if not args.skip_charts:
            generated, skipped = generate_charts(
                connection, symbols, args.chart_dir, (111, 156), args.through
            )
            print(f"Charts generated: {generated}; no data: {len(skipped)}")
            if skipped:
                print(f"No chart data: {', '.join(skipped)}")
    if failures:
        print(f"Completed with {len(failures)} download failure(s).", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
