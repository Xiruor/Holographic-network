"""
=========================================================
全息网络洞察系统 — 数据库操作工具类
封装 PyMySQL，提供统一的数据库访问接口
=========================================================
"""
import threading
import pymysql
from config import Config


class Database:
    """数据库操作工具类，封装常用 CRUD 方法"""

    def __init__(self):
        self.connection = None
        self._lock = threading.Lock()

    def connect(self):
        """获取数据库连接（自动重连）"""
        if self.connection is None or not self._is_connected():
            self.connection = pymysql.connect(
                host=Config.DB_HOST,
                port=Config.DB_PORT,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD,
                database=Config.DB_NAME,
                charset=Config.DB_CHARSET,
                cursorclass=pymysql.cursors.DictCursor,  # 返回字典格式
                autocommit=True,  # 每次查询自动提交，确保读取到最新数据
                ssl_disabled=True  # 禁用 SSL，避免 MySQL 8+ 默认 SSL 配置导致的连接问题
            )
        return self.connection

    def _is_connected(self):
        """检查连接是否有效"""
        try:
            self.connection.ping(reconnect=False)
            return True
        except Exception:
            return False

    def _get_cursor(self):
        """获取游标（失败时强制重连一次）"""
        try:
            conn = self.connect()
            return conn.cursor()
        except Exception:
            # 连接可能已损坏，强制重连
            self.connection = None
            conn = self.connect()
            return conn.cursor()

    def _execute_with_retry(self, sql, params=None):
        """执行 SQL，遇连接错误时自动重连重试一次（线程安全）"""
        with self._lock:
            cursor = self._get_cursor()
            try:
                cursor.execute(sql, params or ())
                return cursor
            except (
                ValueError,
                pymysql.err.OperationalError,
                pymysql.err.InterfaceError,
                pymysql.err.InternalError,
            ):
                # 连接已损坏 — 强制重连再试一次
                cursor.close()
                self.connection = None
                cursor = self._get_cursor()
                cursor.execute(sql, params or ())
                return cursor

    # ---- 查询操作 ----

    def select_one(self, sql, params=None):
        """查询单条记录，返回 dict 或 None"""
        cursor = self._execute_with_retry(sql, params)
        try:
            return cursor.fetchone()
        finally:
            cursor.close()

    def select_all(self, sql, params=None):
        """查询多条记录，返回 list[dict]"""
        cursor = self._execute_with_retry(sql, params)
        try:
            return cursor.fetchall()
        finally:
            cursor.close()

    def select_page(self, sql, params=None, page=1, page_size=10):
        """
        分页查询
        返回: { "list": [...], "total": int, "page": int, "page_size": int }
        """
        # 查询总数
        count_sql = f"SELECT COUNT(*) AS total FROM ({sql}) AS _tmp"
        total = self.select_one(count_sql, params)['total']

        # 查询当前页数据
        offset = (page - 1) * page_size
        page_sql = f"{sql} LIMIT {page_size} OFFSET {offset}"
        data = self.select_all(page_sql, params)

        return {
            'list': data,
            'total': total,
            'page': page,
            'page_size': page_size
        }

    # ---- 写入操作 ----

    def insert(self, sql, params=None):
        """插入记录，返回自增 ID"""
        cursor = self._get_cursor()
        try:
            cursor.execute(sql, params or ())
            self.connection.commit()
            return cursor.lastrowid
        except Exception:
            self.connection.rollback()
            raise
        finally:
            cursor.close()

    def insert_many(self, sql, params_list):
        """批量插入，返回影响行数"""
        cursor = self._get_cursor()
        try:
            affected = cursor.executemany(sql, params_list)
            self.connection.commit()
            return affected
        except Exception:
            self.connection.rollback()
            raise
        finally:
            cursor.close()

    def update(self, sql, params=None):
        """更新记录，返回影响行数"""
        cursor = self._get_cursor()
        try:
            affected = cursor.execute(sql, params or ())
            self.connection.commit()
            return affected
        except Exception:
            self.connection.rollback()
            raise
        finally:
            cursor.close()

    def delete(self, sql, params=None):
        """删除记录，返回影响行数"""
        return self.update(sql, params)

    # ---- 关闭连接 ----

    def close(self):
        """关闭数据库连接"""
        if self.connection:
            try:
                self.connection.close()
            except Exception:
                pass
            finally:
                self.connection = None


# 全局单例
db = Database()
