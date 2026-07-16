"""
=========================================================
可视化看板模块 — ECharts 图表数据
所有数据均从数据库实时查询，支持日期范围和设备筛选
=========================================================
"""
from flask import Blueprint, jsonify, request
from db import db

visualization_bp = Blueprint('visualization', __name__)


@visualization_bp.route('/data', methods=['GET'])
def get_visualization_data():
    """
    获取可视化看板全部图表数据
    查询参数:
      - start_date: 开始日期 (YYYY-MM-DD), 可选
      - end_date:   结束日期 (YYYY-MM-DD), 可选
      - device_name: 设备名称 (传 '全部' 或留空表示所有设备), 可选
    返回: { "code": 200, "data": { ... } }
    """
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    device_name = request.args.get('device_name')

    # 构建时间筛选条件
    time_conditions = []
    time_params = []
    if start_date:
        time_conditions.append('m.timestamp >= %s')
        time_params.append(start_date)
    if end_date:
        time_conditions.append('m.timestamp <= %s + INTERVAL 1 DAY')
        time_params.append(end_date)
    time_clause = ' AND ' + ' AND '.join(time_conditions) if time_conditions else ''

    # 构建设备筛选条件（heatmap 和 line 用 m.device_id 关联）
    device_join = ''
    device_condition = ''
    device_id_val = None
    if device_name and device_name != '全部':
        # 查找设备 ID
        dev = db.select_one("SELECT id FROM devices WHERE name = %s", (device_name,))
        if dev:
            device_id_val = dev['id']
            device_condition = ' AND m.device_id = %s'
            device_join = ' AND d.id = %s'
        else:
            device_condition = ' AND 1=0'   # 设备不存在，返回空
            device_join = ' AND 1=0'

    hours = list(range(24))
    days = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']

    # ============================================
    # 1. 流量时段分布热力图
    # ============================================
    heat_sql = """
        SELECT
            WEEKDAY(m.timestamp) AS day_idx,
            HOUR(m.timestamp)   AS hour,
            AVG(m.network_in + m.network_out) AS traffic
        FROM device_metrics m
        WHERE m.network_in IS NOT NULL
    """
    heat_params = []
    if start_date:
        heat_sql += ' AND m.timestamp >= %s'
        heat_params.append(start_date)
    if end_date:
        heat_sql += ' AND m.timestamp <= %s + INTERVAL 1 DAY'
        heat_params.append(end_date)
    if device_id_val is not None:
        heat_sql += ' AND m.device_id = %s'
        heat_params.append(device_id_val)
    heat_sql += ' GROUP BY WEEKDAY(m.timestamp), HOUR(m.timestamp)'

    heatmap_rows = db.select_all(heat_sql, heat_params) or []

    heat_index = {(r['day_idx'], r['hour']): float(r['traffic']) for r in heatmap_rows}
    heatmap_data = []
    for day_idx in range(7):
        for hour in hours:
            val = heat_index.get((day_idx, hour))
            if val is None:
                val = 0.1
            heatmap_data.append([hour, day_idx, round(val, 1)])

    # ============================================
    # 2. CPU 使用率排行（横向柱状图）
    # 与设备管理页面保持一致：取 device_metrics 最新一条 cpu_usage
    # ============================================
    cpu_sql = """
        SELECT d.name,
               COALESCE((
                   SELECT m.cpu_usage FROM device_metrics m
                   WHERE m.device_id = d.id AND m.cpu_usage IS NOT NULL
                   ORDER BY m.timestamp DESC LIMIT 1
               ), 0) AS cpu
        FROM devices d
        WHERE d.name IS NOT NULL
        ORDER BY cpu DESC
    """
    cpu_rows = db.select_all(cpu_sql) or []
    cpu_ranking = [
        {'name': r['name'], 'cpu': float(r['cpu'])}
        for r in cpu_rows
    ]

    # ============================================
    # 3. 网络延迟趋势（折线图）
    # ============================================
    line_sql = """
        SELECT
            d.name,
            HOUR(m.timestamp) AS hour,
            AVG(m.response_time) AS avg_response
        FROM device_metrics m
        JOIN devices d ON m.device_id = d.id
        WHERE m.response_time IS NOT NULL
    """
    line_params = []
    if start_date:
        line_sql += ' AND m.timestamp >= %s'
        line_params.append(start_date)
    if end_date:
        line_sql += ' AND m.timestamp <= %s + INTERVAL 1 DAY'
        line_params.append(end_date)
    if device_id_val is not None:
        line_sql += ' AND m.device_id = %s'
        line_params.append(device_id_val)
    line_sql += ' GROUP BY d.name, HOUR(m.timestamp) ORDER BY d.name, hour'

    latency_rows = db.select_all(line_sql, line_params) or []

    # 按设备名分组，补全 24 小时
    device_hour_map = {}
    device_order = []
    for r in latency_rows:
        name = r['name']
        if name not in device_hour_map:
            device_hour_map[name] = {}
            device_order.append(name)
        device_hour_map[name][r['hour']] = float(r['avg_response'])

    cpu_trend = []
    for name in device_order:
        data_24 = []
        for h in hours:
            val = device_hour_map[name].get(h)
            if val is not None:
                data_24.append(round(val, 1))
            else:
                prev_vals = [device_hour_map[name].get(ph) for ph in range(h)
                             if device_hour_map[name].get(ph) is not None]
                data_24.append(round(prev_vals[-1], 1) if prev_vals else 0)
        cpu_trend.append({'name': name, 'data': data_24})

    # ============================================
    # 4. 告警数量趋势（柱状图）
    # ============================================
    trend_sql = """
        SELECT DATE(occurred_at) AS dt, COUNT(*) AS count
        FROM alerts
        WHERE 1=1
    """
    trend_params = []
    if start_date:
        trend_sql += ' AND occurred_at >= %s'
        trend_params.append(start_date)
    if end_date:
        trend_sql += ' AND occurred_at <= %s + INTERVAL 1 DAY'
        trend_params.append(end_date)
    trend_sql += ' GROUP BY DATE(occurred_at) ORDER BY dt'

    trend_rows = db.select_all(trend_sql, trend_params) or []
    alert_trend = [
        {'date': str(r['dt']), 'count': r['count']}
        for r in trend_rows
    ]

    return jsonify({
        'code': 200,
        'data': {
            'heatmap': {
                'data': heatmap_data,
                'hours': hours,
                'days': days
            },
            'cpu_ranking': cpu_ranking,
            'cpu_trend': cpu_trend,
            'alert_trend': alert_trend
        }
    })
