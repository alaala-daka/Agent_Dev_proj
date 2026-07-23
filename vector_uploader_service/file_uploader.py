"""
Function:文件向量化上传Chroma数据库
"""
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_deepseek import ChatDeepSeek
from tool.config_handler import Chroma_Config
from md5_tools import md5_file_check,md5_loader,md5_trans
class file_uploader():
    """
    将指定目录文件上传至chroma库便于后期检索
    """
    def __init__(self) -> None:
        self.chroma=Chroma(
            collection_name=Chroma_Config['collection_name'],
            persist_directory=Chroma_Config['persist_directory'],
            embedding_function=Chroma_Config['embeddiing_model_name'],
        )
        self.splitters_model=ChatDeepSeek(
            model="deepseek-v4-flash",
        )
        self.textsplitter=RecursiveCharacterTextSplitter(
            separators=Chroma_Config['separators'],
            keep_separator=False,
            is_separator_regex=True,
            chunk_size=100,
            chunk_overlap=30,
            length_function=len,
        )

    def upload(self,abs_path:str):
