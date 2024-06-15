from flask import Flask, render_template
import pandas as pd
import yfinance as yf
import plotly.graph_objs as go
import plotly.io as pio
import io
import base64

app = Flask(__name__)

@app.route('/')
def index():
    # List of stock symbols
    stocks = ['AAPL', 'MSFT', 'GOOGL']
    
    # Dictionary to store stock data
    stock_data = {}
    
    # Fetch data for each stock
    for stock in stocks:
        # check if the data is already downloaded
        exist = True
        try:
            stock_data[stock] = pd.read_csv(f'data/{stock}.csv', index_col='Date', parse_dates=True)
        except FileNotFoundError:
            exist = False
        if not exist:
            stock_data[stock] = yf.download(stock, start='2024-01-01', end='2024-06-01')
            stock_data[stock].to_csv(f'data/{stock}.csv')
    
    # Generate interactive plots with Plotly
    plots = {}
    for stock, data in stock_data.items():
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=data.index, y=data['Close'], mode='lines', name=f'{stock} Close Price'))
        fig.update_layout(title=f'{stock} Stock Price', xaxis_title='Date', yaxis_title='Close Price')
        img = pio.to_image(fig, format='png')
        plots[stock] = base64.b64encode(img).decode('utf8')

    return render_template('index.html', plots=plots)

if __name__ == '__main__':
    app.run(debug=True)
