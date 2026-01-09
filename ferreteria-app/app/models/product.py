"""Product model."""
from sqlalchemy import Column, BigInteger, String, Boolean, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Product(Base):
    """Product model."""
    
    __tablename__ = 'product'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    sku = Column(String, nullable=True, unique=True)
    barcode = Column(String, nullable=True, unique=True)
    name = Column(String, nullable=False)
    category_id = Column(BigInteger, ForeignKey('category.id'), nullable=True)
    uom_id = Column(BigInteger, ForeignKey('uom.id'), nullable=False)
    active = Column(Boolean, nullable=False, default=True)
    sale_price = Column(Numeric(10, 2), nullable=False)
    image_path = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    category = relationship('Category', foreign_keys=[category_id])
    uom = relationship('UOM', foreign_keys=[uom_id])
    stock = relationship('ProductStock', uselist=False, back_populates='product')
    
    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}', sku='{self.sku}')>"
    
    @property
    def on_hand_qty(self):
        """Get on hand quantity from stock."""
        if self.stock:
            return self.stock.on_hand_qty
        return 0

