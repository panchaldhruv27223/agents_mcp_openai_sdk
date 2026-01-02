"""
=============================================================================
OPENAI AGENTS SDK - ADVANCED MCP (Model Context Protocol)
=============================================================================

Topics:
1. MCP Server Types (Stdio, SSE, HTTP)
2. Multiple MCP Servers
3. MCP Resources (not just tools!)
4. MCP Prompts
5. Hosted MCP Tools
6. MCP Configuration & Authentication
7. Server Lifecycle Management
8. MCP with Streaming
9. Error Handling
10. Building Production MCP Servers
"""

import asyncio
from agents import Agent, Runner, RunContextWrapper
from agents.mcp import (
    MCPServerStdio,
    MCPServerSse, 
    MCPServerStreamableHttp,
    MCPServer,
)
from dataclasses import dataclass
from typing import Any
from dotenv import load_dotenv

load_dotenv()


# =============================================================================
# 1. MCP SERVER TYPES
# =============================================================================

"""
┌─────────────────────────────────────────────────────────────────────────────┐
│                        MCP SERVER TYPES                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  MCPServerStdio                                                             │
│  ───────────────                                                            │
│  • Spawns a subprocess                                                      │
│  • Communicates via stdin/stdout                                            │
│  • Best for: Local tools, CLI-based servers                                 │
│  • Example: File system access, local database                              │
│                                                                              │
│  ┌─────────┐      stdin/stdout      ┌─────────────────┐                    │
│  │  Agent  │ ◄──────────────────►   │  MCP Process    │                    │
│  └─────────┘                        │  (subprocess)   │                    │
│                                     └─────────────────┘                    │
│                                                                              │
│  MCPServerSse                                                               │
│  ─────────────                                                              │
│  • Connects to HTTP server with Server-Sent Events                         │
│  • Best for: Remote servers, cloud services                                │
│  • Example: Third-party APIs, remote databases                             │
│                                                                              │
│  ┌─────────┐        HTTP/SSE        ┌─────────────────┐                    │
│  │  Agent  │ ◄──────────────────►   │  Remote Server  │                    │
│  └─────────┘                        │  (HTTP + SSE)   │                    │
│                                     └─────────────────┘                    │
│                                                                              │
│  MCPServerStreamableHttp                                                    │
│  ────────────────────────                                                   │
│  • HTTP with streaming support                                              │
│  • Best for: Large responses, real-time data                               │
│  • Example: Log streaming, live data feeds                                 │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
"""


# --- MCPServerStdio Example ---
async def demo_stdio_server():
    """
    Stdio server - spawns a local process.
    Good for: Local file system, local databases, CLI tools.
    """
    
    # Option 1: Python MCP server
    python_server = MCPServerStdio(
        name="LocalFileServer",
        command="python",
        args=["mcp_servers/file_server.py"],
        # Environment variables for the subprocess
        env={
            "DATA_DIR": "/path/to/data",
            "LOG_LEVEL": "INFO",
        },
    )
    
    # Option 2: Node.js MCP server
    node_server = MCPServerStdio(
        name="NodeMCPServer",
        command="npx",
        args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
    )
    
    # Option 3: uvx (Python package runner)
    uvx_server = MCPServerStdio(
        name="GitServer",
        command="uvx",
        args=["mcp-server-git", "--repository", "/path/to/repo"],
    )
    
    return python_server


# --- MCPServerSse Example ---
async def demo_sse_server():
    """
    SSE server - connects to remote HTTP server.
    Good for: Cloud services, third-party APIs.
    """
    
    # Remote MCP server
    sse_server = MCPServerSse(
        name="RemoteAPIServer",
        url="https://mcp.example.com/sse",
        # Optional: Authentication headers
        headers={
            "Authorization": "Bearer your-api-key",
            "X-Custom-Header": "value",
        },
        # Optional: Connection timeout
        timeout=30.0,
    )
    
    return sse_server


# --- MCPServerStreamableHttp Example ---
async def demo_http_server():
    """
    Streamable HTTP server - for large/streaming responses.
    """
    
    http_server = MCPServerStreamableHttp(
        name="StreamingServer",
        url="https://mcp.example.com/stream",
        headers={
            "Authorization": "Bearer your-api-key",
        },
    )
    
    return http_server


# =============================================================================
# 2. MULTIPLE MCP SERVERS
# =============================================================================

"""
┌─────────────────────────────────────────────────────────────────────────────┐
│                      MULTIPLE MCP SERVERS                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│                         ┌─────────────────────┐                             │
│                    ┌───►│  File System MCP    │                             │
│                    │    └─────────────────────┘                             │
│                    │                                                        │
│   ┌─────────┐      │    ┌─────────────────────┐                             │
│   │  Agent  │ ─────┼───►│  Database MCP       │                             │
│   └─────────┘      │    └─────────────────────┘                             │
│                    │                                                        │
│                    │    ┌─────────────────────┐                             │
│                    └───►│  External API MCP   │                             │
│                         └─────────────────────┘                             │
│                                                                              │
│   Agent sees tools from ALL servers!                                        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
"""


async def demo_multiple_servers():
    """
    Using multiple MCP servers with one agent.
    """
    
    # Server 1: File operations
    file_server = MCPServerStdio(
        name="FileServer",
        command="python",
        args=["mcp_servers/file_server.py"],
    )
    
    # Server 2: Database operations
    db_server = MCPServerStdio(
        name="DatabaseServer", 
        command="python",
        args=["mcp_servers/db_server.py"],
    )
    
    # Server 3: External API
    api_server = MCPServerSse(
        name="ExternalAPI",
        url="https://api.example.com/mcp",
    )
    
    # Connect all servers
    async with file_server, db_server, api_server:
        
        # Agent has access to tools from ALL servers
        agent = Agent(
            name="MultiMCPAgent",
            instructions="""You have access to:
            - File operations (read, write, list)
            - Database operations (query, insert, update)
            - External API (fetch data, send requests)
            
            Use the appropriate tools for each task.""",
            mcp_servers=[file_server, db_server, api_server],  # All three!
        )
        
        result = await Runner.run(
            agent,
            "Read config.json, query users table, and fetch weather data"
        )
        
        print(result.final_output)


# =============================================================================
# 3. MCP RESOURCES (Not Just Tools!)
# =============================================================================

"""
┌─────────────────────────────────────────────────────────────────────────────┐
│                         MCP RESOURCES                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  MCP provides THREE primitives:                                             │
│                                                                              │
│  1. TOOLS     - Functions the agent can call                                │
│                 @mcp.tool()                                                 │
│                                                                              │
│  2. RESOURCES - Data/files the agent can read                               │
│                 @mcp.resource()                                             │
│                 Like a file system or database                              │
│                                                                              │
│  3. PROMPTS   - Reusable prompt templates                                   │
│                 @mcp.prompt()                                               │
│                 Pre-defined conversation starters                           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
"""

# --- Example MCP Server with Resources (FastMCP) ---

FASTMCP_RESOURCES_EXAMPLE = '''
from fastmcp import FastMCP

mcp = FastMCP("ResourceServer")

# ═══════════════════════════════════════════════════════════════════
# TOOLS - Agent can CALL these
# ═══════════════════════════════════════════════════════════════════

@mcp.tool()
def search_documents(query: str) -> str:
    """Search documents by query."""
    return f"Found 5 documents matching: {query}"


@mcp.tool()
def create_document(title: str, content: str) -> str:
    """Create a new document."""
    return f"Created document: {title}"


# ═══════════════════════════════════════════════════════════════════
# RESOURCES - Agent can READ these (like files)
# ═══════════════════════════════════════════════════════════════════

@mcp.resource("file://config.json")
def get_config() -> str:
    """Application configuration."""
    return """{"app": "MyApp", "version": "1.0", "debug": true}"""


@mcp.resource("file://users/{user_id}")
def get_user(user_id: str) -> str:
    """Get user by ID."""
    return f'{{"id": "{user_id}", "name": "John Doe", "email": "john@example.com"}}'


@mcp.resource("db://schema")
def get_database_schema() -> str:
    """Database schema information."""
    return """
    Tables:
    - users (id, name, email, created_at)
    - orders (id, user_id, total, status)
    - products (id, name, price, stock)
    """


# Dynamic resource with template
@mcp.resource("logs://{date}")
def get_logs(date: str) -> str:
    """Get logs for a specific date."""
    return f"Logs for {date}: [INFO] App started, [WARN] High memory..."


# ═══════════════════════════════════════════════════════════════════
# PROMPTS - Reusable prompt templates
# ═══════════════════════════════════════════════════════════════════

@mcp.prompt()
def code_review_prompt(code: str, language: str) -> str:
    """Prompt for code review."""
    return f"""Please review this {language} code:

```{language}
{code}
```

Check for:
1. Bugs and errors
2. Performance issues
3. Security vulnerabilities
4. Code style
"""


@mcp.prompt()
def sql_query_prompt(tables: str, question: str) -> str:
    """Prompt for SQL query generation."""
    return f"""Given these tables:
{tables}

Write a SQL query to answer: {question}
"""


if __name__ == "__main__":
    mcp.run()
'''


# --- Using Resources in Agent ---

async def demo_resources():
    """
    Using MCP resources with an agent.
    """
    
    server = MCPServerStdio(
        name="ResourceServer",
        command="python",
        args=["mcp_servers/resource_server.py"],
    )
    
    async with server:
        # List available resources
        resources = await server.list_resources()
        print("Available resources:")
        for r in resources:
            print(f"  - {r.uri}: {r.description}")
        
        # Read a specific resource
        config = await server.read_resource("file://config.json")
        print(f"\nConfig: {config}")
        
        # Agent can use resources as context
        agent = Agent(
            name="ResourceAgent",
            instructions=f"""You have access to these resources:
            {[r.uri for r in resources]}
            
            Use tools to interact, and resources for context.""",
            mcp_servers=[server],
        )


# =============================================================================
# 4. MCP PROMPTS
# =============================================================================

"""
┌─────────────────────────────────────────────────────────────────────────────┐
│                          MCP PROMPTS                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Prompts are reusable templates provided by MCP servers.                    │
│                                                                              │
│  Use cases:                                                                  │
│  - Code review templates                                                    │
│  - SQL query generation                                                     │
│  - Document analysis                                                        │
│  - Standardized workflows                                                   │
│                                                                              │
│  MCP Server                             Agent                               │
│  ┌─────────────────┐                   ┌─────────────────┐                 │
│  │ @mcp.prompt()   │                   │ List prompts    │                 │
│  │ code_review     │ ◄─────────────►   │ Get prompt      │                 │
│  │ sql_query       │                   │ Use as input    │                 │
│  └─────────────────┘                   └─────────────────┘                 │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
"""


async def demo_prompts():
    """
    Using MCP prompts.
    """
    
    server = MCPServerStdio(
        name="PromptServer",
        command="python", 
        args=["mcp_servers/prompt_server.py"],
    )
    
    async with server:
        # List available prompts
        prompts = await server.list_prompts()
        print("Available prompts:")
        for p in prompts:
            print(f"  - {p.name}: {p.description}")
        
        # Get a specific prompt with arguments
        prompt_result = await server.get_prompt(
            "code_review_prompt",
            arguments={
                "code": "def hello(): print('world')",
                "language": "python",
            }
        )
        
        print(f"\nGenerated prompt:\n{prompt_result}")
        
        # Use the prompt with an agent
        agent = Agent(
            name="ReviewAgent",
            instructions="You are a code reviewer.",
        )
        
        result = await Runner.run(agent, prompt_result)
        print(f"\nReview: {result.final_output}")


# =============================================================================
# 5. HOSTED MCP TOOLS (OpenAI's Managed MCP)
# =============================================================================

"""
┌─────────────────────────────────────────────────────────────────────────────┐
│                       HOSTED MCP TOOLS                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  OpenAI provides HOSTED MCP tools that run on their infrastructure:         │
│                                                                              │
│  • HostedMCPTool - Connect to OpenAI-hosted MCP servers                    │
│  • No need to run your own server                                           │
│  • Examples: Remote file access, managed databases                          │
│                                                                              │
│  ┌─────────┐                          ┌─────────────────────┐              │
│  │  Agent  │ ◄────────────────────►   │  OpenAI Hosted MCP  │              │
│  └─────────┘       API calls          │  (managed by OpenAI)│              │
│                                       └─────────────────────┘              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
"""

from agents.tool import HostedMCPTool


async def demo_hosted_mcp():
    """
    Using OpenAI's hosted MCP tools.
    """
    
    # Hosted MCP tool (runs on OpenAI's infrastructure)
    hosted_tool = HostedMCPTool(
        tool_config={
            "type": "mcp",
            "server_label": "deepwiki",  # OpenAI-hosted server
            "server_url": "https://mcp.deepwiki.com/mcp",
            "require_approval": "never",  # or "always" for confirmation
        }
    )
    
    agent = Agent(
        name="WikiAgent",
        instructions="You can search and read wiki articles.",
        tools=[hosted_tool],
    )
    
    result = await Runner.run(agent, "What is quantum computing?")
    print(result.final_output)


# =============================================================================
# 6. MCP CONFIGURATION & AUTHENTICATION
# =============================================================================

"""
┌─────────────────────────────────────────────────────────────────────────────┐
│                    MCP CONFIGURATION                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  mcp_config parameter on Agent:                                             │
│                                                                              │
│  • Tool filtering (include/exclude tools)                                   │
│  • Authentication                                                           │
│  • Custom headers                                                           │
│  • Timeout settings                                                         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
"""


async def demo_mcp_config():
    """
    Advanced MCP configuration.
    """
    
    server = MCPServerSse(
        name="SecureServer",
        url="https://mcp.example.com/sse",
        headers={
            "Authorization": "Bearer secret-token",
            "X-API-Version": "2.0",
        },
    )
    
    async with server:
        agent = Agent(
            name="ConfiguredAgent",
            instructions="Use available tools.",
            mcp_servers=[server],
            # MCP configuration
            mcp_config={
                # Filter which tools the agent can see
                "allowed_tools": ["read_file", "list_files"],  # Only these
                # Or exclude specific tools
                # "excluded_tools": ["delete_file", "write_file"],
                
                # Convert tool results to content blocks
                "convert_tool_results_to_content_blocks": True,
            },
        )
        
        result = await Runner.run(agent, "List all files")
        print(result.final_output)


# --- Authentication Patterns ---

async def demo_auth_patterns():
    """
    Different authentication patterns for MCP servers.
    """
    
    # Pattern 1: API Key in headers
    api_key_server = MCPServerSse(
        name="APIKeyServer",
        url="https://mcp.example.com/sse",
        headers={
            "X-API-Key": "your-api-key",
        },
    )
    
    # Pattern 2: Bearer token
    bearer_server = MCPServerSse(
        name="BearerServer",
        url="https://mcp.example.com/sse",
        headers={
            "Authorization": "Bearer your-jwt-token",
        },
    )
    
    # Pattern 3: Environment variables for Stdio
    env_server = MCPServerStdio(
        name="EnvServer",
        command="python",
        args=["server.py"],
        env={
            "DATABASE_URL": "postgresql://...",
            "API_KEY": "secret",
            "ENV": "production",
        },
    )
    
    # Pattern 4: Dynamic token (refresh before use)
    async def get_fresh_token():
        # Call your auth service
        return "fresh-token"
    
    token = await get_fresh_token()
    dynamic_server = MCPServerSse(
        name="DynamicAuthServer",
        url="https://mcp.example.com/sse",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )


# =============================================================================
# 7. SERVER LIFECYCLE MANAGEMENT
# =============================================================================

"""
┌─────────────────────────────────────────────────────────────────────────────┐
│                   SERVER LIFECYCLE                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Important: MCP servers must be properly started and stopped!               │
│                                                                              │
│  1. Context Manager (recommended)                                           │
│     async with server:                                                      │
│         # use server                                                        │
│     # automatically cleaned up                                              │
│                                                                              │
│  2. Manual Management                                                       │
│     await server.connect()                                                  │
│     try:                                                                    │
│         # use server                                                        │
│     finally:                                                                │
│         await server.cleanup()                                              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
"""


async def demo_lifecycle():
    """
    Proper MCP server lifecycle management.
    """
    
    # Method 1: Context manager (RECOMMENDED)
    server = MCPServerStdio(
        name="Server",
        command="python",
        args=["server.py"],
    )
    
    async with server:
        # Server is connected
        agent = Agent(name="Agent", mcp_servers=[server])
        await Runner.run(agent, "Do something")
    # Server is automatically cleaned up
    
    
    # Method 2: Manual management
    server = MCPServerStdio(
        name="Server",
        command="python",
        args=["server.py"],
    )
    
    await server.connect()
    try:
        agent = Agent(name="Agent", mcp_servers=[server])
        await Runner.run(agent, "Do something")
    finally:
        await server.cleanup()
    
    
    # Method 3: Multiple servers with context manager
    server1 = MCPServerStdio(name="S1", command="python", args=["s1.py"])
    server2 = MCPServerStdio(name="S2", command="python", args=["s2.py"])
    
    async with server1, server2:
        agent = Agent(
            name="Agent",
            mcp_servers=[server1, server2],
        )
        await Runner.run(agent, "Do something")


# --- Reconnection Handling ---

async def demo_reconnection():
    """
    Handle disconnections and reconnect.
    """
    
    server = MCPServerSse(
        name="RemoteServer",
        url="https://mcp.example.com/sse",
    )
    
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            async with server:
                agent = Agent(name="Agent", mcp_servers=[server])
                
                # Long-running conversation
                while True:
                    user_input = input("You: ")
                    if user_input == "quit":
                        break
                    
                    result = await Runner.run(agent, user_input)
                    print(f"Agent: {result.final_output}")
                    
        except ConnectionError as e:
            retry_count += 1
            print(f"Connection lost. Retrying ({retry_count}/{max_retries})...")
            await asyncio.sleep(2 ** retry_count)  # Exponential backoff
        else:
            break  # Clean exit
    
    if retry_count >= max_retries:
        print("Failed to maintain connection")


# =============================================================================
# 8. MCP WITH STREAMING
# =============================================================================

"""
┌─────────────────────────────────────────────────────────────────────────────┐
│                     MCP WITH STREAMING                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Stream agent responses while using MCP tools:                              │
│                                                                              │
│  User ──► Agent ──► MCP Tool ──► Stream results back                       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
"""


async def demo_mcp_streaming():
    """
    Streaming with MCP tools.
    """
    
    server = MCPServerStdio(
        name="Server",
        command="python",
        args=["server.py"],
    )
    
    async with server:
        agent = Agent(
            name="StreamingAgent",
            instructions="Help users with data analysis.",
            mcp_servers=[server],
        )
        
        # Stream the response
        result = Runner.run_streamed(agent, "Analyze the sales data")
        
        async for event in result.stream_events():
            if event.type == "raw_response_event":
                # Text tokens
                try:
                    if hasattr(event.data, 'delta'):
                        text = getattr(event.data.delta, 'content', '')
                        if text:
                            print(text, end="", flush=True)
                except:
                    pass
            
            elif event.type == "run_item_stream_event":
                # Tool calls (including MCP tools)
                if hasattr(event, 'item'):
                    item_type = getattr(event.item, 'type', '')
                    if item_type == 'tool_call_item':
                        tool_name = getattr(event.item, 'name', '?')
                        print(f"\n🔧 Calling MCP tool: {tool_name}")
                    elif item_type == 'tool_call_output_item':
                        output = getattr(event.item, 'output', '')
                        print(f"\n📤 MCP tool result: {output[:100]}...")


# =============================================================================
# 9. ERROR HANDLING
# =============================================================================

"""
┌─────────────────────────────────────────────────────────────────────────────┐
│                      MCP ERROR HANDLING                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Common MCP errors:                                                         │
│  - Connection errors (server not running)                                   │
│  - Timeout errors (server too slow)                                         │
│  - Tool execution errors                                                    │
│  - Authentication errors                                                    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
"""

from agents.exceptions import UserError


async def demo_error_handling():
    """
    Robust MCP error handling.
    """
    
    server = MCPServerStdio(
        name="Server",
        command="python",
        args=["server.py"],
    )
    
    try:
        async with server:
            agent = Agent(name="Agent", mcp_servers=[server])
            result = await Runner.run(agent, "Do something")
            print(result.final_output)
            
    except FileNotFoundError:
        print("❌ MCP server script not found")
        
    except ConnectionError as e:
        print(f"❌ Failed to connect to MCP server: {e}")
        
    except TimeoutError:
        print("❌ MCP server timed out")
        
    except UserError as e:
        print(f"❌ Tool execution error: {e}")
        
    except Exception as e:
        print(f"❌ Unexpected error: {type(e).__name__}: {e}")


# --- Graceful Fallback ---

async def demo_fallback():
    """
    Fallback when MCP server is unavailable.
    """
    
    from agents import function_tool
    
    # Fallback tools (local implementation)
    @function_tool
    def fallback_search(query: str) -> str:
        return f"[Fallback] Search results for: {query}"
    
    
    async def create_agent_with_fallback():
        server = MCPServerStdio(
            name="SearchServer",
            command="python",
            args=["search_server.py"],
        )
        
        try:
            await server.connect()
            # MCP server available
            return Agent(
                name="Agent",
                instructions="Use MCP tools for search.",
                mcp_servers=[server],
            ), server
            
        except Exception as e:
            print(f"⚠️ MCP unavailable, using fallback: {e}")
            # Use local fallback tools
            return Agent(
                name="Agent",
                instructions="Use fallback search.",
                tools=[fallback_search],
            ), None
    
    
    agent, server = await create_agent_with_fallback()
    
    try:
        result = await Runner.run(agent, "Search for AI news")
        print(result.final_output)
    finally:
        if server:
            await server.cleanup()


# =============================================================================
# 10. BUILDING PRODUCTION MCP SERVERS (FastMCP)
# =============================================================================

PRODUCTION_MCP_SERVER = '''
"""
Production-ready MCP Server with FastMCP
"""

from fastmcp import FastMCP
from fastmcp.resources import Resource
from pydantic import BaseModel
from typing import Optional
import asyncio
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create MCP server
mcp = FastMCP(
    name="ProductionServer",
    version="1.0.0",
)


# ═══════════════════════════════════════════════════════════════════
# CONTEXT / STATE MANAGEMENT
# ═══════════════════════════════════════════════════════════════════

class ServerContext:
    """Shared state for the MCP server."""
    
    def __init__(self):
        self.db_pool = None
        self.cache = {}
        self.request_count = 0
    
    async def initialize(self):
        """Initialize connections."""
        # Setup database pool
        # self.db_pool = await create_pool(...)
        logger.info("Server context initialized")
    
    async def cleanup(self):
        """Cleanup connections."""
        # if self.db_pool:
        #     await self.db_pool.close()
        logger.info("Server context cleaned up")


# Global context
ctx = ServerContext()


# ═══════════════════════════════════════════════════════════════════
# LIFECYCLE HOOKS
# ═══════════════════════════════════════════════════════════════════

@mcp.on_startup
async def startup():
    """Called when server starts."""
    await ctx.initialize()
    logger.info("MCP Server started")


@mcp.on_shutdown
async def shutdown():
    """Called when server stops."""
    await ctx.cleanup()
    logger.info("MCP Server stopped")


# ═══════════════════════════════════════════════════════════════════
# INPUT VALIDATION WITH PYDANTIC
# ═══════════════════════════════════════════════════════════════════

class QueryInput(BaseModel):
    """Input for database queries."""
    table: str
    filters: Optional[dict] = None
    limit: int = 100


class FileInput(BaseModel):
    """Input for file operations."""
    path: str
    encoding: str = "utf-8"


# ═══════════════════════════════════════════════════════════════════
# TOOLS WITH ERROR HANDLING
# ═══════════════════════════════════════════════════════════════════

@mcp.tool()
async def query_database(input: QueryInput) -> str:
    """
    Query the database safely.
    
    Args:
        input: Query parameters (table, filters, limit)
    
    Returns:
        Query results as JSON string
    """
    ctx.request_count += 1
    logger.info(f"Query #{ctx.request_count}: {input.table}")
    
    try:
        # Validate table name (prevent SQL injection)
        allowed_tables = ["users", "orders", "products"]
        if input.table not in allowed_tables:
            return f"Error: Invalid table '{input.table}'"
        
        # Execute query (example)
        results = [
            {"id": 1, "name": "Item 1"},
            {"id": 2, "name": "Item 2"},
        ]
        
        import json
        return json.dumps(results[:input.limit])
        
    except Exception as e:
        logger.error(f"Query error: {e}")
        return f"Error: {str(e)}"


@mcp.tool()
async def read_file_safe(input: FileInput) -> str:
    """
    Read a file with safety checks.
    """
    import os
    
    # Security: Prevent path traversal
    safe_base = "/app/data"
    full_path = os.path.normpath(os.path.join(safe_base, input.path))
    
    if not full_path.startswith(safe_base):
        return "Error: Access denied - path traversal detected"
    
    try:
        with open(full_path, "r", encoding=input.encoding) as f:
            return f.read()
    except FileNotFoundError:
        return f"Error: File not found: {input.path}"
    except Exception as e:
        return f"Error: {str(e)}"


# ═══════════════════════════════════════════════════════════════════
# ASYNC TOOLS WITH TIMEOUT
# ═══════════════════════════════════════════════════════════════════

@mcp.tool()
async def fetch_external_data(url: str, timeout_seconds: int = 10) -> str:
    """
    Fetch data from external URL with timeout.
    """
    import aiohttp
    
    try:
        async with asyncio.timeout(timeout_seconds):
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.text()
                    return f"Error: HTTP {response.status}"
                    
    except asyncio.TimeoutError:
        return f"Error: Request timed out after {timeout_seconds}s"
    except Exception as e:
        return f"Error: {str(e)}"


# ═══════════════════════════════════════════════════════════════════
# RESOURCES
# ═══════════════════════════════════════════════════════════════════

@mcp.resource("config://app")
def get_app_config() -> str:
    """Application configuration."""
    import json
    return json.dumps({
        "name": "ProductionApp",
        "version": "1.0.0",
        "environment": "production",
    })


@mcp.resource("stats://server")
def get_server_stats() -> str:
    """Server statistics."""
    import json
    return json.dumps({
        "request_count": ctx.request_count,
        "uptime": "running",
    })


# ═══════════════════════════════════════════════════════════════════
# PROMPTS
# ═══════════════════════════════════════════════════════════════════

@mcp.prompt()
def data_analysis_prompt(table_name: str, question: str) -> str:
    """Generate a data analysis prompt."""
    return f"""Analyze the '{table_name}' table to answer:
{question}

Use the query_database tool to fetch data, then provide insights."""


# ═══════════════════════════════════════════════════════════════════
# RUN SERVER
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Run with stdio (for subprocess)
    mcp.run()
    
    # Or run with SSE (for HTTP)
    # mcp.run(transport="sse", port=8080)
'''


# =============================================================================
# MAIN
# =============================================================================

async def main():
    print("=" * 60)
    print("ADVANCED MCP GUIDE")
    print("=" * 60)
    print("\nThis file contains examples for:")
    print("1. MCP Server Types")
    print("2. Multiple MCP Servers")
    print("3. MCP Resources")
    print("4. MCP Prompts")
    print("5. Hosted MCP Tools")
    print("6. MCP Configuration")
    print("7. Lifecycle Management")
    print("8. MCP with Streaming")
    print("9. Error Handling")
    print("10. Production MCP Servers")
    print("\nSee the code comments for detailed explanations!")


if __name__ == "__main__":
    asyncio.run(main())
