import unittest
import re
import pandas as pd
import sqlite3


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
            self.cursor.execute("INSERT INTO stock_info (symbol, is_etf, name) VALUES (?,?, ?)", (ticker, 0,  name))
        self.conn.commit()
        pass

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

