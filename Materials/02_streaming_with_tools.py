"""
=============================================================================
OPENAI AGENTS SDK - STREAMING WITH TOOLS
=============================================================================

When agents use tools, streaming becomes more complex.
You'll see events for:
- Tool call requests
- Tool execution
- Tool results
- Final response

This file shows how to handle all of these.
"""

import asyncio
import json
from datetime import datetime
from agents import Agent, Runner, function_tool


# =============================================================================
# DEFINE SOME TOOLS
# =============================================================================

@function_tool
def get_weather(city: str) -> str:
    """Get current weather for a city."""
    # Simulated weather data
    weathers = {
        "tokyo": "☀️ Sunny, 22°C",
        "london": "🌧️ Rainy, 15°C",
        "new york": "⛅ Cloudy, 18°C",
        "paris": "🌤️ Partly cloudy, 20°C"
    }
    return weathers.get(city.lower(), f"🌡️ Weather for {city}: 20°C")


@function_tool
def get_time(timezone: str) -> str:
    """Get current time in a timezone."""
    return f"🕐 Current time in {timezone}: {datetime.now().strftime('%H:%M:%S')}"


@function_tool
def calculate(expression: str) -> str:
    """Calculate a math expression."""
    try:
        result = eval(expression)  # Simple eval for demo
        return f"🔢 {expression} = {result}"
    except Exception as e:
        return f"❌ Error: {e}"


# =============================================================================
# STREAMING WITH TOOLS - Basic
# =============================================================================

async def streaming_with_tools_basic():
    """
    Stream an agent that uses tools.
    Shows all event types including tool calls.
    """
    
    agent = Agent(
        name="WeatherBot",
        instructions="You help with weather information. Use the weather tool when asked.",
        tools=[get_weather],
        model="gpt-4o-mini"
    )
    
    result = Runner.run_streamed(
        agent,
        input="What's the weather in Tokyo?"
    )
    
    print("🌤️ Weather Query (with tool streaming):\n")
    print("-" * 50)
    
    async for event in result.stream_events():
        event_type = event.type
        
        if event_type == "raw_response_event":
            # Token streaming
            text = extract_text(event)
            if text:
                print(text, end="", flush=True)
                
        elif event_type == "run_item_created":
            item_type = getattr(event.item, 'type', 'unknown')
            if item_type == "tool_call":
                print(f"\n\n🔧 [Tool Call Started]")
                
        elif event_type == "run_item_completed":
            item = event.item
            item_type = getattr(item, 'type', 'unknown')
            
            if item_type == "tool_call":
                # Tool call completed
                tool_name = getattr(item, 'name', 'unknown')
                print(f"✅ [Tool '{tool_name}' completed]")
                
            elif item_type == "tool_result":
                # Tool returned a result
                output = getattr(item, 'output', '')
                print(f"📤 [Tool Result: {output}]\n")
    
    print("\n" + "-" * 50)
    print("\n✅ Complete!")


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
# STREAMING WITH MULTIPLE TOOLS
# =============================================================================

async def streaming_multi_tool():
    """
    Agent that can use multiple tools in one response.
    """
    
    agent = Agent(
        name="MultiToolBot",
        instructions="""You are a helpful assistant with access to:
        - Weather information
        - Time information  
        - Calculator
        
        Use the appropriate tool for each request.""",
        tools=[get_weather, get_time, calculate],
        model="gpt-4o-mini"
    )
    
    result = Runner.run_streamed(
        agent,
        input="What's 25 * 4, what's the weather in London, and what time is it in UTC?"
    )
    
    print("🛠️ Multi-Tool Query:\n")
    print("-" * 50)
    
    tool_calls = []
    
    async for event in result.stream_events():
        if event.type == "raw_response_event":
            text = extract_text(event)
            if text:
                print(text, end="", flush=True)
                
        elif event.type == "run_item_completed":
            item = event.item
            
            if getattr(item, 'type', '') == "tool_call":
                tool_name = getattr(item, 'name', 'unknown')
                tool_calls.append(tool_name)
                print(f"\n🔧 [{tool_name}] executed")
                
            elif getattr(item, 'type', '') == "tool_result":
                output = getattr(item, 'output', '')
                print(f"   → Result: {output}")
    
    print("\n" + "-" * 50)
    print(f"\n📊 Tools used: {', '.join(tool_calls)}")


# =============================================================================
# DETAILED TOOL STREAMING
# =============================================================================

async def detailed_tool_streaming():
    """
    Capture detailed information about tool execution.
    Useful for debugging and logging.
    """
    
    @function_tool
    def search_database(query: str, limit: int = 5) -> str:
        """Search a database for records."""
        # Simulate search
        return json.dumps({
            "query": query,
            "results": [f"Result {i+1} for '{query}'" for i in range(limit)],
            "total": limit
        })
    
    agent = Agent(
        name="SearchBot",
        instructions="You search databases. Always use the search tool.",
        tools=[search_database],
        model="gpt-4o-mini"
    )
    
    result = Runner.run_streamed(
        agent,
        input="Search for 'python tutorials' with limit 3"
    )
    
    print("🔍 Detailed Tool Streaming:\n")
    
    # Track all events
    events_log = []
    
    async for event in result.stream_events():
        # Log every event
        log_entry = {
            "type": event.type,
            "timestamp": datetime.now().isoformat()
        }
        
        if event.type == "run_item_created":
            item = event.item
            log_entry["item_type"] = getattr(item, 'type', 'unknown')
            log_entry["item_id"] = getattr(item, 'id', None)
            
            if getattr(item, 'type', '') == "tool_call":
                log_entry["tool_name"] = getattr(item, 'name', '')
                log_entry["tool_args"] = getattr(item, 'arguments', '{}')
                print(f"📞 Tool Call: {log_entry['tool_name']}")
                print(f"   Args: {log_entry['tool_args']}")
        
        elif event.type == "run_item_completed":
            item = event.item
            log_entry["item_type"] = getattr(item, 'type', 'unknown')
            
            if getattr(item, 'type', '') == "tool_result":
                output = getattr(item, 'output', '')
                log_entry["output"] = output
                print(f"📤 Tool Result:")
                # Pretty print JSON output
                try:
                    parsed = json.loads(output)
                    print(f"   {json.dumps(parsed, indent=2)}")
                except:
                    print(f"   {output}")
        
        elif event.type == "raw_response_event":
            text = extract_text(event)
            if text:
                print(text, end="", flush=True)
        
        events_log.append(log_entry)
    
    print(f"\n\n📊 Total events captured: {len(events_log)}")


# =============================================================================
# STREAMING EVENT HANDLER CLASS
# =============================================================================

class StreamEventHandler:
    """
    A reusable class to handle streaming events.
    Useful for web applications.
    """
    
    def __init__(self):
        self.tokens = []
        self.tool_calls = []
        self.tool_results = []
        self.errors = []
        
    async def handle_event(self, event):
        """Process a single event."""
        
        if event.type == "raw_response_event":
            text = extract_text(event)
            if text:
                self.tokens.append(text)
                return {"type": "token", "content": text}
                
        elif event.type == "run_item_created":
            item = event.item
            if getattr(item, 'type', '') == "tool_call":
                tool_info = {
                    "name": getattr(item, 'name', ''),
                    "arguments": getattr(item, 'arguments', '{}'),
                    "status": "started"
                }
                self.tool_calls.append(tool_info)
                return {"type": "tool_start", "tool": tool_info}
                
        elif event.type == "run_item_completed":
            item = event.item
            
            if getattr(item, 'type', '') == "tool_call":
                return {"type": "tool_call_complete"}
                
            elif getattr(item, 'type', '') == "tool_result":
                output = getattr(item, 'output', '')
                self.tool_results.append(output)
                return {"type": "tool_result", "output": output}
        
        return None
    
    def get_full_response(self) -> str:
        """Get the complete text response."""
        return "".join(self.tokens)
    
    def get_summary(self) -> dict:
        """Get a summary of the stream."""
        return {
            "token_count": len(self.tokens),
            "full_text": self.get_full_response(),
            "tool_calls": self.tool_calls,
            "tool_results": self.tool_results,
            "errors": self.errors
        }


async def using_event_handler():
    """
    Demonstrate using the StreamEventHandler class.
    """
    
    agent = Agent(
        name="HandlerDemo",
        instructions="You help with weather and calculations.",
        tools=[get_weather, calculate],
        model="gpt-4o-mini"
    )
    
    result = Runner.run_streamed(
        agent,
        input="What's 100 / 4 and what's the weather in Paris?"
    )
    
    # Use our handler
    handler = StreamEventHandler()
    
    print("🎯 Using StreamEventHandler:\n")
    
    async for event in result.stream_events():
        processed = await handler.handle_event(event)
        
        if processed:
            if processed["type"] == "token":
                print(processed["content"], end="", flush=True)
            elif processed["type"] == "tool_start":
                print(f"\n🔧 Starting: {processed['tool']['name']}")
            elif processed["type"] == "tool_result":
                print(f"   Result: {processed['output']}")
    
    # Get summary
    print("\n\n📊 Stream Summary:")
    summary = handler.get_summary()
    print(f"   • Tokens received: {summary['token_count']}")
    print(f"   • Tool calls: {len(summary['tool_calls'])}")
    print(f"   • Tool results: {len(summary['tool_results'])}")


# =============================================================================
# RUN ALL EXAMPLES
# =============================================================================

async def main():
    print("=" * 70)
    print("OPENAI AGENTS SDK - STREAMING WITH TOOLS")
    print("=" * 70)
    
    print("\n\n### Example 1: Basic Tool Streaming ###\n")
    await streaming_with_tools_basic()
    
    print("\n\n### Example 2: Multi-Tool Streaming ###\n")
    await streaming_multi_tool()
    
    print("\n\n### Example 3: Detailed Tool Streaming ###\n")
    await detailed_tool_streaming()
    
    print("\n\n### Example 4: Using Event Handler Class ###\n")
    await using_event_handler()
    
    print("\n\n" + "=" * 70)
    print("✅ ALL TOOL STREAMING EXAMPLES COMPLETE!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
