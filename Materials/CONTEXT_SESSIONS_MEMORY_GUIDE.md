# Context, State, Sessions & Memory - Complete Guide

> **Production-ready patterns for OpenAI Agents SDK**

---

## 🎯 Quick Overview

| Concept | Purpose | Scope | Sent to LLM? |
|---------|---------|-------|--------------|
| **Context** | Dependency injection (user info, API clients) | Single run | ❌ No |
| **State** | Mutable data that changes during run | Single run | ❌ No |
| **Session** | Conversation history | Across runs | ✅ Yes |
| **Memory** | Long-term storage (preferences, facts) | Across sessions | ✅ Yes |

---

## 📦 1. CONTEXT (RunContextWrapper)

### What is it?
Context is a **dependency injection** mechanism. Pass any Python object to your agent run, and it's available in all tools, hooks, and lifecycle events.

### Key Points:
- ❌ **NOT sent to LLM** - It's private to your code
- ✅ **Shared across** all tools, agents, hooks in a run
- ✅ **Same type required** - All components must use same context type
- ✅ **Mutable** - Tools can modify context

### Basic Usage:

```python
from dataclasses import dataclass
from agents import Agent, Runner, function_tool, RunContextWrapper

# 1. Define your context type
@dataclass
class UserContext:
    user_id: str
    user_name: str
    is_premium: bool
    api_calls: int = 0  # Mutable state

# 2. Create tools that use context
@function_tool
async def get_user_info(ctx: RunContextWrapper[UserContext]) -> str:
    user = ctx.context  # Access your data
    user.api_calls += 1  # Modify state
    return f"User: {user.user_name}, Premium: {user.is_premium}"

# 3. Create typed agent
agent = Agent[UserContext](
    name="MyAgent",
    instructions="Help users with their account.",
    tools=[get_user_info],
)

# 4. Pass context when running
user = UserContext(user_id="123", user_name="Dhruv", is_premium=True)

result = await Runner.run(
    agent,
    "Show my profile",
    context=user,  # Pass context here!
)

# Context was mutated!
print(user.api_calls)  # 1
```

### Production Context Example:

```python
@dataclass
class ProductionContext:
    # User information
    user_id: str
    user_name: str
    email: str
    roles: List[str]
    
    # Settings
    language: str = "en"
    timezone: str = "UTC"
    
    # Dependencies (injected services)
    db: DatabaseConnection = None
    cache: RedisClient = None
    logger: Logger = None
    
    # Mutable state
    request_count: int = 0
    last_activity: datetime = None
    audit_log: List[str] = field(default_factory=list)
```

---

## 🔄 2. DYNAMIC INSTRUCTIONS

Instructions can be functions that receive context:

```python
def dynamic_instructions(
    ctx: RunContextWrapper[UserContext],
    agent: Agent[UserContext]
) -> str:
    user = ctx.context
    
    base = f"You are helping {user.user_name}."
    
    if user.is_premium:
        return base + " Provide detailed, comprehensive answers."
    else:
        return base + " Be helpful but mention premium features."

agent = Agent[UserContext](
    name="DynamicAgent",
    instructions=dynamic_instructions,  # Function, not string!
)
```

---

## 📊 3. STATE MANAGEMENT

State = Mutable fields in your context that change during execution.

### Pattern: Shopping Cart

```python
@dataclass
class CartContext:
    user_id: str
    items: List[dict] = field(default_factory=list)
    total: float = 0.0

@function_tool
async def add_item(ctx: RunContextWrapper[CartContext], name: str, price: float) -> str:
    ctx.context.items.append({"name": name, "price": price})
    ctx.context.total += price
    return f"Added {name}. Total: ${ctx.context.total}"

# State persists across tool calls within same run
# State persists if you reuse same context object across runs
```

---

## 💬 4. SESSIONS (Conversation History)

### What is it?
Sessions automatically manage conversation history across multiple `Runner.run()` calls.

### Session Types:

| Type | Use Case | Persistence |
|------|----------|-------------|
| `SQLiteSession("id")` | Development, simple apps | In-memory (lost on restart) |
| `SQLiteSession("id", "file.db")` | Small production apps | File-based |
| `SQLAlchemySession` | Production with existing DB | PostgreSQL, MySQL, etc. |
| `RedisSession` | Distributed, scalable | Redis server |
| `EncryptedSession` | Security-sensitive | Wraps any session |
| `OpenAIConversationsSession` | OpenAI-hosted | OpenAI servers |

### Basic Usage:

```python
from agents import Agent, Runner, SQLiteSession

agent = Agent(name="Assistant", instructions="Be helpful.")

# Create session with unique ID
session = SQLiteSession("user_123")

# Turn 1
result = await Runner.run(agent, "My name is Dhruv", session=session)

# Turn 2 - Agent remembers!
result = await Runner.run(agent, "What's my name?", session=session)
# Agent knows: "Your name is Dhruv"
```

### Persistent File-Based Session:

```python
# Saves to file - survives program restart
session = SQLiteSession(
    session_id="user_123",
    db_path="conversations.db"
)
```

### Production SQLAlchemy Session:

```python
from agents.extensions.memory import SQLAlchemySession

# PostgreSQL
session = SQLAlchemySession.from_url(
    session_id="user_123",
    url="postgresql+asyncpg://user:pass@localhost/mydb",
    create_tables=True
)

# MySQL
session = SQLAlchemySession.from_url(
    session_id="user_123",
    url="mysql+aiomysql://user:pass@localhost/mydb",
    create_tables=True
)
```

### Encrypted Session:

```python
from agents.extensions.memory import EncryptedSession

underlying = SQLiteSession("user_123", "data.db")

session = EncryptedSession(
    session_id="user_123",
    underlying_session=underlying,
    encryption_key="your-secret-key",
    ttl=3600  # Auto-expire after 1 hour
)
```

### Multi-Agent Shared Session:

```python
# Multiple agents can share the same session
session = SQLiteSession("shared_conversation")

# Agent 1 talks
await Runner.run(agent_greeter, "Hi, I'm Dhruv", session=session)

# Agent 2 knows what Agent 1 learned!
await Runner.run(agent_helper, "What's my name?", session=session)
```

### Session Protocol (Custom Implementation):

```python
from agents.memory import Session

class MyCustomSession(Session):
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.items = []
    
    async def get_items(self) -> list:
        return self.items
    
    async def add_items(self, items: list) -> None:
        self.items.extend(items)
    
    async def pop_item(self):
        return self.items.pop() if self.items else None
    
    async def clear_session(self) -> None:
        self.items.clear()
```

---

## 🏭 5. PRODUCTION PATTERN

### Combine Context + Session:

```python
@dataclass
class AppContext:
    user_id: str
    user_name: str
    subscription: str
    api_client: APIClient
    logger: Logger

async def handle_user_request(user_id: str, message: str):
    # 1. Load user data
    user_data = await db.get_user(user_id)
    
    # 2. Create context (per-request data)
    context = AppContext(
        user_id=user_id,
        user_name=user_data.name,
        subscription=user_data.subscription,
        api_client=get_api_client(),
        logger=get_logger(user_id),
    )
    
    # 3. Get or create session (conversation history)
    session = SQLiteSession(
        session_id=f"user_{user_id}",
        db_path="conversations.db"
    )
    
    # 4. Run agent with both
    result = await Runner.run(
        agent,
        message,
        context=context,   # User data + dependencies
        session=session,   # Conversation history
    )
    
    return result.final_output
```

---

## 📊 6. COMPARISON TABLE

| Feature | Context | Session |
|---------|---------|---------|
| **Purpose** | Pass data/dependencies to tools | Store conversation history |
| **Sent to LLM** | ❌ No | ✅ Yes |
| **Persistence** | In-memory (you control) | Configurable (SQLite, Redis, etc.) |
| **Mutability** | ✅ Tools can modify | ✅ Auto-updated each turn |
| **Scope** | Single run (or multiple if reused) | Across runs with same session_id |
| **Use for** | User info, API clients, settings | Multi-turn conversations |

---

## 🔑 Key Decisions

### When to use Context:
- ✅ Passing user info that tools need
- ✅ Injecting dependencies (DB, cache, logger)
- ✅ Tracking state during a run (counters, flags)
- ✅ Sensitive data that LLM shouldn't see

### When to use Session:
- ✅ Multi-turn conversations
- ✅ Agent should remember previous messages
- ✅ Chat applications
- ✅ Building conversation history

### When to use Both:
- ✅ Production applications!
- ✅ Context for user data + Session for history

---

## 📁 Installation Notes

```bash
# Basic (includes SQLiteSession)
pip install openai-agents

# With SQLAlchemy support
pip install "openai-agents[sqlalchemy]"

# With Redis support
pip install "openai-agents[redis]"

# With encryption support
pip install "openai-agents[encrypt]"

# All extras
pip install "openai-agents[sqlalchemy,redis,encrypt]"
```

---

## 🔗 Official Resources

- [Context Management](https://openai.github.io/openai-agents-python/context/)
- [Sessions](https://openai.github.io/openai-agents-python/sessions/)
- [SQLAlchemy Sessions](https://openai.github.io/openai-agents-python/sessions/sqlalchemy_session/)
- [Encrypted Sessions](https://openai.github.io/openai-agents-python/sessions/encrypted_session/)
- [Advanced SQLite Sessions](https://openai.github.io/openai-agents-python/sessions/advanced_sqlite_session/)
