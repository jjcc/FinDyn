import os
import unittest
import re
import pandas as pd
import sqlite3

from constant import INDUSTRY_ETFS, SECTOR_ETFS, ISHARE_SECTOR1_ETF, ISHARE_SECTOR2_ETF


class TestDb(unittest.TestCase):
    
    def setUp(self) -> None:
        self.db = "stock_info.db"
        self.conn = sqlite3.connect(self.db)
        self.cursor = self.conn.cursor()
        self.df_sp1500 = pd.read_excel("output/holdings-daily-us-en-sptm.xlsx")
        pass

    def test_populate_sp1500(self):
        # get Ticker and Name
        df = self.df_sp1500[['Ticker','Name']]
        for index, row in df.iterrows():
            ticker = row['Ticker']
            name = row['Name']
            if ticker == '-':
                continue
            if ticker == float('nan'):
                continue
            self.cursor.execute("INSERT INTO stock_info (symbol, is_etf, is_sp1500, name) VALUES (?,?,?, ?)", (ticker, 0, 1, name))
        self.conn.commit()
        pass

    def test_populate_etf(self):
        '''
        populate the etf and the relation of etf and stocks'''
        # get the sp1500 list
        df = pd.read_excel("output/holdings-daily-us-en-sptm.xlsx")
        sp1500_list = df['Ticker'].tolist()
        target_list = sp1500_list

        # get ishare etf list
        df_ishare = pd.read_csv("data/meta/ishare_etf_info.csv")
        etf_to_name = df_ishare.set_index('Ticker')['Name'].to_dict()

        for index, group in enumerate( [INDUSTRY_ETFS, SECTOR_ETFS, ISHARE_SECTOR1_ETF, ISHARE_SECTOR2_ETF]):
            group_name = ['spdr_industry', 'spdr', 'ishare_sector1', 'ishare_sector2'][index]
            for etf in group:
                # populate the etf
                if etf in etf_to_name.keys():
                    etf_name = etf_to_name[etf]
                else:
                    etf_name = ''
                self.cursor.execute("INSERT INTO stock_info (symbol, is_etf, is_sp1500, name) VALUES (?,?,?, ?)", (etf, 1, 0, etf_name))

                # deal with stocks
                file_name = None
                #if etf in SECTOR_ETFS:
                if index == 1:
                    etf_lower = etf.lower()
                    if etf == 'XLSR':
                        continue
                    file_name = f'data/meta/spdr/index-holdings-{etf_lower}.csv'
                else:
                    file_name = f'data/meta/{group_name}/{etf}.csv'
                    
                if  os.path.exists(file_name):
                    df_etf = pd.read_csv(file_name)

                    if group_name in ['ishare_sector1', 'ishare_sector2']:
                        df_vip = df_etf[df_etf['WeightJson'] >= 0.2]
                        df_vip = df_vip[df_vip['Exchange'].str.contains('NASD|New York')]
                        symbols = df_vip['Symbol'].tolist()
                    else:
                        symbols = df_etf['Symbol'].tolist()
                    
                    if index == 1: # spdr
                        sym_to_name = df_etf.set_index('Symbol')['Company Name'].to_dict()
                    else:
                        sym_to_name = df_etf.set_index('Symbol')['Name'].to_dict()


                    for symbol in symbols:
                        # populate the relationship
                        self.cursor.execute("INSERT INTO relation (stock_symbol, belong_to_etf) VALUES (?,?)", ( symbol, etf))
                        if symbol not in target_list:
                            name = sym_to_name[symbol]
                            # check if exist
                            self.cursor.execute("SELECT * FROM stock_info WHERE symbol = ?", (symbol,))
                            if self.cursor.fetchone() is None:
                                # insert into db
                                self.cursor.execute("INSERT INTO stock_info (symbol, is_etf, is_sp1500, name) VALUES (?,?,?, ?)", (symbol, 0, 0, name))
                            
                else:
                    print(f"File not found for {etf}")
        self.conn.commit()
        pass


    def test_duplicate_symbol(self):
        # check if there is any duplicate symbol
        list = self.df_sp1500['Ticker'].tolist()
        duplicates = self._find_duplicates(list)
        print(duplicates)
        pass
        

    def _find_duplicates(self, lst):
        seen = set()
        duplicates = set()
        for item in lst:
            if item in seen:
                duplicates.add(item)
            else:
                seen.add(item)
        return list(duplicates)
    
    def test_mark_sp500(self):
        # get the sp500 list
        df = pd.read_csv("output/sp500_stocks.csv")
        sp500_list = df['Symbol'].tolist()
        for symbol in sp500_list:
            self.cursor.execute("UPDATE stock_info SET is_sp500 = 1 WHERE symbol = ?", (symbol,))
        self.conn.commit()
        pass
    
    def test_select_list(self):
        self.cursor.execute("SELECT * FROM stock_info where is_sp1500 = 1 and is_sp500 = 0")
        rows = self.cursor.fetchall()
        print(len(rows))


