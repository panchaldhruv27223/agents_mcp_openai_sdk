"""
=============================================================================
PRACTICAL MCP EXAMPLE - Multi-Server Production Setup
=============================================================================

This example shows a realistic setup with:
- File System MCP Server (local)
- Database MCP Server (local)  
- External API MCP Server (remote)
- Proper lifecycle management
- Error handling
- Streaming
"""

import asyncio
from agents import Agent, Runner, function_tool, RunContextWrapper
from agents.mcp import MCPServerStdio, MCPServerSse
from dataclasses import dataclass, field
from typing import Any, Optional
from dotenv import load_dotenv

load_dotenv()


# =============================================================================
# CONTEXT
# =============================================================================

@dataclass
class AppContext:
    """Application context passed through agent runs."""
    user_id: str
    session_id: str
    mcp_servers_status: dict = field(default_factory=dict)


# =============================================================================
# MCP SERVER MANAGER
# =============================================================================

class MCPServerManager:
    """
    Manages multiple MCP servers with proper lifecycle and fallbacks.
    """
    
    def __init__(self):
        self.servers: dict[str, Any] = {}
        self.connected: set[str] = set()
    
    def add_stdio_server(
        self,
        name: str,
        command: str,
        args: list[str],
        env: dict = None,
    ):
        """Add a stdio-based MCP server."""
        self.servers[name] = {
            "type": "stdio",
            "server": MCPServerStdio(
                name=name,
                command=command,
                args=args,
                env=env or {},
            ),
        }
    
    def add_sse_server(
        self,
        name: str,
        url: str,
        headers: dict = None,
    ):
        """Add an SSE-based MCP server."""
        self.servers[name] = {
            "type": "sse",
            "server": MCPServerSse(
                name=name,
                url=url,
                headers=headers or {},
            ),
        }
    
    async def connect_all(self) -> list:
        """Connect all servers, return list of connected servers."""
        connected_servers = []
        
        for name, config in self.servers.items():
            server = config["server"]
            try:
                await server.connect()
                self.connected.add(name)
                connected_servers.append(server)
                print(f"✅ Connected: {name}")
            except Exception as e:
                print(f"⚠️ Failed to connect {name}: {e}")
        
        return connected_servers
    
    async def cleanup_all(self):
        """Cleanup all connected servers."""
        for name in list(self.connected):
            try:
                await self.servers[name]["server"].cleanup()
                self.connected.remove(name)
                print(f"🔌 Disconnected: {name}")
            except Exception as e:
                print(f"⚠️ Error cleaning up {name}: {e}")
    
    def get_connected_servers(self) -> list:
        """Get list of connected server objects."""
        return [
            self.servers[name]["server"]
            for name in self.connected
        ]
    
    async def __aenter__(self):
        await self.connect_all()
        return self
    
    async def __aexit__(self, *args):
        await self.cleanup_all()


# =============================================================================
# FALLBACK TOOLS (When MCP is unavailable)
# =============================================================================

@function_tool
def fallback_read_file(filename: str) -> str:
    """Fallback file reading (limited functionality)."""
    return f"[Fallback] Unable to read {filename} - MCP server unavailable"


@function_tool
def fallback_query(query: str) -> str:
    """Fallback database query (limited functionality)."""
    return f"[Fallback] Cannot execute query - MCP server unavailable"


# =============================================================================
# AGENT FACTORY
# =============================================================================

def create_data_agent(mcp_servers: list, use_fallbacks: bool = False) -> Agent:
    """
    Create an agent with MCP servers or fallback tools.
    """
    
    if mcp_servers:
        return Agent(
            name="DataAnalyst",
            instructions="""You are a data analyst with access to:
- File system operations (read, write, list files)
- Database operations (query, insert, update)
- External API access (fetch data, webhooks)

Help users analyze data, generate reports, and automate tasks.
Always explain what you're doing before using tools.""",
            mcp_servers=mcp_servers,
            mcp_config={
                # Optional: Filter dangerous tools
                # "excluded_tools": ["delete_file", "drop_table"],
            },
        )
    elif use_fallbacks:
        return Agent(
            name="DataAnalyst",
            instructions="""You are a data analyst, but MCP servers are unavailable.
Use fallback tools and let the user know about limited functionality.""",
            tools=[fallback_read_file, fallback_query],
        )
    else:
        return Agent(
            name="DataAnalyst",
            instructions="You are a data analyst but tools are currently unavailable.",
        )


# =============================================================================
# STREAMING HANDLER
# =============================================================================

async def stream_agent_response(agent: Agent, message: str):
    """
    Stream agent response with MCP tool visibility.
    """
    result = Runner.run_streamed(agent, message)
    
    current_tool = None
    
    async for event in result.stream_events():
        
        # Track agent changes
        if event.type == "agent_updated_stream_event":
            print(f"\n🤖 Agent: {event.agent.name}")
        
        # Track tool calls (including MCP tools)
        elif event.type == "run_item_stream_event":
            if hasattr(event, 'item'):
                item_type = getattr(event.item, 'type', '')
                
                if item_type == 'tool_call_item':
                    tool_name = getattr(event.item, 'name', 'unknown')
                    current_tool = tool_name
                    print(f"\n🔧 Calling: {tool_name}")
                
                elif item_type == 'tool_call_output_item':
                    output = getattr(event.item, 'output', '')
                    # Truncate long outputs
                    display = output[:200] + "..." if len(output) > 200 else output
                    print(f"📤 Result: {display}")
                    current_tool = None
        
        # Stream text tokens
        elif event.type == "raw_response_event":
            try:
                if hasattr(event.data, 'delta'):
                    text = getattr(event.data.delta, 'content', '')
                    if text:
                        print(text, end="", flush=True)
            except:
                pass
    
    print("\n")
    return await result.final_output


# =============================================================================
# EXAMPLE MCP SERVERS (FastMCP)
# =============================================================================

FILE_SERVER_CODE = '''
"""file_server.py - MCP server for file operations"""
from fastmcp import FastMCP
import os

mcp = FastMCP("FileServer")

@mcp.tool()
def read_file(path: str) -> str:
    """Read contents of a file."""
    try:
        with open(path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        return f"Error: File not found: {path}"
    except Exception as e:
        return f"Error: {e}"

@mcp.tool()
def write_file(path: str, content: str) -> str:
    """Write content to a file."""
    try:
        with open(path, 'w') as f:
            f.write(content)
        return f"Successfully wrote to {path}"
    except Exception as e:
        return f"Error: {e}"

@mcp.tool()
def list_files(directory: str = ".") -> str:
    """List files in a directory."""
    try:
        files = os.listdir(directory)
        return "\\n".join(files)
    except Exception as e:
        return f"Error: {e}"

@mcp.resource("file://{path}")
def get_file_resource(path: str) -> str:
    """Get file as resource."""
    try:
        with open(path, 'r') as f:
            return f.read()
    except:
        return ""

if __name__ == "__main__":
    mcp.run()
'''


DB_SERVER_CODE = '''
"""db_server.py - MCP server for database operations"""
from fastmcp import FastMCP
import json

mcp = FastMCP("DatabaseServer")

# Simulated database
DATABASE = {
    "users": [
        {"id": 1, "name": "Alice", "email": "alice@example.com"},
        {"id": 2, "name": "Bob", "email": "bob@example.com"},
    ],
    "orders": [
        {"id": 1, "user_id": 1, "total": 99.99, "status": "completed"},
        {"id": 2, "user_id": 2, "total": 149.99, "status": "pending"},
    ],
}

@mcp.tool()
def query_table(table: str, limit: int = 10) -> str:
    """Query a database table."""
    if table not in DATABASE:
        return f"Error: Table '{table}' not found. Available: {list(DATABASE.keys())}"
    
    results = DATABASE[table][:limit]
    return json.dumps(results, indent=2)

@mcp.tool()
def count_records(table: str) -> str:
    """Count records in a table."""
    if table not in DATABASE:
        return f"Error: Table '{table}' not found"
    return f"Table '{table}' has {len(DATABASE[table])} records"

@mcp.tool()
def get_schema() -> str:
    """Get database schema."""
    schema = {}
    for table, records in DATABASE.items():
        if records:
            schema[table] = list(records[0].keys())
    return json.dumps(schema, indent=2)

@mcp.resource("db://schema")
def schema_resource() -> str:
    """Database schema as resource."""
    return get_schema()

@mcp.prompt()
def sql_analysis_prompt(question: str) -> str:
    """Generate SQL analysis prompt."""
    schema = get_schema()
    return f"""Given this database schema:
{schema}

Answer this question using the query tools: {question}
"""

if __name__ == "__main__":
    mcp.run()
'''


# =============================================================================
# MAIN DEMO
# =============================================================================

async def main():
    print("=" * 60)
    print("MULTI-SERVER MCP DEMO")
    print("=" * 60)
    
    # Setup server manager
    manager = MCPServerManager()
    
    # Add servers (these would be real paths in production)
    manager.add_stdio_server(
        name="FileServer",
        command="python",
        args=["mcp_servers/file_server.py"],
    )
    
    manager.add_stdio_server(
        name="DatabaseServer",
        command="python",
        args=["mcp_servers/db_server.py"],
    )
    
    # Optional: Remote server
    # manager.add_sse_server(
    #     name="ExternalAPI",
    #     url="https://api.example.com/mcp",
    #     headers={"Authorization": "Bearer token"},
    # )
    
    try:
        async with manager:
            # Get connected servers
            servers = manager.get_connected_servers()
            
            if not servers:
                print("\n⚠️ No MCP servers available, using fallbacks")
                agent = create_data_agent([], use_fallbacks=True)
            else:
                print(f"\n✅ Connected to {len(servers)} MCP server(s)")
                agent = create_data_agent(servers)
            
            # Interactive loop
            print("\n" + "-" * 40)
            print("Chat with the agent (type 'quit' to exit)")
            print("-" * 40)
            
            while True:
                try:
                    user_input = input("\n📝 You: ").strip()
                    
                    if user_input.lower() in ['quit', 'exit', 'q']:
                        break
                    
                    if not user_input:
                        continue
                    
                    print("\n🤖 Agent:")
                    await stream_agent_response(agent, user_input)
                    
                except KeyboardInterrupt:
                    break
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
    
    print("\n👋 Goodbye!")


# =============================================================================
# ALTERNATIVE: Simple single-server usage
# =============================================================================

async def simple_mcp_example():
    """
    Simpler example with single MCP server.
    """
    
    server = MCPServerStdio(
        name="MyServer",
        command="python",
        args=["server.py"],
    )
    
    async with server:
        agent = Agent(
            name="Assistant",
            instructions="Help users with tasks.",
            mcp_servers=[server],
        )
        
        # Single query
        result = await Runner.run(agent, "List all files")
        print(result.final_output)
        
        # Or streaming
        result = Runner.run_streamed(agent, "Analyze the data")
        async for event in result.stream_events():
            if event.type == "raw_response_event":
                if hasattr(event.data, 'delta'):
                    text = getattr(event.data.delta, 'content', '')
                    print(text, end="", flush=True)


# =============================================================================
# SAVE EXAMPLE SERVER FILES
# =============================================================================

def save_example_servers():
    """Save example MCP server files."""
    import os
    
    os.makedirs("mcp_servers", exist_ok=True)
    
    with open("mcp_servers/file_server.py", "w") as f:
        f.write(FILE_SERVER_CODE)
    
    with open("mcp_servers/db_server.py", "w") as f:
        f.write(DB_SERVER_CODE)
    
    print("✅ Example server files saved to mcp_servers/")


if __name__ == "__main__":
    # Uncomment to save example server files:
    # save_example_servers()
    
    asyncio.run(main())
