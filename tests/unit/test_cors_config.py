"""CORS 配置单元测试 - Phase C"""
import os
import pytest


class TestCORSConfig:
    """Phase C: CORS 配置修复"""

    def test_default_origin(self):
        """未设置 FRONTEND_ORIGIN 时，默认返回 localhost:5173"""
        # 保存原值
        original = os.environ.get("FRONTEND_ORIGIN")

        # 清除环境变量
        if "FRONTEND_ORIGIN" in os.environ:
            del os.environ["FRONTEND_ORIGIN"]

        from api.cors_config import get_allowed_origins
        origins = get_allowed_origins()

        assert origins == ["http://localhost:5173"]

        # 恢复
        if original is not None:
            os.environ["FRONTEND_ORIGIN"] = original

    def test_custom_origin(self):
        """设置 FRONTEND_ORIGIN 后，返回配置的源"""
        original = os.environ.get("FRONTEND_ORIGIN")
        os.environ["FRONTEND_ORIGIN"] = "https://example.com"

        # 重新导入以获取新配置
        import importlib
        import api.cors_config
        importlib.reload(api.cors_config)
        from api.cors_config import get_allowed_origins

        origins = get_allowed_origins()
        assert origins == ["https://example.com"]

        # 恢复
        if original is not None:
            os.environ["FRONTEND_ORIGIN"] = original

    def test_validate_allowed_origin(self):
        """校验允许的源"""
        original = os.environ.get("FRONTEND_ORIGIN")
        if "FRONTEND_ORIGIN" in os.environ:
            del os.environ["FRONTEND_ORIGIN"]

        import importlib
        import api.cors_config
        importlib.reload(api.cors_config)
        from api.cors_config import validate_cors_origin

        assert validate_cors_origin("http://localhost:5173") is True
        assert validate_cors_origin("http://evil.com") is False

        if original is not None:
            os.environ["FRONTEND_ORIGIN"] = original

    def test_multiple_origins_not_allowed(self):
        """不应该允许多个源（单源策略）"""
        original = os.environ.get("FRONTEND_ORIGIN")
        if "FRONTEND_ORIGIN" in os.environ:
            del os.environ["FRONTEND_ORIGIN"]

        import importlib
        import api.cors_config
        importlib.reload(api.cors_config)
        from api.cors_config import get_allowed_origins

        origins = get_allowed_origins()
        assert len(origins) == 1
        assert origins[0] == "http://localhost:5173"

        if original is not None:
            os.environ["FRONTEND_ORIGIN"] = original
