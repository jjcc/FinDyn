#!/usr/bin/env python3
"""
Interactive Stock Chart Visualization with Plotly

This script creates an interactive visualization of stock price data with volume
and EMA indicators for 5, 12, and 26 periods using Plotly.
"""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
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
    
    for period in periods:
        df[f'EMA_{period}'] = df['Close'].ewm(span=period, adjust=False).mean()
    
    return df

def convert_to_eastern_time(df, datetime_col=None):
    """
    Convert UTC timestamps to US/Eastern time.
    
    Args:
        df: DataFrame with DatetimeIndex or datetime column in UTC
        datetime_col: Name of datetime column if not using index
        
    Returns:
        DataFrame with datetime converted to US/Eastern time
    """
    df_copy = df.copy()
    
    # If using a column instead of index
    if datetime_col is not None:
        # Ensure datetime column is datetime with timezone info (assume UTC if not specified)
        if not pd.api.types.is_datetime64_dtype(df_copy[datetime_col]):
            df_copy[datetime_col] = pd.to_datetime(df_copy[datetime_col])
            
        if df_copy[datetime_col].dt.tz is None:
            df_copy[datetime_col] = df_copy[datetime_col].dt.tz_localize('UTC')
            
        # Convert to Eastern time
        df_copy[datetime_col] = df_copy[datetime_col].dt.tz_convert('US/Eastern')
    else:
        # Using index
        if not isinstance(df_copy.index, pd.DatetimeIndex):
            df_copy.index = pd.to_datetime(df_copy.index)
            
        if df_copy.index.tz is None:
            df_copy.index = df_copy.index.tz_localize('UTC')
            
        # Convert to Eastern time
        df_copy.index = df_copy.index.tz_convert('US/Eastern')
    
    return df_copy

def plot_stock_chart_plotly(csv_file_path, output_path=None):
    """
    Generate an interactive stock chart with price, volume, and EMAs using Plotly.
    
    Args:
        csv_file_path: Path to the CSV file containing stock data
        output_path: Optional path to save the generated chart
    """
    # Read the CSV file
    df = pd.read_csv(csv_file_path, parse_dates=['Datetime'])
    
    # Convert UTC time to Eastern time
    df = convert_to_eastern_time(df, datetime_col='Datetime')
    
    # Calculate EMAs
    ema_periods = [5, 12, 26]
    df = calculate_ema(df, ema_periods)
    
    # Get ticker name from filename
    ticker = os.path.basename(csv_file_path).split('_')[0]
    title = f'{ticker} Stock Price with EMA Indicators (US/Eastern Time)'
    
    # Create figure with secondary y-axis (for volume)
    fig = make_subplots(
        rows=2, cols=1, 
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.7, 0.3],
        subplot_titles=(title, "Volume")
    )
    
    # Add candlestick chart
    fig.add_trace(
        go.Candlestick(
            x=df['Datetime'],
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name='Price',
            increasing_line_color='green',
            decreasing_line_color='red',
            showlegend=True
        ),
        row=1, col=1
    )
    
    # Add EMA traces
    colors = ['blue', 'green', 'red']  # Colors for 5, 12, 26 EMAs
    
    for period, color in zip(ema_periods, colors):
        fig.add_trace(
            go.Scatter(
                x=df['Datetime'],
                y=df[f'EMA_{period}'],
                mode='lines',
                name=f'EMA {period}',
                line=dict(color=color, width=1.5)
            ),
            row=1, col=1
        )
    
    # Add volume bar chart
    fig.add_trace(
        go.Bar(
            x=df['Datetime'],
            y=df['Volume'],
            name='Volume',
            marker=dict(color='rgba(100, 100, 100, 0.5)')
        ),
        row=2, col=1
    )
    
    # Update layout
    fig.update_layout(
        height=800,
        width=1200,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        xaxis_rangeslider_visible=False
    )
    
    # Update x-axes to show Eastern time format
    fig.update_xaxes(
        tickformat='%m-%d %H:%M',
        tickangle=45,
        title_text="Date & Time (US/Eastern)",
        row=2, col=1
    )
    
    # Update y-axes labels
    fig.update_yaxes(title_text="Price", row=1, col=1)
    fig.update_yaxes(title_text="Volume", row=2, col=1)
    
    # Save or display the chart
    if output_path:
        # Check extension, if not html, use png as default
        if not output_path.endswith('.html'):
            file_name = os.path.splitext(output_path)[0] + '.html'
        else:
            file_name = output_path
            
        fig.write_html(file_name)
        print(f"Interactive chart saved to {file_name}")
    else:
        fig.show()

def main():
    """Parse command line arguments and generate the chart."""
    parser = argparse.ArgumentParser(description='Generate interactive stock price chart with Plotly')
    parser.add_argument('file_path', help='Path to the CSV file containing stock data')
    parser.add_argument('--output', '-o', help='Path to save the chart as HTML (optional)')
    
    args = parser.parse_args()
    
    plot_stock_chart_plotly(args.file_path, args.output)

if __name__ == "__main__":
    main()