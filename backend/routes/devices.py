"""
=========================================================
设备管理模块 — CRUD + 筛选 + 分页 + 设备详情
=========================================================
"""
from flask import Blueprint, request, jsonify
from db import db
from .auth import login_required
import pymysql

devices_bp = Blueprint('devices', __name__)


@devices_bp.route('', methods=['GET'])
def get_devices():
    """
    获取设备列表（支持筛选和分页）
    查询参数:
      keyword    - 搜索设备名称/IP
      device_type - 设备类型
      status     - 设备状态
      page       - 页码（默认1）
      page_size  - 每页条数（默认10）
    """
    keyword = request.args.get('keyword', '').strip()
    device_type = request.args.get('device_type', '')
    status = request.args.get('status', '')
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 10))

    # 动态拼接 WHERE 条件
    conditions = []
    params = []

    if keyword:
        conditions.append("(d.name LIKE %s OR d.ip_address LIKE %s)")
        params.extend([f'%{keyword}%', f'%{keyword}%'])
    if device_type:
        conditions.append("d.device_type = %s")
        params.append(device_type)
    if status:
        conditions.append("d.status = %s")
        params.append(status)

    where = "WHERE " + " AND ".join(conditions) if conditions else ""

    # 从 device_metrics 取最新 CPU/内存，没有记录则返回 0
    sql = f"""
        SELECT d.id, d.name, d.device_type AS type, d.ip_address AS ip,
               d.port, d.status, d.location,
               COALESCE((
                   SELECT m.cpu_usage FROM device_metrics m
                   WHERE m.device_id = d.id
                   ORDER BY m.timestamp DESC LIMIT 1
               ), 0) AS cpuUsage,
               COALESCE((
                   SELECT m.memory_usage FROM device_metrics m
                   WHERE m.device_id = d.id
                   ORDER BY m.timestamp DESC LIMIT 1
               ), 0) AS memUsage
        FROM devices d {where} ORDER BY d.id ASC
    """

    result = db.select_page(sql, params, page, page_size)

    return jsonify({
        'code': 200,
        'data': result
    })


@devices_bp.route('/<int:device_id>', methods=['GET'])
def get_device(device_id):
    """
    获取设备详情（含关联告警）
    """
    device = db.select_one("""
        SELECT id, name, device_type AS type, ip_address AS ip,
               port, status, location,
               COALESCE((
                   SELECT m.cpu_usage FROM device_metrics m
                   WHERE m.device_id = %s
                   ORDER BY m.timestamp DESC LIMIT 1
               ), 0) AS cpuUsage,
               COALESCE((
                   SELECT m.memory_usage FROM device_metrics m
                   WHERE m.device_id = %s
                   ORDER BY m.timestamp DESC LIMIT 1
               ), 0) AS memUsage
        FROM devices WHERE id = %s
    """, (device_id, device_id, device_id))

    if not device:
        return jsonify({'code': 404, 'message': '设备不存在'}), 404

    # 关联告警
    related_alerts = db.select_all("""
        SELECT alert_id, alert_type AS alertType, level, status,
               occurred_at AS `time`
        FROM alerts WHERE device_id = %s ORDER BY occurred_at DESC LIMIT 10
    """, (device_id,))

    device['related_alerts'] = related_alerts or []

    return jsonify({'code': 200, 'data': device})


@devices_bp.route('', methods=['POST'])
def create_device():
    """
    添加设备
    请求: { "name": "...", "type": "...", "ip": "...", "port": 22, "status": "..." }
    """
    payload, err = login_required()
    if err:
        return err

    data = request.get_json() or {}
    name = data.get('name', '').strip()
    if not name:
        return jsonify({'code': 400, 'message': '设备名称不能为空'}), 400

    try:
        device_id = db.insert("""
            INSERT INTO devices (name, device_type, ip_address, port, status, cpu_usage, memory_usage, location)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            name,
            data.get('type', '路由器'),
            data.get('ip', ''),
            data.get('port', 22),
            data.get('status', '在线'),
            data.get('cpuUsage', 0),
            data.get('memUsage', 0),
            data.get('location', '')
        ))
    except pymysql.err.IntegrityError as e:
        err_msg = str(e)
        if 'uk_name' in err_msg:
            return jsonify({'code': 400, 'message': f'设备名称 "{name}" 已存在'}), 400
        if 'uk_ip' in err_msg:
            return jsonify({'code': 400, 'message': f'IP 地址 "{data.get("ip", "")}" 已被其他设备使用'}), 400
        return jsonify({'code': 400, 'message': '添加设备失败，数据冲突'}), 400

    return jsonify({'code': 200, 'message': '添加成功', 'data': {'id': device_id}})


@devices_bp.route('/<int:device_id>', methods=['PUT'])
def update_device(device_id):
    """
    编辑设备
    请求: { "name": "...", "type": "...", "ip": "...", ... }
    """
    payload, err = login_required()
    if err:
        return err

    data = request.get_json() or {}
    try:
        db.update("""
            UPDATE devices SET name=%s, device_type=%s, ip_address=%s,
                   port=%s, status=%s, cpu_usage=%s, memory_usage=%s, location=%s
            WHERE id=%s
        """, (
            data.get('name'),
            data.get('type'),
            data.get('ip'),
            data.get('port', 22),
            data.get('status'),
            data.get('cpuUsage', 0),
            data.get('memUsage', 0),
            data.get('location', ''),
            device_id
        ))
    except pymysql.err.IntegrityError as e:
        err_msg = str(e)
        if 'uk_name' in err_msg:
            return jsonify({'code': 400, 'message': f'设备名称 "{data.get("name")}" 已存在'}), 400
        if 'uk_ip' in err_msg:
            return jsonify({'code': 400, 'message': f'IP 地址 "{data.get("ip")}" 已被其他设备使用'}), 400
        return jsonify({'code': 400, 'message': '更新失败，数据冲突'}), 400

    return jsonify({'code': 200, 'message': '更新成功'})


@devices_bp.route('/<int:device_id>', methods=['DELETE'])
def delete_device(device_id):
    """删除设备"""
    payload, err = login_required()
    if err:
        return err

    db.delete("DELETE FROM devices WHERE id = %s", (device_id,))
    return jsonify({'code': 200, 'message': '删除成功'})
