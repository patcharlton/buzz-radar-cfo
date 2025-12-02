import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration."""

    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

    # Database
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///cfo.db')

    # Handle Render's postgres:// URL format (SQLAlchemy 1.4+ requires postgresql://)
    if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Connection pool settings for PostgreSQL
    if DATABASE_URL and DATABASE_URL.startswith('postgresql://'):
        SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_pre_ping': True,  # Test connections before using
            'pool_recycle': 300,    # Recycle connections after 5 minutes
            'pool_size': 5,         # Number of connections to maintain
            'max_overflow': 10,     # Allow up to 10 additional connections
        }
    else:
        SQLALCHEMY_ENGINE_OPTIONS = {}

    # Xero OAuth2
    XERO_CLIENT_ID = os.getenv('XERO_CLIENT_ID')
    XERO_CLIENT_SECRET = os.getenv('XERO_CLIENT_SECRET')
    XERO_REDIRECT_URI = os.getenv('XERO_REDIRECT_URI', 'http://localhost:5000/callback')

    # Xero OAuth2 URLs
    XERO_AUTH_URL = 'https://login.xero.com/identity/connect/authorize'
    XERO_TOKEN_URL = 'https://identity.xero.com/connect/token'

    # Required Xero scopes
    XERO_SCOPES = [
        'offline_access',
        'openid',
        'profile',
        'accounting.transactions.read',
        'accounting.reports.read',
        'accounting.contacts.read',
        'accounting.settings.read',
    ]

    @classmethod
    def validate(cls):
        """Validate required configuration is present."""
        missing = []
        if not cls.XERO_CLIENT_ID:
            missing.append('XERO_CLIENT_ID')
        if not cls.XERO_CLIENT_SECRET:
            missing.append('XERO_CLIENT_SECRET')

        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
