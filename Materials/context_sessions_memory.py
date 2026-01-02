"""
🧠 CONTEXT, STATE, SESSIONS & MEMORY - Production Guide
=========================================================

This file covers the 4 key concepts for production agents:

1. CONTEXT (RunContextWrapper) - Dependency injection, pass data to tools
2. STATE - Mutable data that changes during agent runs  
3. SESSIONS - Conversation history persistence
4. MEMORY - Long-term storage across sessions

Run: python context_sessions_memory.py
"""

import asyncio
import os
from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime

from openai import AsyncOpenAI
from agents import (
    Agent, Runner, RunConfig, 
    OpenAIChatCompletionsModel, 
    function_tool, 
    RunContextWrapper,
    SQLiteSession,
)

# ============================================
# SETUP - Using Ollama (change as needed)
# ============================================

client = AsyncOpenAI(
    api_key=os.getenv("OLLAMA_API_KEY", "ollama"),
    base_url="http://localhost:11434/v1"
)

def create_model(model: str = "mistral:7b"):
    return OpenAIChatCompletionsModel(model=model, openai_client=client)

config = RunConfig(tracing_disabled=True)


# ============================================
# PART 1: CONTEXT (RunContextWrapper)
# ============================================
"""
Context is for DEPENDENCY INJECTION:
- Pass user info, settings, API clients to tools
- NOT sent to LLM (private to your code)
- Same context shared across all agents, tools, hooks in a run
"""

@dataclass
class UserContext:
    """Custom context - can be any Python object"""
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
async def get_user_profile(ctx: RunContextWrapper[UserContext]) -> str:
    """Get the current user's profile information"""
    user = ctx.context
    user.request_count += 1  # Modify state!
    user.last_activity = datetime.now().isoformat()
    
    return f"""
User Profile:
- Name: {user.user_name}
- Email: {user.email}
- Premium: {'Yes' if user.is_premium else 'No'}
- Language: {user.language}
- Request #: {user.request_count}
"""


@function_tool
async def check_premium_feature(
    ctx: RunContextWrapper[UserContext],
    feature_name: str
) -> str:
    """Check if user has access to a premium feature"""
    user = ctx.context
    
    if user.is_premium:
        return f"✅ {user.user_name} has access to '{feature_name}'"
    else:
        return f"❌ {user.user_name} needs premium for '{feature_name}'. Upgrade at example.com/premium"


@function_tool
async def log_activity(
    ctx: RunContextWrapper[UserContext],
    activity: str
) -> str:
    """Log user activity"""
    user = ctx.context
    timestamp = datetime.now().isoformat()
    
    # In production, this would write to a database/logging service
    log_entry = f"[{timestamp}] User {user.user_id}: {activity}"
    print(f"📝 LOG: {log_entry}")
    
    return f"Activity logged: {activity}"


async def demo_context():
    """Demonstrate Context usage"""
    print("=" * 60)
    print("📦 PART 1: CONTEXT (RunContextWrapper)")
    print("=" * 60)
    
    # Create context object
    user_context = UserContext(
        user_id="usr_123",
        user_name="Dhruv",
        email="dhruv@example.com",
        is_premium=True,
        language="en",
    )
    
    # Create agent with context type
    agent = Agent[UserContext](
        name="ProfileAgent",
        instructions="""You help users with their profile and account.
        Use get_user_profile to show user info.
        Use check_premium_feature to verify access.
        Use log_activity to record actions.""",
        model=create_model(),
        tools=[get_user_profile, check_premium_feature, log_activity],
    )
    
    # Run with context
    print("\n🔍 Query: 'Show my profile and check if I can use AI features'")
    result = await Runner.run(
        agent,
        "Show my profile and check if I can use AI features",
        context=user_context,  # Pass context here!
        run_config=config,
    )
    
    print(f"\n🤖 Response:\n{result.final_output}")
    
    # Context was mutated by tools!
    print(f"\n📊 Context State After Run:")
    print(f"   - Request count: {user_context.request_count}")
    print(f"   - Last activity: {user_context.last_activity}")


# ============================================
# PART 2: DYNAMIC INSTRUCTIONS WITH CONTEXT
# ============================================
"""
Instructions can be dynamic functions that use context
"""

def dynamic_instructions(
    ctx: RunContextWrapper[UserContext],
    agent: Agent[UserContext]
) -> str:
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


async def demo_dynamic_instructions():
    """Demonstrate dynamic instructions"""
    print("\n" + "=" * 60)
    print("🔄 PART 2: DYNAMIC INSTRUCTIONS")
    print("=" * 60)
    
    # Free user
    free_user = UserContext(
        user_id="usr_456",
        user_name="Alex",
        email="alex@example.com",
        is_premium=False,
    )
    
    agent = Agent[UserContext](
        name="DynamicAgent",
        instructions=dynamic_instructions,  # Function, not string!
        model=create_model(),
    )
    
    print("\n🔍 Query from FREE user: 'Hello!'")
    result = await Runner.run(
        agent,
        "Hello!",
        context=free_user,
        run_config=config,
    )
    print(f"🤖 Response:\n{result.final_output}")


# ============================================
# PART 3: STATE MANAGEMENT
# ============================================
"""
State = Mutable data that changes during agent execution
- Use dataclass with mutable fields
- Tools can read AND write to context
- State persists across tool calls within a single run
"""

@dataclass
class ShoppingContext:
    """Context with mutable state for shopping cart"""
    user_id: str
    cart: List[dict] = field(default_factory=list)
    total: float = 0.0
    discount_applied: bool = False


@function_tool
async def add_to_cart(
    ctx: RunContextWrapper[ShoppingContext],
    item_name: str,
    price: float,
    quantity: int = 1
) -> str:
    """Add an item to the shopping cart"""
    cart = ctx.context
    
    item = {
        "name": item_name,
        "price": price,
        "quantity": quantity,
        "subtotal": price * quantity
    }
    cart.cart.append(item)
    cart.total += item["subtotal"]
    
    return f"Added {quantity}x {item_name} (${price:.2f} each) to cart. Total: ${cart.total:.2f}"


@function_tool
async def view_cart(ctx: RunContextWrapper[ShoppingContext]) -> str:
    """View current shopping cart"""
    cart = ctx.context
    
    if not cart.cart:
        return "Your cart is empty!"
    
    lines = ["🛒 Your Cart:"]
    for i, item in enumerate(cart.cart, 1):
        lines.append(f"  {i}. {item['name']} x{item['quantity']} - ${item['subtotal']:.2f}")
    
    lines.append(f"\n💰 Total: ${cart.total:.2f}")
    if cart.discount_applied:
        lines.append("🎉 Discount applied!")
    
    return "\n".join(lines)


@function_tool
async def apply_discount(
    ctx: RunContextWrapper[ShoppingContext],
    percent: float
) -> str:
    """Apply a discount to the cart"""
    cart = ctx.context
    
    if cart.discount_applied:
        return "A discount has already been applied!"
    
    discount_amount = cart.total * (percent / 100)
    cart.total -= discount_amount
    cart.discount_applied = True
    
    return f"Applied {percent}% discount! Saved ${discount_amount:.2f}. New total: ${cart.total:.2f}"


async def demo_state():
    """Demonstrate state management"""
    print("\n" + "=" * 60)
    print("📊 PART 3: STATE MANAGEMENT")
    print("=" * 60)
    
    # Create mutable state
    shopping_cart = ShoppingContext(user_id="usr_789")
    
    agent = Agent[ShoppingContext](
        name="ShoppingAgent",
        instructions="Help users shop. Use tools to manage their cart.",
        model=create_model(),
        tools=[add_to_cart, view_cart, apply_discount],
    )
    
    # Multiple queries that modify state
    queries = [
        "Add a laptop for $999 and a mouse for $29",
        "Show my cart",
        "Apply a 10% discount",
        "Show my cart again",
    ]
    
    for query in queries:
        print(f"\n👤 User: {query}")
        result = await Runner.run(
            agent,
            query,
            context=shopping_cart,  # Same context across runs!
            run_config=config,
        )
        print(f"🤖 Agent: {result.final_output}")
    
    # State persisted across runs
    print(f"\n📊 Final State:")
    print(f"   - Items in cart: {len(shopping_cart.cart)}")
    print(f"   - Total: ${shopping_cart.total:.2f}")
    print(f"   - Discount applied: {shopping_cart.discount_applied}")


# ============================================
# PART 4: SESSIONS (Conversation History)
# ============================================
"""
Sessions = Automatic conversation history management
- Agent remembers previous messages
- Multiple session backends: SQLite, SQLAlchemy, Redis, etc.
- Different session IDs = different conversations
"""

async def demo_sessions():
    """Demonstrate session-based memory"""
    print("\n" + "=" * 60)
    print("💬 PART 4: SESSIONS (Conversation History)")
    print("=" * 60)
    
    agent = Agent(
        name="MemoryAgent",
        instructions="You are a helpful assistant. Remember what the user tells you.",
        model=create_model(),
    )
    
    # Create a session (in-memory SQLite)
    session = SQLiteSession("user_dhruv_123")
    
    # Multi-turn conversation
    conversations = [
        "Hi! My name is Dhruv and I'm a developer from India.",
        "What programming languages do you think I should learn?",
        "What's my name and where am I from?",  # Tests memory!
    ]
    
    print("\n🔄 Multi-turn conversation with session memory:\n")
    
    for i, msg in enumerate(conversations, 1):
        print(f"👤 Turn {i}: {msg}")
        
        result = await Runner.run(
            agent,
            msg,
            session=session,  # Pass session here!
            run_config=config,
        )
        print(f"🤖 Agent: {result.final_output}\n")
    
    # Session persists across runs
    print("✅ Agent remembered user's name and location from earlier turns!")


async def demo_session_persistence():
    """Demonstrate persistent sessions with file-based SQLite"""
    print("\n" + "=" * 60)
    print("💾 PART 4b: PERSISTENT SESSIONS")
    print("=" * 60)
    
    # File-based SQLite (persists after program ends)
    session = SQLiteSession(
        session_id="persistent_user_123",
        db_path="conversations.db"  # File path!
    )
    
    agent = Agent(
        name="PersistentAgent",
        instructions="Remember everything the user tells you.",
        model=create_model(),
    )
    
    result = await Runner.run(
        agent,
        "Remember that my favorite color is blue and I like pizza.",
        session=session,
        run_config=config,
    )
    print(f"🤖 {result.final_output}")
    
    print("\n💡 This conversation is saved to 'conversations.db'")
    print("   Next time you run this, the agent will remember!")


async def demo_multi_agent_shared_session():
    """Demonstrate multiple agents sharing the same session"""
    print("\n" + "=" * 60)
    print("🤝 PART 4c: MULTI-AGENT SHARED SESSION")
    print("=" * 60)
    
    # Shared session
    shared_session = SQLiteSession("multi_agent_session")
    
    # Different agents
    greeter = Agent(
        name="Greeter",
        instructions="You greet users warmly.",
        model=create_model(),
    )
    
    helper = Agent(
        name="Helper", 
        instructions="You help users with their questions. Reference what you know about them.",
        model=create_model(),
    )
    
    # Greeter talks first
    print("\n👤 User talks to Greeter first...")
    result1 = await Runner.run(
        greeter,
        "Hi! I'm Dhruv, a Python developer.",
        session=shared_session,
        run_config=config,
    )
    print(f"🤖 Greeter: {result1.final_output}")
    
    # Helper continues (same session!)
    print("\n👤 User then talks to Helper...")
    result2 = await Runner.run(
        helper,
        "Can you recommend some Python libraries for me?",
        session=shared_session,  # Same session!
        run_config=config,
    )
    print(f"🤖 Helper: {result2.final_output}")
    
    print("\n✅ Helper knows user's name from Greeter's conversation!")


# ============================================
# PART 5: COMBINING CONTEXT + SESSIONS
# ============================================
"""
Production pattern: Use BOTH context and sessions
- Context: User info, settings, API clients, mutable state
- Session: Conversation history
"""

@dataclass
class ProductionContext:
    user_id: str
    user_name: str
    subscription_tier: str
    api_calls_remaining: int = 100


@function_tool
async def get_account_status(ctx: RunContextWrapper[ProductionContext]) -> str:
    """Get user's account status"""
    user = ctx.context
    return f"""
Account Status for {user.user_name}:
- User ID: {user.user_id}
- Tier: {user.subscription_tier}
- API Calls Remaining: {user.api_calls_remaining}
"""


@function_tool
async def use_api_call(ctx: RunContextWrapper[ProductionContext]) -> str:
    """Simulate using an API call"""
    user = ctx.context
    if user.api_calls_remaining <= 0:
        return "❌ No API calls remaining! Please upgrade."
    
    user.api_calls_remaining -= 1
    return f"✅ API call used. {user.api_calls_remaining} remaining."


async def demo_production_pattern():
    """Demonstrate production pattern with context + sessions"""
    print("\n" + "=" * 60)
    print("🏭 PART 5: PRODUCTION PATTERN (Context + Sessions)")
    print("=" * 60)
    
    # Context for user data and state
    context = ProductionContext(
        user_id="usr_prod_001",
        user_name="Dhruv",
        subscription_tier="Pro",
        api_calls_remaining=5,
    )
    
    # Session for conversation history
    session = SQLiteSession("prod_user_001")
    
    agent = Agent[ProductionContext](
        name="ProductionAgent",
        instructions="""You are a production assistant.
        Always check account status before operations.
        Track API usage carefully.""",
        model=create_model(),
        tools=[get_account_status, use_api_call],
    )
    
    queries = [
        "What's my account status?",
        "Use an API call for me",
        "What's my remaining balance now?",
    ]
    
    for query in queries:
        print(f"\n👤 User: {query}")
        result = await Runner.run(
            agent,
            query,
            context=context,   # User data + state
            session=session,   # Conversation history
            run_config=config,
        )
        print(f"🤖 Agent: {result.final_output}")
    
    print(f"\n📊 Final Context State:")
    print(f"   - API calls remaining: {context.api_calls_remaining}")


# ============================================
# MAIN
# ============================================

async def main():
    print("""
╔══════════════════════════════════════════════════════════════╗
║     🧠 CONTEXT, STATE, SESSIONS & MEMORY                      ║
║     Production Guide for OpenAI Agents SDK                    ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Run all demos
    await demo_context()
    await demo_dynamic_instructions()
    await demo_state()
    await demo_sessions()
    # await demo_session_persistence()  # Uncomment to test file persistence
    await demo_multi_agent_shared_session()
    await demo_production_pattern()
    
    print("\n" + "=" * 60)
    print("✅ ALL DEMOS COMPLETE!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
