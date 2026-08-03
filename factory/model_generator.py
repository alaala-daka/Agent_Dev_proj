from dotenv import load_dotenv
load_dotenv()

from langchain_community.embeddings import DashScopeEmbeddings
from langchain_deepseek import ChatDeepSeek
from langchain_openai import ChatOpenAI
from tool.config_handler import  Chroma_Config,Agent_Config,Rag_Config,Model_Config
from tool.logger_handler import logger
from abc import ABC,abstractmethod

class BaseModelGenerator(ABC):
    @abstractmethod
    def modelgenerator(self):
        pass


def _active_model_entry() -> dict | None:
    """返回 Model_Config 注册表中 active_model 指向的模型项；取不到则回退第一项"""
    active = Model_Config.get("active_model")
    models = Model_Config.get("models") or []
    for m in models:
        if m.get("name") == active:
            return m
    return models[0] if models else None


def _build_chat(model_name: str, base_url: str, api_key: str):
    """按配置构建聊天模型实例。

    base_url 非空 → 任意 OpenAI 兼容端点（ChatOpenAI，可配 url + apikey + 模型名）；
    base_url 为空   → 内置 DeepSeek 路径（ChatDeepSeek 走环境变量 DEEPSEEK_API_KEY）。
    注意：必须用 base_url= 参数，api_base= 是 Pydantic alias 之外的名字，不会生效。
    """
    model_name = model_name or "deepseek-v4-pro"
    base_url = (base_url or "").strip()
    api_key = (api_key or "").strip()
    if base_url:
        # 本地端点（如 Ollama）可能不需要 key → 传占位符避免构造失败
        return ChatOpenAI(model=model_name, base_url=base_url, api_key=api_key or "not-needed")
    return ChatDeepSeek(model=model_name)


class EmbeddingModelGenerator(BaseModelGenerator):
    def modelgenerator(self):
        return DashScopeEmbeddings(
            model=Chroma_Config["embedding_model_name"]
        )

class ChatModelGenerator(BaseModelGenerator):
    def modelgenerator(self):
        return create_chatmodel()

class RagSummarizeModelGenerator(BaseModelGenerator):
    def modelgenerator(self):
        return create_ragmodel()


def create_chatmodel(model_name: str | None = None):
    """工厂函数：按 Model_Config 当前 active 模型构建主对话模型（每次读取最新配置）。
    不替换模块级单例，仅用于按需创建。
    """
    entry = _active_model_entry()
    name = model_name or (
        entry.get("model") if entry else Agent_Config.get("chat_model_name", "deepseek-v4-pro")
    )
    return _build_chat(
        name,
        entry.get("base_url", "") if entry else "",
        entry.get("api_key", "") if entry else "",
    )


def create_ragmodel():
    """工厂函数：按 Model_Config 当前 active 模型构建 RAG 总结/切分模型"""
    entry = _active_model_entry()
    name = (
        entry.get("model") if entry
        else Rag_Config.get("rag_summarize_model_name", "deepseek-v4-flash")
    )
    return _build_chat(
        name,
        entry.get("base_url", "") if entry else "",
        entry.get("api_key", "") if entry else "",
    )


ragsummarizemodel=RagSummarizeModelGenerator().modelgenerator()
chatmodel=ChatModelGenerator().modelgenerator()
embeddingmodel=EmbeddingModelGenerator().modelgenerator()


def get_model_info() -> dict:
    """返回当前 Agent 使用的模型信息"""
    entry = _active_model_entry()
    name = entry.get("model") if entry else Agent_Config.get("chat_model_name", "deepseek-v4-pro")
    base_url = (entry.get("base_url", "") if entry else "") or "env:DEEPSEEK_API_KEY"
    return {
        "chat_model": name,
        "provider": "ChatOpenAI" if (entry and (entry.get("base_url") or "").strip()) else "ChatDeepSeek",
        "base_url": base_url,
        "rag_model": name,
        "embedding_model": Chroma_Config.get("embedding_model_name", "text-embedding-v4"),
    }


def rebuild_singletons() -> None:
    """配置变更后重建全部模型单例，并重绑消费方模块的 import 别名。

    永远新建对象再重绑名字，绝不修改旧对象——进行中的 WebSocket 持有自己的
    agent 局部引用，其流与保存不受影响。
    """
    global chatmodel, ragsummarizemodel
    chatmodel = create_chatmodel()
    ragsummarizemodel = create_ragmodel()

    # 1) Agent 模块在 import 时绑定的是 mg.chatmodel → 必须同步重绑，
    #    否则 Agent.__init__ 与 _generate_title 读到的还是旧模型。
    import Agent as agent_mod
    agent_mod.chatmodel = chatmodel

    # 2) RAG 服务：重建单例并同步 agent_tools 的 import 别名。
    #    较重（重开 Chroma），失败不阻断切换。
    try:
        import vector_uploader_service.rag_summarize as rs
        rs.ragsummarizemodel = ragsummarizemodel
        rs.Rag_Summarize = rs._Rag_Summarize()
        import agent_tools.agent_tools as at
        at.Rag_Summarize = rs.Rag_Summarize
    except Exception as e:
        logger.warning(f"[model] RAG 服务重建失败: {e}")

    # 3) file_uploader 单例重建（api/files.py 每次上传新建 File_Uploader，此项可选）
    try:
        import vector_uploader_service.file_uploader as fu
        fu._file_upload_service = fu.File_Uploader()
    except Exception as e:
        logger.warning(f"[model] file_uploader 重建失败: {e}")


def apply_model_change() -> dict:
    """模型配置变更后的完整生效流程：重读配置 → 重建单例 → 驱逐 Agent 缓存。

    调用方（api/models.py）负责先持久化 ModelConfig.yml。
    """
    from tool.config_handler import reload_model_config
    reload_model_config()
    rebuild_singletons()
    from api.chat import evict_all_agents_for_model_change
    evict_all_agents_for_model_change()
    return get_model_info()
