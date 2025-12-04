from .auth_routes import auth_bp
from .data_routes import data_bp
from .ai_routes import ai_bp
from .projection_routes import projection_bp
from .notion_routes import notion_bp
from .history_routes import history_bp
from .drill_routes import drill_bp
from .upload_routes import upload_bp
from .metrics_routes import metrics_bp

__all__ = ['auth_bp', 'data_bp', 'ai_bp', 'projection_bp', 'notion_bp', 'history_bp', 'drill_bp', 'upload_bp', 'metrics_bp']
