from dotenv import load_dotenv
load_dotenv()

from langchain_community.embeddings import DashScopeEmbeddings
from langchain_deepseek import ChatDeepSeek
from tool.config_handler import  Chroma_Config,Agent_Config,Rag_Config
from abc import ABC,abstractmethod

class BaseModelGenerator(ABC):
    @abstractmethod
    def modelgenerator(self):
        pass

class EmbeddingModelGenerator(BaseModelGenerator):
    def modelgenerator(self):
        return DashScopeEmbeddings(
            model=Chroma_Config["embedding_model_name"]
        )

class ChatModelGenerator(BaseModelGenerator):
    def modelgenerator(self):
        return ChatDeepSeek(
            model=Agent_Config["chat_model_name"]
        )

class RagSummarizeModelGenerator(BaseModelGenerator):
    def modelgenerator(self):
        return ChatDeepSeek(
            model=Rag_Config["rag_summarize_model_name"]
        )

ragsummarizemodel=RagSummarizeModelGenerator().modelgenerator()
chatmodel=ChatModelGenerator().modelgenerator()
embeddingmodel=EmbeddingModelGenerator().modelgenerator()


def create_chatmodel(model_name: str | None = None):
    """工厂函数：使用指定模型名创建 ChatDeepSeek 实例（不替换模块级单例）"""
    from tool.config_handler import Agent_Config
    name = model_name or Agent_Config.get("chat_model_name", "deepseek-v4-pro")
    return ChatDeepSeek(model=name)


def get_model_info() -> dict:
    """返回当前 Agent 使用的模型信息"""
    from tool.config_handler import Agent_Config, Rag_Config, Chroma_Config
    return {
        "chat_model": Agent_Config.get("chat_model_name", "deepseek-v4-pro"),
        "rag_model": Rag_Config.get("rag_summarize_model_name", "deepseek-v4-flash"),
        "embedding_model": Chroma_Config.get("embedding_model_name", "text-embedding-v4"),
    }
