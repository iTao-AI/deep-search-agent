from typing import Literal
from langchain_core.tools import tool
from tavily import TavilyClient

import os
from dotenv import load_dotenv

from api.monitor import monitor

load_dotenv()

if TavilyClient:
    tavily_client = TavilyClient(api_key=os.getenv('TAVILY_API_KEY'))
else:
    tavily_client = None


@tool
def internet_search(
        query: str,
        max_results: int = 5,
        topic: Literal["general", "news", "finance"] = "general",
        include_raw_content: bool = False
):
    """Search the internet for public information, news, or finance data."""
    if not tavily_client:
        return "Error: 'tavily-python' library is not installed."
    monitor.report_tool("网络搜索工具", {"网络搜索工具": query})
    try:
        results = tavily_client.search(
            query,
            max_results=max_results,
            include_raw_content=include_raw_content,
            topic=topic,
        )
        return results
    except Exception as e:
        raise e
