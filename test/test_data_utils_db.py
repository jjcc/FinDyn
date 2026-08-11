import sqlite3

from src.config import Config
from src.utils.data_utils import (
    get_db_connection,
    get_symbols,
    get_symbols_by_page,
)


def _create_stock_database(path):
    with sqlite3.connect(path) as connection:
        connection.execute(
            """
            CREATE TABLE stock_info (
                symbol TEXT,
                is_sp500 INTEGER,
                is_sp1500 INTEGER
            )
            """
        )
        connection.executemany(
            "INSERT INTO stock_info VALUES (?, ?, ?)",
            [
                ('BRK.B', 1, 1),
                ('MSFT', 1, 1),
                ('SMALL', 0, 1),
            ],
        )


def test_symbol_queries_use_configured_database(tmp_path, monkeypatch):
    database = tmp_path / 'configured.db'
    _create_stock_database(database)
    monkeypatch.setattr(Config, 'DB_PATH', str(database))

    assert get_symbols(2) == ['BRK.B', 'MSFT']
    assert get_symbols_by_page(is_sp500=True, page_length=2) == {
        0: ['BRK-B', 'MSFT']
    }


def test_connection_helper_accepts_explicit_path(tmp_path):
    database = tmp_path / 'explicit.db'
    connection = get_db_connection(database)
    try:
        assert connection.execute('PRAGMA database_list').fetchone()[2] == str(database)
    finally:
        connection.close()
