from agents import Agent, Runner, RunConfig, OpenAIChatCompletionsModel
from openai import AsyncOpenAI
from dotenv import load_dotenv
import os 
import asyncio


load_dotenv()

client = AsyncOpenAI(
    api_key= os.getenv("OLLAMA_API_KEY"),
    base_url = "http://localhost:11434/v1"
)


def create_ollama_model():
    return OpenAIChatCompletionsModel(
        model=os.getenv("OLLAMA_MODEL_NAME"),
        openai_client=client
    )


# Research Agent - finds information
research_agent = Agent(
    name="ResearchAgent",
    instructions="""You are a research specialist.
- Provide factual, well-researched information
- Be concise but comprehensive
- Focus on accuracy""",
    model=create_ollama_model(),
)

# Writer Agent - writes content
writer_agent = Agent(
    name="WriterAgent",
    instructions="""You are a creative writer.
- Write engaging, well-structured content
- Use clear and compelling language
- Adapt tone to the request""",
    model=create_ollama_model(),
)

# Critic Agent - reviews and improves
critic_agent = Agent(
    name="CriticAgent",
    instructions="""You are a constructive critic.
- Review content for quality and accuracy
- Suggest specific improvements
- Be helpful, not harsh""",
    model=create_ollama_model(),
)

## Main Agent 
## Coordinator Main Agent

project_coordinator_agent = Agent(
    name="ProjectCoordinatorAgent",
    instructions="""You are a project coordinator that manages a team of specialists.

Your team (available as tools):
1. research_expert - Use for gathering facts and information
2. writing_expert - Use for creating written content
3. review_expert - Use for reviewing and improving content

For complex tasks:
1. First, use research_expert to gather information
2. Then, use writing_expert to create content
3. Finally, use review_expert to get feedback

Compile all inputs into a polished final response.
Always coordinate - don't do specialist work yourself.""",
    model=create_ollama_model(),
    tools=[
        # Convert agents to tools!
        research_agent.as_tool(
            tool_name="research_expert",
            tool_description="Research specialist. Use for gathering facts, data, and information on any topic.",
        ),
        writer_agent.as_tool(
            tool_name="writing_expert", 
            tool_description="Writing specialist. Use for creating articles, summaries, or any written content.",
        ),
        critic_agent.as_tool(
            tool_name="review_expert",
            tool_description="Review specialist. Use for critiquing and improving content quality.",
        ),
    ],
)


#### Translator Agents

spanish_translator = Agent(
    name="SpanishTranslator",
    instructions="You translate text to Spanish. Return ONLY the translation, nothing else.",
    model=create_ollama_model(),
)

french_translator = Agent(
    name="FrenchTranslator", 
    instructions="You translate text to French. Return ONLY the translation, nothing else.",
    model=create_ollama_model(),
)

german_translator = Agent(
    name="GermanTranslator",
    instructions="You translate text to German. Return ONLY the translation, nothing else.",
    model=create_ollama_model(),
)

translation_coordinator = Agent(
    name="TranslationCoordinator",
    instructions="""You coordinate translations to multiple languages.

When user asks to translate something:
1. Use the appropriate translator tools
2. Compile all translations in a nice format
3. Present results clearly

Available tools: spanish_translator, french_translator, german_translator""",
    model=create_ollama_model(),
    tools=[
        spanish_translator.as_tool(
            tool_name="spanish_translator",
            tool_description="Translates text to Spanish",
        ),
        french_translator.as_tool(
            tool_name="french_translator",
            tool_description="Translates text to French",
        ),
        german_translator.as_tool(
            tool_name="german_translator",
            tool_description="Translates text to German",
        ),
    ],
)



## lets first test the coordinator individually 

async def main():

    result = await Runner.run(project_coordinator_agent, "I want to learn about mcp in ai, give me path to follow.", run_config=RunConfig(tracing_disabled=True))

    print("Coordinator output:")
    print(result)
    print("Final Result: ")
    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())