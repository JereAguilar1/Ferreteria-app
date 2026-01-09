"""Configuration module for Flask application."""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Base configuration class."""
    
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('FLASK_DEBUG', '1') == '1'
    
    # Database - Support multiple environment variable naming conventions
    # Priority: DATABASE_URL > DB_* > POSTGRES_*
    DATABASE_URL = os.getenv('DATABASE_URL')
    
    if not DATABASE_URL:
        # Try DB_* variables (Docker style)
        DB_HOST = os.getenv('DB_HOST') or os.getenv('POSTGRES_HOST', 'localhost')
        DB_PORT = os.getenv('DB_PORT') or os.getenv('POSTGRES_PORT', '5432')
        DB_NAME = os.getenv('DB_NAME') or os.getenv('POSTGRES_DB', 'ferreteria')
        DB_USER = os.getenv('DB_USER') or os.getenv('POSTGRES_USER', 'ferreteria')
        DB_PASSWORD = os.getenv('DB_PASSWORD') or os.getenv('POSTGRES_PASSWORD', 'ferreteria')
        
        DATABASE_URL = (
            f"postgresql://{DB_USER}:{DB_PASSWORD}"
            f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        )
    
    # SQLAlchemy
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = DEBUG

