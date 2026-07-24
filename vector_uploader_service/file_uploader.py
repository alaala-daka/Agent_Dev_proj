"""
Function:文件向量化上传Chroma数据库
"""
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_deepseek import ChatDeepSeek
from tool.config_handler import Chroma_Config,Prompt_Config
from md5_tools import md5_file_check,md5_loader,md5_trans
from tool.file_handler import textloader,pdfloader
from tool.logger_handler import logger
from langchain_core.prompts import SystemMessagePromptTemplate,ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import datetime
import os

#def spliter_model prompt
sys_prompt=SystemMessagePromptTemplate.from_template_file(Prompt_Config["spliter_prompt_path"],input_variables=[])

class file_uploader():
    """
    将指定目录文件上传至chroma库便于后期检索
    """
    def __init__(self) -> None:
        self.chroma=Chroma(
            collection_name=Chroma_Config['collection_name'],
            persist_directory=Chroma_Config['persist_directory'],
            embedding_function=DashScopeEmbeddings(
                model=Chroma_Config['embeddiing_model_name']
                )
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
        self.chain = (
        ChatPromptTemplate([sys_prompt, ('human', '{input}')])
        | self.splitters_model
        | StrOutputParser()
    )

    def file_upload(self,abs_path:str):
        """
        上传本地文件至向量数据库
        """

        docs=[]
        upload_content=''
        if abs_path.endswith('txt'):
            docs=textloader(abs_path)
            if docs:
                upload_content=docs[0].page_content
            else: 
                logger.error("未能读取.txt文件内容")
                return
        elif abs_path.endswith('pdf'):
            docs=pdfloader(abs_path)
            if docs:
                upload_content='\n'.join(doc.page_content for doc in docs)
        if not docs:
            logger.error("[file_upload]所提供链接无可识别上传文件，文件应为pdf或txt，或者提供链接无效")
            return
        md5_val=md5_trans(upload_content)
        if md5_file_check(md5_val):
            logger.info('[file_upload]所提供文件已被存储')
            return
        res=self.chain.invoke({'input':upload_content})
        content_processed=self.textsplitter.split_text(res)
        metadatas={"source":os.path.basename(abs_path) or None,"timestamp":datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        self.chroma.add_texts(content_processed,ids=[f'{os.path.basename(abs_path)}id{num}' for num in range(1,len(content_processed)+1)],metadatas=[metadatas for _ in range(0,len(content_processed))])
        logger.info(f'[file_upload]{abs_path}对应文件被成功储存')
        md5_loader(md5_val)
    def dir_upload(self,abs_path):
        pass

    def get_retriever(self):
        #提供快速入链的功能
        return self.chroma.as_retriever(search_kwargs={"k":6})