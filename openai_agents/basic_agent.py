from agents import Agent, Runner
import asyncio
from dotenv import load_dotenv
import os 
import sys


## Approach 1 Where we use open ai provider from agents and we have user AsyncOpenAI from openai



# ## if we want to access gemini by using openai-sdk

# load_dotenv()
# from openai import AsyncOpenAI
# from agents import set_tracing_disabled, RunConfig, set_default_openai_api
# from agents.models.openai_provider import OpenAIProvider

# set_tracing_disabled(True)

# set_default_openai_api("chat_completions")

# gemini_client = AsyncOpenAI(
#     base_url = "https://generativelanguage.googleapis.com/v1beta/openai/",
#     api_key = os.getenv("GEMINI_API_KEY")
# )

# async def main():

#     GEMINI_PROVIDER = OpenAIProvider(openai_client=gemini_client)
#     RUN_CONFIG = RunConfig(
#         model = "gemini-2.5-flash-lite",
#         model_provider = GEMINI_PROVIDER
#     ) 


#     agent = Agent(
#         name= "Assistant",
#         instructions= "You are a helpful assistant that answer question clearly and concisely."
#     )

#     result = await Runner.run(
#         agent,
#         input="What is the capital of France??",
#         run_config = RUN_CONFIG

#     )

#     print(result.final_output)



## if we want to access Ollama models by using openai-sdk

# load_dotenv()
# from openai import AsyncOpenAI
# from agents import set_tracing_disabled, RunConfig, set_default_openai_api
# from agents.models.openai_provider import OpenAIProvider


# ollama_client = AsyncOpenAI(
#     base_url = "http://localhost:11434/v1",
#     api_key = "OLLAMA"
# )

# async def main():

#     ollama_provider = OpenAIProvider(openai_client=ollama_client)
#     RUN_CONFIG = RunConfig(
#         model = "ministral-3:3b",
#         model_provider = ollama_provider,
#         tracing_disabled=True
#     ) 


#     agent = Agent(
#         name= "Assistant",
#         instructions= "You are a helpful assistant that answer question clearly and concisely."
#     )

#     result = await Runner.run(
#         agent,
#         input="What is the capital of France??",
#         run_config = RUN_CONFIG

#     )

#     print(result.final_output)





### Approach 2 

### here the case is we don't want to use run config we want to create agent and we explicitly provide them a model.

## here we prvovide model to each agent sepratly. 

# from agents import OpenAIChatCompletionsModel
# from agents import Agent, Runner, RunConfig
# from dotenv import load_dotenv
# import os 
# import sys
# import asyncio
# from openai import AsyncOpenAI


# load_dotenv()


# gemini_client = AsyncOpenAI(
#     base_url = "https://generativelanguage.googleapis.com/v1beta/openai/",
#     api_key = os.getenv("GEMINI_API_KEY")
#     )


# async def main():
    
#     agent = Agent(
#         name = "Assistant",
#         instructions = "You are a helpful assistant that answer question clearly and concisely.",
#         model = OpenAIChatCompletionsModel(
#             openai_client = gemini_client,
#             model = "gemini-2.5-flash-lite"
#         )

#     )

#     result = await Runner.run(
#         agent,
#         input=  "What is 2 + 2 = ??",
#         run_config = RunConfig(
#             tracing_disabled=True
#         )
#     )    

#     print(result.final_output)


from agents import OpenAIChatCompletionsModel
from agents import Agent, Runner, RunConfig
from dotenv import load_dotenv
import os 
import sys
import asyncio
from openai import AsyncOpenAI

load_dotenv()

ollama_client = AsyncOpenAI(
    base_url = "http://localhost:11434/v1",
    api_key = "OLLAMA"
    )


async def main():
    agent = Agent(
        name = "Assistant",
        instructions = "You are a helpful assistant that answer question clearly and concisely.",
        model = OpenAIChatCompletionsModel(
            openai_client = ollama_client,
            model = "ministral-3:3b"
        )
    )

    result = await Runner.run(
        agent,
        input=  "What is 2 + 2 = ??",
        run_config = RunConfig(
            tracing_disabled=True
        )
    )    

    print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())
