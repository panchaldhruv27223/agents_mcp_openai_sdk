from openai._module_client import conversations
import asyncio
import os
import sys 
from agents import Agent, Runner, RunConfig, function_tool
from dotenv import load_dotenv
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

load_dotenv()

from openai import AsyncOpenAI
from agents import OpenAIChatCompletionsModel, RunContextWrapper, SQLiteSession



client = AsyncOpenAI(
    api_key=os.getenv("OLLAMA_API_KEY", "ollama"),
    base_url="http://localhost:11434/v1"
)


def create_model(mdoel:str ="ministral-3:3b"):
    return OpenAIChatCompletionsModel(
        model=mdoel,
        openai_client=client,
    )

config = RunConfig(tracing_disabled=True)




#### CONTEXT



### lets create context for user 

class UserContext(BaseModel):
    # User information
    user_id: str
    user_name: str
    email: str
    is_premium: bool = False
    
    # Settings/preferences
    language: str = "en"
    timezone: str = "UTC"
    
    # Dependencies (API clients, loggers, etc.)
    # db_connection: Any = None
    # logger: Any = None
    
    # Mutable state (can be modified by tools)
    request_count: int = 0
    last_activity: Optional[str] = None


@function_tool
async def get_user_profile(ctx: RunContextWrapper[UserContext]):
    """
    Get the current user profile information.
    """
    user = ctx.context
    user.request_count += 1
    user.last_activity = datetime.now().isoformat()
    
    return f"""
    User Information:
    -Name: {user.user_name}
    -Email: {user.email}
    -Request Count: {user.request_count}
    -Last Activity: {user.last_activity}
    -Premium: {'Yes' if user.is_premium else 'No'}
    -Language: {user.language}
    -Timezone: {user.timezone}
    """
    

@function_tool
async def check_premium(ctx: RunContextWrapper[UserContext], feature_name:str) -> str:
    """
    Check if user has access to a premium features
    """

    user = ctx.context

    if user.is_premium:
        return f"User {user.user_name} has access to this {feature_name}"
    else:
        return f"User {user.user_name} does not have access to this {feature_name}, to use this feature please upgrade your plan."


@function_tool
async def log_activity(
    ctx:RunContextWrapper[UserContext],
    activity:str
):
    """
    Log User activity
    """

    user = ctx.context
    timestamp = datetime.now().isoformat()

    log_entry = f"[{timestamp}] User {user.user_id}: {activity}"

    print(f"LOG: {log_entry}")
    return f"activity logged: {activity}"
    


async def demo():
    user_context  = UserContext(user_id="1", user_name="Dhruv", email="dhruv@dhruv.com", is_premium=True)
    
    agent = Agent[UserContext](
        name="ProfileAgent",
        instructions="""You help users with their profile and account.
        Use get_user_profile to show user info.
        Use check_premium_feature to verify access.
        Use log_activity to record actions.""",
        model=create_model(),
        tools=[get_user_profile, check_premium, log_activity],
    )

    result = await Runner.run(
        agent,
        "Show my profile and check if I can use AI features",
        context=user_context,
        run_config=config,
    )

    print(f"\nResponse:\n{result.final_output}")
    
    print(f"\nContext State After Run:")
    print(f"- Request count: {user_context.request_count}")
    print(f"- Last activity: {user_context.last_activity}")







## DYNAMIC INSTRUCTIONS WITH CONTEXT

"""
Instructions can be dynamic functions that use context
"""

async def dynamic_instructions(ctx: RunContextWrapper[UserContext], agent:Agent[UserContext]):
    """Generate instructions based on context"""

    user = ctx.context

    base = f"""You are a helpful assistant for {user.user_name}.
User preferences:
- Language: {user.language}
- Timezone: {user.timezone}
- Premium status: {'Premium member' if user.is_premium else 'Free tier'}

Always be polite and address the user by name."""

    if user.is_premium:
        base += "\n\nThis is a premium user - provide detailed, comprehensive answers."
    else:
        base += "\n\nThis is a free user - be helpful but mention premium features when relevant."
    
    return base


## lets try this dyanamic instructions

async def demo_dynamic_instructions():
    user_context = UserContext(user_id="1", user_name="Dhruv", email="dhruv@dhruv.com", is_premium=True)
    
    agent = Agent[UserContext](
        name="DynamicAgent",
        instructions=dynamic_instructions,
        model=create_model(),
        tools=[get_user_profile, check_premium, log_activity],
    )

    result = await Runner.run(
        agent,
        "Show my profile and check if I can use AI features",
        context=user_context,
        run_config=config,
    )

    print(f"\nResponse:\n{result.final_output}")
    
    # Context was mutated by tools!
    print(f"\nContext State After Run:")
    print(f"- Request count: {user_context.request_count}")
    print(f"- Last activity: {user_context.last_activity}")

# if __name__ == "__main__":
#     asyncio.run(demo_dynamic_instructions())




# SESSIONS (Conversation History)

"""
Sessions = Automatic conversation history management
- Agent remembers previous messages
- Multiple session backends: SQLite, SQLAlchemy, Redis, etc.
- Different session IDs = different conversations
"""


async def demo_session():

    agent = Agent(
        name="MemoryAgent",
        instructions="You are a helpful assistant. Remember what user tells you.",
        model=create_model()
    )

    session = SQLiteSession("Demo_session_1")

    conversations = [
        "Hi! My name is Dhruv and I'm a developer from India.",
        "What programming languages do you think I should learn?",
        "What's my name and where am I from?", 
    ]

    
    for i, msg in enumerate(conversations, 1):
        print(f"Turn {i}: {msg}")
        
        result = await Runner.run(
            agent,
            msg,
            session=session,
            run_config=config,
        )
        print(f"Agent: {result.final_output}\n")
    
    # Session persists across runs
    print("Agent remembered user's name and location from earlier turns!")



async def demo_session_persistence():

    agent = Agent(
        name="MemoryAgent",
        instructions="You are a helpful assistant. Remember what user tells you.",
        model=create_model()
    )

    session = SQLiteSession("Demo_session_1", db_path="demo_session_persistence.db")

    conversations = [
        "Hi! My name is Dhruv and I'm a developer from India.",
        "What programming languages do you think I should learn?",
        "What's my name and where am I from?",
    ]

    
    for i, msg in enumerate(conversations, 1):
        print(f"Turn {i}: {msg}")
        
        result = await Runner.run(
            agent,
            msg,
            session=session,
            run_config=config,
        )
        print(f"Agent: {result.final_output}\n")
    
    # Session persists across runs
    print("Agent remembered user's name and location from earlier turns!")

    # result = await Runner.run(
    #     agent,
    #     "Hey What is my name ??",
    #     session=session,
    #     run_config=config,
    # )

    # print(f"Agent: {result.final_output}")



## now lets combine both the context and session

class ProductionContext(BaseModel):
    user_id: str
    user_name: str
    subscription_tier: str
    api_calls_remaining: int = 100


@function_tool
async def get_account_status(ctx: RunContextWrapper[ProductionContext]) -> str:
    
    """
        Get User's account status
    """

    user = ctx.context

    return f"""
    Account Status for {user.user_name}:
    - User ID: {user.user_id}
    - Tier: {user.subscription_tier}
    - API Calls Remaining: {user.api_calls_remaining}
    """

@function_tool
async def use_api_call(ctx: RunContextWrapper[ProductionContext]) -> str:
    
    """
        Simulate using an API call
    """

    user = ctx.context
    user.api_calls_remaining -= 1
    return f"API call used successfully. {user.api_calls_remaining} calls remaining."


async def demo_production_session_context():
    context = ProductionContext(
        user_id="usr_prod_001",
        user_name="Dhruv",
        subscription_tier="Pro",
        api_calls_remaining=5,
    )


    session = SQLiteSession("prod_user_001", db_path="prod_user_001.db")


    agent = Agent[ProductionContext](
        name="ProductionAgent",
        instructions="""You are a production assistant.
        Always check account status before operations.
        Track API usage carefully.""",
        model=create_model(),
        tools=[get_account_status, use_api_call],
    )

    queries = [
        "What is my account status??",
        "Use an API call for me",
        "What is my remaining balance now??"
    ]

    for query in queries:
        result = await Runner.run(
            agent, 
            query,
            context=context,
            session=session,
            run_config=config,
        )

        print(f"\n\nQuery: {query}")
        print(f"\n\nResponse: {result.final_output}")



if __name__ == "__main__":
    asyncio.run(demo_production_session_context())