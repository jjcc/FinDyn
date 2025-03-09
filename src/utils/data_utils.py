import datetime
from typing import Dict, List, Tuple
import pandas as pd
from ..services.stock_service import StockService

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
    


class Helper:
    def get_start_end_date(self, days: int) -> Tuple[str, str]:
        """Calculate start and end dates for stock data"""
        end = datetime.datetime.now()
        start = end - datetime.timedelta(days=days)
        return start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d')
