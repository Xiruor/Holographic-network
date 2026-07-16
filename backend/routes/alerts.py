"""
=========================================================
告警中心模块 — 告警列表/筛选/详情/处理
=========================================================
"""
from flask import Blueprint, request, jsonify
from db import db
from .auth import login_required

alerts_bp = Blueprint('alerts', __name__)


@alerts_bp.route('', methods=['GET'])
def get_alerts():
    """
    获取告警列表（支持多条件筛选、分页）
    查询参数:
      level      - 告警级别
      status     - 状态
      device     - 关联设备名称
      start_date, end_date - 时间范围
      page, page_size
    返回: 含统计数据（待处理数、今日新增、平均响应时间）
    """
    level = request.args.get('level', '')
    status = request.args.get('status', '')
    device = request.args.get('device', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 10))

    conditions = []
    params = []

    if level and level != '全部':
        conditions.append("a.level = %s")
        params.append(level)
    if status and status != '全部':
        conditions.append("a.status = %s")
        params.append(status)
    if device and device != '全部':
        conditions.append("d.name = %s")
        params.append(device)
    if start_date:
        conditions.append("a.occurred_at >= %s")
        params.append(f"{start_date} 00:00:00")
    if end_date:
        conditions.append("a.occurred_at <= %s")
        params.append(f"{end_date} 23:59:59")

    where = "WHERE " + " AND ".join(conditions) if conditions else ""

    # 统计数据（使用与主查询相同的 WHERE 条件）
    stats_sql = f"""
        SELECT
            SUM(CASE WHEN a.status = '未处理' THEN 1 ELSE 0 END) AS pending,
            SUM(CASE WHEN DATE(a.occurred_at) = CURDATE() THEN 1 ELSE 0 END) AS today
        FROM alerts a
        JOIN devices d ON a.device_id = d.id
        {where}
    """
    stats = db.select_one(stats_sql, params if params else None)

    # 计算平均响应时间（已处理的告警从发生到处理的平均耗时）
    avg_sql = """
        SELECT
            COALESCE(
                CONCAT(
                    ROUND(AVG(TIMESTAMPDIFF(MINUTE, a.occurred_at, a.resolved_at))),
                    'min'
                ),
                '-'
            ) AS avg_time
        FROM alerts a
        WHERE a.status = '已处理' AND a.resolved_at IS NOT NULL
    """
    avg_result = db.select_one(avg_sql)

    # 查询列表
    sql = f"""
        SELECT a.alert_id AS id, d.name AS deviceName,
               a.alert_type AS alertType, a.level, a.status,
               DATE_FORMAT(a.occurred_at, '%%Y-%%m-%%d %%H:%%i:%%s') AS `time`,
               COALESCE(DATE_FORMAT(a.resolved_at, '%%Y-%%m-%%d %%H:%%i:%%s'), '') AS processTime,
               a.message
        FROM alerts a
        JOIN devices d ON a.device_id = d.id
        {where}
        ORDER BY a.occurred_at DESC
    """

    result = db.select_page(sql, params, page, page_size)

    return jsonify({
        'code': 200,
        'data': {
            **result,
            'pending_count': stats['pending'] if stats and stats['pending'] else 0,
            'today_count': stats['today'] if stats and stats['today'] else 0,
            'avg_response_time': avg_result['avg_time'] if avg_result and avg_result['avg_time'] else '-'
        }
    })


@alerts_bp.route('/<alert_id>', methods=['GET'])
def get_alert(alert_id):
    """
    获取告警详情
    URL 参数: alert_id (字符串，如 ALT-20260710-001)
    """
    alert = db.select_one("""
        SELECT a.alert_id AS id, d.name AS deviceName,
               a.alert_type AS alertType, a.level, a.status, a.message,
               DATE_FORMAT(a.occurred_at, '%%Y-%%m-%%d %%H:%%i:%%s') AS `time`,
               COALESCE(DATE_FORMAT(a.resolved_at, '%%Y-%%m-%%d %%H:%%i:%%s'), '') AS processTime,
               a.device_id
        FROM alerts a
        JOIN devices d ON a.device_id = d.id
        WHERE a.alert_id = %s
    """, (alert_id,))

    if not alert:
        return jsonify({'code': 404, 'message': '告警不存在'}), 404

    return jsonify({'code': 200, 'data': alert})


@alerts_bp.route('/<alert_id>', methods=['PUT'])
def process_alert(alert_id):
    """
    处理告警（标记为已处理）
    请求: {} (无需body)
    """
    payload, err = login_required()
    if err:
        return err

    affected = db.update("""
        UPDATE alerts SET status = '已处理', resolved_at = NOW(), resolved_by = %s
        WHERE alert_id = %s AND status = '未处理'
    """, (payload['user_id'], alert_id))

    if affected == 0:
        return jsonify({'code': 200, 'message': '该告警已处理或不存在'})

    return jsonify({'code': 200, 'message': '已标记为已处理'})


@alerts_bp.route('/batch', methods=['POST'])
def batch_process():
    """批量处理告警"""
    payload, err = login_required()
    if err:
        return err

    data = request.get_json() or {}
    ids = data.get('ids', [])

    if not ids:
        return jsonify({'code': 400, 'message': '请选择要处理的告警'}), 400

    placeholders = ','.join(['%s'] * len(ids))
    affected = db.update(f"""
        UPDATE alerts SET status = '已处理', resolved_at = NOW(), resolved_by = %s
        WHERE alert_id IN ({placeholders}) AND status = '未处理'
    """, (payload['user_id'], *ids))

    return jsonify({'code': 200, 'message': f'已处理 {affected} 项'})
