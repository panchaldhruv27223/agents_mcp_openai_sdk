import os 
import sys
from agents import Agent, Runner, RunContextWrapper, RunHooks, Tool, function_tool, FunctionTool, AgentHooks, input_guardrail, output_guardrail, InputGuardrailTripwireTriggered, OutputGuardrailTripwireTriggered

from agents.items import ToolCallItem, ToolCallOutputItem
from pydantic import BaseModel
from typing import Any
from dotenv import load_dotenv
import asyncio

load_dotenv()


### 
@function_tool
def delete_file(filename:str) -> str:
    """Delete a file"""
    
    response = input(f"        ALLOW?(y/n) deleting this file {filename}: ").strip().lower()
    
    if response == "y":
        return f"File Deleted {filename}."
    else:
        return f"User denied permission to delete {filename}"
    

@function_tool
def send_mail(to:str, subject:str, body:str)->str:
    """Send An Email (asks for permission first)"""
    
    response = input("    ALLOW?? (y/n): ").strip().lower()
    
    if response == "y":
        return f"Email sent to {to}."
    else:
        return f"User denied permission to send email"
    
    
    
    
#### lets try this pattern

async def demo_1():
    agent = Agent(
        name= "FileManager",
        instructions="Help manage files. use tools when asked",
        tools = [delete_file, send_mail]
    )
    
    
    result = await Runner.run(agent, "Delete the file called 'important_data.txt'")
    
    print(f"Result: {result.final_output}")
    
    
# if __name__ == "__main__":
#     asyncio.run(demo_1())









from agents.exceptions import UserError 

### This same thing lets do via hook

sensitive_tools = {"delete_file", "send_email", "make_payment", "execute_query"}

class PermissionHooks(AgentHooks):
    """Custom Hooks to intercept tool calls and ask permission."""
    
    async def on_tool_start(self, context: RunContextWrapper[Any], agent: Agent[Any], tool: Tool) -> None:
        """Call BEFORE a tool executes."""
        
        tool_name = tool.name
        
        if tool_name in sensitive_tools:
            print(f"Hook intercepted: {tool.name}")
            
            response = input(f"  Allow '{tool_name}'?? (y/n):").strip().lower()
            
            if response != "y":
                raise PermissionDeniedError(f"User denied permission for {tool_name}")
            
    
    async def on_tool_end(self, context: RunContextWrapper[Any], agent: Agent[Any], tool: Tool, result: str) -> None:
        """Called  After a tool executes."""
        print(f"     Tool '{tool.name}' Completed")
        
        

class PermissionDeniedError(Exception):
    """Raised when user denies permission."""
    
    def __init__(self, msg):
        super()
        self.msg = msg





@function_tool
def delete_file(filename: str) -> str:
    """Delete a file."""
    return f"Deleted {filename}"


@function_tool
def read_file(filename: str) -> str:
    """Read a file (not sensitive)."""
    return f"Contents of {filename}: Hello World!"


async def demo_pattern_2():
    """Demo: Agent hooks for permission."""
    
    agent = Agent(
        name = "FileManager",
        instructions="Help manage files.",
        tools = [delete_file, read_file],
        hooks = PermissionHooks(),
    )
    
    
    try:
        
        result = await Runner.run(agent, "delete test.txt")
        print(f"Result: {result.final_output}")
        
    except PermissionDeniedError as error:
        print(f"\n Operation cancelled: {error}")
        
    except UserError as error:
        if "denied permission" in str(error):
            print(f"Operation cancelled: Permission denied.")
            
        else:
            print(f"New error: {error}")
            
    
    
    print("\n--- Now trying a non-sensitive operation ---")
    result = await Runner.run(agent, "Read the file config.txt")
    print(f"\nResult: {result.final_output}")
    
    
    
# if __name__ == "__main__":
#     asyncio.run(demo_pattern_2())







## let try this new pattern

class ActionPlan(BaseModel):
    """Structured plan output."""
    steps: list[str]
    tools_to_use: list[str]
    risks: list[str]
    estimated_impact: str


planning_agent = Agent(
    name="Planner",
    instructions="""You are a planning agent. When user asks to do something:
    1. Describe what steps you WOULD take
    2. List tools you WOULD use
    3. Identify risks
    4. DO NOT actually execute anything
    
    Output a structured plan.""",
    output_type=ActionPlan,  # Structured output
)


@function_tool
def execute_database_query(query: str) -> str:
    """Execute a database query."""
    return f"Query executed: {query}. Affected 150 rows."


@function_tool
def backup_database(db_name: str) -> str:
    """Create a database backup."""
    return f"Backup created for {db_name}"


execution_agent = Agent(
    name="Executor",
    instructions="Execute the approved plan using available tools.",
    tools=[execute_database_query, backup_database],
)

async def demo_pattern_3():
    user_request = "Delete All inactive users from the databse"
    
    plan_result = await Runner.run(planning_agent, user_request)
    
    plan : ActionPlan = plan_result.final_output_as(ActionPlan)
    
    print(plan)
    
    approval = input("\n Approve this plan?? (y/n):").strip().lower()
    
    if approval == "y":
        
        execution_prompt = f"""Execute this approved plan:
        original request: {user_request}
        steps: {plan.steps}
        """
        
        exec_result = await Runner.run(execution_agent, execution_prompt)
        
        print(f"Execution result: {exec_result.final_output}")
        
        
    else:
        
        print("\n Plan rejected. No actions taken.")
        
# if __name__ == "__main__":
#     asyncio.run(demo_pattern_3())











