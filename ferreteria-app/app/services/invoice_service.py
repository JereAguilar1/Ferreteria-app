"""Invoice service with transactional logic."""
from decimal import Decimal
import decimal
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from app.models import (
    Product, Supplier, PurchaseInvoice, PurchaseInvoiceLine,
    StockMove, StockMoveLine,
    InvoiceStatus, StockMoveType, StockReferenceType
)


def create_invoice_with_lines(payload: dict, session) -> int:
    """
    Create purchase invoice with lines and update stock.
    
    Steps:
    1. Validate supplier and data
    2. Validate lines (>=1, product exists, qty>0, unit_cost>=0)
    3. Calculate totals
    4. Create purchase_invoice + purchase_invoice_line
    5. Create stock_move (IN) + stock_move_line
    6. Trigger updates product_stock
    7. Commit transaction
    
    Args:
        payload: Dictionary with:
            - supplier_id: int
            - invoice_number: str
            - invoice_date: date
            - due_date: date | None
            - lines: list of {product_id, qty, unit_cost}
        session: SQLAlchemy session
    
    Returns:
        invoice_id: ID of created invoice
        
    Raises:
        ValueError: For business logic errors
        Exception: For other errors
    """
    
    try:
        # Start transaction
        session.begin_nested()
        
        # Step 1: Validate supplier
        supplier_id = payload.get('supplier_id')
        if not supplier_id:
            raise ValueError('El proveedor es requerido')
        
        supplier = session.query(Supplier).filter_by(id=supplier_id).first()
        if not supplier:
            raise ValueError(f'Proveedor con ID {supplier_id} no encontrado')
        
        # Validate invoice data
        invoice_number = payload.get('invoice_number', '').strip()
        if not invoice_number:
            raise ValueError('El número de boleta es requerido')
        
        invoice_date = payload.get('invoice_date')
        if not invoice_date:
            raise ValueError('La fecha de boleta es requerida')
        
        due_date = payload.get('due_date')
        
        # Step 2: Validate lines
        lines = payload.get('lines', [])
        
        if not lines or len(lines) == 0:
            raise ValueError('Debe agregar al menos un ítem a la boleta')
        
        # Validate and prepare lines
        validated_lines = []
        total_amount = Decimal('0.00')
        
        for line in lines:
            product_id = line.get('product_id')
            if not product_id:
                raise ValueError('Producto ID es requerido en cada línea')
            
            # Get product
            product = session.query(Product).filter_by(id=product_id).first()
            if not product:
                raise ValueError(f'Producto con ID {product_id} no encontrado')
            
            if not product.active:
                raise ValueError(f'El producto "{product.name}" no está activo')
            
            # Validate qty and unit_cost
            try:
                qty = Decimal(str(line.get('qty', 0)))
                if qty <= 0:
                    raise ValueError(f'La cantidad debe ser mayor a 0 para "{product.name}"')
            except (TypeError, ValueError, decimal.InvalidOperation):
                raise ValueError(f'Cantidad inválida para "{product.name}"')
            
            try:
                raw_unit_cost = Decimal(str(line.get('unit_cost', 0)))
                if raw_unit_cost < 0:
                    raise ValueError(f'El costo unitario no puede ser negativo para "{product.name}"')
                
                unit_cost = raw_unit_cost.quantize(Decimal('0.01'))
                if raw_unit_cost != unit_cost:
                    raise ValueError(f'El costo unitario debe tener exactamente 2 decimales para "{product.name}"')
                    
            except (TypeError, ValueError, decimal.InvalidOperation):
                raise ValueError(f'Costo unitario inválido para "{product.name}"')
            
            # Calculate line total
            line_total = (qty * unit_cost).quantize(Decimal('0.01'))
            
            validated_lines.append({
                'product_id': product_id,
                'product': product,
                'qty': qty,
                'unit_cost': unit_cost,
                'line_total': line_total
            })
            
            total_amount += line_total
        
        total_amount = total_amount.quantize(Decimal('0.01'))
        
        # Step 3: Check for duplicate invoice_number for same supplier
        existing = (session.query(PurchaseInvoice)
                   .filter_by(supplier_id=supplier_id, invoice_number=invoice_number)
                   .first())
        if existing:
            raise ValueError(
                f'Ya existe una boleta con número "{invoice_number}" '
                f'para el proveedor "{supplier.name}"'
            )
        
        # Step 4: Create PurchaseInvoice
        invoice = PurchaseInvoice(
            supplier_id=supplier_id,
            invoice_number=invoice_number,
            invoice_date=invoice_date,
            due_date=due_date,
            total_amount=total_amount,
            status=InvoiceStatus.PENDING,
            paid_at=None
        )
        session.add(invoice)
        session.flush()  # Get invoice.id
        
        # Step 5: Create PurchaseInvoiceLines
        for line_data in validated_lines:
            invoice_line = PurchaseInvoiceLine(
                invoice_id=invoice.id,
                product_id=line_data['product_id'],
                qty=line_data['qty'],
                unit_cost=line_data['unit_cost'],
                line_total=line_data['line_total']
            )
            session.add(invoice_line)
        
        # Step 6: Create StockMove (IN)
        stock_move = StockMove(
            date=datetime.now(),
            type=StockMoveType.IN,
            reference_type=StockReferenceType.INVOICE,
            reference_id=invoice.id,
            notes=f'Compra - Boleta #{invoice_number}'
        )
        session.add(stock_move)
        session.flush()  # Get stock_move.id
        
        # Step 7: Create StockMoveLines
        # Note: The trigger on stock_move_line will update product_stock automatically
        for line_data in validated_lines:
            product = line_data['product']
            stock_move_line = StockMoveLine(
                stock_move_id=stock_move.id,
                product_id=line_data['product_id'],
                qty=line_data['qty'],
                uom_id=product.uom_id,
                unit_cost=line_data['unit_cost']
            )
            session.add(stock_move_line)
        
        # Commit transaction
        session.commit()
        
        return invoice.id
        
    except ValueError:
        # Business logic errors - rollback and re-raise
        session.rollback()
        raise
        
    except IntegrityError as e:
        session.rollback()
        error_msg = str(e.orig)
        
        if 'unique' in error_msg.lower() and 'invoice_number' in error_msg.lower():
            raise ValueError(
                f'Ya existe una boleta con número "{invoice_number}" '
                f'para este proveedor'
            )
        else:
            raise Exception(f'Error de integridad: {error_msg}')
        
    except Exception as e:
        # Other errors - rollback and re-raise
        session.rollback()
        raise Exception(f'Error al crear boleta: {str(e)}')


def update_invoice_with_lines(invoice_id: int, payload: dict, session) -> None:
    """
    Update purchase invoice with lines and adjust stock (PENDING only).
    
    Steps:
    1. Lock invoice FOR UPDATE
    2. Validate status == PENDING
    3. Load old lines, parse new lines
    4. Calculate deltas per product
    5. Create stock_move ADJUST + stock_move_line for deltas
    6. Replace invoice_line (delete old + insert new)
    7. Update invoice metadata + total_amount
    8. Commit
    
    Args:
        invoice_id: Invoice ID to update
        payload: Dictionary with:
            - supplier_id: int (optional, can change supplier)
            - invoice_number: str
            - invoice_date: date
            - due_date: date | None
            - notes: str (optional)
            - lines: list of {product_id, qty, unit_cost}
        session: SQLAlchemy session
    
    Raises:
        ValueError: For business logic errors
        Exception: For other errors
    """
    
    try:
        # Start transaction
        session.begin_nested()
        
        # Step 1: Lock invoice FOR UPDATE
        invoice = (
            session.query(PurchaseInvoice)
            .filter(PurchaseInvoice.id == invoice_id)
            .with_for_update()
            .first()
        )
        
        if not invoice:
            raise ValueError(f'Boleta con ID {invoice_id} no encontrada')
        
        # Step 2: Validate status
        if invoice.status != InvoiceStatus.PENDING:
            raise ValueError(
                f'Solo se pueden editar boletas PENDING. '
                f'Esta boleta está en estado {invoice.status.value}'
            )
        
        # Step 3: Load old lines
        old_lines = {line.product_id: line for line in invoice.lines}
        
        # Step 4: Validate and parse new lines
        lines = payload.get('lines', [])
        
        if not lines or len(lines) == 0:
            raise ValueError('Debe agregar al menos un ítem a la boleta')
        
        # Validate new lines
        new_lines_data = []
        new_lines_by_product = {}
        total_amount = Decimal('0.00')
        
        for line in lines:
            product_id = line.get('product_id')
            if not product_id:
                raise ValueError('Producto ID es requerido en cada línea')
            
            # Check for duplicates
            if product_id in new_lines_by_product:
                raise ValueError(f'El producto ID {product_id} está duplicado en las líneas')
            
            # Get product
            product = session.query(Product).filter_by(id=product_id).first()
            if not product:
                raise ValueError(f'Producto con ID {product_id} no encontrado')
            
            if not product.active:
                raise ValueError(f'El producto "{product.name}" no está activo')
            
            # Validate qty and unit_cost
            try:
                qty = Decimal(str(line.get('qty', 0)))
                if qty <= 0:
                    raise ValueError(f'La cantidad debe ser mayor a 0 para "{product.name}"')
            except (TypeError, ValueError, decimal.InvalidOperation):
                raise ValueError(f'Cantidad inválida para "{product.name}"')
            
            try:
                raw_unit_cost = Decimal(str(line.get('unit_cost', 0)))
                if raw_unit_cost < 0:
                    raise ValueError(f'El costo unitario no puede ser negativo para "{product.name}"')
                
                unit_cost = raw_unit_cost.quantize(Decimal('0.01'))
                if raw_unit_cost != unit_cost:
                    raise ValueError(f'El costo unitario debe tener exactamente 2 decimales para "{product.name}"')
            except (TypeError, ValueError, decimal.InvalidOperation):
                raise ValueError(f'Costo unitario inválido para "{product.name}"')
            
            # Calculate line total
            line_total = (qty * unit_cost).quantize(Decimal('0.01'))
            
            line_data = {
                'product_id': product_id,
                'product': product,
                'qty': qty,
                'unit_cost': unit_cost,
                'line_total': line_total
            }
            
            new_lines_data.append(line_data)
            new_lines_by_product[product_id] = line_data
            total_amount += line_total
        
        total_amount = total_amount.quantize(Decimal('0.01'))
        
        # Step 5: Calculate deltas per product
        deltas = {}  # {product_id: delta_qty}
        
        # Products in old but not in new: delta is negative (remove all)
        for product_id, old_line in old_lines.items():
            if product_id not in new_lines_by_product:
                deltas[product_id] = -old_line.qty
        
        # Products in new: calculate delta
        for product_id, new_line_data in new_lines_by_product.items():
            new_qty = new_line_data['qty']
            old_qty = old_lines[product_id].qty if product_id in old_lines else Decimal('0')
            delta = new_qty - old_qty
            if delta != 0:
                deltas[product_id] = delta
        
        # Step 6: Create stock_move ADJUST for deltas (if any)
        if deltas:
            stock_move = StockMove(
                date=datetime.now(),
                type=StockMoveType.ADJUST,
                reference_type=StockReferenceType.MANUAL,
                reference_id=None,
                notes=f'Ajuste por edición de Boleta #{invoice.invoice_number}'
            )
            session.add(stock_move)
            session.flush()  # Get stock_move.id
            
            # Create stock_move_line for each delta
            for product_id, delta_qty in deltas.items():
                product = session.query(Product).filter_by(id=product_id).first()
                
                stock_move_line = StockMoveLine(
                    stock_move_id=stock_move.id,
                    product_id=product_id,
                    qty=delta_qty,  # Can be positive or negative
                    uom_id=product.uom_id,
                    unit_cost=Decimal('0')  # Adjustments don't have cost
                )
                session.add(stock_move_line)
        
        # Step 7: Update invoice metadata
        # Validate supplier if provided
        supplier_id = payload.get('supplier_id')
        if supplier_id is not None:
            supplier = session.query(Supplier).filter_by(id=supplier_id).first()
            if not supplier:
                raise ValueError(f'Proveedor con ID {supplier_id} no encontrado')
            invoice.supplier_id = supplier_id
        
        # Validate invoice_number uniqueness (if changed)
        invoice_number = payload.get('invoice_number', '').strip()
        if invoice_number and invoice_number != invoice.invoice_number:
            existing = (session.query(PurchaseInvoice)
                       .filter_by(supplier_id=invoice.supplier_id, invoice_number=invoice_number)
                       .filter(PurchaseInvoice.id != invoice_id)
                       .first())
            if existing:
                supplier = session.query(Supplier).filter_by(id=invoice.supplier_id).first()
                raise ValueError(
                    f'Ya existe una boleta con número "{invoice_number}" '
                    f'para el proveedor "{supplier.name}"'
                )
            invoice.invoice_number = invoice_number
        
        # Update other fields
        invoice_date = payload.get('invoice_date')
        if invoice_date:
            invoice.invoice_date = invoice_date
        
        due_date = payload.get('due_date')
        if due_date is not None:
            invoice.due_date = due_date
        
        notes = payload.get('notes')
        if notes is not None:
            invoice.notes = notes.strip() if notes.strip() else None
        
        # Update total_amount
        invoice.total_amount = total_amount
        
        # Step 8: Replace lines (delete old + insert new)
        session.query(PurchaseInvoiceLine).filter_by(invoice_id=invoice_id).delete()
        
        for line_data in new_lines_data:
            invoice_line = PurchaseInvoiceLine(
                invoice_id=invoice_id,
                product_id=line_data['product_id'],
                qty=line_data['qty'],
                unit_cost=line_data['unit_cost'],
                line_total=line_data['line_total']
            )
            session.add(invoice_line)
        
        # Commit transaction
        session.commit()
        
    except ValueError:
        session.rollback()
        raise
    
    except IntegrityError as e:
        session.rollback()
        error_msg = str(e.orig)
        raise Exception(f'Error de integridad al actualizar boleta: {error_msg}')
    
    except Exception as e:
        session.rollback()
        raise Exception(f'Error al actualizar boleta: {str(e)}')


def delete_invoice(invoice_id: int, session) -> None:
    """
    Delete purchase invoice and revert stock (PENDING only).
    
    Steps:
    1. Lock invoice FOR UPDATE
    2. Validate status == PENDING
    3. Load lines
    4. Create stock_move OUT to revert stock
    5. Create stock_move_line for each product (negative qty)
    6. Delete invoice (cascade deletes lines)
    7. Commit
    
    Args:
        invoice_id: Invoice ID to delete
        session: SQLAlchemy session
    
    Raises:
        ValueError: For business logic errors
        Exception: For other errors
    """
    
    try:
        # Start transaction
        session.begin_nested()
        
        # Step 1: Lock invoice FOR UPDATE
        invoice = (
            session.query(PurchaseInvoice)
            .filter(PurchaseInvoice.id == invoice_id)
            .with_for_update()
            .first()
        )
        
        if not invoice:
            raise ValueError(f'Boleta con ID {invoice_id} no encontrada')
        
        # Step 2: Validate status
        if invoice.status != InvoiceStatus.PENDING:
            raise ValueError(
                f'Solo se pueden eliminar boletas PENDING. '
                f'Esta boleta está en estado {invoice.status.value}. '
                f'Si está PAID, tiene un asiento contable registrado y no debe eliminarse.'
            )
        
        # Step 3: Load lines
        lines = invoice.lines
        
        if not lines:
            # No lines, just delete
            session.delete(invoice)
            session.commit()
            return
        
        # Step 4: Create stock_move to revert stock (type ADJUST with negative qty)
        stock_move = StockMove(
            date=datetime.now(),
            type=StockMoveType.ADJUST,
            reference_type=StockReferenceType.MANUAL,
            reference_id=None,
            notes=f'Reversión por eliminación de Boleta #{invoice.invoice_number}'
        )
        session.add(stock_move)
        session.flush()  # Get stock_move.id
        
        # Step 5: Create stock_move_line to revert each product
        for line in lines:
            product = session.query(Product).filter_by(id=line.product_id).first()
            
            # Revert qty: negative delta to remove stock
            revert_qty = -line.qty
            
            stock_move_line = StockMoveLine(
                stock_move_id=stock_move.id,
                product_id=line.product_id,
                qty=revert_qty,  # Negative to remove stock
                uom_id=product.uom_id if product else None,
                unit_cost=Decimal('0')
            )
            session.add(stock_move_line)
        
        # Step 6: Delete invoice (cascade deletes lines)
        session.delete(invoice)
        
        # Commit transaction
        session.commit()
        
    except ValueError:
        session.rollback()
        raise
    
    except IntegrityError as e:
        session.rollback()
        error_msg = str(e.orig)
        raise Exception(f'Error de integridad al eliminar boleta: {error_msg}')
    
    except Exception as e:
        session.rollback()
        raise Exception(f'Error al eliminar boleta: {str(e)}')

