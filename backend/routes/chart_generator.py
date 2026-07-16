"""
=========================================================
图表生成器 — 为 PDF 报告生成各类统计图表
=========================================================
"""
import os
import matplotlib
matplotlib.use('Agg')  # 非交互式后端
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np

# 注册中文字体
FONT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'static', 'NotoSansSC-Regular.ttf'
)
FONT_BOLD_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'static', 'NotoSansSC-Bold.ttf'
)

# 如果存在 BOLD 字体，Bold 和 Regular 用同一个 SimHei
FONT_BOLD_PATH = FONT_PATH

FONT_PROP = fm.FontProperties(fname=FONT_PATH)
FONT_BOLD = fm.FontProperties(fname=FONT_BOLD_PATH)

# 图表输出目录
CHARTS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'reports_output', '_charts_tmp'
)
os.makedirs(CHARTS_DIR, exist_ok=True)

# 样式统一
COLOR_BLUE = '#1890FF'
COLOR_CYAN = '#13C2C2'
COLOR_GREEN = '#52C41A'
COLOR_ORANGE = '#FA8C16'
COLOR_RED = '#FF4D4F'
COLOR_PURPLE = '#722ED1'
COLOR_GREY = '#D9D9D9'

COLORS = [COLOR_BLUE, COLOR_CYAN, COLOR_GREEN, COLOR_ORANGE, COLOR_RED, COLOR_PURPLE]


def _cleanup():
    """清理临时图表文件"""
    if os.path.exists(CHARTS_DIR):
        for f in os.listdir(CHARTS_DIR):
            try:
                os.remove(os.path.join(CHARTS_DIR, f))
            except OSError:
                pass


def _save_chart(fig, name, report_id):
    """保存图表为 PNG，返回文件路径"""
    path = os.path.join(CHARTS_DIR, f'report_{report_id}_{name}.png')
    fig.savefig(path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    return path


def chart_basic_stats(report_id):
    """基础统计概览 — 仪表盘关键指标卡片图"""
    fig, ax = plt.subplots(figsize=(7, 2.5))
    ax.axis('off')

    metrics = [
        ('管理设备', '10 台', COLOR_BLUE),
        ('在线设备', '7 台', COLOR_GREEN),
        ('今日告警', '3 条', COLOR_ORANGE),
        ('CPU 平均', '56.4%', COLOR_CYAN),
    ]

    for i, (label, value, color) in enumerate(metrics):
        x = i * 0.25 + 0.03
        # 背景圆角矩形
        rect = plt.Rectangle((x, 0.1), 0.22, 0.8, facecolor=color + '15',
                             edgecolor=color, linewidth=1.5, transform=ax.transAxes,
                             corner_radius=0.02)
        ax.add_patch(rect)
        # 数值
        ax.text(x + 0.11, 0.65, value, ha='center', va='center',
                fontproperties=FONT_BOLD, fontsize=22, color=color, transform=ax.transAxes)
        # 标签
        ax.text(x + 0.11, 0.28, label, ha='center', va='center',
                fontproperties=FONT_PROP, fontsize=10, color='#595959', transform=ax.transAxes)

    return _save_chart(fig, 'basic_stats', report_id)


def chart_traffic_trend(report_id):
    """设备流量趋势 — 折线图"""
    fig, ax = plt.subplots(figsize=(7, 3.5))

    days = ['7/8', '7/9', '7/10', '7/11', '7/12', '7/13', '7/14']
    in_traffic = [180, 210, 195, 175, 205, 190, 165]
    out_traffic = [120, 145, 130, 115, 140, 125, 110]

    x = range(len(days))
    ax.plot(x, in_traffic, 'o-', color=COLOR_BLUE, linewidth=2, markersize=5, label='入流量 (Mbps)')
    ax.plot(x, out_traffic, 's-', color=COLOR_GREEN, linewidth=2, markersize=5, label='出流量 (Mbps)')

    # 填充区域
    ax.fill_between(x, in_traffic, alpha=0.08, color=COLOR_BLUE)
    ax.fill_between(x, out_traffic, alpha=0.08, color=COLOR_GREEN)

    ax.set_xticks(x)
    ax.set_xticklabels(days, fontproperties=FONT_PROP, fontsize=9)
    ax.set_ylabel('流量 (Mbps)', fontproperties=FONT_PROP, fontsize=10)
    ax.legend(prop=FONT_PROP, fontsize=9, framealpha=0.9)
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_ylim(0, 260)

    # 添加峰值标注
    max_idx = in_traffic.index(max(in_traffic))
    ax.annotate(f'峰值 {max(in_traffic)} Mbps', xy=(max_idx, in_traffic[max_idx]),
                xytext=(max_idx + 0.3, in_traffic[max_idx] + 15),
                arrowprops=dict(arrowstyle='->', color=COLOR_RED, lw=1.2),
                fontproperties=FONT_PROP, fontsize=9, color=COLOR_RED)

    return _save_chart(fig, 'traffic_trend', report_id)


def chart_device_type_dist(report_id):
    """设备类型分布 — 饼图"""
    fig, ax = plt.subplots(figsize=(5, 4))

    labels = ['路由器', '交换机', '防火墙', '服务器']
    sizes = [2, 3, 2, 3]
    colors = [COLOR_BLUE, COLOR_CYAN, COLOR_ORANGE, COLOR_PURPLE]
    explode = (0, 0.05, 0, 0.05)

    wedges, texts, autotexts = ax.pie(
        sizes, explode=explode, labels=labels, colors=colors,
        autopct='%1.0f%%', startangle=90, pctdistance=0.6,
        textprops={'fontproperties': FONT_PROP, 'fontsize': 11}
    )
    for t in autotexts:
        t.set_fontproperties(FONT_BOLD)
        t.set_fontsize(12)
        t.set_color('white')

    ax.legend(wedges, [f'{l}: {s} 台' for l, s in zip(labels, sizes)],
              loc='lower center', ncol=4, prop=FONT_PROP, fontsize=9,
              frameon=False, bbox_to_anchor=(0.5, -0.05))

    return _save_chart(fig, 'device_type_dist', report_id)


def chart_cpu_ranking(report_id):
    """CPU 使用率排行 — 横向柱状图"""
    fig, ax = plt.subplots(figsize=(7, 3.5))

    devices = ['应用服务器-02', '汇聚交换机-02', '汇聚交换机-01',
               '应用服务器-01', '数据库服务器-01']
    values = [95, 91, 72, 67, 58]
    bar_colors = [COLOR_RED if v >= 80 else COLOR_ORANGE if v >= 70 else COLOR_BLUE for v in values]

    bars = ax.barh(devices, values, color=bar_colors, height=0.5, edgecolor='white', linewidth=0.5)

    # 数值标签
    for bar, v in zip(bars, values):
        ax.text(bar.get_width() + 1.5, bar.get_y() + bar.get_height() / 2,
                f'{v}%', va='center', fontproperties=FONT_BOLD, fontsize=10, color='#333')

    ax.set_xlim(0, 110)
    ax.set_xlabel('CPU 使用率 (%)', fontproperties=FONT_PROP, fontsize=10)
    ax.tick_params(axis='y', labelsize=9)
    for label in ax.get_yticklabels():
        label.set_fontproperties(FONT_PROP)

    # 阈值线
    ax.axvline(x=80, color=COLOR_RED, linestyle='--', alpha=0.6, linewidth=1)
    ax.text(81, len(devices) - 0.3, '阈值 80%', fontproperties=FONT_PROP, fontsize=8, color=COLOR_RED)

    ax.grid(True, axis='x', alpha=0.3, linestyle='--')

    return _save_chart(fig, 'cpu_ranking', report_id)


def chart_memory_analysis(report_id):
    """内存使用率分析 — 横向柱状图"""
    fig, ax = plt.subplots(figsize=(7, 3.5))

    devices = ['应用服务器-02', '汇聚交换机-02', '汇聚交换机-01',
               '应用服务器-01', '数据库服务器-01']
    values = [91, 88, 80, 74, 70]
    bar_colors = [COLOR_RED if v >= 90 else COLOR_ORANGE if v >= 80 else COLOR_BLUE for v in values]

    bars = ax.barh(devices, values, color=bar_colors, height=0.5, edgecolor='white', linewidth=0.5)

    for bar, v in zip(bars, values):
        ax.text(bar.get_width() + 1.5, bar.get_y() + bar.get_height() / 2,
                f'{v}%', va='center', fontproperties=FONT_BOLD, fontsize=10, color='#333')

    ax.set_xlim(0, 105)
    ax.set_xlabel('内存使用率 (%)', fontproperties=FONT_PROP, fontsize=10)
    ax.tick_params(axis='y', labelsize=9)
    for label in ax.get_yticklabels():
        label.set_fontproperties(FONT_PROP)

    ax.axvline(x=80, color=COLOR_ORANGE, linestyle='--', alpha=0.6, linewidth=1)
    ax.text(81, len(devices) - 0.3, '阈值 80%', fontproperties=FONT_PROP, fontsize=8, color=COLOR_ORANGE)
    ax.axvline(x=90, color=COLOR_RED, linestyle='--', alpha=0.6, linewidth=1)
    ax.text(91, len(devices) - 0.8, '危险 90%', fontproperties=FONT_PROP, fontsize=8, color=COLOR_RED)

    ax.grid(True, axis='x', alpha=0.3, linestyle='--')

    return _save_chart(fig, 'memory_analysis', report_id)


def chart_latency_trend(report_id):
    """网络延迟趋势 — 折线图"""
    fig, ax = plt.subplots(figsize=(7, 3.5))

    hours = [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22]
    latency_router1 = [8, 7, 6, 9, 15, 18, 14, 16, 20, 22, 18, 12]
    latency_router2 = [7, 6, 6, 8, 13, 15, 12, 14, 17, 19, 16, 11]

    ax.plot(hours, latency_router1, 'o-', color=COLOR_BLUE, linewidth=2, markersize=4, label='核心路由器-01')
    ax.plot(hours, latency_router2, 's-', color=COLOR_GREEN, linewidth=2, markersize=4, label='核心路由器-02')

    ax.fill_between(hours, latency_router1, alpha=0.06, color=COLOR_BLUE)
    ax.fill_between(hours, latency_router2, alpha=0.06, color=COLOR_GREEN)

    ax.set_xticks(hours)
    ax.set_xlabel('时间段 (时)', fontproperties=FONT_PROP, fontsize=10)
    ax.set_ylabel('延迟 (ms)', fontproperties=FONT_PROP, fontsize=10)
    ax.legend(prop=FONT_PROP, fontsize=9, framealpha=0.9)
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_ylim(0, 30)

    # 正常范围标记
    ax.axhline(y=25, color=COLOR_ORANGE, linestyle='--', alpha=0.5, linewidth=1)
    ax.text(22.5, 25.5, '警告线 25ms', fontproperties=FONT_PROP, fontsize=8, color=COLOR_ORANGE, ha='right')

    return _save_chart(fig, 'latency_trend', report_id)


def chart_traffic_heatmap(report_id):
    """流量时段热力图 — 模拟热力图"""
    fig, ax = plt.subplots(figsize=(7, 3.5))

    # 模拟一周 × 24小时的流量数据
    days = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
    hours = list(range(24))

    np.random.seed(42)
    data = np.random.rand(len(days), len(hours)) * 100
    # 工作日高峰
    for i in range(5):
        for h in [9, 10, 11, 14, 15, 16]:
            data[i, h] = 70 + np.random.rand() * 25
    # 周末较低
    for i in [5, 6]:
        data[i, :] = data[i, :] * 0.4
    # 凌晨低谷
    for h in range(6):
        data[:, h] = data[:, h] * 0.15 + 2

    im = ax.imshow(data, cmap='YlOrRd', aspect='auto', interpolation='bilinear')

    ax.set_xticks(range(0, 24, 2))
    ax.set_xticklabels([f'{h}:00' for h in range(0, 24, 2)], fontproperties=FONT_PROP, fontsize=8)
    ax.set_yticks(range(len(days)))
    ax.set_yticklabels(days, fontproperties=FONT_PROP, fontsize=9)
    ax.set_xlabel('时段', fontproperties=FONT_PROP, fontsize=10)
    ax.set_ylabel('星期', fontproperties=FONT_PROP, fontsize=10)

    cbar = fig.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label('流量指数', fontproperties=FONT_PROP, fontsize=9)

    return _save_chart(fig, 'traffic_heatmap', report_id)


def chart_alert_trend(report_id):
    """告警数量趋势 — 分组柱状图"""
    fig, ax = plt.subplots(figsize=(7, 3.5))

    days = ['7/8', '7/9', '7/10', '7/11', '7/12', '7/13', '7/14']
    categories = ['紧急', '严重', '警告']
    colors = [COLOR_RED, COLOR_ORANGE, COLOR_CYAN]

    data = {
        '紧急': [0, 1, 0, 1, 0, 0, 0],
        '严重': [1, 1, 0, 0, 1, 1, 0],
        '警告': [1, 0, 2, 0, 1, 0, 0],
    }

    x = np.arange(len(days))
    width = 0.25
    offsets = [-width, 0, width]

    for i, cat in enumerate(categories):
        bars = ax.bar(x + offsets[i], data[cat], width, label=cat,
                      color=colors[i], edgecolor='white', linewidth=0.5)
        for bar, v in zip(bars, data[cat]):
            if v > 0:
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.1,
                        str(v), ha='center', va='bottom', fontsize=8, fontproperties=FONT_PROP)

    ax.set_xticks(x)
    ax.set_xticklabels(days, fontproperties=FONT_PROP, fontsize=9)
    ax.set_ylabel('告警数量', fontproperties=FONT_PROP, fontsize=10)
    ax.legend(prop=FONT_PROP, fontsize=9, framealpha=0.9)
    ax.grid(True, axis='y', alpha=0.3, linestyle='--')
    ax.set_ylim(0, 3.5)

    return _save_chart(fig, 'alert_trend', report_id)


def chart_ai_conclusion(report_id):
    """AI 分析结论 — 雷达图"""
    fig, ax = plt.subplots(figsize=(5, 5), subplot_kw=dict(polar=True))

    categories = ['网络性能', '设备健康', '安全状态', '告警处理', '资源利用']
    values = [85, 72, 60, 45, 68]  # 百分制评分

    angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
    values += values[:1]
    angles += angles[:1]

    ax.plot(angles, values, 'o-', color=COLOR_BLUE, linewidth=2, markersize=6)
    ax.fill(angles, values, alpha=0.15, color=COLOR_BLUE)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontproperties=FONT_PROP, fontsize=11)
    ax.set_ylim(0, 100)

    # 评分值标注
    for angle, val in zip(angles[:-1], values[:-1]):
        ax.text(angle, val + 5, f'{val}', ha='center', fontproperties=FONT_BOLD, fontsize=10, color=COLOR_BLUE)

    # 阈值圈
    ax.axhline(y=60, color=COLOR_ORANGE, linestyle='--', alpha=0.4, linewidth=0.8)

    return _save_chart(fig, 'ai_conclusion', report_id)


# 图表调度映射
CHART_GENERATORS = {
    'basic_stats':      chart_basic_stats,
    'traffic_trend':    chart_traffic_trend,
    'device_type_dist': chart_device_type_dist,
    'cpu_ranking':      chart_cpu_ranking,
    'memory_analysis':  chart_memory_analysis,
    'latency_trend':    chart_latency_trend,
    'traffic_heatmap':  chart_traffic_heatmap,
    'alert_trend':      chart_alert_trend,
    'ai_conclusion':    chart_ai_conclusion,
}


def generate_charts(contents, report_id):
    """
    批量生成图表
    参数:
        contents: list of content keys
        report_id: 报告 ID
    返回:
        dict: { content_key: chart_image_path }
    """
    _cleanup()
    result = {}
    for key in contents:
        generator = CHART_GENERATORS.get(key)
        if generator:
            try:
                path = generator(report_id)
                result[key] = path
            except Exception as e:
                print(f'[chart_generator] 生成图表 {key} 失败: {e}')
    return result
