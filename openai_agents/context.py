from agents import Agent, Runner, function_tool, RunConfig, RunContextWrapper
from pydantic import BaseModel 
from dotenv import load_dotenv
import asyncio

load_dotenv()


## lets define the user context
class UserContext(BaseModel):
    user_id: str
    user_name: str
    is_allowded: bool
    api_calls: int



@function_tool
async def get_user_information(ctx: RunContextWrapper[UserContext]):
    ctx.context.user_name = "Dhruv Panchal"
    return ctx.context



agent = Agent(
    name="User helpfull Agent",
    instructions="Help Full User with their account.",
    tools=[get_user_information],
    
)


async def main(user_id, user_name):
    user = UserContext(user_id=user_id, user_name=user_name, is_allowded=True, api_calls=0)
    print(user.user_name)
    result = await Runner.run(agent, "who i am ?", context=user, run_config=RunConfig(tracing_disabled=True))
    print(result.final_output)

    print("\n\n")

    print("This is user information")
    print(user.user_name)



if __name__ == "__main__":
    asyncio.run(main("1", "Dhruv"))