"""
test
"""
from Agent import Agent
if __name__=='__main__':
    a=Agent()
    for content in a.stream("告诉我在LangGraph基于开发过程中需要注意的点"):
        print(content,flush=True,end='')
