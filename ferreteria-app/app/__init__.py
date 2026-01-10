"""Flask application factory."""
from flask import Flask, session, redirect, url_for, request, current_app
from app.database import db, init_db


def create_app(config_object='config.Config'):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_object(config_object)
    
    # Initialize database
    init_db(app)
    
    # Register Jinja filters for date formatting (MEJORA 7)
    from app.utils.formatters import date_ar, datetime_ar, month_ar, year_ar
    app.jinja_env.filters['date_ar'] = date_ar
    app.jinja_env.filters['datetime_ar'] = datetime_ar
    app.jinja_env.filters['month_ar'] = month_ar
    app.jinja_env.filters['year_ar'] = year_ar
    
    # Register blueprints
    from app.blueprints.auth import auth_bp
    from app.blueprints.main import main_bp
    from app.blueprints.catalog import catalog_bp
    from app.blueprints.sales import sales_bp
    from app.blueprints.suppliers import suppliers_bp
    from app.blueprints.invoices import invoices_bp
    from app.blueprints.balance import balance_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(catalog_bp)
    app.register_blueprint(sales_bp)
    app.register_blueprint(suppliers_bp)
    app.register_blueprint(invoices_bp)
    app.register_blueprint(balance_bp)
    
    # MEJORA 8: Password protection middleware
    @app.before_request
    def require_authentication():
        """
        Global middleware to protect all routes with password authentication.
        
        Allows unauthenticated access only to:
        - /login (auth form)
        - /static/* (CSS, JS, images)
        - /health (Docker healthcheck)
        
        All other routes require authentication via session.
        """
        # Get authentication key from config
        auth_key = app.config.get('SESSION_AUTH_KEY', 'authenticated')
        
        # Check if user is authenticated
        is_authenticated = session.get(auth_key, False)
        
        # Define public endpoints that don't require authentication
        public_endpoints = ['auth.login', 'auth.root', 'static']
        
        # Allow /health endpoint without authentication (Docker healthcheck)
        if request.path == '/health':
            return None
        
        # Allow public endpoints
        if request.endpoint in public_endpoints:
            return None
        
        # If not authenticated and trying to access protected route, redirect to login
        if not is_authenticated:
            return redirect(url_for('auth.login'))
        
        # User is authenticated, allow request to proceed
        return None
    
    return app

