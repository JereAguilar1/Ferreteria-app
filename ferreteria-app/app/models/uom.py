"""Unit of Measure model."""
from sqlalchemy import Column, BigInteger, String, DateTime
from sqlalchemy.sql import func
from app.database import Base


class UOM(Base):
    """Unit of Measure (Unidad de Medida)."""
    
    __tablename__ = 'uom'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    symbol = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    def __repr__(self):
        return f"<UOM(id={self.id}, name='{self.name}', symbol='{self.symbol}')>"

