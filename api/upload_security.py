"""文件上传安全：文件名净化与校验"""
from pathlib import Path, PureWindowsPath


def sanitize_filename(filename: str) -> str:
    """文件名净化：提取纯文件名，防御路径遍历攻击"""
    # 先处理 Windows 风格路径
    if "\\" in filename:
        filename = PureWindowsPath(filename).name
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
