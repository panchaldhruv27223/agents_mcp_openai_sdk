import asyncio
from agents import Agent, Runner, RunConfig, function_tool, RunContextWrapper
from agents import AgentHooks, RunHooks
from dotenv import load_dotenv
import time
from agents import TContext, TResponseInputItem
from typing import Optional 
from agents import ModelResponse
from agents import Tool
from agents import Agent
from typing import Any

load_dotenv()

@function_tool
async def fetch_transaction_details(tx_id:str):
    """Fetch transction details"""

    await asyncio.sleep(0.5)

    return f"Transaction {tx_id}: Amount=$5000. Location=Nigeria, user=john"

@function_tool
async def analyze_risk(amount:int, location:str):
    """Analyze risk based on amount and location"""
    await asyncio.sleep(0.5)
    if amount > 2000 and location != "US":
        return "RISK LEVEL: HIGH"
    
    return "RISK LEVEL: LOW"


#### Lets define the hooks 
## This is a run hooks

class AuditTimeHook(RunHooks):
    async def on_llm_start(
        self,
        context: RunContextWrapper[TContext],
        agent: Agent[TContext],
        system_prompt: Optional[str],
        input_items: list[TResponseInputItem],
    ) -> None:
        print("Wooow LLM is starting")
        print(agent.name)
        print("\n\n")

    async def on_llm_end(
        self,
        context: RunContextWrapper[TContext],
        agent: Agent[TContext],
        response: ModelResponse,
    ) -> None:
        print("Wooow LLM is ending")
        print(agent.name)
        print("\n\n")

    async def on_agent_start(self, context: RunContextWrapper[TContext], agent: Agent) -> None:
        print("Agent is starting")
        print(agent.name)
        print("\n\n")

    async def on_agent_end(
        self,
        context: RunContextWrapper[TContext],
        agent: Agent,
        output: Any,
    ) -> None:
        print("Agent is ending")
        print(agent.name)
        print("\n\n")

    async def on_handoff(
        self,
        context: RunContextWrapper[TContext],
        from_agent: Agent,
        to_agent: Agent,
    ) -> None:
        print("Handoff is starting")
        print(from_agent.name)
        print(to_agent.name)
        print("\n\n")

    async def on_tool_start(
        self,
        context: RunContextWrapper[TContext],
        agent: Agent,
        tool: Tool,
    ) -> None:
        print("Tool is starting")
        print(agent.name)
        print(tool.name)
        print("\n\n")

    async def on_tool_end(
        self,
        context: RunContextWrapper[TContext],
        agent: Agent,
        tool: Tool,
        result: str,
    ) -> None:
        print("Tool is ending")
        print(agent.name)
        print(tool.name)
        print("\n\n")


## Lets define the agent hooks 
class AuditAgentHook(AgentHooks):
    # async def on_start(self, ctx, agent):
    #     print(f"\n [Agent] {agent.name} is waking up....")

    # async def on_tool_start(self, ctx, agent, tool_call):
    #     print(f"[spy] Tool Requested: {tool_call}")

    # async def on_tool_end(self, ctx, agent, tool_call, tool_output):
    #     print(f"[spy] Tool Output: {tool_output}")

    # async def on_message_generation(self, ctx, message):
    #     print(f"[spy] Message Generated: {message}")

    async def on_start(self, context: RunContextWrapper[TContext], agent: Agent) -> None:
        print("Agent is starting")
        print(agent.name)
        print("\n\n")

    async def on_end(
        self,
        context: RunContextWrapper[TContext],
        agent: Agent,
        output: Any,
    ) -> None:
        print("Agent is ending")
        print(agent.name)
        print("\n\n")

    async def on_handoff(
        self,
        context: RunContextWrapper[TContext],
        agent: Agent,
        source: Agent,
    ) -> None:
        print("Agent is being handed off to")
        print(agent.name)
        print(source.name)
        print("\n\n")

    async def on_tool_start(
        self,
        context: RunContextWrapper[TContext],
        agent: Agent,
        tool: Tool,
    ) -> None:
        print("Tool is starting")
        print(agent.name)
        print(tool.name)
        print("\n\n")

    async def on_tool_end(
        self,
        context: RunContextWrapper[TContext],
        agent: Agent,
        tool: Tool,
        result: str,
    ) -> None:
        print("Tool is ending")
        print(agent.name)
        print(tool.name)
        print("\n\n")

    async def on_llm_start(
        self,
        context: RunContextWrapper[TContext],
        agent: Agent[TContext],
        system_prompt: Optional[str],
        input_items: list[TResponseInputItem],
    ) -> None:
        print("LLM is starting")
        print(agent.name)
        print("\n\n")

    async def on_llm_end(
        self,
        context: RunContextWrapper[TContext],
        agent: Agent[TContext],
        response: ModelResponse,
    ) -> None:
        print("LLM is ending")
        print(agent.name)
        print("\n\n")


async def main():
    try:
        agent = Agent(
            name = "FraudAuditor",
            instructions="You are a strict financial auditor. fetch transaction details, analyze risk, and give me a final verdict (APPROVE/REJECT).",
            tools=[fetch_transaction_details, analyze_risk],
            hooks= AuditAgentHook()
        )

        # result = await Runner.run(agent, "Check transaction 123456", hooks=AuditTimeHook())
        result = await Runner.run(agent, "Check transaction 123456")

        print(result.final_output)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())

    