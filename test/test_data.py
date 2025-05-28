#Create a unit test for the readmeta function in the readmeta.py file.
#The function should read the metadata from the given file and return the count of each exchange.
#Use the given test_readmeta.py file to write the unit test.
#The test should check if the function returns the correct count of each exchange.
#The test should use the sample metadata file provided in the test folder.

import datetime
import json
import socket
import unittest
from constant import INDUSTRY_ETFS, SECTOR_ETFS, ISHARE_SECTOR1_ETF, ISHARE_SECTOR2_ETF
import pandas as pd
import pandas as pd
import yfinance as yf
#from helper import Helper
from src.utils.data_utils import Helper, fetch_stock_data


class TestData(unittest.TestCase):
    def setUp(self) -> None:

        self.etf = 'IBB'
        etf = self.etf
        file_name = f'data/meta/ishare_sector1/{etf}.csv'
        self.df_etf = pd.read_csv(file_name)
        self.helper = Helper()
    
    def test_readmeta_empty(self):
        df_etf = self.df_etf
        df_vip = df_etf[df_etf['WeightJson'] >= 0.2]
        sum_vip = df_vip['WeightJson'].sum()

        dg = df_vip.groupby('Exchange')
        symbol_list = []
        for i,g  in dg:
            if "NASD" in i or "New York" in i:
                symbols = g['Symbol'].tolist()  
                symbol_list.extend(symbols)
            else:
                continue
        print(len(symbol_list))
        #print(symbol_list)
        # filter the df_vip that the column 'Exchange' contains 'NASD' or 'New York'
        df_vip2 = df_vip[df_vip['Exchange'].str.contains('NASD|New York')]
        symbol_list2 = df_vip2['Symbol'].tolist()
        #print(symbol_list2)
        set1 = set(symbol_list)
        set2 = set(symbol_list2)
        # check if the two lists are equal
        self.assertEqual(set1, set2)


    def test_retrieve_data(self):
        df_etf = self.df_etf
        df_vip = df_etf[df_etf['WeightJson'] >= 0.2]
        df_vip = df_vip[df_vip['Exchange'].str.contains('NASD|New York')]
        symbols = df_vip['Symbol'].tolist()

        start, end = self.helper.get_start_end_date(156)

        df_list = {}
        for i, stock in enumerate(symbols, start=1):

            if i > 10:
                break
            df_stk = yf.download(stock, start=start, end=end)
            df_list[stock] = df_stk
        self.assertEqual(len(df_list), 10)


    def test_complement(self):
        helper = self.helper
        start, end = helper.get_start_end_date(300)
        # Dictionary to store stock data
    
        stock = 'AVGO'

        # check if the data is already downloaded
        exist = True
        #price_file = f'data/{stock}_{end}.csv'
        price_file = f'data/{stock}_last.csv'
        try:
            df = pd.read_csv(price_file , index_col='Date', parse_dates=True)
            # check the last date
            last_date = df.index[-1]
            # get the end date from the string format of end
            end_date = datetime.datetime.strptime(end, '%Y-%m-%d')
            if end_date > last_date:
                # get the next date of the last date
                next_of_last = last_date + datetime.timedelta(days=1)
                df_complement = yf.download(stock, start=next_of_last, end=end)
                # check overlap between df and df_complement before append
                overlap = df.index.intersection(df_complement.index)
                if not overlap.empty:
                    df_complement = df_complement.loc[~df_complement.index.isin(overlap)]
                if not df_complement.empty:
                    # append the complement data to the original data
                    df = pd.concat([df, df_complement], axis=0)
                    df.to_csv(price_file)
            # sleep 10ms to simulate the delay
            import time
            time.sleep(0.01)
        except FileNotFoundError:
            exist = False
        if not exist:
            df = yf.download(stock, start=start, end=end)
            df.to_csv(price_file)
        df.reset_index(inplace=True)

    def _getData(self, etf):
        global_data = {}
        in_spdr = False
        if etf in SECTOR_ETFS:
            in_spdr = True
            etf_lower = etf.lower()
            if etf == 'XLSR':
                return []
            file_name = f'data/meta/spdr/index-holdings-{etf_lower}.csv'
            print('ETF in SPDR:', etf)
        if etf in ISHARE_SECTOR1_ETF:
            file_name = f'data/meta/ishare_sector1/{etf}.csv'
            print('ETF in iShares Sector 1:', etf)
        if etf in ISHARE_SECTOR2_ETF:
            file_name = f'data/meta/ishare_sector2/{etf}.csv'
            print('ETF in iShares Sector 2:', etf)
        if file_name:
            df_etf = pd.read_csv(file_name)
            if not in_spdr:
                # filter the data: weight >= 0.2, exchange contains 'NASD' or 'New York'
                df_vip = df_etf[df_etf['WeightJson'] >= 0.2]
                df_vip = df_vip[df_vip['Exchange'].str.contains('NASD|New York')]
                # with filtering, only 1/4 of the data is left, sum of the weight is 88%
                symbols = df_vip['Symbol'].tolist()
                print('Symbols:', symbols)
                global_data['df_data'] = df_etf
                global_data['etf'] = etf
                stocks = symbols
            else:
                # SPDR ETF
                symbols = df_etf['Symbol'].tolist()
                print('Symbols:', symbols)
                global_data['df_data'] = None
                global_data['etf'] = etf
                stocks = symbols

        return stocks

    
    def testGetData(self):
        for etf in SECTOR_ETFS:
            stocks = get_stocks(etf)
            if etf == 'XLSR':
                self.assertTrue(len(stocks) == 0)
                continue
            self.assertTrue(len(stocks) > 0)
        for etf in ISHARE_SECTOR1_ETF:
            stocks = get_stocks(etf)
            if len(stocks) == 0:
                assert (etf == 'EUFN')
                continue
            self.assertTrue(len(stocks) > 0)
        for etf in ISHARE_SECTOR2_ETF:
            stocks = get_stocks(etf)
            self.assertTrue(len(stocks) > 0)
    
    def test_walkdir(self):
        import os
        file_by_dir = {}
        for root, dirs, files in os.walk('data'):
            if root == 'data':
                continue
            if root == 'data/meta':
                continue
            print(root)
            file_by_dir[root] = files

        set_of_files = set()
        duplicates = []
        for k,v in file_by_dir.items():
            for file in v:
                if file in set_of_files:
                    print(f'Duplicate files in different directories, file name: {file}, folder name: {k}')
                    dup = f'{k}/{file}'
                    duplicates.append(dup)
                else:
                    set_of_files.add(file)
        self.assertTrue(len(file_by_dir) > 0)

    def test_duplicates(self):
        '''
        generate a symbol map to record duplicated symbols in different ETFs
        '''
        sectors = [SECTOR_ETFS, ISHARE_SECTOR1_ETF, ISHARE_SECTOR2_ETF,INDUSTRY_ETFS]
        sector_folders = ['spdr', 'ishare_sector1', 'ishare_sector2','spdr_industry']
        folder_to_sector = dict(zip(sector_folders, sectors))
        base_dir = 'data/meta'

        # build a structure that reduce the duplicated stocks
        map_info = {}

        for etf_folder in sector_folders:
            curr_folder = etf_folder
            etfs = folder_to_sector[curr_folder]
            for etf in etfs:
                if curr_folder == 'spdr':
                    if etf == 'XLSR':
                        continue
                    file_name = f'{base_dir}/{curr_folder}/index-holdings-{etf.lower()}.csv'
                else:
                    file_name = f'{base_dir}/{curr_folder}/{etf}.csv'
                try:
                    df = pd.read_csv(file_name)
                except FileNotFoundError:
                    print(f'File not found: {file_name}')
                    continue
                symbols = df['Symbol'].tolist()
                # check all the symbols in the map_info
                for s in symbols:
                    if s in map_info:
                        map_info[s][False].append(etf) 
                        print(f'Duplicate symbol: {s} in {etf}')
                    else:
                        map_info[s] = { True: etf, False: []}
        with open("symbol_map.json", "w") as f:
            json.dump(map_info, f)

    def _map_etf_folder(self, stock,etf):
        with open("data/meta/symbol_map.json", "r") as f:
            symbol_map = json.load(f)
        assert stock in symbol_map
        etf_first = symbol_map[stock]['true']
        etfs = symbol_map[stock]['false']
        return etf_first, etfs
        

    def test_symbol_map(self):
        stock = 'AAPL'
        etf = 'XLK'
        etf_first, etfs = self._map_etf_folder(stock,etf)
        print(f"Symbol: {stock}, ETF: {etf_first}, Duplicates: {etfs}")
    
    def test_fetch_data(self):
        with open("data/meta/symbol_map.json", "r") as f:
            symbol_map = json.load(f)
        stocks = ['AAPL', 'GOOGL', 'MSFT']
        socketio = None  # Assuming socketio is not used in this test
        data = fetch_stock_data(stocks, socketio, symbol_map, test=True)
        # save the data to a csv file
        assert len(data) > 0