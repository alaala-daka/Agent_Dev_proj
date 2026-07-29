from langchain.agents import create_agent
from factory.model_generator import chatmodel
from agent_tools.middleware import tool_monitor,task_reflection_trigger
from agent_tools.agent_tools import search,calculator,todo,reflection,rag_summarize
from tool.prompt_loader import system_prompt_load
"""
组建Agent
"""
class Agent():
    def __init__(self) -> None:
        self.agent=create_agent(
            model=chatmodel,
            middleware=[task_reflection_trigger,tool_monitor],
            tools=[calculator,todo,search,reflection,rag_summarize],
            system_prompt=system_prompt_load()   
        )

    def stream(self,query:str):
        msg_dict={
            'messages':[
                {'role':'user','content':query}
            ]
        }
        for chunk in self.agent.stream(msg_dict,stream_mode='values'):
            mes=chunk["messages"][-1]
            if mes.content:
                yield mes.content.strip()+'\n'