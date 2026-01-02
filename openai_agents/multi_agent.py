import asyncio
import os
from agents import Agent, Runner
from openai import AsyncOpenAI
from agents import OpenAIChatCompletionsModel, RunConfig, ModelSettings
from dotenv import load_dotenv

load_dotenv()


client = AsyncOpenAI(
    # api_key = os.getenv("OPENAI_API_KEY"),
    # base_url = "https://api.openai.com/v1"
    api_key= os.getenv("OLLAMA_API_KEY"),
    base_url = "http://localhost:11434/v1"
)


math_expert = Agent(
    name="MathExpert",
    instructions="""You are a math expert that can answer any math question.""",
    model = OpenAIChatCompletionsModel(
        model="ministral-3:3b",
        openai_client=client
    )
)


## First HandOff agent

handoff_agent = Agent(
    name="HandOffAgent",
    instructions="""You are a handoff agent that can handoff any math question to math expert.""",
    model = OpenAIChatCompletionsModel(
        model="ministral-3:3b",
        openai_client=client
    ),
    handoffs=[math_expert],
)


### Agent As tool

tool_agent = Agent(
    name="ToolCoordinator",
    instructions="""You are a tool coordinator with specialisys. if user asks about math, use math_expert tool to answer. then present the result in yout own words with additional context""",
    model = OpenAIChatCompletionsModel(
        model="ministral-3:3b",
        openai_client=client
    ),
    tools= [
        math_expert.as_tool(
            tool_name="MathExpert",
            tool_description="Solve math problems. use this tool to answer any math question."
        ),
    ],
)


async def main():
    query = "What is 10 + 20 ?"

    result1 = await Runner.run(
        handoff_agent,
        query,
        run_config= RunConfig(tracing_disabled=True)
    )

    print("HandOff agents output:")
    print(result1)

    result2= await Runner.run(
        tool_agent,
        query,
        run_config= RunConfig(tracing_disabled=True)
    )

    print("Tool agents output:")
    print(result2)

if __name__ == "__main__":
    asyncio.run(main())