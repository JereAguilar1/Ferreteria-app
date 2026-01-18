"""Service for managing product UOM prices."""
from decimal import Decimal
from typing import List, Dict
from sqlalchemy.orm import Session
from app.models import ProductUomPrice, UOM


def create_or_update_uom_prices(session: Session, product_id: int, uom_prices_data: List[Dict]):
    """
    Create or update UOM prices for a product.
    
    Args:
        session: Database session
        product_id: Product ID
        uom_prices_data: List of dicts with keys: uom_id, sale_price, conversion_to_base, is_base
    
    Raises:
        ValueError: If validation fails
    """
    # Validations
    if not uom_prices_data:
        raise ValueError('Debe definir al menos una unidad de medida con precio')
    
    # Count base UOMs
    base_count = sum(1 for uom_data in uom_prices_data if uom_data.get('is_base', False))
    if base_count != 1:
        raise ValueError('Debe haber exactamente una unidad de medida base')
    
    # Validate each UOM
    for uom_data in uom_prices_data:
        if uom_data['sale_price'] < 0:
            raise ValueError('El precio de venta debe ser mayor o igual a 0')
        if uom_data['conversion_to_base'] <= 0:
            raise ValueError('El factor de conversión debe ser mayor a 0')
        
        # Verify UOM exists
        uom = session.query(UOM).filter_by(id=uom_data['uom_id']).first()
        if not uom:
            raise ValueError(f'La unidad de medida con ID {uom_data["uom_id"]} no existe')
    
    # Check for duplicate UOMs
    uom_ids = [uom_data['uom_id'] for uom_data in uom_prices_data]
    if len(uom_ids) != len(set(uom_ids)):
        raise ValueError('No puede haber unidades de medida duplicadas')
    
    # Delete existing UOM prices for this product
    session.query(ProductUomPrice).filter_by(product_id=product_id).delete()
    
    # Create new UOM prices
    for uom_data in uom_prices_data:
        uom_price = ProductUomPrice(
            product_id=product_id,
            uom_id=uom_data['uom_id'],
            sale_price=Decimal(str(uom_data['sale_price'])),
            conversion_to_base=Decimal(str(uom_data['conversion_to_base'])),
            is_base=uom_data.get('is_base', False)
        )
        session.add(uom_price)


def get_product_uom_prices(session: Session, product_id: int) -> List[ProductUomPrice]:
    """Get all UOM prices for a product."""
    return session.query(ProductUomPrice).filter_by(product_id=product_id).order_by(
        ProductUomPrice.is_base.desc(),
        ProductUomPrice.id
    ).all()


def get_base_uom_price(session: Session, product_id: int) -> ProductUomPrice:
    """Get the base UOM price for a product."""
    return session.query(ProductUomPrice).filter_by(
        product_id=product_id,
        is_base=True
    ).first()
