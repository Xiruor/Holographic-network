"""
路由模块，使用相对导入避免包名冲突
在 app.py 中统一注册
"""
from .auth import auth_bp
from .dashboard import dashboard_bp
from .devices import devices_bp
from .alerts import alerts_bp
from .metrics import metrics_bp
from .upload import upload_bp
from .analysis import analysis_bp
from .ai_analysis import ai_analysis_bp
from .visualization import visualization_bp
from .reports import reports_bp
from .admin import admin_bp

__all__ = [
    'auth_bp', 'dashboard_bp', 'devices_bp', 'alerts_bp',
    'metrics_bp', 'upload_bp', 'analysis_bp', 'ai_analysis_bp',
    'visualization_bp', 'reports_bp', 'admin_bp'
]
