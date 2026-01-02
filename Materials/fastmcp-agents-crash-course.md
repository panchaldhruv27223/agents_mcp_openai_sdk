# 🚀 FAST-TRACK: FastMCP + OpenAI Agents SDK

> **Goal:** Learn FastMCP → Build MCP Server → Create Agent → Integrate Everything
> **Time:** ~2 hours hands-on

---

## 📦 PHASE 1: Setup (5 min)

```bash
# Create project directory
mkdir mcp-agent-project && cd mcp-agent-project

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# OR: venv\Scripts\activate  # Windows

# Install both packages
pip install fastmcp openai-agents

# Set your OpenAI API key
export OPENAI_API_KEY="sk-your-key-here"
```

---

## 🔧 PHASE 2: FastMCP Core Concepts (15 min)

### The 3 Building Blocks

| Component | Purpose | Analogy |
|-----------|---------|---------|
| **Tools** | Execute actions, perform computations | POST endpoints |
| **Resources** | Expose read-only data | GET endpoints |
| **Prompts** | Reusable instruction templates | Pre-built queries |

### Minimal Server Structure

```python
from fastmcp import FastMCP

# 1. Create server instance
mcp = FastMCP("MyServer")

# 2. Add tools (@mcp.tool)
# 3. Add resources (@mcp.resource)  
# 4. Add prompts (@mcp.prompt)

# 5. Run it
if __name__ == "__main__":
    mcp.run()
```

---

## 🛠️ PHASE 3: Build Your First MCP Server (20 min)

Create `my_server.py`:

```python
from fastmcp import FastMCP
from typing import Annotated
from pydantic import Field
import json

# Initialize the MCP server
mcp = FastMCP("TaskManager")

# ============================================
# 📊 IN-MEMORY DATABASE (for demo purposes)
# ============================================
tasks_db = {
    "1": {"id": "1", "title": "Learn FastMCP", "status": "in_progress", "priority": "high"},
    "2": {"id": "2", "title": "Build Agent", "status": "pending", "priority": "medium"},
}

# ============================================
# 🔧 TOOLS - Actions the AI can perform
# ============================================

@mcp.tool
def get_all_tasks() -> str:
    """Get all tasks from the database"""
    return json.dumps(list(tasks_db.values()), indent=2)


@mcp.tool
def get_task(
    task_id: Annotated[str, Field(description="The unique ID of the task")]
) -> str:
    """Get a specific task by ID"""
    if task_id in tasks_db:
        return json.dumps(tasks_db[task_id], indent=2)
    return json.dumps({"error": f"Task {task_id} not found"})


@mcp.tool
def create_task(
    title: Annotated[str, Field(description="Title of the new task")],
    priority: Annotated[str, Field(description="Priority: low, medium, or high")] = "medium"
) -> str:
    """Create a new task"""
    new_id = str(len(tasks_db) + 1)
    new_task = {
        "id": new_id,
        "title": title,
        "status": "pending",
        "priority": priority
    }
    tasks_db[new_id] = new_task
    return json.dumps({"success": True, "task": new_task})


@mcp.tool
def update_task_status(
    task_id: Annotated[str, Field(description="The task ID to update")],
    status: Annotated[str, Field(description="New status: pending, in_progress, or completed")]
) -> str:
    """Update the status of a task"""
    if task_id in tasks_db:
        tasks_db[task_id]["status"] = status
        return json.dumps({"success": True, "task": tasks_db[task_id]})
    return json.dumps({"error": f"Task {task_id} not found"})


@mcp.tool
def delete_task(
    task_id: Annotated[str, Field(description="The task ID to delete")]
) -> str:
    """Delete a task by ID"""
    if task_id in tasks_db:
        deleted = tasks_db.pop(task_id)
        return json.dumps({"success": True, "deleted": deleted})
    return json.dumps({"error": f"Task {task_id} not found"})


# ============================================
# 📚 RESOURCES - Read-only data access
# ============================================

@mcp.resource("tasks://summary")
def get_tasks_summary() -> str:
    """Get a summary of all tasks"""
    total = len(tasks_db)
    by_status = {}
    by_priority = {}
    
    for task in tasks_db.values():
        status = task["status"]
        priority = task["priority"]
        by_status[status] = by_status.get(status, 0) + 1
        by_priority[priority] = by_priority.get(priority, 0) + 1
    
    return json.dumps({
        "total_tasks": total,
        "by_status": by_status,
        "by_priority": by_priority
    }, indent=2)


@mcp.resource("tasks://{task_id}")
def get_task_resource(task_id: str) -> str:
    """Get task details as a resource"""
    if task_id in tasks_db:
        return json.dumps(tasks_db[task_id], indent=2)
    return json.dumps({"error": f"Task {task_id} not found"})


# ============================================
# 💬 PROMPTS - Reusable instruction templates
# ============================================

@mcp.prompt
def task_analysis_prompt() -> str:
    """Generate a prompt for analyzing tasks"""
    return """You are a task management assistant. Analyze the current tasks and provide:
1. A summary of pending vs completed work
2. Recommendations for prioritization
3. Any tasks that might be blocked or need attention

Use the available tools to fetch task data before providing your analysis."""


@mcp.prompt
def daily_standup_prompt(focus_area: str = "all") -> str:
    """Generate a daily standup prompt"""
    return f"""Generate a daily standup report focusing on: {focus_area}
    
Include:
- What was completed yesterday
- What's planned for today  
- Any blockers or concerns

Use the task management tools to gather accurate information."""


# ============================================
# 🚀 RUN THE SERVER
# ============================================

if __name__ == "__main__":
    # For local testing with stdio transport
    # mcp.run()
    
    # For HTTP transport (needed for agent integration)
    mcp.run(transport="sse", port=8000)
```

### Run & Test Your Server

```bash
# Option 1: Run with HTTP/SSE transport
python my_server.py
# Server runs at http://localhost:8000/sse

# Option 2: Test with MCP Inspector (in another terminal)
fastmcp dev my_server.py
```

---

## 🤖 PHASE 4: OpenAI Agents SDK Basics (15 min)

### Core Concepts

| Concept | Description |
|---------|-------------|
| **Agent** | LLM with instructions + tools |
| **Runner** | Executes the agent |
| **Handoffs** | Delegate between agents |
| **Guardrails** | Input/output validation |
| **Sessions** | Conversation history |

### Basic Agent (No MCP)

Create `basic_agent.py`:

```python
from agents import Agent, Runner

# Define a simple agent
agent = Agent(
    name="Assistant",
    instructions="You are a helpful assistant that answers questions clearly and concisely."
)

# Run synchronously
result = Runner.run_sync(agent, "What is the capital of France?")
print(result.final_output)
```

### Agent with Custom Tools

Create `agent_with_tools.py`:

```python
from agents import Agent, Runner, function_tool

# Define a custom tool
@function_tool
def calculate(expression: str) -> str:
    """Calculate a mathematical expression. Example: '2 + 2' or '10 * 5'"""
    try:
        result = eval(expression)  # Note: Use safer eval in production
        return f"Result: {result}"
    except Exception as e:
        return f"Error: {str(e)}"

@function_tool
def get_current_time() -> str:
    """Get the current date and time"""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Create agent with tools
agent = Agent(
    name="Calculator",
    instructions="You are a helpful assistant that can perform calculations and tell the time.",
    tools=[calculate, get_current_time]
)

# Run it
result = Runner.run_sync(agent, "What is 25 * 4? Also, what time is it?")
print(result.final_output)
```

---

## 🔗 PHASE 5: Connect FastMCP Server to Agent (20 min)

### Method 1: SSE Transport (Remote/HTTP Server)

Create `agent_with_mcp_sse.py`:

```python
import asyncio
from agents import Agent, Runner
from agents.mcp import MCPServerSse

async def main():
    # Connect to your FastMCP server running on localhost:8000
    async with MCPServerSse(
        name="TaskManager",
        params={
            "url": "http://localhost:8000/sse",
        },
        cache_tools_list=True  # Cache for better performance
    ) as mcp_server:
        
        # Create agent with MCP server
        agent = Agent(
            name="TaskAssistant",
            instructions="""You are a task management assistant. 
            Use the available tools to help users manage their tasks.
            Always confirm actions and provide clear summaries.""",
            mcp_servers=[mcp_server]
        )
        
        # Test the agent
        result = await Runner.run(agent, "Show me all my tasks")
        print("Agent Response:")
        print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())
```

### Method 2: Stdio Transport (Local Subprocess)

Create `agent_with_mcp_stdio.py`:

```python
import asyncio
from agents import Agent, Runner
from agents.mcp import MCPServerStdio

async def main():
    # Launch MCP server as subprocess
    async with MCPServerStdio(
        name="TaskManager",
        params={
            "command": "python",
            "args": ["my_server.py"],  # Your FastMCP server file
        }
    ) as mcp_server:
        
        agent = Agent(
            name="TaskAssistant",
            instructions="""You are a task management assistant.
            Help users create, update, and manage their tasks.""",
            mcp_servers=[mcp_server]
        )
        
        # Interactive conversation
        queries = [
            "What tasks do I have?",
            "Create a new task called 'Review PR' with high priority",
            "Mark task 1 as completed",
            "Give me a summary of all tasks"
        ]
        
        for query in queries:
            print(f"\n👤 User: {query}")
            result = await Runner.run(agent, query)
            print(f"🤖 Agent: {result.final_output}")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 🎯 PHASE 6: Complete Project Example (30 min)

### Full-Featured MCP Server + Multi-Agent System

Create `complete_project.py`:

```python
"""
Complete FastMCP + OpenAI Agents Integration
A task management system with specialized agents
"""

import asyncio
import json
from datetime import datetime
from typing import Annotated
from pydantic import Field

from fastmcp import FastMCP
from agents import Agent, Runner
from agents.mcp import MCPServerSse

# ============================================
# PART 1: ENHANCED MCP SERVER
# ============================================

mcp = FastMCP("ProductivityHub")

# Database
tasks_db = {}
notes_db = {}
task_counter = 0
note_counter = 0

# --- TASK TOOLS ---

@mcp.tool
def create_task(
    title: Annotated[str, Field(description="Task title")],
    description: Annotated[str, Field(description="Task description")] = "",
    priority: Annotated[str, Field(description="Priority: low, medium, high")] = "medium",
    due_date: Annotated[str, Field(description="Due date in YYYY-MM-DD format")] = ""
) -> str:
    """Create a new task with optional description and due date"""
    global task_counter
    task_counter += 1
    task_id = f"task_{task_counter}"
    
    tasks_db[task_id] = {
        "id": task_id,
        "title": title,
        "description": description,
        "priority": priority,
        "status": "pending",
        "due_date": due_date,
        "created_at": datetime.now().isoformat()
    }
    return json.dumps({"success": True, "task": tasks_db[task_id]})

@mcp.tool
def list_tasks(
    status_filter: Annotated[str, Field(description="Filter by status: all, pending, in_progress, completed")] = "all"
) -> str:
    """List all tasks, optionally filtered by status"""
    if status_filter == "all":
        return json.dumps(list(tasks_db.values()), indent=2)
    filtered = [t for t in tasks_db.values() if t["status"] == status_filter]
    return json.dumps(filtered, indent=2)

@mcp.tool
def update_task(
    task_id: Annotated[str, Field(description="Task ID to update")],
    status: Annotated[str, Field(description="New status")] = None,
    priority: Annotated[str, Field(description="New priority")] = None
) -> str:
    """Update task status or priority"""
    if task_id not in tasks_db:
        return json.dumps({"error": "Task not found"})
    
    if status:
        tasks_db[task_id]["status"] = status
    if priority:
        tasks_db[task_id]["priority"] = priority
    
    return json.dumps({"success": True, "task": tasks_db[task_id]})

# --- NOTE TOOLS ---

@mcp.tool
def create_note(
    title: Annotated[str, Field(description="Note title")],
    content: Annotated[str, Field(description="Note content")]
) -> str:
    """Create a new note"""
    global note_counter
    note_counter += 1
    note_id = f"note_{note_counter}"
    
    notes_db[note_id] = {
        "id": note_id,
        "title": title,
        "content": content,
        "created_at": datetime.now().isoformat()
    }
    return json.dumps({"success": True, "note": notes_db[note_id]})

@mcp.tool
def list_notes() -> str:
    """List all notes"""
    return json.dumps(list(notes_db.values()), indent=2)

@mcp.tool
def search_notes(
    query: Annotated[str, Field(description="Search query")]
) -> str:
    """Search notes by title or content"""
    results = []
    query_lower = query.lower()
    for note in notes_db.values():
        if query_lower in note["title"].lower() or query_lower in note["content"].lower():
            results.append(note)
    return json.dumps(results, indent=2)

# --- RESOURCES ---

@mcp.resource("productivity://dashboard")
def get_dashboard() -> str:
    """Get productivity dashboard summary"""
    total_tasks = len(tasks_db)
    completed = sum(1 for t in tasks_db.values() if t["status"] == "completed")
    pending = sum(1 for t in tasks_db.values() if t["status"] == "pending")
    high_priority = sum(1 for t in tasks_db.values() if t["priority"] == "high")
    
    return json.dumps({
        "tasks": {
            "total": total_tasks,
            "completed": completed,
            "pending": pending,
            "high_priority": high_priority,
            "completion_rate": f"{(completed/total_tasks*100):.1f}%" if total_tasks > 0 else "N/A"
        },
        "notes": {
            "total": len(notes_db)
        },
        "generated_at": datetime.now().isoformat()
    }, indent=2)

# --- PROMPTS ---

@mcp.prompt
def weekly_review_prompt() -> str:
    """Generate weekly review prompt"""
    return """Analyze the current tasks and notes to provide a weekly review:
    1. Summary of completed tasks
    2. Outstanding high-priority items
    3. Recommendations for the upcoming week
    Use the available tools to gather data."""

# ============================================
# PART 2: MULTI-AGENT SYSTEM
# ============================================

async def run_agent_system():
    """Run the multi-agent productivity system"""
    
    async with MCPServerSse(
        name="ProductivityHub",
        params={"url": "http://localhost:8000/sse"},
        cache_tools_list=True
    ) as mcp_server:
        
        # Agent 1: Task Manager
        task_agent = Agent(
            name="TaskManager",
            instructions="""You are a task management specialist.
            Help users create, organize, and track their tasks.
            Always provide clear confirmations and summaries.
            Prioritize tasks based on urgency and importance.""",
            mcp_servers=[mcp_server]
        )
        
        # Agent 2: Note Taker
        note_agent = Agent(
            name="NoteTaker", 
            instructions="""You are a note-taking assistant.
            Help users capture and organize their thoughts.
            Create well-structured notes with clear titles.
            Help search and retrieve relevant notes.""",
            mcp_servers=[mcp_server]
        )
        
        # Agent 3: Productivity Coach
        coach_agent = Agent(
            name="ProductivityCoach",
            instructions="""You are a productivity coach.
            Analyze user's tasks and notes to provide insights.
            Give actionable recommendations for improvement.
            Help users stay focused and organized.""",
            mcp_servers=[mcp_server]
        )
        
        # Interactive demo
        print("🚀 Productivity Hub - Multi-Agent System")
        print("=" * 50)
        
        # Demo workflow
        demo_queries = [
            (task_agent, "Create a task: 'Complete FastMCP tutorial' with high priority"),
            (task_agent, "Create a task: 'Review documentation' with medium priority"),
            (note_agent, "Create a note titled 'MCP Learning' with content: 'FastMCP is great for building AI tool servers'"),
            (task_agent, "Show me all pending tasks"),
            (coach_agent, "Give me a productivity summary and recommendations"),
        ]
        
        for agent, query in demo_queries:
            print(f"\n📤 [{agent.name}] Query: {query}")
            result = await Runner.run(agent, query)
            print(f"📥 Response: {result.final_output}")
            print("-" * 40)

# ============================================
# PART 3: RUN EVERYTHING
# ============================================

def run_server():
    """Run just the MCP server"""
    print("🔧 Starting MCP Server on http://localhost:8000/sse")
    mcp.run(transport="sse", port=8000)

async def run_demo():
    """Run the demo (assumes server is already running)"""
    await run_agent_system()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "server":
        run_server()
    elif len(sys.argv) > 1 and sys.argv[1] == "demo":
        asyncio.run(run_demo())
    else:
        print("Usage:")
        print("  python complete_project.py server  # Run MCP server")
        print("  python complete_project.py demo    # Run agent demo (server must be running)")
```

### How to Run

```bash
# Terminal 1: Start the MCP server
python complete_project.py server

# Terminal 2: Run the agent demo
python complete_project.py demo
```

---

## 📋 QUICK REFERENCE CHEATSHEET

### FastMCP Decorators

```python
@mcp.tool              # Create a tool (action)
@mcp.resource("uri")   # Create a resource (data)
@mcp.prompt            # Create a prompt template
```

### Server Transports

```python
mcp.run()                           # stdio (local)
mcp.run(transport="sse", port=8000) # HTTP/SSE (remote)
mcp.run(transport="streamable-http") # Modern HTTP
```

### OpenAI Agents SDK

```python
# Basic agent
Agent(name="...", instructions="...", tools=[...])

# With MCP
Agent(name="...", instructions="...", mcp_servers=[server])

# Run agent
Runner.run_sync(agent, "query")      # Sync
await Runner.run(agent, "query")     # Async
```

### MCP Server Connections

```python
# SSE (HTTP)
MCPServerSse(params={"url": "http://..."})

# Stdio (subprocess)
MCPServerStdio(params={"command": "python", "args": ["server.py"]})
```

---

## 🎓 NEXT STEPS

1. **Add Authentication** - FastMCP supports OAuth, API keys
2. **Deploy to Cloud** - FastMCP Cloud or your own infra
3. **Multi-Agent Handoffs** - Let agents delegate to each other
4. **Guardrails** - Add input/output validation
5. **Tracing** - Debug and monitor agent workflows

---

## 📚 RESOURCES

- FastMCP Docs: https://gofastmcp.com
- OpenAI Agents SDK: https://openai.github.io/openai-agents-python/
- MCP Protocol: https://modelcontextprotocol.io

---

**Happy Building! 🚀**
