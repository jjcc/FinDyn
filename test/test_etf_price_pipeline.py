import datetime as dt
from pathlib import Path
import sqlite3

import pandas as pd
import pytest
import requests

from src.etl.etf_prices import (
    PRICE_COLUMNS,
    chart_data,
    connect_database,
    download_prices,
    latest_date,
    upsert_prices,
    update_symbol,
)


def price_frame(symbol='WOOD', close=50.0, date='2026-08-11T00:00:00.000Z'):
    return pd.DataFrame(
        [{
            'date': date,
            'open': 49.0,
            'high': 51.0,
            'low': 48.0,
            'close': close,
            'volume': 1000,
            'adjOpen': 49.0,
            'adjLow': 48.0,
            'adjHigh': 51.0,
            'adjClose': close,
            'adjVolume': 1000,
            'divCash': 0.0,
            'splitFactor': 1.0,
            'Symbol': symbol,
        }],
        columns=PRICE_COLUMNS,
    )


def test_connect_database_deduplicates_legacy_rows(tmp_path):
    path = tmp_path / 'prices.sqlite3'
    connection = sqlite3.connect(path)
    connection.execute(
        '''CREATE TABLE daily_tick (
            date text, open real, high real, low real, close real, volume real,
            adjLow real, adjClose real, adjHigh real, adjOpen real,
            adjVolume real, divCash real, splitFactor real, Symbol text
        )'''
    )
    values = next(price_frame(close=50).itertuples(index=False, name=None))
    connection.execute(
        f"INSERT INTO daily_tick ({','.join(PRICE_COLUMNS)}) VALUES ({','.join('?' for _ in PRICE_COLUMNS)})",
        values,
    )
    values = next(price_frame(close=55).itertuples(index=False, name=None))
    connection.execute(
        f"INSERT INTO daily_tick ({','.join(PRICE_COLUMNS)}) VALUES ({','.join('?' for _ in PRICE_COLUMNS)})",
        values,
    )
    connection.commit()
    connection.close()

    with connect_database(path) as migrated:
        rows = migrated.execute(
            "SELECT close FROM daily_tick WHERE Symbol='WOOD'"
        ).fetchall()

    assert rows == [(55.0,)]


def test_upsert_replaces_same_symbol_date(tmp_path):
    with connect_database(tmp_path / 'prices.sqlite3') as connection:
        assert upsert_prices(connection, price_frame(close=50)) == 1
        assert upsert_prices(connection, price_frame(close=55)) == 1
        rows = connection.execute(
            "SELECT close FROM daily_tick WHERE Symbol='WOOD'"
        ).fetchall()

    assert rows == [(55.0,)]


def test_update_symbol_uses_its_own_latest_date(tmp_path, monkeypatch):
    calls = []
    with connect_database(tmp_path / 'prices.sqlite3') as connection:
        upsert_prices(connection, price_frame(date='2026-08-08T00:00:00.000Z'))

        def fake_download(session, symbol, start, end, token, timeout):
            calls.append((symbol, start, end))
            return pd.DataFrame(columns=PRICE_COLUMNS)

        monkeypatch.setattr('src.etl.etf_prices.download_prices', fake_download)
        update_symbol(
            connection,
            object(),
            'WOOD',
            'secret',
            dt.date(2026, 1, 1),
            dt.date(2026, 8, 11),
            20,
        )

    assert calls == [('WOOD', '2026-08-09', '2026-08-12')]


class FakeResponse:
    def __init__(self, text, status=200):
        self.text = text
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(str(self.status_code))


class FakeSession:
    def __init__(self, response):
        self.response = response
        self.kwargs = None

    def get(self, url, **kwargs):
        self.kwargs = kwargs
        return self.response


def test_download_uses_params_without_embedding_token_in_url():
    header = ','.join(column for column in PRICE_COLUMNS if column != 'Symbol')
    values = ','.join(str(value) for value in price_frame().iloc[0][:-1])
    session = FakeSession(FakeResponse(f'{header}\n{values}\n'))

    result = download_prices(
        session, 'WOOD', '2026-08-11', '2026-08-12', 'secret-token'
    )

    assert result['Symbol'].tolist() == ['WOOD']
    assert session.kwargs['params']['token'] == 'secret-token'


def test_download_rejects_http_error():
    session = FakeSession(FakeResponse('rate limited', status=429))

    with pytest.raises(requests.HTTPError):
        download_prices(session, 'WOOD', '2026-08-11', '2026-08-12', 'secret')


def test_chart_data_uses_adjusted_prices(tmp_path):
    with connect_database(tmp_path / 'prices.sqlite3') as connection:
        upsert_prices(connection, price_frame(close=50))
        frame = chart_data(connection, 'WOOD', 156)

    assert frame['Close'].tolist() == [50.0]
    assert frame.index.name == 'date'
