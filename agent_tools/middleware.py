"""
Agent 中间件
===========
工具调用监控 + 任务结束反思触发器
"""
from langchain.agents.middleware import wrap_tool_call, after_agent
from typing import Callable
from langchain_core.messages import HumanMessage, ToolMessage, SystemMessage, AIMessage
from langgraph.types import Command
from langchain.tools.tool_node import ToolCallRequest
from tool.logger_handler import logger

# ── 工具调用监控 ──
@wrap_tool_call
def tool_monitor(request: ToolCallRequest, handler: Callable[[ToolCallRequest], ToolMessage | Command]) -> ToolMessage | Command:
    logger.info(f"[tool_monitor] 执行工具：{request.tool_call['name']}")
    logger.info(f"[tool_monitor] 传入参数：{request.tool_call['args']}")

    try:
        result = handler(request)
        logger.info(f"[tool_monitor] 工具 {request.tool_call['name']} 调用成功")
        return result
    except Exception as e:
        logger.exception(f"[tool_monitor] 工具 {request.tool_call['name']} 调用失败，错误捕捉 {str(e)}")
        raise e


# ── 任务结束反思触发器 ──
@after_agent
def task_reflection_trigger(state, runtime) -> Command | None:
    """Agent 每次任务结束后自动提示其进行反思总结。

    检测逻辑：
    1. 如果本轮已有 ToolMessage → 判定为"执行了实质性任务"
    2. 如果最近消息不包含 reflection 调用 → 尚未反思
    3. 满足条件 → 注入一条 SystemMessage，引导 Agent 调用 reflection add
    """
    messages = state.get("messages", [])
    if not messages:
        return None

    # ── 检测本轮是否执行了实质性工具调用（只统计最近一条用户消息之后，避免历史累计）──
    turn_tool_msgs = 0
    for m in reversed(messages):
        if isinstance(m, HumanMessage) or (isinstance(m, dict) and m.get("role") == "user"):
            break
        if isinstance(m, ToolMessage):
            turn_tool_msgs += 1
    if turn_tool_msgs == 0:
        return None  # 纯聊天，不需要反思

    # ── 检测是否已经做过反思（避免循环）──
    recent_texts = []
    for m in messages[-6:]:
        if hasattr(m, "content") and m.content:
            content = m.content if isinstance(m.content, str) else str(m.content)
            recent_texts.append(content)
    recent_concat = " ".join(recent_texts).lower()

    if "reflection add" in recent_concat or "reflection_add" in recent_concat:
        return None  # 已记录反思，不再提示

    # ── 检查 Agent 是否正在调用 reflection 工具 ──
    last_ai = None
    for m in reversed(messages):
        if isinstance(m, AIMessage):
            last_ai = m
            break
    if last_ai and hasattr(last_ai, "tool_calls") and last_ai.tool_calls:
        for tc in last_ai.tool_calls:
            if tc.get("name") == "reflection":
                return None  # Agent 正在操作 reflection 工具

    # ── 注入反思提示 ──
    logger.info("[task_reflection] 检测到任务结束，注入反思提示")

    reflection_prompt = "\n".join([
        ">> 任务已完成。请花一点时间反思本次执行过程：",
        "",
        "使用 reflection add 命令记录经验教训。格式如下：",
        "  reflection add <错误描述> | <解决方案> | <Agent哲学理解> | <标签1,标签2> | <严重程度>",
        "",
        "字段说明：",
        "  - 错误描述：本次任务中遇到的错误或问题",
        "  - 解决方案：你采取的解决措施（成功或失败都值得记录）",
        "  - Agent哲学理解：你从这件事中提炼出的原则性认知，以第一人称叙述",
        "  - 标签（可选）：逗号分隔的分类，如 代码错误,逻辑缺陷,工具使用",
        "  - 严重程度（可选）：fatal / high / medium / low",
        "",
        "即使任务顺利完成，也值得记录为什么这次做对了。",
        "如果多次尝试后才解决，请记录失败路径和最终成功的转折点。",
    ])

    return Command(
        update={"messages": [SystemMessage(content=reflection_prompt)]},
        goto="model",
    )
