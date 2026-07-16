# 全息网络洞察系统 — 后端服务

Flask + MySQL 后端，为前端提供 RESTful API。

## 项目结构

```
backend/
├── app.py              # Flask 应用入口
├── config.py           # 配置类（读取 .env）
├── db.py               # 数据库工具类（封装 PyMySQL）
├── requirements.txt    # Python 依赖
├── .env                # 环境变量（修改数据库连接信息）
└── routes/
    ├── __init__.py     # 蓝图汇总
    ├── auth.py         # 登录/注册/登出
    ├── dashboard.py    # 仪表盘统计
    ├── devices.py      # 设备 CRUD
    ├── alerts.py       # 告警 CRUD/处理
    ├── metrics.py      # 设备指标
    ├── upload.py       # 数据上传
    ├── analysis.py     # 数据分析统计
    ├── ai_analysis.py  # AI 智能分析
    ├── visualization.py# 可视化图表数据
    ├── reports.py      # 报表生成/列表
    └── admin.py        # 用户管理/操作日志
```

## 接口列表

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/auth/login | 登录 |
| POST | /api/auth/register | 注册 |
| POST | /api/auth/logout | 登出 |
| GET | /api/auth/current | 获取当前用户 |
| GET | /api/dashboard/summary | 仪表盘概览 |
| GET | /api/devices | 设备列表(分页筛选) |
| GET | /api/devices/:id | 设备详情(含关联告警) |
| POST | /api/devices | 添加设备 |
| PUT | /api/devices/:id | 编辑设备 |
| DELETE | /api/devices/:id | 删除设备 |
| GET | /api/alerts | 告警列表(分页筛选) |
| GET | /api/alerts/:id | 告警详情 |
| PUT | /api/alerts/:id | 处理告警 |
| POST | /api/alerts/batch | 批量处理 |
| GET | /api/metrics | 指标列表(分页) |
| GET | /api/metrics/:id | 设备指标 |
| POST | /api/data/upload | 文件上传 |
| GET | /api/data/preview | 数据预览 |
| GET | /api/data/upload/history | 上传历史 |
| POST | /api/data/upload/confirm | 确认导入 |
| GET | /api/analysis/statistics | 数据分析统计 |
| POST | /api/analysis/ai | AI分析 |
| GET | /api/visualization/data | 可视化图表数据 |
| GET | /api/reports | 报告列表 |
| POST | /api/reports/generate | 生成报告 |
| GET | /api/admin/users | 用户管理列表 |
| DELETE | /api/admin/users/:id | 删除用户 |
| GET | /api/admin/logs | 操作日志 |
