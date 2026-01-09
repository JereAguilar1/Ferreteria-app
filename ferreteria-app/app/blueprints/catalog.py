"""Catalog blueprint for products management."""
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from sqlalchemy import or_, func
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename
import os
from app.database import get_session
from app.models import Product, ProductStock, UOM, Category

catalog_bp = Blueprint('catalog', __name__, url_prefix='/products')

# Allowed image extensions
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB


def allowed_file(filename):
    """Check if file has allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_product_image(file):
    """
    Save product image and return the filename.
    Returns None if no file or invalid file.
    """
    if not file or file.filename == '':
        return None
    
    if not allowed_file(file.filename):
        flash('Formato de imagen no permitido. Use JPG, JPEG o PNG', 'danger')
        return None
    
    # Check file size
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)  # Reset file pointer
    
    if file_size > MAX_FILE_SIZE:
        flash('La imagen es demasiado grande. Máximo 2MB', 'danger')
        return None
    
    # Generate secure filename
    filename = secure_filename(file.filename)
    # Add timestamp to avoid collisions
    import time
    filename = f"{int(time.time())}_{filename}"
    
    # Save file
    upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'products')
    os.makedirs(upload_folder, exist_ok=True)
    filepath = os.path.join(upload_folder, filename)
    file.save(filepath)
    
    return filename


@catalog_bp.route('/')
def list_products():
    """List all products with stock information."""
    session = get_session()
    
    try:
        # Get search and filter parameters
        search_query = request.args.get('q', '').strip()
        category_id = request.args.get('category_id', '').strip()
        
        # Get all categories for the filter dropdown
        categories = session.query(Category).order_by(Category.name).all()
        
        # Build query with left join to product_stock
        query = session.query(Product).outerjoin(ProductStock)
        
        # Apply category filter if provided
        category_filter_applied = False
        if category_id:
            try:
                category_id_int = int(category_id)
                # Verify category exists
                category_exists = session.query(Category).filter_by(id=category_id_int).first()
                if category_exists:
                    query = query.filter(Product.category_id == category_id_int)
                    category_filter_applied = True
                else:
                    flash('La categoría seleccionada no existe. Mostrando todos los productos.', 'warning')
                    category_id = ''  # Reset to show all
            except ValueError:
                flash('ID de categoría inválido. Mostrando todos los productos.', 'warning')
                category_id = ''  # Reset to show all
        
        # Apply search filter if provided
        if search_query:
            search_filter = or_(
                func.lower(Product.name).like(f'%{search_query.lower()}%'),
                func.lower(Product.sku).like(f'%{search_query.lower()}%'),
                func.lower(Product.barcode).like(f'%{search_query.lower()}%')
            )
            query = query.filter(search_filter)
        
        # Order by name
        products = query.order_by(Product.name).all()
        
        return render_template('products/list.html', 
                             products=products, 
                             search_query=search_query,
                             categories=categories,
                             selected_category_id=category_id)
        
    except Exception as e:
        flash(f'Error al cargar productos: {str(e)}', 'danger')
        categories = session.query(Category).order_by(Category.name).all()
        return render_template('products/list.html', 
                             products=[], 
                             search_query='',
                             categories=categories,
                             selected_category_id='')


@catalog_bp.route('/new', methods=['GET'])
def new_product():
    """Show form to create a new product."""
    session = get_session()
    
    try:
        # Check if UOM table has data
        uom_count = session.query(UOM).count()
        if uom_count == 0:
            flash('No hay unidades de medida cargadas. Por favor, ejecute el script de seed primero.', 'warning')
            return redirect(url_for('catalog.list_products'))
        
        uoms = session.query(UOM).order_by(UOM.name).all()
        categories = session.query(Category).order_by(Category.name).all()
        
        return render_template('products/form.html', 
                             product=None, 
                             uoms=uoms, 
                             categories=categories,
                             action='new')
        
    except Exception as e:
        flash(f'Error al cargar formulario: {str(e)}', 'danger')
        return redirect(url_for('catalog.list_products'))


@catalog_bp.route('/new', methods=['POST'])
def create_product():
    """Create a new product."""
    session = get_session()
    
    try:
        # Get form data
        name = request.form.get('name', '').strip()
        sku = request.form.get('sku', '').strip() or None
        barcode = request.form.get('barcode', '').strip() or None
        category_id = request.form.get('category_id', '').strip() or None
        uom_id = request.form.get('uom_id', '').strip()
        sale_price = request.form.get('sale_price', '0').strip()
        active = request.form.get('active') == 'on'
        
        # Server-side validations
        errors = []
        
        if not name:
            errors.append('El nombre es requerido')
        
        if not uom_id:
            errors.append('La unidad de medida es requerida')
        else:
            # Verify UOM exists
            uom = session.query(UOM).filter_by(id=int(uom_id)).first()
            if not uom:
                errors.append('La unidad de medida seleccionada no existe')
        
        try:
            sale_price_decimal = float(sale_price)
            if sale_price_decimal < 0:
                errors.append('El precio de venta debe ser mayor o igual a 0')
        except ValueError:
            errors.append('El precio de venta debe ser un número válido')
        
        if errors:
            for error in errors:
                flash(error, 'danger')
            uoms = session.query(UOM).order_by(UOM.name).all()
            categories = session.query(Category).order_by(Category.name).all()
            return render_template('products/form.html',
                                 product=None,
                                 uoms=uoms,
                                 categories=categories,
                                 action='new')
        
        # Handle image upload
        image_filename = None
        if 'image' in request.files:
            image_file = request.files['image']
            image_filename = save_product_image(image_file)
        
        # Create product
        product = Product(
            name=name,
            sku=sku,
            barcode=barcode,
            category_id=int(category_id) if category_id else None,
            uom_id=int(uom_id),
            sale_price=sale_price_decimal,
            active=active,
            image_path=image_filename
        )
        
        session.add(product)
        session.commit()
        
        # Note: product_stock is created automatically by database trigger
        
        flash(f'Producto "{product.name}" creado exitosamente', 'success')
        return redirect(url_for('catalog.list_products'))
        
    except IntegrityError as e:
        session.rollback()
        error_msg = str(e.orig)
        
        if 'unique' in error_msg.lower():
            if 'sku' in error_msg.lower():
                flash(f'El SKU "{sku}" ya está en uso. Por favor, use otro SKU.', 'danger')
            elif 'barcode' in error_msg.lower():
                flash(f'El código de barras "{barcode}" ya está en uso. Por favor, use otro código.', 'danger')
            else:
                flash('Ya existe un producto con estos datos únicos.', 'danger')
        else:
            flash(f'Error de integridad al crear producto: {error_msg}', 'danger')
        
        uoms = session.query(UOM).order_by(UOM.name).all()
        categories = session.query(Category).order_by(Category.name).all()
        return render_template('products/form.html',
                             product=None,
                             uoms=uoms,
                             categories=categories,
                             action='new')
        
    except Exception as e:
        session.rollback()
        flash(f'Error al crear producto: {str(e)}', 'danger')
        return redirect(url_for('catalog.list_products'))


@catalog_bp.route('/<int:product_id>/edit', methods=['GET'])
def edit_product(product_id):
    """Show form to edit a product."""
    session = get_session()
    
    try:
        product = session.query(Product).filter_by(id=product_id).first()
        
        if not product:
            flash('Producto no encontrado', 'danger')
            return redirect(url_for('catalog.list_products'))
        
        uoms = session.query(UOM).order_by(UOM.name).all()
        categories = session.query(Category).order_by(Category.name).all()
        
        return render_template('products/form.html',
                             product=product,
                             uoms=uoms,
                             categories=categories,
                             action='edit')
        
    except Exception as e:
        flash(f'Error al cargar producto: {str(e)}', 'danger')
        return redirect(url_for('catalog.list_products'))


@catalog_bp.route('/<int:product_id>/edit', methods=['POST'])
def update_product(product_id):
    """Update a product."""
    session = get_session()
    
    try:
        product = session.query(Product).filter_by(id=product_id).first()
        
        if not product:
            flash('Producto no encontrado', 'danger')
            return redirect(url_for('catalog.list_products'))
        
        # Get form data
        name = request.form.get('name', '').strip()
        sku = request.form.get('sku', '').strip() or None
        barcode = request.form.get('barcode', '').strip() or None
        category_id = request.form.get('category_id', '').strip() or None
        uom_id = request.form.get('uom_id', '').strip()
        sale_price = request.form.get('sale_price', '0').strip()
        active = request.form.get('active') == 'on'
        
        # Server-side validations
        errors = []
        
        if not name:
            errors.append('El nombre es requerido')
        
        if not uom_id:
            errors.append('La unidad de medida es requerida')
        else:
            uom = session.query(UOM).filter_by(id=int(uom_id)).first()
            if not uom:
                errors.append('La unidad de medida seleccionada no existe')
        
        try:
            sale_price_decimal = float(sale_price)
            if sale_price_decimal < 0:
                errors.append('El precio de venta debe ser mayor o igual a 0')
        except ValueError:
            errors.append('El precio de venta debe ser un número válido')
        
        if errors:
            for error in errors:
                flash(error, 'danger')
            uoms = session.query(UOM).order_by(UOM.name).all()
            categories = session.query(Category).order_by(Category.name).all()
            return render_template('products/form.html',
                                 product=product,
                                 uoms=uoms,
                                 categories=categories,
                                 action='edit')
        
        # Handle image upload
        if 'image' in request.files:
            image_file = request.files['image']
            if image_file and image_file.filename != '':
                # Delete old image if exists
                if product.image_path:
                    old_image_path = os.path.join(current_app.root_path, 'static', 'uploads', 'products', product.image_path)
                    if os.path.exists(old_image_path):
                        try:
                            os.remove(old_image_path)
                        except Exception:
                            pass  # Ignore errors deleting old image
                
                # Save new image
                image_filename = save_product_image(image_file)
                if image_filename:
                    product.image_path = image_filename
        
        # Update product
        product.name = name
        product.sku = sku
        product.barcode = barcode
        product.category_id = int(category_id) if category_id else None
        product.uom_id = int(uom_id)
        product.sale_price = sale_price_decimal
        product.active = active
        
        session.commit()
        
        flash(f'Producto "{product.name}" actualizado exitosamente', 'success')
        return redirect(url_for('catalog.list_products'))
        
    except IntegrityError as e:
        session.rollback()
        error_msg = str(e.orig)
        
        if 'unique' in error_msg.lower():
            if 'sku' in error_msg.lower():
                flash(f'El SKU "{sku}" ya está en uso. Por favor, use otro SKU.', 'danger')
            elif 'barcode' in error_msg.lower():
                flash(f'El código de barras "{barcode}" ya está en uso. Por favor, use otro código.', 'danger')
            else:
                flash('Ya existe un producto con estos datos únicos.', 'danger')
        else:
            flash(f'Error de integridad al actualizar producto: {error_msg}', 'danger')
        
        uoms = session.query(UOM).order_by(UOM.name).all()
        categories = session.query(Category).order_by(Category.name).all()
        return render_template('products/form.html',
                             product=product,
                             uoms=uoms,
                             categories=categories,
                             action='edit')
        
    except Exception as e:
        session.rollback()
        flash(f'Error al actualizar producto: {str(e)}', 'danger')
        return redirect(url_for('catalog.list_products'))


@catalog_bp.route('/<int:product_id>/toggle-active', methods=['POST'])
def toggle_active(product_id):
    """Toggle product active status."""
    session = get_session()
    
    try:
        product = session.query(Product).filter_by(id=product_id).first()
        
        if not product:
            flash('Producto no encontrado', 'danger')
            return redirect(url_for('catalog.list_products'))
        
        product.active = not product.active
        session.commit()
        
        status = 'activado' if product.active else 'desactivado'
        flash(f'Producto "{product.name}" {status} exitosamente', 'success')
        
        return redirect(url_for('catalog.list_products'))
        
    except Exception as e:
        session.rollback()
        flash(f'Error al cambiar estado: {str(e)}', 'danger')
        return redirect(url_for('catalog.list_products'))

