import yaml
import os
from tool.path_tool import get_abs_path

def RagLoadConfig(abs_path:str|None=None,encoding='utf-8'):
    if not abs_path:
        abs_path=get_abs_path("config/RagConfig.yml")
    with open(abs_path,'r',encoding=encoding) as f:
        return yaml.load(f,Loader=yaml.FullLoader)

def PromptLoadConfig(abs_path:str|None=None,encoding='utf-8'):
    if not abs_path:
        abs_path=get_abs_path("config/PromptConfig.yml")
    with open(abs_path,'r',encoding=encoding) as f:
        return yaml.load(f,Loader=yaml.FullLoader)
    
def AgentLoadConfig(abs_path:str|None=None,encoding='utf-8'):
    if not abs_path:
        abs_path=get_abs_path("config/AgentConfig.yml")
    with open(abs_path,'r',encoding=encoding) as f:
        return yaml.load(f,Loader=yaml.FullLoader)
    
def ChromaLoadConfig(abs_path:str|None=None,encoding='utf-8'):
    if not abs_path:
        abs_path=get_abs_path("config/ChromaConfig.yml")
    with open(abs_path,'r',encoding=encoding) as f:
        return yaml.load(f,Loader=yaml.FullLoader)

def SystemLoadConfig(abs_path:str|None=None,encoding='utf-8'):
    if not abs_path:
        abs_path=get_abs_path("config/SystemConfig.yml")
    with open(abs_path,'r',encoding=encoding) as f:
        return yaml.load(f,Loader=yaml.FullLoader)

def FileManageLoadConfig(abs_path:str|None=None,encoding='utf-8'):
    if not abs_path:
        abs_path=get_abs_path("config/FileManageConfig.yml")
    with open(abs_path,'r',encoding=encoding) as f:
        return yaml.load(f,Loader=yaml.FullLoader)

Rag_Config=RagLoadConfig()
Prompt_Config=PromptLoadConfig()
Chroma_Config=ChromaLoadConfig()
Agent_Config=AgentLoadConfig()
System_Config=SystemLoadConfig()
FileManage_Config=FileManageLoadConfig()

if __name__=='__main__':
    #module_test
    print(Rag_Config["embedding_model_name"])