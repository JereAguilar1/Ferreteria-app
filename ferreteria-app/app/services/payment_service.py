"""Payment service for purchase invoice payment processing."""
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from app.models import (
    PurchaseInvoice, InvoiceStatus, PurchaseInvoicePayment,
    FinanceLedger, LedgerType, LedgerReferenceType, PaymentMethod  # MEJORA 12
)
from sqlalchemy import func


def pay_invoice(invoice_id: int, paid_at: date, session, payment_method: str = 'CASH') -> None:
    """
    Mark a purchase invoice as PAID and register EXPENSE in finance_ledger.
    
    Steps (in a single transaction):
    1. Lock invoice row (SELECT FOR UPDATE) to prevent concurrent payment
    2. Validate invoice exists and is PENDING
    3. Validate paid_at is provided
    4. Update invoice: status=PAID, paid_at=paid_at
    5. Insert finance_ledger: type=EXPENSE, amount=total_amount, reference=INVOICE_PAYMENT, payment_method
    6. Commit or rollback
    
    Args:
        invoice_id: ID of the invoice to pay
        paid_at: Payment date
        session: SQLAlchemy session
        payment_method: 'CASH' or 'TRANSFER' (MEJORA 12)
        
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
        
        # Step 5: Create finance_ledger entry (EXPENSE) with payment_method (MEJORA 12)
        # FIX: Normalize payment_method to ensure it's a valid string
        from app.models import normalize_payment_method
        payment_method_normalized = normalize_payment_method(payment_method)
        
        # Sanitize notes to prevent issues with special characters (backslashes, quotes, etc.)
        supplier_name_safe = str(invoice.supplier.name).replace('\\', '/').replace('\n', ' ').replace('\r', '')
        invoice_number_safe = str(invoice.invoice_number).replace('\\', '/').replace('\n', ' ').replace('\r', '')
        notes_text = f'Pago boleta #{invoice_number_safe} - {supplier_name_safe}'
        
        ledger_entry = FinanceLedger(
            datetime=datetime.now(),
            type=LedgerType.EXPENSE,
            amount=invoice.total_amount,
            reference_type=LedgerReferenceType.INVOICE_PAYMENT,
            reference_id=invoice.id,
            notes=notes_text[:500],  # Limit length to prevent issues
            payment_method=payment_method_normalized  # MEJORA 12 FIX
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


def add_invoice_payment(invoice_id: int, paid_at: date, amount: Decimal, session, notes: str = None, payment_method: str = 'CASH') -> None:
    """
    Add a partial payment to a purchase invoice (MEJORA B).
    
    This allows paying an invoice in multiple installments (adelantos).
    The invoice status is automatically updated based on the remaining balance:
    - If balance == 0: status = PAID
    - If balance > 0: status = PENDING
    
    Steps (in a single transaction):
    1. Lock invoice row (SELECT FOR UPDATE)
    2. Validate invoice exists
    3. Calculate current balance (total - sum of payments)
    4. Validate amount <= balance (no overpayment)
    5. Insert purchase_invoice_payment
    6. Insert finance_ledger EXPENSE for this payment
    7. Recalculate balance and update invoice status
    8. Commit or rollback
    
    Args:
        invoice_id: ID of the invoice to pay
        paid_at: Payment date
        amount: Payment amount (must be > 0 and <= balance)
        session: SQLAlchemy session
        notes: Optional notes for this payment
        payment_method: 'CASH' or 'TRANSFER'
        
    Raises:
        ValueError: For business logic errors
        Exception: For other errors
    """
    
    try:
        # Start nested transaction
        session.begin_nested()
        
        # Step 1: Lock invoice row
        invoice = (
            session.query(PurchaseInvoice)
            .filter(PurchaseInvoice.id == invoice_id)
            .with_for_update()
            .first()
        )
        
        if not invoice:
            raise ValueError(f'Boleta con ID {invoice_id} no encontrada')
        
        # Step 2: Validate paid_at
        if not paid_at:
            raise ValueError('La fecha de pago es obligatoria')
        
        # Step 3: Validate amount
        if amount <= 0:
            raise ValueError('El monto del pago debe ser mayor a 0')
        
        # Step 4: Calculate current balance
        total_paid = (
            session.query(func.coalesce(func.sum(PurchaseInvoicePayment.amount), Decimal('0')))
            .filter(PurchaseInvoicePayment.invoice_id == invoice_id)
            .scalar()
        )
        
        balance = invoice.total_amount - total_paid
        
        # Step 5: Validate amount <= balance (no overpayment)
        if amount > balance:
            raise ValueError(
                f'El monto del pago (${amount}) excede el saldo pendiente (${balance}). '
                f'Total boleta: ${invoice.total_amount}, Ya pagado: ${total_paid}'
            )
        
        # Step 6: Insert payment record
        payment = PurchaseInvoicePayment(
            invoice_id=invoice_id,
            paid_at=paid_at,
            amount=amount,
            notes=notes
        )
        session.add(payment)
        session.flush()  # Get payment.id
        
        # Step 7: Insert finance_ledger EXPENSE
        # Normalize payment_method
        if payment_method and payment_method.strip():
            payment_method_enum = PaymentMethod[payment_method.upper()]
        else:
            payment_method_enum = None
        
        # Convert date to datetime for ledger
        paid_datetime = datetime.combine(paid_at, datetime.min.time())
        
        ledger_entry = FinanceLedger(
            datetime=paid_datetime,
            type=LedgerType.EXPENSE,
            amount=amount,
            reference_type=LedgerReferenceType.INVOICE_PAYMENT,
            reference_id=invoice_id,
            notes=f'Pago parcial boleta {invoice.invoice_number}' + (f' - {notes}' if notes else ''),
            payment_method=payment_method_enum.value if payment_method_enum else 'CASH'
        )
        session.add(ledger_entry)
        
        # Step 8: Recalculate balance and update status
        new_balance = balance - amount
        
        if new_balance == 0:
            # Invoice fully paid
            invoice.status = InvoiceStatus.PAID
            invoice.paid_at = paid_at  # Set to last payment date
        elif new_balance > 0:
            # Still pending
            invoice.status = InvoiceStatus.PENDING
            invoice.paid_at = None
        else:
            # This shouldn't happen due to validation above
            raise ValueError(f'Balance negativo detectado: {new_balance}')
        
        # Step 9: Commit transaction
        session.commit()
        
    except ValueError:
        session.rollback()
        raise
        
    except IntegrityError as e:
        session.rollback()
        error_msg = str(e.orig)
        raise Exception(f'Error de integridad al registrar pago parcial: {error_msg}')
        
    except Exception as e:
        session.rollback()
        raise Exception(f'Error al procesar pago parcial: {str(e)}')


def get_invoice_balance(invoice_id: int, session) -> dict:
    """
    Calculate the balance of an invoice (MEJORA B).
    
    Returns:
        dict with:
            - total_amount: Decimal
            - total_paid: Decimal
            - balance: Decimal
            - is_fully_paid: bool
    """
    
    try:
        invoice = session.query(PurchaseInvoice).filter_by(id=invoice_id).first()
        
        if not invoice:
            raise ValueError(f'Boleta con ID {invoice_id} no encontrada')
        
        total_paid = (
            session.query(func.coalesce(func.sum(PurchaseInvoicePayment.amount), Decimal('0')))
            .filter(PurchaseInvoicePayment.invoice_id == invoice_id)
            .scalar()
        )
        
        balance = invoice.total_amount - total_paid
        
        return {
            'total_amount': invoice.total_amount,
            'total_paid': total_paid,
            'balance': balance,
            'is_fully_paid': balance == 0
        }
        
    except Exception as e:
        raise Exception(f'Error al calcular saldo: {str(e)}')

