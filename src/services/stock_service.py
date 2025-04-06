import pandas as pd
import yfinance as yf
import plotly.graph_objs as go
import plotly.utils
import json
import datetime
import os
from typing import Dict, List, Tuple, Union

class StockService:
    def __init__(self, symbol_map: Dict):
        self.symbol_map = symbol_map
        
    def get_stock_data_old(self, stock: str, etf: str, start: str, end: str) -> pd.DataFrame:
        """
        Fetch stock data from yfinance or local cache
        The compatible function to get stock data from yfinance. It put multi_level_index to False
        """
        etfx, _ = self._mapping_etf_folder(stock, etf)
        if not os.path.exists(f'data/{etfx}'):
            os.makedirs(f'data/{etfx}')

        price_file = f'data/{etfx}/{stock}_last.csv'
        
        try:
            df = pd.read_csv(price_file, index_col='Date', parse_dates=True)
            last_date = df.index[-1]
            end_date = datetime.datetime.strptime(end, '%Y-%m-%d')
            
            # Adjust for weekends
            if end_date.weekday() == 5:
                end_date -= datetime.timedelta(days=1)
            elif end_date.weekday() == 6:
                end_date -= datetime.timedelta(days=2)
            print(f'adjusted end_date {end_date} and last_date {last_date} for {stock}')
                
            if end_date > last_date:
                next_of_last = last_date + datetime.timedelta(days=1)
                df_complement = yf.download(stock, start=next_of_last, end=end, multi_level_index=False)
                
                # Remove overlapping data
                overlap = df.index.intersection(df_complement.index)
                if not overlap.empty:
                    df_complement = df_complement.loc[~df_complement.index.isin(overlap)]
                
                if not df_complement.empty:
                    df = pd.concat([df, df_complement])
                    df.to_csv(price_file)
                    
            return df.reset_index()
            
        except (IndexError, FileNotFoundError):
            df = yf.download(stock, start=start, end=end, multi_level_index=False)
            df.to_csv(price_file)
            return df.reset_index()

    def calculate_emas(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate EMA indicators for stock data"""
        df['EMA_6'] = df['Close'].ewm(span=6, adjust=False).mean()
        df['EMA_12'] = df['Close'].ewm(span=12, adjust=False).mean()
        df['EMA_30'] = df['Close'].ewm(span=30, adjust=False).mean()
        return df

    def generate_plot(self, stock: str, data: pd.DataFrame, info: pd.DataFrame) -> str:
        """Generate Plotly chart for stock data"""
        name = self._get_stock_name(stock, info)
        
        fig = go.Figure()
        
        # Candlestick chart
        fig.add_trace(go.Candlestick(
            x=data['Date'],
            open=data['Open'],
            high=data['High'],
            low=data['Low'],
            close=data['Close'],
            name='Candlesticks',
            line=dict(width=0.5),
            whiskerwidth=0.4,
            increasing_line_color='black',
            decreasing_line_color='black',
            increasing_fillcolor='green',
            decreasing_fillcolor='red'
        ))
        
        # EMA lines
        for ema in ['EMA_6', 'EMA_12', 'EMA_30']:
            fig.add_trace(go.Scatter(
                x=data['Date'], y=data[ema], mode='lines', name=ema
            ))
            
        fig.update_layout(
            title=f'{name}',
            xaxis_title='Date',
            yaxis_title='',
            xaxis_rangeslider_visible=True,
            showlegend=False,
            margin=dict(l=0, r=0, t=30, b=20),
            height=400,
            font=dict(size=10)
        )
        
        return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    def _get_stock_name(self, stock: str, info: pd.DataFrame) -> str:
        """Get stock name from info DataFrame"""
        if len(info) > 0:
            if 'Name' in info.columns:
                return info['Name'].values[0]
            elif 'Company Name' in info.columns:
                return info['Company Name'].values[0]
        return stock

    def _mapping_etf_folder(self, stock: str, etf: str) -> Tuple[str, List[str]]:
        """Map stock to ETF folder"""
        etf_first = self.symbol_map[stock]['true']
        etfs = self.symbol_map[stock]['false']
        return etf_first, etfs


    def get_data(self, ticker_symbols: Union[str, List[str]],
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
                datetime.datetime.strptime(start_date, '%Y-%m-%d')
                datetime.datetime.strptime(end_date, '%Y-%m-%d')
            except ValueError:
                raise ValueError("Dates must be in 'YYYY-MM-DD' format")
    
            # Download data
            data = yf.download(ticker_symbols, start=start_date, end=end_date)
    
            if data.empty:
                print(f"Warning: No data found for the specified symbols and date range")
    
            return data
        except Exception as e:
            raise Exception(f"Error downloading data: {str(e)}")


def organize_data_by_symbol(data: pd.DataFrame,
                           symbols: List[str]) -> Dict[str, pd.DataFrame]:
    """
    Organize combined stock data into separate DataFrames by symbol.

    Args:
        data: Combined DataFrame with stock data for multiple symbols
        symbols: List of ticker symbols to extract

    Returns:
        Dictionary mapping each symbol to its corresponding DataFrame
    """
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
