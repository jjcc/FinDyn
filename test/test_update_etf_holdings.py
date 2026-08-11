import importlib.util
from pathlib import Path

import pandas as pd


SCRIPT = Path(__file__).parents[1] / 'scripts' / 'update_etf_holdings.py'
SPEC = importlib.util.spec_from_file_location('update_etf_holdings', SCRIPT)
updater = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(updater)


def test_parse_ishares_records_unwraps_raw_numbers():
    row = [
        'AAPL',
        'APPLE INC',
        'Information Technology',
        'Equity',
        {'raw': 1000.0},
        {'raw': 12.5},
        {'raw': 1000.0},
        {'raw': 5},
        '037833100',
        'US0378331005',
        '2046251',
        {'raw': 200.0},
        'United States',
        'NASDAQ',
        'USD',
        '200.00',
        '-',
    ]

    frame = updater.parse_ishares_records([row])

    assert frame.loc[0, 'Symbol'] == 'AAPL'
    assert frame.loc[0, 'WeightJson'] == 12.5
    assert frame.loc[0, 'Share'] == 5


def test_parse_current_ishares_csv_schema():
    content = b'''iShares Example ETF\nFund Holdings as of,"Aug 10, 2026"\n\nTicker,Name,Sector,Asset Class,Market Value,Weight (%),Notional Value,Quantity,Price,Location,Exchange,Currency,FX Rate,Market Currency,Accrual Date\n"AAPL","APPLE INC","Information Technology","Equity","1,000.50","12.5","1,000.50","5.00","200.10","United States","NASDAQ","USD","1.00","USD","-"\n'''

    frame = updater.parse_ishares_csv(content)

    assert frame.loc[0, 'Symbol'] == 'AAPL'
    assert frame.loc[0, 'WeightJson'] == 12.5
    assert frame.loc[0, 'MarketCapJson'] == 1000.5
    assert frame.loc[0, 'Exchange'] == 'NASDAQ'


def test_parse_current_ishares_csv_excludes_non_equity_rows():
    content = b'''Ticker,Name,Sector,Asset Class,Market Value,Weight (%),Notional Value,Quantity,Price,Location,Exchange,Currency,FX Rate,Market Currency,Accrual Date\n"AAPL","APPLE INC","Technology","Equity","1,000","99","1,000","5","200","United States","NASDAQ","USD","1","USD","-"\n"USD","US DOLLAR","Cash","Cash","10","1","10","10","1","United States","-","USD","1","USD","-"\n'''

    frame = updater.parse_ishares_csv(content)

    assert frame['Symbol'].tolist() == ['AAPL']


def test_parse_current_ishares_csv_excludes_non_us_exchange_rows():
    content = b'''Ticker,Name,Sector,Asset Class,Market Value,Weight (%),Notional Value,Quantity,Price,Location,Exchange,Currency,Accrual Date\n"AAPL","APPLE INC","Technology","Equity","900","90","900","5","180","United States","NASDAQ","USD","-"\n"2330","TAIWAN SEMICONDUCTOR","Technology","Equity","100","10","100","2","50","Taiwan","Taiwan Stock Exchange","USD","-"\n'''

    frame = updater.parse_ishares_csv(content)

    assert frame['Symbol'].tolist() == ['AAPL']


def test_us_exchange_filter_keeps_supported_us_venues():
    frame = pd.DataFrame(
        {
            'Symbol': ['NASD', 'NYSE', 'AMEX', 'BZX', 'FOREIGN'],
            'Exchange': [
                'NASDAQ',
                'New York Stock Exchange Inc.',
                'Nyse Mkt Llc',
                'Cboe BZX',
                'Tokyo Stock Exchange',
            ],
        }
    )

    filtered = updater.filter_us_listings(frame)

    assert filtered['Symbol'].tolist() == ['NASD', 'NYSE', 'AMEX', 'BZX']


def test_parse_current_ishares_csv_handles_type_and_asset_class_columns():
    content = b'''Ticker,Name,Sector,Type,Asset Class,Market Value,Weight (%),Notional Value,Quantity,Price,Location,Exchange,Currency,Accrual Date\n"AAPL","APPLE INC","Technology","Common Stock","Equity","1,000","100","1,000","5","200","United States","NASDAQ","USD","-"\n'''

    frame = updater.parse_ishares_csv(content)

    assert frame['Symbol'].tolist() == ['AAPL']
    assert frame.loc[0, 'Type'] == 'Equity'


def test_normalize_holdings_excludes_placeholder_symbol():
    frame = pd.DataFrame({'Symbol': ['-', 'AAPL'], 'Name': ['Placeholder', 'Apple']})

    normalized = updater.normalize_holdings(frame, required={'Symbol', 'Name'})

    assert normalized['Symbol'].tolist() == ['AAPL']


def test_ishares_csv_allows_valid_fund_with_no_us_listings():
    content = b'''Ticker,Name,Sector,Asset Class,Market Value,Weight (%),Notional Value,Quantity,Price,Location,Exchange,Currency,Accrual Date\n"2330","TAIWAN SEMICONDUCTOR","Technology","Equity","100","100","100","2","50","Taiwan","Taiwan Stock Exchange","USD","-"\n'''

    frame = updater.parse_ishares_csv(content)

    assert frame.empty
    assert list(frame.columns) == updater.ISHARES_COLUMNS


def test_symbol_map_preserves_existing_primary_membership(tmp_path):
    spdr = tmp_path / 'spdr'
    ishare = tmp_path / 'ishare_sector1'
    spdr.mkdir()
    ishare.mkdir()
    pd.DataFrame({'Symbol': ['AAPL', 'MSFT']}).to_csv(
        spdr / 'index-holdings-xlk.csv', index=False
    )
    pd.DataFrame({'Symbol': ['AAPL']}).to_csv(ishare / 'IYW.csv', index=False)

    symbol_map = updater.build_symbol_map(
        tmp_path,
        existing_map={'AAPL': {'true': 'IYW', 'false': ['XLK']}},
    )

    assert symbol_map['AAPL'] == {'true': 'IYW', 'false': ['XLK']}
    assert symbol_map['MSFT'] == {'true': 'XLK', 'false': []}


def test_symbol_changes_reports_additions_and_removals(tmp_path):
    path = tmp_path / 'holdings.csv'
    pd.DataFrame({'Symbol': ['OLD', 'SAME']}).to_csv(path, index=False)
    new = pd.DataFrame({'Symbol': ['SAME', 'NEW']})

    added, removed = updater.symbol_changes(path, new)

    assert added == {'NEW'}
    assert removed == {'OLD'}


def test_large_removal_requires_explicit_override(tmp_path):
    path = tmp_path / 'holdings.csv'
    pd.DataFrame({'Symbol': [f'S{i}' for i in range(20)]}).to_csv(path, index=False)
    replacement = pd.DataFrame({'Symbol': ['ONLY']})

    try:
        updater.validate_removal_size(path, replacement, allow_large_removals=False)
    except ValueError as error:
        assert '--allow-large-removals' in str(error)
    else:
        raise AssertionError('large removal should have been rejected')

    updater.validate_removal_size(path, replacement, allow_large_removals=True)
