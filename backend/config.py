"""
=========================================================
全息网络洞察系统 — 配置文件
从 .env 读取配置，提供统一配置入口
=========================================================
"""
import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()


class Config:
    """应用配置类"""

    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    DEBUG = os.getenv('FLASK_DEBUG', '1') == '1'

    # MySQL 数据库
    DB_HOST = os.getenv('DB_HOST', '127.0.0.1')
    DB_PORT = int(os.getenv('DB_PORT', 3306))
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'root')
    DB_NAME = os.getenv('DB_NAME', 'holographic_network')
    DB_CHARSET = 'utf8mb4'

    # JWT
    JWT_SECRET = os.getenv('JWT_SECRET', 'holographic-network-jwt-secret')
    JWT_EXPIRE_HOURS = int(os.getenv('JWT_EXPIRE_HOURS', 24))
