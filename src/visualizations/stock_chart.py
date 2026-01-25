#!/usr/bin/env python3
"""
Stock Chart Visualization

This script creates a visualization of stock price data with volume and EMA indicators
for 5, 12, and 26 periods using matplotlib.
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.gridspec import GridSpec
import os
import argparse
from datetime import datetime
import pytz

def calculate_ema(data, periods):
    """
    Calculate Exponential Moving Average for the specified periods.
    
    Args:
        data: DataFrame containing 'Close' prices
        periods: List of periods to calculate EMAs for
    
    Returns:
        DataFrame with original data and added EMA columns
    """
    from src.config import Config
    
    df = data.copy()
    
    # Use standardized EMA periods
    ema_periods = Config.EMA_PERIODS
    
    for period in ema_periods:
        df[f'EMA_{period}'] = df['Close'].ewm(span=period, adjust=False).mean()
    
    return df

def convert_to_eastern_time(df):
    """
    Convert UTC timestamps to US/Eastern time.
    
    Args:
        df: DataFrame with DatetimeIndex in UTC
        
    Returns:
        DataFrame with DatetimeIndex converted to US/Eastern time
    """
    # Ensure index is datetime with timezone info (assume UTC if not specified)
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)
        
    if df.index.tz is None:
        df.index = df.index.tz_localize('UTC')
        
    # Convert to Eastern time
    df.index = df.index.tz_convert('US/Eastern')
    
    return df

def plot_stock_chart(csv_file_path, output_path=None):
    """
    Generate a stock chart with price, volume, and EMAs.
    
    Args:
        csv_file_path: Path to the CSV file containing stock data
        output_path: Optional path to save the generated chart
    """
    # Read the CSV file
    df = pd.read_csv(csv_file_path, parse_dates=['Datetime'])
    
    # Set datetime as index
    df.set_index('Datetime', inplace=True)
    
    # Convert UTC time to Eastern time
    df = convert_to_eastern_time(df)
    
    # Calculate EMAs using standardized periods
    df = calculate_ema(df, None)  # Pass None as the periods will be determined in the function
    
    # Create figure with two subplots (price and volume)
    fig = plt.figure(figsize=(14, 10))
    gs = GridSpec(2, 1, height_ratios=[3, 1])  # 3:1 ratio for price:volume
    
    # Price chart (top subplot)
    ax1 = fig.add_subplot(gs[0])
    
    # Plot price
    ax1.plot(df.index, df['Close'], color='black', linewidth=1.5, label='Price')
    
    # Plot EMAs
    ax1.plot(df.index, df['EMA_5'], color='blue', linewidth=1, label='EMA 5')
    ax1.plot(df.index, df['EMA_12'], color='green', linewidth=1, label='EMA 12')
    ax1.plot(df.index, df['EMA_26'], color='red', linewidth=1, label='EMA 26')
    
    # Configure price chart
    ticker = os.path.basename(csv_file_path).split('_')[0]
    ax1.set_title(f'{ticker} Stock Price with EMA Indicators (US/Eastern Time)')
    ax1.set_ylabel('Price')
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc='best')
    
    # Format x-axis dates
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M', tz=pytz.timezone('US/Eastern')))
    ax1.xaxis.set_major_locator(mdates.AutoDateLocator())
    
    # Volume chart (bottom subplot)
    ax2 = fig.add_subplot(gs[1], sharex=ax1)
    
    # Plot volume bars
    ax2.bar(df.index, df['Volume'], color='gray', alpha=0.7, width=0.0005)
    
    # Configure volume chart
    ax2.set_ylabel('Volume')
    ax2.grid(True, alpha=0.3)
    
    # Format x-axis dates
    plt.xticks(rotation=45)
    fig.tight_layout()
    
    # Save or show chart
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Chart saved to {output_path}")
    else:
        plt.show()
    
    plt.close()

def main():
    """Parse command line arguments and generate the chart."""
    parser = argparse.ArgumentParser(description='Generate stock price chart with volume and EMA indicators')
    parser.add_argument('file_path', help='Path to the CSV file containing stock data')
    parser.add_argument('--output', '-o', help='Path to save the chart (optional)')
    
    args = parser.parse_args()
    
    plot_stock_chart(args.file_path, args.output)

if __name__ == "__main__":
    main()