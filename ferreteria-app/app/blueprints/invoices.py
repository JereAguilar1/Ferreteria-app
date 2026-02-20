"""Invoices blueprint for purchase invoice management."""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from decimal import Decimal
import decimal
from datetime import datetime, date, timedelta
import calendar
from sqlalchemy import and_
from app.database import get_session
from app.models import PurchaseInvoice, Supplier, Product, InvoiceStatus, PurchaseInvoicePayment
from sqlalchemy import func
from app.services.invoice_service import create_invoice_with_lines, update_invoice_with_lines, delete_invoice
from app.services.payment_service import pay_invoice, add_invoice_payment, get_invoice_balance
from app.services.invoice_alerts_service import is_invoice_overdue
from app.utils.number_format import parse_ar_decimal, parse_ar_number

invoices_bp = Blueprint('invoices', __name__, url_prefix='/invoices')


def add_months(sourcedate, months):
    """Add months to a date, handling month wrap and end of month."""
    month = sourcedate.month - 1 + months
    year = sourcedate.year + month // 12
    month = month % 12 + 1
    day = min(sourcedate.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def get_invoice_draft():
    """Get invoice draft from session."""
    if 'invoice_draft' not in session:
        session['invoice_draft'] = {
            'supplier_id': None,
            'invoice_number': '',
            'invoice_date': '',
            'due_date': '',
            'lines': []  # List of {product_id, qty, unit_cost, vat_rate}
        }
    return session['invoice_draft']


def save_invoice_draft(draft):
    """Save invoice draft to session."""
    session['invoice_draft'] = draft
    session.modified = True


def clear_invoice_draft():
    """Clear invoice draft from session."""
    session['invoice_draft'] = {
        'supplier_id': None,
        'invoice_number': '',
        'invoice_date': '',
        'due_date': '',
        'lines': []
    }
    session.modified = True


@invoices_bp.route('/')
def list_invoices():
    """List all purchase invoices, ordered by due date."""
    db_session = get_session()
    
    try:
        # Optional filters
        supplier_id = request.args.get('supplier_id', type=int)
        status = request.args.get('status', '').upper()
        search_query = request.args.get('q', '').strip()
        due_soon = request.args.get('due_soon', type=int)  # MEJORA 21
        overdue = request.args.get('overdue', type=int)  # MEJORA 21
        
        query = db_session.query(PurchaseInvoice)
        
        if supplier_id:
            query = query.filter(PurchaseInvoice.supplier_id == supplier_id)
        
        if status and status in ['PENDING', 'PAID']:
            query = query.filter(PurchaseInvoice.status == InvoiceStatus[status])
        
        # MEJORA 21: Filter by due soon (tomorrow)
        if due_soon:
            tomorrow = date.today() + timedelta(days=1)
            query = query.filter(
                and_(
                    PurchaseInvoice.status == InvoiceStatus.PENDING,
                    PurchaseInvoice.due_date == tomorrow
                )
            )
        
        # MEJORA 21: Filter by overdue
        if overdue:
            today = date.today()
            query = query.filter(
                and_(
                    PurchaseInvoice.status == InvoiceStatus.PENDING,
                    PurchaseInvoice.due_date < today,
                    PurchaseInvoice.due_date.isnot(None)
                )
            )
        
        # Search by invoice number
        if search_query:
            query = query.filter(PurchaseInvoice.invoice_number.ilike(f'%{search_query}%'))
        
        # MEJORA 21: Order by due_date (ascending, NULLS LAST), then by created_at (descending)
        invoices = query.order_by(
            PurchaseInvoice.due_date.asc().nullslast(),
            PurchaseInvoice.created_at.desc()
        ).all()
        
        # MEJORA 21: Calculate "overdue" status for each invoice
        # MEJORA B: Calculate balance (total_paid, balance) for each invoice
        from app.utils.formatters import get_now_ar
        today = get_now_ar().date()
        for invoice in invoices:
            invoice.is_overdue = is_invoice_overdue(invoice, today)
            
            # Use unified balance service
            balance_info = get_invoice_balance(invoice.id, db_session)
            invoice.total_paid = balance_info['total_paid']
            invoice.balance = balance_info['balance']
        
        # Get suppliers for filter
        suppliers = db_session.query(Supplier).order_by(Supplier.name).all()
        
        # Check if HTMX request (live search)
        is_htmx = request.headers.get('HX-Request') == 'true'
        template = 'invoices/_list_table.html' if is_htmx else 'invoices/list.html'
        
        return render_template(template,
                             invoices=invoices,
                             suppliers=suppliers,
                             selected_supplier=supplier_id,
                             selected_status=status,
                             search_query=search_query,
                             due_soon=due_soon,
                             overdue=overdue)
        
    except Exception as e:
        flash(f'Error al cargar boletas: {str(e)}', 'danger')
        
        is_htmx = request.headers.get('HX-Request') == 'true'
        template = 'invoices/_list_table.html' if is_htmx else 'invoices/list.html'
        
        return render_template(template,
                             invoices=[],
                             suppliers=[],
                             selected_supplier=None,
                             selected_status='',
                             search_query='',
                             due_soon=None,
                             overdue=None)


@invoices_bp.route('/<int:invoice_id>')
def view_invoice(invoice_id):
    """View invoice detail."""
    db_session = get_session()
    
    try:
        invoice = db_session.query(PurchaseInvoice).filter_by(id=invoice_id).first()
        
        if not invoice:
            flash('Boleta no encontrada', 'danger')
            return redirect(url_for('invoices.list_invoices'))
        
        # MEJORA 21: Calculate overdue status
        from app.utils.formatters import get_now_ar
        today_date = get_now_ar().date()
        invoice.is_overdue = is_invoice_overdue(invoice, today_date)
        
        # MEJORA B: Calculate balance (total - sum of payments)
        balance_info = get_invoice_balance(invoice_id, db_session)
        
        # Pass today's date for payment form default
        today = today_date.strftime('%Y-%m-%d')
        
        return render_template('invoices/detail.html', 
                             invoice=invoice, 
                             today=today,
                             balance_info=balance_info)
        
    except Exception as e:
        # Log the full traceback for debugging
        import traceback
        current_app.logger.error(f"Error loading invoice {invoice_id}: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        
        flash(f'Error al cargar boleta: {str(e)}', 'danger')
        return redirect(url_for('invoices.list_invoices'))


@invoices_bp.route('/<int:invoice_id>/add-payment', methods=['POST'])
def add_payment(invoice_id):
    """
    Add a partial payment to an invoice (MEJORA B).
    
    Allows paying an invoice in multiple installments.
    """
    db_session = get_session()
    
    try:
        # Get form data
        paid_at_str = request.form.get('paid_at', '').strip()
        amount_str = request.form.get('amount', '').strip()
        notes = request.form.get('notes', '').strip() or None
        payment_method = request.form.get('payment_method', 'CASH').strip()
        
        # Validate required fields
        if not paid_at_str:
            flash('La fecha de pago es obligatoria', 'danger')
            return redirect(url_for('invoices.view_invoice', invoice_id=invoice_id))
        
        if not amount_str:
            flash('El monto del pago es obligatorio', 'danger')
            return redirect(url_for('invoices.view_invoice', invoice_id=invoice_id))
        
        # Parse date
        try:
            paid_at = datetime.strptime(paid_at_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Fecha de pago inválida', 'danger')
            return redirect(url_for('invoices.view_invoice', invoice_id=invoice_id))
        
        # Parse amount
        try:
            amount = Decimal(amount_str.replace(',', '.'))
            if amount <= 0:
                flash('El monto debe ser mayor a 0', 'danger')
                return redirect(url_for('invoices.view_invoice', invoice_id=invoice_id))
        except (ValueError, TypeError):
            flash('Monto inválido', 'danger')
            return redirect(url_for('invoices.view_invoice', invoice_id=invoice_id))
        
        # Add payment
        add_invoice_payment(
            invoice_id=invoice_id,
            paid_at=paid_at,
            amount=amount,
            session=db_session,
            notes=notes,
            payment_method=payment_method
        )
        
        # Get updated balance
        balance_info = get_invoice_balance(invoice_id, db_session)
        
        if balance_info['is_fully_paid']:
            flash(f'Pago de ${amount} registrado exitosamente. Boleta pagada completamente.', 'success')
        else:
            flash(f'Pago de ${amount} registrado exitosamente. Saldo pendiente: ${balance_info["balance"]}', 'success')
        
        return redirect(url_for('invoices.view_invoice', invoice_id=invoice_id))
        
    except ValueError as e:
        flash(str(e), 'danger')
        return redirect(url_for('invoices.view_invoice', invoice_id=invoice_id))
        
    except Exception as e:
        import traceback
        current_app.logger.error(f"Error adding payment to invoice {invoice_id}: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        flash(f'Error al registrar pago: {str(e)}', 'danger')
        return redirect(url_for('invoices.view_invoice', invoice_id=invoice_id))


@invoices_bp.route('/<int:invoice_id>/update-due-date', methods=['POST'])
def update_due_date(invoice_id):
    """
    Update the due date of an invoice (MEJORA B).
    
    This allows changing the payment deadline without affecting payments or ledger.
    """
    db_session = get_session()
    
    try:
        invoice = db_session.query(PurchaseInvoice).filter_by(id=invoice_id).first()
        
        if not invoice:
            flash('Boleta no encontrada', 'danger')
            return redirect(url_for('invoices.list_invoices'))
        
        # Get new due date
        due_date_str = request.form.get('due_date', '').strip()
        
        if due_date_str:
            try:
                new_due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
                
                # Validate: due_date should be >= invoice_date
                if new_due_date < invoice.invoice_date:
                    flash('La fecha de vencimiento no puede ser anterior a la fecha de la boleta', 'warning')
                    return redirect(url_for('invoices.view_invoice', invoice_id=invoice_id))
                
                invoice.due_date = new_due_date
                db_session.commit()
                
                flash(f'Fecha de vencimiento actualizada a {new_due_date.strftime("%d/%m/%Y")}', 'success')
                
            except ValueError:
                flash('Fecha de vencimiento inválida', 'danger')
        else:
            # Allow clearing due_date
            invoice.due_date = None
            db_session.commit()
            flash('Fecha de vencimiento eliminada', 'success')
        
        return redirect(url_for('invoices.view_invoice', invoice_id=invoice_id))
        
    except Exception as e:
        db_session.rollback()
        current_app.logger.error(f"Error updating due date for invoice {invoice_id}: {str(e)}")
        flash(f'Error al actualizar vencimiento: {str(e)}', 'danger')
        return redirect(url_for('invoices.view_invoice', invoice_id=invoice_id))


@invoices_bp.route('/new', methods=['GET'])
def new_invoice():
    """Show form to create new invoice."""
    db_session = get_session()
    
    try:
        # Check if suppliers exist
        supplier_count = db_session.query(Supplier).count()
        if supplier_count == 0:
            flash('No hay proveedores registrados. Por favor, cree al menos un proveedor primero.', 'warning')
            return redirect(url_for('suppliers.new_supplier'))
        
        # Get suppliers and products
        suppliers = db_session.query(Supplier).order_by(Supplier.name).all()
        products = db_session.query(Product).filter_by(active=True).order_by(Product.name).all()
        
        # Get or initialize draft
        draft = get_invoice_draft()
        
        # MEJORA: Initialize dates if empty (Argentina)
        from app.utils.formatters import get_now_ar
        today = get_now_ar().date()
        if not draft.get('invoice_date'):
            draft['invoice_date'] = today.strftime('%Y-%m-%d')
        
        if not draft.get('due_date'):
            # Default to +1 month
            draft['due_date'] = add_months(today, 1).strftime('%Y-%m-%d')
            
        save_invoice_draft(draft)
        
        # Calculate totals
        total_amount = Decimal('0.00')
        for line in draft['lines']:
            qty = Decimal(str(line['qty']))
            unit_cost = Decimal(str(line['unit_cost']))
            vat_rate = Decimal(str(line.get('vat_rate', 0)))
            
            net_amount = (qty * unit_cost).quantize(Decimal('0.01'), rounding=decimal.ROUND_HALF_UP)
            
            line_total = (qty * unit_cost * (Decimal('1') + vat_rate / Decimal('100'))).quantize(Decimal('0.01'), rounding=decimal.ROUND_HALF_UP)
            
            total_amount += line_total
        total_amount = total_amount.quantize(Decimal('0.01'), rounding=decimal.ROUND_HALF_UP)
        
        return render_template('invoices/new.html',
                             suppliers=suppliers,
                             products=products,
                             draft=draft,
                             total_amount=total_amount)
        
    except Exception as e:
        flash(f'Error al cargar formulario: {str(e)}', 'danger')
        return redirect(url_for('invoices.list_invoices'))


@invoices_bp.route('/draft/update-header', methods=['POST'])
def update_draft_header():
    """Update invoice draft header (HTMX endpoint)."""
    try:
        draft = get_invoice_draft()
        
        # Update header fields
        draft['supplier_id'] = request.form.get('supplier_id', type=int)
        draft['invoice_number'] = request.form.get('invoice_number', '').strip()
        draft['invoice_date'] = request.form.get('invoice_date', '').strip()
        draft['due_date'] = request.form.get('due_date', '').strip()
        
        save_invoice_draft(draft)
        
        return '', 204  # No content
        
    except Exception as e:
        flash(f'Error al actualizar: {str(e)}', 'danger')
        return '', 500


@invoices_bp.route('/draft/add-line', methods=['POST'])
def add_draft_line():
    """Add line to invoice draft (HTMX endpoint)."""
    db_session = get_session()
    
    try:
        product_id = request.form.get('product_id', type=int)
        qty = request.form.get('qty', type=float, default=1)
        unit_cost_raw = request.form.get('unit_cost', '').strip()
        vat_rate_raw = request.form.get('vat_rate', '0').strip()
        
        try:
            unit_cost_decimal = parse_ar_decimal(unit_cost_raw)
            vat_rate_decimal = Decimal(vat_rate_raw.replace(',', '.'))
        except ValueError as e:
            flash(str(e), 'danger')
            return redirect(url_for('invoices.new_invoice'))
        
        try:
            qty_decimal = Decimal(str(qty))
        except Exception:
            flash('Cantidad inválida.', 'danger')
            return redirect(url_for('invoices.new_invoice'))
        
        # Validations
        if not product_id:
            flash('Debe seleccionar un producto', 'danger')
            return redirect(url_for('invoices.new_invoice'))
        
        if qty_decimal <= 0:
            flash('La cantidad debe ser mayor a 0', 'danger')
            return redirect(url_for('invoices.new_invoice'))
        
        if unit_cost_decimal < 0:
            flash('El costo unitario no puede ser negativo', 'danger')
            return redirect(url_for('invoices.new_invoice'))
        
        # Get product to verify it exists
        product = db_session.query(Product).filter_by(id=product_id).first()
        if not product:
            flash('Producto no encontrado', 'danger')
            return redirect(url_for('invoices.new_invoice'))
        
        # Add line to draft
        draft = get_invoice_draft()
        
        # Check if product already exists in lines
        existing_line = next((line for line in draft['lines'] if line['product_id'] == product_id), None)
        
        if existing_line:
            # Update existing line
            existing_line['qty'] = float(qty_decimal)
            existing_line['unit_cost'] = float(unit_cost_decimal)
        else:
            # Add new line
            draft['lines'].append({
                'product_id': product_id,
                'qty': float(qty_decimal),
                'unit_cost': float(unit_cost_decimal),
                'vat_rate': float(vat_rate_decimal)
            })
        
        save_invoice_draft(draft)
        
        return redirect(url_for('invoices.new_invoice'))
        
    except Exception as e:
        flash(f'Error al agregar línea: {str(e)}', 'danger')
        return redirect(url_for('invoices.new_invoice'))


@invoices_bp.route('/draft/remove-line/<int:product_id>', methods=['POST'])
def remove_draft_line(product_id):
    """Remove line from invoice draft (HTMX endpoint)."""
    try:
        draft = get_invoice_draft()
        
        # Remove line
        draft['lines'] = [line for line in draft['lines'] if line['product_id'] != product_id]
        
        save_invoice_draft(draft)
        
        return redirect(url_for('invoices.new_invoice'))
        
    except Exception as e:
        flash(f'Error al remover línea: {str(e)}', 'danger')
        return redirect(url_for('invoices.new_invoice'))


@invoices_bp.route('/new/confirm-preview', methods=['GET'])
def confirm_create_preview():
    """Preview invoice creation details before confirmation (HTMX modal)."""
    db_session = get_session()
    
    try:
        draft = get_invoice_draft()
        
        # Validate draft has required data
        errors = []
        
        if not draft.get('supplier_id'):
            errors.append('Debe seleccionar un proveedor')
        
        if not draft.get('invoice_number'):
            errors.append('El número de boleta es requerido')
        
        if not draft.get('invoice_date'):
            errors.append('La fecha de boleta es requerida')
        
        if not draft.get('lines'):
            errors.append('Debe agregar al menos un ítem a la boleta')
        
        if errors:
            error_html = '<div class="alert alert-danger"><ul class="mb-0">'
            for error in errors:
                error_html += f'<li>{error}</li>'
            error_html += '</ul></div>'
            return error_html
        
        # Get supplier
        supplier = db_session.query(Supplier).filter_by(id=draft['supplier_id']).first()
        if not supplier:
            return '<div class="alert alert-danger">Proveedor no encontrado.</div>'
        
        # Get products for lines
        products = db_session.query(Product).filter_by(active=True).all()
        product_dict = {p.id: p for p in products}
        
        # Prepare lines with product info
        lines_data = []
        total_amount = Decimal('0.00')
        
        for line in draft['lines']:
            product_id = line['product_id']
            product = product_dict.get(product_id)
            
            if not product:
                continue
            
            qty = Decimal(str(line['qty']))
            unit_cost = Decimal(str(line['unit_cost']))
            vat_rate = Decimal(str(line.get('vat_rate', 0)))
            
            net_amount = (qty * unit_cost).quantize(Decimal('0.01'), rounding=decimal.ROUND_HALF_UP)
            
            line_total = (qty * unit_cost * (Decimal('1') + vat_rate / Decimal('100'))).quantize(Decimal('0.01'), rounding=decimal.ROUND_HALF_UP)
            
            # Derive VAT for preview
            vat_amount = line_total - net_amount
            
            total_amount += line_total
            
            lines_data.append({
                'product': product,
                'qty': qty,
                'unit_cost': unit_cost.quantize(Decimal('0.01'), rounding=decimal.ROUND_HALF_UP),
                'vat_rate': vat_rate,
                'vat_amount': vat_amount,
                'net_amount': net_amount,
                'line_total': line_total
            })
        
        # Parse dates for display
        try:
            invoice_date = datetime.strptime(draft['invoice_date'], '%Y-%m-%d').date()
            if draft.get('due_date'):
                due_date = datetime.strptime(draft['due_date'], '%Y-%m-%d').date()
            else:
                due_date = add_months(invoice_date, 1)
        except ValueError:
            return '<div class="alert alert-danger">Fecha inválida en el draft.</div>'
        
        total_amount = total_amount.quantize(Decimal('0.01'), rounding=decimal.ROUND_HALF_UP)

        return render_template('invoices/_create_confirm_modal.html',
                             supplier=supplier,
                             invoice_number=draft['invoice_number'],
                             invoice_date=invoice_date,
                             due_date=due_date,
                             lines=lines_data,
                             total_amount=total_amount)
        
    except Exception as e:
        current_app.logger.error(f"Error generating create preview: {e}")
        return f'<div class="alert alert-danger">Error al generar vista previa: {str(e)}</div>'


@invoices_bp.route('/create', methods=['POST'])
def create_invoice():
    """Create invoice with lines and update stock."""
    db_session = get_session()
    
    try:
        draft = get_invoice_draft()
        
        # Validate draft has required data
        if not draft['supplier_id']:
            flash('Debe seleccionar un proveedor', 'danger')
            return redirect(url_for('invoices.new_invoice'))
        
        if not draft['invoice_number']:
            flash('El número de boleta es requerido', 'danger')
            return redirect(url_for('invoices.new_invoice'))
        
        if not draft['invoice_date']:
            flash('La fecha de boleta es requerida', 'danger')
            return redirect(url_for('invoices.new_invoice'))
        
        if not draft['lines']:
            flash('Debe agregar al menos un ítem a la boleta', 'danger')
            return redirect(url_for('invoices.new_invoice'))
        
        # Parse dates
        try:
            if draft['invoice_date']:
                invoice_date = datetime.strptime(draft['invoice_date'], '%Y-%m-%d').date()
            else:
                from app.utils.formatters import get_now_ar
                invoice_date = get_now_ar().date()
                
            if draft['due_date']:
                due_date = datetime.strptime(draft['due_date'], '%Y-%m-%d').date()
            else:
                due_date = add_months(invoice_date, 1)
        except ValueError:
            flash('Fecha inválida', 'danger')
            return redirect(url_for('invoices.new_invoice'))
        
        # Prepare payload
        lines_payload = []
        for line in draft['lines']:
            lines_payload.append({
                'product_id': line['product_id'],
                'qty': Decimal(str(line['qty'])),
                'unit_cost': Decimal(str(line['unit_cost'])),
                'vat_rate': Decimal(str(line.get('vat_rate', 0)))
            })

        payload = {
            'supplier_id': draft['supplier_id'],
            'invoice_number': draft['invoice_number'],
            'invoice_date': invoice_date,
            'due_date': due_date,
            'lines': lines_payload
        }
        
        # Call service to create invoice
        invoice_id = create_invoice_with_lines(payload, db_session)
        
        # Clear draft
        clear_invoice_draft()
        
        flash(f'Boleta #{invoice_id} creada exitosamente. Stock actualizado.', 'success')
        return redirect(url_for('invoices.view_invoice', invoice_id=invoice_id))
        
    except ValueError as e:
        # Business logic errors
        flash(str(e), 'danger')
        return redirect(url_for('invoices.new_invoice'))
        
    except Exception as e:
        flash(f'Error al crear boleta: {str(e)}', 'danger')
        return redirect(url_for('invoices.new_invoice'))


@invoices_bp.route('/<int:invoice_id>/pay/preview', methods=['GET'])
def pay_invoice_preview(invoice_id):
    """Preview invoice payment details before confirmation (MEJORA 19 - Modal)."""
    db_session = get_session()
    
    try:
        invoice = db_session.query(PurchaseInvoice).filter_by(id=invoice_id).first()
        
        if not invoice:
            return '<div class="alert alert-danger">Boleta no encontrada.</div>'
        
        if invoice.status != InvoiceStatus.PENDING:
            return f'<div class="alert alert-danger">Solo se pueden pagar boletas PENDING. Estado actual: {invoice.status.value}</div>'
        
        # Calculate balance info
        balance_info = get_invoice_balance(invoice_id, db_session)
        
        # Pass today's date for default (Argentina)
        from app.utils.formatters import get_now_ar
        today = get_now_ar().date().strftime('%Y-%m-%d')
        
        return render_template('invoices/_pay_confirm_modal.html',
                             invoice=invoice,
                             today=today,
                             balance_info=balance_info)
        
    except Exception as e:
        current_app.logger.error(f"Error generating payment preview for invoice {invoice_id}: {e}")
        return f'<div class="alert alert-danger">Error al generar vista previa: {str(e)}</div>'


@invoices_bp.route('/<int:invoice_id>/pay', methods=['POST'])
def pay_invoice_route(invoice_id):
    """Mark invoice as PAID and register EXPENSE in finance_ledger."""
    db_session = get_session()
    
    try:
        # Get paid_at from form
        paid_at_str = request.form.get('paid_at', '').strip()
        payment_method = request.form.get('payment_method', 'CASH').upper()  # MEJORA 12
        
        if not paid_at_str:
            flash('La fecha de pago es requerida', 'danger')
            return redirect(url_for('invoices.view_invoice', invoice_id=invoice_id))
        
        # MEJORA 12: Validate payment method
        if payment_method not in ['CASH', 'TRANSFER']:
            flash('Método de pago inválido.', 'danger')
            return redirect(url_for('invoices.view_invoice', invoice_id=invoice_id))
        
        # Parse date
        try:
            paid_at = datetime.strptime(paid_at_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Formato de fecha inválido', 'danger')
            return redirect(url_for('invoices.view_invoice', invoice_id=invoice_id))
        
        # Call payment service with payment_method (MEJORA 12)
        pay_invoice(invoice_id, paid_at, db_session, payment_method)
        
        payment_label = 'Efectivo' if payment_method == 'CASH' else 'Transferencia'
        flash(f'Boleta #{invoice_id} marcada como pagada ({payment_label}). Egreso registrado en el libro mayor.', 'success')
        return redirect(url_for('invoices.view_invoice', invoice_id=invoice_id))
        
    except ValueError as e:
        # Business logic errors
        flash(str(e), 'danger')
        return redirect(url_for('invoices.view_invoice', invoice_id=invoice_id))
        
    except Exception as e:
        flash(f'Error al procesar pago: {str(e)}', 'danger')
        return redirect(url_for('invoices.view_invoice', invoice_id=invoice_id))


def is_invoice_editable(invoice):
    """Check if an invoice can be edited."""
    if invoice.status != InvoiceStatus.PENDING:
        return False, f'Solo se pueden editar boletas PENDING. Esta boleta está en estado {invoice.status.value}.'
    return True, None


def is_invoice_deletable(invoice):
    """Check if an invoice can be deleted."""
    if invoice.status != InvoiceStatus.PENDING:
        return False, f'Solo se pueden eliminar boletas PENDING. Esta boleta está en estado {invoice.status.value}. Si está PAID, tiene un asiento contable registrado.'
    return True, None


@invoices_bp.route('/<int:invoice_id>/edit', methods=['GET'])
def edit_invoice(invoice_id):
    """Show form to edit an invoice (PENDING only)."""
    db_session = get_session()
    
    try:
        invoice = db_session.query(PurchaseInvoice).filter_by(id=invoice_id).first()
        
        if not invoice:
            flash('Boleta no encontrada.', 'danger')
            return redirect(url_for('invoices.list_invoices'))
        
        # Validate invoice is editable
        can_edit, error_msg = is_invoice_editable(invoice)
        if not can_edit:
            flash(error_msg, 'danger')
            return redirect(url_for('invoices.view_invoice', invoice_id=invoice_id))
        
        # Get all active products for the product selector
        products = db_session.query(Product).filter_by(active=True).order_by(Product.name).all()
        
        # Get all suppliers
        suppliers = db_session.query(Supplier).order_by(Supplier.name).all()
        
        return render_template('invoices/edit.html', 
                             invoice=invoice, 
                             products=products,
                             suppliers=suppliers)
        
    except Exception as e:
        flash(f'Error al cargar formulario de edición: {str(e)}', 'danger')
        return redirect(url_for('invoices.view_invoice', invoice_id=invoice_id))


@invoices_bp.route('/<int:invoice_id>/edit/preview', methods=['POST'])
def edit_invoice_preview(invoice_id):
    """Preview invoice changes before confirmation (HTMX modal)."""
    db_session = get_session()
    
    try:
        invoice = db_session.query(PurchaseInvoice).filter_by(id=invoice_id).first()
        
        if not invoice:
            return '<div class="alert alert-danger">Boleta no encontrada.</div>'
        
        # Validate invoice is editable
        can_edit, error_msg = is_invoice_editable(invoice)
        if not can_edit:
            return f'<div class="alert alert-danger">{error_msg}</div>'
        
        # Parse form data
        supplier_id = request.form.get('supplier_id')
        if not supplier_id:
            return '<div class="alert alert-danger">El proveedor es requerido.</div>'
        
        supplier_id = int(supplier_id)
        supplier = db_session.query(Supplier).filter_by(id=supplier_id).first()
        if not supplier:
            return '<div class="alert alert-danger">Proveedor no encontrado.</div>'
        
        invoice_number = request.form.get('invoice_number', '').strip()
        if not invoice_number:
            return '<div class="alert alert-danger">El número de boleta es requerido.</div>'
        
        invoice_date_str = request.form.get('invoice_date', '').strip()
        if not invoice_date_str:
            return '<div class="alert alert-danger">La fecha de boleta es requerida.</div>'
        
        try:
            invoice_date = datetime.strptime(invoice_date_str, '%Y-%m-%d').date()
        except ValueError:
            return '<div class="alert alert-danger">Fecha de boleta inválida.</div>'
        
        due_date_str = request.form.get('due_date', '').strip()
        due_date = None
        if due_date_str:
            try:
                due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
            except ValueError:
                return '<div class="alert alert-danger">Fecha de vencimiento inválida.</div>'
        
        # Parse lines from form
        lines_data = []
        line_index = 0
        
        while True:
            product_id_key = f'lines[{line_index}][product_id]'
            qty_key = f'lines[{line_index}][qty]'
            unit_cost_key = f'lines[{line_index}][unit_cost]'
            
            if product_id_key not in request.form:
                break
            
            product_id = request.form.get(product_id_key, '').strip()
            qty = request.form.get(qty_key, '').strip()
            unit_cost = request.form.get(unit_cost_key, '').strip()
            
            if not product_id or not qty or not unit_cost:
                line_index += 1
                continue
            
            try:
                product_id_int = int(product_id)
                qty_decimal = parse_ar_number(qty)
                unit_cost_decimal = parse_ar_decimal(unit_cost)
                
                if qty_decimal <= 0:
                    return f'<div class="alert alert-danger">La cantidad debe ser mayor a 0 en la línea {line_index + 1}.</div>'
                
                if unit_cost_decimal < 0:
                    return f'<div class="alert alert-danger">El costo unitario no puede ser negativo en la línea {line_index + 1}.</div>'
                
                # Get product
                product = db_session.query(Product).filter_by(id=product_id_int).first()
                if not product:
                    return f'<div class="alert alert-danger">Producto con ID {product_id_int} no encontrado.</div>'
                
                if not product.active:
                    return f'<div class="alert alert-danger">El producto "{product.name}" está inactivo.</div>'
                
                lines_data.append({
                    'product_id': product_id_int,
                    'qty': qty_decimal,
                    'unit_cost': unit_cost_decimal,
                    'product': product
                })
                
            except (ValueError, TypeError) as e:
                return f'<div class="alert alert-danger">Error en línea {line_index + 1}: {str(e)}</div>'
            
            line_index += 1
        
        if not lines_data:
            return '<div class="alert alert-danger">Debe agregar al menos una línea.</div>'
        
        # Calculate changes
        old_lines_by_product = {line.product_id: line for line in invoice.lines}
        new_lines_by_product = {line['product_id']: line for line in lines_data}
        
        # Calculate old and new totals
        old_total = invoice.total_amount
        new_total = Decimal('0.00')
        
        changes = {
            'added': [],
            'removed': [],
            'modified': [],
            'stock_deltas': []
        }
        
        # Check for removed lines
        for old_line in invoice.lines:
            if old_line.product_id not in new_lines_by_product:
                changes['removed'].append({
                    'product': old_line.product.name,
                    'qty': old_line.qty,
                    'unit_cost': old_line.unit_cost,
                    'line_total': old_line.line_total
                })
                # Stock delta: negative (removing this line removes stock)
                changes['stock_deltas'].append({
                    'product': old_line.product.name,
                    'delta': -old_line.qty,
                    'uom': old_line.product.uom.symbol if old_line.product.uom else ''
                })
        
        # Check for added/modified lines
        for new_line_data in lines_data:
            product_id = new_line_data['product_id']
            new_qty = new_line_data['qty']
            new_unit_cost = new_line_data['unit_cost']
            product = new_line_data['product']
            
            line_total = (new_qty * new_unit_cost).quantize(Decimal('0.01'))
            new_total += line_total
            
            if product_id not in old_lines_by_product:
                # Added line
                changes['added'].append({
                    'product': product.name,
                    'qty': new_qty,
                    'unit_cost': new_unit_cost,
                    'line_total': line_total
                })
                # Stock delta: positive (adding this line adds stock)
                changes['stock_deltas'].append({
                    'product': product.name,
                    'delta': new_qty,
                    'uom': product.uom.symbol if product.uom else ''
                })
            else:
                # Check if modified
                old_line = old_lines_by_product[product_id]
                if old_line.qty != new_qty or old_line.unit_cost != new_unit_cost:
                    changes['modified'].append({
                        'product': product.name,
                        'old_qty': old_line.qty,
                        'new_qty': new_qty,
                        'old_unit_cost': old_line.unit_cost,
                        'new_unit_cost': new_unit_cost,
                        'old_line_total': old_line.line_total,
                        'new_line_total': line_total
                    })
                    # Stock delta: difference in qty
                    delta = new_qty - old_line.qty
                    if delta != 0:
                        changes['stock_deltas'].append({
                            'product': product.name,
                            'delta': delta,
                            'uom': product.uom.symbol if product.uom else ''
                        })
        
        new_total = new_total.quantize(Decimal('0.01'))

        # Check if there are any changes
        has_changes = (
            len(changes['added']) > 0 or
            len(changes['removed']) > 0 or
            len(changes['modified']) > 0 or
            supplier_id != invoice.supplier_id or
            invoice_number != invoice.invoice_number or
            invoice_date != invoice.invoice_date or
            due_date != invoice.due_date or
            old_total != new_total
        )
        
        if not has_changes:
            return '<div class="alert alert-info">No hay cambios para aplicar.</div>'
        
        return render_template('invoices/_edit_confirm_modal.html',
                             invoice=invoice,
                             old_total=old_total,
                             new_total=new_total,
                             changes=changes,
                             supplier=supplier,
                             invoice_number=invoice_number,
                             invoice_date=invoice_date,
                             due_date=due_date)
        
    except Exception as e:
        current_app.logger.error(f"Error generating edit preview for invoice {invoice_id}: {e}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        return f'<div class="alert alert-danger">Error al generar vista previa: {str(e)}</div>'


@invoices_bp.route('/<int:invoice_id>/edit', methods=['POST'])
def save_invoice_edit(invoice_id):
    """Save invoice changes (transactional)."""
    db_session = get_session()
    
    try:
        invoice = db_session.query(PurchaseInvoice).filter_by(id=invoice_id).first()
        
        if not invoice:
            flash('Boleta no encontrada.', 'danger')
            return redirect(url_for('invoices.list_invoices'))
        
        # Validate invoice is editable
        can_edit, error_msg = is_invoice_editable(invoice)
        if not can_edit:
            flash(error_msg, 'danger')
            return redirect(url_for('invoices.view_invoice', invoice_id=invoice_id))
        
        # Parse form data
        supplier_id = request.form.get('supplier_id')
        invoice_number = request.form.get('invoice_number', '').strip()
        invoice_date_str = request.form.get('invoice_date', '').strip()
        due_date_str = request.form.get('due_date', '').strip()
        
        if not supplier_id or not invoice_number or not invoice_date_str:
            flash('Proveedor, número de boleta y fecha son requeridos.', 'danger')
            return redirect(url_for('invoices.edit_invoice', invoice_id=invoice_id))
        
        try:
            invoice_date = datetime.strptime(invoice_date_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Fecha de boleta inválida.', 'danger')
            return redirect(url_for('invoices.edit_invoice', invoice_id=invoice_id))
        
        due_date = None
        if due_date_str:
            try:
                due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Fecha de vencimiento inválida.', 'danger')
                return redirect(url_for('invoices.edit_invoice', invoice_id=invoice_id))
        
        # Parse lines from form
        lines_data = []
        line_index = 0
        
        while True:
            product_id_key = f'lines[{line_index}][product_id]'
            qty_key = f'lines[{line_index}][qty]'
            unit_cost_key = f'lines[{line_index}][unit_cost]'
            
            if product_id_key not in request.form:
                break
            
            product_id = request.form.get(product_id_key, '').strip()
            qty = request.form.get(qty_key, '').strip()
            unit_cost = request.form.get(unit_cost_key, '').strip()
            
            if not product_id or not qty or not unit_cost:
                line_index += 1
                continue
            
            try:
                product_id_int = int(product_id)
                qty_decimal = parse_ar_number(qty)
                unit_cost_decimal = parse_ar_decimal(unit_cost)
                
                if qty_decimal <= 0:
                    flash(f'La cantidad debe ser mayor a 0 en la línea {line_index + 1}.', 'danger')
                    return redirect(url_for('invoices.edit_invoice', invoice_id=invoice_id))
                
                lines_data.append({
                    'product_id': product_id_int,
                    'qty': qty_decimal,
                    'unit_cost': unit_cost_decimal
                })
                
            except (ValueError, TypeError) as e:
                flash(f'Error en línea {line_index + 1}: {str(e)}', 'danger')
                return redirect(url_for('invoices.edit_invoice', invoice_id=invoice_id))
            
            line_index += 1
        
        if not lines_data:
            flash('Debe agregar al menos una línea.', 'danger')
            return redirect(url_for('invoices.edit_invoice', invoice_id=invoice_id))
        
        # Build payload
        payload = {
            'supplier_id': int(supplier_id),
            'invoice_number': invoice_number,
            'invoice_date': invoice_date,
            'due_date': due_date,
            'lines': lines_data
        }
        
        # Call service to update invoice
        update_invoice_with_lines(invoice_id, payload, db_session)
        
        flash('Boleta actualizada exitosamente. El stock se ha ajustado automáticamente.', 'success')
        return redirect(url_for('invoices.view_invoice', invoice_id=invoice_id))
        
    except ValueError as e:
        flash(str(e), 'danger')
        return redirect(url_for('invoices.edit_invoice', invoice_id=invoice_id))
        
    except Exception as e:
        db_session.rollback()
        flash(f'Error al actualizar boleta: {str(e)}', 'danger')
        return redirect(url_for('invoices.edit_invoice', invoice_id=invoice_id))


@invoices_bp.route('/<int:invoice_id>/delete/preview', methods=['GET'])
def delete_invoice_preview(invoice_id):
    """Preview invoice deletion (HTMX modal)."""
    db_session = get_session()
    
    try:
        invoice = db_session.query(PurchaseInvoice).filter_by(id=invoice_id).first()
        
        if not invoice:
            return '<div class="alert alert-danger">Boleta no encontrada.</div>'
        
        # Validate invoice can be deleted
        can_delete, error_msg = is_invoice_deletable(invoice)
        if not can_delete:
            return f'<div class="alert alert-danger">{error_msg}</div>'
        
        return render_template('invoices/_delete_confirm_modal.html', invoice=invoice)
        
    except Exception as e:
        current_app.logger.error(f"Error generating delete preview for invoice {invoice_id}: {e}")
        return f'<div class="alert alert-danger">Error: {str(e)}</div>'


@invoices_bp.route('/<int:invoice_id>/delete', methods=['POST'])
def delete_invoice_route(invoice_id):
    """Delete invoice and revert stock (PENDING only)."""
    db_session = get_session()
    
    try:
        invoice = db_session.query(PurchaseInvoice).filter_by(id=invoice_id).first()
        
        if not invoice:
            flash('Boleta no encontrada.', 'danger')
            return redirect(url_for('invoices.list_invoices'))
        
        # Validate invoice can be deleted
        can_delete, error_msg = is_invoice_deletable(invoice)
        if not can_delete:
            flash(error_msg, 'danger')
            return redirect(url_for('invoices.view_invoice', invoice_id=invoice_id))
        
        # Store invoice_number for flash message
        invoice_number = invoice.invoice_number
        
        # Call service to delete invoice
        delete_invoice(invoice_id, db_session)
        
        flash(f'Boleta #{invoice_number} eliminada exitosamente. El stock se ha revertido automáticamente.', 'success')
        return redirect(url_for('invoices.list_invoices'))
        
    except ValueError as e:
        flash(str(e), 'danger')
        return redirect(url_for('invoices.view_invoice', invoice_id=invoice_id))
        
    except Exception as e:
        db_session.rollback()
        flash(f'Error al eliminar boleta: {str(e)}', 'danger')
        return redirect(url_for('invoices.view_invoice', invoice_id=invoice_id))

