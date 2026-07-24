"""
Function:文件向量化上传Chroma数据库
"""
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_deepseek import ChatDeepSeek
from tool.config_handler import Chroma_Config,Prompt_Config
from md5_tools import md5_file_check,md5_loader,md5_trans
from tool.file_handler import textloader,pdfloader,listdir_readable_file
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
    def dir_upload(self,abs_path:str):
        """
        批量上传目录中的 .txt 和 .pdf 至向量数据库。
        大文件采用生成器懒加载，分批送入 LLM，设计贴合 file_upload 模式。
        """
        if not os.path.isdir(abs_path):
            logger.error("[dir_upload] 提供路径不是目录")
            return

        readable_files=[
            os.path.join(abs_path,f)
            for f in os.listdir(abs_path)
            if f.endswith(('.txt','.pdf'))
        ]

        if not readable_files:
            logger.warning(f"[dir_upload] {abs_path} 无可读 .txt/.pdf 文件")
            return

        logger.info(f"[dir_upload] 发现 {len(readable_files)} 个文件待处理")

        total_uploaded=0
        for file_path in readable_files:
            try:
                uploaded=self._batch_upload(file_path)
                total_uploaded+=uploaded
            except Exception:
                logger.exception(f"[dir_upload] 处理 {file_path} 失败")

        logger.info(f"[dir_upload] 目录处理完成，共入库 {total_uploaded} 条")

    def _batch_upload(self,abs_path:str,pdf_pages_per_batch:int=3,txt_chars_per_batch:int=3000):
        """
        懒加载分批上传单个文件。
        生成器逐批产出内容，每批独立走「md5去重→LLM→切分→入库」流程。
        """
        file_name=os.path.basename(abs_path)
        timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # --- 1. 选择对应的懒加载生成器 ---
        if abs_path.endswith('.txt'):
            batches=self._iter_txt_batches(abs_path,txt_chars_per_batch)
        elif abs_path.endswith('.pdf'):
            batches=self._iter_pdf_batches(abs_path,pdf_pages_per_batch)
        else:
            logger.warning(f"[_batch_upload] 跳过不支持类型: {file_name}")
            return 0

        # --- 2. 逐批处理（与 file_upload 相同管线） ---
        total_chunks=0
        for batch_idx,batch_content in enumerate(batches):
            if not batch_content.strip():
                continue

            # md5 去重
            md5_val=md5_trans(batch_content)
            if md5_file_check(md5_val):
                logger.debug(f"[_batch_upload] {file_name}#{batch_idx} 已入库，跳过")
                continue

            # LLM 处理 → 切分
            res=self.chain.invoke({'input':batch_content})
            chunks=self.textsplitter.split_text(res)

            if not chunks:
                continue

            # 入库
            meta={"source":file_name,"timestamp":timestamp,"batch":batch_idx}
            batch_ids=[f"{file_name}_b{batch_idx}c{i}" for i in range(len(chunks))]
            self.chroma.add_texts(chunks,ids=batch_ids,metadatas=[meta]*len(chunks))
            md5_loader(md5_val)

            total_chunks+=len(chunks)

        logger.info(f"[_batch_upload] {file_name} → {total_chunks} chunks 入库")
        return total_chunks

    def _iter_txt_batches(self,abs_path:str,chars_per_batch:int):
        """
        生成器：逐行读取 txt，累积满 chars_per_batch 字符后产出一批。
        不将整个文件一次加载到内存。
        """
        with open(abs_path,'r',encoding='utf-8') as f:
            buffer=""
            for line in f:
                buffer+=line
                if len(buffer)>=chars_per_batch:
                    yield buffer
                    buffer=""
            if buffer.strip():
                yield buffer

    def _iter_pdf_batches(self,abs_path:str,pages_per_batch:int):
        """
        生成器：PDF 按页读取后分组，每 pages_per_batch 页拼为一批。
        """
        docs=pdfloader(abs_path)
        if not docs:
            return

        batch=[]
        for doc in docs:
            batch.append(doc.page_content)
            if len(batch)>=pages_per_batch:
                yield "\n".join(batch)
                batch=[]
        if batch:
            yield "\n".join(batch)

    def get_retriever(self):
        #提供快速入链的功能
        return self.chroma.as_retriever(search_kwargs={"k":6})