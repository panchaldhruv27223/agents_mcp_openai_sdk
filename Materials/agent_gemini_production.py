"""
🏭 PRODUCTION-READY: OpenAI Agent with Gemini

Key Principles:
1. NO global settings (set_default_openai_api, set_tracing_disabled)
2. Explicit model configuration per agent
3. Scalable for multi-provider setups
4. Each agent is self-contained and testable

Run: python agent_gemini_production.py test
"""

import asyncio
import os
from openai import AsyncOpenAI
from agents import (
    Agent,
    Runner,
    RunConfig,
    OpenAIChatCompletionsModel,  # Explicit model class
)
from agents.mcp import MCPServerSse


# ============================================
# CONFIGURATION CLASS (Production Pattern)
# ============================================

class GeminiConfig:
    """Centralized configuration for Gemini provider"""
    
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
    
    # Available models
    FLASH = "gemini-2.0-flash"
    FLASH_LITE = "gemini-2.0-flash-lite"
    PRO = "gemini-1.5-pro"
    
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY required. "
                "Set via environment or pass to GeminiConfig(api_key='...')"
            )
        
        # Create the client once
        self._client = AsyncOpenAI(
            base_url=self.BASE_URL,
            api_key=self.api_key,
        )
    
    def get_model(self, model_name: str | None = None) -> OpenAIChatCompletionsModel:
        """
        Factory method to create model instances.
        Each call returns a NEW model instance - safe for concurrent use.
        """
        return OpenAIChatCompletionsModel(
            model=model_name or self.FLASH,
            openai_client=self._client,
        )


# ============================================
# AGENT FACTORY (Production Pattern)
# ============================================

class AgentFactory:
    """
    Factory for creating agents with specific configurations.
    Promotes reusability and testability.
    """
    
    def __init__(self, gemini_config: GeminiConfig):
        self.gemini = gemini_config
    
    def create_task_agent(
        self,
        mcp_servers: list | None = None,
        model_name: str | None = None,
    ) -> Agent:
        """Create a task management agent"""
        return Agent(
            name="TaskAssistant",
            instructions="""You are a task management assistant.
Your capabilities:
- View, create, update, and delete tasks
- Provide task summaries and analysis
Be concise and actionable.""",
            model=self.gemini.get_model(model_name),  # Explicit model!
            mcp_servers=mcp_servers or [],
        )
    
    def create_simple_agent(
        self,
        name: str = "Assistant",
        instructions: str = "You are a helpful assistant.",
        model_name: str | None = None,
    ) -> Agent:
        """Create a simple chat agent"""
        return Agent(
            name=name,
            instructions=instructions,
            model=self.gemini.get_model(model_name),  # Explicit model!
        )


# ============================================
# RUNNER WRAPPER (Optional - for tracing control)
# ============================================

async def run_agent(
    agent: Agent,
    query: str,
    run_config: RunConfig | None = None,
) -> str:
    """
    Wrapper for running agents with consistent configuration.
    In production, you might add: logging, metrics, error handling.
    """
    config = run_config or RunConfig(
        tracing_disabled=True,  # Per-run tracing control, NOT global!
    )
    
    result = await Runner.run(
        agent,
        query,
        run_config=config,
    )
    
    return result.final_output


# ============================================
# EXAMPLE: Simple Test
# ============================================

async def simple_test():
    """Test basic Gemini connection"""
    print("🧪 Testing Production Setup...")
    print("-" * 50)
    
    # Initialize configuration
    config = GeminiConfig()
    factory = AgentFactory(config)
    
    # Create agent with explicit model
    agent = factory.create_simple_agent()
    
    # Run with explicit tracing control
    response = await run_agent(
        agent,
        "Hello! What AI model are you? One sentence only.",
    )
    
    print(f"🤖 Response: {response}")


# ============================================
# EXAMPLE: With MCP Server
# ============================================

async def mcp_demo():
    """Demo with MCP server"""
    print("🤖 Production Demo with MCP...")
    print("-" * 50)
    
    config = GeminiConfig()
    factory = AgentFactory(config)
    
    async with MCPServerSse(
        name="TaskManager",
        params={"url": "http://localhost:8000/sse"},
        cache_tools_list=True,
    ) as mcp_server:
        
        # Create agent with MCP
        agent = factory.create_task_agent(mcp_servers=[mcp_server])
        
        queries = [
            "Show me all tasks",
            "Create a high priority task: 'Deploy to production'",
            "Give me a summary",
        ]
        
        for query in queries:
            print(f"\n👤 Query: {query}")
            response = await run_agent(agent, query)
            print(f"🤖 Response: {response}")


# ============================================
# EXAMPLE: Multi-Provider Setup
# ============================================

async def multi_provider_demo():
    """
    Shows how to use multiple providers in the same application.
    This is where explicit configuration really shines!
    """
    print("🌐 Multi-Provider Demo...")
    print("-" * 50)
    
    gemini_config = GeminiConfig()
    
    # You could add more providers here:
    # openai_config = OpenAIConfig()
    # anthropic_config = AnthropicConfig()
    
    # Create specialized agents with different models
    fast_agent = Agent(
        name="FastAgent",
        instructions="Quick, concise responses only.",
        model=gemini_config.get_model(GeminiConfig.FLASH_LITE),
    )
    
    smart_agent = Agent(
        name="SmartAgent", 
        instructions="Detailed, thoughtful analysis.",
        model=gemini_config.get_model(GeminiConfig.PRO),
    )
    
    # Use appropriate agent based on task
    print("\n⚡ Fast Agent (gemini-2.0-flash-lite):")
    fast_response = await run_agent(fast_agent, "What is 2+2?")
    print(f"   {fast_response}")
    
    print("\n🧠 Smart Agent (gemini-1.5-pro):")
    smart_response = await run_agent(
        smart_agent, 
        "Explain quantum entanglement briefly."
    )
    print(f"   {smart_response}")


# ============================================
# INTERACTIVE MODE
# ============================================

async def interactive():
    """Interactive chat mode"""
    print("=" * 50)
    print("💬 PRODUCTION TASK ASSISTANT")
    print("=" * 50)
    
    config = GeminiConfig()
    factory = AgentFactory(config)
    
    async with MCPServerSse(
        name="TaskManager",
        params={"url": "http://localhost:8000/sse"},
        cache_tools_list=True,
    ) as mcp_server:
        
        agent = factory.create_task_agent(mcp_servers=[mcp_server])
        print("✅ Ready! Type 'quit' to exit.\n")
        
        while True:
            try:
                user_input = input("👤 You: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                
                if not user_input:
                    continue
                
                response = await run_agent(agent, user_input)
                print(f"🤖 Agent: {response}\n")
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}\n")


# ============================================
# ENTRY POINT
# ============================================

if __name__ == "__main__":
    import sys
    
    commands = {
        "test": simple_test,
        "demo": mcp_demo,
        "multi": multi_provider_demo,
    }
    
    if len(sys.argv) > 1 and sys.argv[1] in commands:
        asyncio.run(commands[sys.argv[1]]())
    elif len(sys.argv) > 1:
        print("Usage:")
        print("  python agent_gemini_production.py test   # Simple test")
        print("  python agent_gemini_production.py demo   # MCP demo")
        print("  python agent_gemini_production.py multi  # Multi-model demo")
        print("  python agent_gemini_production.py        # Interactive mode")
    else:
        asyncio.run(interactive())
