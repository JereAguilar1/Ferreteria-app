"""Stock service for manual stock adjustments."""
from decimal import Decimal
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from app.models import (
    Product, ProductStock, StockMove, StockMoveLine,
    StockMoveType, StockReferenceType
)


def adjust_stock_to(session, product_id: int, new_qty: Decimal, notes: str = None) -> None:
    """
    Adjust product stock to a specific quantity (manual adjustment).
    
    This creates a stock_move of type ADJUST with a delta quantity.
    IMPORTANT: This does NOT affect finance_ledger (no INCOME/EXPENSE).
    
    Steps:
    1. Lock product_stock FOR UPDATE
    2. Get current qty
    3. Calculate delta = new_qty - current_qty
    4. If delta == 0: do nothing (no movement needed)
    5. Create stock_move (type ADJUST, reference_type MANUAL)
    6. Create stock_move_line with qty = delta
    7. Trigger updates product_stock automatically
    8. Commit
    
    Args:
        session: SQLAlchemy session
        product_id: Product ID to adjust
        new_qty: New target quantity (must be >= 0)
        notes: Optional notes for the adjustment (e.g., "Stock inicial", "Ajuste manual")
    
    Raises:
        ValueError: For business logic errors
        Exception: For other errors
    """
    
    try:
        # Start nested transaction
        session.begin_nested()
        
        # Step 1: Validate new_qty
        if new_qty < 0:
            raise ValueError('El stock no puede ser negativo')
        
        # Step 2: Get product and lock stock
        product = session.query(Product).filter_by(id=product_id).first()
        if not product:
            raise ValueError(f'Producto con ID {product_id} no encontrado')
        
        # Lock product_stock FOR UPDATE
        product_stock = (
            session.query(ProductStock)
            .filter(ProductStock.product_id == product_id)
            .with_for_update()
            .first()
        )
        
        # Get current qty (or 0 if no stock record exists yet)
        current_qty = product_stock.on_hand_qty if product_stock else Decimal('0')
        
        # Step 3: Calculate delta
        delta = new_qty - current_qty
        
        # Step 4: If delta is 0, no adjustment needed
        if delta == 0:
            # No movement needed, stock is already at target
            session.commit()
            return
        
        # Step 5: Create stock_move (type ADJUST)
        default_notes = f'Ajuste manual de stock para "{product.name}"'
        stock_move = StockMove(
            date=datetime.now(),
            type=StockMoveType.ADJUST,
            reference_type=StockReferenceType.MANUAL,
            reference_id=None,  # Manual adjustment, no reference
            notes=notes if notes else default_notes
        )
        session.add(stock_move)
        session.flush()  # Get stock_move.id
        
        # Step 6: Create stock_move_line with delta
        # The trigger will apply this delta to product_stock.on_hand_qty
        # For type='ADJUST', the trigger should: stock += qty (where qty can be positive or negative)
        stock_move_line = StockMoveLine(
            stock_move_id=stock_move.id,
            product_id=product_id,
            qty=delta,  # Can be positive (increase) or negative (decrease)
            uom_id=product.uom_id,
            unit_cost=Decimal('0')  # Manual adjustments have no cost
        )
        session.add(stock_move_line)
        
        # Step 7: Commit transaction
        # The trigger on stock_move_line will update product_stock.on_hand_qty automatically
        session.commit()
        
    except ValueError:
        session.rollback()
        raise
    
    except IntegrityError as e:
        session.rollback()
        error_msg = str(e.orig)
        raise Exception(f'Error de integridad al ajustar stock: {error_msg}')
    
    except Exception as e:
        session.rollback()
        raise Exception(f'Error al ajustar stock: {str(e)}')


def get_recent_manual_adjustments(session, product_id: int, limit: int = 5) -> list:
    """
    Get recent manual stock adjustments for a product.
    
    Args:
        session: SQLAlchemy session
        product_id: Product ID
        limit: Number of recent adjustments to return
    
    Returns:
        List of dicts with adjustment info: {date, delta, notes, stock_after}
    """
    
    try:
        # Query stock_move_line with JOIN to stock_move
        # Filter by: product_id, type=ADJUST, reference_type=MANUAL
        # Order by date DESC
        
        adjustments = (
            session.query(StockMoveLine, StockMove)
            .join(StockMove, StockMove.id == StockMoveLine.stock_move_id)
            .filter(StockMoveLine.product_id == product_id)
            .filter(StockMove.type == StockMoveType.ADJUST)
            .filter(StockMove.reference_type == StockReferenceType.MANUAL)
            .order_by(StockMove.date.desc())
            .limit(limit)
            .all()
        )
        
        result = []
        for line, move in adjustments:
            result.append({
                'date': move.date,
                'delta': line.qty,
                'notes': move.notes,
                'move_id': move.id
            })
        
        return result
        
    except Exception as e:
        # Return empty list on error (non-critical)
        return []
