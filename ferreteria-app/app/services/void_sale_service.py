"""
Void Sale Service

Allows full cancellation of a confirmed sale by:
- Setting sale.status = CANCELLED
- Restoring stock with a compensating StockMove (IN)
- Reversing the ledger income with a FinanceLedger EXPENSE
"""

from decimal import Decimal
from datetime import datetime

from app.models import (
    Sale, SaleStatus, StockMove, StockMoveLine,
    StockMoveType, StockReferenceType,
    FinanceLedger, LedgerType, LedgerReferenceType,
    normalize_payment_method
)


def void_sale(sale_id: int, session) -> None:
    """
    Void a confirmed sale.

    Steps:
    1. Lock sale FOR UPDATE and validate it is CONFIRMED
    2. Set sale.status = CANCELLED
    3. Create StockMove IN to restore stock for each line
    4. Create FinanceLedger EXPENSE to reverse the original income
    5. Commit

    Args:
        sale_id: ID of the sale to void
        session: SQLAlchemy session

    Raises:
        ValueError: For business logic errors (e.g., already cancelled)
        Exception: For other errors
    """
    try:
        session.begin_nested()

        # Step 1: Lock sale and validate
        sale = (
            session.query(Sale)
            .filter(Sale.id == sale_id)
            .with_for_update()
            .first()
        )

        if not sale:
            raise ValueError(f'Venta #{sale_id} no encontrada.')

        if sale.status == SaleStatus.CANCELLED:
            raise ValueError(f'La venta #{sale_id} ya está anulada.')

        if sale.status != SaleStatus.CONFIRMED:
            status_str = sale.status.value if hasattr(sale.status, 'value') else str(sale.status)
            raise ValueError(f'Solo se pueden anular ventas confirmadas. Estado actual: {status_str}')

        if not sale.lines:
            raise ValueError(f'La venta #{sale_id} no tiene líneas.')

        # Step 2: Mark sale as CANCELLED
        sale.status = SaleStatus.CANCELLED

        # Step 3: Restore stock with a compensating StockMove IN
        from app.utils.formatters import get_now_ar, ar_to_utc
        now_utc = ar_to_utc(get_now_ar())

        stock_move = StockMove(
            date=now_utc,
            type=StockMoveType.IN,
            reference_type=StockReferenceType.SALE,
            reference_id=sale.id,
            notes=f'Anulación de Venta #{sale.id}'
        )
        session.add(stock_move)
        session.flush()  # Get stock_move.id

        for line in sale.lines:
            from app.models import Product
            product = session.query(Product).filter_by(id=line.product_id).first()

            stock_move_line = StockMoveLine(
                stock_move_id=stock_move.id,
                product_id=line.product_id,
                qty=line.qty,  # Restore the full qty sold
                uom_id=line.uom_id if line.uom_id else (product.uom_id if product else None),
                unit_cost=None
            )
            session.add(stock_move_line)

        # Step 4: Reverse the income ledger entry
        # Look up the original ledger entry to get the payment_method
        original_ledger = (
            session.query(FinanceLedger)
            .filter_by(
                reference_type=LedgerReferenceType.SALE,
                reference_id=sale.id,
                type=LedgerType.INCOME
            )
            .first()
        )

        original_payment_method = original_ledger.payment_method if original_ledger else 'CASH'
        payment_method_normalized = normalize_payment_method(original_payment_method)

        reversal_entry = FinanceLedger(
            datetime=now_utc,
            type=LedgerType.EXPENSE,
            amount=sale.total,
            concept=f'Anulación Venta #{sale.id}',
            category='Anulaciones',
            reference_type=LedgerReferenceType.SALE,
            reference_id=sale.id,
            notes=f'Reversión por anulación de venta #{sale.id}',
            payment_method=payment_method_normalized
        )
        session.add(reversal_entry)

        session.commit()

    except ValueError:
        session.rollback()
        raise

    except Exception as e:
        session.rollback()
        raise Exception(f'Error al anular venta: {str(e)}')
