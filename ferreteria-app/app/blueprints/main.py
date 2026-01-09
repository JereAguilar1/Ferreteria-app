"""Main blueprint with health check endpoint."""
from flask import Blueprint, jsonify
from sqlalchemy import text
from app.database import get_session

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Home page."""
    return """
    <html>
        <head>
            <title>Ferretería App</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    max-width: 800px;
                    margin: 50px auto;
                    padding: 20px;
                }
                h1 { color: #2c3e50; }
                .status { 
                    background: #e8f5e9; 
                    padding: 15px; 
                    border-radius: 5px;
                    margin: 20px 0;
                }
                a {
                    color: #3498db;
                    text-decoration: none;
                }
                a:hover {
                    text-decoration: underline;
                }
            </style>
        </head>
        <body>
            <h1>🔧 Sistema de Ferretería</h1>
            <div class="status">
                <p><strong>Estado:</strong> Aplicación funcionando correctamente</p>
                <p><a href="/health">Ver estado de conexión a base de datos →</a></p>
            </div>
            <h2>Módulos disponibles:</h2>
            <ul>
                <li>Productos y Stock (próximamente)</li>
                <li>Ventas (próximamente)</li>
                <li>Compras/Boletas (próximamente)</li>
                <li>Balance (próximamente)</li>
            </ul>
        </body>
    </html>
    """


@main_bp.route('/health')
def health():
    """Health check endpoint that validates database connection."""
    try:
        session = get_session()
        # Execute simple query to test connection
        result = session.execute(text("SELECT 1 as health_check"))
        row = result.fetchone()
        
        if row and row[0] == 1:
            return jsonify({
                'status': 'healthy',
                'database': 'connected',
                'message': 'Database connection successful'
            }), 200
        else:
            return jsonify({
                'status': 'unhealthy',
                'database': 'error',
                'message': 'Unexpected query result'
            }), 500
            
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'database': 'disconnected',
            'error': str(e),
            'message': 'Failed to connect to database'
        }), 500

