"""Balance service for financial reporting."""
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy import func, case, extract
from app.models import FinanceLedger, LedgerType, Product, ProductStock, ProductUomPrice


def get_balance_series(view: str, start: date, end: date, session, method: str = 'all'):
    """
    Get balance series (income, expense, net) grouped by period.
    
    Args:
        view: 'daily', 'monthly', or 'yearly'
        start: Start date (inclusive)
        end: End date (inclusive)
        session: SQLAlchemy session
        method: 'all', 'cash', or 'transfer' (MEJORA 12) - filter by payment method
        
    Returns:
        List of dicts with keys:
        - period: date/string of the period
        - period_label: formatted string for display
        - income: Decimal
        - expense: Decimal
        - net: Decimal
    """
    
    # Map view to date_trunc granularity
    granularity_map = {
        'daily': 'day',
        'monthly': 'month',
        'yearly': 'year'
    }
    
    granularity = granularity_map.get(view, 'month')
    
    # Convert dates to datetime for comparison
    # start at 00:00:00, end at 23:59:59
    start_dt = datetime.combine(start, datetime.min.time())
    end_dt = datetime.combine(end, datetime.max.time())
    
    # Build query with date_trunc and aggregation
    # MEJORA TZ: Convert to Argentina time before truncating
    # FinanceLedger.datetime is TIMESTAMPTZ (UTC). 
    # timezone('America/Argentina/Buenos_Aires', ...) converts it to TIMESTAMP (naive) in AR time.
    local_datetime = func.timezone('America/Argentina/Buenos_Aires', FinanceLedger.datetime)
    period_col = func.date_trunc(granularity, local_datetime).label('period')
    
    income_sum = func.sum(
        case(
            (FinanceLedger.type == LedgerType.INCOME, FinanceLedger.amount),
            else_=0
        )
    ).label('income')
    
    expense_sum = func.sum(
        case(
            (FinanceLedger.type == LedgerType.EXPENSE, FinanceLedger.amount),
            else_=0
        )
    ).label('expense')
    
    query = (
        session.query(
            period_col,
            income_sum,
            expense_sum
        )
        .filter(local_datetime >= start_dt)
        .filter(local_datetime <= end_dt)
        .filter(FinanceLedger.deleted_at.is_(None))
    )
    
    # MEJORA 12: Apply payment method filter
    if method == 'cash':
        query = query.filter(FinanceLedger.payment_method == 'CASH')
    elif method == 'transfer':
        query = query.filter(FinanceLedger.payment_method == 'TRANSFER')
    # if 'all', no filter applied
    
    query = query.group_by(period_col).order_by(period_col.asc())
    
    results = query.all()
    
    # Format results
    series = []
    for row in results:
        period = row.period
        income = Decimal(str(row.income)) if row.income else Decimal('0.00')
        expense = Decimal(str(row.expense)) if row.expense else Decimal('0.00')
        net = income - expense
        
        # Format period label based on granularity
        if granularity == 'day':
            period_label = period.strftime('%Y-%m-%d')
        elif granularity == 'month':
            period_label = period.strftime('%Y-%m')
        else:  # year
            period_label = period.strftime('%Y')
        
        series.append({
            'period': period,
            'period_label': period_label,
            'income': income,
            'expense': expense,
            'net': net
        })
    
    return series


def get_default_date_range(view: str):
    """
    Get default date range based on view.
    
    Args:
        view: 'daily', 'monthly', or 'yearly'
        
    Returns:
        Tuple of (start_date, end_date)
    """
    today = date.today()
    
    if view == 'daily':
        # Last 30 days
        start = today - timedelta(days=30)
        end = today
    elif view == 'monthly':
        # Last 12 months
        start = today - timedelta(days=365)
        end = today
    else:  # yearly
        # Last 5 years
        start = today.replace(year=today.year - 5)
        end = today
    
    return start, end


def get_totals(series):
    """
    Calculate totals from a balance series.
    
    Args:
        series: List returned by get_balance_series
        
    Returns:
        Dict with keys: total_income, total_expense, total_net
    """
    total_income = Decimal('0.00')
    total_expense = Decimal('0.00')
    
    for item in series:
        total_income += item['income']
        total_expense += item['expense']
    
    total_net = total_income - total_expense
    
    return {
        'total_income': total_income,
        'total_expense': total_expense,
        'total_net': total_net
    }


def get_available_years(session):
    """
    Get list of years with finance_ledger data.
    
    Args:
        session: SQLAlchemy session
        
    Returns:
        List of integers (years) in descending order
    """
    # MEJORA TZ: Use local time for year extraction
    local_datetime = func.timezone('America/Argentina/Buenos_Aires', FinanceLedger.datetime)
    
    query = (
        session.query(extract('year', local_datetime).label('year'))
        .filter(FinanceLedger.deleted_at.is_(None))
        .distinct()
        .order_by(extract('year', local_datetime).desc())
    )
    
    results = query.all()
    return [int(row.year) for row in results]


def get_available_months(year: int, session):
    """
    Get list of months with finance_ledger data for a specific year.
    
    Args:
        year: Year (int)
        session: SQLAlchemy session
        
    Returns:
        List of integers (1-12) in ascending order
    """
    # MEJORA TZ: Use local time for year/month extraction
    local_datetime = func.timezone('America/Argentina/Buenos_Aires', FinanceLedger.datetime)
    
    query = (
        session.query(extract('month', local_datetime).label('month'))
        .filter(extract('year', local_datetime) == year)
        .filter(FinanceLedger.deleted_at.is_(None))
        .distinct()
        .order_by(extract('month', local_datetime).asc())
    )
    
    results = query.all()
    return [int(row.month) for row in results]


def get_month_date_range(year: int, month: int):
    """
    Get start and end dates for a specific month.
    
    Args:
        year: Year (int)
        month: Month (1-12)
        
    Returns:
        Tuple of (start_date, end_date)
        start_date: First day of month
        end_date: Last day of month
    """
    from calendar import monthrange
    
    start = date(year, month, 1)
    last_day = monthrange(year, month)[1]
    end = date(year, month, last_day)
    
    return start, end


def get_year_date_range(year: int):
    """
    Get start and end dates for a specific year.
    
    Args:
        year: Year (int)
        
    Returns:
        Tuple of (start_date, end_date)
        start_date: First day of year (Jan 1)
        end_date: Last day of year (Dec 31)
    """
    start = date(year, 1, 1)
    end = date(year, 12, 31)
    
    return start, end


def get_inventory_valuation(session) -> Decimal:
    """
    Calculate inventory valuation (Goodwill / Fondo de Comercio).
    
    MEJORA C: Sum of (sale_price * on_hand_qty) for all products with stock > 0.
    Uses the base UOM price for valuation.
    
    Args:
        session: SQLAlchemy session
        
    Returns:
        Decimal: Total inventory value at sale price
    """
    # Query: JOIN product_stock + product_uom_price (base) + product
    # WHERE stock > 0 AND product.active = true AND is_base = true
    # SUM(stock * sale_price)
    
    query = (
        session.query(
            func.sum(ProductStock.on_hand_qty * ProductUomPrice.sale_price).label('total_valuation')
        )
        .join(ProductUomPrice, ProductUomPrice.product_id == ProductStock.product_id)
        .join(Product, Product.id == ProductStock.product_id)
        .filter(ProductStock.on_hand_qty > 0)
        .filter(Product.active == True)
        .filter(ProductUomPrice.is_base == True)
    )
    
    result = query.scalar()
    
    if result is None:
        return Decimal('0.00')
    
    return Decimal(str(result)).quantize(Decimal('0.01'))


def get_current_total_balance(session) -> Decimal:
    """
    Calculate the current net balance (total income - total expense).
    
    Args:
        session: SQLAlchemy session
        
    Returns:
        Decimal: Current net balance
    """
    income_sum = (
        session.query(func.sum(FinanceLedger.amount))
        .filter(FinanceLedger.type == LedgerType.INCOME)
        .filter(FinanceLedger.deleted_at.is_(None))
        .scalar()
    ) or Decimal('0.00')
    
    expense_sum = (
        session.query(func.sum(FinanceLedger.amount))
        .filter(FinanceLedger.type == LedgerType.EXPENSE)
        .filter(FinanceLedger.deleted_at.is_(None))
        .scalar()
    ) or Decimal('0.00')
    
    return Decimal(str(income_sum)) - Decimal(str(expense_sum))

