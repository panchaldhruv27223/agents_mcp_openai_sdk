"""
FastMCP Task Manager Server
Run: python my_server.py
"""

from fastmcp import FastMCP
from typing import Annotated
from pydantic import Field
import json

# Initialize the MCP server
mcp = FastMCP("TaskManager")

# In-memory database
tasks_db = {
    "1": {"id": "1", "title": "Learn FastMCP", "status": "in_progress", "priority": "high"},
    "2": {"id": "2", "title": "Build Agent", "status": "pending", "priority": "medium"},
}

# ============================================
# TOOLS - Actions the AI can perform
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
# RESOURCES - Read-only data access
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
# PROMPTS - Reusable instruction templates
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
# RUN THE SERVER
# ============================================

if __name__ == "__main__":
    print("🚀 Starting TaskManager MCP Server...")
    print("📡 Server URL: http://localhost:8000/sse")
    print("Press Ctrl+C to stop")
    mcp.run(transport="sse", port=8000)
