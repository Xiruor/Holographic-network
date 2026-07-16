"""
=========================================================
系统管理模块 — 用户管理 / 操作日志
=========================================================
"""
from flask import Blueprint, request, jsonify
from db import db
from .auth import login_required

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/users', methods=['GET'])
def get_users():
    """
    获取用户列表
    查询参数: page, page_size
    """
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 10))

    result = db.select_page("""
        SELECT id, username, email, role, is_enabled AS isEnabled,
               DATE_FORMAT(register_time, '%%Y-%%m-%%d') AS registerTime,
               COALESCE(DATE_FORMAT(last_login, '%%Y-%%m-%%d %%H:%%i'), '') AS lastLogin
        FROM users ORDER BY register_time DESC
    """, page=page, page_size=page_size)

    return jsonify({'code': 200, 'data': result})


@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """删除用户"""
    payload, err = login_required()
    if err:
        return err

    db.delete("DELETE FROM users WHERE id = %s", (user_id,))
    return jsonify({'code': 200, 'message': '删除成功'})


@admin_bp.route('/logs', methods=['GET'])
def get_logs():
    """
    获取操作日志
    查询参数: page, page_size
    """
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 10))

    result = db.select_page("""
        SELECT o.id, u.username, o.action_type AS actionType,
               o.target_type AS targetType, o.detail,
               o.ip_address AS ipAddress,
               DATE_FORMAT(o.created_at, '%%Y-%%m-%%d %%H:%%i:%%s') AS createTime
        FROM operation_logs o
        JOIN users u ON o.user_id = u.id
        ORDER BY o.created_at DESC
    """, page=page, page_size=page_size)

    return jsonify({'code': 200, 'data': result})
