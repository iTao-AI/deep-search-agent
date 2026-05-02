import logging
from pathlib import Path

try:
    from typing import Annotated
except ImportError:
    from typing_extensions import Annotated
from langchain_core.tools import tool
from api.monitor import monitor
from api.context import get_session_context
from utils.path_utils import resolve_path


@tool
def generate_markdown(
        content: Annotated[str, "Text content for the Markdown document"],
        filename: Annotated[str, "Markdown filename (with or without .md extension)"],
        path: Annotated[str, "Save path (absolute or relative to session dir)"] = ""
):
    """Generate a Markdown (.md) file from text content."""
    monitor.report_tool("Markdown文档生成工具", {"写入的文本内容": content})
    if not filename.endswith('.md'):
        filename += '.md'

    session_dir = get_session_context()

    if path and path != ".":
        full_input_path = str(Path(path) / filename)
    else:
        full_input_path = filename

    full_path_str = resolve_path(full_input_path, session_dir)
    file_path = Path(full_path_str)
    parent_dir = file_path.parent

    try:
        if not parent_dir.exists():
            parent_dir.mkdir(parents=True, exist_ok=True)

        file_path.write_text(content, encoding='utf-8')
        return f"Markdown文件 '{file_path}' 已成功生成并保存。"
    except Exception as e:
        return f"生成Markdown文件失败: {str(e)}"
