import datetime
from flask import render_template, request, send_file
from flask_socketio import emit
from flask_paginate import Pagination, get_page_parameter
from ..constant import SECTOR_ETFS, ISHARE_SECTOR1_ETF, ISHARE_SECTOR2_ETF, INDUSTRY_ETFS
from ..utils.data_utils import fetch_stock_data, generate_plots
import pandas as pd
import json
import io
import os

def init_app(app, socketio):
    # Load symbol map
    with open("data/meta/symbol_map.json", "r") as f:
        symbol_map = json.load(f)
    
    # Global data storage
    global_data = {}

    @app.route('/')
    def index():
        stocks = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX', 'BABA', 'INTC', 'CSCO', 'ADBE']
        etf = request.args.get('etf', default='SPY')
        if etf != 'SPY':
            stocks = get_stocks(etf)
        
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
        output.write(content.encode())
        output.seek(0)
        return send_file(output, download_name=f'selected_stks_{etf}{page}_{timenow}.txt', as_attachment=True)

    @socketio.on('fetch_data')
    def fetch_data(stocks):
        df_data = global_data.get('df_data',None)
        stock_data = fetch_stock_data(stocks, socketio, symbol_map)
        plots = generate_plots(stock_data, df_data)
        emit('data_ready', {'plots': plots})

    def get_stocks(etf):
        file_name = None
        group = None
        if etf in SECTOR_ETFS:
            group = 'spdr'
            etf_lower = etf.lower()
            if etf == 'XLSR':
                return []
            file_name = f'data/meta/spdr/index-holdings-{etf_lower}.csv'
        elif etf in ISHARE_SECTOR1_ETF:
            group = 'ishare_sector1'
            file_name = f'data/meta/ishare_sector1/{etf}.csv'
        elif etf in ISHARE_SECTOR2_ETF:
            group = 'ishare_sector2'
            file_name = f'data/meta/ishare_sector2/{etf}.csv'
        elif etf in INDUSTRY_ETFS:
            group = 'spdr_industry'
            file_name = f'data/meta/spdr_industry/{etf}.csv'
            
        if file_name:
            df_etf = pd.read_csv(file_name)
            if group in ['ishare_sector1', 'ishare_sector2']:
                df_vip = df_etf[df_etf['WeightJson'] >= 0.2]
                df_vip = df_vip[df_vip['Exchange'].str.contains('NASD|New York')]
                symbols = df_vip['Symbol'].tolist()
            else:
                symbols = df_etf['Symbol'].tolist()
                
            global_data['df_data'] = df_etf
            global_data['etf'] = etf
            return symbols
        return []

    def _mapping_etf_folder(stock, etf):
        etf_first = symbol_map[stock]['true']
        etfs = symbol_map[stock]['false']
        return etf_first, etfs
