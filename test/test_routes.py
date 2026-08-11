import pytest
import pandas as pd
from unittest import mock
import sys
from types import SimpleNamespace

# Patch imports from routes.py

# Mock constants
SECTOR_ETFS = {'XLF', 'XLY'}
ISHARE_SECTOR1_ETF = {'IYZ'}
ISHARE_SECTOR2_ETF = {'IXC'}
INDUSTRY_ETFS = {'XAR'}

# Patch the module under test to inject mocks
routes_mod = sys.modules.get("src.routes.routes")
if routes_mod is None:
    import importlib.util
    import importlib.machinery
    loader = importlib.machinery.SourceFileLoader("src.routes.routes", "src/routes/routes.py")
    spec = importlib.util.spec_from_loader(loader.name, loader)
    routes_mod = importlib.util.module_from_spec(spec)
    sys.modules["src.routes.routes"] = routes_mod
    spec.loader.exec_module(routes_mod)

# Inject mocks
routes_mod.SECTOR_ETFS = SECTOR_ETFS
routes_mod.ISHARE_SECTOR1_ETF = ISHARE_SECTOR1_ETF
routes_mod.ISHARE_SECTOR2_ETF = ISHARE_SECTOR2_ETF
routes_mod.INDUSTRY_ETFS = INDUSTRY_ETFS
routes_mod.global_data = {}

@pytest.fixture(autouse=True)
def clear_global_data():
    routes_mod.global_data.clear()
    yield
    routes_mod.global_data.clear()

@mock.patch("pandas.read_csv")
def test_get_stocks_sector_etf(mock_read_csv):
    # Setup
    df = pd.DataFrame({'Symbol': ['A', 'B', 'C']})
    mock_read_csv.return_value = df
    symbols = routes_mod.get_stocks('XLF')
    assert symbols == ['A', 'B', 'C']
    assert routes_mod.global_data['etf'] == 'XLF'
    assert routes_mod.global_data['df_data'].equals(df)
    mock_read_csv.assert_called_once_with('data/meta/spdr/index-holdings-xlf.csv')

@mock.patch("pandas.read_csv")
def test_get_stocks_ishare_sector1(mock_read_csv):
    df = pd.DataFrame({
        'Symbol': ['A', 'B', 'C'],
        'WeightJson': [0.3, 0.1, 0.25],
        'Exchange': ['NASDAQ', 'New York', 'Other']
    })
    mock_read_csv.return_value = df
    symbols = routes_mod.get_stocks('IYZ')
    # Only rows with WeightJson >= 0.2 and Exchange containing NASD or New York
    assert symbols == ['A', 'C']
    mock_read_csv.assert_called_once_with('data/meta/ishare_sector1/IYZ.csv')

@mock.patch("pandas.read_csv")
def test_get_stocks_ishare_sector2(mock_read_csv):
    df = pd.DataFrame({
        'Symbol': ['X', 'Y'],
        'WeightJson': [0.21, 0.19],
        'Exchange': ['New York', 'Other']
    })
    mock_read_csv.return_value = df
    symbols = routes_mod.get_stocks('IXC')
    assert symbols == ['X']
    mock_read_csv.assert_called_once_with('data/meta/ishare_sector2/IXC.csv')

@mock.patch("pandas.read_csv")
def test_get_stocks_industry_etf(mock_read_csv):
    df = pd.DataFrame({'Symbol': ['M', 'N']})
    mock_read_csv.return_value = df
    symbols = routes_mod.get_stocks('XAR')
    assert symbols == ['M', 'N']
    mock_read_csv.assert_called_once_with('data/meta/spdr_industry/XAR.csv')

def test_get_stocks_xlsr_returns_empty():
    symbols = routes_mod.get_stocks('XLSR')
    assert symbols == []

def test_get_stocks_unknown_etf_returns_empty():
    symbols = routes_mod.get_stocks('UNKNOWN')
    assert symbols == []
