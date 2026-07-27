"""
Agent test
"""
from dotenv import load_dotenv
load_dotenv()

from Agent import Agent
if __name__=='__main__':
    a=Agent()
    for content in a.stream("客观叙述符号主义在人工智能领域发展的影响"):
        print(content,flush=True,end='')
