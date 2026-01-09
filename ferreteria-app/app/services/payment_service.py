"""Payment service for purchase invoice payment processing."""
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from app.models import (
    PurchaseInvoice, InvoiceStatus,
    FinanceLedger, LedgerType, LedgerReferenceType
)


def pay_invoice(invoice_id: int, paid_at: date, session) -> None:
    """
    Mark a purchase invoice as PAID and register EXPENSE in finance_ledger.
    
    Steps (in a single transaction):
    1. Lock invoice row (SELECT FOR UPDATE) to prevent concurrent payment
    2. Validate invoice exists and is PENDING
    3. Validate paid_at is provided
    4. Update invoice: status=PAID, paid_at=paid_at
    5. Insert finance_ledger: type=EXPENSE, amount=total_amount, reference=INVOICE_PAYMENT
    6. Commit or rollback
    
    Args:
        invoice_id: ID of the invoice to pay
        paid_at: Payment date
        session: SQLAlchemy session
        
    Raises:
        ValueError: For business logic errors
        Exception: For other errors
    """
    
    try:
        # Start nested transaction
        session.begin_nested()
        
        # Step 1: Lock invoice row to prevent concurrent payment
        # Use FOR UPDATE to ensure no other transaction can modify this invoice
        invoice = (
            session.query(PurchaseInvoice)
            .filter(PurchaseInvoice.id == invoice_id)
            .with_for_update()
            .first()
        )
        
        if not invoice:
            raise ValueError(f'Boleta con ID {invoice_id} no encontrada')
        
        # Step 2: Validate invoice is PENDING
        if invoice.status != InvoiceStatus.PENDING:
            raise ValueError(
                f'La boleta ya está {invoice.status.value}. '
                f'Solo se pueden pagar boletas PENDING.'
            )
        
        # Step 3: Validate paid_at
        if not paid_at:
            raise ValueError('La fecha de pago es requerida')
        
        # Defensive: validate total_amount
        if invoice.total_amount < 0:
            raise ValueError(
                f'El monto total de la boleta es inválido: {invoice.total_amount}'
            )
        
        # Defensive: validate invoice has lines
        if not invoice.lines or len(invoice.lines) == 0:
            raise ValueError('La boleta no tiene ítems. No se puede pagar.')
        
        # Step 4: Update invoice
        invoice.status = InvoiceStatus.PAID
        invoice.paid_at = paid_at
        
        session.flush()  # Ensure invoice is updated before creating ledger entry
        
        # Step 5: Create finance_ledger entry (EXPENSE)
        ledger_entry = FinanceLedger(
            datetime=datetime.now(),
            type=LedgerType.EXPENSE,
            amount=invoice.total_amount,
            reference_type=LedgerReferenceType.INVOICE_PAYMENT,
            reference_id=invoice.id,
            notes=f'Pago boleta #{invoice.invoice_number} - {invoice.supplier.name}'
        )
        
        session.add(ledger_entry)
        
        # Step 6: Commit transaction
        session.commit()
        
    except ValueError:
        # Business logic errors - rollback and re-raise
        session.rollback()
        raise
        
    except IntegrityError as e:
        session.rollback()
        error_msg = str(e.orig)
        raise Exception(f'Error de integridad al registrar pago: {error_msg}')
        
    except Exception as e:
        # Other errors - rollback and re-raise
        session.rollback()
        raise Exception(f'Error al procesar pago: {str(e)}')

