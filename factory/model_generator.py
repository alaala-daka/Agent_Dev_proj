from langchain_community.embeddings import DashScopeEmbeddings
from langchain_deepseek import ChatDeepSeek
from tool.config_handler import  Chroma_Config,Agent_Config
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
    def chatmodelgenerator(self):
        return ChatDeepSeek(
            model=Agent_Config["chat_model_name"]
        )

