from langchain.agents import create_agent
from factory.model_generator import chatmodel
from agent_tools.middleware import tool_monitor,task_reflection_trigger
from agent_tools.agent_tools import search,calculator,todo,reflection,rag_summarize
from agent_tools.file_manage_tools import file_manage, ask_for_answer
from tool.prompt_loader import system_prompt_load
from tool.config_handler import FileManage_Config
"""
组建Agent，集成文件管理工具（支持 manual/auto 双模式）
"""
class Agent():
    def __init__(self) -> None:
        # 加载基础系统提示词并附加文件管理模式说明
        base_prompt = system_prompt_load()
        mode_section = _build_mode_section()
        full_prompt = base_prompt + "\n" + mode_section

        self.agent=create_agent(
            model=chatmodel,
            middleware=[task_reflection_trigger,tool_monitor],
            tools=[calculator,todo,search,reflection,rag_summarize,file_manage,ask_for_answer],
            system_prompt=full_prompt
        )

    def stream(self,query:str):
        msg_dict={
            'messages':[
                {'role':'user','content':query}
            ]
        }
        for chunk in self.agent.stream(msg_dict,stream_mode='values'):
            mes=chunk["messages"][-1]
            if mes.content:
                yield mes.content.strip()+'\n'


def _build_mode_section() -> str:
    """根据 FileManageConfig 中的模式，构建附加到系统提示词的模式说明"""
    mode = FileManage_Config.get("mode", "manual")
    allowed_paths = FileManage_Config.get("allowed_paths", ["."])
    blocked_patterns = FileManage_Config.get("blocked_patterns", [])

    allowed_str = ", ".join(allowed_paths)
    blocked_str = ", ".join(blocked_patterns[:10])  # 仅展示前10个

    if mode == "manual":
        section = f"""
## 文件管理模式 - 手动模式 (MANUAL)

当前文件管理处于 **手动模式**。你必须遵循以下规则：

### 操作权限
- ✅ **自由执行**（无需用户批准）: read / list / info / exists / search
- 🔐 **需用户批准**（必须先调用 ask_for_answer）: write / append / delete / mkdir

### 批准流程
1. 你调用 file_manage write/append/delete/mkdir（不加 --approved）
2. file_manage 返回预览信息和拒绝提示
3. 你根据提示调用 ask_for_answer 向用户说明操作细节
4. 用户回复后，用返回结果判断是否获批
5. 如获批: 用 **--approved** 标记重新调用 file_manage 完成操作
   格式: file_manage("write --approved <路径> | <内容>")
6. 如被拒: 放弃该操作，告知用户

### 示例
```
用户: "帮我创建一个 test.txt，内容是 hello"
Agent:
  Thought: 手动模式写文件需要批准，先预览操作。
  Action: file_manage("write test.txt | hello")
  Observation: [手动模式 - 需要用户批准] ... 请先调用 ask_for_answer ...
Agent:
  Thought: 需要获得用户批准。
  Action: ask_for_answer("是否允许在项目根目录创建 test.txt？内容: hello")
  Observation: 用户回答: yes
Agent:
  Thought: 用户已批准，执行写入。
  Action: file_manage("write --approved test.txt | hello")
  Observation: ✅ 已写入文件 ...
```

### 安全边界
- 允许操作目录: {allowed_str}
- 全局拦截模式: {blocked_str} ...
- 每次写入/删除操作都会记录到日志
"""
    else:
        section = f"""
## 文件管理模式 - 自动模式 (AUTO)

当前文件管理处于 **自动模式**。你可以较自由地执行文件 CRUD 操作，但有以下硬性限制：

### 自动模式禁止的操作
1. ❌ **禁止删除目录**（delete 仅支持删除单个文件）
2. ❌ **禁止操作系统敏感路径**: /etc/, C:\\Windows, ~/.ssh 等
3. ❌ **禁止操作匹配封锁模式的文件**: {blocked_str} ...
4. ❌ **禁止写入不允许的扩展名文件**（如 .exe, .dll）
5. ❌ **文件大小限制**: 读 {FileManage_Config.get('max_file_size_read', 1048576) // 1024 // 1024}MB / 写 {FileManage_Config.get('max_file_size_write', 5242880) // 1024 // 1024}MB

### 允许的操作
- ✅ read / list / info / exists / search: 自由查询
- ✅ write / append / delete / mkdir: 在安全边界内自由执行

### 安全边界
- 允许操作目录: {allowed_str}
- 所有操作都会被记录到日志
- 遇到被拦截的操作时，如实告知用户原因并建议手动处理

### 注意事项
- 不要删除任何看起来重要的文件
- 不确定是否安全的操作，先向用户说明
- 路径遍历攻击 (. . /) 在任何模式下都会被自动拦截
"""
    return section
