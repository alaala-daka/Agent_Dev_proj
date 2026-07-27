from langchain_community.embeddings import DashScopeEmbeddings
from langchain_deepseek import ChatDeepSeek
from tool.config_handler import  Chroma_Config,Agent_Config,Rag_Config
from langchain_community.chat_models import moonshot
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
