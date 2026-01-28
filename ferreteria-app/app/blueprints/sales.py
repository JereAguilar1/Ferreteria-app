"""Sales blueprint for POS and cart management."""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, send_file, current_app
from sqlalchemy import or_, func
from decimal import Decimal, InvalidOperation
from datetime import datetime
from app.database import get_session
from app.models import Product, ProductStock, Sale, SaleLine, SaleStatus
from app.services.sales_service import confirm_sale
from app.services.top_products_service import get_top_selling_products
from app.services.quote_service import generate_quote_pdf

sales_bp = Blueprint('sales', __name__, url_prefix='/sales')

def parse_decimal_ar(raw, default="0"):
    """
    Acepta '1.234,56' (AR) y '1234.56' (normalizado).
    Devuelve Decimal o lanza ValueError con mensaje claro.
    """
    if raw is None:
        raw = ""
    s = str(raw).strip()

    if s == "":
        s = str(default)

    # AR -> estándar Decimal
    s = s.replace(".", "").replace(",", ".")

    try:
        return Decimal(s)
    except InvalidOperation:
        raise ValueError(f"Numero invalido: {raw!r}")

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
    from app.models import ProductUomPrice, UOM
    cart = get_cart()
    cart_items = []
    total = Decimal('0.00')
    
    for cart_key, item in cart['items'].items():
        # MEJORA A: Handle new cart format (product_id_uom_id) or legacy (product_id)
        if isinstance(item, dict) and 'product_id' in item:
            # New format
            product_id = item['product_id']
            uom_id = item['uom_id']
            qty = Decimal(str(item['qty']))
            unit_price = Decimal(str(item['unit_price']))
        else:
            # Legacy format: cart_key is product_id_str
            try:
                product_id = int(cart_key)
            except ValueError:
                # New format: cart_key is "product_id_uom_id"
                parts = cart_key.split('_')
                if len(parts) == 2:
                    product_id = int(parts[0])
                    uom_id = int(parts[1])
                else:
                    continue
            
            qty = Decimal(str(item['qty']))
            # Get unit_price from item or product
            if 'unit_price' in item:
                unit_price = Decimal(str(item['unit_price']))
                uom_id = item.get('uom_id')
            else:
                # Legacy: get from product
                product = db_session.query(Product).filter_by(id=product_id).first()
                if not product:
                    continue
                unit_price = product.sale_price
                uom_id = product.uom_id
        
        product = db_session.query(Product).filter_by(id=product_id).first()
        
        if product:
            # Get UOM details
            uom = db_session.query(UOM).filter_by(id=uom_id).first() if uom_id else product.uom
            
            subtotal = qty * unit_price
            
            cart_items.append({
                'cart_key': cart_key,
                'product_id': product.id,
                'product': product,
                'uom_id': uom_id,
                'uom': uom,
                'qty': qty,
                'qty_base': Decimal(str(item.get('qty_base', qty))) if isinstance(item, dict) else qty,
                'unit_price': unit_price,
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


@sales_bp.route('/product/<int:product_id>/uom-selector', methods=['GET'])
def product_uom_selector(product_id):
    """Get UOM selector modal for a product (HTMX endpoint)."""
    from app.models import ProductUomPrice
    db_session = get_session()
    
    try:
        product = db_session.query(Product).filter_by(id=product_id).first()
        if not product:
            return '<div class="alert alert-danger">Producto no encontrado</div>'
        
        # Get all UOM prices for this product
        uom_prices = db_session.query(ProductUomPrice).filter_by(product_id=product_id).order_by(
            ProductUomPrice.is_base.desc()
        ).all()
        
        if not uom_prices or len(uom_prices) == 1:
            # Only one UOM, add directly with default qty
            return f'''
                <script>
                    htmx.ajax('POST', '{url_for("sales.cart_add")}', {{
                        target: '#cart-container',
                        swap: 'outerHTML',
                        values: {{
                            product_id: {product_id},
                            uom_id: {uom_prices[0].uom_id if uom_prices else product.uom_id},
                            qty: 1
                        }}
                    }});
                </script>
            '''
        
        # Multiple UOMs, show modal
        return render_template('sales/_uom_selector_modal.html',
                             product=product,
                             uom_prices=uom_prices)
        
    except Exception as e:
        return f'<div class="alert alert-danger">Error: {str(e)}</div>'


@sales_bp.route('/cart/add', methods=['POST'])
def cart_add():
    """Add product to cart (HTMX endpoint)."""
    db_session = get_session()
    
    try:
        product_id = int(request.form.get('product_id'))
        qty = parse_decimal_ar(request.form.get('qty'), default="1")
        uom_id = request.form.get('uom_id')  # MEJORA A: UOM selection
        
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
        
        # MEJORA A: Get UOM price
        if uom_id:
            uom_id = int(uom_id)
            from app.models import ProductUomPrice
            uom_price = db_session.query(ProductUomPrice).filter_by(
                product_id=product_id,
                uom_id=uom_id
            ).first()
            
            if not uom_price:
                flash(f'Unidad de medida no válida para "{product.name}"', 'danger')
                return redirect(url_for('sales.new_sale'))
            
            unit_price = uom_price.sale_price
            conversion_to_base = uom_price.conversion_to_base
            qty_base = qty * conversion_to_base
        else:
            # Fallback to base UOM
            from app.services.product_uom_service import get_base_uom_price
            base_uom_price = get_base_uom_price(db_session, product_id)
            if base_uom_price:
                uom_id = base_uom_price.uom_id
                unit_price = base_uom_price.sale_price
                conversion_to_base = base_uom_price.conversion_to_base
                qty_base = qty * conversion_to_base
            else:
                # Legacy fallback
                uom_id = product.uom_id
                unit_price = product.sale_price
                qty_base = qty
        
        # Check stock (in base units)
        if product.on_hand_qty <= 0:
            flash(f'El producto "{product.name}" no tiene stock disponible', 'danger')
            return redirect(url_for('sales.new_sale'))
        
        # Get cart
        cart = get_cart()
        # MEJORA A: Use product_id + uom_id as key
        cart_key = f"{product_id}_{uom_id}"
        
        # Add or update qty
        if cart_key in cart['items']:
            current_qty = Decimal(str(cart['items'][cart_key]['qty']))
            current_qty_base = Decimal(str(cart['items'][cart_key]['qty_base']))
            new_qty = current_qty + qty
            new_qty_base = current_qty_base + qty_base
            
            # Check if new qty exceeds stock
            if new_qty_base > product.on_hand_qty:
                flash(f'Stock insuficiente para "{product.name}". Disponible: {product.on_hand_qty}', 'warning')
                return redirect(url_for('sales.new_sale'))
            
            cart['items'][cart_key]['qty'] = float(new_qty)
            cart['items'][cart_key]['qty_base'] = float(new_qty_base)
        else:
            # Check if qty exceeds stock
            if qty_base > product.on_hand_qty:
                flash(f'Stock insuficiente para "{product.name}". Disponible: {product.on_hand_qty}', 'warning')
                return redirect(url_for('sales.new_sale'))
            
            cart['items'][cart_key] = {
                'product_id': product_id,
                'uom_id': uom_id,
                'qty': float(qty),
                'qty_base': float(qty_base),
                'unit_price': float(unit_price)
            }
        
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
        # MEJORA A: Use cart_key instead of product_id
        cart_key = request.form.get('cart_key', '').strip()
        qty_str = request.form.get('qty', '').strip()
        
        if not cart_key:
            flash('Error: clave de carrito no válida', 'danger')
            cart_items, cart_total = get_cart_with_products(db_session)
            return render_template('sales/_cart.html',
                                 cart_items=cart_items,
                                 cart_total=cart_total)
        
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
            if cart_key in cart['items']:
                del cart['items'][cart_key]
                session['cart'] = cart
                session.modified = True
                flash('Producto eliminado del carrito', 'info')
            cart_items, cart_total = get_cart_with_products(db_session)
            return render_template('sales/_cart.html',
                                 cart_items=cart_items,
                                 cart_total=cart_total)
        
        # Get cart and item
        cart = get_cart()
        
        if cart_key not in cart['items']:
            flash('Producto no encontrado en el carrito', 'warning')
            cart_items, cart_total = get_cart_with_products(db_session)
            return render_template('sales/_cart.html',
                                 cart_items=cart_items,
                                 cart_total=cart_total)
        
        item = cart['items'][cart_key]
        
        # Get product_id from cart_key or item
        if isinstance(item, dict) and 'product_id' in item:
            product_id = item['product_id']
            uom_id = item.get('uom_id')
            conversion_to_base = Decimal(str(item.get('conversion_to_base', 1)))
        else:
            # Legacy format: cart_key might be product_id or "product_id_uom_id"
            try:
                parts = cart_key.split('_')
                product_id = int(parts[0])
                uom_id = int(parts[1]) if len(parts) > 1 else None
                conversion_to_base = Decimal('1')
            except:
                product_id = int(cart_key)
                uom_id = None
                conversion_to_base = Decimal('1')
        
        # Get product and verify stock
        product = db_session.query(Product).filter_by(id=product_id).first()
        
        if not product:
            flash('Producto no encontrado', 'danger')
            return redirect(url_for('sales.new_sale'))
        
        # MEJORA A: Calculate qty_base for stock validation
        if isinstance(item, dict) and 'conversion_to_base' in item:
            conversion_to_base = Decimal(str(item['conversion_to_base']))
        else:
            # Get conversion from UOM price if available
            if uom_id:
                from app.models import ProductUomPrice
                uom_price = db_session.query(ProductUomPrice).filter_by(
                    product_id=product_id,
                    uom_id=uom_id
                ).first()
                if uom_price:
                    conversion_to_base = uom_price.conversion_to_base
        
        qty_base = qty * conversion_to_base
        
        # Check stock (in base units)
        if qty_base > product.on_hand_qty:
            flash(f'Stock insuficiente para "{product.name}". Disponible: {product.on_hand_qty}', 'warning')
            cart_items, cart_total = get_cart_with_products(db_session)
            return render_template('sales/_cart.html',
                                 cart_items=cart_items,
                                 cart_total=cart_total)
        
        # Update cart
        if isinstance(item, dict):
            cart['items'][cart_key]['qty'] = float(qty)
            cart['items'][cart_key]['qty_base'] = float(qty_base)
        else:
            # Legacy format
            cart['items'][cart_key] = {'qty': float(qty)}
        
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
        # MEJORA A: Use cart_key instead of product_id
        cart_key = request.form.get('cart_key', '').strip()
        
        if not cart_key:
            flash('Error: clave de carrito no válida', 'danger')
            cart_items, cart_total = get_cart_with_products(db_session)
            return render_template('sales/_cart.html',
                                 cart_items=cart_items,
                                 cart_total=cart_total)
        
        # Remove from cart
        cart = get_cart()
        
        if cart_key in cart['items']:
            del cart['items'][cart_key]
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
        
        # Generate filename with timestamp (Argentina)
        from app.utils.formatters import get_now_ar
        filename = f"presupuesto_{get_now_ar().strftime('%Y%m%d_%H%M%S')}.pdf"
        
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

