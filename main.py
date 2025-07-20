from login import login
from mode import DoubaoAgent, KimiAgent


async def login_mode():
    await login()

async def test():
    # 只需登陆一次
    await login_mode()


    cfg = {
        "is_agent": "0",
        "agent_id": "",
        "agent_prompt": "你好，我由字节跳动公司开发的人工智能：豆包，咱们来闲聊一下吧。那么就让我先开启一个话题吧",
        "deep_think": "1", # 是否开启深度思考
        "mode": "k2" # 只有kimi 需要填 k1.5或k2
    }
    kimi = await KimiAgent.load(cfg,"1")

    while True:
        a = input("人类发言：")
        await kimi.send_message(a)
        kimi_message = (await kimi.wait_answer())["answer_text"]
        print(kimi_message)

if __name__ == "__main__":
    import asyncio

    
    asyncio.run(test())
