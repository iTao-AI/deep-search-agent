"""Phase A: MySQLConnectionManager 单元测试"""
import pytest
import sys
from unittest.mock import MagicMock, patch


@pytest.fixture(autouse=True)
def _mock_mysql_connector():
    """Mock mysql.connector before importing db_connection, clean up after"""
    # Clear cached modules FIRST so lazy imports use our mocks
    for mod in ["mysql.connector", "mysql", "tools.db_connection", "tools.mysql_tools"]:
        sys.modules.pop(mod, None)

    mock_module = MagicMock()
    mock_pool = MagicMock()
    mock_module.pooling.MySQLConnectionPool = mock_pool
    mock_module.Error = Exception
    mock_module.errors.Error = Exception
    sys.modules["mysql.connector"] = mock_module
    sys.modules["mysql"] = MagicMock()
    yield
    for mod in ["mysql.connector", "mysql", "tools.db_connection", "tools.mysql_tools"]:
        sys.modules.pop(mod, None)


class TestMySQLConnectionManager:
    """测试 MySQLConnectionManager 连接池管理"""

    def _get_manager_class(self):
        """Import after mocks are set up"""
        from tools.db_connection import MySQLConnectionManager
        return MySQLConnectionManager

    def test_create_pool_valid_config(self):
        """有效配置应该成功创建连接池"""
        Manager = self._get_manager_class()
        config = {
            "user": "test",
            "password": "test",
            "host": "localhost",
            "port": "3306",
            "database": "test_db",
        }
        manager = Manager(config)
        manager.create_pool()
        assert manager._pool is not None

    def test_create_pool_missing_config(self):
        """缺失配置应该返回错误字符串"""
        Manager = self._get_manager_class()
        manager = Manager({"user": "test"})
        result = manager.create_pool()
        assert "错误" in result

    def test_get_connection_returns_connection(self):
        """连接池存在时应返回连接"""
        Manager = self._get_manager_class()
        mock_conn = MagicMock()
        mock_pool_instance = MagicMock()
        mock_pool_instance.get_connection.return_value = mock_conn

        with patch("tools.db_connection.pooling.MySQLConnectionPool") as MockPool:
            MockPool.return_value = mock_pool_instance
            config = {
                "user": "test", "password": "test", "host": "localhost",
                "port": "3306", "database": "test_db",
            }
            manager = Manager(config)
            manager.create_pool()
            conn = manager.get_connection()
            assert conn is mock_conn
            mock_pool_instance.get_connection.assert_called_once()

    def test_release_connection_returns_to_pool(self):
        """释放连接应调用 pool.add_connection"""
        Manager = self._get_manager_class()
        mock_conn = MagicMock()
        mock_pool_instance = MagicMock()

        with patch("tools.db_connection.pooling.MySQLConnectionPool") as MockPool:
            MockPool.return_value = mock_pool_instance
            config = {
                "user": "test", "password": "test", "host": "localhost",
                "port": "3306", "database": "test_db",
            }
            manager = Manager(config)
            manager.create_pool()
            manager.release_connection(mock_conn)
            mock_pool_instance.add_connection.assert_called_once_with(mock_conn)

    def test_get_connection_without_pool_returns_error(self):
        """未创建连接池时获取连接应返回错误"""
        Manager = self._get_manager_class()
        config = {
            "user": "test", "password": "test", "host": "localhost",
            "port": "3306", "database": "test_db",
        }
        manager = Manager(config)
        result = manager.get_connection()
        assert "错误" in result
