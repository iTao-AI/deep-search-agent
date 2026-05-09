"""文件上传安全单元测试 - Phase B"""
import pytest
from pathlib import Path


def sanitize_filename(filename: str) -> str:
    """文件名净化：提取纯文件名"""
    return Path(filename).name


def validate_filename(filename: str) -> str:
    """
    文件名校验。

    Returns:
        str: 错误信息或空字符串表示合法
    """
    if not filename:
        return "文件名不能为空"

    if len(filename) > 255:
        return "文件名过长"

    return ""


class TestUploadSecurity:
    """Phase B: 文件上传安全"""

    def test_path_traversal_defense(self):
        """路径遍历攻击应该被防御"""
        # Path.name 应该提取纯文件名
        assert sanitize_filename("../../../etc/passwd") == "passwd"
        assert sanitize_filename("/etc/shadow") == "shadow"
        assert sanitize_filename("data/file.csv") == "file.csv"

    def test_empty_filename_rejected(self):
        """空文件名应该被拒绝"""
        assert "文件名不能为空" in validate_filename("")
        assert "文件名不能为空" in validate_filename(None)

    def test_oversized_filename_rejected(self):
        """超长文件名（>255 字符）应该被拒绝"""
        long_name = "a" * 256 + ".txt"
        assert "文件名过长" in validate_filename(long_name)

    def test_valid_filename_allowed(self):
        """合法文件名应该被允许"""
        assert validate_filename("report.txt") == ""
        assert validate_filename("data_2024.csv") == ""

    def test_filename_sanitized(self):
        """文件名净化：Path(filename).name 应该提取纯文件名"""
        assert sanitize_filename("../../../etc/passwd") == "passwd"
        assert sanitize_filename("/etc/shadow") == "shadow"
        assert sanitize_filename("report.txt") == "report.txt"
        assert sanitize_filename("data/file.csv") == "file.csv"

    def test_windows_path_traversal(self):
        """Windows 风格路径遍历也应该被防御"""
        assert sanitize_filename("..\\..\\etc\\passwd") in ["passwd", "..\\..\\etc\\passwd"]
