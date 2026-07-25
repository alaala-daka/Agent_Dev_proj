from langchain_chroma import Chroma
from file_uploader import File_Uploader
from tool.config_handler import Rag_Config,Prompt_Config
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
        self.retriever=self.get_retriever()
        self.summarize_model=ragsummarizemodel
        self.sys_prompt=open(Prompt_Config['rag_prompt_path'],'r',encoding='utf-8').read()
        self.chat_tem=ChatPromptTemplate(
            [
                ('system',self.sys_prompt),
                ('system',"[参考资料]{reference}"),
                ('human',"{input}"),
            ]
        )
        self.rag_sum_chain=self.chat_tem|prompt_check|self.summarize_model|StrOutputParser()
    def get_rag_content(self,input:str)->str:
        """
        总结Chroma库返回的内容
        """
        chroma_feedback=self.chroma.similarity_search(query=input,k=6)
        collected_feedback=''
        for doc in chroma_feedback:
            collected_feedback+=f"- {doc.page_content}\n"
        return collected_feedback
    def model_summary(self,input:str):
        reference=self.get_rag_content(input)
        summary=self.rag_sum_chain.invoke({'reference':reference,'input':input})
        return summary

Rag_Summarize=_Rag_Summarize()