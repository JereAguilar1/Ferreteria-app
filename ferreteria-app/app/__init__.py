"""Flask application factory."""
from flask import Flask
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
    from app.blueprints.main import main_bp
    from app.blueprints.catalog import catalog_bp
    from app.blueprints.sales import sales_bp
    from app.blueprints.suppliers import suppliers_bp
    from app.blueprints.invoices import invoices_bp
    from app.blueprints.balance import balance_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(catalog_bp)
    app.register_blueprint(sales_bp)
    app.register_blueprint(suppliers_bp)
    app.register_blueprint(invoices_bp)
    app.register_blueprint(balance_bp)
    
    return app

