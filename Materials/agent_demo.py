"""
OpenAI Agent with FastMCP Integration
Run: python agent_demo.py (after starting my_server.py)
"""

import asyncio
from agents import Agent, Runner
from agents.mcp import MCPServerSse


async def main():
    print("🤖 Connecting to FastMCP Server...")
    
    # Connect to FastMCP server running on localhost:8000
    async with MCPServerSse(
        name="TaskManager",
        params={
            "url": "http://localhost:8000/sse",
        },
        cache_tools_list=True
    ) as mcp_server:
        
        print("✅ Connected! Creating agent...")
        
        # Create agent with MCP server
        agent = Agent(
            name="TaskAssistant",
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
            mcp_servers=[mcp_server]
        )
        
        print("✅ Agent ready!\n")
        print("=" * 50)
        print("💬 INTERACTIVE TASK ASSISTANT")
        print("=" * 50)
        print("Type your queries below. Type 'quit' to exit.\n")
        
        # Interactive loop
        while True:
            try:
                user_input = input("👤 You: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                
                if not user_input:
                    continue
                
                print("🤖 Thinking...")
                result = await Runner.run(agent, user_input)
                print(f"🤖 Agent: {result.final_output}\n")
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}\n")


async def demo_queries():
    """Run a set of demo queries"""
    print("🤖 Running Demo Queries...")
    
    async with MCPServerSse(
        name="TaskManager",
        params={"url": "http://localhost:8000/sse"},
        cache_tools_list=True
    ) as mcp_server:
        
        agent = Agent(
            name="TaskAssistant",
            instructions="""You are a task management assistant.
            Help users manage their tasks efficiently.
            Be concise and action-oriented.""",
            mcp_servers=[mcp_server]
        )
        
        queries = [
            "Show me all my current tasks",
            "Create a new high priority task called 'Learn OpenAI Agents SDK'",
            "Mark task 1 as completed",
            "Give me a summary of my task priorities",
        ]
        
        for query in queries:
            print(f"\n{'='*50}")
            print(f"👤 Query: {query}")
            print("-" * 50)
            result = await Runner.run(agent, query)
            print(f"🤖 Response: {result.final_output}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        # Run demo queries
        asyncio.run(demo_queries())
    else:
        # Run interactive mode
        asyncio.run(main())
