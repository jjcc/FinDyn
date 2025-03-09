
import datetime
import json
import unittest
from constant import INDUSTRY_ETFS, SECTOR_ETFS, ISHARE_SECTOR1_ETF, ISHARE_SECTOR2_ETF
import pandas as pd
import pandas as pd
import yfinance as yf
from helper import Helper
from src.utils.data_utils import get_sp500_stocks


class TestInvestigate(unittest.TestCase):
    def setUp(self) -> None:

        self.etf = 'IBB'
        etf = self.etf
        file_name = f'data/meta/ishare_sector1/{etf}.csv'
        self.df_etf = pd.read_csv(file_name)
        self.helper = Helper()
    
    def test_get_sp500_stocks(self):
        df = get_sp500_stocks()
        # Optionally, save the DataFrame to a CSV file
        df.to_csv("output/sp500_stocks.csv", index=False)
        pass

