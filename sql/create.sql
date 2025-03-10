 CREATE TABLE stock_price (
    symbol TEXT, 
    date TEXT,
    open REAL,
    high REAL,
    low REAL,
    close REAL,
    adj_close REAL,
    volume INTEGER,
    FOREIGN KEY (symbol) REFERENCES stock_info(symbol)
); 

CREATE TABLE stock_info (
    symbol TEXT PRIMARY KEY,
    is_etf BOOLEAN,
    name TEXT,
    group TEXT,
);

CREATE TABLE relation (
    stock_symbol TEXT,
    belong_to_etf TEXT,
	belong_to_index TEXT
);