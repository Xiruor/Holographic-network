"""
=========================================================
认证模块 — 登录 / 注册 / 登出 / 当前用户
=========================================================
"""
import hashlib
import jwt
import datetime
from flask import Blueprint, request, jsonify
from config import Config
from db import db

auth_bp = Blueprint('auth', __name__)


def _hash_password(password):
    """使用 SHA-256 哈希密码（生产环境建议用 bcrypt）"""
    return hashlib.sha256(password.encode()).hexdigest()


def _generate_token(user_id, username, role):
    """生成 JWT 令牌"""
    payload = {
        'user_id': user_id,
        'username': username,
        'role': role,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=Config.JWT_EXPIRE_HOURS)
    }
    return jwt.encode(payload, Config.JWT_SECRET, algorithm='HS256')


def _decode_token(token):
    """解码 JWT 令牌，返回 payload 或 None"""
    try:
        return jwt.decode(token, Config.JWT_SECRET, algorithms=['HS256'])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


def login_required():
    """
    请求头中提取并验证 Token
    返回值: (user_info_dict, error_response_tuple)
    如果验证通过，user_info_dict 非 None，error_response 为 None
    """
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        return None, (jsonify({'code': 401, 'message': '未提供认证令牌'}), 401)

    payload = _decode_token(token)
    if not payload:
        return None, (jsonify({'code': 401, 'message': '令牌无效或已过期'}), 401)

    return payload, None


# ---------- 接口 ----------

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    用户登录
    请求: { "username": "...", "password": "..." }
    返回: { "code": 200, "message": "ok", "data": { "token": "...", "user": {...} } }
    """
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    if not username or not password:
        return jsonify({'code': 400, 'message': '用户名和密码不能为空'}), 400

    user = db.select_one(
        "SELECT id, username, role, email, is_enabled FROM users WHERE username = %s AND password_hash = %s",
        (username, _hash_password(password))
    )

    if not user:
        return jsonify({'code': 401, 'message': '用户名或密码错误'}), 401

    if not user['is_enabled']:
        return jsonify({'code': 403, 'message': '账户已被禁用'}), 403

    # 更新最后登录时间
    db.update("UPDATE users SET last_login = NOW() WHERE id = %s", (user['id'],))

    # 生成令牌
    token = _generate_token(user['id'], user['username'], user['role'])

    return jsonify({
        'code': 200,
        'message': '登录成功',
        'data': {
            'token': token,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'role': user['role'],
                'email': user.get('email', '')
            }
        }
    })


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    用户注册
    请求: { "username": "...", "password": "...", "email": "...", "role": "..." }
    返回: { "code": 200, "message": "ok" }
    """
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    email = data.get('email', '').strip()
    role = data.get('role', 'viewer')

    if not username or not password:
        return jsonify({'code': 400, 'message': '用户名和密码不能为空'}), 400

    # 检查用户名重复
    exist = db.select_one("SELECT id FROM users WHERE username = %s", (username,))
    if exist:
        return jsonify({'code': 409, 'message': '用户名已存在'}), 409

    db.insert(
        "INSERT INTO users (username, password_hash, email, role) VALUES (%s, %s, %s, %s)",
        (username, _hash_password(password), email, role)
    )

    return jsonify({'code': 200, 'message': '注册成功'})


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """
    登出（客户端清除 token 即可）
    返回: { "code": 200, "message": "ok" }
    """
    return jsonify({'code': 200, 'message': '已登出'})


@auth_bp.route('/current', methods=['GET'])
def current_user():
    """
    获取当前登录用户信息
    请求头: Authorization: Bearer <token>
    返回: { "code": 200, "data": { "id": ..., "username": ..., "role": ... } }
    """
    payload, err = login_required()
    if err:
        return err

    return jsonify({
        'code': 200,
        'data': {
            'id': payload['user_id'],
            'username': payload['username'],
            'role': payload['role']
        }
    })
