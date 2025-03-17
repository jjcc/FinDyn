import datetime
from typing import Dict, List, Tuple
import pandas as pd
from ..services.stock_service import StockService
import yfinance as yf
from typing import Dict, List, Union, Optional

def fetch_stock_data(stocks: List[str], socketio, symbol_map: Dict) -> Dict[str, str]:
    ## TODO: develop new stock fetching function based on database
    """Fetch and process stock data for multiple stocks"""
    stock_service = StockService(symbol_map)
    helper = Helper()
    start, end = helper.get_start_end_date(156)
    
    stock_data = {}
    total_stocks = len(stocks)
    
    for i, stock in enumerate(stocks, start=1):
        # Fetch and process stock data
        df = stock_service.get_stock_data(stock, None, start, end)
        df = stock_service.calculate_emas(df)
        stock_data[stock] = df
        
        # Send progress update
        progress = int((i / total_stocks) * 100)
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

def get_data(ticker_symbols: Union[str, List[str]], 
             start_date: str, 
             end_date: str) -> pd.DataFrame:
    """
    Download historical stock data from Yahoo Finance.
    
    Args:
        ticker_symbols: A string or list of ticker symbols to download data for
        start_date: Start date in 'YYYY-MM-DD' format
        end_date: End date in 'YYYY-MM-DD' format
        
    Returns:
        DataFrame containing the historical price data
        
    Raises:
        ValueError: If date format is invalid
        Exception: If data download fails
    """
    try:
        # Validate date formats
        try:
            datetime.strptime(start_date, '%Y-%m-%d')
            datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            raise ValueError("Dates must be in 'YYYY-MM-DD' format")
            
        # Download data
        data = yf.download(ticker_symbols, start=start_date, end=end_date)
        
        if data.empty:
            print(f"Warning: No data found for the specified symbols and date range")
            
        return data
    except Exception as e:
        raise Exception(f"Error downloading data: {str(e)}")


def get_data_by_list(symbols: List[str], 
                     start_date: str, 
                     end_date: str) -> Dict[str, pd.DataFrame]:
    """
    Download and organize stock data by individual symbols.
    
    Args:
        symbols: List of ticker symbols to download data for
        start_date: Start date in 'YYYY-MM-DD' format
        end_date: End date in 'YYYY-MM-DD' format
        
    Returns:
        Dictionary mapping each symbol to its corresponding DataFrame
        
    Raises:
        ValueError: If symbols is not a list or is empty
        Exception: If data processing fails
    """
    if not isinstance(symbols, list) or not symbols:
        raise ValueError("Symbols must be a non-empty list")
        
    try:
        # Download data for all symbols
        data = get_data(symbols, start_date, end_date)
        data_by_symbol = {}
        
        # Check if we have multiple symbols
        if isinstance(data.columns, pd.MultiIndex):
            # For multiple symbols, extract data for each symbol
            for symbol in symbols:
                try:
                    # Get data for single symbol and flatten the MultiIndex
                    df_single = data.xs(symbol, level=1, axis=1)
                    data_by_symbol[symbol] = df_single
                except KeyError:
                    print(f"Warning: No data found for symbol {symbol}")
        else:
            # For single symbol (when only one symbol is valid)
            if len(symbols) == 1:
                data_by_symbol[symbols[0]] = data
            else:
                print("Warning: Expected multiple symbols but received single dataset")
                
        return data_by_symbol
    except Exception as e:
        raise Exception(f"Error processing data: {str(e)}")

def test():
    symbols = ['AAPL', 'GOOGL']
    start_date = '2024-11-01'
    end_date = '2025-02-21'
    data_by_symbol = get_data_by_list(symbols, start_date, end_date)
    
    for symbol, df_single in data_by_symbol.items():
        print(f"\nPrice data for {symbol}:")
        print(df_single.head())

class Helper:
    def get_start_end_date(self, days: int) -> Tuple[str, str]:
        """Calculate start and end dates for stock data"""
        end = datetime.datetime.now()
        start = end - datetime.timedelta(days=days)
        return start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d')
