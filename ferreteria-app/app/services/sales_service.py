"""Sales service with transactional logic."""
from decimal import Decimal
from datetime import datetime
from sqlalchemy import text
from app.models import (
    Product, ProductStock, Sale, SaleLine, 
    StockMove, StockMoveLine, FinanceLedger,
    SaleStatus, StockMoveType, StockReferenceType,
    LedgerType, LedgerReferenceType
)


def confirm_sale(cart: dict, session, payment_method: str = 'CASH') -> int:
    """
    Confirm sale with full transactional processing.
    
    Steps:
    1. Validate cart and products
    2. Lock product_stock rows (FOR UPDATE)
    3. Validate sufficient stock
    4. Create sale and sale_lines
    5. Create stock_move and stock_move_lines (OUT)
    6. Create finance_ledger entry (INCOME) with payment_method
    7. Commit transaction
    
    Args:
        cart: Cart dictionary with items
        session: SQLAlchemy session
        payment_method: 'CASH' or 'TRANSFER' (MEJORA 12)
    
    Returns:
        sale_id: ID of created sale
        
    Raises:
        ValueError: For business logic errors
        Exception: For other errors
    """
    
    # Validate cart not empty
    if not cart or not cart.get('items'):
        raise ValueError('El carrito está vacío')
    
    try:
        # Start transaction
        session.begin_nested()
        
        # Step 1: Get all product IDs and validate
        # MEJORA A: Handle new cart format with product_id in item dict
        product_ids = []
        for cart_key, item in cart['items'].items():
            if isinstance(item, dict) and 'product_id' in item:
                product_ids.append(item['product_id'])
            else:
                # Legacy format
                try:
                    product_ids.append(int(cart_key))
                except ValueError:
                    # New format: cart_key is "product_id_uom_id"
                    parts = cart_key.split('_')
                    if len(parts) >= 2:
                        product_ids.append(int(parts[0]))
        
        product_ids = list(set(product_ids))  # Remove duplicates
        
        # Get products
        products_dict = {}
        for pid in product_ids:
            product = session.query(Product).filter_by(id=pid).first()
            if not product:
                raise ValueError(f'Producto con ID {pid} no encontrado')
            if not product.active:
                raise ValueError(f'El producto "{product.name}" no está activo')
            products_dict[pid] = product
        
        # Step 2: Lock product_stock rows FOR UPDATE to prevent race conditions
        # Build placeholders for IN clause
        placeholders = ', '.join([f':pid{i}' for i in range(len(product_ids))])
        lock_query = text(f"""
            SELECT product_id, on_hand_qty 
            FROM product_stock 
            WHERE product_id IN ({placeholders})
            FOR UPDATE
        """)
        
        # Execute with parameters
        params = {f'pid{i}': pid for i, pid in enumerate(product_ids)}
        locked_stocks = session.execute(lock_query, params).fetchall()
        
        # Build stock dict
        stock_dict = {row[0]: Decimal(str(row[1])) for row in locked_stocks}
        
        # Step 3: Validate sufficient stock and calculate totals
        sale_lines_data = []
        sale_total = Decimal('0.00')
        
        for cart_key, item in cart['items'].items():
            # MEJORA A: Handle new cart format
            if isinstance(item, dict) and 'product_id' in item:
                product_id = item['product_id']
                uom_id = item['uom_id']
                qty = Decimal(str(item['qty']))
                qty_base = Decimal(str(item['qty_base']))
                unit_price = Decimal(str(item['unit_price']))
            else:
                # Legacy format
                try:
                    product_id = int(cart_key)
                except ValueError:
                    # New format: cart_key is "product_id_uom_id"
                    parts = cart_key.split('_')
                    if len(parts) >= 2:
                        product_id = int(parts[0])
                        uom_id = int(parts[1])
                    else:
                        continue
                
                qty = Decimal(str(item['qty']))
                qty_base = qty  # Legacy: qty == qty_base
                product = products_dict[product_id]
                unit_price = product.sale_price
                uom_id = product.uom_id
            
            if qty <= 0:
                raise ValueError(f'La cantidad debe ser mayor a 0')
            
            product = products_dict[product_id]
            current_stock = stock_dict.get(product_id, Decimal('0'))
            
            # MEJORA A: Check stock using qty_base
            if current_stock < qty_base:
                raise ValueError(
                    f'Stock insuficiente para "{product.name}". '
                    f'Disponible: {current_stock}, Solicitado: {qty_base}'
                )
            
            # Calculate line total
            line_total = (qty * unit_price).quantize(Decimal('0.01'))
            
            sale_lines_data.append({
                'product_id': product_id,
                'product': product,
                'uom_id': uom_id,
                'qty': qty,
                'qty_base': qty_base,
                'unit_price': unit_price,
                'line_total': line_total
            })
            
            sale_total += line_total
        
        sale_total = sale_total.quantize(Decimal('0.01'))
        
        # Step 4: Create Sale
        sale = Sale(
            datetime=datetime.now(),
            total=sale_total,
            status=SaleStatus.CONFIRMED
        )
        session.add(sale)
        session.flush()  # Get sale.id
        
        # Step 5: Create SaleLines
        for line_data in sale_lines_data:
            sale_line = SaleLine(
                sale_id=sale.id,
                product_id=line_data['product_id'],
                uom_id=line_data['uom_id'],  # MEJORA A
                qty=line_data['qty'],
                unit_price=line_data['unit_price'],
                line_total=line_data['line_total']
            )
            session.add(sale_line)
        
        # Step 6: Create StockMove (OUT)
        stock_move = StockMove(
            date=datetime.now(),
            type=StockMoveType.OUT,
            reference_type=StockReferenceType.SALE,
            reference_id=sale.id,
            notes=f'Venta #{sale.id}'
        )
        session.add(stock_move)
        session.flush()  # Get stock_move.id
        
        # Step 7: Create StockMoveLines
        # Note: The trigger on stock_move_line will update product_stock automatically
        # MEJORA A: Use qty_base for stock movement
        for line_data in sale_lines_data:
            product = line_data['product']
            stock_move_line = StockMoveLine(
                stock_move_id=stock_move.id,
                product_id=line_data['product_id'],
                qty=line_data['qty_base'],  # MEJORA A: Use qty_base for stock
                uom_id=line_data['uom_id'],  # MEJORA A: Use selected UOM
                unit_cost=None  # Not relevant for sales
            )
            session.add(stock_move_line)
        
        # Step 8: Create FinanceLedger entry (INCOME) with payment_method (MEJORA 12)
        # FIX: Normalize payment_method to ensure it's a valid string
        from app.models import normalize_payment_method
        payment_method_normalized = normalize_payment_method(payment_method)
        
        ledger_entry = FinanceLedger(
            datetime=datetime.now(),
            type=LedgerType.INCOME,
            amount=sale_total,
            concept=f'Venta #{sale.id}',
            category='Ventas',
            reference_type=LedgerReferenceType.SALE,
            reference_id=sale.id,
            notes=f'Ingreso por venta #{sale.id}',
            payment_method=payment_method_normalized
        )
        session.add(ledger_entry)
        
        # Commit transaction
        session.commit()
        
        return sale.id
        
    except ValueError:
        # Business logic errors - rollback and re-raise
        session.rollback()
        raise
        
    except Exception as e:
        # Other errors - rollback and re-raise
        session.rollback()
        raise Exception(f'Error al confirmar venta: {str(e)}')

