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
            'AAPL', None, '2026-01-01', '2026-08-12'
        )

    download.assert_not_called()
    assert result['Date'].tolist() == [pd.Timestamp('2026-08-11')]


def test_weekend_after_latest_friday_does_not_call_yahoo(tmp_path, monkeypatch):
    monkeypatch.setattr(Config, 'DATA_FOLDER', str(tmp_path))
    _write_cached_price(tmp_path, '2026-08-07')
    service = StockService({'AAPL': {'true': 'SPY', 'false': []}})

    with patch('src.services.stock_service.yf.download') as download:
        service.get_stock_data_old('AAPL', None, '2026-01-01', '2026-08-10')

    download.assert_not_called()
