# MCP Advanced Cheatsheet

## Server Types

| Type | Use Case | Example |
|------|----------|---------|
| `MCPServerStdio` | Local subprocess | File system, local DB |
| `MCPServerSse` | Remote HTTP + SSE | Cloud APIs, remote services |
| `MCPServerStreamableHttp` | HTTP with streaming | Large data, live feeds |

```python
# Stdio (local)
server = MCPServerStdio(
    name="LocalServer",
    command="python",
    args=["server.py"],
    env={"API_KEY": "secret"},
)

# SSE (remote)
server = MCPServerSse(
    name="RemoteServer",
    url="https://mcp.example.com/sse",
    headers={"Authorization": "Bearer token"},
)

# HTTP Streaming
server = MCPServerStreamableHttp(
    name="StreamServer",
    url="https://mcp.example.com/stream",
)
```

---

## Lifecycle Management

```python
# ✅ Recommended: Context manager
async with server:
    agent = Agent(mcp_servers=[server])
    await Runner.run(agent, "query")

# Manual management
await server.connect()
try:
    agent = Agent(mcp_servers=[server])
    await Runner.run(agent, "query")
finally:
    await server.cleanup()

# Multiple servers
async with server1, server2, server3:
    agent = Agent(mcp_servers=[server1, server2, server3])
```

---

## Multiple MCP Servers

```python
file_server = MCPServerStdio(name="Files", command="python", args=["file_mcp.py"])
db_server = MCPServerStdio(name="Database", command="python", args=["db_mcp.py"])
api_server = MCPServerSse(name="API", url="https://api.example.com/mcp")

async with file_server, db_server, api_server:
    agent = Agent(
        name="MultiAgent",
        mcp_servers=[file_server, db_server, api_server],  # All three!
    )
```

---

## MCP Primitives

| Primitive | Purpose | FastMCP Decorator |
|-----------|---------|-------------------|
| **Tools** | Functions agent can call | `@mcp.tool()` |
| **Resources** | Data agent can read | `@mcp.resource("uri")` |
| **Prompts** | Reusable templates | `@mcp.prompt()` |

```python
# In FastMCP server:

@mcp.tool()
def search(query: str) -> str:
    return f"Results for {query}"

@mcp.resource("file://config.json")
def get_config() -> str:
    return '{"key": "value"}'

@mcp.prompt()
def review_prompt(code: str) -> str:
    return f"Review this code: {code}"
```

---

## Reading Resources & Prompts

```python
async with server:
    # List resources
    resources = await server.list_resources()
    
    # Read a resource
    content = await server.read_resource("file://config.json")
    
    # List prompts
    prompts = await server.list_prompts()
    
    # Get a prompt
    prompt = await server.get_prompt("review_prompt", {"code": "..."})
```

---

## MCP Configuration

```python
agent = Agent(
    name="Agent",
    mcp_servers=[server],
    mcp_config={
        # Only allow specific tools
        "allowed_tools": ["read_file", "list_files"],
        
        # Or exclude specific tools
        # "excluded_tools": ["delete_file"],
    },
)
```

---

## Authentication Patterns

```python
# API Key
server = MCPServerSse(
    url="https://mcp.example.com",
    headers={"X-API-Key": "your-key"},
)

# Bearer Token
server = MCPServerSse(
    url="https://mcp.example.com",
    headers={"Authorization": "Bearer your-token"},
)

# Environment Variables (for Stdio)
server = MCPServerStdio(
    command="python",
    args=["server.py"],
    env={
        "DATABASE_URL": "postgresql://...",
        "API_KEY": "secret",
    },
)
```

---

## Hosted MCP (OpenAI Managed)

```python
from agents.tool import HostedMCPTool

hosted = HostedMCPTool(
    tool_config={
        "type": "mcp",
        "server_label": "deepwiki",
        "server_url": "https://mcp.deepwiki.com/mcp",
        "require_approval": "never",
    }
)

agent = Agent(tools=[hosted])
```

---

## Streaming with MCP

```python
async with server:
    agent = Agent(mcp_servers=[server])
    
    result = Runner.run_streamed(agent, "Analyze data")
    
    async for event in result.stream_events():
        if event.type == "raw_response_event":
            # Text tokens
            text = getattr(event.data.delta, 'content', '')
            print(text, end="")
        
        elif event.type == "run_item_stream_event":
            # MCP tool calls
            if event.item.type == 'tool_call_item':
                print(f"\n🔧 MCP Tool: {event.item.name}")
```

---

## Error Handling

```python
try:
    async with server:
        result = await Runner.run(agent, "query")
        
except FileNotFoundError:
    print("MCP server script not found")
    
except ConnectionError:
    print("Failed to connect to MCP server")
    
except TimeoutError:
    print("MCP server timed out")
    
except UserError as e:
    print(f"Tool execution error: {e}")
```

---

## Production FastMCP Server

```python
from fastmcp import FastMCP
from pydantic import BaseModel

mcp = FastMCP("ProductionServer")

# Lifecycle
@mcp.on_startup
async def startup():
    # Initialize DB, cache, etc.
    pass

@mcp.on_shutdown
async def shutdown():
    # Cleanup
    pass

# Input validation
class QueryInput(BaseModel):
    table: str
    limit: int = 100

@mcp.tool()
async def query(input: QueryInput) -> str:
    # Validate, execute, return
    return "results"

# Run
if __name__ == "__main__":
    mcp.run()  # stdio
    # mcp.run(transport="sse", port=8080)  # HTTP
```

---

## Common Patterns

### Fallback when MCP unavailable

```python
try:
    await server.connect()
    agent = Agent(mcp_servers=[server])
except:
    agent = Agent(tools=[local_fallback_tool])
```

### Reconnection with backoff

```python
for attempt in range(3):
    try:
        async with server:
            await run_agent()
            break
    except ConnectionError:
        await asyncio.sleep(2 ** attempt)
```

### MCP + Regular Tools

```python
@function_tool
def local_tool(x: str) -> str:
    return f"Local: {x}"

agent = Agent(
    tools=[local_tool],        # Regular tools
    mcp_servers=[mcp_server],  # MCP tools
)
```

---

## Quick Reference

| Task | Code |
|------|------|
| Create stdio server | `MCPServerStdio(name, command, args)` |
| Create SSE server | `MCPServerSse(name, url, headers)` |
| Connect server | `async with server:` or `await server.connect()` |
| Use with agent | `Agent(mcp_servers=[server])` |
| List tools | `await server.list_tools()` |
| List resources | `await server.list_resources()` |
| Read resource | `await server.read_resource(uri)` |
| Get prompt | `await server.get_prompt(name, args)` |
| Filter tools | `mcp_config={"allowed_tools": [...]}` |
