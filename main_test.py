"""
Agent test
"""
from dotenv import load_dotenv
load_dotenv()

from Agent import Agent
if __name__=='__main__':
    a=Agent()
    while True:
        user_mess=input("User_input(输入'quit'退出本轮对话): ")
        if 'quit' in user_mess:
            break
        for content in a.stream(user_mess):
            print(content,flush=True,end='')
    print("本轮对话结束")