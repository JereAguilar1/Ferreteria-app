"""Sale model."""
from sqlalchemy import Column, BigInteger, Numeric, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


class SaleStatus(enum.Enum):
    """Sale status enum."""
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"


class Sale(Base):
    """Sale (venta confirmada)."""
    
    __tablename__ = 'sale'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    datetime = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    total = Column(Numeric(10, 2), nullable=False)
    status = Column(Enum(SaleStatus, name='sale_status'), nullable=False, default=SaleStatus.CONFIRMED)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    # Relationships
    lines = relationship('SaleLine', back_populates='sale', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<Sale(id={self.id}, total={self.total}, status={self.status.value})>"

