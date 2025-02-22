import datetime
from flask import Flask, render_template, request, send_file
from flask_socketio import SocketIO, emit
import pandas as pd
import yfinance as yf
import plotly.graph_objs as go
import plotly.utils
import json
from flask_paginate import Pagination, get_page_parameter
from constant import SECTOR_ETFS, ISHARE_SECTOR1_ETF, ISHARE_SECTOR2_ETF, INDUSTRY_ETFS
import io
import os

from helper import Helper
app = Flask(__name__)
#socketio = SocketIO(app, async_mode='eventlet', cors_allowed_origins='*')
socketio = SocketIO(app)

# global variables
global_data = {}
with open("data/meta/symbol_map.json", "r") as f:
    symbol_map = json.load(f)
@app.route('/')
def index():
    # List of stock symbols
    stocks = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX', 'BABA', 'INTC', 'CSCO', 'ADBE']
    etf = request.args.get('etf', default='SPY')
    if etf != 'SPY':
        stocks = get_stocks(etf)
    
    # Pagination
    page = request.args.get(get_page_parameter(), type=int, default=1)
    per_page = 20
    offset = (page - 1) * per_page
    paginated_stocks = stocks[offset:offset + per_page]
    
    pagination = Pagination(page=page, total=len(stocks), per_page=per_page, css_framework='bootstrap4')

    return render_template('index.html', stocks=paginated_stocks, etf=etf, pagination=pagination)

@app.route('/sectors')
def sectors():
    return render_template('sectors.html')

@app.route('/sectors2')
def sectors2():
    return render_template('sectors2.html')

@app.route('/sectors3')
def sectors3():
    return render_template('sectors3.html')

def get_stocks(etf):
    file_name = None
    in_spdr = False
    group = None
    if etf in SECTOR_ETFS:
        in_spdr = True
        group = 'spdr'
        etf_lower = etf.lower()
        if etf == 'XLSR':
            return []
        file_name = f'data/meta/spdr/index-holdings-{etf_lower}.csv'
        print('ETF in SPDR:', etf)
    if etf in ISHARE_SECTOR1_ETF:
        group = 'ishare_sector1'
        file_name = f'data/meta/ishare_sector1/{etf}.csv'
        print('ETF in iShares Sector 1:', etf)
    if etf in ISHARE_SECTOR2_ETF:
        group = 'ishare_sector2'
        file_name = f'data/meta/ishare_sector2/{etf}.csv'
        print('ETF in iShares Sector 2:', etf)
    if etf in INDUSTRY_ETFS:
        group = 'spdr_industry'
        file_name = f'data/meta/spdr_industry/{etf}.csv'
        print('ETF in Industry:', etf)
    if file_name:
        df_etf = pd.read_csv(file_name)
        if group in ['ishare_sector1', 'ishare_sector2']:
            # filter the data: weight >= 0.2, exchange contains 'NASD' or 'New York'
            df_vip = df_etf[df_etf['WeightJson'] >= 0.2]
            df_vip = df_vip[df_vip['Exchange'].str.contains('NASD|New York')]
            # with filtering, only 1/4 of the data is left, sum of the weight is 88%
            symbols = df_vip['Symbol'].tolist()
        elif group in ['spdr']:
            # SPDR ETF
            symbols = df_etf['Symbol'].tolist()
        elif group in ['spdr_industry']:
            # SPDR Industry ETF
            symbols = df_etf['Symbol'].tolist()
        # common for all groups
        print('Symbols:', symbols)
        global_data['df_data'] = df_etf 
        global_data['etf'] = etf
        stocks = symbols
    return stocks

def _mapping_etf_folder(stock, etf):
    # for now return the same value which works as before
    etf_first = symbol_map[stock]['true']
    etfs = symbol_map[stock]['false']
    return etf_first, etfs

@socketio.on('fetch_data')
def fetch_data(stocks):
    time = datetime.datetime.now()
    print(f'fetch_data mk0 {time}')
    helper = Helper()
    start, end = helper.get_start_end_date(156)
    # Dictionary to store stock data
    stock_data = {}
    df_data = global_data.get('df_data',None)
    etf = global_data.get('etf',None)
    # due to the shared stocks among different ETFs, we need to use alternative variable as folder
    # it needs a mapping beteen etf and folder. There's only one etf will retrieve the data in its folder and shared with other etfs

    # check if the folder f'data/{etf}' exist, if not create it
    if etf:
        if not os.path.exists(f'data/{etf}'):
            os.makedirs(f'data/{etf}')
    
    # Fetch data for each stock and reset the index
    total_stocks = len(stocks)
    time = datetime.datetime.now()
    print(f'fetch_data mk1 {time}')
    for i, stock in enumerate(stocks, start=1):
        etfx, _ = _mapping_etf_folder(stock, etf)
        if not os.path.exists(f'data/{etfx}'):
            os.makedirs(f'data/{etfx}')

        # check if the data is already downloaded
        exist = True
        #>price_file = f'data/{stock}_{end}.csv'
        if etf:
            price_file = f'data/{etfx}/{stock}_last.csv'
        else:
            price_file = f'data/{stock}_last.csv'
        try:
            df = pd.read_csv(price_file , index_col='Date', parse_dates=True)
            # check the last date
            last_date = df.index[-1]
            # get the end date from the string format of end
            end_date = datetime.datetime.strptime(end, '%Y-%m-%d')
            # if end_date is weekend, get the previous friday
            if end_date.weekday() == 5:
                end_date = end_date - datetime.timedelta(days=1)
            elif end_date.weekday() == 6:
                end_date = end_date - datetime.timedelta(days=2) 
            print(f'adjusted end_date {end_date} and last_date {last_date} for {stock}')
            if end_date > last_date:
                # get the next date of the last date
                next_of_last = last_date + datetime.timedelta(days=1)
                df_complement = yf.download(stock, start=next_of_last, end=end, multi_level_index=False)
                # check overlap between df and df_complement before append
                overlap = df.index.intersection(df_complement.index)
                if not overlap.empty:
                    df_complement = df_complement.loc[~df_complement.index.isin(overlap)]
                if not df_complement.empty:
                    # append the complement data to the original data
                    df = pd.concat([df, df_complement], axis=0)
                    df.to_csv(price_file)
            # sleep 10ms to simulate the delay
            import time
            time.sleep(0.01)
        except IndexError:
            continue
        except FileNotFoundError:
            exist = False
        if not exist:
            df = yf.download(stock, start=start, end=end)
            df.to_csv(price_file)
        df.reset_index(inplace=True)
        
        # Calculate EMAs
        df['EMA_6'] = df['Close'].ewm(span=6, adjust=False).mean()
        df['EMA_12'] = df['Close'].ewm(span=12, adjust=False).mean()
        df['EMA_30'] = df['Close'].ewm(span=30, adjust=False).mean()
        
        stock_data[stock] = df
        
        # Send progress update to client
        progress = int((i / total_stocks) * 100)
        emit('progress_update', {'progress': progress})
    time = datetime.datetime.now()
    print(f'fetch_data mk2 {time}')
    # Generate interactive plots with Plotly and convert to JSON
    plots = {}
    for stock, data in stock_data.items():
        # stock information
        if df_data is not None:
            info = df_data[df_data['Symbol'] == stock]
        else:
            info = ''
        if len(info)>0:
            if 'Name' in info.columns:
                name = info['Name'].values[0]
            elif 'Company Name' in info.columns:
                name = info['Company Name'].values[0]
            else:
                name = stock
        else:
            name = stock
        
        fig = go.Figure()
        
        # Add candlestick chart
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
        
        # Add EMA lines
        fig.add_trace(go.Scatter(
            x=data['Date'], y=data['EMA_6'], mode='lines', name='EMA 6'
        ))
        fig.add_trace(go.Scatter(
            x=data['Date'], y=data['EMA_12'], mode='lines', name='EMA 12'
        ))
        fig.add_trace(go.Scatter(
            x=data['Date'], y=data['EMA_30'], mode='lines', name='EMA 30'
        ))
        
        fig.update_layout(
            title=f'{name}',
            xaxis_title='Date',
            yaxis_title='',
            xaxis_rangeslider_visible=True,
            showlegend=False,
            margin=dict(l=0, r=0, t=30, b=20),  # Reduce left and right margins
            height=400,  # Adjust height
            font=dict(size=10)  # Adjust font size
        )
        
        plots[stock] = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    time = datetime.datetime.now()
    print(f'fetch_data mk3 {time}')
    emit('data_ready', {'plots': plots})


@app.route('/download_selected')
def download_selected():
    timenow = datetime.datetime.now().strftime('%Y-%m-%d_%H_%M')
    stocks = request.args.get('stocks').split(',')
    etf = request.args.get('etf')
    page = request.args.get('page')
    if page is None or len(page) == 0:
        page = 1
    output = io.BytesIO()
    content = ",".join(stocks)
    # write the content to the output
    output.write(content.encode())
    output.seek(0)
    return send_file(output, download_name =f'selected_stks_{etf}{page}_{timenow}.txt', as_attachment=True)


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', debug=True)
    #socketio.run(app, debug=True, port=8000)
