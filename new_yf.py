"""
Yahoo Finance Data Retrieval Module

This module provides functions to download and process financial data from Yahoo Finance.
It allows retrieving historical price data for multiple stock symbols and organizing the data
by individual symbols.
"""

from datetime import datetime
import os
import sqlite3
from numpy import save
import pandas as pd
from src.services.stock_service import StockService
from src.utils.data_utils import  get_symbols_by_page
from dotenv import load_dotenv

load_dotenv()
db = os.getenv('DB_PATH')

# action callback functions
def action_print(symbol,df):
    print(f"\nPrice data for {symbol}:")
    print(df.head())
    print(f"Shape: {df.shape}")

def action_save_csv(symbol,df):
    output_dir = os.getenv('PRICE_INFO_FOLDER')
    file_name = f"{symbol}_data.csv"
    file_name = os.path.join(output_dir, file_name)
    df.to_csv(file_name)
    print(f"Data saved to {file_name}")    

def action_save_csv2(symbol,df):
    output_dir = os.getenv('PRICE_INFO_FOLDER')
    file_name = f"{symbol}_5m_data.csv" #Should use parameter in future
    file_name = os.path.join(output_dir, file_name)
    df.to_csv(file_name)
    print(f"Data saved to {file_name}")    



def test(start_date='2024-04-04',end_date = '2025-04-04',
         action_callback = action_save_csv , interval = '1d' ) -> None:
    """
    Test function demonstrating how to use the module.
    Downloads and displays  or saves the price data for a list of stock symbols.
    """
    page_length = 200
    page_list = get_symbols_by_page(page_length=page_length)

    save = False
    #action_callback = action_save_csv
    for page_start, slist in page_list.items():
        print(f"Page {page_start}: {slist}")
        symbols = slist
        stock_service = StockService({})
        all_data = stock_service.get_data(symbols, start_date, end_date, interval=interval)
        data_by_symbol = stock_service.organize_data_by_symbol(all_data, symbols)
        if save:
            today = datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
            all_data.to_csv(f'{today}_stock_data.csv')
        time_end = datetime.now()
        #print(f"Time taken: {time_end - time_start} for {len(slist)} symbols")
        # get the df for each symbol and call the action callback 
        for symbol, df in data_by_symbol.items():
            action_callback(symbol,df)


def test_get_saved_data() -> None:
    """
    Get the data from the saved CSV file instead of downloading

    """
    data_by_symbol = {}
    df = pd.read_csv("2025_03_17_08_54_04_stock_data.csv", header=[0, 1], index_col=0)
    # Extract unique symbols from the MultiIndex
    symbols = df.columns.get_level_values(1).unique()
    print(f"Symbols: {symbols}")

    stock_service = StockService({})
    data_by_symbol = stock_service.organize_data_by_symbol(df, symbols)
    print(data_by_symbol.keys())
    for symbol in symbols:
        df_single = data_by_symbol[symbol]
        # for testing action_save_csv2 function
        #action_save_csv2(symbol, df_single)
        print(df_single.head())



            


if __name__ == '__main__':
    start_date = '2025-04-01'
    end_date = '2025-04-04'
    interval = '5m'
    test(start_date=start_date, end_date=end_date,
         action_callback=action_save_csv2, interval=interval)
    #test_get_saved_data()


