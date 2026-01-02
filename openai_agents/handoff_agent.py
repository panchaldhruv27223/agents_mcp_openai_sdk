import asyncio
import os 
from openai import AsyncOpenAI
from agents import Agent, Runner, RunConfig, OpenAIChatCompletionsModel
from dotenv import load_dotenv

load_dotenv()

client = AsyncOpenAI(
    api_key= os.getenv("OLLAMA_API_KEY"),
    base_url = "http://localhost:11434/v1"
)


def create_ollama_model():
    return OpenAIChatCompletionsModel(
        model=os.getenv("OLLAMA_MODEL_NAME"),
        openai_client=client
    )

## Agent For Spanish Speakers
spanish_agent = Agent(
    name="SpanishAgent",
    instructions="""You are a spanish agent that can answer any spanish question. 
    - always respond in spanish only
    - be helpful and friendly
    - you handle all queries in Spanish""",
    model = create_ollama_model()
    
)


## Agent For Technical Support
tech_agent = Agent(
    name="TechSupportAgent",
    instructions= """You are a technical support specialist.
    - help with coding, debugging, technical issues
    - Be precise and provide code examples when needed
    - you handle all technical queries
    """,
    model = create_ollama_model()
)

## Agent For Sales inquiries
sales_agent = Agent(
    name = "SalesAgent",
    instructions="""You are a sales agent that can answer any sales questions.
    - help with pricing, plans and purchases
    - be persuasive but honest
    - you handle all sales-related queries""",
    model = create_ollama_model()
)



#### Triage_agent

triage_agent = Agent(
    name = "TriageAgent",
    instructions="""You are a routing agent. Analyze the user's messages and handoff to the appropriate specialist:

1. If user writes in Spanish or asks for Spanish → handoff to SpanishAgent
2. If user asks about code, bugs, technical issues → handoff to TechSupportAgent  
3. If user asks about pricing, buying, plans → handoff to SalesAgent
4. For general questions, answer yourself briefly.

Always handoff to specialists for their domain - don't try to handle everything yourself.""",

    model = create_ollama_model(),
    handoffs= [spanish_agent, tech_agent, sales_agent]
)

async def test_handoffs(query):
    
    result = await Runner.run(
        triage_agent,
        query,
        run_config= RunConfig(tracing_disabled=True)
    )

    return result


async def main():

    test_case = "How do i fix a null pointer exception in python???"

    result = await test_handoffs(test_case)

    print("Handoff agent output:")
    print(result)
    print("Final Result: ")
    print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())