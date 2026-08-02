from langchain_chroma import Chroma
from vector_uploader_service.file_uploader import File_Uploader
from tool.config_handler import Rag_Config,Prompt_Config
from tool.path_tool import get_abs_path
from factory.model_generator import ragsummarizemodel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
"""
筛选Chroma库返回结果,总结并以string反馈
"""
def prompt_check(mes):
    print('='*20)
    print(mes.to_string())
    print('='*20)
    return mes
class _Rag_Summarize(File_Uploader):
    def __init__(self) -> None:
        super().__init__()
        self.retriever=self.get_retriever()
        self.summarize_model=ragsummarizemodel
        rag_prompt_path = get_abs_path(Prompt_Config['rag_prompt_path'])
        self.sys_prompt=open(rag_prompt_path,'r',encoding='utf-8').read()
        self.chat_tem=ChatPromptTemplate(
            [
                ('system',self.sys_prompt),
                ('system',"[参考资料]{reference}"),
                ('human',"{input}"),
            ]
        )
        self.rag_sum_chain=self.chat_tem|self.summarize_model|StrOutputParser()
    def get_rag_content(self,input:str)->str:
        """
        总结Chroma库返回的内容
        """
        chroma_feedback=self.chroma.similarity_search(query=input,k=4)
        collected_feedback=''
        for doc in chroma_feedback:
            collected_feedback+=f"- {doc.page_content}\n"
        return collected_feedback
    def model_summary(self,input:str):
        reference=self.get_rag_content(input)
        summary=self.rag_sum_chain.invoke({'reference':reference,'input':input})
        return summary

Rag_Summarize=_Rag_Summarize()