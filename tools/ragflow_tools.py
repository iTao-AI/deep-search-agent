import os
import logging
from langchain_core.tools import tool
from ragflow_sdk import RAGFlow

from api.monitor import monitor
from typing import Tuple, Optional

logger = logging.getLogger(__name__)


def _load_ragflow_env() -> Tuple[Optional[str], Optional[str]]:
    """加载 RAGFlow 环境变量（不再调用 load_dotenv）"""
    api_key = os.getenv("RAGFLOW_API_KEY")
    base_url = os.getenv("RAGFLOW_API_URL")
    return api_key, base_url


@tool
def get_assistant_list(
        dummy_arg: str = "",
) -> str:
    """Get info for all RAGFlow chat assistants."""
    monitor.report_tool("RAGFlow助手列表查询")
    api_key, base_url = _load_ragflow_env()

    if not api_key or not base_url:
        return "错误：RAGFlow 环境变量未配置（需设置 RAGFLOW_API_URL 与 RAGFLOW_API_KEY）"

    result = ""
    try:
        rag = RAGFlow(api_key=api_key, base_url=base_url)
        for assistant in rag.list_chats():
            kb_names = []
            if assistant.datasets and isinstance(assistant.datasets, list):
                for dataset in assistant.datasets:
                    if isinstance(dataset, dict) and "name" in dataset:
                        kb_names.append(dataset["name"])

            kb_names_str = "、".join(kb_names) if kb_names else "无"
            result += f"助手名称：{assistant.name}； 功能介绍：{assistant.description}； 关联知识库：{kb_names_str}\n"

        return result.rstrip("\n") if result else "未找到任何聊天助手"
    except Exception as e:
        return f"获取助手列表失败：{str(e)}"


@tool
def create_ask_delete(
        assistant_name: str,
        question: str
) -> str:
    """Ask a RAGFlow assistant a question (temporary session, deleted after use)."""
    monitor.report_tool(
        "RAGFlow助手提问工具",
        {"助手名称": assistant_name, "查询问题": question}
    )
    api_key, base_url = _load_ragflow_env()

    if not api_key or not base_url:
        return "错误：RAGFlow 环境变量未配置（需设置 RAGFLOW_API_URL 与 RAGFLOW_API_KEY）"

    session = None
    try:
        rag = RAGFlow(api_key=api_key, base_url=base_url)
        chats = rag.list_chats(name=assistant_name)
        if not chats:
            return f"没有找到name:{assistant_name}的聊天助手！"
        chat = chats[0]
        session = chat.create_session(name="temp_session")

        response_stream = session.ask(question=question, stream=True)
        full_answer = ''
        for response in response_stream:
            if hasattr(response, "content") and response.content:
                full_answer = response.content
        monitor.report_tool(
            "RAGFlow助手回答记录",
            {"助手名称": assistant_name, "问题": question, "答案": full_answer}
        )
        return full_answer
    except Exception as e:
        return f"提问过程失败：{str(e)}"
    finally:
        if session and hasattr(session, "id"):
            try:
                chat.delete_sessions(ids=[session.id])
            except Exception as e:
                logger.warning(f"Failed to delete RAGFlow session: {e}")
