"""Incremental ETF price ingestion and sector-chart generation."""

from __future__ import annotations

from dataclasses import dataclass
import datetime as dt
import io
import os
from pathlib import Path
import sqlite3
import tempfile
from typing import Iterable

import mplfinance as mpf
import matplotlib.pyplot as plt
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


PRICE_COLUMNS = (
    "date", "open", "high", "low", "close", "volume", "adjOpen", "adjLow",
    "adjHigh", "adjClose", "adjVolume", "divCash", "splitFactor", "Symbol",
)


@dataclass(frozen=True)
class UpdateResult:
    symbol: str
    start_date: str
    rows: int


def connect_database(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA busy_timeout=30000")
    ensure_schema(connection)
    return connection


def ensure_schema(connection: sqlite3.Connection) -> None:
    connection.execute(
        """CREATE TABLE IF NOT EXISTS daily_tick (
            date TEXT NOT NULL, open REAL, high REAL, low REAL, close REAL,
            volume REAL, adjLow REAL, adjClose REAL, adjHigh REAL, adjOpen REAL,
            adjVolume REAL, divCash REAL, splitFactor REAL, Symbol TEXT NOT NULL
        )"""
    )
    unique_index = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='index' "
        "AND name='ux_daily_tick_symbol_date'"
    ).fetchone()
    if not unique_index:
        # Imported legacy databases contain duplicate rows. Keep the newest
        # row once, before enforcing the natural key used by future updates.
        connection.execute(
            """DELETE FROM daily_tick
               WHERE rowid NOT IN (
                   SELECT MAX(rowid) FROM daily_tick GROUP BY Symbol, date
               )"""
        )
        connection.execute(
            "CREATE UNIQUE INDEX ux_daily_tick_symbol_date "
            "ON daily_tick(Symbol, date)"
        )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS ix_daily_tick_symbol_date "
        "ON daily_tick(Symbol, date DESC)"
    )
    connection.commit()


def latest_date(connection: sqlite3.Connection, symbol: str) -> dt.date | None:
    value = connection.execute(
        "SELECT MAX(date(date)) FROM daily_tick WHERE Symbol = ?", (symbol,)
    ).fetchone()[0]
    return dt.date.fromisoformat(value) if value else None


def create_session() -> requests.Session:
    retry = Retry(
        total=3,
        connect=3,
        read=3,
        backoff_factor=1,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
    )
    session = requests.Session()
    session.headers["User-Agent"] = "FinDyn ETF price updater/1.0"
    session.mount("https://", HTTPAdapter(max_retries=retry))
    return session


def download_prices(
    session: requests.Session,
    symbol: str,
    start_date: str,
    end_date: str,
    token: str,
    timeout: float = 20,
) -> pd.DataFrame:
    response = session.get(
        f"https://api.tiingo.com/tiingo/daily/{symbol}/prices",
        params={
            "startDate": start_date,
            "endDate": end_date,
            "format": "csv",
            "token": token,
        },
        timeout=timeout,
    )
    response.raise_for_status()
    if not response.text.strip():
        return pd.DataFrame(columns=PRICE_COLUMNS)
    frame = pd.read_csv(io.StringIO(response.text))
    if frame.empty:
        return pd.DataFrame(columns=PRICE_COLUMNS)
    required = set(PRICE_COLUMNS) - {"Symbol"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"Tiingo response for {symbol} is missing {sorted(missing)}")
    frame["Symbol"] = symbol
    frame["date"] = pd.to_datetime(frame["date"], utc=True).dt.strftime(
        "%Y-%m-%dT%H:%M:%S.000Z"
    )
    return frame[list(PRICE_COLUMNS)]


def upsert_prices(connection: sqlite3.Connection, frame: pd.DataFrame) -> int:
    if frame.empty:
        return 0
    placeholders = ",".join("?" for _ in PRICE_COLUMNS)
    updates = ",".join(
        f'"{column}"=excluded."{column}"'
        for column in PRICE_COLUMNS
        if column not in {"Symbol", "date"}
    )
    sql = (
        f"INSERT INTO daily_tick ({','.join(PRICE_COLUMNS)}) VALUES ({placeholders}) "
        f"ON CONFLICT(Symbol, date) DO UPDATE SET {updates}"
    )
    connection.executemany(
        sql, frame.loc[:, PRICE_COLUMNS].itertuples(index=False, name=None)
    )
    connection.commit()
    return len(frame)


def update_symbol(
    connection: sqlite3.Connection,
    session: requests.Session,
    symbol: str,
    token: str,
    default_start: dt.date,
    through: dt.date,
    timeout: float,
) -> UpdateResult:
    current = latest_date(connection, symbol)
    start = current + dt.timedelta(days=1) if current else default_start
    end = through + dt.timedelta(days=1)
    if start > through:
        return UpdateResult(symbol, start.isoformat(), 0)
    frame = download_prices(
        session, symbol, start.isoformat(), end.isoformat(), token, timeout
    )
    return UpdateResult(symbol, start.isoformat(), upsert_prices(connection, frame))


def chart_data(
    connection: sqlite3.Connection, symbol: str, days: int
) -> pd.DataFrame:
    frame = pd.read_sql_query(
        """SELECT date, adjOpen AS Open, adjHigh AS High, adjLow AS Low,
                  adjClose AS Close, adjVolume AS Volume
           FROM daily_tick WHERE Symbol = ?
           ORDER BY date(date) DESC LIMIT ?""",
        connection,
        params=(symbol, days),
    )
    if frame.empty:
        return frame
    frame["date"] = pd.to_datetime(frame["date"], utc=True).dt.tz_localize(None)
    return frame.iloc[::-1].set_index("date")


def render_chart_atomic(
    frame: pd.DataFrame, symbol: str, output: Path, through: dt.date
) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    market_colors = mpf.make_marketcolors(up="r", down="g")
    style = mpf.make_mpf_style(marketcolors=market_colors)
    descriptor = tempfile.NamedTemporaryFile(
        suffix=".png", dir=output.parent, delete=False
    )
    temporary = Path(descriptor.name)
    descriptor.close()
    try:
        mpf.plot(
            frame,
            type="candle",
            mav=(6, 12, 26),
            datetime_format="%Y-%m-%d",
            volume=True,
            title=f"{symbol}:{through.isoformat()}",
            style=style,
            tight_layout=True,
            ylabel="Price",
            ylabel_lower="Volume",
            scale_padding={"bottom": 1.1, "left": 0.8},
            figsize=(8.0, 5.75),
            savefig=str(temporary),
        )
        os.replace(temporary, output)
    finally:
        plt.close("all")
        temporary.unlink(missing_ok=True)


def generate_charts(
    connection: sqlite3.Connection,
    symbols: Iterable[str],
    output_dir: Path,
    windows: Iterable[int],
    through: dt.date,
) -> tuple[int, list[str]]:
    generated = 0
    skipped: list[str] = []
    for symbol in sorted(set(symbols)):
        symbol_generated = False
        try:
            for days in windows:
                frame = chart_data(connection, symbol, days)
                if frame.empty:
                    continue
                render_chart_atomic(
                    frame, symbol, output_dir / f"etf_{symbol}_{days}.png", through
                )
                generated += 1
                symbol_generated = True
        except Exception as error:
            skipped.append(f"{symbol} ({error})")
            continue
        if not symbol_generated:
            skipped.append(symbol)
    return generated, skipped
