from langchain.agents.middleware import wrap_tool_call
from typing import Callable
from langchain_core.messages import ToolMessage
from langgraph.types import Command
from langchain.tools.tool_node import ToolCallRequest
from tool.logger_handler import logger
@wrap_tool_call
def tool_monitor(request:ToolCallRequest,handler:Callable[[ToolCallRequest],ToolMessage|Command])->ToolMessage|Command:
    pass