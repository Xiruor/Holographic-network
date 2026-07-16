"""
=========================================================
设备指标模块 — 查询性能指标数据
=========================================================
"""
from flask import Blueprint, request, jsonify
from db import db

metrics_bp = Blueprint('metrics', __name__)


@metrics_bp.route('', methods=['GET'])
def get_metrics():
    """
    查询指标列表（支持设备ID、时间范围筛选、分页）
    查询参数:
      device_id  - 设备ID
      start_date - 开始时间
      end_date   - 结束时间
      page, page_size
    """
    device_id = request.args.get('device_id', type=int)
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 10))

    conditions = []
    params = []

    if device_id:
        conditions.append("device_id = %s")
        params.append(device_id)
    if start_date:
        conditions.append("timestamp >= %s")
        params.append(f"{start_date} 00:00:00")
    if end_date:
        conditions.append("timestamp <= %s")
        params.append(f"{end_date} 23:59:59")

    where = "WHERE " + " AND ".join(conditions) if conditions else ""

    sql = f"""
        SELECT id, device_id AS deviceId,
               DATE_FORMAT(timestamp, '%%Y-%%m-%%d %%H:%%i:%%s') AS timestamp,
               cpu_usage AS cpuUsage, memory_usage AS memUsage,
               network_in AS netIn, network_out AS netOut,
               packet_loss AS lossRate, response_time AS responseTime
        FROM device_metrics {where}
        ORDER BY timestamp DESC
    """

    result = db.select_page(sql, params, page, page_size)

    return jsonify({'code': 200, 'data': result})


@metrics_bp.route('/<int:device_id>', methods=['GET'])
def get_device_metrics(device_id):
    """
    获取指定设备的最近指标数据
    查询参数: limit - 返回条数（默认20）
    """
    limit = int(request.args.get('limit', 20))

    data = db.select_all("""
        SELECT id, DATE_FORMAT(timestamp, '%%Y-%%m-%%d %%H:%%i:%%s') AS timestamp,
               cpu_usage AS cpuUsage, memory_usage AS memUsage,
               network_in AS netIn, network_out AS netOut,
               packet_loss AS lossRate
        FROM device_metrics
        WHERE device_id = %s
        ORDER BY timestamp DESC LIMIT %s
    """, (device_id, limit))

    return jsonify({'code': 200, 'data': data or []})
