"""
Agent工具实现
"""
from langchain_core.tools import tool
from tavily import TavilyClient
from tool.config_handler import System_Config
"""
Travily网络搜索工具
"""
@tool(description="网络搜索工具，用于搜索具有时效性知识和知识库以外的知识")
def search(query:str)->str:
    tavily_client=TavilyClient(
        api_key=System_Config["tavily_api_key"],
    )
    response=tavily_client.search(query=query,search_depth='fast',topic='general')
