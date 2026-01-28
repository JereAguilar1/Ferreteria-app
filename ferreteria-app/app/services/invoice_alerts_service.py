"""
Service for invoice alerts and critical invoice tracking.
"""
from datetime import date, timedelta
from sqlalchemy import and_, or_
from app.models import PurchaseInvoice, InvoiceStatus


def get_invoice_alert_counts(session, today: date = None):
    """
    Get counts of critical invoices (due tomorrow or overdue).
    
    Args:
        session: SQLAlchemy session
        today: Date to use as reference (defaults to date.today())
    
    Returns:
        dict with keys:
            - due_tomorrow_count: int
            - overdue_count: int
            - total_critical: int
    """
    if today is None:
        from app.utils.formatters import get_now_ar
        today = get_now_ar().date()
    
    tomorrow = today + timedelta(days=1)
    
    # Count invoices due tomorrow (PENDING only)
    due_tomorrow_count = session.query(PurchaseInvoice).filter(
        and_(
            PurchaseInvoice.status == InvoiceStatus.PENDING,
            PurchaseInvoice.due_date == tomorrow
        )
    ).count()
    
    # Count overdue invoices (PENDING only)
    overdue_count = session.query(PurchaseInvoice).filter(
        and_(
            PurchaseInvoice.status == InvoiceStatus.PENDING,
            PurchaseInvoice.due_date < today,
            PurchaseInvoice.due_date.isnot(None)
        )
    ).count()
    
    return {
        'due_tomorrow_count': due_tomorrow_count,
        'overdue_count': overdue_count,
        'total_critical': due_tomorrow_count + overdue_count
    }


def is_invoice_overdue(invoice, today: date = None):
    """
    Check if an invoice is overdue.
    
    Args:
        invoice: PurchaseInvoice instance
        today: Date to use as reference (defaults to date.today())
    
    Returns:
        bool: True if invoice is overdue
    """
    if today is None:
        from app.utils.formatters import get_now_ar
        today = get_now_ar().date()
    
    return (
        invoice.status == InvoiceStatus.PENDING and
        invoice.due_date is not None and
        invoice.due_date < today
    )


def is_invoice_due_tomorrow(invoice, today: date = None):
    """
    Check if an invoice is due tomorrow.
    
    Args:
        invoice: PurchaseInvoice instance
        today: Date to use as reference (defaults to date.today())
    
    Returns:
        bool: True if invoice is due tomorrow
    """
    if today is None:
        from app.utils.formatters import get_now_ar
        today = get_now_ar().date()
    
    tomorrow = today + timedelta(days=1)
    
    return (
        invoice.status == InvoiceStatus.PENDING and
        invoice.due_date == tomorrow
    )
