"""
=============================================================================
OPENAI AGENTS SDK - STREAMING WITH HANDOFFS & MULTI-AGENT
=============================================================================

When agents hand off to other agents, streaming continues across agents.
This file shows how to track handoffs and multi-agent interactions.
"""

import asyncio
from agents import Agent, Runner, function_tool, handoff


# =============================================================================
# DEFINE SPECIALIZED AGENTS
# =============================================================================

# Technical Support Agent
tech_agent = Agent(
    name="TechSupport",
    instructions="""You are a technical support specialist.
    Help with technical issues, troubleshooting, and software problems.
    Be precise and technical.""",
    model="gpt-4o-mini"
)

# Billing Agent
billing_agent = Agent(
    name="BillingSupport",
    instructions="""You are a billing specialist.
    Help with invoices, payments, refunds, and account billing.
    Be professional and helpful.""",
    model="gpt-4o-mini"
)

# Triage Agent (Routes to specialists)
triage_agent = Agent(
    name="TriageBot",
    instructions="""You are a customer service triage agent.
    Determine what the customer needs and hand off to the right specialist:
    - Technical issues → hand off to TechSupport
    - Billing questions → hand off to BillingSupport
    
    Ask clarifying questions if needed before handing off.""",
    handoffs=[
        handoff(agent=tech_agent, description="For technical issues and troubleshooting"),
        handoff(agent=billing_agent, description="For billing, payments, and refunds"),
    ],
    model="gpt-4o-mini"
)


# =============================================================================
# STREAMING WITH HANDOFFS
# =============================================================================

async def streaming_handoff_example():
    """
    Stream a conversation that involves agent handoffs.
    Track when handoffs occur.
    """
    
    result = Runner.run_streamed(
        triage_agent,
        input="My software keeps crashing when I try to export files"
    )
    
    print("🔄 Streaming with Handoff:\n")
    print("-" * 60)
    
    current_agent = "TriageBot"
    
    async for event in result.stream_events():
        
        # Track agent changes
        if event.type == "agent_updated_event":
            new_agent = getattr(event.agent, 'name', 'Unknown')
            if new_agent != current_agent:
                print(f"\n\n🔀 [HANDOFF: {current_agent} → {new_agent}]\n")
                current_agent = new_agent
        
        # Stream tokens
        elif event.type == "raw_response_event":
            text = extract_text(event)
            if text:
                print(text, end="", flush=True)
        
        # Track handoff items
        elif event.type == "run_item_created":
            item = event.item
            if getattr(item, 'type', '') == "handoff":
                target = getattr(item, 'target_agent', 'Unknown')
                print(f"\n\n📤 [Initiating handoff to: {target}]")
        
        elif event.type == "run_item_completed":
            item = event.item
            if getattr(item, 'type', '') == "handoff":
                print(f"✅ [Handoff completed]")
    
    print("\n" + "-" * 60)
    print(f"\n✅ Final agent: {current_agent}")


def extract_text(event) -> str:
    """Extract text from raw_response_event."""
    try:
        data = event.data
        if hasattr(data, 'delta') and hasattr(data.delta, 'content'):
            return data.delta.content or ""
        return ""
    except:
        return ""


# =============================================================================
# DETAILED HANDOFF TRACKING
# =============================================================================

class HandoffTracker:
    """Track handoffs during streaming."""
    
    def __init__(self):
        self.agents_visited = []
        self.handoffs = []
        self.current_agent = None
        self.messages_per_agent = {}
    
    def track_agent(self, agent_name: str):
        if agent_name != self.current_agent:
            if self.current_agent:
                self.handoffs.append({
                    "from": self.current_agent,
                    "to": agent_name
                })
            if agent_name not in self.agents_visited:
                self.agents_visited.append(agent_name)
            self.current_agent = agent_name
            self.messages_per_agent[agent_name] = []
    
    def add_token(self, token: str):
        if self.current_agent:
            self.messages_per_agent[self.current_agent].append(token)
    
    def get_agent_response(self, agent_name: str) -> str:
        return "".join(self.messages_per_agent.get(agent_name, []))
    
    def get_summary(self) -> dict:
        return {
            "agents_visited": self.agents_visited,
            "handoffs": self.handoffs,
            "responses": {
                agent: self.get_agent_response(agent)
                for agent in self.agents_visited
            }
        }


async def detailed_handoff_tracking():
    """
    Track detailed handoff information.
    """
    
    result = Runner.run_streamed(
        triage_agent,
        input="I need a refund for my last payment"
    )
    
    tracker = HandoffTracker()
    tracker.track_agent("TriageBot")  # Initial agent
    
    print("📊 Detailed Handoff Tracking:\n")
    print("-" * 60)
    
    async for event in result.stream_events():
        
        if event.type == "agent_updated_event":
            agent_name = getattr(event.agent, 'name', 'Unknown')
            tracker.track_agent(agent_name)
            print(f"\n🔀 [Now: {agent_name}]\n")
        
        elif event.type == "raw_response_event":
            text = extract_text(event)
            if text:
                tracker.add_token(text)
                print(text, end="", flush=True)
    
    # Print summary
    summary = tracker.get_summary()
    
    print("\n" + "-" * 60)
    print("\n📊 Handoff Summary:")
    print(f"   Agents visited: {' → '.join(summary['agents_visited'])}")
    print(f"   Total handoffs: {len(summary['handoffs'])}")
    
    for handoff in summary['handoffs']:
        print(f"      • {handoff['from']} → {handoff['to']}")


# =============================================================================
# STREAMING MULTI-TURN WITH HANDOFFS
# =============================================================================

async def multi_turn_streaming():
    """
    Handle multi-turn conversations with streaming and handoffs.
    Maintains conversation history.
    """
    
    # Conversation history
    history = []
    
    # Simulated user inputs
    user_inputs = [
        "Hi, I have a problem",
        "My account is being charged twice",
        "Yes, please help me get a refund"
    ]
    
    print("💬 Multi-Turn Streaming Conversation:\n")
    print("=" * 60)
    
    for user_input in user_inputs:
        print(f"\n👤 User: {user_input}\n")
        
        # Add to history
        history.append({"role": "user", "content": user_input})
        
        # Stream response
        result = Runner.run_streamed(
            triage_agent,
            input=history  # Pass full history
        )
        
        assistant_response = []
        current_agent = "TriageBot"
        
        print(f"🤖 [{current_agent}]: ", end="")
        
        async for event in result.stream_events():
            
            if event.type == "agent_updated_event":
                new_agent = getattr(event.agent, 'name', 'Unknown')
                if new_agent != current_agent:
                    print(f"\n\n🔀 [Handoff to {new_agent}]")
                    print(f"🤖 [{new_agent}]: ", end="")
                    current_agent = new_agent
            
            elif event.type == "raw_response_event":
                text = extract_text(event)
                if text:
                    assistant_response.append(text)
                    print(text, end="", flush=True)
        
        # Add assistant response to history
        full_response = "".join(assistant_response)
        history.append({"role": "assistant", "content": full_response})
        
        print("\n")
        print("-" * 60)
    
    print("\n✅ Conversation complete!")
    print(f"📝 Total turns: {len(history) // 2}")


# =============================================================================
# PARALLEL AGENT STREAMING (Simulated)
# =============================================================================

async def stream_single_agent(agent: Agent, prompt: str, name: str):
    """Helper to stream a single agent."""
    result = Runner.run_streamed(agent, input=prompt)
    
    tokens = []
    async for event in result.stream_events():
        if event.type == "raw_response_event":
            text = extract_text(event)
            if text:
                tokens.append(text)
    
    return {"agent": name, "response": "".join(tokens)}


async def parallel_agent_streaming():
    """
    Stream multiple agents in parallel (for comparison).
    """
    
    # Create different agents for comparison
    agents = [
        Agent(
            name="Concise",
            instructions="Be extremely brief and concise. One sentence max.",
            model="gpt-4o-mini"
        ),
        Agent(
            name="Detailed",
            instructions="Be detailed and thorough in explanations.",
            model="gpt-4o-mini"
        ),
        Agent(
            name="Creative",
            instructions="Be creative and use metaphors/analogies.",
            model="gpt-4o-mini"
        )
    ]
    
    prompt = "Explain what an API is"
    
    print("🔀 Parallel Agent Streaming:\n")
    print(f"📝 Prompt: {prompt}\n")
    print("-" * 60)
    
    # Run all agents in parallel
    tasks = [
        stream_single_agent(agent, prompt, agent.name)
        for agent in agents
    ]
    
    results = await asyncio.gather(*tasks)
    
    # Display results
    for result in results:
        print(f"\n🤖 [{result['agent']}]:")
        print(f"   {result['response'][:200]}...")  # First 200 chars
    
    print("\n" + "-" * 60)
    print("✅ All agents complete!")


# =============================================================================
# RUN ALL EXAMPLES
# =============================================================================

async def main():
    print("=" * 70)
    print("OPENAI AGENTS SDK - STREAMING WITH HANDOFFS")
    print("=" * 70)
    
    print("\n\n### Example 1: Basic Handoff Streaming ###\n")
    await streaming_handoff_example()
    
    print("\n\n### Example 2: Detailed Handoff Tracking ###\n")
    await detailed_handoff_tracking()
    
    print("\n\n### Example 3: Multi-Turn Streaming ###\n")
    await multi_turn_streaming()
    
    print("\n\n### Example 4: Parallel Agent Streaming ###\n")
    await parallel_agent_streaming()
    
    print("\n\n" + "=" * 70)
    print("✅ ALL HANDOFF STREAMING EXAMPLES COMPLETE!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
