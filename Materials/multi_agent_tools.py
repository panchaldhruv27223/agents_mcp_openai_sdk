"""
🔧 MULTI-AGENT PATTERN 2: Agent-as-Tool

Agent-as-Tool = Agent A uses Agent B as a tool, but A stays in control
- Agent A calls Agent B to get information
- Agent B returns result to Agent A
- Agent A compiles final response

Use Case: Coordinator agent that gathers info from specialists

Run: python multi_agent_tools.py
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
# SPECIALIST AGENTS (Used as Tools)
# ============================================

# Research Agent - finds information
research_agent = Agent(
    name="ResearchAgent",
    instructions="""You are a research specialist.
- Provide factual, well-researched information
- Be concise but comprehensive
- Focus on accuracy""",
    model=create_model(),
)

# Writer Agent - writes content
writer_agent = Agent(
    name="WriterAgent",
    instructions="""You are a creative writer.
- Write engaging, well-structured content
- Use clear and compelling language
- Adapt tone to the request""",
    model=create_model(),
)

# Critic Agent - reviews and improves
critic_agent = Agent(
    name="CriticAgent",
    instructions="""You are a constructive critic.
- Review content for quality and accuracy
- Suggest specific improvements
- Be helpful, not harsh""",
    model=create_model(),
)


# ============================================
# COORDINATOR AGENT (Uses others as tools)
# ============================================

coordinator_agent = Agent(
    name="CoordinatorAgent",
    instructions="""You are a project coordinator that manages a team of specialists.

Your team (available as tools):
1. research_expert - Use for gathering facts and information
2. writing_expert - Use for creating written content
3. review_expert - Use for reviewing and improving content

For complex tasks:
1. First, use research_expert to gather information
2. Then, use writing_expert to create content
3. Finally, use review_expert to get feedback

Compile all inputs into a polished final response.
Always coordinate - don't do specialist work yourself.""",
    model=create_model(),
    tools=[
        # Convert agents to tools!
        research_agent.as_tool(
            tool_name="research_expert",
            tool_description="Research specialist. Use for gathering facts, data, and information on any topic.",
        ),
        writer_agent.as_tool(
            tool_name="writing_expert", 
            tool_description="Writing specialist. Use for creating articles, summaries, or any written content.",
        ),
        critic_agent.as_tool(
            tool_name="review_expert",
            tool_description="Review specialist. Use for critiquing and improving content quality.",
        ),
    ],
)


# ============================================
# SIMPLER EXAMPLE: Translation Coordinator
# ============================================

spanish_translator = Agent(
    name="SpanishTranslator",
    instructions="You translate text to Spanish. Return ONLY the translation, nothing else.",
    model=create_model(),
)

french_translator = Agent(
    name="FrenchTranslator", 
    instructions="You translate text to French. Return ONLY the translation, nothing else.",
    model=create_model(),
)

german_translator = Agent(
    name="GermanTranslator",
    instructions="You translate text to German. Return ONLY the translation, nothing else.",
    model=create_model(),
)

translation_coordinator = Agent(
    name="TranslationCoordinator",
    instructions="""You coordinate translations to multiple languages.

When user asks to translate something:
1. Use the appropriate translator tools
2. Compile all translations in a nice format
3. Present results clearly

Available tools: spanish_translator, french_translator, german_translator""",
    model=create_model(),
    tools=[
        spanish_translator.as_tool(
            tool_name="spanish_translator",
            tool_description="Translates text to Spanish",
        ),
        french_translator.as_tool(
            tool_name="french_translator",
            tool_description="Translates text to French",
        ),
        german_translator.as_tool(
            tool_name="german_translator",
            tool_description="Translates text to German",
        ),
    ],
)


# ============================================
# RUN EXAMPLES
# ============================================

async def demo_translation():
    """Demo: Translation coordinator"""
    print("\n" + "=" * 60)
    print("📝 DEMO 1: Translation Coordinator")
    print("=" * 60)
    
    query = "Translate 'Hello, how are you?' to Spanish, French, and German"
    print(f"\n👤 User: {query}\n")
    print("🔄 Coordinator calling translator agents...")
    
    result = await Runner.run(
        translation_coordinator,
        query,
        run_config=RunConfig(tracing_disabled=True),
    )
    
    print(f"\n🤖 Final Response:\n{result.final_output}")
    
    # Show that coordinator stayed in control
    print(f"\n📊 Handled by: {result.last_agent.name}")


async def demo_content_creation():
    """Demo: Content creation pipeline"""
    print("\n" + "=" * 60)
    print("📝 DEMO 2: Content Creation Pipeline")
    print("=" * 60)
    
    query = "Create a short paragraph about the benefits of async programming"
    print(f"\n👤 User: {query}\n")
    print("🔄 Coordinator orchestrating: Research → Write → Review...")
    
    result = await Runner.run(
        coordinator_agent,
        query,
        run_config=RunConfig(tracing_disabled=True),
    )
    
    print(f"\n🤖 Final Response:\n{result.final_output}")
    print(f"\n📊 Handled by: {result.last_agent.name}")


async def main():
    print("=" * 60)
    print("🔧 AGENT-AS-TOOL DEMO")
    print("=" * 60)
    print("""
How it works:
1. Coordinator agent receives the task
2. Coordinator calls specialist agents as TOOLS
3. Specialists return results to Coordinator
4. Coordinator compiles final response

Key difference from Handoffs:
- Handoff: Control transfers completely
- As-Tool: Coordinator stays in control
    """)
    
    await demo_translation()
    await asyncio.sleep(1)
    
    await demo_content_creation()
    
    print(f"\n{'='*60}")
    print("✅ Demo complete!")


async def interactive():
    """Interactive mode"""
    print("=" * 60)
    print("🔧 INTERACTIVE AGENT-AS-TOOL DEMO")
    print("=" * 60)
    print("\nChoose a coordinator:")
    print("1. Translation Coordinator (translates to multiple languages)")
    print("2. Content Coordinator (research, write, review)")
    
    choice = input("\nEnter 1 or 2: ").strip()
    
    if choice == "1":
        agent = translation_coordinator
        print("\n📝 Translation Coordinator selected")
        print("Example: 'Translate Good morning to all languages'")
    else:
        agent = coordinator_agent
        print("\n📝 Content Coordinator selected")
        print("Example: 'Write a summary about machine learning'")
    
    print("\nType 'quit' to exit.\n")
    
    while True:
        try:
            query = input("👤 You: ").strip()
            if query.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            if not query:
                continue
            
            print("🔄 Processing...")
            result = await Runner.run(
                agent,
                query,
                run_config=RunConfig(tracing_disabled=True),
            )
            
            print(f"\n🤖 Response:\n{result.final_output}\n")
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        asyncio.run(interactive())
    else:
        asyncio.run(main())
