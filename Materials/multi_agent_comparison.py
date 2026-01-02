"""
📊 MULTI-AGENT PATTERNS COMPARISON

This file demonstrates the difference between:
1. Handoffs - Transfer control completely
2. Agent-as-Tool - Stay in control, use agents as helpers

Run: python multi_agent_comparison.py
"""

import asyncio
import os
from openai import AsyncOpenAI
from agents import Agent, Runner, RunConfig, OpenAIChatCompletionsModel

# ============================================
# SETUP
# ============================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("❌ Set GEMINI_API_KEY first!")
    exit(1)

client = AsyncOpenAI(
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    api_key=GEMINI_API_KEY,
)

def create_model():
    return OpenAIChatCompletionsModel(
        model="gemini-2.0-flash",
        openai_client=client,
    )


# ============================================
# SHARED SPECIALIST AGENT
# ============================================

math_expert = Agent(
    name="MathExpert",
    instructions="You are a math expert. Solve math problems step by step. Be concise.",
    model=create_model(),
)


# ============================================
# PATTERN 1: HANDOFF
# ============================================

handoff_agent = Agent(
    name="HandoffRouter",
    instructions="""You route requests to specialists.
If user asks about math, handoff to MathExpert.
For other questions, answer briefly yourself.""",
    model=create_model(),
    handoffs=[math_expert],  # <-- HANDOFF: Will transfer control
)


# ============================================
# PATTERN 2: AGENT-AS-TOOL
# ============================================

tool_agent = Agent(
    name="ToolCoordinator",
    instructions="""You coordinate with specialists.
If user asks about math, use the math_expert tool to get the answer.
Then present the result in your own words with additional context.""",
    model=create_model(),
    tools=[
        math_expert.as_tool(  # <-- AS-TOOL: Will call and get response back
            tool_name="math_expert",
            tool_description="Solves math problems. Use for any calculations.",
        ),
    ],
)


# ============================================
# COMPARISON DEMO
# ============================================

async def main():
    query = "What is 15 * 23?"
    
    print("=" * 70)
    print("📊 MULTI-AGENT PATTERNS COMPARISON")
    print("=" * 70)
    print(f"\n📝 Same query to both patterns: '{query}'")
    
    # Pattern 1: Handoff
    print("\n" + "-" * 70)
    print("🔀 PATTERN 1: HANDOFF")
    print("-" * 70)
    print("""
    ┌──────────────┐         ┌─────────────┐
    │ HandoffRouter│ ──────► │  MathExpert │ ──► Response
    └──────────────┘ handoff └─────────────┘
                              (takes over)
    """)
    
    result1 = await Runner.run(
        handoff_agent,
        query,
        run_config=RunConfig(tracing_disabled=True),
    )
    
    print(f"🏷️  Final Agent: {result1.last_agent.name}")
    print(f"💬 Response: {result1.final_output}")
    
    # Pattern 2: Agent-as-Tool
    print("\n" + "-" * 70)
    print("🔧 PATTERN 2: AGENT-AS-TOOL")
    print("-" * 70)
    print("""
    ┌────────────────┐         ┌─────────────┐
    │ToolCoordinator │ ──────► │  MathExpert │
    │                │ ◄────── │   (tool)    │
    │  (compiles)    │ result  └─────────────┘
    └────────────────┘
           │
           ▼
       Response
    """)
    
    result2 = await Runner.run(
        tool_agent,
        query,
        run_config=RunConfig(tracing_disabled=True),
    )
    
    print(f"🏷️  Final Agent: {result2.last_agent.name}")
    print(f"💬 Response: {result2.final_output}")
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 SUMMARY")
    print("=" * 70)
    print(f"""
┌─────────────────┬─────────────────────┬─────────────────────┐
│                 │      HANDOFF        │    AGENT-AS-TOOL    │
├─────────────────┼─────────────────────┼─────────────────────┤
│ Control         │ Transfers to        │ Stays with          │
│                 │ specialist          │ coordinator         │
├─────────────────┼─────────────────────┼─────────────────────┤
│ Final Agent     │ {result1.last_agent.name:<19} │ {result2.last_agent.name:<19} │
├─────────────────┼─────────────────────┼─────────────────────┤
│ Use When        │ Specialist should   │ Need to combine     │
│                 │ handle entirely     │ multiple sources    │
├─────────────────┼─────────────────────┼─────────────────────┤
│ Code            │ handoffs=[agent]    │ tools=[agent.as_tool()]│
└─────────────────┴─────────────────────┴─────────────────────┘
    """)


if __name__ == "__main__":
    asyncio.run(main())
