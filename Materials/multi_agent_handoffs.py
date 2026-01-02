"""
🤝 MULTI-AGENT PATTERN 1: Handoffs

Handoff = Agent A transfers COMPLETE CONTROL to Agent B
- Agent A stops processing
- Agent B takes over the conversation
- User now talks to Agent B

Use Case: Route users to specialized agents based on their needs

Run: python multi_agent_handoffs.py
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
# SPECIALIZED AGENTS
# ============================================

# Agent for Spanish speakers
spanish_agent = Agent(
    name="SpanishAgent",
    instructions="""You are a Spanish-speaking assistant.
- ALWAYS respond in Spanish only
- Be helpful and friendly
- You handle all queries in Spanish""",
    model=create_model(),
    # No handoffs - this is a leaf agent
)

# Agent for Technical support
tech_agent = Agent(
    name="TechSupportAgent",
    instructions="""You are a technical support specialist.
- Help with coding, debugging, technical issues
- Be precise and provide code examples when needed
- You handle all technical queries""",
    model=create_model(),
)

# Agent for Sales inquiries
sales_agent = Agent(
    name="SalesAgent",
    instructions="""You are a sales assistant.
- Help with pricing, plans, and purchases
- Be persuasive but honest
- You handle all sales-related queries""",
    model=create_model(),
)


# ============================================
# TRIAGE AGENT (Router)
# ============================================

triage_agent = Agent(
    name="TriageAgent",
    instructions="""You are a routing agent. Analyze the user's message and handoff to the appropriate specialist:

1. If user writes in Spanish or asks for Spanish → handoff to SpanishAgent
2. If user asks about code, bugs, technical issues → handoff to TechSupportAgent  
3. If user asks about pricing, buying, plans → handoff to SalesAgent
4. For general questions, answer yourself briefly.

Always handoff to specialists for their domain - don't try to handle everything yourself.""",
    model=create_model(),
    handoffs=[spanish_agent, tech_agent, sales_agent],  # <-- Agents it can handoff to
)


# ============================================
# RUN EXAMPLES
# ============================================

async def test_handoff(query: str):
    """Test a single handoff scenario"""
    print(f"\n{'='*60}")
    print(f"👤 User: {query}")
    print("-" * 60)
    
    result = await Runner.run(
        triage_agent,
        query,
        run_config=RunConfig(tracing_disabled=True),
    )
    
    # Show which agent responded
    print(f"🤖 Responded by: {result.last_agent.name}")
    print(f"💬 Response: {result.final_output}")


async def main():
    print("=" * 60)
    print("🤝 MULTI-AGENT HANDOFFS DEMO")
    print("=" * 60)
    print("""
How it works:
1. User message goes to TriageAgent
2. TriageAgent decides which specialist to handoff to
3. Specialist agent takes over and responds
    """)
    
    # Test different scenarios
    test_cases = [
        # Spanish - should go to SpanishAgent
        "Hola, necesito ayuda con mi cuenta",
        
        # Technical - should go to TechSupportAgent
        "How do I fix a null pointer exception in Python?",
        
        # Sales - should go to SalesAgent
        "What are your pricing plans?",
        
        # General - TriageAgent handles itself
        "What time is it?",
    ]
    
    for query in test_cases:
        await test_handoff(query)
        await asyncio.sleep(1)  # Small delay between requests
    
    print(f"\n{'='*60}")
    print("✅ Demo complete!")
    print("=" * 60)


async def interactive():
    """Interactive mode to test handoffs"""
    print("=" * 60)
    print("🤝 INTERACTIVE HANDOFF DEMO")
    print("=" * 60)
    print("Try different queries to see handoffs in action!")
    print("Examples:")
    print("  - 'Hola, ¿cómo estás?' → Spanish Agent")
    print("  - 'Fix my code' → Tech Agent")
    print("  - 'How much does it cost?' → Sales Agent")
    print("Type 'quit' to exit.\n")
    
    while True:
        try:
            query = input("👤 You: ").strip()
            if query.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            if not query:
                continue
            
            result = await Runner.run(
                triage_agent,
                query,
                run_config=RunConfig(tracing_disabled=True),
            )
            
            print(f"🏷️  Handled by: {result.last_agent.name}")
            print(f"🤖 Response: {result.final_output}\n")
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        asyncio.run(interactive())
    else:
        asyncio.run(main())
