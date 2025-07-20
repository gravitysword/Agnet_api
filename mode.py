import asyncio
import shutil
from playwright.async_api import async_playwright
import os

# 获取当前模块所在目录
current_dir = os.path.dirname(__file__)
js_path = os.path.join(current_dir, "a.js")

class Agent:
    def __init__(self, agent_details,index):
        # 注意重构
        self.web_url = ""
        self.name = ""

        self.agent_details = agent_details
        self.index = index

        self.browser = None
        self.context = None
        self.page = None


        self.page_size = {"width": 1000, "height": 800}


        with open(js_path,"r",encoding="utf-8") as f:
            self.copy_stop_js = f.read()

    @classmethod
    async def load(cls, agent_details,index):
        instance = cls(agent_details,index)
        # 调用异步方法进行初始化
        await instance.load_agent()
        return instance

    async def load_agent(self):
        pass

    async def wait(self, seconds=1):
        await asyncio.sleep(seconds)

    async  def login(self):
        p = await async_playwright().start()

        self.context = await p.chromium.launch_persistent_context(
            user_data_dir=f"browser/root",
            headless=False,  # 可视化调试
            args=[]  # 可添加额外启动参数
        )
        self.page = await self.context.new_page()
        await self.page.goto(self.web_url)
        input('登陆成功后，按回车键')

        await self.context.close()

    async def  scroll(self):
        await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await self.wait()

    async  def send_message_action(self, message,textarea_selector, send_button_selector):
        await self.page.fill(textarea_selector, message)
        await self.wait()
        await self.page.click(send_button_selector)
        await self.wait()

    async def wait_answer_action(self,copy_selector, copy_element=None):
        if copy_element:
            e = copy_element
        else:
            e = await self.page.wait_for_selector(copy_selector)
        await e.click()
        await self.wait()
        copy_data = await self.page.evaluate("""window.capturedText""")
        return copy_data



    async def close(self):
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        self.page = None
        self.context = None
        print(f"{self.name} 实例资源已释放")


class DoubaoAgent(Agent):
    def __init__(self, agent_details,index):
        super().__init__(agent_details,index)
        self.name = "doubao"
        self.web_url = "https://www.doubao.com/chat/"

    async def load_agent(self):
        p = await async_playwright().start()

        root = f"browser/root/"
        user_data_dir=f"browser/{self.name}/{self.index}/"
        shutil.copytree(root, user_data_dir, dirs_exist_ok=True)

        self.context = await p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,  # 可视化调试
            args=[],  # 可添加额外启动参数
            permissions=["clipboard-read"]
        )

        self.page = await self.context.new_page()
        await self.page.set_viewport_size(self.page_size)


        async def clear_context():
            e = await self.page.wait_for_selector('//button[@data-testid="bot_setting_button"]')
            await e.click()
            await asyncio.sleep(1)

            e = (await self.page.query_selector_all('//div[@class="main-title-pkMGVd"]'))[3]
            await e.click()
            e = (await self.page.query_selector_all('//button[@data-testid="bot_setting_close"]'))[0]
            await e.click()

        async def create_context():

            # 深度思考
            e = await self.page.wait_for_selector('//button[@data-testid="deep_think_select_button"]')
            await e.click()

            deep_think = await self.page.query_selector_all('//li[@role="menuitem"]')

            if self.agent_details["deep_think"] == "0":
                e = deep_think[2]
            elif self.agent_details["deep_think"] == "1":
                e = deep_think[1]
            elif self.agent_details["deep_think"] == "-1":
                e = deep_think[0]
            await e.click()



            text_zone = await self.page.query_selector('//textarea[@data-testid="chat_input_input"]')
            await text_zone.fill(self.agent_details["agent_prompt"])

            e = await self.page.query_selector('//button[@id="flow-end-msg-send"]')
            await e.click()

            pass

        if self.agent_details["is_agent"] == "1":
            await self.page.goto(self.agent_details["agent_id"])
            await clear_context()

        elif self.agent_details["is_agent"] == "0":
            await self.page.goto(self.web_url)
            await create_context()
        await self.page.add_script_tag(content=self.copy_stop_js)
        await self.wait_answer()

    async def wait_answer(self) :
        await self.wait(3)
        while True:
            stop_element = await self.page.query_selector('//div[@data-testid="chat_input_local_break_button"]')
            if "!hidden" in await stop_element.get_attribute("class"):
                break
            await self.wait()

        await self.scroll()

        answer_area = (await self.page.query_selector_all('//div[@class="container-PrUkKo"]'))[-1]

        answer = {
            "answer_text": "",
            "think_text": "",
        }


        deepthink_elements = await answer_area.query_selector_all(
            'xpath=.//div[@class="auto-hide-last-sibling-br paragraph-JOTKXA paragraph-element"]')
        for i in deepthink_elements:
            answer["think_text"] += await i.inner_text()

        answer["answer_text"] = await self.wait_answer_action('xpath=//button[@data-testid="message_action_copy"]')

        return answer

    async def send_message(self, message):
        textarea_selector = 'xpath=.//textarea[@data-testid="chat_input_input"]'
        send_button_selector = 'xpath=.//button[@data-testid="chat_input_send_button"]'
        await self.send_message_action(message, textarea_selector, send_button_selector)



class KimiAgent(Agent):
    def __init__(self, agent_details,index):
        super().__init__(agent_details,index)
        self.name = "kimi"
        self.web_url = "https://www.kimi.com/"
    async def load_agent(self):
        p = await async_playwright().start()

        root = f"browser/root/"
        user_data_dir=f"browser/{self.name}/{self.index}/"
        shutil.copytree(root, user_data_dir, dirs_exist_ok=True)

        self.context = await p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,  # 可视化调试
            args=[],  # 可添加额外启动参数
            permissions=["clipboard-read"]
        )

        self.page = await self.context.new_page()
        await self.page.set_viewport_size(self.page_size)


        async def create_context():

            e = await self.page.wait_for_selector('//div[@class="current-model"]')
            await e.click()
            kimi_mode = await self.page.wait_for_selector('//div[@class="models-container"]')
            kimi_mode = await kimi_mode.query_selector_all('xpath=./div')

            if self.agent_details["mode"] == "k1.5":
                await kimi_mode[1].click()
            elif self.agent_details["mode"] == "k2":
                await kimi_mode[0].click()


            e = await self.page.wait_for_selector('//div[@class="icon-button toolkit-trigger-btn"]')
            await e.click()

            deep_think = await self.page.query_selector_all('//div[@class="search-switch"]')
            deep_think = deep_think[1]
            a_open = await deep_think.query_selector('xpath=.//div[@class="switch-icon open"]')
            a_close = await deep_think.query_selector('xpath=.//div[@class="switch-icon"]')
            a = 1
            if a_open is None:
                a = 0
            elif a_close is None :
                a = 1

            if a^int(self.agent_details['deep_think']) == 1 :
                await deep_think.click()

            t = await self.page.query_selector('//div[@class="chat-input-editor-container"]/div')
            await t.fill( self.agent_details['agent_prompt'])

            e = await self.page.query_selector('//div[@class="send-button"]')
            await e.click()


        await self.page.goto(self.web_url)
        await create_context()
        await self.page.go_forward()

        await self.page.add_script_tag(content=self.copy_stop_js)
        await self.wait_answer()

    async def wait_answer(self):

        await self.wait(3)
        while True:

            if await self.page.query_selector('svg[name="stop"]') is None:
                break
            await self.wait()
        await self.scroll()

        answer_area = (await self.page.query_selector_all('xpath=//div[@class="chat-content-item chat-content-item-assistant"]'))[-1]
        answer = {
            "answer_text" : "",
            "think_text": "",
        }

        deepthink_elements = await answer_area.query_selector_all('.research-item-info .paragraph')
        for i in deepthink_elements:
            answer["think_text"] += await i.inner_text()


        answer["answer_text"] = await self.wait_answer_action('xpath=//div[contains(@class,"simple-button")][position() = last() - 2]')
        #print("Answer:", answer)
        return answer

    async def send_message(self, message):

        textarea_selector = '//div[@class="chat-input-editor-container"]/div'
        send_button_selector = '//div[@class="send-button"]'
        await self.send_message_action(message,textarea_selector, send_button_selector)

class QwenAgent(Agent):
    def __init__(self, agent_details,index):
        super().__init__(agent_details,index)
        self.name = "qwen"
        self.web_url = "https://www.tongyi.com/"

    async def load_agent(self):
        p = await async_playwright().start()

        root = f"browser/root/"
        user_data_dir=f"browser/{self.name}/{self.index}/"
        shutil.copytree(root, user_data_dir, dirs_exist_ok=True)

        self.context = await p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,  # 可视化调试
            args=[],  # 可添加额外启动参数
            permissions=["clipboard-read"]
        )

        self.page = await self.context.new_page()
        await self.page.set_viewport_size(self.page_size)


        async def create_context():
            if self.agent_details["deep_think"] == "1":
                await (await self.page.query_selector_all('//div[@class="tagBtn--jji85P_L hoverContainer--Yu0w7bNM"]'))[0].click()
            e = await self.page.wait_for_selector('//textarea[@class="ant-input css-1r287do ant-input-outlined textarea--FEdqShqI fadeIn--rfb4PDTu"]')
            await e.fill(self.agent_details["agent_prompt"])

            e = await self.page.wait_for_selector('//div[@class="operateBtn--qMhYIdIu"]')
            await e.click()


        await self.page.goto(self.web_url)
        await create_context()
        await self.page.go_forward()

        await self.page.add_script_tag(content=self.copy_stop_js)

        await self.wait_answer()

    async def wait_answer(self):

        await self.wait(3)
        while True:
            if await self.page.query_selector('//div[@class="operateBtn--qMhYIdIu stop--P_jcrPFo"]') is None:
                break
            await self.wait()

        await self.scroll()

        answer_area = (await self.page.query_selector_all('xpath=//div[@class="content--FOu1seVU"]'))[-1]
        answer = {
            "answer_text" : "",
            "think_text": "",
        }

        deepthink_elements = await answer_area.query_selector_all('.deepThinkContent--rWKbpkBx p')
        for i in deepthink_elements:
            answer["think_text"] += await i.inner_text()

        await self.wait()


        answer["answer_text"] =  await self.wait_answer_action('xpath=//div[@class="answerItem--Fjp8fBsN"][last()]//div[@class="tools--JSWHLNPm"]//div[contains(@class,"btn--YtZqkWMA")][3]')


        return answer

    async def send_message(self, message):

        textarea_selector = '//textarea[contains(@class,"textarea--FEdqShqI")]'
        send_button_selector = '//div[@class="operateBtn--qMhYIdIu"]'
        await self.send_message_action(message, textarea_selector, send_button_selector)

class MinimaxAgent(Agent):
    def __init__(self, agent_details,index):
        super().__init__(agent_details,index)
        self.name = "minimax"
        self.web_url = "https://chat.minimaxi.com/"

    async def load_agent(self):
        p = await async_playwright().start()

        root = f"browser/root/"
        user_data_dir = f"browser/{self.name}/{self.index}/"
        shutil.copytree(root, user_data_dir, dirs_exist_ok=True)

        self.context = await p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,  # 可视化调试
            args=[],  # 可添加额外启动参数
            permissions=["clipboard-read"]
        )

        self.page = await self.context.new_page()
        await self.page.set_viewport_size(self.page_size)


        async def create_context():
            chosen_area = 0

            if await self.page.is_visible('xpath=//div[@id="input-wrapper"][2]/div[2]/div[1]/div[2]'):
                deep_think_btn = await self.page.wait_for_selector('xpath=//div[@id="input-wrapper"][2]/div[2]/div[1]/div[2]',timeout=5000)
            else:
                deep_think_btn = await self.page.wait_for_selector('xpath=//div[@id="input-wrapper"][1]/div[2]/div[1]/div[2]', timeout=5000)

            if "text-col_text06" in await deep_think_btn.get_attribute('class'):
                a=0
            else:
                a=1

            if a^int(self.agent_details["deep_think"]):
                await deep_think_btn.click()

            await self.wait(1)

            for i in await self.page.query_selector_all('//textarea'):
                if await i.is_visible():
                    await i.fill(self.agent_details["agent_prompt"])
                    break

            await  self.wait(1)

            for i in await self.page.query_selector_all('//div[@id="input-send-icon"]'):
                if await i.is_visible():
                    await i.click()
                    break



        await self.page.goto(self.web_url)
        await create_context()
        await self.page.go_forward()

        await self.page.add_script_tag(content=self.copy_stop_js)

        await self.wait_answer()

    async def wait_answer(self):
        try:
            await self.page.click('xpath=//span[@class="absolute right-2 top-0 z-10 flex h-[56px] w-12 cursor-pointer items-center justify-center md:right-0 "]', timeout=2000)
        except :
            pass
        await self.wait(3)

        while True:
            if await self.page.query_selector('//div[@id="stop-create-btn"]') is None:
                break
            await self.wait()

        await self.scroll()

        try:
            await self.page.click('xpath=//span[@class="absolute right-2 top-0 z-10 flex h-[56px] w-12 cursor-pointer items-center justify-center md:right-0 "]', timeout=2000)
        except :
            pass

        answer = {
            "answer_text": "",
            "think_text": "",
        }
        answer_area = (await self.page.query_selector_all('xpath=//div[@class="hailuo-markdown "]'))[-1]

        try:
            deepthink_elements = (await answer_area.query_selector_all(' > div '))[0]
            for i in await deepthink_elements.query_selector_all('xpath=.//*[@class="target pending"]'):
                text = await i.evaluate("el => el.firstChild?.textContent.trim()")
                answer["think_text"] += text
        except:
            pass

        answer["answer_text"] =  await self.wait_answer_action('xpath=//div[contains(@class,"chat-card-item-wrapper")][last()]//div[contains(@class,"system-operation-box")]/div//div[1]')


        #print("Answer:", answer)
        return answer

    async def send_message(self, message):
        try:
            await self.page.click('xpath=//span[@class="absolute right-2 top-0 z-10 flex h-[56px] w-12 cursor-pointer items-center justify-center md:right-0 "]', timeout=2000)
        except :
            pass

        for i in await self.page.query_selector_all('//textarea'):
            if await i.is_visible():
                await i.fill( message)
                break

        await  self.wait(1)

        for i in await self.page.query_selector_all('//div[@id="input-send-icon"]'):
            if await i.is_visible():
                await i.click()
                break


class ChatglmAgent(Agent):
    def __init__(self, agent_details,index):
        super().__init__(agent_details,index)
        self.name = "chatglm"
        self.web_url = "https://chatglm.cn/main/alltoolsdetail?lang=zh"

    async def load_agent(self):
        p = await async_playwright().start()

        root = f"browser/root/"
        user_data_dir = f"browser/{self.name}/{self.index}/"
        shutil.copytree(root, user_data_dir, dirs_exist_ok=True)

        self.context = await p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,  # 可视化调试
            args=[],  # 可添加额外启动参数
            permissions=["clipboard-read"]
        )

        self.page = await self.context.new_page()
        await self.page.set_viewport_size(self.page_size)


        async def create_context():

            deep_think = await self.page.query_selector('xpath=//div[contains(@class, "zero-button") and contains(@class, "flex") and contains(@class, "flex-y-center") and contains(@class, "flex-x-center") and contains(@class, "el-tooltip__trigger")]')
            if "selected" in await deep_think.get_attribute("class"):
                a = 1
            else:
                a=0

            if a^int(self.agent_details['deep_think']) == 1 :
                await deep_think.click()

            t = await self.page.query_selector('//textarea')
            await t.fill( self.agent_details['agent_prompt'])

            e = await self.page.query_selector('//div[@class="enter m-three-row"]')
            await e.click()


        await self.page.goto(self.web_url)
        await create_context()
        await self.page.go_forward()

        await self.page.add_script_tag(content=self.copy_stop_js)
        await self.wait_answer()

    async def wait_answer(self):

        await self.wait(3)
        while True:
            if await self.page.query_selector('xpath=.//div[@class="enter searching"]') is None:
                break

        await self.scroll()

        answer_area = (await self.page.query_selector_all('xpath=//div[@class="code-box flex1"]'))[-1]
        answer = {
            "answer_text" : "",
            "think_text": "",
        }
        deepthink_elements = await answer_area.query_selector_all('xpath=.//div[@class="markdown-body dr_margin_botttom md-body tl"]//p')
        for i in deepthink_elements:
            answer["think_text"] += await i.inner_text()

        #await ((await self.page.query_selector_all('xpath=//div[@data-v-3f701107="" and  @data-v-2161dc6d="" and @class="copy"]'))[-1]).click()
        e = (await self.page.query_selector_all('xpath=//i[contains(@class,"copy")]'))[-1]
        answer["answer_text"] = await self.wait_answer_action("",copy_element= e)
        #print("Answer:", answer)
        return answer

    async def send_message(self, message):
        textarea_selector = '//textarea'
        send_button_selector = '//div[@class="enter m-three-row"]'

        await self.send_message_action(message, textarea_selector, send_button_selector)

class DeepseekAgent(Agent):
    def __init__(self, agent_details,index):
        super().__init__(agent_details,index)
        self.name = "deepseek"
        self.web_url = "https://chat.deepseek.com/"

    async def load_agent(self):
        p = await async_playwright().start()

        root = f"browser/root/"
        user_data_dir = f"browser/{self.name}/{self.index}/"
        shutil.copytree(root, user_data_dir, dirs_exist_ok=True)

        self.context = await p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,  # 可视化调试
            args=[],  # 可添加额外启动参数
            permissions=["clipboard-read"]
        )
        self.page = await self.context.new_page()
        await self.page.set_viewport_size(self.page_size)


        async def create_context():

            try:
                v = (await self.page.query_selector_all('xpath=.//div[@style="--ds-button-color: #DBEAFE; --button-text-color: #4D6BFE; --button-border-color: rgba(0, 122, 255, 0.15); --ds-button-hover-color: #C3DAF8;"]'))[0]
                a = 1
            except:
                a=0


            if a^int(self.agent_details['deep_think']) == 1 :
                await (await self.page.query_selector_all(".ad0c98fd"))[0].click()

            t = await self.page.query_selector('//textarea')
            await t.fill( self.agent_details['agent_prompt'])

            e = await self.page.query_selector('//div[@class="_6f28693"]')
            await e.click()


        await self.page.goto(self.web_url)
        await create_context()
        await self.page.go_forward()
        await self.page.add_script_tag(content=self.copy_stop_js)


        await self.wait_answer()

    async def wait_answer(self):

        await self.wait(5)
        while True:
            if await (await self.page.query_selector('._7436101')).get_attribute("aria-disabled") == "true":
                break
            await self.wait()

        await self.scroll()

        answer_area = await self.page.query_selector('xpath=//div[@class="_4f9bf79 d7dc56a8 _43c05b5"]')
        answer = {
            "answer_text" : "",
            "think_text": "",
        }
        try:
            deepthink_elements = await answer_area.query_selector('xpath=.//div[@class="e1675d8b"]')
            answer["think_text"] = await deepthink_elements.inner_text()
        except:
            pass

        el = (await self.page.query_selector_all('xpath=//div[@class="ds-icon-button"]'))[-4]
        answer["answer_text"] = await  self.wait_answer_action("",el)

        #print("Answer:", answer)
        return answer

    async def send_message(self, message):
        textarea_selector = '//textarea'
        send_button_selector = '//div[@class="_7436101"]'
        await self.send_message_action(message, textarea_selector, send_button_selector)

class Help:
    def __init__(self):
        self.models = [DoubaoAgent,QwenAgent,MinimaxAgent,ChatglmAgent,DeepseekAgent,KimiAgent]
        self.models_name = [model("","").name for model in self.models]
        self.func = """
        
        cfg = {
        "is_agent": "0",
        "agent_id": "",
        "agent_prompt": "你好",
        "deep_think": "1", //是否开启深度思考
        "mode": "k2"  // 只有kimi 需要填 k1.5或k2
    }
    
        mode = await DoubaoAgent().load(cfg,index)
        
        await mode.send_message(message)
        message = await mode.wait_message()
        
        
        """


