import datetime
from typing import Dict, List, Tuple
import pandas as pd
from ..services.stock_service import StockService

def fetch_stock_data(stocks: List[str], socketio, symbol_map: Dict) -> Dict[str, str]:
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

class Helper:
    def get_start_end_date(self, days: int) -> Tuple[str, str]:
        """Calculate start and end dates for stock data"""
        end = datetime.datetime.now()
        start = end - datetime.timedelta(days=days)
        return start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d')
