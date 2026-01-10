"""
Settings blueprint for managing master data (UOM and Categories).
MEJORA 9: Allows users to create/edit/delete UOMs and Categories from UI.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from sqlalchemy import func
from app.database import get_session
from app.models import UOM, Category, Product


settings_bp = Blueprint('settings', __name__, url_prefix='/settings')


# ============================================================================
# UOM (Unidades de Medida) Routes
# ============================================================================

@settings_bp.route('/uoms')
def list_uoms():
    """List all UOMs with product count."""
    session = get_session()
    
    # Get all UOMs with product count
    uoms_with_count = session.query(
        UOM,
        func.count(Product.id).label('product_count')
    ).outerjoin(Product, Product.uom_id == UOM.id)\
     .group_by(UOM.id)\
     .order_by(UOM.name)\
     .all()
    
    return render_template('settings/uoms_list.html', uoms_with_count=uoms_with_count)


@settings_bp.route('/uoms/new', methods=['GET', 'POST'])
def new_uom():
    """Create new UOM."""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        symbol = request.form.get('symbol', '').strip()
        
        # Validations
        if not name:
            flash('El nombre es obligatorio.', 'danger')
            return render_template('settings/uoms_form.html', uom=None)
        
        if len(name) > 80:
            flash('El nombre debe tener máximo 80 caracteres.', 'danger')
            return render_template('settings/uoms_form.html', uom=None)
        
        if not symbol:
            flash('El símbolo es obligatorio.', 'danger')
            return render_template('settings/uoms_form.html', uom=None)
        
        if len(symbol) > 16:
            flash('El símbolo debe tener máximo 16 caracteres.', 'danger')
            return render_template('settings/uoms_form.html', uom=None)
        
        session = get_session()
        
        # Check if name already exists (case-insensitive)
        existing_name = session.query(UOM).filter(
            func.lower(UOM.name) == func.lower(name)
        ).first()
        
        if existing_name:
            flash(f'Ya existe una unidad de medida con el nombre "{name}".', 'danger')
            return render_template('settings/uoms_form.html', uom=None)
        
        # Check if symbol already exists (case-insensitive)
        existing_symbol = session.query(UOM).filter(
            func.lower(UOM.symbol) == func.lower(symbol)
        ).first()
        
        if existing_symbol:
            flash(f'Ya existe una unidad de medida con el símbolo "{symbol}".', 'danger')
            return render_template('settings/uoms_form.html', uom=None)
        
        # Create UOM
        try:
            uom = UOM(name=name, symbol=symbol)
            session.add(uom)
            session.commit()
            flash(f'Unidad de medida "{name}" creada exitosamente.', 'success')
            return redirect(url_for('settings.list_uoms'))
        except Exception as e:
            session.rollback()
            flash(f'Error al crear unidad de medida: {str(e)}', 'danger')
            return render_template('settings/uoms_form.html', uom=None)
    
    # GET request
    return render_template('settings/uoms_form.html', uom=None)


@settings_bp.route('/uoms/<int:uom_id>/edit', methods=['GET', 'POST'])
def edit_uom(uom_id):
    """Edit existing UOM."""
    session = get_session()
    uom = session.query(UOM).filter_by(id=uom_id).first()
    
    if not uom:
        flash('Unidad de medida no encontrada.', 'danger')
        return redirect(url_for('settings.list_uoms'))
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        symbol = request.form.get('symbol', '').strip()
        
        # Validations
        if not name:
            flash('El nombre es obligatorio.', 'danger')
            return render_template('settings/uoms_form.html', uom=uom)
        
        if len(name) > 80:
            flash('El nombre debe tener máximo 80 caracteres.', 'danger')
            return render_template('settings/uoms_form.html', uom=uom)
        
        if not symbol:
            flash('El símbolo es obligatorio.', 'danger')
            return render_template('settings/uoms_form.html', uom=uom)
        
        if len(symbol) > 16:
            flash('El símbolo debe tener máximo 16 caracteres.', 'danger')
            return render_template('settings/uoms_form.html', uom=uom)
        
        # Check if name already exists (excluding current UOM)
        existing_name = session.query(UOM).filter(
            func.lower(UOM.name) == func.lower(name),
            UOM.id != uom_id
        ).first()
        
        if existing_name:
            flash(f'Ya existe otra unidad de medida con el nombre "{name}".', 'danger')
            return render_template('settings/uoms_form.html', uom=uom)
        
        # Check if symbol already exists (excluding current UOM)
        existing_symbol = session.query(UOM).filter(
            func.lower(UOM.symbol) == func.lower(symbol),
            UOM.id != uom_id
        ).first()
        
        if existing_symbol:
            flash(f'Ya existe otra unidad de medida con el símbolo "{symbol}".', 'danger')
            return render_template('settings/uoms_form.html', uom=uom)
        
        # Update UOM
        try:
            uom.name = name
            uom.symbol = symbol
            session.commit()
            flash(f'Unidad de medida "{name}" actualizada exitosamente.', 'success')
            return redirect(url_for('settings.list_uoms'))
        except Exception as e:
            session.rollback()
            flash(f'Error al actualizar unidad de medida: {str(e)}', 'danger')
            return render_template('settings/uoms_form.html', uom=uom)
    
    # GET request
    return render_template('settings/uoms_form.html', uom=uom)


@settings_bp.route('/uoms/<int:uom_id>/delete', methods=['POST'])
def delete_uom(uom_id):
    """Delete UOM if not in use."""
    session = get_session()
    uom = session.query(UOM).filter_by(id=uom_id).first()
    
    if not uom:
        flash('Unidad de medida no encontrada.', 'danger')
        return redirect(url_for('settings.list_uoms'))
    
    # Check if UOM is used by any product
    product_count = session.query(func.count(Product.id))\
        .filter(Product.uom_id == uom_id)\
        .scalar()
    
    if product_count > 0:
        flash(
            f'No se puede eliminar la unidad "{uom.name}" porque está asociada a {product_count} producto(s).',
            'danger'
        )
        return redirect(url_for('settings.list_uoms'))
    
    # Delete UOM
    try:
        uom_name = uom.name
        session.delete(uom)
        session.commit()
        flash(f'Unidad de medida "{uom_name}" eliminada exitosamente.', 'success')
    except Exception as e:
        session.rollback()
        flash(f'Error al eliminar unidad de medida: {str(e)}', 'danger')
    
    return redirect(url_for('settings.list_uoms'))


# ============================================================================
# Category Routes
# ============================================================================

@settings_bp.route('/categories')
def list_categories():
    """List all categories with product count."""
    session = get_session()
    
    # Get all categories with product count
    categories_with_count = session.query(
        Category,
        func.count(Product.id).label('product_count')
    ).outerjoin(Product, Product.category_id == Category.id)\
     .group_by(Category.id)\
     .order_by(Category.name)\
     .all()
    
    return render_template('settings/categories_list.html', categories_with_count=categories_with_count)


@settings_bp.route('/categories/new', methods=['GET', 'POST'])
def new_category():
    """Create new category."""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        
        # Validations
        if not name:
            flash('El nombre es obligatorio.', 'danger')
            return render_template('settings/categories_form.html', category=None)
        
        if len(name) > 120:
            flash('El nombre debe tener máximo 120 caracteres.', 'danger')
            return render_template('settings/categories_form.html', category=None)
        
        session = get_session()
        
        # Check if name already exists (case-insensitive)
        existing = session.query(Category).filter(
            func.lower(Category.name) == func.lower(name)
        ).first()
        
        if existing:
            flash(f'Ya existe una categoría con el nombre "{name}".', 'danger')
            return render_template('settings/categories_form.html', category=None)
        
        # Create category
        try:
            category = Category(name=name)
            session.add(category)
            session.commit()
            flash(f'Categoría "{name}" creada exitosamente.', 'success')
            return redirect(url_for('settings.list_categories'))
        except Exception as e:
            session.rollback()
            flash(f'Error al crear categoría: {str(e)}', 'danger')
            return render_template('settings/categories_form.html', category=None)
    
    # GET request
    return render_template('settings/categories_form.html', category=None)


@settings_bp.route('/categories/<int:category_id>/edit', methods=['GET', 'POST'])
def edit_category(category_id):
    """Edit existing category."""
    session = get_session()
    category = session.query(Category).filter_by(id=category_id).first()
    
    if not category:
        flash('Categoría no encontrada.', 'danger')
        return redirect(url_for('settings.list_categories'))
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        
        # Validations
        if not name:
            flash('El nombre es obligatorio.', 'danger')
            return render_template('settings/categories_form.html', category=category)
        
        if len(name) > 120:
            flash('El nombre debe tener máximo 120 caracteres.', 'danger')
            return render_template('settings/categories_form.html', category=category)
        
        # Check if name already exists (excluding current category)
        existing = session.query(Category).filter(
            func.lower(Category.name) == func.lower(name),
            Category.id != category_id
        ).first()
        
        if existing:
            flash(f'Ya existe otra categoría con el nombre "{name}".', 'danger')
            return render_template('settings/categories_form.html', category=category)
        
        # Update category
        try:
            category.name = name
            session.commit()
            flash(f'Categoría "{name}" actualizada exitosamente.', 'success')
            return redirect(url_for('settings.list_categories'))
        except Exception as e:
            session.rollback()
            flash(f'Error al actualizar categoría: {str(e)}', 'danger')
            return render_template('settings/categories_form.html', category=category)
    
    # GET request
    return render_template('settings/categories_form.html', category=category)


@settings_bp.route('/categories/<int:category_id>/delete', methods=['POST'])
def delete_category(category_id):
    """Delete category if not in use."""
    session = get_session()
    category = session.query(Category).filter_by(id=category_id).first()
    
    if not category:
        flash('Categoría no encontrada.', 'danger')
        return redirect(url_for('settings.list_categories'))
    
    # Check if category is used by any product
    product_count = session.query(func.count(Product.id))\
        .filter(Product.category_id == category_id)\
        .scalar()
    
    if product_count > 0:
        flash(
            f'No se puede eliminar la categoría "{category.name}" porque está asociada a {product_count} producto(s).',
            'danger'
        )
        return redirect(url_for('settings.list_categories'))
    
    # Delete category
    try:
        category_name = category.name
        session.delete(category)
        session.commit()
        flash(f'Categoría "{category_name}" eliminada exitosamente.', 'success')
    except Exception as e:
        session.rollback()
        flash(f'Error al eliminar categoría: {str(e)}', 'danger')
    
    return redirect(url_for('settings.list_categories'))
