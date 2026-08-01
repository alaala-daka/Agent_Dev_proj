"""
WebSocket 聊天端点 — Agent 流式对话 + ask_for_answer 请求-响应协议

协议:
  Client → Server:
    { type: "chat", content: "..." }
    { type: "cancel" }
    { type: "user_answer", request_id: "...", answer: "approved"|"rejected", detail: "..." }
    { type: "ping" }

  Server → Client:
    { type: "chunk", content: "..." }
    { type: "tool_call", call_id: "...", tool: "...", args: {...} }
    { type: "tool_result", call_id: "...", tool: "...", result: "..." }
    { type: "tool_error", call_id: "...", tool: "...", error: "..." }
    { type: "ask_user", request_id: "...", question: "..." }
    { type: "done" }
    { type: "error", message: "..." }
    { type: "pong" }
"""
import asyncio
import json
import threading
import uuid
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage

from tool.logger_handler import logger
from Agent import Agent

router = APIRouter()

# ── Agent 实例缓存（按 session_id）──
_agents: dict[str, Agent] = {}
_lock = threading.Lock()


def _get_or_create_agent(session_id: str | None) -> Agent:
    """获取或创建 Agent 实例"""
    if session_id:
        with _lock:
            if session_id not in _agents:
                _agents[session_id] = Agent(session_id=session_id)
            return _agents[session_id]
    return Agent()  # ephemeral


# ── ask_for_answer 的 WebSocket 适配 ──

# 全局映射: request_id → asyncio.Event
_pending_requests: dict[str, asyncio.Event] = {}
_pending_results: dict[str, str] = {}


async def _websocket_ask_user(ws: WebSocket, question: str) -> str:
    """
    替代 input() 的 ask_for_answer 实现。
    通过 WebSocket 向客户端发送确认请求，等待用户回答后返回。
    """
    request_id = uuid.uuid4().hex[:12]
    event = asyncio.Event()
    _pending_requests[request_id] = event

    await ws.send_json({
        "type": "ask_user",
        "request_id": request_id,
        "question": question,
    })

    # 等待客户端回答（带超时 5 分钟）
    try:
        await asyncio.wait_for(event.wait(), timeout=300.0)
    except asyncio.TimeoutError:
        _pending_requests.pop(request_id, None)
        _pending_results.pop(request_id, None)
        return "用户回答: 超时未响应，操作视为被拒绝。"

    answer = _pending_results.pop(request_id, "用户取消输入，操作视为被拒绝。")
    _pending_requests.pop(request_id, None)
    return answer


def resolve_user_answer(request_id: str, answer: str):
    """由 WebSocket 消息处理调用：解析用户回答并恢复等待的协程"""
    _pending_results[request_id] = answer
    event = _pending_requests.get(request_id)
    if event:
        event.set()


# ── 工具包装：将 ask_for_answer 的 input() 替换为 WebSocket 版本 ──

def _wrap_input_for_websocket(ws: WebSocket):
    """
    通过 monkey-patch input() 将 ask_for_answer 重定向到 WebSocket。
    LangGraph 编译后的 graph 不直接暴露 .tools 属性，
    所以我们直接 patch builtins.input 即可——所有工具共享同一个 input()。
    """
    import builtins
    original_input = builtins.input

    def ws_input(prompt: str = "") -> str:
        """同步包装器：在事件循环中运行异步 ask_user"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        if loop.is_running():
            # 从同步上下文中调用异步 — 创建新任务等待
            future = asyncio.run_coroutine_threadsafe(
                _websocket_ask_user(ws, prompt), loop
            )
            return future.result(timeout=310)
        else:
            return loop.run_until_complete(_websocket_ask_user(ws, prompt))

    builtins.input = ws_input
    return original_input


def _unwrap_input(original_input):
    """恢复原始 input() 函数"""
    import builtins
    builtins.input = original_input


# ── WebSocket 端点 ──

@router.websocket("/ws/chat/{session_id}")
async def websocket_chat(ws: WebSocket, session_id: str):
    await ws.accept()
    logger.info(f"[chat] WebSocket 连接: session={session_id}")

    # 处理特殊 session_id
    agent_sid = None if session_id in ("_ephemeral", "null", "undefined") else session_id
    agent = _get_or_create_agent(agent_sid)
    original_input = None
    cancel_event = asyncio.Event()

    try:
        # 发送当前会话信息
        await ws.send_json({
            "type": "session_info",
            "session_id": agent.session_id or "ephemeral",
            "message_count": len(agent.messages),
        })

        while True:
            data = await ws.receive_json()
            msg_type = data.get("type", "")

            if msg_type == "chat":
                content = data.get("content", "")
                if not content.strip():
                    continue

                # 包装 input() 为 WebSocket 版本
                original_input = _wrap_input_for_websocket(ws)
                cancel_event.clear()

                try:
                    # 在单独的线程中运行 Agent.stream（因为它是同步生成器）
                    # 同时监听取消信号
                    chunks = []
                    stream_finished = False

                    def run_stream():
                        nonlocal stream_finished
                        try:
                            user_query = content.strip()
                            saw_first = False
                            for chunk in agent.stream(content):
                                if cancel_event.is_set():
                                    break
                                c = chunk.strip()
                                # 跳过模型回显的用户输入（第一个非空 chunk 可能与 query 相同或以 query 开头）
                                if not saw_first and c:
                                    saw_first = True
                                    if c == user_query or c.startswith(user_query):
                                        logger.info(f"[chat] 跳过回显: {c[:80]}")
                                        continue
                                chunks.append(chunk)
                            stream_finished = True
                        except Exception as e:
                            logger.exception(f"[chat] Agent 流错误")
                            chunks.append(json.dumps({"type": "error", "message": str(e)}))

                    stream_thread = threading.Thread(target=run_stream)
                    stream_thread.start()

                    # 等待流完成或取消
                    while stream_thread.is_alive():
                        # 检查是否有新的 chunks
                        while chunks:
                            chunk = chunks.pop(0)
                            try:
                                msg = json.loads(chunk)
                                await ws.send_json(msg)
                            except (json.JSONDecodeError, TypeError):
                                # 纯文本块
                                await ws.send_json({
                                    "type": "chunk",
                                    "content": chunk.strip(),
                                })
                        await asyncio.sleep(0.05)

                    # 处理剩余 chunks
                    while chunks:
                        chunk = chunks.pop(0)
                        try:
                            msg = json.loads(chunk)
                            await ws.send_json(msg)
                        except (json.JSONDecodeError, TypeError):
                            await ws.send_json({
                                "type": "chunk",
                                "content": chunk.strip(),
                            })

                    if cancel_event.is_set():
                        await ws.send_json({"type": "interrupted"})
                    else:
                        await ws.send_json({"type": "done"})

                finally:
                    if original_input:
                        _unwrap_input(original_input)
                        original_input = None

            elif msg_type == "cancel":
                cancel_event.set()
                await ws.send_json({"type": "done"})

            elif msg_type == "user_answer":
                request_id = data.get("request_id", "")
                answer = data.get("answer", "rejected")
                detail = data.get("detail", "")
                result = f"用户回答: {answer}"
                if detail:
                    result += f" —— {detail}"
                resolve_user_answer(request_id, result)

            elif msg_type == "ping":
                await ws.send_json({"type": "pong"})

    except WebSocketDisconnect:
        logger.info(f"[chat] WebSocket 断开: session={session_id}")
    except Exception as e:
        logger.exception(f"[chat] WebSocket 异常: session={session_id}")
        try:
            await ws.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass
    finally:
        if original_input:
            _unwrap_input(original_input)
        # 保存会话状态
        if agent.session_id:
            try:
                agent._save_session_state()
            except Exception:
                pass
