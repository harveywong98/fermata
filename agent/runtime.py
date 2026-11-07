"""Agent 创建与调用草稿，保留未完成实现。"""
from deepagents import create_deep_agent
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from agent.prompts import SYSTEM_PROMPT
from tools import AGENT_TOOLS


def run():
    # TODO: 接入模型配置、验证 Skills backend 路径、增加多轮对话与执行预算。
    raise NotImplementedError('Agent 尚未完成，请继续实现 agent/runtime.py；知识管理使用 python main.py web')


def run_draft():
    """原入口中的开发草稿；不在导入或启动 Web 时执行。"""
    model = ChatOpenAI(
        model="?", # todo
        api_key="sk-",
        base_url="",
        max_retries=2
    )

    agent = create_deep_agent(
        model=model,
        tools=AGENT_TOOLS,
        system_prompt=SYSTEM_PROMPT,
        skills=["/skills/"],
    )

    result = agent.invoke(
        dict(
            messages = [
                HumanMessage(content="帮我看看隐私数据有没有泄露")
            ]
        )
    )

    final_res = result["messages"][-1].content


    print(final_res)
