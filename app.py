from flask import Flask, render_template
import pandas as pd
import yfinance as yf
import plotly.graph_objs as go
import plotly.utils
import json

app = Flask(__name__)

@app.route('/')
def index():
    # List of stock symbols
    stocks = ['AAPL', 'MSFT', 'GOOGL']
    
    # Dictionary to store stock data
    stock_data = {}
    
    # Fetch data for each stock and reset the index
    for stock in stocks:
        # check if the data is already downloaded
        exist = True
        try:
            df = pd.read_csv(f'data/{stock}.csv', index_col='Date', parse_dates=True)
        except FileNotFoundError:
            exist = False
        if not exist:
            stock_data[stock] = yf.download(stock, start='2024-01-01', end='2024-06-01')
            stock_data[stock].to_csv(f'data/{stock}.csv')
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
            yaxis_title='Price',
            xaxis_rangeslider_visible=False
        )
        
        plots[stock] = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    return render_template('index.html', plots=plots)

if __name__ == '__main__':
    app.run(debug=True)
