import asyncio
from agents import Agent, Runner, Tool, function_schema, function_tool, RunContextWrapper
from dotenv import load_dotenv
from openai.types.responses import ResponseTextDeltaEvent, ResponseFunctionCallArgumentsDeltaEvent

from agents import AgentToolStreamEvent, ModelSettings

load_dotenv()
 

@function_tool(
    name_override="billing_status_checker",
    description_override="Answer questions about customer billing status."
               )
def billing_status_checker(customer_id: str | None = None, question:str= "") -> str:
    
    """ Return a canned billing answer or a fallback when the question is unrelated."""
    
    normalized = question.lower()
    
    if "bill" in normalized or "billing" in normalized :
        return f"This customer (ID: {customer_id}'s bill is $1oo)"
    
    return "I can only answer questions about billing."


def handle_stream(event:AgentToolStreamEvent) -> None:
    """ Print Streaming events emitted by the nested billing agent."""
    
    stream = event["event"]
    tool_call = event.get("tool_call")
    tool_call_info = tool_call.call_id if tool_call is not None else "unknow"
    
    print(f"[Stream] agent={event["agent"].name} call= {tool_call_info} type = {stream.type} {stream}" )
    

            
            
async def main() -> None:

    billing_agent = Agent(
        name="Billing Agent",
        instructions="You are a billing agent that answers billing questions.",
        model_settings=ModelSettings(tool_choice="required"),
        tools=[billing_status_checker],
    )

    billing_agent_tool = billing_agent.as_tool(
        tool_name="billing_agent",
        tool_description="You are a billing agent that answers billing questions.",
        on_stream=handle_stream,
    )

    main_agent = Agent(
        name="Customer Support Agent",
        instructions=(
            "You are a customer support agent. Always call the billing agent to answer billing "
            "questions and return the billing agent response to the user."
        ),
        tools=[billing_agent_tool],
    )

    # result = await Runner.run(
    #     main_agent,
    #     "Hello, my customer ID is ABC123. How much is my bill for this month?",
    # )

    # print(f"\nFinal response:\n{result.final_output}")
    
    
    result = Runner.run_streamed(main_agent, "Hello, my customer ID is ABC123. How much is my bill for this month?",)
    
    async for event in result.stream_events():
        # print(f"Event: {event}")
        pass
        
    print(result.final_output)
    
    
    # out_stream = Runner.run_streamed(main_agent,
    #     "Hello, my customer ID is ABC123. How much is my bill for this month?",)
    
    # async for event in out_stream.events:
    #     if event.type == "message_delta" and event.delta.content:
    #         print(event.delta.content, end="", flush=True)
            
    #     elif event.type == "run_step_completed":
    #          pass

    # print(f"Type: {type(out_stream)}")
    # attributes = [attr for attr in dir(out_stream) if not attr.startswith("_")]
    # # print(attributes)
    
    # async for event in out_stream.stream_events():
    #     if event.type == "raw_response_event":
    #         if isinstance(event.data, ResponseTextDeltaEvent) or isinstance(event.data,     ResponseFunctionCallArgumentsDeltaEvent):
    #             print(event.data.delta, end= "", flush=True)
        
    #     elif event.type == "message_delta" and event.delta.content:
    #         print(event.delta.content, end="", flush=True)

    #     elif event.type == "run_step_completed":
    #                 pass

    #     elif event.type == "run_item_stream_event":
    #         if event.name == "tool_called":
    #             print()
    #             print(f">> Tool Called, name: {event.item.raw_item.name}")
    #             print(f">> Tool Called, args: {event.item.raw_item.arguments}")
                
    #         elif event.name == "tool_output":
    #             print(f">> Tool output: {event.item.raw_item["output"]}")
                




if __name__ == "__main__":
    asyncio.run(main())