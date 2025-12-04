import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from flask_cors import CORS

from config import Config
from database import init_db
from routes import auth_bp, data_bp, ai_bp, projection_bp, notion_bp, history_bp, drill_bp, upload_bp, metrics_bp


def create_app():
    """Application factory for Flask app."""
    app = Flask(__name__)

    # Load configuration
    app.config.from_object(Config)

    # Enable CORS for React frontend
    CORS(app, origins=[
        'http://localhost:5173',
        'http://127.0.0.1:5173',
        'http://localhost:5174',
        'http://127.0.0.1:5174',
        'https://buzzradar-cfo-app.onrender.com'
    ], supports_credentials=True)

    # Configure session cookies for cross-domain
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'None'

    # Initialize database
    init_db(app)

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(data_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(projection_bp)
    app.register_blueprint(notion_bp)
    app.register_blueprint(history_bp)
    app.register_blueprint(drill_bp)
    app.register_blueprint(upload_bp)
    app.register_blueprint(metrics_bp)

    # Health check endpoint
    @app.route('/health')
    def health():
        return {'status': 'healthy'}

    return app


if __name__ == '__main__':
    app = create_app()

    # Validate configuration on startup
    try:
        Config.validate()
    except ValueError as e:
        print(f"Configuration error: {e}")
        print("Please copy .env.example to .env and fill in your Xero credentials")
        sys.exit(1)

    app.run(debug=True, host='0.0.0.0', port=5002)
