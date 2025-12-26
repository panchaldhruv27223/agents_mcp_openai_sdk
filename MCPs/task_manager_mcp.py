from fastmcp import FastMCP
import asyncio
import json
from pydantic import Field
from typing import Annotated, Optional


mcp = FastMCP(
    name = "TaskManager"
)

## demo task db 

tasks_db  = {
    "1" : {"id" : 1, "title": "Learn FastMCP", "Status" : "In Progress", "Priority" : "High"},
    "2" : {"id" : 2, "title": "Learn OpenAI SDK", "Status" : "In Progress", "Priority" : "High"},
    "3" : {"id" : 3, "title": "Learn Python", "Status" : "Done", "Priority" : None}
}



### Tool definitions

async def get_all_tasks() -> str:
    """
    get all tasks from database 
    """
    return json.dumps(tasks_db, indent=2)


async def get_task_by_id(task_id: Annotated[str, Field(description="Id of the task.")]) -> str:
    """
    get task by id from database
    """
    if task_id not in tasks_db:
        return json.dumps({"error" : f"task {task_id} not found"})

    return json.dumps(tasks_db[task_id], indent = 2)

async def get_task_by_status(status: Annotated[str, Field(description="Status of the task.")]) -> str:
    """
    get task by status from database
    """
    
    result = [] 

    for task_key, task_value in tasks_db.items():

        if (task_value["Status"]).lower() == status.lower():
            result.append(task_value)

    return json.dumps(result, indent=2)

async def get_task_by_priority(priority: Annotated[str, Field(description="Priority of the task.")]) -> str:
    """
    get task by priority from database
    """
    
    result = [] 

    for task_key, task_value in tasks_db.items():

        if task_value["Priority"] == priority:
            result.append(task_value)

    return json.dumps(result, indent=2)


## also we can add function as tool in mcp.


mcp.tool((get_all_tasks))
mcp.tool((get_task_by_id))
mcp.tool((get_task_by_status))
mcp.tool((get_task_by_priority))


@mcp.tool()
async def create_task(
    
    title : Annotated[str, Field(description="Title of the task.")],
    status : Annotated[str, Field(description="Status of the task.")],
    priority : Annotated[str, Field(description="Priority of the task.")]
    
    ) -> str:
    
    """
    create new task in database
    """
    
    new_id = str(len(tasks_db) + 1)

    new_task = {
        "id" : new_id,
        "title" : title,
        "Status" : status,
        "Priority" : priority
        }
    
    tasks_db[new_id] = new_task

    return json.dumps({"success" : True, "task" : new_id})


@mcp.tool()
async def update_task_status(
    task_id  : Annotated[str, Field(description= "The task id to update")],
    status : Annotated[str, Field(description= "New status: pending, in progress, done")]
    ) -> str:
    """
    Update the status of a task
    """
    if task_id not in tasks_db:
        return json.dumps({"error" : f"task {task_id} not found"})

    tasks_db[task_id]["Status"] = status

    return json.dumps({"success" : True, "task" : task_id})


@mcp.tool()
async def delete_task(
    task_id  : Annotated[str, Field(description= "The task id to delete")]
    ) -> str:
    """
    Delete a task from database
    """
    if task_id not in tasks_db:
        return json.dumps({"error" : f"task {task_id} not found"})

    del tasks_db[task_id]

    return json.dumps({"success" : True, "task" : task_id})



## resources - read only data access


@mcp.resource("tasks://summary")
def get_task_summary() -> str:
    """
    get summary of tasks
    """

    total = len(tasks_db)
    by_status = {}
    by_priority = {}

    for task_key, task_value in tasks_db.items():

        if task_value["Status"] not in by_status:
            by_status[task_value["Status"]] = 0

        if task_value["Priority"] not in by_priority:
            by_priority[task_value["Priority"]] = 0

        by_status[task_value["Status"]] += 1
        by_priority[task_value["Priority"]] += 1

    return json.dumps({"total" : total, "by_status" : by_status, "by_priority" : by_priority}, indent=2)


@mcp.resource("tasks://{task_id}")
def get_task_resource(task_id:str) -> str:
    """
    Get Task details as a resource
    """

    if task_id not in tasks_db:
        return json.dumps({"error" : f"task {task_id} not found"})

    return json.dumps(tasks_db[task_id], indent = 2)



## Prompts templates


@mcp.prompt()
def task_analysis_prompt() -> str:
    """
    Generate a prompt for analysis tasks
    """

    return """You are a task management assistant, analyze the current task and provide:

1. A summary of pending vs completed tasks
2. Recommendations for prioritization
3. Any tasks that might be blocked  or need attention

use the available tools to fetch task data before providing your analysis.
"""

@mcp.prompt()
def daily_standup_prompt(focus_area: str ="all") -> str:
    """
    Generate daily standup report"
    """
    return """Generate a daily standup report focusing on: {focus_area}

Include:
- what was completed yesterday
- what is planned for today
- any blockers or issues

use the task management tools to gather accuearte informaiton before providing your report.
"""




if __name__ == "__main__":

    # mcp.run()
    # print(asyncio.run(get_task_by_id("1")))
    # print(asyncio.run(get_task_by_status("In Progress")))
    # print(asyncio.run(get_task_by_priority("High")))
    # print(asyncio.run(get_all_tasks()))

    # print(type(asyncio.run(get_task_by_id("1"))))
    # print(type(asyncio.run(get_task_by_status("In Progress"))))
    # print(type(asyncio.run(get_task_by_priority("High"))))
    # print(type(asyncio.run(get_all_tasks())))

    # asyncio.run(mcp.run())
    # mcp.run(transport= "sse", port=8000)
    mcp.run(transport="streamable-http", port=8000)