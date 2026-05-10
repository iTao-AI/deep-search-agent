import os
import time
from typing import Literal
from langchain_core.tools import tool

from api.monitor import monitor


def _search_with_retry(query: str, max_results: int, topic: str, include_raw_content: bool,
                       max_retries: int = 3, timeout: int = 10) -> dict:
    """Internal search with retry logic. Raises on persistent failure."""
    from tavily import TavilyClient

    client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    last_error = None

    for attempt in range(max_retries):
        try:
            return client.search(
                query,
                max_results=max_results,
                include_raw_content=include_raw_content,
                topic=topic,
            )
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                backoff = min(2 ** attempt, 10)
                time.sleep(backoff)

    raise last_error


@tool
def internet_search(
        query: str,
        max_results: int = 5,
        topic: Literal["general", "news", "finance"] = "general",
        include_raw_content: bool = False
):
    """Search the internet for public information, news, or finance data."""
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return "Error: TAVILY_API_KEY is not configured."

    monitor.report_tool("网络搜索工具", {"网络搜索工具": query})
    try:
        results = _search_with_retry(
            query, max_results, topic, include_raw_content,
            max_retries=3, timeout=10,
        )
        return results
    except Exception as e:
        return f"Error: internet search failed after retries — {e}"
