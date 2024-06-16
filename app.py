from flask import Flask, render_template, request
import pandas as pd
import yfinance as yf
import plotly.graph_objs as go
import plotly.utils
import json
from flask_paginate import Pagination, get_page_parameter

app = Flask(__name__)

@app.route('/')
def index():
    # List of stock symbols
    stocks = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX', 'BABA', 'INTC', 'CSCO', 'ADBE']
    
    # Pagination
    page = request.args.get(get_page_parameter(), type=int, default=1)
    per_page = 8
    offset = (page - 1) * per_page
    paginated_stocks = stocks[offset:offset + per_page]
    
    # Dictionary to store stock data
    stock_data = {}
    
    # Fetch data for each stock and reset the index
    for stock in paginated_stocks:
        # check if the data is already downloaded
        exist = True
        try:
            df = pd.read_csv(f'data/{stock}.csv', index_col='Date', parse_dates=True)
        except FileNotFoundError:
            exist = False
        if not exist:
            df = yf.download(stock, start='2024-01-01', end='2024-06-01')
            df.to_csv(f'data/{stock}.csv')
        df.reset_index(inplace=True)
        
        # Calculate EMAs
        df['EMA_5'] = df['Close'].ewm(span=5, adjust=False).mean()
        df['EMA_13'] = df['Close'].ewm(span=13, adjust=False).mean()
        df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
        
        stock_data[stock] = df
    
    # Generate interactive plots with Plotly and convert to JSON
    plots = {}
    for stock, data in stock_data.items():
        fig = go.Figure()
        
        # Add candlestick chart
        fig.add_trace(go.Candlestick(
            x=data['Date'],
            open=data['Open'],
            high=data['High'],
            low=data['Low'],
            close=data['Close'],
            name='Candlesticks'
        ))
        
        # Add EMA lines
        fig.add_trace(go.Scatter(
            x=data['Date'], y=data['EMA_5'], mode='lines', name='EMA 5'
        ))
        fig.add_trace(go.Scatter(
            x=data['Date'], y=data['EMA_13'], mode='lines', name='EMA 13'
        ))
        fig.add_trace(go.Scatter(
            x=data['Date'], y=data['EMA_50'], mode='lines', name='EMA 50'
        ))
        
        fig.update_layout(
            title=f'{stock} Stock Price',
            xaxis_title='Date',
            yaxis_title='',
            xaxis_rangeslider_visible=False,
            showlegend=False,
            margin=dict(l=20, r=20, t=30, b=20),  # Reduce left and right margins
            height=300,  # Adjust height
            font=dict(size=10)  # Adjust font size
        )
        
        plots[stock] = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    pagination = Pagination(page=page, total=len(stocks), per_page=per_page, css_framework='bootstrap4')

    return render_template('index.html', plots=plots, pagination=pagination)

if __name__ == '__main__':
    app.run(debug=True)
