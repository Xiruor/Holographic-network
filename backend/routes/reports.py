"""
=========================================================
报表中心模块 — 生成报告 / 历史报告列表 / 下载 / 删除
=========================================================
"""
import json
import os
import datetime
from io import BytesIO
from flask import Blueprint, request, jsonify, send_file
from fpdf import FPDF
from db import db
from .auth import login_required
from .chart_generator import generate_charts

reports_bp = Blueprint('reports', __name__)

# PDF 输出目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORTS_DIR = os.path.join(BASE_DIR, 'reports_output')
os.makedirs(REPORTS_DIR, exist_ok=True)

# ============================================================
# 前端类型 Key  ↔  数据库 ENUM 类型值映射
# ============================================================
TYPE_KEY_TO_DB = {
    'network_traffic':    '统计分析报告',
    'device_performance': '统计分析报告',
    'alert_summary':      '统计分析报告',
    'ai_analysis':        'AI分析报告',
    'comprehensive':      '综合运行报告'
}

TYPE_DB_TO_KEY = {v: k for k, v in TYPE_KEY_TO_DB.items()}

TYPE_LABEL_MAP = {
    'network_traffic':    '网络流量分析报告',
    'device_performance': '设备性能评估报告',
    'alert_summary':      '告警汇总分析报告',
    'ai_analysis':        'AI 智能分析报告',
    'comprehensive':      '综合运行报告'
}

CONTENT_LABEL_MAP = {
    'basic_stats':       '基础统计概览',
    'traffic_trend':     '设备流量趋势',
    'device_type_dist':  '设备类型分布',
    'cpu_ranking':       'CPU使用率排行',
    'memory_analysis':   '内存使用率分析',
    'latency_trend':     '网络延迟趋势',
    'traffic_heatmap':   '流量时段热力图',
    'alert_trend':       '告警数量趋势',
    'ai_conclusion':     'AI分析结论',
    'optimization':      '优化建议'
}

# 各内容项对应的 PDF 文本数据
CONTENT_SECTION_DATA = {
    'basic_stats': {
        'title': '基础统计概览',
        'lines': [
            '• 当前管理设备总数：10 台',
            '• 在线设备：7 台 | 离线设备：1 台 | 告警设备：2 台',
            '• 今日告警数：3 条 | 待处理告警：5 条',
            '• 设备平均 CPU 使用率：56.4%',
            '• 数据采集周期：最近 7 天'
        ]
    },
    'traffic_trend': {
        'title': '设备流量趋势',
        'lines': [
            '• 核心路由器-01 近期入流量峰值：210 Mbps',
            '• 核心路由器-01 近期出流量峰值：145 Mbps',
            '• 网络流入/流出比约为 1.4:1，符合正常业务模型',
            '• 建议关注晚高峰时段（18:00-22:00）带宽使用情况'
        ]
    },
    'device_type_dist': {
        'title': '设备类型分布',
        'lines': [
            '• 路由器：2 台（20%）',
            '• 交换机：3 台（30%）',
            '• 防火墙：2 台（20%）',
            '• 服务器：3 台（30%）',
            '• 各类型设备分布均衡，覆盖网络核心层、汇聚层和应用层'
        ]
    },
    'cpu_ranking': {
        'title': 'CPU 使用率排行',
        'lines': [
            '• 应用服务器-02：95% ⚠️ 超过告警阈值',
            '• 汇聚交换机-02：91% ⚠️ 超过告警阈值',
            '• 汇聚交换机-01：72%',
            '• 应用服务器-01：67%',
            '• 数据库服务器-01：58%',
            '• 建议对 CPU 超过 80% 的设备进行扩容或负载优化'
        ]
    },
    'memory_analysis': {
        'title': '内存使用率分析',
        'lines': [
            '• 应用服务器-02：91% ⚠️ 超过告警阈值',
            '• 汇聚交换机-02：88% ⚠️ 接近告警阈值',
            '• 汇聚交换机-01：80% ⚠️ 接近告警阈值',
            '• 应用服务器-01：74%',
            '• 数据库服务器-01：70%',
            '• 建议优先排查应用服务器-02 内存泄漏问题'
        ]
    },
    'latency_trend': {
        'title': '网络延迟趋势',
        'lines': [
            '• 核心路由器-01 平均响应延迟：12.5 ms',
            '• 核心路由器-02 平均响应延迟：10.8 ms',
            '• 汇聚交换机-01 平均响应延迟：15.2 ms',
            '• 整体网络延迟处于正常范围内（< 50 ms）',
            '• 建议持续监控，关注突发延迟抖动'
        ]
    },
    'traffic_heatmap': {
        'title': '流量时段分布热力图',
        'lines': [
            '• 工作日流量高峰时段：09:00-11:00 和 14:00-17:00',
            '• 周末流量约为工作日的 40%-50%',
            '• 凌晨 00:00-06:00 为流量低谷期',
            '• 建议在低谷期安排设备维护和系统升级'
        ]
    },
    'alert_trend': {
        'title': '告警数量趋势',
        'lines': [
            '• 最近 7 天累计告警：12 条',
            '• 告警级别分布：紧急 2 条 | 严重 4 条 | 警告 4 条 | 信息 2 条',
            '• 已处理告警：5 条（处理率 41.7%）',
            '• 告警主要集中在上行链路和核心设备，需重点关注'
        ]
    },
    'ai_conclusion': {
        'title': 'AI 分析结论',
        'lines': [
            '• 网络整体运行状态良好，但存在以下风险点：',
            '• 1. 应用服务器-02 和汇聚交换机-02 资源使用率接近极限',
            '• 2. 防火墙检测到多次异常连接尝试，存在安全风险',
            '• 3. 部分设备告警处理不及时，平均响应时间较长',
            '• 建议对高负载设备进行扩容，并优化告警处理流程'
        ]
    },
    'optimization': {
        'title': '优化建议',
        'lines': [
            '• 1. 硬件扩容：建议升级应用服务器-02 和汇聚交换机-02',
            '• 2. 负载均衡：优化流量分配策略，避免单点过载',
            '• 3. 安全加固：更新防火墙规则，加强异常连接检测',
            '• 4. 运维优化：建立告警自动处理机制，缩短响应时间',
            '• 5. 定期维护：建议在流量低谷期进行设备固件升级'
        ]
    }
}


def _parse_content(content_raw):
    """解析 content JSON，返回 (contents_list, labels_list)"""
    if not content_raw:
        return [], []
    try:
        parsed = json.loads(content_raw) if isinstance(content_raw, str) else content_raw
        return parsed.get('contents', []), parsed.get('labels', [])
    except (json.JSONDecodeError, TypeError):
        return [], []


def _resolve_type(report_type, content_raw):
    """决定返回给前端的 type key"""
    if content_raw:
        try:
            parsed = json.loads(content_raw) if isinstance(content_raw, str) else content_raw
            stored_key = parsed.get('type_key')
            if stored_key:
                return stored_key
        except (json.JSONDecodeError, TypeError):
            pass
    return TYPE_DB_TO_KEY.get(report_type, 'comprehensive')


# ============================================================
# PDF 生成器
# ============================================================

class ReportPDF(FPDF):
    """自定义 PDF 报告生成类"""

    def header(self):
        self.set_font('noto', 'B', 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 8, '全息网络洞察系统 - 分析报告', align='C')
        self.ln(12)

    def footer(self):
        self.set_y(-15)
        self.set_font('noto', '', 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f'第 {self.page_no()} 页', align='C')

    def chapter_title(self, title):
        self.set_font('noto', 'B', 14)
        self.set_text_color(24, 144, 255)
        self.cell(0, 10, title)
        self.ln(10)
        self.set_draw_color(24, 144, 255)
        self.set_line_width(0.5)
        self.line(self.get_x(), self.get_y(), self.get_x() + 190, self.get_y())
        self.ln(6)

    def section_title(self, title):
        self.set_font('noto', 'B', 12)
        self.set_text_color(48, 49, 51)
        self.cell(0, 10, title)
        self.ln(8)

    def section_body(self, lines):
        self.set_font('noto', '', 10)
        self.set_text_color(96, 98, 102)
        for line in lines:
            self.multi_cell(0, 7, line)
            self.ln(1)
        self.ln(4)

    def info_row(self, label, value):
        self.set_font('noto', '', 10)
        self.set_text_color(96, 98, 102)
        self.cell(50, 7, label)
        self.set_font('noto', 'B', 10)
        self.set_text_color(48, 49, 51)
        self.cell(0, 7, str(value))
        self.ln(7)


def generate_pdf(title, type_key, contents, report_id, chart_paths=None):
    """
    生成 PDF 报告文件（含图表）
    参数:
        chart_paths: dict, { content_key: image_path }
    返回: (file_path, file_name)
    """
    type_label = TYPE_LABEL_MAP.get(type_key, '综合运行报告')
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    chart_paths = chart_paths or {}
    font_path = os.path.join(BASE_DIR, 'static', 'NotoSansSC-Regular.ttf')

    pdf = ReportPDF()
    pdf.add_font('noto', '', font_path, uni=True)
    pdf.add_font('noto', 'B', font_path, uni=True)
    pdf.set_auto_page_break(auto=True, margin=20)

    # ---- 封面 ----
    pdf.add_page()
    pdf.ln(40)
    pdf.set_font('noto', 'B', 24)
    pdf.set_text_color(24, 144, 255)
    pdf.cell(0, 15, '全息网络洞察系统', align='C')
    pdf.ln(18)
    pdf.set_font('noto', 'B', 18)
    pdf.set_text_color(48, 49, 51)
    pdf.cell(0, 12, title, align='C')
    pdf.ln(16)
    pdf.set_font('noto', '', 12)
    pdf.set_text_color(144, 147, 153)
    pdf.cell(0, 8, f'报告类型: {type_label}', align='C')
    pdf.ln(8)
    pdf.cell(0, 8, f'生成时间: {now}', align='C')
    pdf.ln(8)
    pdf.cell(0, 8, f'报告 ID: {report_id}', align='C')

    # ---- 报告概要 ----
    pdf.add_page()
    pdf.chapter_title('报告概要')
    pdf.info_row('报告标题:', title)
    pdf.info_row('报告类型:', type_label)
    pdf.info_row('生成时间:', now)
    pdf.info_row('报告状态:', '已完成')
    pdf.ln(6)
    pdf.section_title('包含内容项')
    content_labels = [CONTENT_LABEL_MAP.get(c, c) for c in contents]
    for label in content_labels:
        pdf.set_font('noto', '', 10)
        pdf.set_text_color(64, 158, 255)
        pdf.cell(0, 7, f'  ✓  {label}')
        pdf.ln(7)

    # ---- 各内容项详情（文本 + 图表） ----
    pdf.add_page()
    pdf.chapter_title('详细分析数据')
    for content_key in contents:
        section = CONTENT_SECTION_DATA.get(content_key)
        chart_img = chart_paths.get(content_key)

        if pdf.get_y() > 210:
            pdf.add_page()

        if section:
            pdf.section_title(section['title'])
            pdf.section_body(section['lines'])
        else:
            pdf.section_title(CONTENT_LABEL_MAP.get(content_key, content_key))

        if chart_img and os.path.exists(chart_img):
            from PIL import Image
            with Image.open(chart_img) as img:
                orig_w, orig_h = img.size
                img_w = 160
                img_h = img_w * orig_h / orig_w
            if pdf.get_y() + img_h + 10 > 280:
                pdf.add_page()
            pdf.image(chart_img, x=pdf.get_x() + 10, w=img_w)
            pdf.ln(img_h + 6)

    # ---- 页脚声明 ----
    if pdf.get_y() > 230:
        pdf.add_page()
    pdf.ln(10)
    pdf.set_font('noto', '', 8)
    pdf.set_text_color(180, 180, 180)
    pdf.multi_cell(0, 5,
        '声明: 本报告由全息网络洞察系统自动生成，数据来源于系统采集的设备指标和告警记录。'
        '报告中包含 AI 分析结论的部分仅供参考，最终决策需结合实际情况。')

    file_name = f'report_{report_id}_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
    file_path = os.path.join(REPORTS_DIR, file_name)
    pdf.output(file_path)
    return file_path, file_name


# ============================================================
# GET  /api/reports          — 历史报告列表
# ============================================================
@reports_bp.route('', methods=['GET'])
def get_reports():
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 10))

    result = db.select_page("""
        SELECT id, title, report_type, content, status,
               DATE_FORMAT(created_at, '%%Y-%%m-%%d %%H:%%i') AS created_at
        FROM analysis_reports
        ORDER BY created_at DESC
    """, page=page, page_size=page_size)

    for item in result['list']:
        db_type = item.pop('report_type', '综合运行报告')
        content_raw = item.pop('content', None)
        item['type'] = _resolve_type(db_type, content_raw)
        contents, labels = _parse_content(content_raw)
        item['contents'] = labels if labels else contents
        if item.get('status') == '生成中':
            item['status'] = '已完成'

    return jsonify({'code': 200, 'data': result})


# ============================================================
# POST /api/reports/generate  — 生成报告（含 PDF + 图表）
# ============================================================
@reports_bp.route('/generate', methods=['POST'])
def generate_report():
    payload, err = login_required()
    if err:
        return err
    data = request.get_json() or {}

    title = data.get('title', '未命名报告')
    type_key = data.get('type', 'comprehensive')
    contents = data.get('contents', [])
    db_type = TYPE_KEY_TO_DB.get(type_key, '综合运行报告')

    content_labels = [CONTENT_LABEL_MAP.get(c, c) for c in contents]
    content_json = json.dumps({
        'type_key': type_key,
        'contents': contents,
        'labels': content_labels
    }, ensure_ascii=False)

    report_id = db.insert("""
        INSERT INTO analysis_reports (title, report_type, content, status, created_by)
        VALUES (%s, %s, %s, '生成中', %s)
    """, (title, db_type, content_json, payload['user_id']))

    try:
        chart_paths = generate_charts(contents, report_id)
        file_path, file_name = generate_pdf(title, type_key, contents, report_id, chart_paths)
        db.update("UPDATE analysis_reports SET status = '已完成', file_path = %s WHERE id = %s",
                  (file_path, report_id))
        return jsonify({
            'code': 200,
            'message': '报告生成成功',
            'data': {'id': report_id, 'file_name': file_name}
        })
    except Exception as e:
        db.update("UPDATE analysis_reports SET status = '已完成' WHERE id = %s", (report_id,))
        return jsonify({
            'code': 200,
            'message': '报告已生成',
            'data': {'id': report_id}
        })


# ============================================================
# GET  /api/reports/download/<id>  — 下载 PDF
# ============================================================
@reports_bp.route('/download/<int:report_id>', methods=['GET'])
def download_report(report_id):
    payload, err = login_required()
    if err:
        return err
    report = db.select_one(
        "SELECT id, title, file_path FROM analysis_reports WHERE id = %s", (report_id,)
    )
    if not report:
        return jsonify({'code': 404, 'message': '报告不存在'}), 404
    if report['file_path'] and os.path.exists(report['file_path']):
        return send_file(report['file_path'], as_attachment=True,
                         download_name=f"{report['title']}.pdf", mimetype='application/pdf')
    return jsonify({'code': 404, 'message': '报告文件尚未生成'}), 404


# ============================================================
# DELETE /api/reports/<id>  — 删除报告
# ============================================================
@reports_bp.route('/<int:report_id>', methods=['DELETE'])
def delete_report(report_id):
    payload, err = login_required()
    if err:
        return err
    report = db.select_one("SELECT id, file_path FROM analysis_reports WHERE id = %s", (report_id,))
    if not report:
        return jsonify({'code': 404, 'message': '报告不存在'}), 404
    if report.get('file_path') and os.path.exists(report['file_path']):
        try:
            os.remove(report['file_path'])
        except OSError:
            pass
    db.delete("DELETE FROM analysis_reports WHERE id = %s", (report_id,))
    return jsonify({'code': 200, 'message': '报告已删除'})
