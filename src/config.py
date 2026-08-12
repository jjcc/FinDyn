import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Application configuration settings"""
    
    # Database configuration
    DB_PATH = os.getenv('DB_PATH', 'stock_info.db')
    
    # Data paths
    DATA_FOLDER = os.getenv('DATA_FOLDER', 'data')
    META_DATA_FOLDER = os.path.join(os.getenv('DATA_FOLDER', 'data'), 'meta')
    PRICE_INFO_FOLDER = os.getenv('PRICE_INFO_FOLDER', 'extra_data/price_info/2025-04_5m')
    EXTRA_DATA_FOLDER = os.getenv('EXTRA_DATA', 'extra_data')
    ETF_PRICE_DB = os.getenv('ETF_PRICE_DB', os.path.join(DATA_FOLDER, 'etf_prices.sqlite3'))
    ETF_CHART_FOLDER = os.getenv('ETF_CHART_DIR', os.path.join('image', 'sectors'))
    TIINGO_API_TOKEN = os.getenv('TIINGO_API_TOKEN', '')
    
    # Stock data folders
    SPDR_FOLDER = os.path.join(META_DATA_FOLDER, 'spdr')
    ISHARE_SECTOR1_FOLDER = os.path.join(META_DATA_FOLDER, 'ishare_sector1')
    ISHARE_SECTOR2_FOLDER = os.path.join(META_DATA_FOLDER, 'ishare_sector2')
    SPDR_INDUSTRY_FOLDER = os.path.join(META_DATA_FOLDER, 'spdr_industry')
    
    # File paths for stock data
    SYMBOL_MAP_FILE = os.path.join(META_DATA_FOLDER, 'symbol_map.json')
    ISHARE_ETF_INFO_FILE = os.path.join(META_DATA_FOLDER, 'ishare_etf_info.csv')
    
    # API settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    
    # Session configuration
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    SESSION_KEY_PREFIX = 'finndyn_session:'
    
    # yfinance settings
    YFINANCE_INTERVAL = '1d'
    
    # EMA calculation periods (standardized across all modules)
    EMA_PERIODS = [6, 12, 30]
    
    # Date range settings (in days)
    DEFAULT_DATA_RANGE = 156
