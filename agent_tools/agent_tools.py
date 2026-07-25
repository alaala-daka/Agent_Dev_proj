"""
Agent工具实现
"""
from langchain_core.tools import tool
from tavily import TavilyClient
from tool.config_handler import System_Config

"""
Travily网络搜索工具
"""
@tool(description="网络搜索工具，用于搜索具有时效性知识和知识库以外的知识，输入为你要查询的问题字符串")
def search(query:str)->str:
    tavily_client=TavilyClient(
        api_key=System_Config["tavily_api_key"],
    )
    response=tavily_client.search(query=query,search_depth='basic',topic='general',max_results=4)
    search_content=''
    for res in response["results"]:
        search_content+=res['title']+'\n'
        search_content+=res['content']+'\n'
    return search_content

"""
计算器工具 — 基于AST的安全表达式求值
"""
import ast
import math
import operator

# 安全求值器：仅允许白名单内的节点和运算符，避免 eval 的安全风险
_SAFE_OPS = {
    ast.Add:      operator.add,
    ast.Sub:      operator.sub,
    ast.Mult:     operator.mul,
    ast.Div:      operator.truediv,
    ast.Pow:      operator.pow,
    ast.USub:     operator.neg,
    ast.UAdd:     operator.pos,
    ast.Mod:      operator.mod,
    ast.FloorDiv: operator.floordiv,
}

_SAFE_FUNCS = {
    "abs":    abs,
    "round":  round,
    "min":    min,
    "max":    max,
    "sum":    sum,
    "pow":    pow,
    "sqrt":   math.sqrt,
    "log":    math.log,
    "log10":  math.log10,
    "log2":   math.log2,
    "exp":    math.exp,
    "sin":    math.sin,
    "cos":    math.cos,
    "tan":    math.tan,
    "asin":   math.asin,
    "acos":   math.acos,
    "atan":   math.atan,
    "pi":     math.pi,
    "e":      math.e,
    "ceil":   math.ceil,
    "floor":  math.floor,
    "factorial": math.factorial,
    "gcd":    math.gcd,
    "radians": math.radians,
    "degrees": math.degrees,
}


def _safe_eval(node: ast.AST) -> float:
    """递归遍历 AST 节点，仅计算白名单内的运算"""
    if isinstance(node, ast.Expression):
        return _safe_eval(node.body)

    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return float(node.value)
        raise ValueError(f"不支持的常量类型: {type(node.value).__name__}")

    if isinstance(node, ast.BinOp) and type(node.op) in _SAFE_OPS:
        left = _safe_eval(node.left)
        right = _safe_eval(node.right)
        return _SAFE_OPS[type(node.op)](left, right)

    if isinstance(node, ast.UnaryOp) and type(node.op) in _SAFE_OPS:
        return _SAFE_OPS[type(node.op)](_safe_eval(node.operand))

    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        name = node.func.id
        if name in _SAFE_FUNCS:
            args = [_safe_eval(a) for a in node.args]
            return _SAFE_FUNCS[name](*args)

    raise ValueError(f"表达式包含不支持的操作: {ast.dump(node)}")


@tool(description="""安全计算器工具，基于AST白名单求值，支持以下运算和函数：

运算符: + - * / // % ** （及正负号 +x / -x）
常量: pi, e
基础: abs, round, min, max, sum, pow, sqrt
指数对数: exp, log, log2, log10
三角: sin, cos, tan, asin, acos, atan
取整: ceil, floor
数论/转换: factorial, gcd, radians, degrees

输入为一个数学表达式字符串，例如 '3+5*2'、'sqrt(16)+log(e)'、'sin(pi/2)'、'ceil(3.14)'""")
def calculator(expression: str) -> str:
    try:
        tree = ast.parse(expression.strip(), mode="eval")
        result = _safe_eval(tree)
        # 结果若为整数则去掉小数点后缀
        if isinstance(result, float) and result == int(result) and not math.isinf(result):
            result = int(result)
        return str(result)
    except SyntaxError:
        return f"错误: 表达式语法无效 —— '{expression}'"
    except (ValueError, ZeroDivisionError, OverflowError) as e:
        return f"错误: {e}"

"""
待办清单工具 — 支持 Agent 自主管理任务计划与执行进度
"""
from datetime import datetime
from typing import Any

# 内存存储：任务列表，每条记录为 {"id", "title", "desc", "status", "created_at", "done_at"}
_TODOS: list[dict[str, Any]] = []
_TODO_ID_COUNTER = 0

_STATUS_ICON = {
    "pending":     "⬜",
    "in_progress": "🔄",
    "done":        "✅",
}


def _format_todos(todos: list[dict[str, Any]]) -> str:
    """将任务列表格式化为 Agent 友好的文本"""
    if not todos:
        return "（空）暂无待办事项。"

    total = len(todos)
    done_count = sum(1 for t in todos if t["status"] == "done")
    progress = f"{done_count}/{total}"

    lines = [f"📋 待办清单 [{progress} 已完成]", "─" * 36]
    for t in todos:
        icon = _STATUS_ICON.get(t["status"], "❓")
        line = f"  {icon} [{t['id']}] {t['title']}"
        if t.get("desc"):
            line += f"\n       └ {t['desc']}"
        if t["status"] == "done" and t.get("done_at"):
            line += f"  ✓{t['done_at']}"
        lines.append(line)
    return "\n".join(lines)


@tool(description="""待办清单工具，用于记录和追踪任务计划与执行进度。

操作命令（输入以下格式的字符串）：
  add <标题>                    → 添加新任务
  add <标题> | <描述>           → 添加带描述的任务
  list [all|pending|done]       → 列出任务（默认 all）
  doing <id>                    → 将任务标记为"进行中"
  done <id>                     → 将任务标记为"已完成"
  delete <id>                   → 删除任务
  clear done                    → 清除所有已完成任务
  reset                         → 清空全部任务

示例：'add 实现登录模块 | 含OAuth和JWT两种方式'、'list pending'、'done 3'""")
def todo(command: str) -> str:
    global _TODO_ID_COUNTER

    cmd = command.strip()
    if not cmd:
        return "错误: 请输入操作命令，例如 'list' 或 'add 任务名称'"

    parts = cmd.split(maxsplit=1)
    action = parts[0].lower()
    arg = parts[1] if len(parts) > 1 else ""

    # ── add ──
    if action == "add":
        if not arg:
            return "错误: 用法 'add <标题>' 或 'add <标题> | <描述>'"
        if "|" in arg:
            title, _, desc = arg.partition("|")
            title, desc = title.strip(), desc.strip()
        else:
            title, desc = arg, ""
        _TODO_ID_COUNTER += 1
        item = {
            "id": _TODO_ID_COUNTER,
            "title": title,
            "desc": desc,
            "status": "pending",
            "created_at": datetime.now().strftime("%m-%d %H:%M"),
            "done_at": None,
        }
        _TODOS.append(item)
        return f"✅ 已添加任务 [{item['id']}] {title}" + (f"\n   描述: {desc}" if desc else "")

    # ── list ──
    if action == "list":
        filter_status = arg.lower() if arg else "all"
        if filter_status in ("pending", "in_progress", "done"):
            filtered = [t for t in _TODOS if t["status"] == filter_status]
        else:
            filtered = _TODOS
        return _format_todos(filtered)

    # ── done / doing ──
    if action in ("done", "doing"):
        if not arg:
            return f"错误: 用法 '{action} <任务ID>'"
        try:
            tid = int(arg)
        except ValueError:
            return f"错误: 任务ID必须是数字，收到 '{arg}'"
        for t in _TODOS:
            if t["id"] == tid:
                if action == "done":
                    t["status"] = "done"
                    t["done_at"] = datetime.now().strftime("%m-%d %H:%M")
                    return f"✅ 任务 [{tid}] {t['title']} 已完成。"
                else:
                    t["status"] = "in_progress"
                    return f"🔄 任务 [{tid}] {t['title']} 标记为进行中。"
        return f"错误: 未找到ID为 {tid} 的任务"

    # ── delete ──
    if action == "delete":
        if not arg:
            return "错误: 用法 'delete <任务ID>'"
        try:
            tid = int(arg)
        except ValueError:
            return f"错误: 任务ID必须是数字，收到 '{arg}'"
        for i, t in enumerate(_TODOS):
            if t["id"] == tid:
                removed = _TODOS.pop(i)
                return f"🗑 已删除任务 [{tid}] {removed['title']}。"
        return f"错误: 未找到ID为 {tid} 的任务"

    # ── clear done ──
    if action == "clear" and arg.lower() == "done":
        before = len(_TODOS)
        _TODOS[:] = [t for t in _TODOS if t["status"] != "done"]
        removed = before - len(_TODOS)
        return f"🗑 已清除 {removed} 条已完成任务。"

    # ── reset ──
    if action == "reset":
        count = len(_TODOS)
        _TODOS.clear()
        _TODO_ID_COUNTER = 0
        return f"🗑 已清空全部 {count} 条任务。"

    return f"错误: 未知操作 '{action}'。支持: add / list / doing / done / delete / clear done / reset"
