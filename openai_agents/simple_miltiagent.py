"""
OpenAI Agent with fastmcp integration

"""

from agents import Agent, Runner
import asyncio
from agents.mcp import MCPServerSse, MCPServerStreamableHttp
from openai import AsyncOpenAI
from agents import OpenAIChatCompletionsModel
from dotenv import load_dotenv
import os 
import sys

load_dotenv()


async def main():

    # async with MCPServerSse(
    async with MCPServerStreamableHttp(
        name = "TaskManager",
        params = {
            "url" : "http://localhost:8000/mcp",
        },
        cache_tools_list = True
        ) as mcp_server:

        agent = Agent(
            name= "TaskAssistant",
            instructions="""You are a helpful task management assistant.
                    Your capabilities:
                    - View all tasks and their details
                    - Create new tasks with priorities
                    - Update task status (pending, in_progress, completed)
                    - Delete tasks
                    - Provide task summaries and insights

                    Always:
                    - Confirm actions you take
                    - Provide clear, concise responses
                    - Suggest next steps when appropriate""",
            mcp_servers = [mcp_server],
            # model = OpenAIChatCompletionsModel(
            #     openai_client = AsyncOpenAI(
            #         base_url = "https://generativelanguage.googleapis.com/v1beta/openai/",
            #         api_key = os.getenv("GEMINI_API_KEY")
            #     ),
            #     model = "gemini-2.5-flash-lite"
            # )
        )

        print("Agent Ready")
        print("Interactive task assistant")
        print("Type your queries below. Type 'quit' to exit.")



        while True:

            try:

                user_input = input("User:")

                if user_input.lower() == "quit":
                    break

                if not user_input.strip():
                    continue 

                print("Thinking ... ")

                response = await Runner.run(agent,user_input)

                print(f"Assistant: {response.final_output}")

            except Exception as e:
                print(f"Error: {e}") 
                break
        
        print("Developed by Dhruv Panchal.")



if __name__ == "__main__":
    asyncio.run(main())