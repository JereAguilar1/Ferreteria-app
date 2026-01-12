"""Sales blueprint for POS and cart management."""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, send_file, current_app
from sqlalchemy import or_, func
from decimal import Decimal
from datetime import datetime
from app.database import get_session
from app.models import Product, ProductStock, Sale, SaleLine, SaleStatus
from app.services.sales_service import confirm_sale
from app.services.top_products_service import get_top_selling_products
from app.services.quote_service import generate_quote_pdf

sales_bp = Blueprint('sales', __name__, url_prefix='/sales')


def get_cart():
    """Get cart from session."""
    if 'cart' not in session:
        session['cart'] = {'items': {}}
    return session['cart']


def save_cart(cart):
    """Save cart to session."""
    session['cart'] = cart
    session.modified = True


def get_cart_with_products(db_session):
    """Get cart with product details from database."""
    cart = get_cart()
    cart_items = []
    total = Decimal('0.00')
    
    for product_id_str, item in cart['items'].items():
        product_id = int(product_id_str)
        product = db_session.query(Product).filter_by(id=product_id).first()
        
        if product:
            qty = Decimal(str(item['qty']))
            subtotal = qty * product.sale_price
            
            cart_items.append({
                'product_id': product.id,
                'product': product,
                'qty': qty,
                'unit_price': product.sale_price,
                'subtotal': subtotal
            })
            total += subtotal
    
    return cart_items, total


@sales_bp.route('/new')
def new_sale():
    """POS screen for new sale."""
    db_session = get_session()
    
    try:
        # Get search query if any
        search_query = request.args.get('q', '').strip()
        
        # Search products
        products = []
        if search_query:
            search_filter = or_(
                func.lower(Product.name).like(f'%{search_query.lower()}%'),
                func.lower(Product.sku).like(f'%{search_query.lower()}%'),
                func.lower(Product.barcode).like(f'%{search_query.lower()}%')
            )
            products = (db_session.query(Product)
                       .outerjoin(ProductStock)
                       .filter(Product.active == True)
                       .filter(search_filter)
                       .order_by(Product.name)
                       .limit(20)
                       .all())
        
        # Get cart items with details
        cart_items, cart_total = get_cart_with_products(db_session)
        
        # Get top selling products
        top_products = get_top_selling_products(db_session, limit=10)
        
        return render_template('sales/new.html',
                             products=products,
                             search_query=search_query,
                             cart_items=cart_items,
                             cart_total=cart_total,
                             top_products=top_products)
        
    except Exception as e:
        flash(f'Error al cargar POS: {str(e)}', 'danger')
        return render_template('sales/new.html',
                             products=[],
                             search_query='',
                             cart_items=[],
                             cart_total=Decimal('0.00'),
                             top_products=[])


@sales_bp.route('/cart/add', methods=['POST'])
def cart_add():
    """Add product to cart (HTMX endpoint)."""
    db_session = get_session()
    
    try:
        product_id = int(request.form.get('product_id'))
        qty = Decimal(request.form.get('qty', '1'))
        
        if qty <= 0:
            flash('La cantidad debe ser mayor a 0', 'danger')
            return redirect(url_for('sales.new_sale'))
        
        # Get product and verify stock
        product = db_session.query(Product).filter_by(id=product_id).first()
        
        if not product:
            flash('Producto no encontrado', 'danger')
            return redirect(url_for('sales.new_sale'))
        
        if not product.active:
            flash(f'El producto "{product.name}" no está activo', 'warning')
            return redirect(url_for('sales.new_sale'))
        
        # Check stock
        if product.on_hand_qty <= 0:
            flash(f'El producto "{product.name}" no tiene stock disponible', 'danger')
            return redirect(url_for('sales.new_sale'))
        
        # Get cart
        cart = get_cart()
        product_id_str = str(product_id)
        
        # Add or update qty
        if product_id_str in cart['items']:
            current_qty = Decimal(str(cart['items'][product_id_str]['qty']))
            new_qty = current_qty + qty
            
            # Check if new qty exceeds stock
            if new_qty > product.on_hand_qty:
                flash(f'Stock insuficiente para "{product.name}". Disponible: {product.on_hand_qty}', 'warning')
                return redirect(url_for('sales.new_sale'))
            
            cart['items'][product_id_str]['qty'] = float(new_qty)
        else:
            # Check if qty exceeds stock
            if qty > product.on_hand_qty:
                flash(f'Stock insuficiente para "{product.name}". Disponible: {product.on_hand_qty}', 'warning')
                return redirect(url_for('sales.new_sale'))
            
            cart['items'][product_id_str] = {'qty': float(qty)}
        
        save_cart(cart)
        flash(f'"{product.name}" agregado al carrito', 'success')
        
        # If HTMX request, return partial
        if request.headers.get('HX-Request'):
            cart_items, cart_total = get_cart_with_products(db_session)
            return render_template('sales/_cart.html',
                                 cart_items=cart_items,
                                 cart_total=cart_total)
        
        return redirect(url_for('sales.new_sale'))
        
    except Exception as e:
        flash(f'Error al agregar producto: {str(e)}', 'danger')
        return redirect(url_for('sales.new_sale'))


@sales_bp.route('/cart/update', methods=['POST'])
def cart_update():
    """Update cart item quantity (HTMX endpoint)."""
    db_session = get_session()
    
    try:
        product_id = int(request.form.get('product_id'))
        qty_str = request.form.get('qty', '').strip()
        
        # MEJORA 15: Handle empty qty (return cart unchanged)
        if not qty_str:
            cart_items, cart_total = get_cart_with_products(db_session)
            return render_template('sales/_cart.html',
                                 cart_items=cart_items,
                                 cart_total=cart_total)
        
        try:
            qty = Decimal(qty_str)
        except:
            flash('Cantidad inválida', 'warning')
            cart_items, cart_total = get_cart_with_products(db_session)
            return render_template('sales/_cart.html',
                                 cart_items=cart_items,
                                 cart_total=cart_total)
        
        # MEJORA 15: If qty <= 0, remove item automatically
        if qty <= 0:
            cart = session.get('cart', {'items': {}})
            if str(product_id) in cart['items']:
                del cart['items'][str(product_id)]
                session['cart'] = cart
                session.modified = True
                flash('Producto eliminado del carrito', 'info')
            cart_items, cart_total = get_cart_with_products(db_session)
            return render_template('sales/_cart.html',
                                 cart_items=cart_items,
                                 cart_total=cart_total)
        
        # Get product and verify stock
        product = db_session.query(Product).filter_by(id=product_id).first()
        
        if not product:
            flash('Producto no encontrado', 'danger')
            return redirect(url_for('sales.new_sale'))
        
        # Check stock
        if qty > product.on_hand_qty:
            flash(f'Stock insuficiente para "{product.name}". Disponible: {product.on_hand_qty}', 'warning')
            cart_items, cart_total = get_cart_with_products(db_session)
            return render_template('sales/_cart.html',
                                 cart_items=cart_items,
                                 cart_total=cart_total)
        
        # Update cart
        cart = get_cart()
        product_id_str = str(product_id)
        
        if product_id_str in cart['items']:
            cart['items'][product_id_str]['qty'] = float(qty)
            save_cart(cart)
        
        # Return updated cart partial
        cart_items, cart_total = get_cart_with_products(db_session)
        return render_template('sales/_cart.html',
                             cart_items=cart_items,
                             cart_total=cart_total)
        
    except Exception as e:
        flash(f'Error al actualizar carrito: {str(e)}', 'danger')
        cart_items, cart_total = get_cart_with_products(db_session)
        return render_template('sales/_cart.html',
                             cart_items=cart_items,
                             cart_total=cart_total)


@sales_bp.route('/cart/remove', methods=['POST'])
def cart_remove():
    """Remove item from cart (HTMX endpoint)."""
    db_session = get_session()
    
    try:
        product_id = int(request.form.get('product_id'))
        
        # Remove from cart
        cart = get_cart()
        product_id_str = str(product_id)
        
        if product_id_str in cart['items']:
            del cart['items'][product_id_str]
            save_cart(cart)
            flash('Producto removido del carrito', 'info')
        
        # Return updated cart partial
        cart_items, cart_total = get_cart_with_products(db_session)
        return render_template('sales/_cart.html',
                             cart_items=cart_items,
                             cart_total=cart_total)
        
    except Exception as e:
        flash(f'Error al remover producto: {str(e)}', 'danger')
        cart_items, cart_total = get_cart_with_products(db_session)
        return render_template('sales/_cart.html',
                             cart_items=cart_items,
                             cart_total=cart_total)


@sales_bp.route('/confirm/preview', methods=['GET'])
def confirm_preview():
    """Preview sale before confirmation (MEJORA 15 - Modal)."""
    db_session = get_session()
    
    try:
        cart = get_cart()
        
        # Validate cart not empty
        if not cart.get('items'):
            return '''
                <div class="alert alert-warning">
                    El carrito está vacío. Agregue productos para continuar.
                </div>
            '''
        
        # Get cart items with products
        cart_items, cart_total = get_cart_with_products(db_session)
        
        # Get payment method from form (if selected)
        # For preview, we'll pass it from the button or default to CASH
        payment_method = request.args.get('payment_method', 'CASH')
        
        return render_template('sales/_confirm_modal.html',
                             cart_items=cart_items,
                             cart_total=cart_total,
                             payment_method=payment_method)
        
    except Exception as e:
        return f'''
            <div class="alert alert-danger">
                Error al cargar vista previa: {str(e)}
            </div>
        '''


@sales_bp.route('/confirm', methods=['POST'])
def confirm():
    """Confirm sale and process transaction."""
    db_session = get_session()
    
    try:
        cart = get_cart()
        
        # Validate cart not empty
        if not cart['items']:
            flash('El carrito está vacío. Agregue productos antes de confirmar.', 'warning')
            return redirect(url_for('sales.new_sale'))
        
        # MEJORA 12: Get payment method from form
        payment_method = request.form.get('payment_method', 'CASH').upper()
        
        # Validate payment method
        if payment_method not in ['CASH', 'TRANSFER']:
            flash('Método de pago inválido.', 'danger')
            return redirect(url_for('sales.new_sale'))
        
        # Call service to confirm sale
        sale_id = confirm_sale(cart, db_session, payment_method)
        
        # Clear cart
        session['cart'] = {'items': {}}
        session.modified = True
        
        payment_label = 'Efectivo' if payment_method == 'CASH' else 'Transferencia'
        flash(f'Venta #{sale_id} confirmada exitosamente ({payment_label}). Stock actualizado.', 'success')
        return redirect(url_for('sales.new_sale'))
        
    except ValueError as e:
        # Business logic errors
        flash(str(e), 'danger')
        return redirect(url_for('sales.new_sale'))
        
    except Exception as e:
        flash(f'Error al confirmar venta: {str(e)}', 'danger')
        return redirect(url_for('sales.new_sale'))


@sales_bp.route('/quote.pdf')
def quote_pdf():
    """Generate and download PDF quote from current cart (no sale creation)."""
    db_session = get_session()
    
    try:
        cart = get_cart()
        
        # Validate cart not empty
        if not cart['items']:
            flash('El carrito está vacío. Agregue productos para generar un presupuesto.', 'warning')
            return redirect(url_for('sales.new_sale'))
        
        # Build cart with product details
        cart_with_details = {'items': {}}
        
        for product_id_str, item in cart['items'].items():
            product_id = int(product_id_str)
            product = db_session.query(Product).filter_by(id=product_id).first()
            
            if not product:
                continue
            
            cart_with_details['items'][product_id_str] = {
                'name': product.name,
                'qty': Decimal(str(item['qty'])),
                'price': product.sale_price,
                'uom': product.uom.symbol if product.uom else '—'
            }
        
        # Get payment method from session if available (MEJORA 12)
        # Note: In the current UI, method is only sent on confirm, not stored in session
        # So this will be empty unless we modify the UI to store it
        payment_method = session.get('quote_payment_method', None)
        
        # Business info from config
        business_info = {
            'name': current_app.config.get('BUSINESS_NAME', 'Ferretería'),
            'address': current_app.config.get('BUSINESS_ADDRESS', ''),
            'phone': current_app.config.get('BUSINESS_PHONE', ''),
            'email': current_app.config.get('BUSINESS_EMAIL', ''),
            'valid_days': current_app.config.get('QUOTE_VALID_DAYS', 7),
            'payment_method': payment_method
        }
        
        # Generate PDF
        pdf_buffer = generate_quote_pdf(cart_with_details, business_info)
        
        # Generate filename with timestamp
        filename = f"presupuesto_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        # Return PDF as download
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        flash(f'Error al generar presupuesto: {str(e)}', 'danger')
        return redirect(url_for('sales.new_sale'))


# ============================================================================
# MEJORA 16: Sales Management (List, Detail, Edit/Adjust)
# ============================================================================

@sales_bp.route('/')
def list_sales():
    """List all confirmed sales with search."""
    db_session = get_session()
    
    try:
        # Get search params
        sale_id_search = request.args.get('id', '').strip()
        
        # Build query
        from app.models import Sale, SaleStatus
        query = db_session.query(Sale).filter(Sale.status == SaleStatus.CONFIRMED)
        
        # Search by ID
        if sale_id_search:
            try:
                sale_id = int(sale_id_search)
                query = query.filter(Sale.id == sale_id)
            except ValueError:
                flash('ID de venta inválido', 'warning')
        
        # Order by most recent first
        sales = query.order_by(Sale.datetime.desc()).all()
        
        return render_template('sales/list.html', 
                             sales=sales,
                             sale_id_search=sale_id_search)
        
    except Exception as e:
        flash(f'Error al cargar ventas: {str(e)}', 'danger')
        return redirect(url_for('sales.new_sale'))


@sales_bp.route('/<int:sale_id>')
def detail_sale(sale_id):
    """Show sale detail."""
    db_session = get_session()
    
    try:
        from app.models import Sale
        sale = db_session.query(Sale).filter_by(id=sale_id).first()
        
        if not sale:
            flash('Venta no encontrada', 'danger')
            return redirect(url_for('sales.list_sales'))
        
        return render_template('sales/detail.html', sale=sale)
        
    except Exception as e:
        flash(f'Error al cargar venta: {str(e)}', 'danger')
        return redirect(url_for('sales.list_sales'))


@sales_bp.route('/<int:sale_id>/edit', methods=['GET'])
def edit_sale_form(sale_id):
    """Show form to edit/adjust a sale."""
    db_session = get_session()
    
    try:
        from app.services.sale_adjustment_service import get_sale_summary
        
        sale_summary = get_sale_summary(sale_id, db_session)
        
        # Get active products for search
        products = db_session.query(Product).filter(
            Product.active == True
        ).order_by(Product.name).all()
        
        return render_template('sales/edit.html', 
                             sale=sale_summary,
                             products=products)
        
    except ValueError as e:
        flash(str(e), 'danger')
        return redirect(url_for('sales.list_sales'))
    except Exception as e:
        flash(f'Error al cargar formulario de edición: {str(e)}', 'danger')
        return redirect(url_for('sales.list_sales'))


@sales_bp.route('/<int:sale_id>/edit/preview', methods=['POST'])
def edit_sale_preview(sale_id):
    """Preview sale adjustments before applying (MEJORA 17)."""
    db_session = get_session()
    
    try:
        # Parse lines from form
        lines = []
        line_index = 0
        
        while True:
            product_id_key = f'lines[{line_index}][product_id]'
            qty_key = f'lines[{line_index}][qty]'
            
            if product_id_key not in request.form:
                break
            
            product_id = request.form.get(product_id_key)
            qty = request.form.get(qty_key)
            
            if product_id and qty:
                lines.append({
                    'product_id': int(product_id),
                    'qty': Decimal(qty)
                })
            
            line_index += 1
        
        if not lines:
            return '<div class="alert alert-warning">Debe haber al menos una línea en la venta.</div>'
        
        # Get current sale
        sale = db_session.query(Sale).filter_by(id=sale_id).first()
        if not sale:
            return '<div class="alert alert-danger">Venta no encontrada.</div>'
        
        # Build old_lines
        old_lines = []
        old_total = Decimal('0.00')
        for line in sale.lines:
            old_lines.append({
                'product_id': line.product_id,
                'product_name': line.product.name,
                'product_sku': line.product.sku or '-',
                'product_uom': line.product.uom.symbol if line.product.uom else '-',
                'qty': line.qty,
                'unit_price': line.unit_price,
                'subtotal': line.line_total
            })
            old_total += line.line_total
        
        # Build new_lines with product info
        new_lines = []
        new_total = Decimal('0.00')
        products_cache = {}
        
        for line_data in lines:
            product_id = line_data['product_id']
            qty = line_data['qty']
            
            # Get product
            if product_id not in products_cache:
                product = db_session.query(Product).filter_by(id=product_id).first()
                if not product:
                    continue
                products_cache[product_id] = product
            else:
                product = products_cache[product_id]
            
            # Use original unit_price if product was in old sale, else current price
            old_line = next((ol for ol in old_lines if ol['product_id'] == product_id), None)
            unit_price = old_line['unit_price'] if old_line else product.sale_price
            
            subtotal = qty * unit_price
            new_lines.append({
                'product_id': product_id,
                'product_name': product.name,
                'product_sku': product.sku or '-',
                'product_uom': product.uom.symbol if product.uom else '-',
                'qty': qty,
                'unit_price': unit_price,
                'subtotal': subtotal,
                'current_stock': product.on_hand_qty
            })
            new_total += subtotal
        
        # Calculate deltas
        changes = {
            'added': [],
            'removed': [],
            'modified': [],
            'stock_issues': []
        }
        
        # Check for removed
        for old_line in old_lines:
            if not any(nl['product_id'] == old_line['product_id'] for nl in new_lines):
                changes['removed'].append(old_line)
        
        # Check for added and modified
        for new_line in new_lines:
            old_line = next((ol for ol in old_lines if ol['product_id'] == new_line['product_id']), None)
            
            if not old_line:
                # Added
                changes['added'].append(new_line)
                
                # Check stock
                if new_line['qty'] > new_line['current_stock']:
                    changes['stock_issues'].append({
                        'product_name': new_line['product_name'],
                        'needed': new_line['qty'],
                        'available': new_line['current_stock']
                    })
            else:
                # Modified?
                if new_line['qty'] != old_line['qty']:
                    delta_qty = new_line['qty'] - old_line['qty']
                    changes['modified'].append({
                        'product_name': new_line['product_name'],
                        'old_qty': old_line['qty'],
                        'new_qty': new_line['qty'],
                        'delta_qty': delta_qty
                    })
                    
                    # Check stock if increasing
                    if delta_qty > 0:
                        if delta_qty > new_line['current_stock']:
                            changes['stock_issues'].append({
                                'product_name': new_line['product_name'],
                                'needed': delta_qty,
                                'available': new_line['current_stock']
                            })
        
        # Check if no changes
        if not changes['added'] and not changes['removed'] and not changes['modified']:
            return '<div class="alert alert-info">No hay cambios para aplicar.</div>'
        
        # Calculate diff
        diff = new_total - old_total
        
        return render_template('sales/_edit_confirm_modal.html',
                             sale_id=sale_id,
                             old_lines=old_lines,
                             new_lines=new_lines,
                             old_total=old_total,
                             new_total=new_total,
                             diff=diff,
                             changes=changes)
        
    except Exception as e:
        current_app.logger.error(f"Error in edit_sale_preview: {str(e)}", exc_info=True)
        return f'<div class="alert alert-danger">Error al generar vista previa: {str(e)}</div>'


@sales_bp.route('/<int:sale_id>/edit', methods=['POST'])
def edit_sale_save(sale_id):
    """Save sale adjustments."""
    db_session = get_session()
    
    try:
        from app.services.sale_adjustment_service import adjust_sale
        
        # Parse lines from form
        # Expected format: lines[0][product_id], lines[0][qty], lines[1][product_id], ...
        lines = []
        line_index = 0
        
        while True:
            product_id_key = f'lines[{line_index}][product_id]'
            qty_key = f'lines[{line_index}][qty]'
            
            if product_id_key not in request.form:
                break
            
            product_id = request.form.get(product_id_key)
            qty = request.form.get(qty_key)
            
            if product_id and qty:
                lines.append({
                    'product_id': int(product_id),
                    'qty': Decimal(qty)
                })
            
            line_index += 1
        
        if not lines:
            flash('Debe haber al menos una línea en la venta', 'warning')
            return redirect(url_for('sales.edit_sale_form', sale_id=sale_id))
        
        # Apply adjustment
        adjust_sale(sale_id, lines, db_session)
        
        flash(f'Venta #{sale_id} ajustada exitosamente', 'success')
        return redirect(url_for('sales.detail_sale', sale_id=sale_id))
        
    except ValueError as e:
        flash(str(e), 'danger')
        return redirect(url_for('sales.edit_sale_form', sale_id=sale_id))
    except Exception as e:
        flash(f'Error al guardar ajustes: {str(e)}', 'danger')
        return redirect(url_for('sales.edit_sale_form', sale_id=sale_id))

