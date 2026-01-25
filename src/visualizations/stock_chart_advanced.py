#!/usr/bin/env python3
"""
Advanced Stock Chart Visualization with mplfinance

This script creates a visualization of stock price data with volume and EMA indicators
for 5, 12, and 26 periods using mplfinance, which is specialized for financial charts.
"""

import pandas as pd
import mplfinance as mpf
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
    df = data.copy()
    
    ema_dict = {}
    for period in periods:
        ema_dict[f'EMA_{period}'] = df['Close'].ewm(span=period, adjust=False).mean()
    
    return ema_dict

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

def plot_stock_chart_mpf(csv_file_path, output_path=None):
    """
    Generate a stock chart with price, volume, and EMAs using mplfinance.
    
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
    
    # Rename columns to match mplfinance requirements
    df = df.rename(columns={
        'Open': 'Open',
        'High': 'High', 
        'Low': 'Low',
        'Close': 'Close',
        'Volume': 'Volume'
    })
    
    # Calculate EMAs
    ema_periods = [5, 12, 26]
    emas = calculate_ema(df, ema_periods)
    
    # Create a list of additional plots for the EMAs
    ema_plots = []
    colors = ['blue', 'green', 'red']  # Colors for 5, 12, 26 EMAs
    
    for (name, ema_data), color in zip(emas.items(), colors):
        ema_plots.append(
            mpf.make_addplot(ema_data, color=color, width=1, label=name)
        )
    
    # Get ticker name from filename
    ticker = os.path.basename(csv_file_path).split('_')[0]
    title = f'{ticker} Stock Price with EMA Indicators (US/Eastern Time)'
    
    # Custom style
    mc = mpf.make_marketcolors(
        up='green',
        down='red',
        edge='black',
        wick='black',
        volume='gray'
    )
    
    s = mpf.make_mpf_style(
        marketcolors=mc,
        gridstyle='-',
        y_on_right=False,
        figcolor='white',
        gridcolor='lightgray',
        facecolor='white',
        rc={'font.size': 10}
    )
    
    # Set the figure size and title
    kwargs = dict(
        type='candle',
        volume=True,
        figsize=(14, 10),
        title=title,
        style=s,
        addplot=ema_plots,
        panel_ratios=(3, 1),
        datetime_format='%m-%d %H:%M',
        xrotation=45,
        show_nontrading=False,
        tight_layout=True
    )
    
    # Create figure and axis objects to customize x-ticks directly
    import matplotlib.pyplot as plt
    fig, axes = mpf.plot(
        df, 
        **kwargs,
        returnfig=True  # Return figure instead of showing it
    )
    
    # Get the main price axis (first axis)
    ax1 = axes[0]
    
    # Increase the number of x-ticks - double the current amount
    # Current ticks
    current_ticks = len(ax1.get_xticks())
    # Double the number of ticks (at least)
    ax1.xaxis.set_major_locator(plt.MaxNLocator(current_ticks * 2))
    
    # Save or display the chart
    if output_path:
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Chart saved to {output_path}")
    else:
        plt.show()

def main():
    """Parse command line arguments and generate the chart."""
    parser = argparse.ArgumentParser(description='Generate advanced stock price chart with mplfinance')
    parser.add_argument('file_path', help='Path to the CSV file containing stock data')
    parser.add_argument('--output', '-o', help='Path to save the chart (optional)')
    
    args = parser.parse_args()
    
    plot_stock_chart_mpf(args.file_path, args.output)

if __name__ == "__main__":
    main()