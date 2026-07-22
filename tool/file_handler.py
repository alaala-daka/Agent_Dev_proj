import os
import hashlib
from typing import List
from logger_handler import logger
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader,TextLoader
def get_file_md5_hex(abs_path:str):
    if not os.path.exists(abs_path):
        logger.error("未找到文件路径")
    if not os.path.isfile(abs_path):
        logger.error("所提供路径对应并非文件")

    hash_obj=hashlib.md5()
    
    chunk_size=4096
    try:    
        with open(abs_path,'rb') as f:
            chunk=f.read(chunk_size)
            while chunk:
                hash_obj.update(chunk)
                chunk=f.read(chunk_size)
            return hash_obj.hexdigest()
    except Exception as e:
        logger.exception(f'md5过程出错{str(e)}')

def listdir_readable_file(abs_path:str,type:tuple[str]):
    """
    列出当前目录中可读文件
    """
    files=[]

    if not os.path.isdir(abs_path):
        logger.error('提供路径对应不是目录')
    
    for f in os.listdir(abs_path):
        if f.endswith(type):
            files.append(os.path.join(abs_path,f))
    
    if not f:
        logger.warning('无可读文件')

    return files

def textloader(abs_path:str)->list[Document]|None:
    if abs_path.endswith('txt'):
        return TextLoader(abs_path,encoding='utf-8').load()

def pdfloader(abs_path:str)->list[Document]|None:
    if abs_path.endswith('txt'):
        return PyPDFLoader(abs_path).load()
