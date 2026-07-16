"""
=========================================================
数据上传模块 — 文件上传 / 预览 / 上传历史
=========================================================
"""
import os
import csv
import io
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file
from db import db
from .auth import login_required

upload_bp = Blueprint('upload', __name__)

# 上传目录
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)


@upload_bp.route('/upload', methods=['POST'])
def upload_file():
    """
    上传数据文件（CSV/Excel/TXT）
    请求: multipart/form-data, file 字段为上传文件
    返回: { "code": 200, "data": { "preview": [...], "file_name": "..." } }
    """
    payload, err = login_required()
    if err:
        return err

    if 'file' not in request.files:
        return jsonify({'code': 400, 'message': '未选择文件'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'code': 400, 'message': '文件名为空'}), 400

    # 先读取内容（用于预览），再保存文件
    try:
        content = file.read()
        file_size = len(content)
    except Exception:
        content = b''
        file_size = 0

    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, 'wb') as f:
        f.write(content)

    # 解析 CSV 预览
    preview = []
    try:
        stream = io.StringIO(content.decode('utf-8'))
        reader = csv.DictReader(stream)
        for i, row in enumerate(reader):
            if i >= 10:  # 只预览前10行
                break
            preview.append(row)
    except Exception:
        pass

    # 记录上传历史
    db.insert("""
        INSERT INTO upload_history (user_id, file_name, file_size, status)
        VALUES (%s, %s, %s, '处理中')
    """, (payload['user_id'], file.filename, file_size))

    return jsonify({
        'code': 200,
        'data': {
            'preview': preview,
            'file_name': file.filename
        }
    })


@upload_bp.route('/preview', methods=['GET'])
def preview_data():
    """
    获取模拟预览数据
    返回: { "code": 200, "data": [...] }
    """
    mock = [
        {'timestamp': '2026-07-10 08:00:00', 'deviceName': '核心路由器-01', 'cpuUsage': 42, 'memUsage': 58, 'netIn': 156, 'netOut': 98, 'lossRate': 0.01},
        {'timestamp': '2026-07-10 08:05:00', 'deviceName': '核心路由器-02', 'cpuUsage': 37, 'memUsage': 52, 'netIn': 142, 'netOut': 87, 'lossRate': 0.00},
        {'timestamp': '2026-07-10 08:10:00', 'deviceName': '汇聚交换机-01', 'cpuUsage': 68, 'memUsage': 77, 'netIn': 230, 'netOut': 185, 'lossRate': 0.03},
        {'timestamp': '2026-07-10 08:15:00', 'deviceName': '汇聚交换机-03', 'cpuUsage': 53, 'memUsage': 61, 'netIn': 198, 'netOut': 154, 'lossRate': 0.02},
        {'timestamp': '2026-07-10 08:20:00', 'deviceName': '防火墙-FW01', 'cpuUsage': 29, 'memUsage': 43, 'netIn': 320, 'netOut': 210, 'lossRate': 0.00}
    ]
    return jsonify({'code': 200, 'data': mock})


@upload_bp.route('/upload/history', methods=['GET'])
def upload_history():
    """
    获取上传历史记录
    返回: { "code": 200, "data": [...] }
    """
    records = db.select_all("""
        SELECT id, file_name AS fileName,
               DATE_FORMAT(uploaded_at, '%%Y-%%m-%%d %%H:%%i:%%s') AS uploadTime,
               data_count AS dataCount, status, file_size AS fileSize
        FROM upload_history
        ORDER BY uploaded_at DESC LIMIT 20
    """)

    return jsonify({'code': 200, 'data': records or []})


@upload_bp.route('/upload/download/<int:record_id>', methods=['GET'])
def download_file(record_id):
    """
    下载已上传的原始文件
    需校验该记录属于当前登录用户
    """
    payload, err = login_required()
    if err:
        return err

    record = db.select_one(
        "SELECT id, file_name FROM upload_history WHERE id = %s AND user_id = %s",
        (record_id, payload['user_id'])
    )
    if not record:
        return jsonify({'code': 404, 'message': '文件记录不存在'}), 404

    file_path = os.path.join(UPLOAD_DIR, record['file_name'])
    if not os.path.exists(file_path):
        return jsonify({'code': 404, 'message': '文件已丢失'}), 404

    return send_file(file_path, as_attachment=True, download_name=record['file_name'])


@upload_bp.route('/upload/preview/<int:record_id>', methods=['GET'])
def preview_history_file(record_id):
    """
    预览历史上传文件的数据内容（前 20 行）
    需校验该记录属于当前登录用户
    """
    payload, err = login_required()
    if err:
        return err

    record = db.select_one(
        "SELECT id, file_name FROM upload_history WHERE id = %s AND user_id = %s",
        (record_id, payload['user_id'])
    )
    if not record:
        return jsonify({'code': 404, 'message': '文件记录不存在'}), 404

    file_path = os.path.join(UPLOAD_DIR, record['file_name'])
    if not os.path.exists(file_path):
        return jsonify({'code': 404, 'message': '文件已丢失'}), 404

    preview = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                if i >= 20:
                    break
                preview.append(row)
    except Exception:
        return jsonify({'code': 500, 'message': '文件解析失败'}), 500

    return jsonify({'code': 200, 'data': {'preview': preview, 'file_name': record['file_name']}})


@upload_bp.route('/upload/confirm', methods=['POST'])
def confirm_import():
    """
    确认导入数据
    请求: { "mode": "append|overwrite" }
    从该用户最近一次上传（状态为"处理中"）的文件中读取数据并写入 device_metrics 表
    """
    payload, err = login_required()
    if err:
        return err

    data = request.get_json() or {}
    mode = data.get('mode', 'append')
    user_id = payload['user_id']

    # 查找该用户最近一次待处理的上传记录
    record = db.select_one("""
        SELECT id, file_name FROM upload_history
        WHERE user_id = %s AND status = '处理中'
        ORDER BY uploaded_at DESC LIMIT 1
    """, (user_id,))

    if not record:
        return jsonify({'code': 400, 'message': '未找到待处理的上传文件，请先上传文件'}), 400

    file_path = os.path.join(UPLOAD_DIR, record['file_name'])
    if not os.path.exists(file_path):
        db.update("UPDATE upload_history SET status = '失败' WHERE id = %s", (record['id'],))
        return jsonify({'code': 400, 'message': '上传文件已丢失，请重新上传'}), 400

    imported = 0
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = []
            for row in reader:
                ts = row.get('timestamp') or datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                device_name = (row.get('deviceName') or '').strip()

                # 根据设备名称查找 device_id
                device = None
                if device_name:
                    device = db.select_one("SELECT id FROM devices WHERE name = %s", (device_name,))

                device_id = device['id'] if device else None
                if device_id is None:
                    continue  # 跳过找不到设备的行

                rows.append((
                    device_id,
                    ts,
                    float(row.get('cpuUsage', 0) or 0),
                    float(row.get('memUsage', 0) or 0),
                    float(row.get('netIn', 0) or 0),
                    float(row.get('netOut', 0) or 0),
                    float(row.get('lossRate', 0) or 0),
                ))

        if mode == 'overwrite' and rows:
            # 覆盖模式：删除相关设备的所有历史指标
            device_ids = list(set(r[0] for r in rows))
            for did in device_ids:
                db.delete("DELETE FROM device_metrics WHERE device_id = %s", (did,))

        if rows:
            db.insert_many("""
                INSERT INTO device_metrics
                    (device_id, timestamp, cpu_usage, memory_usage, network_in, network_out, packet_loss)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, rows)
            imported = len(rows)

        db.update("""
            UPDATE upload_history SET status = '成功', data_count = %s WHERE id = %s
        """, (imported, record['id']))

    except Exception as e:
        db.update("UPDATE upload_history SET status = '失败' WHERE id = %s", (record['id'],))
        return jsonify({'code': 500, 'message': f'数据导入失败: {str(e)}'}), 500

    return jsonify({
        'code': 200,
        'message': f'数据已{"追加" if mode == "append" else "覆盖导入"}成功，共导入 {imported} 条记录'
    })
