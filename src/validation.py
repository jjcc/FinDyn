from typing import List, Dict, Any, Optional
import re

class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass

def validate_stock_symbols(symbols: List[str]) -> List[str]:
    """
    Validate stock symbols.
    
    Args:
        symbols: List of stock symbols to validate
        
    Returns:
        List of validated symbols
        
    Raises:
        ValidationError: If any symbol is invalid
    """
    if not isinstance(symbols, list):
        raise ValidationError("Stock symbols must be provided as a list")
    
    if not symbols:
        raise ValidationError("At least one stock symbol is required")
    
    validated_symbols = []
    for symbol in symbols:
        if not isinstance(symbol, str):
            raise ValidationError(f"Invalid stock symbol: {symbol}. Must be a string.")
        
        # Stock symbols should be uppercase letters, numbers, and possibly hyphens
        if not re.match(r'^[A-Z0-9.-]+$', symbol):
            raise ValidationError(f"Invalid stock symbol format: {symbol}")
        
        validated_symbols.append(symbol)
    
    return validated_symbols

def validate_etf_symbol(etf: str) -> str:
    """
    Validate ETF symbol.
    
    Args:
        etf: ETF symbol to validate
        
    Returns:
        Validated ETF symbol
        
    Raises:
        ValidationError: If ETF symbol is invalid
    """
    if not isinstance(etf, str):
        raise ValidationError("ETF symbol must be a string")
    
    # ETF symbols should be uppercase letters and numbers only
    if not re.match(r'^[A-Z0-9]+$', etf):
        raise ValidationError(f"Invalid ETF symbol format: {etf}")
    
    return etf

def validate_page_number(page: Any) -> int:
    """
    Validate page number.
    
    Args:
        page: Page number to validate
        
    Returns:
        Validated page number
        
    Raises:
        ValidationError: If page number is invalid
    """
    if page is None:
        return 1
    
    if isinstance(page, str):
        if not page.isdigit():
            raise ValidationError("Page number must be a number")
        return int(page)
    
    if isinstance(page, int):
        if page <= 0:
            raise ValidationError("Page number must be positive")
        return page
    
    if isinstance(page, (float, complex)):
        if page != int(page) or int(page) <= 0:
            raise ValidationError("Page number must be a positive integer")
        return int(page)
    
    raise ValidationError("Page number must be a number")

def validate_date_range(start_date: str, end_date: str) -> tuple:
    """
    Validate date range strings.
    
    Args:
        start_date: Start date string in YYYY-MM-DD format
        end_date: End date string in YYYY-MM-DD format
        
    Returns:
        Tuple of validated dates
        
    Raises:
        ValidationError: If dates are invalid
    """
    import datetime
    
    # Validate date format
    try:
        datetime.datetime.strptime(start_date, '%Y-%m-%d')
        datetime.datetime.strptime(end_date, '%Y-%m-%d')
    except ValueError:
        raise ValidationError("Dates must be in 'YYYY-MM-DD' format")
    
    # Check if start_date is before end_date
    if start_date > end_date:
        raise ValidationError("Start date must be before end date")
    
    return start_date, end_date

def validate_csv_filename(filename: str) -> str:
    """
    Validate CSV filename.
    
    Args:
        filename: Filename to validate
        
    Returns:
        Validated filename
        
    Raises:
        ValidationError: If filename is invalid
    """
    if not isinstance(filename, str):
        raise ValidationError("Filename must be a string")
    
    # Check for invalid characters in filename
    if not re.match(r'^[\w\-. ]+$', filename):
        raise ValidationError("Invalid characters in filename")
    
    return filename