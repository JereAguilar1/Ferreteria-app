"""Product service for business logic."""
from sqlalchemy import func
from app.models import (
    Product, SaleLine, PurchaseInvoiceLine, StockMoveLine
)


def can_hard_delete_product(session, product_id: int) -> tuple[bool, str]:
    """
    Check if a product can be safely deleted (hard delete).
    
    A product can only be deleted if it has NO references in:
    - sale_line (sales)
    - purchase_invoice_line (purchase invoices)
    - stock_move_line (stock movements)
    
    Args:
        session: SQLAlchemy session
        product_id: Product ID to check
    
    Returns:
        tuple: (can_delete: bool, reason: str)
            - If can_delete is True, reason is empty
            - If can_delete is False, reason contains explanation
    """
    
    try:
        # Check if product exists
        product = session.query(Product).filter_by(id=product_id).first()
        if not product:
            return False, 'Producto no encontrado'
        
        # Check sale_line references
        sale_count = (
            session.query(func.count(SaleLine.id))
            .filter(SaleLine.product_id == product_id)
            .scalar()
        )
        
        if sale_count > 0:
            return False, f'El producto tiene {sale_count} venta(s) asociada(s)'
        
        # Check purchase_invoice_line references
        invoice_count = (
            session.query(func.count(PurchaseInvoiceLine.id))
            .filter(PurchaseInvoiceLine.product_id == product_id)
            .scalar()
        )
        
        if invoice_count > 0:
            return False, f'El producto tiene {invoice_count} línea(s) de boleta asociada(s)'
        
        # Check stock_move_line references
        stock_move_count = (
            session.query(func.count(StockMoveLine.id))
            .filter(StockMoveLine.product_id == product_id)
            .scalar()
        )
        
        if stock_move_count > 0:
            return False, f'El producto tiene {stock_move_count} movimiento(s) de stock asociado(s)'
        
        # If we reach here, product can be safely deleted
        return True, ''
        
    except Exception as e:
        return False, f'Error al verificar referencias: {str(e)}'


def get_product_usage_summary(session, product_id: int) -> dict:
    """
    Get a summary of where a product is being used.
    
    Args:
        session: SQLAlchemy session
        product_id: Product ID
    
    Returns:
        dict with counts: {
            'sales': int,
            'invoices': int,
            'stock_moves': int,
            'total_references': int,
            'can_delete': bool
        }
    """
    
    try:
        sale_count = (
            session.query(func.count(SaleLine.id))
            .filter(SaleLine.product_id == product_id)
            .scalar() or 0
        )
        
        invoice_count = (
            session.query(func.count(PurchaseInvoiceLine.id))
            .filter(PurchaseInvoiceLine.product_id == product_id)
            .scalar() or 0
        )
        
        stock_move_count = (
            session.query(func.count(StockMoveLine.id))
            .filter(StockMoveLine.product_id == product_id)
            .scalar() or 0
        )
        
        total = sale_count + invoice_count + stock_move_count
        
        return {
            'sales': sale_count,
            'invoices': invoice_count,
            'stock_moves': stock_move_count,
            'total_references': total,
            'can_delete': total == 0
        }
        
    except Exception:
        return {
            'sales': 0,
            'invoices': 0,
            'stock_moves': 0,
            'total_references': 0,
            'can_delete': False
        }
