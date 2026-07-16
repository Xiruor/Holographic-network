"""
=========================================================
全息网络洞察系统 — Flask 后端入口
注册蓝图、配置 CORS、启动服务
=========================================================
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
from config import Config
from routes import *

app = Flask(__name__)
app.config.from_object(Config)

# ===================== 解决跨域 =====================
# 允许前端开发服务器 (5173/5174) 访问
# 生产环境请限制具体域名 (origins=["https://your-domain.com"])
CORS(app,
     origins=["http://localhost:5173", "http://localhost:5174",
              "http://127.0.0.1:5173", "http://127.0.0.1:5174"],
     supports_credentials=True)

# ===================== 注册蓝图 =====================
# 所有接口前缀为 /api

# 认证 (登录/注册/登出)
app.register_blueprint(auth_bp, url_prefix='/api/auth')

# 仪表盘
app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')

# 设备管理
app.register_blueprint(devices_bp, url_prefix='/api/devices')

# 告警中心
app.register_blueprint(alerts_bp, url_prefix='/api/alerts')

# 设备指标
app.register_blueprint(metrics_bp, url_prefix='/api/metrics')

# 数据上传
app.register_blueprint(upload_bp, url_prefix='/api/data')

# 数据分析
app.register_blueprint(analysis_bp, url_prefix='/api/analysis')

# AI 分析
app.register_blueprint(ai_analysis_bp, url_prefix='/api/analysis/ai')

# 可视化看板
app.register_blueprint(visualization_bp, url_prefix='/api/visualization')

# 报表中心
app.register_blueprint(reports_bp, url_prefix='/api/reports')

# 系统管理
app.register_blueprint(admin_bp, url_prefix='/api/admin')


# ===================== 根路径 =====================
@app.route('/')
def index():
    """后端根路径，提示用户访问前端或 API 文档"""
    return {
        'code': 200,
        'message': '全息网络洞察系统后端服务运行中',
        'frontend': 'http://localhost:5174',
        'api_docs': {
            'health': '/api/health',
            'login': '/api/auth/login',
            'dashboard': '/api/dashboard/summary',
            'devices': '/api/devices',
            'alerts': '/api/alerts'
        }
    }


# ===================== 健康检查 =====================
@app.route('/api/health')
def health_check():
    """后端健康检查接口"""
    return {'code': 200, 'message': 'ok'}


# ===================== 全局 CORS 头 =====================
# 确保所有响应（包括错误响应）都带有 CORS 头
# 避免浏览器因 500 等错误缺少 CORS 头而报跨域错误
ALLOWED_ORIGINS = [
    'http://localhost:5173', 'http://localhost:5174',
    'http://127.0.0.1:5173', 'http://127.0.0.1:5174'
]

def _set_cors(response, origin):
    """给 response 添加 CORS 头（公用函数）"""
    if origin in ALLOWED_ORIGINS:
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    return response

@app.after_request
def add_cors_headers(response):
    origin = request.headers.get('Origin', '')
    return _set_cors(response, origin)


# ===================== 全局 404 / 500 处理 =====================
# 处理因蓝图未注册等原因导致的 404，确保仍返回 JSON
# 同时手动添加 CORS 头，因为 errorhandler 的返回值不经过 after_request
@app.errorhandler(404)
def not_found(e):
    origin = request.headers.get('Origin', '')
    resp = jsonify({'code': 404, 'message': '接口不存在，请检查路径是否正确'})
    resp.status_code = 404
    return _set_cors(resp, origin)


@app.errorhandler(500)
def internal_error(e):
    origin = request.headers.get('Origin', '')
    app.logger.error(f'服务器内部错误: {e}')
    resp = jsonify({'code': 500, 'message': '服务器内部错误'})
    resp.status_code = 500
    return _set_cors(resp, origin)


# ===================== 启动入口 =====================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=Config.DEBUG, use_reloader=False)
