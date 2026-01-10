"""
Authentication blueprint for password protection.
Simple password-based access control for the entire application.
"""

import hmac
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app


auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page with password validation."""
    
    # If already authenticated, redirect to products
    if session.get(current_app.config.get('SESSION_AUTH_KEY', 'authenticated')):
        return redirect(url_for('catalog.list_products'))
    
    if request.method == 'POST':
        password = request.form.get('password', '')
        app_password = current_app.config.get('APP_PASSWORD')
        
        # Validate that APP_PASSWORD is configured
        if not app_password:
            current_app.logger.error('APP_PASSWORD not configured in environment')
            flash('Error de configuración: APP_PASSWORD no está definida. Contacte al administrador.', 'danger')
            return render_template('auth/login.html'), 500
        
        # Use constant-time comparison to prevent timing attacks
        if hmac.compare_digest(password, app_password):
            # Authentication successful
            session[current_app.config.get('SESSION_AUTH_KEY', 'authenticated')] = True
            session.permanent = True  # Keep session across browser restarts
            flash('Acceso concedido. Bienvenido.', 'success')
            return redirect(url_for('catalog.list_products'))
        else:
            # Authentication failed
            flash('Contraseña incorrecta. Intente nuevamente.', 'danger')
            return render_template('auth/login.html'), 401
    
    # GET request - show login form
    return render_template('auth/login.html')


@auth_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    """Logout endpoint - clear session and redirect to login."""
    session.clear()
    flash('Sesión cerrada correctamente.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/')
def root():
    """Root route - redirect based on authentication status."""
    if session.get(current_app.config.get('SESSION_AUTH_KEY', 'authenticated')):
        return redirect(url_for('catalog.list_products'))
    else:
        return redirect(url_for('auth.login'))
