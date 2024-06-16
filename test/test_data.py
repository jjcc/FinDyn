#Create a unit test for the readmeta function in the readmeta.py file.
#The function should read the metadata from the given file and return the count of each exchange.
#Use the given test_readmeta.py file to write the unit test.
#The test should check if the function returns the correct count of each exchange.
#The test should use the sample metadata file provided in the test folder.

import unittest
from constant import SECTOR_ETFS, ISHARE_SECTOR1_ETF, ISHARE_SECTOR2_ETF
import pandas as pd


class TestData(unittest.TestCase):
    
    def test_readmeta_empty(self):
        etf = 'IBB'
        file_name = f'data/meta/ishare_sector1/{etf}.csv'
        df_etf = pd.read_csv(file_name)

        df_vip = df_etf[df_etf['WeightJson'] >= 0.2]
        sum_vip = df_vip['WeightJson'].sum()

        dg = df_etf.groupby('Exchange')
        symbol_list = []
        for i,g  in dg:
            if "NASD" in i or "New York" in i:
                symbols = g['Symbol'].tolist()  
                symbol_list.append(symbols)
            else:
                continue
        print(symbol_list)
