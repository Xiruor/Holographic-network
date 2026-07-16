"""
=========================================================
仪表盘模块 — 首页统计概览与图表数据
=========================================================
"""
from flask import Blueprint, jsonify
from db import db

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/summary', methods=['GET'])
def get_summary():
    """
    获取仪表盘概览数据
    返回: {
      "code": 200,
      "data": {
        "device_count": ...,        # 设备总数
        "online_count": ...,        # 在线设备数
        "alert_count": ...,         # 未处理告警数
        "today_alert_count": ...,   # 今日新增告警数
        "cpu_trend": [...],         # CPU趋势图数据
        "network_trend": [...],     # 流量趋势图数据
        "device_type_dist": [...],  # 设备类型分布
        "recent_alerts": [...]      # 最近告警列表
      }
    }
    """
    # 设备统计
    device_stats = db.select_one("""
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN status = '在线' THEN 1 ELSE 0 END) AS online,
            SUM(CASE WHEN status = '告警' THEN 1 ELSE 0 END) AS warning
        FROM devices
    """)

    # 告警统计
    alert_stats = db.select_one("""
        SELECT
            COUNT(*) AS pending,
            SUM(CASE WHEN DATE(occurred_at) = CURDATE() THEN 1 ELSE 0 END) AS today
        FROM alerts WHERE status = '未处理'
    """)

    # 设备类型分布
    device_types = db.select_all("""
        SELECT device_type AS name, COUNT(*) AS value
        FROM devices GROUP BY device_type ORDER BY value DESC
    """)

    # CPU 趋势（最近7天核心路由器-02的数据）
    cpu_trend = db.select_all("""
        SELECT DATE_FORMAT(timestamp, '%%Y-%%m-%%d %%H:%%i') AS time, cpu_usage
        FROM device_metrics
        WHERE device_id = 2 AND timestamp >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        ORDER BY timestamp ASC LIMIT 20
    """)

    # 网络流量趋势
    network_trend = db.select_all("""
        SELECT DATE_FORMAT(timestamp, '%%Y-%%m-%%d %%H:%%i') AS time,
               network_in, network_out
        FROM device_metrics
        WHERE device_id = 2 AND timestamp >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        ORDER BY timestamp ASC LIMIT 20
    """)

    # 最近告警
    recent_alerts = db.select_all("""
        SELECT a.alert_id, a.alert_type AS alertType,
               a.level, a.status, a.occurred_at AS `time`,
               d.name AS deviceName
        FROM alerts a
        JOIN devices d ON a.device_id = d.id
        ORDER BY a.occurred_at DESC LIMIT 10
    """)

    return jsonify({
        'code': 200,
        'data': {
            'device_count': device_stats['total'] if device_stats else 0,
            'online_count': device_stats['online'] if device_stats else 0,
            'alert_count': alert_stats['pending'] if alert_stats else 0,
            'today_alert_count': alert_stats['today'] if alert_stats else 0,
            'cpu_trend': cpu_trend or [],
            'network_trend': network_trend or [],
            'device_type_dist': device_types or [],
            'recent_alerts': recent_alerts or []
        }
    })
