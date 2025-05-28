from datetime import datetime
import os
import sqlite3
from typing import Dict, List, Tuple
import pandas as pd

from ..services.stock_service import StockService
from typing import Dict, List
from dotenv import load_dotenv

load_dotenv()
db = os.getenv('DB_PATH')

def fetch_stock_data(stocks: List[str], socketio, symbol_map: Dict, test = False) -> Dict[str, str]:
    ## TODO: develop new stock fetching function based on database
    """Fetch and process stock data for multiple stocks"""
    stock_service = StockService(symbol_map)
    helper = Helper()
    start, end = helper.get_start_end_date(156)
    
    stock_data = {}
    total_stocks = len(stocks)
    
    for i, stock in enumerate(stocks, start=1):
        # Fetch and process stock data
        df = stock_service.get_stock_data_old(stock, None, start, end) #This is the old method not using multi_level index
        df = stock_service.calculate_emas(df)
        stock_data[stock] = df
        
        # Send progress update
        progress = int((i / total_stocks) * 100)
        if not test:
            socketio.emit('progress_update', {'progress': progress})
    
    return stock_data

def generate_plots(stock_data: Dict[str, pd.DataFrame], df_data: pd.DataFrame) -> Dict[str, str]:
    """Generate Plotly charts for all stocks"""
    stock_service = StockService({})
    plots = {}
    
    for stock, data in stock_data.items():
        info = df_data[df_data['Symbol'] == stock] if df_data is not None else pd.DataFrame()
        plot_json = stock_service.generate_plot(stock, data, info)
        plots[stock] = plot_json
        
    return plots


def get_sp500_stocks():
    """Get S&P 500 stocks"""
    import requests
    from bs4 import BeautifulSoup
    
    # URL to scrape
    url = "https://stockanalysis.com/list/sp-500-stocks/"
    
    # Fetch the page content
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Failed to load page {url}")
    
    # Parse the HTML content
    soup = BeautifulSoup(response.text, "html.parser")
    
    # Find the table containing the stocks information.
    # This example assumes there is a <table> element on the page.
    table = soup.find("table")
    if not table:
        raise Exception("Could not find the stocks table on the page.")
    
    # Extract table headers
    headers = []
    thead = table.find("thead")
    if thead:
        for th in thead.find_all("th"):
            headers.append(th.get_text(strip=True))
    else:
        # If there's no thead, try the first row of tbody as headers.
        first_row = table.find("tr")
        if first_row:
            headers = [th.get_text(strip=True) for th in first_row.find_all(["th", "td"])]
    
    # Extract table rows from tbody
    rows = []
    tbody = table.find("tbody")
    if tbody:
        for tr in tbody.find_all("tr"):
            cells = [td.get_text(strip=True) for td in tr.find_all("td")]
            if cells:
                rows.append(cells)
    else:
        # Fall back: extract rows from all tr elements excluding the header row if no tbody is present.
        for tr in table.find_all("tr")[1:]:
            cells = [td.get_text(strip=True) for td in tr.find_all("td")]
            if cells:
                rows.append(cells)
    
    # Create a DataFrame from the scraped data
    df = pd.DataFrame(rows, columns=headers)
    #print(df)
    
    return df

def get_data_by_list(symbols: List[str], 
                     start_date: str, 
                     end_date: str) -> Tuple[Dict[str, pd.DataFrame], pd.DataFrame]:
    """
    Download and organize stock data by individual symbols.
    
    Args:
        symbols: List of ticker symbols to download data for
        start_date: Start date in 'YYYY-MM-DD' format
        end_date: End date in 'YYYY-MM-DD' format
        
    Returns:
        Tuple containing:
            - Dictionary mapping each symbol to its corresponding DataFrame
            - Original combined DataFrame with all symbols
        
    Raises:
        ValueError: If symbols is not a list or is empty
        Exception: If data processing fails
    """
    if not isinstance(symbols, list) or not symbols:
        raise ValueError("Symbols must be a non-empty list")
    
    try: 
        # Download data for all symbols
        stock_service = StockService({})
        all_data = stock_service.get_data(symbols, start_date, end_date)
        
        # Organize data by symbol
        data_by_symbol = stock_service.organize_data_by_symbol(all_data, symbols)
        
        return data_by_symbol, all_data
        
    except Exception as e:
        raise Exception(f"Error processing data: {str(e)}")
        
def get_symbols(count:int,start:int = 0)->List[str]:
    conn = sqlite3.connect('stock_info.db')
    sql = f"SELECT symbol FROM stock_info LIMIT {start}, {count}"

    df = pd.read_sql(sql, conn)
    conn.close()
    return df['symbol'].tolist()


def get_symbols_by_page(is_sp500=True, page_length = 100) -> List[str]:
    """
    Retrieve the list of S&P 500 stock symbols from the database.
    
    Returns:
        List of S&P 500 stock symbols
    """
    db = os.getenv('DB_PATH')
    conn = sqlite3.connect(db)
    if is_sp500:
        sql = "SELECT symbol FROM stock_info WHERE is_sp500 = 1"
    else:
        sql = "SELECT symbol FROM stock_info WHERE is_sp500 = 0 AND is_sp1500 = 1"
    df = pd.read_sql(sql, conn)
    conn.close()
    all_list =df['symbol'].tolist()
    # replace any symbol with '.' with '-'
    all_list = [symbol.replace('.','-') for symbol in all_list]
    # segment the list into pages
    page_list = { i: all_list[i:i + page_length] for i in range(0, len(all_list), page_length)}
    return page_list




def test():
    symbols = ['AAPL', 'GOOGL']
    start_date = '2024-11-01'
    end_date = '2025-02-21'
    data_by_symbol = get_data_by_list(symbols, start_date, end_date)
    
    for symbol, df_single in data_by_symbol.items():
        print(f"\nPrice data for {symbol}:")
        print(df_single.head())

class Helper:
    def get_start_end_date_old(self, days: int) -> Tuple[str, str]:
        """Calculate start and end dates for stock data"""
        end = datetime.datetime.now()
        start = end - datetime.timedelta(days=days)
        return start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d')

    def get_start_end_date(self, days=156):
        today = pd.Timestamp.today()
        # add 1 day to today to include today in the range
        # the yfinance has parameter of [start, end), so extra day is needed
        today_ex = today + pd.DateOffset(days=1)
        today_ex_str = today_ex.strftime('%Y-%m-%d')
        # 180 ago
        start_date = today - pd.DateOffset(days=days)
        start_date_str = start_date.strftime('%Y-%m-%d')
        return start_date_str, today_ex_str   