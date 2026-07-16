"""
=========================================================
数据分析模块 — 统计、趋势、对比、排行
=========================================================
"""
from flask import Blueprint, request, jsonify
from db import db

analysis_bp = Blueprint('analysis', __name__)


def _build_time_filter(table_alias, start_date, end_date):
    """构建时间过滤条件的 (where_clause, params)"""
    conds = []
    params = []
    if start_date:
        conds.append(f"{table_alias}.timestamp >= %s")
        params.append(start_date)
    if end_date:
        conds.append(f"{table_alias}.timestamp <= %s")
        params.append(end_date + ' 23:59:59')
    return conds, params


@analysis_bp.route('/statistics', methods=['GET'])
def get_statistics():
    """
    获取统计数据
    查询参数:
      dimension - 分析维度 (device/time/metric)
      type      - 分析类型 (descriptive/trend/comparison/topn)
      start_date, end_date - 时间范围
    """
    dimension = request.args.get('dimension', 'device')
    analysis_type = request.args.get('type', 'descriptive')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')

    # ---- 总数据量（按时间过滤） ----
    m_conds, m_params = _build_time_filter('m', start_date, end_date)
    m_where = "WHERE " + " AND ".join(m_conds) if m_conds else ""

    if m_conds:
        total_metrics = db.select_one(
            f"SELECT COUNT(*) AS count FROM device_metrics m {m_where}",
            m_params
        )
    else:
        total_metrics = db.select_one("SELECT COUNT(*) AS count FROM device_metrics")

    total_devices = db.select_one("SELECT COUNT(*) AS count FROM devices")

    # ---- 最新值子查询的时间条件 ----
    m2_conds, m2_params = _build_time_filter('m2', start_date, end_date)
    m2_extra = " AND " + " AND ".join(m2_conds) if m2_conds else ""

    # ---- 设备统计（平均值 + 最新值） ----
    # 参数顺序: 4个子查询各需 m2_params, 主查询需 m_params
    device_stats = db.select_all(
        f"""
        SELECT d.name, d.device_type AS type, d.status,
               COALESCE(ROUND(AVG(m.cpu_usage), 1), 0) AS avg_cpu,
               COALESCE(ROUND(AVG(m.memory_usage), 1), 0) AS avg_mem,
               COALESCE(ROUND(AVG(m.network_in), 1), 0) AS avg_net_in,
               COALESCE(ROUND(AVG(m.network_out), 1), 0) AS avg_net_out,
               COALESCE((
                   SELECT m2.cpu_usage FROM device_metrics m2
                   WHERE m2.device_id = d.id{m2_extra}
                   ORDER BY m2.timestamp DESC LIMIT 1
               ), 0) AS cpu_usage,
               COALESCE((
                   SELECT m2.memory_usage FROM device_metrics m2
                   WHERE m2.device_id = d.id{m2_extra}
                   ORDER BY m2.timestamp DESC LIMIT 1
               ), 0) AS memory_usage,
               COALESCE((
                   SELECT m2.network_in FROM device_metrics m2
                   WHERE m2.device_id = d.id{m2_extra}
                   ORDER BY m2.timestamp DESC LIMIT 1
               ), 0) AS net_in,
               COALESCE((
                   SELECT m2.network_out FROM device_metrics m2
                   WHERE m2.device_id = d.id{m2_extra}
                   ORDER BY m2.timestamp DESC LIMIT 1
               ), 0) AS net_out
        FROM devices d
        LEFT JOIN device_metrics m ON d.id = m.device_id
        {m_where}
        GROUP BY d.id
        ORDER BY cpu_usage DESC
        """,
        m2_params * 4 + m_params  # 4个子查询 * m2_params, 最后是主查询的 m_params
    )

    return jsonify({
        'code': 200,
        'data': {
            'total_metrics': total_metrics['count'] if total_metrics else 0,
            'total_devices': total_devices['count'] if total_devices else 0,
            'device_stats': device_stats or []
        }
    })
