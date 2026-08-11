#!/usr/bin/env python3
"""Refresh ETF holdings and rebuild FinDyn's stock-to-ETF symbol map.

The command downloads configured holdings from State Street and iShares,
validates each response, reports symbol additions/removals, and atomically
replaces valid CSV files. A provider failure never overwrites its current file.
"""

from __future__ import annotations

import argparse
import io
import json
import os
from pathlib import Path
import sys
import tempfile
from typing import Iterable

import pandas as pd
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import Config  # noqa: E402
from src.constant import (  # noqa: E402
    INDUSTRY_ETFS,
    ISHARE_SECTOR1_ETF,
    ISHARE_SECTOR2_ETF,
    SECTOR_ETFS,
    US_EXCHANGES,
)


SSGA_URL = (
    "https://www.ssga.com/library-content/products/fund-data/etfs/us/"
    "holdings-daily-us-en-{ticker}.xlsx"
)
ISHARES_ORIGIN = "https://www.ishares.com"
ISHARES_COLUMNS = [
    "Symbol",
    "Name",
    "Sector",
    "Type",
    "MarketCapJson",
    "WeightJson",
    "NotionCapJson",
    "Share",
    "CUSIP",
    "ISIN",
    "SEDOL",
    "Unknown",
    "Country",
    "Exchange",
    "Currency",
    "LastPrice",
    "LastPriceDate",
]
GROUPS = (
    ("spdr", sorted(SECTOR_ETFS - {"XLSR"})),
    ("ishare_sector1", sorted(ISHARE_SECTOR1_ETF)),
    ("ishare_sector2", sorted(ISHARE_SECTOR2_ETF)),
    ("spdr_industry", sorted(INDUSTRY_ETFS)),
)


def create_session() -> requests.Session:
    retry = Retry(
        total=2,
        connect=2,
        read=2,
        backoff_factor=0.5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
    )
    session = requests.Session()
    session.headers.update(
        {"User-Agent": "FinDyn ETF holdings updater/1.0 (+local maintenance)"}
    )
    session.mount("https://", HTTPAdapter(max_retries=retry))
    return session


def parse_ssga_xlsx(content: bytes) -> pd.DataFrame:
    raw = pd.read_excel(io.BytesIO(content), sheet_name=0, header=None)
    header_row = next(
        (
            index
            for index, row in raw.iterrows()
            if row.astype(str).str.strip().str.casefold().eq("ticker").any()
        ),
        None,
    )
    if header_row is None:
        raise ValueError("State Street workbook has no Ticker header")

    frame = pd.read_excel(io.BytesIO(content), sheet_name=0, header=header_row)
    frame = frame.rename(
        columns={
            "Ticker": "Symbol",
            "Weight": "Index Weight",
            "Name": "Company Name",
        }
    )
    frame = normalize_holdings(frame, required={"Symbol", "Company Name"})
    if "SEDOL" in frame.columns:
        frame = frame[
            frame["SEDOL"].astype("string").str.strip().fillna("-").ne("-")
        ]
    return normalize_holdings(frame, required={"Symbol", "Company Name"})


def download_ssga(
    session: requests.Session, ticker: str, timeout: float
) -> pd.DataFrame:
    response = session.get(
        SSGA_URL.format(ticker=ticker.lower()), timeout=timeout
    )
    response.raise_for_status()
    return parse_ssga_xlsx(response.content)


def _raw_value(value):
    return value.get("raw") if isinstance(value, dict) else value


def filter_us_listings(frame: pd.DataFrame) -> pd.DataFrame:
    """Keep securities whose primary listing is on a supported US exchange."""
    if "Exchange" not in frame.columns:
        raise ValueError("holdings data has no Exchange column for US filtering")
    exchanges = frame["Exchange"].astype("string").str.strip().str.casefold()
    return frame[exchanges.isin(US_EXCHANGES)].copy()


def parse_ishares_records(records: list) -> pd.DataFrame:
    frame = pd.DataFrame(records)
    if frame.empty:
        raise ValueError("iShares holdings response is empty")
    if len(frame.columns) == 18:
        frame = frame.drop(columns=[2])
        frame.columns = range(17)
    if len(frame.columns) != 17:
        raise ValueError(
            f"iShares returned {len(frame.columns)} columns; expected 17 or 18"
        )

    frame.columns = ISHARES_COLUMNS
    for column in ("MarketCapJson", "WeightJson", "NotionCapJson", "Share", "Unknown"):
        frame[column] = frame[column].map(_raw_value)
    for column in ("MarketCapJson", "WeightJson", "NotionCapJson", "Share"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame = frame[frame["Type"].astype("string").str.casefold().eq("equity")]
    frame = filter_us_listings(frame)
    return normalize_holdings(
        frame,
        required={"Symbol", "WeightJson", "Exchange"},
        allow_empty=True,
    )


def parse_ishares_csv(content: bytes) -> pd.DataFrame:
    lines = content.decode("utf-8-sig").splitlines()
    header_row = next(
        (index for index, line in enumerate(lines) if line.startswith("Ticker,")),
        None,
    )
    if header_row is None:
        raise ValueError("iShares CSV has no Ticker header")

    frame = pd.read_csv(io.StringIO("\n".join(lines[header_row:])))
    if frame.empty:
        raise ValueError("iShares holdings CSV is empty")
    frame = frame.rename(
        columns={
            "Ticker": "Symbol",
            "Market Value": "MarketCapJson",
            "Weight (%)": "WeightJson",
            "Notional Value": "NotionCapJson",
            "Quantity": "Share",
            "Location": "Country",
            "Price": "LastPrice",
            "Accrual Date": "LastPriceDate",
        }
    )
    # Current exports may include both a security "Type" column and the
    # broader "Asset Class" used by the legacy data files.  Assign instead of
    # renaming so we never create two columns named Type.
    if "Asset Class" in frame.columns:
        frame["Type"] = frame["Asset Class"]
    for column in ISHARES_COLUMNS:
        if column not in frame.columns:
            frame[column] = pd.NA
    for column in (
        "MarketCapJson",
        "WeightJson",
        "NotionCapJson",
        "Share",
        "LastPrice",
    ):
        frame[column] = pd.to_numeric(
            frame[column].astype("string").str.replace(",", "", regex=False),
            errors="coerce",
        )
    frame = frame[frame["Type"].astype("string").str.casefold().eq("equity")]
    frame = filter_us_listings(frame)
    return normalize_holdings(
        frame[ISHARES_COLUMNS],
        required={"Symbol", "WeightJson", "Exchange"},
        allow_empty=True,
    )


def download_ishares(
    session: requests.Session,
    product_path: str,
    timeout: float,
) -> pd.DataFrame:
    product_url = requests.compat.urljoin(ISHARES_ORIGIN, product_path)
    product_response = session.get(product_url, timeout=timeout)
    product_response.raise_for_status()
    soup = BeautifulSoup(product_response.text, "html.parser")

    csv_link = soup.find(
        "a", href=lambda value: value and value.endswith("latest-holdings.csv")
    )
    if csv_link:
        holdings_response = session.get(
            requests.compat.urljoin(ISHARES_ORIGIN, csv_link["href"]),
            timeout=timeout,
        )
        holdings_response.raise_for_status()
        return parse_ishares_csv(holdings_response.content)

    # Compatibility fallback for the previous iShares product-page format.
    holdings_tab = soup.find(id="allHoldingsTab")
    ajax_path = holdings_tab.get("data-ajaxuri") if holdings_tab else None
    if not ajax_path:
        raise ValueError("iShares product page has no holdings endpoint")

    holdings_response = session.get(
        requests.compat.urljoin(ISHARES_ORIGIN, ajax_path), timeout=timeout
    )
    holdings_response.raise_for_status()
    payload = holdings_response.json()
    records = payload.get("aaData")
    if not isinstance(records, list):
        raise ValueError("iShares holdings response has no aaData list")
    return parse_ishares_records(records)


def normalize_holdings(
    frame: pd.DataFrame,
    required: set[str],
    allow_empty: bool = False,
) -> pd.DataFrame:
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"holdings data is missing columns: {sorted(missing)}")
    frame = frame.copy()
    frame["Symbol"] = frame["Symbol"].astype("string").str.strip()
    frame = frame[
        frame["Symbol"].notna()
        & frame["Symbol"].ne("")
        & frame["Symbol"].ne("-")
    ]
    frame = frame.drop_duplicates(subset=["Symbol"], keep="first")
    if frame.empty and not allow_empty:
        raise ValueError("holdings response contains no symbols")
    return frame.reset_index(drop=True)


def holdings_path(meta_dir: Path, group: str, ticker: str) -> Path:
    filename = (
        f"index-holdings-{ticker.lower()}.csv" if group == "spdr" else f"{ticker}.csv"
    )
    return meta_dir / group / filename


def read_symbols(path: Path) -> set[str]:
    if not path.exists():
        return set()
    frame = pd.read_csv(path, usecols=["Symbol"])
    return set(frame["Symbol"].dropna().astype(str).str.strip()) - {""}


def symbol_changes(path: Path, new_frame: pd.DataFrame) -> tuple[set[str], set[str]]:
    old = read_symbols(path)
    new = set(new_frame["Symbol"].dropna().astype(str).str.strip()) - {""}
    return new - old, old - new


def validate_removal_size(
    path: Path,
    new_frame: pd.DataFrame,
    allow_large_removals: bool,
    minimum_ratio: float = 0.5,
) -> None:
    old = read_symbols(path)
    if allow_large_removals or len(old) < 10:
        return
    new_count = new_frame["Symbol"].dropna().astype(str).str.strip().nunique()
    if new_count < len(old) * minimum_ratio:
        removed_percent = (1 - new_count / len(old)) * 100
        raise ValueError(
            f"refusing {removed_percent:.0f}% holdings reduction "
            f"({len(old)} -> {new_count}); review it and rerun with "
            "--allow-large-removals"
        )


def atomic_write_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".tmp", dir=path.parent, delete=False
    ) as temporary:
        temporary_path = Path(temporary.name)
    try:
        frame.to_csv(temporary_path, index=False)
        os.replace(temporary_path, path)
    finally:
        temporary_path.unlink(missing_ok=True)


def atomic_write_json(value: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", suffix=".tmp", dir=path.parent, delete=False
    ) as temporary:
        temporary_path = Path(temporary.name)
        json.dump(value, temporary, indent=4, sort_keys=True)
        temporary.write("\n")
    try:
        os.replace(temporary_path, path)
    finally:
        temporary_path.unlink(missing_ok=True)


def load_existing_map(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def build_symbol_map(
    meta_dir: Path,
    existing_map: dict | None = None,
    overrides: dict[Path, pd.DataFrame] | None = None,
) -> dict:
    memberships: dict[str, list[str]] = {}
    overrides = overrides or {}
    existing_map = existing_map or {}

    for group, tickers in GROUPS:
        for ticker in tickers:
            path = holdings_path(meta_dir, group, ticker)
            if path in overrides:
                symbols = overrides[path]["Symbol"]
            elif path.exists():
                symbols = pd.read_csv(path, usecols=["Symbol"])["Symbol"]
            else:
                continue
            for symbol in symbols.dropna().astype(str).str.strip():
                if not symbol:
                    continue
                memberships.setdefault(symbol, [])
                if ticker not in memberships[symbol]:
                    memberships[symbol].append(ticker)

    result = {}
    for symbol, etfs in memberships.items():
        previous_primary = existing_map.get(symbol, {}).get("true")
        primary = previous_primary if previous_primary in etfs else etfs[0]
        result[symbol] = {
            "true": primary,
            "false": [ticker for ticker in etfs if ticker != primary],
        }
    return result


def format_symbols(symbols: Iterable[str], limit: int = 12) -> str:
    values = sorted(symbols)
    shown = ", ".join(values[:limit])
    return shown + (f", … (+{len(values) - limit})" if len(values) > limit else "")


def load_ishares_links(meta_dir: Path) -> dict[str, str]:
    info_path = meta_dir / "ishare_etf_info.csv"
    info = pd.read_csv(info_path, usecols=["Ticker", "Link"])
    links = dict(zip(info["Ticker"], info["Link"]))
    missing = (ISHARE_SECTOR1_ETF | ISHARE_SECTOR2_ETF) - set(links)
    if missing:
        raise ValueError(f"iShares metadata has no links for: {sorted(missing)}")
    return links


def update_holdings(
    provider: str,
    meta_dir: Path,
    timeout: float,
    dry_run: bool,
    allow_large_removals: bool,
) -> int:
    session = create_session()
    overrides: dict[Path, pd.DataFrame] = {}
    failures = 0
    links = load_ishares_links(meta_dir) if provider in ("all", "ishares") else {}

    selected_groups = [
        (group, tickers)
        for group, tickers in GROUPS
        if provider == "all"
        or (provider == "ishares" and group.startswith("ishare_"))
        or (provider == "spdr" and group.startswith("spdr"))
    ]

    for group, tickers in selected_groups:
        for ticker in tickers:
            path = holdings_path(meta_dir, group, ticker)
            try:
                if group.startswith("ishare_"):
                    frame = download_ishares(session, links[ticker], timeout)
                else:
                    frame = download_ssga(session, ticker, timeout)
                validate_removal_size(path, frame, allow_large_removals)
                added, removed = symbol_changes(path, frame)
                overrides[path] = frame
                status = "DRY" if dry_run else "OK "
                print(
                    f"{status} {ticker:<5} {len(frame):>4} holdings  "
                    f"+{len(added):<3} -{len(removed):<3}  {path}"
                )
                if added:
                    print(f"      added:   {format_symbols(added)}")
                if removed:
                    print(f"      removed: {format_symbols(removed)}")
                if not dry_run:
                    atomic_write_csv(frame, path)
            except Exception as error:
                failures += 1
                print(f"FAIL {ticker:<5} {error}", file=sys.stderr)

    map_path = meta_dir / "symbol_map.json"
    existing_map = load_existing_map(map_path)
    symbol_map = build_symbol_map(meta_dir, existing_map, overrides)
    old_symbols = set(existing_map)
    new_symbols = set(symbol_map)
    print(
        f"{'DRY' if dry_run else 'OK '} symbol_map: {len(symbol_map)} symbols  "
        f"+{len(new_symbols - old_symbols)} -{len(old_symbols - new_symbols)}"
    )
    if not dry_run:
        atomic_write_json(symbol_map, map_path)
    return failures


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--provider",
        choices=("all", "spdr", "ishares"),
        default="all",
        help="provider group to refresh (default: all)",
    )
    parser.add_argument(
        "--meta-dir",
        type=Path,
        default=Path(Config.META_DATA_FOLDER),
        help="metadata directory (default: Config.META_DATA_FOLDER)",
    )
    parser.add_argument(
        "--timeout", type=float, default=30.0, help="HTTP timeout in seconds"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="download, validate, and report without changing files",
    )
    parser.add_argument(
        "--allow-large-removals",
        action="store_true",
        help="allow an ETF to lose more than half of its previous symbols",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    failures = update_holdings(
        provider=args.provider,
        meta_dir=args.meta_dir,
        timeout=args.timeout,
        dry_run=args.dry_run,
        allow_large_removals=args.allow_large_removals,
    )
    if failures:
        print(f"Completed with {failures} failed ETF update(s).", file=sys.stderr)
        return 1
    print("ETF holdings update completed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
