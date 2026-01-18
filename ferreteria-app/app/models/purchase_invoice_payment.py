"""Purchase Invoice Payment model - for partial payments."""
from sqlalchemy import Column, BigInteger, Numeric, Date, String, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class PurchaseInvoicePayment(Base):
    """
    Purchase Invoice Payment - Partial payments for invoices.
    
    Allows paying an invoice in multiple installments (adelantos).
    The invoice status is derived from: total_amount - sum(payments).
    """
    
    __tablename__ = 'purchase_invoice_payment'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    invoice_id = Column(BigInteger, ForeignKey('purchase_invoice.id', ondelete='CASCADE'), nullable=False)
    paid_at = Column(Date, nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    notes = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    # Relationships
    invoice = relationship('PurchaseInvoice', back_populates='payments')
    
    # Constraints
    __table_args__ = (
        CheckConstraint('amount > 0', name='chk_payment_amount_positive'),
    )
    
    def __repr__(self):
        return f"<PurchaseInvoicePayment(id={self.id}, invoice_id={self.invoice_id}, amount={self.amount}, paid_at={self.paid_at})>"
