import datetime
from flask import render_template, request, send_file, session
from flask_socketio import emit
from flask_paginate import Pagination, get_page_parameter
from ..constant import SECTOR_ETFS, ISHARE_SECTOR1_ETF, ISHARE_SECTOR2_ETF, INDUSTRY_ETFS
from ..utils.data_utils import fetch_stock_data, generate_plots
import pandas as pd
import json
import io
import os
from ..config import Config

def init_app(app, socketio):
    # Load symbol map
    symbol_map_file = Config.SYMBOL_MAP_FILE
    with open(symbol_map_file, "r") as f:
        symbol_map = json.load(f)

    @app.route('/')
    def index():
        from ..validation import validate_etf_symbol, validate_page_number
        
        stocks = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX', 'BABA', 'INTC', 'CSCO', 'ADBE']
        etf = request.args.get('etf', default='SPY')
        try:
            etf = validate_etf_symbol(etf)
        except Exception as e:
            etf = 'SPY'  # Default to SPY if validation fails
        
        if etf != 'SPY':
            stocks = get_stocks(etf)
        
        try:
            page = validate_page_number(request.args.get(get_page_parameter(), type=int, default=1))
        except Exception as e:
            page = 1
            
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
        from ..validation import validate_stock_symbols, validate_etf_symbol, validate_page_number
        
        timenow = datetime.datetime.now().strftime('%Y-%m-%d_%H_%M')
        
        # Validate input parameters
        stocks_param = request.args.get('stocks')
        if not stocks_param:
            # Return error or default
            stocks = []
        else:
            stocks = stocks_param.split(',')
            try:
                validate_stock_symbols(stocks)
            except Exception as e:
                stocks = []
        
        etf = request.args.get('etf')
        if etf:
            try:
                etf = validate_etf_symbol(etf)
            except Exception as e:
                etf = "SPY"  # Default ETF if validation fails
        
        page = request.args.get('page')
        try:
            page = validate_page_number(page)
        except Exception as e:
            page = 1
            
        output = io.BytesIO()
        content = ",".join(stocks) if stocks else ""
        output.write(content.encode())
        output.seek(0)
        return send_file(output, download_name=f'selected_stks_{etf}{page}_{timenow}.txt', as_attachment=True)

    @socketio.on('fetch_data')
    def fetch_data(stocks):
        from ..validation import validate_stock_symbols
        
        # Validate stock symbols
        try:
            stocks = validate_stock_symbols(stocks)
        except Exception as e:
            stocks = []
            
        # Get df_data from session instead of global storage
        df_data_dict = session.get('df_data', None)
        # Convert dict back to DataFrame if it exists
        df_data = pd.DataFrame(df_data_dict) if df_data_dict is not None else None
        stock_data = fetch_stock_data(stocks, socketio, symbol_map)
        plots = generate_plots(stock_data, df_data)
        emit('data_ready', {'plots': plots})

    def get_stocks(etf):
        from ..validation import validate_etf_symbol
        
        # Validate ETF symbol
        try:
            etf = validate_etf_symbol(etf)
        except Exception as e:
            return []
            
        file_name = None
        group = None
        if etf in SECTOR_ETFS:
            group = 'spdr'
            etf_lower = etf.lower()
            if etf == 'XLSR':
                return []
            file_name = f'{Config.SPDR_FOLDER}/index-holdings-{etf_lower}.csv'
        elif etf in ISHARE_SECTOR1_ETF:
            group = 'ishare_sector1'
            file_name = f'{Config.ISHARE_SECTOR1_FOLDER}/{etf}.csv'
        elif etf in ISHARE_SECTOR2_ETF:
            group = 'ishare_sector2'
            file_name = f'{Config.ISHARE_SECTOR2_FOLDER}/{etf}.csv'
        elif etf in INDUSTRY_ETFS:
            group = 'spdr_industry'
            file_name = f'{Config.SPDR_INDUSTRY_FOLDER}/{etf}.csv'
            
        if file_name:
            try:
                df_etf = pd.read_csv(file_name)
                if group in ['ishare_sector1', 'ishare_sector2']:
                    df_vip = df_etf[df_etf['WeightJson'] >= 0.2]
                    df_vip = df_vip[df_vip['Exchange'].str.contains('NASD|New York')]
                    symbols = df_vip['Symbol'].tolist()
                else:
                    symbols = df_etf['Symbol'].tolist()
                    
                # Store df_data in session instead of global storage
                # Convert DataFrame to dict for JSON serialization
                session['df_data'] = df_etf.to_dict()
                session['etf'] = etf
                return symbols
            except Exception as e:
                print(f"Error reading ETF file {file_name}: {e}")
                return []
        return []

    def _mapping_etf_folder(stock, etf):
        etf_first = symbol_map[stock]['true']
        etfs = symbol_map[stock]['false']
        return etf_first, etfs
