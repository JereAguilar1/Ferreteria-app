"""Sales blueprint for POS and cart management."""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from sqlalchemy import or_, func
from decimal import Decimal
from app.database import get_session
from app.models import Product, ProductStock
from app.services.sales_service import confirm_sale
from app.services.top_products_service import get_top_selling_products

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
        qty = Decimal(request.form.get('qty', '1'))
        
        if qty <= 0:
            flash('La cantidad debe ser mayor a 0', 'danger')
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
        
        # Call service to confirm sale
        sale_id = confirm_sale(cart, db_session)
        
        # Clear cart
        session['cart'] = {'items': {}}
        session.modified = True
        
        flash(f'Venta #{sale_id} confirmada exitosamente. Stock actualizado.', 'success')
        return redirect(url_for('sales.new_sale'))
        
    except ValueError as e:
        # Business logic errors
        flash(str(e), 'danger')
        return redirect(url_for('sales.new_sale'))
        
    except Exception as e:
        flash(f'Error al confirmar venta: {str(e)}', 'danger')
        return redirect(url_for('sales.new_sale'))

