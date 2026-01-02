# OpenAI Agents SDK: Multi-Agent Production Guide

> **VERIFIED** - Based on official documentation and real testing

---

## 🔑 Key Clarification (What I Got Wrong)

| Feature | Chat Completions API | Responses API |
|---------|---------------------|---------------|
| `handoffs=[agent]` | ✅ **WORKS** | ✅ WORKS |
| `agent.as_tool()` | ✅ **WORKS** | ✅ WORKS |
| `@function_tool` | ✅ **WORKS** | ✅ WORKS |
| Web Search Tool | ❌ | ✅ OpenAI only |
| File Search Tool | ❌ | ✅ OpenAI only |
| Code Interpreter | ❌ | ✅ OpenAI only |
| Computer Use | ❌ | ✅ OpenAI only |

**Bottom Line:** `agent.as_tool()` works with ANY provider that supports tool calling (Ollama, Gemini, Groq, etc.)

---

## 📚 Three Types of Tools (From Official Docs)

### 1. Hosted Tools (OpenAI Responses API ONLY)
```python
from agents import WebSearchTool, FileSearchTool, CodeInterpreterTool

# ❌ These ONLY work with OpenAI Responses API
agent = Agent(
    name="SearchAgent",
    model="gpt-4o",  # Must be OpenAI default model
    tools=[WebSearchTool()],
)
```

### 2. Function Tools (Works EVERYWHERE)
```python
from agents import function_tool

@function_tool
def get_weather(city: str) -> str:
    """Get weather for a city"""
    return f"Weather in {city}: Sunny"

# ✅ Works with any provider
agent = Agent(
    name="WeatherAgent",
    model=OpenAIChatCompletionsModel(model="mistral:7b", openai_client=ollama_client),
    tools=[get_weather],
)
```

### 3. Agents as Tools (Works EVERYWHERE with tool calling support)
```python
# ✅ Works with any provider that supports tool calling
specialist = Agent(name="Specialist", ...)

coordinator = Agent(
    name="Coordinator",
    tools=[
        specialist.as_tool(
            tool_name="ask_specialist",
            tool_description="Get expert advice",
        ),
    ],
)
```

---

## 🏗️ Multi-Agent Patterns

### Pattern 1: Handoffs (Decentralized Control)

**Use When:** You want to transfer conversation completely to another agent.

```python
from agents import Agent, Runner, RunConfig, OpenAIChatCompletionsModel
from openai import AsyncOpenAI

client = AsyncOpenAI(
    api_key="ollama",  # Or your API key
    base_url="http://localhost:11434/v1"
)

def create_model(model_name: str = "mistral:7b"):
    return OpenAIChatCompletionsModel(model=model_name, openai_client=client)

# Specialist agents
billing_agent = Agent(
    name="BillingExpert",
    instructions="You handle all billing and payment questions.",
    model=create_model(),
)

technical_agent = Agent(
    name="TechnicalExpert", 
    instructions="You handle all technical support questions.",
    model=create_model(),
)

# Triage agent with handoffs
triage_agent = Agent(
    name="TriageAgent",
    instructions="""Route customer questions:
    - Billing/payment questions → handoff to BillingExpert
    - Technical issues → handoff to TechnicalExpert
    - General questions → answer yourself""",
    model=create_model(),
    handoffs=[billing_agent, technical_agent],  # ✅ Works with any provider
)

async def main():
    result = await Runner.run(
        triage_agent,
        "I can't connect to my account",
        run_config=RunConfig(tracing_disabled=True),
    )
    print(f"Handled by: {result.last_agent.name}")
    print(f"Response: {result.final_output}")
```

**Key Characteristics:**
- Control transfers completely to specialist
- `result.last_agent` will be the specialist
- Specialist sees full conversation history
- Good for: Customer support routing, language-based routing

---

### Pattern 2: Agents as Tools (Centralized Control)

**Use When:** Main agent should stay in control and compile results.

```python
# Specialist agents
spanish_translator = Agent(
    name="SpanishTranslator",
    instructions="Translate the given text to Spanish. Return ONLY the translation.",
    model=create_model(),
)

french_translator = Agent(
    name="FrenchTranslator",
    instructions="Translate the given text to French. Return ONLY the translation.",
    model=create_model(),
)

# Orchestrator uses agents as tools
orchestrator = Agent(
    name="TranslationOrchestrator",
    instructions="""You coordinate translations.
    Use translate_to_spanish and translate_to_french tools as needed.
    Compile all results into a formatted response.""",
    model=create_model(),
    tools=[
        spanish_translator.as_tool(
            tool_name="translate_to_spanish",
            tool_description="Translates text to Spanish",
        ),
        french_translator.as_tool(
            tool_name="translate_to_french", 
            tool_description="Translates text to French",
        ),
    ],
)

async def main():
    result = await Runner.run(
        orchestrator,
        "Translate 'Hello world' to Spanish and French",
        run_config=RunConfig(tracing_disabled=True),
    )
    print(f"Handled by: {result.last_agent.name}")  # Will be "TranslationOrchestrator"
    print(f"Response: {result.final_output}")
```

**Key Characteristics:**
- Orchestrator stays in control
- `result.last_agent` will be the orchestrator
- Orchestrator compiles/formats final response
- Good for: Multi-source research, parallel tasks, content pipelines

---

## 🔄 Comparison

| Aspect | Handoffs | Agents as Tools |
|--------|----------|-----------------|
| Control flow | Transfers to specialist | Stays with orchestrator |
| `result.last_agent` | The specialist | The orchestrator |
| Final response by | Specialist | Orchestrator (compiled) |
| Conversation history | Specialist sees full history | Sub-agent gets only the query |
| Best for | Routing, triage | Coordination, compilation |

---

## 🏭 Production-Ready Template

```python
"""
Production Multi-Agent System
Works with: OpenAI, Gemini, Ollama, Groq, Together AI, etc.
"""

import asyncio
import os
from typing import Optional
from dataclasses import dataclass
from openai import AsyncOpenAI
from agents import Agent, Runner, RunConfig, OpenAIChatCompletionsModel, function_tool


# ============================================
# CONFIGURATION
# ============================================

@dataclass
class ProviderConfig:
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
        default_model="mistral:7b",
    ),
    "groq": ProviderConfig(
        name="Groq",
        base_url="https://api.groq.com/openai/v1",
        api_key_env="GROQ_API_KEY",
        default_model="llama-3.3-70b-versatile",
    ),
}


# ============================================
# MODEL FACTORY
# ============================================

class ModelFactory:
    def __init__(self, provider: str = "ollama"):
        config = PROVIDERS.get(provider)
        if not config:
            raise ValueError(f"Unknown provider: {provider}")
        
        self.config = config
        self.client = AsyncOpenAI(
            api_key=os.getenv(config.api_key_env, "not-needed"),
            base_url=config.base_url,
        )
    
    def create(self, model: Optional[str] = None) -> OpenAIChatCompletionsModel:
        return OpenAIChatCompletionsModel(
            model=model or self.config.default_model,
            openai_client=self.client,
        )


# ============================================
# AGENTS
# ============================================

def create_agents(factory: ModelFactory):
    """Create all agents using the provided model factory"""
    
    # Specialist agents
    math_agent = Agent(
        name="MathExpert",
        instructions="Solve math problems step by step. Be concise.",
        model=factory.create(),
    )
    
    code_agent = Agent(
        name="CodeExpert",
        instructions="Help with coding questions. Provide clean, working code.",
        model=factory.create(),
    )
    
    writing_agent = Agent(
        name="WritingExpert",
        instructions="Help with writing tasks. Be creative and clear.",
        model=factory.create(),
    )
    
    # Triage agent (handoffs pattern)
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


# ============================================
# MAIN
# ============================================

async def main():
    # Choose your provider
    factory = ModelFactory(provider="ollama")  # or "gemini", "openai", "groq"
    agents = create_agents(factory)
    config = RunConfig(tracing_disabled=True)
    
    print("=" * 60)
    print("🚀 PRODUCTION MULTI-AGENT SYSTEM")
    print(f"📡 Provider: {factory.config.name}")
    print(f"🤖 Model: {factory.config.default_model}")
    print("=" * 60)
    
    # Test 1: Handoff pattern
    print("\n--- HANDOFF PATTERN ---")
    result1 = await Runner.run(
        agents["triage"],
        "What is 25 * 4?",
        run_config=config,
    )
    print(f"Query: What is 25 * 4?")
    print(f"Handled by: {result1.last_agent.name}")
    print(f"Response: {result1.final_output}")
    
    # Test 2: Agent-as-tool pattern
    print("\n--- AGENT-AS-TOOL PATTERN ---")
    result2 = await Runner.run(
        agents["coordinator"],
        "Calculate 100 / 4 and then write a haiku about the number.",
        run_config=config,
    )
    print(f"Query: Calculate 100 / 4 and write a haiku about the number")
    print(f"Handled by: {result2.last_agent.name}")
    print(f"Response: {result2.final_output}")


if __name__ == "__main__":
    asyncio.run(main())
```

---

## ⚠️ Common Mistakes to Avoid

### ❌ Mistake 1: Putting Agent in tools without .as_tool()
```python
# WRONG - Raw agent in tools
tools=[math_agent]

# CORRECT - Use .as_tool()
tools=[math_agent.as_tool(tool_name="math", tool_description="...")]
```

### ❌ Mistake 2: Confusing handoffs with tools
```python
# HANDOFFS - For routing/transfer
handoffs=[agent_a, agent_b]  # Agent takes over

# TOOLS - For coordination
tools=[agent_a.as_tool(...)]  # Main agent stays in control
```

### ❌ Mistake 3: Missing /v1 in base_url for Ollama
```python
# WRONG
base_url="http://localhost:11434"

# CORRECT
base_url="http://localhost:11434/v1"
```

### ❌ Mistake 4: Expecting hosted tools with non-OpenAI providers
```python
# WRONG - WebSearchTool only works with OpenAI Responses API
from agents import WebSearchTool
agent = Agent(
    model=OpenAIChatCompletionsModel(...),  # Chat Completions
    tools=[WebSearchTool()],  # ❌ Won't work!
)

# For web search with other providers, implement your own @function_tool
```

---

## 📊 When to Use Which Pattern

| Scenario | Use |
|----------|-----|
| Customer support routing | Handoffs |
| Language-based routing | Handoffs |
| Research from multiple sources | Agent-as-Tool |
| Translate to multiple languages | Agent-as-Tool |
| Content pipeline (research → write → review) | Agent-as-Tool |
| Deep dive into specialized topic | Handoffs |
| Compile report from specialists | Agent-as-Tool |

---

## 🔗 Official Resources

- [Agents Documentation](https://openai.github.io/openai-agents-python/agents/)
- [Tools Documentation](https://openai.github.io/openai-agents-python/tools/)
- [Handoffs Documentation](https://openai.github.io/openai-agents-python/handoffs/)
- [GitHub Repository](https://github.com/openai/openai-agents-python)
- [OpenAI Cookbook: Multi-Agent Portfolio](https://cookbook.openai.com/examples/agents_sdk/multi-agent-portfolio-collaboration/multi_agent_portfolio_collaboration)
