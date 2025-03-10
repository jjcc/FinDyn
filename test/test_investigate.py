
import datetime
import json
import os
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

    def test_compare_stocks(self):
        '''
        check all the stocks in the ETFs are in the SP500 list or SP1500 list
        '''
        df = pd.read_csv("output/sp500_stocks.csv")
        sp500_list = df['Symbol'].tolist()

        df = pd.read_excel("output/holdings-daily-us-en-sptm.xlsx")
        sp1500_list = df['Ticker'].tolist()
        target_list = sp1500_list

        missing = {}
        for group in [INDUSTRY_ETFS, SECTOR_ETFS, ISHARE_SECTOR1_ETF, ISHARE_SECTOR2_ETF]:
            for etf in group:
                file_name = None
                if etf in SECTOR_ETFS:
                    group = 'spdr'
                    etf_lower = etf.lower()
                    if etf == 'XLSR':
                        continue
                    file_name = f'data/meta/spdr/index-holdings-{etf_lower}.csv'
                elif etf in ISHARE_SECTOR1_ETF:
                    group = 'ishare_sector1'
                    file_name = f'data/meta/ishare_sector1/{etf}.csv'
                elif etf in ISHARE_SECTOR2_ETF:
                    group = 'ishare_sector2'
                    file_name = f'data/meta/ishare_sector2/{etf}.csv'
                elif etf in INDUSTRY_ETFS:
                    group = 'spdr_industry'
                    file_name = f'data/meta/spdr_industry/{etf}.csv'
                    
                if  os.path.exists(file_name):
                    df_etf = pd.read_csv(file_name)
                    if group in ['ishare_sector1', 'ishare_sector2']:
                        df_vip = df_etf[df_etf['WeightJson'] >= 0.2]
                        df_vip = df_vip[df_vip['Exchange'].str.contains('NASD|New York')]
                        symbols = df_vip['Symbol'].tolist()
                    else:
                        symbols = df_etf['Symbol'].tolist()
                    for symbol in symbols:
                        if symbol not in target_list:
                            print(f"Symbol {symbol} (of group:{group}, etf:{etf}) not found in SP500 list")
                            if group not in missing:
                                missing[group] = {}
                            if etf not in missing[group]:
                                missing[group][etf] = []
                            missing[group][etf].append(symbol)
                else:
                    print(f"File not found for {etf}")
        #print(json.dumps(missing, indent=4))
        with open("output/missing_1500.json", "w") as f:
            f.write(json.dumps(missing, indent=4))
        pass


    def test_composit_1500(self):
        '''
        check all the stocks in the SP1500 are in the SP500 list
        '''
        df = pd.read_excel("output/holdings-daily-us-en-sptm.xlsx")
        sp1500_list = df['Ticker'].tolist()

        df = pd.read_csv("output/sp500_stocks.csv")
        sp500_list = df['Symbol'].tolist()

        set1500 = set(sp1500_list)
        len1500 = len(set1500)
        set500 = set(sp500_list)
        len500 = len(set500)
        diff = set1500 - set500
        lendiff = len(diff)
        assert lendiff == len1500 - len500
    
    def test_missing_in_sp1500(self):
        '''
        aggregate all the missing stocks in the SP1500
        '''
        with open("output/missing_1500.json") as f:
            extra = json.load(f)
        # flatten the extra
        flatten_extra = {}
        for k, v in extra.items():
            for etf, symbols in v.items():
                flatten_extra[etf] = symbols
        missing = set()
        for group in [INDUSTRY_ETFS, SECTOR_ETFS, ISHARE_SECTOR1_ETF, ISHARE_SECTOR2_ETF]:
            for etf in group:
                if etf in flatten_extra:
                    for symbol in flatten_extra[etf]:
                        missing.add(symbol)
        missing_list = list(missing)
        len_missing = len(missing_list)
        print(missing_list)
        print(f"Total missing in SP1500: {len_missing}")

