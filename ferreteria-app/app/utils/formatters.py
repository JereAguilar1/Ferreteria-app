"""
Formatters for date and datetime display in Argentine format.
Centralized utility functions to ensure consistent formatting across the application.
"""

from datetime import date, datetime


def date_ar(value):
    """
    Format a date object to Argentine format (DD/MM/YYYY).
    
    Args:
        value: date, datetime, or None
        
    Returns:
        String in format DD/MM/YYYY or "-" if None
    """
    if value is None:
        return "-"
    
    if isinstance(value, datetime):
        # Extract date part from datetime
        value = value.date()
    
    if isinstance(value, date):
        return value.strftime('%d/%m/%Y')
    
    # If it's a string, try to parse it
    if isinstance(value, str):
        try:
            # Try parsing YYYY-MM-DD format
            parsed = datetime.strptime(value, '%Y-%m-%d').date()
            return parsed.strftime('%d/%m/%Y')
        except (ValueError, TypeError):
            pass
        
        try:
            # Try parsing datetime format
            parsed = datetime.fromisoformat(value)
            return parsed.strftime('%d/%m/%Y')
        except (ValueError, TypeError):
            pass
    
    # Fallback: return as-is or dash
    return str(value) if value else "-"


def datetime_ar(value, with_time=False):
    """
    Format a datetime object to Argentine format.
    
    Args:
        value: datetime or None
        with_time: If True, include time as DD/MM/YYYY HH:MM
                   If False, only date as DD/MM/YYYY
        
    Returns:
        String in format DD/MM/YYYY or DD/MM/YYYY HH:MM
    """
    if value is None:
        return "-"
    
    if not isinstance(value, datetime):
        # Try to convert to datetime
        if isinstance(value, date):
            value = datetime.combine(value, datetime.min.time())
        elif isinstance(value, str):
            try:
                value = datetime.fromisoformat(value)
            except (ValueError, TypeError):
                return str(value) if value else "-"
        else:
            return str(value) if value else "-"
    
    if with_time:
        return value.strftime('%d/%m/%Y %H:%M')
    else:
        return value.strftime('%d/%m/%Y')


def month_ar(value):
    """
    Format a datetime/date to show only month and year (MM/YYYY).
    Used for monthly balance view.
    
    Args:
        value: datetime, date, or None
        
    Returns:
        String in format MM/YYYY or "-" if None
    """
    if value is None:
        return "-"
    
    if isinstance(value, datetime):
        return value.strftime('%m/%Y')
    
    if isinstance(value, date):
        return value.strftime('%m/%Y')
    
    if isinstance(value, str):
        try:
            # Try parsing ISO format
            parsed = datetime.fromisoformat(value)
            return parsed.strftime('%m/%Y')
        except (ValueError, TypeError):
            pass
    
    return str(value) if value else "-"


def year_ar(value):
    """
    Format a datetime/date to show only year (YYYY).
    Used for yearly balance view.
    
    Args:
        value: datetime, date, or None
        
    Returns:
        String in format YYYY or "-" if None
    """
    if value is None:
        return "-"
    
    if isinstance(value, datetime):
        return value.strftime('%Y')
    
    if isinstance(value, date):
        return value.strftime('%Y')
    
    if isinstance(value, str):
        try:
            # Try parsing ISO format
            parsed = datetime.fromisoformat(value)
            return parsed.strftime('%Y')
        except (ValueError, TypeError):
            pass
    
    return str(value) if value else "-"
