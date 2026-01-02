"""
Production Multi-agent system
Works with: OpenAI, Gemini, ..
"""

import asyncio
import os 
from typing import Optional 
from pydantic import BaseModel
from agents import OpenAIChatCompletionsModel, Runner, RunConfig, Agent
from openai import AsyncOpenAI

from dotenv import load_dotenv

load_dotenv()


class ProviderConfig(BaseModel):
    name: str
    base_url: str
    api_key_env: str
    default_model: str

PROVIDERS = {
    "openai": ProviderConfig(
        name="OpenAI",
        base_url="https://api.openai.com/v1",
        api_key_env="OPENAI_API_KEY",
        default_model="gpt-4o-mini",
    ),
    "gemini": ProviderConfig(
        name="Gemini",
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        api_key_env="GEMINI_API_KEY",
        default_model="gemini-2.0-flash",
    ),
    "ollama": ProviderConfig(
        name="Ollama",
        base_url="http://localhost:11434/v1",
        api_key_env="OLLAMA_API_KEY",
        default_model="ministral-3:3b",
    ),
}


class ModelFactory:

    def __init__(self, provider:str="ollama"):
        config = PROVIDERS.get(provider.lower())
        if not config:
            raise ValueError(f"Unknown  provider: {provider}")

        self.provider = config

        self.client = AsyncOpenAI(
            api_key = self.provider.api_key_env,
            base_url = self.provider.base_url
        )



    def create(self, model_name:Optional[str]=None) -> OpenAIChatCompletionsModel:
        return OpenAIChatCompletionsModel(
            model = model_name or self.provider.default_model,
            openai_client=self.client
            )



def create_agent(factory: ModelFactory):
    """
    Create All agent using the provided model factory
    """

    math_agent = Agent(
        name = "MathExpert",
        instructions= "Solve math problems step by step. Be concise.",
        model = factory.create()
    )

    code_agent = Agent(
        name= "CodeExpert",
        instructions="Help With coding questions. Provide clean, working code.",
        model = factory.create()
    )

    writing_agent = Agent(
        name= "WritingExpert",
        instructions="Help with writing tasks, be creative and clear",
        model = factory.create()
    )   


    triage_agent = Agent(
        name="TriageAgent",
        instructions="""Route questions to the right expert:
        - Math questions → MathExpert
        - Coding questions → CodeExpert  
        - Writing questions → WritingExpert
        - General questions → answer yourself""",
        model=factory.create(),
        handoffs=[math_agent, code_agent, writing_agent],
    )


    # Coordinator agent (agents-as-tools pattern)
    coordinator_agent = Agent(
        name="Coordinator",
        instructions="""You coordinate complex tasks using your tools.
        Use ask_math_expert, ask_code_expert, ask_writing_expert as needed.
        Compile results into a comprehensive response.""",
        model=factory.create(),
        tools=[
            math_agent.as_tool(
                tool_name="ask_math_expert",
                tool_description="Solve math problems",
            ),
            code_agent.as_tool(
                tool_name="ask_code_expert",
                tool_description="Help with coding tasks",
            ),
            writing_agent.as_tool(
                tool_name="ask_writing_expert",
                tool_description="Help with writing tasks",
            ),
        ],
    )
    
    return {
        "triage": triage_agent,
        "coordinator": coordinator_agent,
        "math": math_agent,
        "code": code_agent,
        "writing": writing_agent,
    }


async def main():
    factory = ModelFactory(provider="ollama")
    agents = create_agent(factory)

    print("\n\n")
    print("Triage Agent output: ")
    result = await Runner.run(agents["triage"], "What is the capital of france??", run_config=RunConfig(tracing_disabled=True))

    print("Final Result: ")
    print(result.final_output)


    print("\n\n")
    print("Coordinator Agent output: ")
    result = await Runner.run(agents["coordinator"], "What is the capital of france??", run_config=RunConfig(tracing_disabled=True))

    print("Final Result: ")
    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())