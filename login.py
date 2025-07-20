from mode import DoubaoAgent,KimiAgent,QwenAgent, MinimaxAgent,ChatglmAgent,DeepseekAgent

a = [ DoubaoAgent,KimiAgent,QwenAgent, MinimaxAgent,ChatglmAgent,DeepseekAgent]



async def login():
    for i in a:
        await i("","").login()

if __name__ == '__main__':
    import asyncio
    asyncio.run(login())
