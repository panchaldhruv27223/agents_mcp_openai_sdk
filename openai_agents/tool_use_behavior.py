from __future__ import annotations

import asyncio
from typing import Any, Literal

from pydantic import BaseModel

from agents import (
    Agent,
    FunctionToolResult,
    ModelSettings,
    RunContextWrapper,
    Runner,
    ToolsToFinalOutputFunction,
    ToolsToFinalOutputResult,
    function_tool,
)

from dotenv import load_dotenv
load_dotenv()

class Weather(BaseModel):
    city:str
    temperature_range:str
    conditions:str
    

@function_tool
def get_weather(city:str) -> Weather:
    print(f"[DEBUG] get weather called")
    
    return Weather(city=city, temperature_range="14-30c", conditions="Sunny with wind")


async def custom_tool_use_behavior(
    context:RunContextWrapper[Any],
    results : list[FunctionToolResult]
) -> ToolsToFinalOutputResult:
    print("Custom Behavior tool calling is setting up:")
    print(f"Lets look what we get as results")
    print(results)
    print(f"\n\n Type of results that we got: ")
    print(type(results))
    print("*"*50)
    
    weather : Weather = results[0].output
    
    return ToolsToFinalOutputResult(
        is_final_output=True,
        final_output = f"{weather.city} is {weather.conditions}"
    )
    




async def main():
    tool_behavior  = "custom"
    
    
    if tool_behavior == "default":
        behavior = "run_llm_again"
        
    elif tool_behavior == "first_tool":
        behavior = "stop_on_first_tool"
        
    elif tool_behavior == "custom":
        behavior = custom_tool_use_behavior
        
        
    agent = Agent(
        name="weather agent",
        instructions="You are a helpful agent.",
        tools= [get_weather],
        tool_use_behavior=behavior,
        model_settings=ModelSettings(tool_choice="required" if behavior != "default" else None, parallel_tool_calls=True)
    )
    


if __name__ == "__main__":
    asyncio.run(main())