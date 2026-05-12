import logging
from pathlib import Path
from typing import Annotated, Optional

from langchain_core.tools import tool
from api.monitor import monitor
from api.context import get_session_context
from utils.path_utils import resolve_path

try:
    import docx
except ImportError:
    docx = None

try:
    import pypdf
except ImportError:
    pypdf = None

try:
    import pandas as pd
except ImportError:
    pd = None


@tool
def read_file_content(
        filename: Annotated[str, "File name or path (supports .md, .docx, .pdf, .xlsx, .xls)"],
        instruction: Annotated[str, "Specific instruction for content extraction"] = "提取全部内容"
) -> str:
    """Read file content. Supports Markdown, Word, PDF, and Excel files."""
    monitor.report_tool("文件内容读取工具", {"filename": filename, "instruction": instruction})

    session_dir = get_session_context()
    file_path = Path(resolve_path(filename, session_dir))

    if not file_path.exists():
        monitor.report_end("文件内容读取工具", error=f"文件 '{filename}' 不存在")
        return f"错误：文件 '{filename}' 不存在 (解析路径: {file_path})。"

    ext = file_path.suffix.lower()

    try:
        if ext in ['.md', '.txt']:
            result = file_path.read_text(encoding='utf-8')
            monitor.report_end("文件内容读取工具", result)
            return result

        elif ext == '.docx':
            if docx is None:
                monitor.report_end("文件内容读取工具", error="未安装 python-docx")
                return "错误：未安装 'python-docx' 库，无法读取 Word 文件。"
            doc = docx.Document(str(file_path))
            full_text = [para.text for para in doc.paragraphs]
            result = '\n'.join(full_text)
            monitor.report_end("文件内容读取工具", result)
            return result

        elif ext == '.pdf':
            if pypdf is None:
                monitor.report_end("文件内容读取工具", error="未安装 pypdf")
                return "错误：未安装 'pypdf' 库，无法读取 PDF 文件。"
            reader = pypdf.PdfReader(str(file_path))
            text = "\n".join([page.extract_text() or "" for page in reader.pages])
            monitor.report_end("文件内容读取工具", text)
            return text

        elif ext in ['.xlsx', '.xls']:
            if pd is None:
                monitor.report_end("文件内容读取工具", error="未安装 pandas")
                return "错误：未安装 'pandas' 库，无法读取 Excel 文件。"

            try:
                df = pd.read_excel(str(file_path))
            except Exception as e:
                monitor.report_end("文件内容读取工具", error=str(e))
                return f"读取 Excel 失败: {str(e)}"

            result = "\n".join([
                f"文件: {filename}",
                f"行数: {len(df)}, 列数: {len(df.columns)}",
                f"列名: {', '.join(df.columns.astype(str))}",
                "\n[前5行数据预览]:",
                df.head().to_string(index=False),
                "\n[统计描述]:",
                df.describe().to_string()
            ])
            monitor.report_end("文件内容读取工具", result)
            return result

        else:
            try:
                result = file_path.read_text(encoding='utf-8')
                monitor.report_end("文件内容读取工具", result)
                return result
            except UnicodeDecodeError:
                monitor.report_end("文件内容读取工具", error=f"不支持的格式 '{ext}'")
                return f"错误：不支持的文件格式 '{ext}'，且无法作为文本读取。"

    except Exception as e:
        monitor.report_end("文件内容读取工具", error=str(e))
        return f"读取文件出错: {str(e)}"
