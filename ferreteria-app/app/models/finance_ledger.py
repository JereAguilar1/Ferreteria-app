"""Finance Ledger model."""
from sqlalchemy import Column, BigInteger, Numeric, DateTime, String, Text, Enum
from sqlalchemy.sql import func
from app.database import Base
import enum


class LedgerType(enum.Enum):
    """Ledger type enum."""
    INCOME = "INCOME"
    EXPENSE = "EXPENSE"


class LedgerReferenceType(enum.Enum):
    """Ledger reference type enum."""
    SALE = "SALE"
    INVOICE_PAYMENT = "INVOICE_PAYMENT"
    MANUAL = "MANUAL"


class FinanceLedger(Base):
    """Finance Ledger (libro contable)."""
    
    __tablename__ = 'finance_ledger'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    datetime = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    type = Column(Enum(LedgerType, name='ledger_type'), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    category = Column(String, nullable=True)
    reference_type = Column(Enum(LedgerReferenceType, name='ledger_ref_type'), nullable=False)
    reference_id = Column(BigInteger, nullable=True)
    notes = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<FinanceLedger(id={self.id}, type={self.type.value}, amount={self.amount})>"

