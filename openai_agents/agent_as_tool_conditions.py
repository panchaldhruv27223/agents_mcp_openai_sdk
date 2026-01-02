import asyncio
from pydantic import BaseModel 
from agents import Agent, AgentBase, RunContextWrapper, Runner, trace
from dotenv import load_dotenv
load_dotenv()

class AppContext(BaseModel):
    language_preference: str = "spanish_only"
    
    
def french_spanish_enabled(ctx: RunContextWrapper[AppContext], agent: AgentBase) -> bool:
    """Enable for French+Spanish and European preferences."""
    return ctx.context.language_preference in ["french_spanish", "european"]


def european_enabled(ctx: RunContextWrapper[AppContext], agent: AgentBase) -> bool:
    """Only enable for European preference."""
    return ctx.context.language_preference == "european"


# Create specialized agents
spanish_agent = Agent(
    name="spanish_agent",
    instructions="You respond in Spanish. Always reply to the user's question in Spanish.",
)

french_agent = Agent(
    name="french_agent",
    instructions="You respond in French. Always reply to the user's question in French.",
)

italian_agent = Agent(
    name="italian_agent",
    instructions="You respond in Italian. Always reply to the user's question in Italian.",
)


orchestrator = Agent(
    name="orchestrator",
    instructions=(
        "You are a multilingual assistant. You use the tools given to you to respond to users. "
        "You must call ALL available tools to provide responses in different languages. "
        "You never respond in languages yourself, you always use the provided tools."
    ),
    tools=[
        spanish_agent.as_tool(
            tool_name="respond_spanish",
            tool_description="Respond to the user's question in Spanish",
            is_enabled=True,
        ),
        french_agent.as_tool(
            tool_name="respond_french",
            tool_description="Respond to the user's question in French",
            is_enabled=french_spanish_enabled,
        ),
        italian_agent.as_tool(
            tool_name="respond_italian",
            tool_description="Respond to the user's question in Italian",
            is_enabled=european_enabled,
        ),
    ],
)


async def main():
    """ Interactive demo with llm interaction."""
    
    print("Lets start our demo")
    
    print("Choose language preference:")
    print("1. Spanish only (1 tools)")
    print("2. French and spanish (2 tools)")
    print("3. European languages (3 tools)")
    
    choice = input("\n select option(1-3): ").strip()
    
    preference_map = {"1" : "spanish_only", "2":"french_spanish", "3":"european"}
    language_preference = preference_map.get(choice, "spanish_only")
    
    context = RunContextWrapper(AppContext(language_preference=language_preference))
    
    available_tools = await orchestrator.get_all_tools(run_context=context)
    
    # print(available_tools)
    
    tool_names = [tool.name for tool in available_tools]
    
    
    print(f"\nLanguage preference: {language_preference}")
    print(f"Available tools: {', '.join(tool_names)}")
    print(f"The LLM will only see and can use these {len(available_tools)} tools\n")

    # Get user request
    user_request = input("Ask a question and see responses in available languages:\n")

    # Run with LLM interaction
    print("\nProcessing request...")
    result = await Runner.run(
        starting_agent=orchestrator,
        input=user_request,
        context=context.context,
    )

    print(f"\nResponse:\n{result.final_output}")


    
if __name__ == "__main__":
    print("lets start my boi..")
    asyncio.run(main())