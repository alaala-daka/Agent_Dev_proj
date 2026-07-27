from tool.logger_handler import logger
from tool.config_handler import Prompt_Config

def system_prompt_load():
    try:
        with open(Prompt_Config["system_prompt_path"],'r',encoding='utf-8') as f:
            chunk=f.read()
            return chunk
    except Exception as e:
        logger.error(f"[system_prompt_load()]出现{str(e)}")
        raise e
    
def rag_prompt_load():
    try:
        with open(Prompt_Config["rag_prompt_path"],'r',encoding='utf-8') as f:
            chunk=f.read()
            return chunk
    except Exception as e:
        logger.error(f"[rag_prompt_load()]出现{str(e)}")
        raise e

def report_prompt_load():
    try:
        with open(Prompt_Config["report_prompt_path"],'r',encoding='utf-8') as f:
            chunk=f.read()
            return chunk
    except Exception as e:
        logger.error(f"[report_prompt_load()]出现{str(e)}")
        raise e
