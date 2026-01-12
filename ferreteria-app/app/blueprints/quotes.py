"""Quotes blueprint for presupuesto management."""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_file, current_app
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import or_, func
from app.database import get_session
from app.models import Quote, QuoteLine, Product
from app.services.quote_service import (
    create_quote_from_cart,
    generate_quote_pdf_from_db,
    convert_quote_to_sale
)

quotes_bp = Blueprint('quotes', __name__, url_prefix='/quotes')


def get_cart():
    """Get cart from session."""
    if 'cart' not in session:
        session['cart'] = {'items': {}}
    return session['cart']


@quotes_bp.route('/')
def list_quotes():
    """List all quotes with filters."""
    db_session = get_session()
    
    try:
        # Get query params
        status_filter = request.args.get('status', '').upper()
        search = request.args.get('q', '').strip()
        
        # Build query
        query = db_session.query(Quote)
        
        # Filter by status
        if status_filter and status_filter in ['DRAFT', 'SENT', 'ACCEPTED', 'CANCELED']:
            query = query.filter(Quote.status == status_filter)
        
        # MEJORA 14: Search by quote_number, customer_name, or customer_phone
        if search:
            query = query.filter(
                or_(
                    Quote.quote_number.ilike(f'%{search}%'),
                    Quote.customer_name.ilike(f'%{search}%'),
                    Quote.customer_phone.ilike(f'%{search}%')
                )
            )
        
        # Order by most recent first
        quotes = query.order_by(Quote.issued_at.desc()).all()
        
        # Calculate "expired" status for display
        today = date.today()
        for quote in quotes:
            if quote.status in ['DRAFT', 'SENT'] and quote.valid_until and today > quote.valid_until:
                quote.display_expired = True
            else:
                quote.display_expired = False
        
        return render_template(
            'quotes/list.html',
            quotes=quotes,
            status_filter=status_filter,
            search=search
        )
        
    except Exception as e:
        flash(f'Error al cargar presupuestos: {str(e)}', 'danger')
        return render_template('quotes/list.html', quotes=[], status_filter='', search='')


@quotes_bp.route('/<int:quote_id>')
def view_quote(quote_id):
    """View quote detail."""
    db_session = get_session()
    
    try:
        quote = db_session.query(Quote).filter_by(id=quote_id).first()
        
        if not quote:
            flash('Presupuesto no encontrado.', 'danger')
            return redirect(url_for('quotes.list_quotes'))
        
        return render_template('quotes/detail.html', quote=quote)
        
    except Exception as e:
        flash(f'Error al cargar presupuesto: {str(e)}', 'danger')
        return redirect(url_for('quotes.list_quotes'))


@quotes_bp.route('/from-cart', methods=['POST'])
def create_from_cart():
    """Create a new quote from current cart."""
    db_session = get_session()
    
    try:
        cart = get_cart()
        
        # Validate cart not empty
        if not cart.get('items'):
            flash('El carrito está vacío. Agregue productos para crear un presupuesto.', 'warning')
            return redirect(url_for('sales.new_sale'))
        
        # MEJORA 14: Get customer data from form
        customer_name = request.form.get('customer_name', '').strip()
        customer_phone = request.form.get('customer_phone', '').strip() or None
        
        # Validate customer_name
        if not customer_name:
            flash('El nombre del cliente es obligatorio para crear un presupuesto.', 'danger')
            return redirect(url_for('sales.new_sale'))
        
        # Get payment method from form (optional, from MEJORA 12)
        payment_method = request.form.get('payment_method', '').upper()
        if payment_method not in ['CASH', 'TRANSFER', '']:
            payment_method = None
        
        # Get notes (optional)
        notes = request.form.get('notes', '').strip() or None
        
        # Get valid_days from config
        valid_days = current_app.config.get('QUOTE_VALID_DAYS', 7)
        
        # Create quote with customer data (MEJORA 14)
        quote_id = create_quote_from_cart(
            cart=cart,
            session=db_session,
            customer_name=customer_name,
            customer_phone=customer_phone,
            payment_method=payment_method,
            notes=notes,
            valid_days=valid_days
        )
        
        # Clear cart
        session['cart'] = {'items': {}}
        session.modified = True
        
        flash(f'Presupuesto creado exitosamente.', 'success')
        return redirect(url_for('quotes.view_quote', quote_id=quote_id))
        
    except ValueError as e:
        flash(str(e), 'danger')
        return redirect(url_for('sales.new_sale'))
        
    except Exception as e:
        flash(f'Error al crear presupuesto: {str(e)}', 'danger')
        return redirect(url_for('sales.new_sale'))


@quotes_bp.route('/<int:quote_id>/pdf')
def download_pdf(quote_id):
    """Generate and download PDF for a quote."""
    db_session = get_session()
    
    try:
        # Verify quote exists
        quote = db_session.query(Quote).filter_by(id=quote_id).first()
        
        if not quote:
            flash('Presupuesto no encontrado.', 'danger')
            return redirect(url_for('quotes.list_quotes'))
        
        # Business info from config
        business_info = {
            'name': current_app.config.get('BUSINESS_NAME', 'Ferretería'),
            'address': current_app.config.get('BUSINESS_ADDRESS', ''),
            'phone': current_app.config.get('BUSINESS_PHONE', ''),
            'email': current_app.config.get('BUSINESS_EMAIL', ''),
            'valid_days': current_app.config.get('QUOTE_VALID_DAYS', 7)
        }
        
        # Generate PDF
        pdf_buffer = generate_quote_pdf_from_db(quote_id, db_session, business_info)
        
        # Generate filename
        filename = f"presupuesto_{quote.quote_number}.pdf"
        
        # Return PDF as download
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        flash(f'Error al generar PDF: {str(e)}', 'danger')
        return redirect(url_for('quotes.view_quote', quote_id=quote_id))


@quotes_bp.route('/<int:quote_id>/convert', methods=['POST'])
def convert_to_sale(quote_id):
    """Convert quote to sale."""
    db_session = get_session()
    
    try:
        # Convert quote to sale
        sale_id = convert_quote_to_sale(quote_id, db_session)
        
        flash(
            f'Presupuesto convertido a venta #{sale_id} exitosamente. '
            f'Stock descontado y registro financiero creado.',
            'success'
        )
        return redirect(url_for('quotes.view_quote', quote_id=quote_id))
        
    except ValueError as e:
        flash(str(e), 'danger')
        return redirect(url_for('quotes.view_quote', quote_id=quote_id))
        
    except Exception as e:
        flash(f'Error al convertir presupuesto: {str(e)}', 'danger')
        return redirect(url_for('quotes.view_quote', quote_id=quote_id))


@quotes_bp.route('/<int:quote_id>/cancel', methods=['POST'])
def cancel_quote(quote_id):
    """Cancel a quote."""
    db_session = get_session()
    
    try:
        quote = db_session.query(Quote).filter_by(id=quote_id).first()
        
        if not quote:
            flash('Presupuesto no encontrado.', 'danger')
            return redirect(url_for('quotes.list_quotes'))
        
        # Validate can be canceled
        if quote.status not in ['DRAFT', 'SENT']:
            flash(
                f'No se puede cancelar un presupuesto en estado {quote.status}.',
                'danger'
            )
            return redirect(url_for('quotes.view_quote', quote_id=quote_id))
        
        # Cancel quote
        quote.status = 'CANCELED'
        db_session.commit()
        
        flash('Presupuesto cancelado exitosamente.', 'success')
        return redirect(url_for('quotes.view_quote', quote_id=quote_id))
        
    except Exception as e:
        db_session.rollback()
        flash(f'Error al cancelar presupuesto: {str(e)}', 'danger')
        return redirect(url_for('quotes.view_quote', quote_id=quote_id))


@quotes_bp.route('/<int:quote_id>/send', methods=['POST'])
def mark_as_sent(quote_id):
    """Mark quote as sent."""
    db_session = get_session()
    
    try:
        quote = db_session.query(Quote).filter_by(id=quote_id).first()
        
        if not quote:
            flash('Presupuesto no encontrado.', 'danger')
            return redirect(url_for('quotes.list_quotes'))
        
        # Validate can be marked as sent
        if quote.status != 'DRAFT':
            flash(
                f'Solo presupuestos en estado DRAFT pueden marcarse como enviados.',
                'warning'
            )
            return redirect(url_for('quotes.view_quote', quote_id=quote_id))
        
        # Mark as sent
        quote.status = 'SENT'
        db_session.commit()
        
        flash('Presupuesto marcado como enviado.', 'success')
        return redirect(url_for('quotes.view_quote', quote_id=quote_id))
        
    except Exception as e:
        db_session.rollback()
        flash(f'Error al actualizar presupuesto: {str(e)}', 'danger')
        return redirect(url_for('quotes.view_quote', quote_id=quote_id))
