"""
🏭 PRODUCTION ARCHITECTURE: Multi-Provider Model Registry

Handles:
1. Different model types (Responses API vs Chat Completions)
2. Provider-specific capabilities
3. Feature validation at runtime
4. Easy provider switching
5. Scalable for 10+ providers

Run: python model_registry.py demo
"""

import os
from enum import Enum
from dataclasses import dataclass, field
from typing import Protocol, Any
from openai import AsyncOpenAI
from agents import (
    Agent,
    Runner,
    RunConfig,
    OpenAIChatCompletionsModel,
    OpenAIResponsesModel,
)


# ============================================
# 1. DEFINE CAPABILITIES
# ============================================

class ModelCapability(Enum):
    """What features does a provider support?"""
    CHAT = "chat"                      # Basic chat
    TOOL_CALLING = "tool_calling"      # Function/tool calls
    VISION = "vision"                  # Image input
    STREAMING = "streaming"            # Stream responses
    STRUCTURED_OUTPUT = "structured"   # JSON mode / structured output
    WEB_SEARCH = "web_search"          # Built-in web search (OpenAI only)
    FILE_SEARCH = "file_search"        # Built-in file search (OpenAI only)
    CODE_INTERPRETER = "code_interpreter"  # (OpenAI only)


class ModelType(Enum):
    """Which API shape to use?"""
    RESPONSES = "responses"            # OpenAI Responses API
    CHAT_COMPLETIONS = "chat_completions"  # Standard Chat Completions


# ============================================
# 2. PROVIDER CONFIGURATION
# ============================================

@dataclass
class ProviderConfig:
    """Configuration for a single provider"""
    name: str
    base_url: str
    api_key_env: str                   # Environment variable name
    default_model: str
    model_type: ModelType
    capabilities: set[ModelCapability]
    models: dict[str, str] = field(default_factory=dict)  # alias -> actual name
    api_key_override: str | None = None  # For providers that don't need real key
    
    def get_api_key(self) -> str:
        """Get API key from env or override"""
        if self.api_key_override:
            return self.api_key_override
        key = os.getenv(self.api_key_env)
        if not key:
            raise ValueError(f"Missing API key: {self.api_key_env}")
        return key
    
    def supports(self, *caps: ModelCapability) -> bool:
        """Check if provider supports all given capabilities"""
        return all(cap in self.capabilities for cap in caps)


# ============================================
# 3. PROVIDER REGISTRY
# ============================================

class ProviderRegistry:
    """
    Central registry for all providers.
    Add new providers here - single source of truth.
    """
    
    PROVIDERS: dict[str, ProviderConfig] = {
        
        # ===== OpenAI (Full Features) =====
        "openai": ProviderConfig(
            name="OpenAI",
            base_url="https://api.openai.com/v1",
            api_key_env="OPENAI_API_KEY",
            default_model="gpt-4o",
            model_type=ModelType.RESPONSES,  # <-- Responses API!
            capabilities={
                ModelCapability.CHAT,
                ModelCapability.TOOL_CALLING,
                ModelCapability.VISION,
                ModelCapability.STREAMING,
                ModelCapability.STRUCTURED_OUTPUT,
                ModelCapability.WEB_SEARCH,        # Exclusive
                ModelCapability.FILE_SEARCH,       # Exclusive
                ModelCapability.CODE_INTERPRETER,  # Exclusive
            },
            models={
                "fast": "gpt-4o-mini",
                "smart": "gpt-4o",
                "reasoning": "o1",
            },
        ),
        
        # ===== Gemini =====
        "gemini": ProviderConfig(
            name="Google Gemini",
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            api_key_env="GEMINI_API_KEY",
            default_model="gemini-2.0-flash",
            model_type=ModelType.CHAT_COMPLETIONS,  # <-- Chat Completions!
            capabilities={
                ModelCapability.CHAT,
                ModelCapability.TOOL_CALLING,
                ModelCapability.VISION,
                ModelCapability.STREAMING,
                ModelCapability.STRUCTURED_OUTPUT,
            },
            models={
                "fast": "gemini-2.0-flash",
                "faster": "gemini-2.0-flash-lite",
                "smart": "gemini-1.5-pro",
            },
        ),
        
        # ===== Ollama (Local) =====
        "ollama": ProviderConfig(
            name="Ollama (Local)",
            base_url="http://localhost:11434/v1",
            api_key_env="OLLAMA_API_KEY",
            api_key_override="ollama",  # Doesn't need real key
            default_model="llama3.2",
            model_type=ModelType.CHAT_COMPLETIONS,
            capabilities={
                ModelCapability.CHAT,
                ModelCapability.TOOL_CALLING,  # Most models support this
                ModelCapability.STREAMING,
            },
            models={
                "fast": "llama3.2",
                "smart": "llama3.1:70b",
                "code": "codellama",
                "small": "phi3",
            },
        ),
        
        # ===== Groq (Fast Inference) =====
        "groq": ProviderConfig(
            name="Groq",
            base_url="https://api.groq.com/openai/v1",
            api_key_env="GROQ_API_KEY",
            default_model="llama-3.3-70b-versatile",
            model_type=ModelType.CHAT_COMPLETIONS,
            capabilities={
                ModelCapability.CHAT,
                ModelCapability.TOOL_CALLING,
                ModelCapability.VISION,
                ModelCapability.STREAMING,
            },
            models={
                "fast": "llama-3.1-8b-instant",
                "smart": "llama-3.3-70b-versatile",
                "vision": "llama-3.2-90b-vision-preview",
            },
        ),
        
        # ===== Azure OpenAI =====
        "azure": ProviderConfig(
            name="Azure OpenAI",
            base_url="",  # Set via AZURE_OPENAI_ENDPOINT
            api_key_env="AZURE_OPENAI_API_KEY",
            default_model="gpt-4o",
            model_type=ModelType.CHAT_COMPLETIONS,  # Azure uses Chat Completions
            capabilities={
                ModelCapability.CHAT,
                ModelCapability.TOOL_CALLING,
                ModelCapability.VISION,
                ModelCapability.STREAMING,
                ModelCapability.STRUCTURED_OUTPUT,
            },
            models={
                "fast": "gpt-4o-mini",
                "smart": "gpt-4o",
            },
        ),
        
        # ===== Together AI =====
        "together": ProviderConfig(
            name="Together AI",
            base_url="https://api.together.xyz/v1",
            api_key_env="TOGETHER_API_KEY",
            default_model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
            model_type=ModelType.CHAT_COMPLETIONS,
            capabilities={
                ModelCapability.CHAT,
                ModelCapability.TOOL_CALLING,
                ModelCapability.STREAMING,
            },
            models={
                "fast": "meta-llama/Llama-3.2-3B-Instruct-Turbo",
                "smart": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
                "mixtral": "mistralai/Mixtral-8x22B-Instruct-v0.1",
            },
        ),
        
        # ===== Anthropic (via proxy/gateway) =====
        "anthropic": ProviderConfig(
            name="Anthropic Claude",
            base_url="https://api.anthropic.com/v1",  # Need adapter/gateway
            api_key_env="ANTHROPIC_API_KEY",
            default_model="claude-sonnet-4-20250514",
            model_type=ModelType.CHAT_COMPLETIONS,
            capabilities={
                ModelCapability.CHAT,
                ModelCapability.TOOL_CALLING,
                ModelCapability.VISION,
                ModelCapability.STREAMING,
            },
            models={
                "fast": "claude-haiku-4-20250514",
                "smart": "claude-sonnet-4-20250514",
                "smartest": "claude-opus-4-20250514",
            },
        ),
        
        # ===== LM Studio (Local) =====
        "lmstudio": ProviderConfig(
            name="LM Studio (Local)",
            base_url="http://localhost:1234/v1",
            api_key_env="LMSTUDIO_API_KEY",
            api_key_override="lm-studio",
            default_model="local-model",
            model_type=ModelType.CHAT_COMPLETIONS,
            capabilities={
                ModelCapability.CHAT,
                ModelCapability.STREAMING,
            },
            models={},
        ),
    }
    
    @classmethod
    def get(cls, provider_name: str) -> ProviderConfig:
        """Get provider config by name"""
        if provider_name not in cls.PROVIDERS:
            available = ", ".join(cls.PROVIDERS.keys())
            raise ValueError(f"Unknown provider: {provider_name}. Available: {available}")
        return cls.PROVIDERS[provider_name]
    
    @classmethod
    def list_providers(cls) -> list[str]:
        """List all available providers"""
        return list(cls.PROVIDERS.keys())
    
    @classmethod
    def find_by_capability(cls, *caps: ModelCapability) -> list[str]:
        """Find providers that support given capabilities"""
        return [
            name for name, config in cls.PROVIDERS.items()
            if config.supports(*caps)
        ]


# ============================================
# 4. MODEL FACTORY
# ============================================

class ModelFactory:
    """
    Creates the correct model instance based on provider.
    Handles the Responses vs ChatCompletions difference.
    """
    
    _clients: dict[str, AsyncOpenAI] = {}
    
    @classmethod
    def _get_client(cls, provider_name: str) -> AsyncOpenAI:
        """Get or create client for provider (cached)"""
        if provider_name not in cls._clients:
            config = ProviderRegistry.get(provider_name)
            cls._clients[provider_name] = AsyncOpenAI(
                base_url=config.base_url,
                api_key=config.get_api_key(),
            )
        return cls._clients[provider_name]
    
    @classmethod
    def create(
        cls,
        provider_name: str,
        model_alias: str | None = None,
        model_name: str | None = None,
    ) -> OpenAIChatCompletionsModel | OpenAIResponsesModel:
        """
        Create appropriate model instance.
        
        Args:
            provider_name: Provider key (gemini, openai, ollama, etc.)
            model_alias: Friendly name (fast, smart, etc.)
            model_name: Exact model name (overrides alias)
        
        Returns:
            Correct model instance for the provider
        """
        config = ProviderRegistry.get(provider_name)
        client = cls._get_client(provider_name)
        
        # Resolve model name
        if model_name:
            resolved_model = model_name
        elif model_alias and model_alias in config.models:
            resolved_model = config.models[model_alias]
        else:
            resolved_model = config.default_model
        
        # Create correct model type
        if config.model_type == ModelType.RESPONSES:
            return OpenAIResponsesModel(
                model=resolved_model,
                openai_client=client,
            )
        else:
            return OpenAIChatCompletionsModel(
                model=resolved_model,
                openai_client=client,
            )
    
    @classmethod
    def validate_capabilities(
        cls,
        provider_name: str,
        required: set[ModelCapability],
    ) -> None:
        """Validate provider supports required capabilities"""
        config = ProviderRegistry.get(provider_name)
        missing = required - config.capabilities
        if missing:
            raise ValueError(
                f"Provider '{provider_name}' doesn't support: {[c.value for c in missing]}. "
                f"Consider using: {ProviderRegistry.find_by_capability(*required)}"
            )


# ============================================
# 5. AGENT BUILDER (High-level API)
# ============================================

class AgentBuilder:
    """
    Fluent builder for creating agents with validation.
    Ensures you don't use unsupported features.
    """
    
    def __init__(self):
        self._name: str = "Agent"
        self._instructions: str = "You are a helpful assistant."
        self._provider: str = "gemini"
        self._model_alias: str | None = None
        self._model_name: str | None = None
        self._tools: list = []
        self._mcp_servers: list = []
        self._required_caps: set[ModelCapability] = {ModelCapability.CHAT}
    
    def name(self, name: str) -> "AgentBuilder":
        self._name = name
        return self
    
    def instructions(self, instructions: str) -> "AgentBuilder":
        self._instructions = instructions
        return self
    
    def provider(self, provider: str, model: str | None = None) -> "AgentBuilder":
        """Set provider and optionally model alias"""
        self._provider = provider
        self._model_alias = model
        return self
    
    def model(self, exact_name: str) -> "AgentBuilder":
        """Set exact model name"""
        self._model_name = exact_name
        return self
    
    def with_tools(self, tools: list) -> "AgentBuilder":
        """Add tools (requires TOOL_CALLING capability)"""
        self._tools = tools
        self._required_caps.add(ModelCapability.TOOL_CALLING)
        return self
    
    def with_mcp(self, servers: list) -> "AgentBuilder":
        """Add MCP servers (requires TOOL_CALLING)"""
        self._mcp_servers = servers
        self._required_caps.add(ModelCapability.TOOL_CALLING)
        return self
    
    def with_vision(self) -> "AgentBuilder":
        """Mark that agent needs vision"""
        self._required_caps.add(ModelCapability.VISION)
        return self
    
    def with_structured_output(self) -> "AgentBuilder":
        """Mark that agent needs structured output"""
        self._required_caps.add(ModelCapability.STRUCTURED_OUTPUT)
        return self
    
    def build(self) -> Agent:
        """Build the agent with validation"""
        # Validate capabilities
        ModelFactory.validate_capabilities(self._provider, self._required_caps)
        
        # Create model
        model = ModelFactory.create(
            self._provider,
            model_alias=self._model_alias,
            model_name=self._model_name,
        )
        
        # Build agent
        return Agent(
            name=self._name,
            instructions=self._instructions,
            model=model,
            tools=self._tools,
            mcp_servers=self._mcp_servers,
        )


# ============================================
# 6. USAGE EXAMPLES
# ============================================

async def demo():
    """Demonstrate the registry pattern"""
    
    print("=" * 60)
    print("🏭 PRODUCTION MODEL REGISTRY DEMO")
    print("=" * 60)
    
    # List all providers
    print("\n📦 Available Providers:")
    for name in ProviderRegistry.list_providers():
        config = ProviderRegistry.get(name)
        caps = [c.value for c in config.capabilities]
        print(f"   • {name}: {config.model_type.value} | {caps[:3]}...")
    
    # Find providers by capability
    print("\n🔍 Providers with WEB_SEARCH:")
    web_providers = ProviderRegistry.find_by_capability(ModelCapability.WEB_SEARCH)
    print(f"   {web_providers}")
    
    print("\n🔍 Providers with TOOL_CALLING + VISION:")
    vision_providers = ProviderRegistry.find_by_capability(
        ModelCapability.TOOL_CALLING, 
        ModelCapability.VISION
    )
    print(f"   {vision_providers}")
    
    # Build agent with validation
    print("\n🔨 Building Agent with Gemini...")
    try:
        agent = (
            AgentBuilder()
            .name("TaskBot")
            .instructions("You help with tasks.")
            .provider("gemini", model="fast")
            .with_tools([])  # Would add real tools here
            .build()
        )
        print(f"   ✅ Created: {agent.name}")
    except ValueError as e:
        print(f"   ❌ Error: {e}")
    
    # Try to use unsupported capability
    print("\n🔨 Trying WEB_SEARCH with Ollama (should fail)...")
    try:
        # This would fail validation
        config = ProviderRegistry.get("ollama")
        ModelFactory.validate_capabilities(
            "ollama",
            {ModelCapability.WEB_SEARCH}
        )
    except ValueError as e:
        print(f"   ❌ Expected error: {e}")
    
    # Run actual agent (if Gemini key available)
    print("\n🤖 Running Agent...")
    if os.getenv("GEMINI_API_KEY"):
        agent = (
            AgentBuilder()
            .name("QuickBot")
            .instructions("Be concise.")
            .provider("gemini", model="fast")
            .build()
        )
        
        result = await Runner.run(
            agent,
            "What is 2+2? One word answer.",
            run_config=RunConfig(tracing_disabled=True),
        )
        print(f"   Response: {result.final_output}")
    else:
        print("   ⚠️  Set GEMINI_API_KEY to test")


async def multi_provider_example():
    """Show using multiple providers in same app"""
    
    print("\n" + "=" * 60)
    print("🌐 MULTI-PROVIDER EXAMPLE")
    print("=" * 60)
    
    # Different agents for different tasks
    agents_config = [
        ("gemini", "fast", "Quick tasks"),
        ("gemini", "smart", "Complex reasoning"),
        # ("openai", "smart", "With web search"),  # Uncomment if you have key
        # ("ollama", "fast", "Local/private"),
    ]
    
    for provider, model, purpose in agents_config:
        try:
            config = ProviderRegistry.get(provider)
            print(f"\n📦 {config.name} ({model}): {purpose}")
            print(f"   Model: {config.models.get(model, config.default_model)}")
            print(f"   Type: {config.model_type.value}")
        except Exception as e:
            print(f"   ❌ {e}")


# ============================================
# ENTRY POINT
# ============================================

if __name__ == "__main__":
    import asyncio
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        asyncio.run(demo())
    elif len(sys.argv) > 1 and sys.argv[1] == "multi":
        asyncio.run(multi_provider_example())
    else:
        print("Usage:")
        print("  python model_registry.py demo   # Full demo")
        print("  python model_registry.py multi  # Multi-provider example")
