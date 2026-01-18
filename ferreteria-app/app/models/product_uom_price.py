"""Product UOM Price model - Multiple UOMs and prices per product."""
from sqlalchemy import Column, BigInteger, Numeric, String, Boolean, DateTime, ForeignKey, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class ProductUomPrice(Base):
    """
    Product UOM Price - Allows a product to be sold in multiple units of measure.
    
    Example:
    - Cable: 
      - UOM "Metro" (base): price $10, conversion = 1
      - UOM "Rollo 100m": price $900, conversion = 100
    
    The 'conversion_to_base' field indicates how many base units this UOM represents.
    Stock is always tracked in the base UOM.
    """
    
    __tablename__ = 'product_uom_price'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    product_id = Column(BigInteger, ForeignKey('product.id', ondelete='CASCADE'), nullable=False)
    uom_id = Column(BigInteger, ForeignKey('uom.id'), nullable=False)
    sale_price = Column(Numeric(12, 2), nullable=False)
    conversion_to_base = Column(Numeric(12, 4), nullable=False, default=1)
    is_base = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    product = relationship('Product', back_populates='uom_prices')
    uom = relationship('UOM')
    
    # Constraints
    __table_args__ = (
        CheckConstraint('sale_price >= 0', name='chk_sale_price_positive'),
        CheckConstraint('conversion_to_base > 0', name='chk_conversion_positive'),
        UniqueConstraint('product_id', 'uom_id', name='uq_product_uom'),
    )
    
    def __repr__(self):
        return f"<ProductUomPrice(id={self.id}, product_id={self.product_id}, uom_id={self.uom_id}, price={self.sale_price}, is_base={self.is_base})>"
    
    def calculate_qty_base(self, qty_in_this_uom):
        """
        Calculate quantity in base UOM.
        
        Args:
            qty_in_this_uom: Quantity in this UOM
        
        Returns:
            Decimal: Quantity in base UOM
        
        Example:
            If this is "Rollo 100m" with conversion_to_base=100,
            and qty_in_this_uom=2, returns 200 (meters)
        """
        from decimal import Decimal
        return Decimal(str(qty_in_this_uom)) * self.conversion_to_base
