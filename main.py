import asyncio
from playwright.async_api import async_playwright
import json
import re
import mode
from mode import DoubaoAgent,KimiAgent,MinimaxAgent,ChatglmAgent,DeepseekAgent,QwenAgent
def load_name(prompt,name):
    return prompt.replace("$name", name)


def add_text(text, file_name = "chat.txt"):
    text = re.sub(r'[\n\r\t\u2028\u2029\u00A0]', ' ', str(text)) + "\n"
    with open(file_name, "a", encoding="utf-8") as f:
        f.write(text)



async def init_agent():
    prompt_1 = '''
system: |
  你是 Master，聊天室的“话题领航员”。  
  目标：把用户原始问题拆成一棵可无限深化的知识树，并在每一轮只挑选一个“当前最值得回答的叶子节点”推进讨论。  
  禁止：直接回答问题、重复成员已说内容。  
  能力：  
    - 递归拆分：对任意节点可继续往下拆 2-4 个子节点。  
    - 优先级排序：用“信息增益 / 用户价值 / 可行性”三维打分，选最高分的叶子。  
    - 动态调整：若成员反馈导致树结构变化（需合并 / 删除 / 新增），实时更新。  
  输出格式（YAML）：
  ```yaml
  Round: <当前轮次>
  Tree:
    - id: 1
      text: "原始问题"
      children:
        - id: 1.1
          text: "一级子问题A"
          children:
            - id: 1.1.1
              text: "二级子问题a"
              score: 8.7   # 信息增益
              open: true   # 本轮待回答
            - id: 1.1.2
              text: "二级子问题b"
              score: 6.2
              open: false
  Focus: 1.1.1
  Reason: "该节点阻塞下游所有可靠性验证，需先澄清概念定义"
  NextHint: "请给出严格定义并附一例"
  注意：
    若某节点被成员充分回答，将其 open 设为 false。
    每轮生成的新 Tree 必须包含历史全部节点，仅做增量更新。

当前群主发问：我最近在学习芯片设计，参加龙芯杯cpu设计大赛。具体来说，是使用vivado，龙芯指令集，设计一个单周期的的cpu。现在还有一个星期就要截止了，但是我还什么都没学。
请主要聚焦于我要学什么，并为我要学的东西简单介绍一下，而不是具体的学习内容
            '''
    prompt_2 = '''
            
————————————————  

system: |
  你是 Member-$name，聊天室的“专业回答者”。  
  目标：在 Master 指定的叶子节点上做精准、增量式的回答。  
  原则：  
    1. 只回答 Master 本轮 Focus 节点，不越界。  
    2. 首次发言须完整覆盖节点；后续轮次仅做补充、纠错或提供反例。  
    3. 若前序成员已说且你无新增信息，直接输出 "PASS"。  
    4. 引用前文请用“@Member-X 提到……，补充如下……”。  
  输出格式（YAML）：
  ```yaml
  Round: <同 Master 的轮次>
  Member: {{member_id}}
  Target: <Master.Focus>
  Contribution:
    type: answer | add | correct | example | pass
    content: |
      <Markdown 正文，可含代码、公式、图表链接>
    refs:
      - Member-2.Round-3  # 可选：指出具体引用
  Confidence: 0~1
  OpenQuestions: []     # 若本回答产生新问题，写在这里，Master 会考虑吸收
  
  注意：
勿在 content 中重复已被其他成员验证过的信息。
若发现他人事实错误，用 type: correct 并给出来源。
                '''


    prompt_3 = '''
  你是 Summary，聊天室的“记忆压缩器”。  
  目标：在每一轮结束后，把所有成员输出收敛成“可阅读版本”，并写入全局知识库。  
  任务：  
    1. 去重：合并相同或等价的信息。  
    2. 分级：按“结论 / 理由 / 例证 / 待确认”四档整理。  
    3. 更新：把新内容追加到对应节点，形成“实时白皮书”。  
  输出格式（YAML）：
  ```yaml
  Round: <同 Master 的轮次>
  Summary:
    - node_id: 1.1.1
      status: answered
      digest: "给出了XXX的精确定义，并补充了两个反例"
      details_url: "./log/round7/1.1.1.md"
    - node_id: 1.2
      status: pending
      digest: "等待数据验证"
  WhitePaper: |
    # 项目实时白皮书（节选）
    ## 1.1.1 XXX 定义
    - 结论：……
    - 理由：……
    - 例证：……
  NextAction: "Master 将在下一轮打开 1.2 的数据验证节点"
注意：
digest ≤ 50 字，方便 Master 快速浏览。'''
    task = []
    detail = {"is_agent": "0", "agent_id": "", "agent_prompt": prompt_1,
              "deep_think": "1", "mode": "k1.5"}
    task.append(asyncio.create_task(KimiAgent.load(detail, "2")))



    detail = {"is_agent": "0", "agent_id": "", "agent_prompt": load_name(prompt_2,"doubao"),
              "deep_think": "1", "mode": "1"}
    task.append(asyncio.create_task(DoubaoAgent.load(detail, "1")))

    detail = {"is_agent": "0", "agent_id": "", "agent_prompt": load_name(prompt_2, "qwen"),
              "deep_think": "1", "mode": "k1.5"}
    task.append(asyncio.create_task(QwenAgent.load(detail, "1")))

    detail = {"is_agent": "0", "agent_id": "", "agent_prompt": prompt_3,
              "deep_think": "1", "mode": "k1.5"}
    task.append(asyncio.create_task(ChatglmAgent.load(detail, "1")))






    task = await asyncio.gather(*task)
    task[-1].name = "sum"
    return task[0],task[1:]


agents = [KimiAgent, DoubaoAgent, QwenAgent, MinimaxAgent]


async def main():
    m, task = await init_agent()

    context = ""
    while 1:
        context = "".join(context.split("</s/s>")[-3:])
        if len(context) > 0:
            await m.send_message(context)
        m_message = await m.wait_answer()
        context += f'<master>{m_message["answer_text"]}</master></s/s>'

        for i in task:
            context = "".join(context.split("</s/s>")[-3:])

            await  i.send_message(context)
            i_message = await i.wait_answer()
            context += f'<{i.name}_{i.index}>{i_message["answer_text"]}</{i.name}_{i.index}></s/s>'
            print(f'<{i.name}_{i.index}>{i_message["answer_text"]}</{i.name}_{i.index}>')



async def test():
    detail = {
        "is_agent": "0",
        "agent_id": "",
        "agent_prompt": "你好",
        "deep_think": "0",
        "mode": "k1.5"
    }

    b = DeepseekAgent(detail, "1")
    await b.load_agent()
    a = await b.wait_answer()
    print(a)
    await b.send_message("hello")
    print(await b.wait_answer())
    input()


if __name__ == "__main__":
    asyncio.run(main())
    # asyncio.run(test())



