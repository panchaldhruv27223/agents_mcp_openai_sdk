import asyncio

from openai.types.responses import ResponseTextDeltaEvent
from pydantic import BaseModel, Field

from agents import Agent, Runner

from dotenv import load_dotenv

load_dotenv()

agent = Agent(
    name= "Assistant",
    instructions=(
        "You are a helpful assistant. you ALWAYS write long response, make sure to be verbose and detailed"
        
    )
)



class GuardrailOutput(BaseModel):
    reasoning: str = Field(
        description= "Reasoning about whether the response could be understood by a ten year old."
    )
    is_readable_by_ten_year_old: bool = Field(
        description="Whether the response is understandable by a ten year old"
    )
    
guardrail_agent = Agent(
    name="checker",
    
    instructions="you will be given a question and a reponse.1 your goal is to judge whether the response is simple enough to be understood by a ten year old.",

    output_type= GuardrailOutput
)


async def check_guardrail(text:str) -> GuardrailOutput:
    result = await Runner.run(guardrail_agent, text)
    
    return result.final_output_as(GuardrailOutput)


async def main():
    question = "what is a block hole, and how does it behave??"
    result = Runner.run_streamed(agent, question)
    
    current_text = ""

    next_guardrail_check_len = 300
    guardrail_task = None
    
    async for event in result.stream_events():
        
        if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
            
            print(event.data.delta, end="", flush=True)
            
            current_text += event.data.delta
            
            if len(current_text) >= next_guardrail_check_len and not guardrail_task:
                print("Running guardrail check")
                guardrail_task = asyncio.create_task(check_guardrail(current_text))
                next_guardrail_check_len += 300
                
                
        if guardrail_task and guardrail_task.done():
            guardrail_result = guardrail_task.result()
            if not guardrail_result.is_readable_by_ten_year_old:
                print("\n\n================\n\n")
                print(f"Guardrail triggered. Reasoning:\n{guardrail_result.reasoning}")
                break

    # Do one final check on the final output
    guardrail_result = await check_guardrail(current_text)
    if not guardrail_result.is_readable_by_ten_year_old:
        print("\n\n================\n\n")
        print(f"Guardrail triggered. Reasoning:\n{guardrail_result.reasoning}")


if __name__ == "__main__":
    asyncio.run(main())