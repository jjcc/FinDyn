from unittest.mock import patch

import pandas as pd

from src.config import Config
from src.services.stock_service import StockService


def _write_cached_price(data_folder, last_date):
    cache_folder = data_folder / 'SPY'
    cache_folder.mkdir()
    pd.DataFrame(
        {
            'Date': [last_date],
            'Open': [100.0],
            'High': [102.0],
            'Low': [99.0],
            'Close': [101.0],
            'Volume': [1000],
        }
    ).to_csv(cache_folder / 'AAPL_last.csv', index=False)


def test_cached_latest_day_does_not_request_empty_yahoo_range(tmp_path, monkeypatch):
    monkeypatch.setattr(Config, 'DATA_FOLDER', str(tmp_path))
    _write_cached_price(tmp_path, '2026-08-11')
    service = StockService({'AAPL': {'true': 'SPY', 'false': []}})

    with patch('src.services.stock_service.yf.download') as download:
        result = service.get_stock_data_old(
            'AAPL', None, '2026-08-11', '2026-08-12'
        )

    download.assert_not_called()
    assert result['Date'].tolist() == [pd.Timestamp('2026-08-11')]


def test_weekend_after_latest_friday_does_not_call_yahoo(tmp_path, monkeypatch):
    monkeypatch.setattr(Config, 'DATA_FOLDER', str(tmp_path))
    _write_cached_price(tmp_path, '2026-08-07')
    service = StockService({'AAPL': {'true': 'SPY', 'false': []}})

    with patch('src.services.stock_service.yf.download') as download:
        service.get_stock_data_old('AAPL', None, '2026-08-07', '2026-08-10')

    download.assert_not_called()


def test_requested_history_before_cache_is_backfilled(tmp_path, monkeypatch):
    monkeypatch.setattr(Config, 'DATA_FOLDER', str(tmp_path))
    _write_cached_price(tmp_path, '2026-08-10')
    service = StockService({'AAPL': {'true': 'SPY', 'false': []}})
    downloaded = pd.DataFrame(
        {
            'Open': [95.0, 97.0, 100.0],
            'High': [97.0, 99.0, 102.0],
            'Low': [94.0, 96.0, 99.0],
            'Close': [96.0, 98.0, 101.5],
            'Volume': [800, 900, 1000],
        },
        index=pd.to_datetime(['2026-08-06', '2026-08-07', '2026-08-10']),
    )
    downloaded.index.name = 'Date'

    with patch(
        'src.services.stock_service.yf.download', return_value=downloaded
    ) as download:
        result = service.get_stock_data_old(
            'AAPL', None, '2026-08-06', '2026-08-11'
        )

    download.assert_called_once()
    assert download.call_args.kwargs['start'] == '2026-08-06'
    assert download.call_args.kwargs['end'] == pd.Timestamp('2026-08-10')
    assert result['Date'].tolist() == list(
        pd.to_datetime(['2026-08-06', '2026-08-07', '2026-08-10'])
    )
    # The overlapping August 10 row returned by Yahoo replaces rather than
    # duplicates the cached row.
    assert result.loc[result['Date'] == pd.Timestamp('2026-08-10'), 'Close'].item() == 101.5


def test_malformed_multirow_cache_is_refreshed(tmp_path, monkeypatch):
    monkeypatch.setattr(Config, 'DATA_FOLDER', str(tmp_path))
    cache_folder = tmp_path / 'SPY'
    cache_folder.mkdir()
    cache_file = cache_folder / 'AAPL_last.csv'
    cache_file.write_text(
        'Price,Close,High,Low,Open,Volume\n'
        'Ticker,AAPL,AAPL,AAPL,AAPL,AAPL\n'
        'Date,,,,,\n'
    )
    downloaded = pd.DataFrame(
        {
            'Open': [100.0],
            'High': [102.0],
            'Low': [99.0],
            'Close': [101.0],
            'Volume': [1000],
        },
        index=pd.to_datetime(['2026-08-11']),
    )
    service = StockService({'AAPL': {'true': 'SPY', 'false': []}})

    with patch(
        'src.services.stock_service.yf.download', return_value=downloaded
    ) as download:
        result = service.get_stock_data_old(
            'AAPL', None, '2026-08-11', '2026-08-12'
        )

    download.assert_called_once()
    assert result['Close'].tolist() == [101.0]
    assert cache_file.read_text().startswith('Date,Open,High,Low,Close,Volume')
