"""
=============================================================================
OPENAI AGENTS SDK - STREAMING FUNDAMENTALS
=============================================================================

Streaming allows you to receive agent responses in real-time, token by token,
instead of waiting for the complete response.

Why Streaming?
--------------
1. Better UX - Users see responses immediately
2. Perceived speed - App feels faster
3. Progress feedback - Know what's happening
4. Cancel early - Stop generation if needed

Key Concepts:
-------------
- Runner.run_streamed() - Returns a stream instead of final result
- StreamEvent - Different event types during execution
- Async iteration - Process events as they arrive
"""

import asyncio
from openai import AsyncOpenAI
from agents import Agent, Runner, function_tool

# =============================================================================
# BASIC STREAMING - Your First Stream
# =============================================================================

async def basic_streaming_example():
    """
    The simplest streaming example.
    Shows how to get real-time token output.
    """
    
    agent = Agent(
        name="StreamingBot",
        instructions="You are a helpful assistant. Be concise.",
        model="gpt-4o-mini"
    )
    
    # KEY: Use run_streamed() instead of run()
    result = Runner.run_streamed(
        agent,
        input="Explain Python in 3 sentences."
    )
    
    print("🔄 Streaming response:\n")
    
    # Iterate over the stream
    async for event in result.stream_events():
        # We'll explore event types in detail next
        # For now, just print raw events
        print(f"Event: {event.type}")
    
    # After streaming completes, get final result
    final = await result.final_output()
    print(f"\n✅ Final output: {final}")


# =============================================================================
# UNDERSTANDING STREAM EVENTS
# =============================================================================

"""
Stream Event Types:
-------------------

1. raw_response_event     - Raw API response chunks (tokens)
2. agent_updated_event    - Agent state changed
3. run_item_created       - New item (message, tool call) created
4. run_item_updated       - Item was updated
5. run_item_completed     - Item finished processing

The most important for UI: raw_response_event (contains tokens)
"""

async def explore_stream_events():
    """
    Explore all event types during streaming.
    """
    
    agent = Agent(
        name="EventExplorer",
        instructions="Be helpful and concise.",
        model="gpt-4o-mini"
    )
    
    result = Runner.run_streamed(agent, input="Say hello!")
    
    print("📊 All Stream Events:\n")
    print("-" * 60)
    
    async for event in result.stream_events():
        event_type = event.type
        
        # Categorize events
        if event_type == "raw_response_event":
            print(f"🔤 RAW_RESPONSE: Token data received")
            
        elif event_type == "agent_updated_event":
            print(f"🤖 AGENT_UPDATED: Agent state changed")
            
        elif event_type == "run_item_created":
            print(f"📝 ITEM_CREATED: {event.item.type}")
            
        elif event_type == "run_item_updated":
            print(f"🔄 ITEM_UPDATED: Item modified")
            
        elif event_type == "run_item_completed":
            print(f"✅ ITEM_COMPLETED: {event.item.type}")
            
        else:
            print(f"❓ OTHER: {event_type}")
    
    print("-" * 60)
    print(f"\n✅ Stream complete!")


# =============================================================================
# TOKEN-BY-TOKEN STREAMING (The Real Magic)
# =============================================================================

async def token_streaming_example():
    """
    Extract and display tokens as they arrive.
    This is what you'd use for a ChatGPT-like UI.
    """
    
    agent = Agent(
        name="TokenStreamer",
        instructions="You are a storyteller. Tell engaging short stories.",
        model="gpt-4o-mini"
    )
    
    result = Runner.run_streamed(
        agent, 
        input="Tell me a 2-sentence story about a robot."
    )
    
    print("📖 Story (token by token):\n")
    
    async for event in result.stream_events():
        # raw_response_event contains the actual tokens
        if event.type == "raw_response_event":
            # Get the raw response data
            data = event.data
            
            # Check if it has delta content (new tokens)
            if hasattr(data, 'delta') and hasattr(data.delta, 'content'):
                content = data.delta.content
                if content:
                    # Print token without newline (streaming effect)
                    print(content, end="", flush=True)
    
    print("\n\n✅ Story complete!")


# =============================================================================
# CLEANER TOKEN EXTRACTION
# =============================================================================

async def clean_token_streaming():
    """
    A cleaner approach to extract just the text tokens.
    Uses helper method if available, or manual extraction.
    """
    
    agent = Agent(
        name="CleanStreamer",
        instructions="Be helpful and friendly.",
        model="gpt-4o-mini"
    )
    
    result = Runner.run_streamed(
        agent,
        input="Count from 1 to 5 with a word for each number."
    )
    
    print("🔢 Counting:\n")
    
    collected_text = []
    
    async for event in result.stream_events():
        if event.type == "raw_response_event":
            # Try to get text from the event
            text = extract_text_from_event(event)
            if text:
                print(text, end="", flush=True)
                collected_text.append(text)
    
    print(f"\n\n📝 Total collected: {''.join(collected_text)}")


def extract_text_from_event(event) -> str:
    """
    Helper to safely extract text from a raw_response_event.
    """
    try:
        data = event.data
        
        # OpenAI streaming format
        if hasattr(data, 'delta'):
            delta = data.delta
            if hasattr(delta, 'content') and delta.content:
                return delta.content
        
        # Alternative: choices format
        if hasattr(data, 'choices') and data.choices:
            choice = data.choices[0]
            if hasattr(choice, 'delta') and choice.delta:
                if hasattr(choice.delta, 'content') and choice.delta.content:
                    return choice.delta.content
        
        return ""
    except Exception:
        return ""


# =============================================================================
# STREAMING WITH PROGRESS TRACKING
# =============================================================================

async def streaming_with_progress():
    """
    Track progress during streaming - useful for UI updates.
    """
    
    agent = Agent(
        name="ProgressTracker",
        instructions="Write detailed explanations.",
        model="gpt-4o-mini"
    )
    
    result = Runner.run_streamed(
        agent,
        input="Explain how a computer boots up in 3 steps."
    )
    
    # Progress counters
    token_count = 0
    event_count = 0
    start_time = asyncio.get_event_loop().time()
    
    print("⏳ Streaming with progress...\n")
    print("-" * 50)
    
    async for event in result.stream_events():
        event_count += 1
        
        if event.type == "raw_response_event":
            text = extract_text_from_event(event)
            if text:
                token_count += 1
                print(text, end="", flush=True)
    
    # Calculate stats
    elapsed = asyncio.get_event_loop().time() - start_time
    
    print("\n" + "-" * 50)
    print(f"\n📊 Stream Statistics:")
    print(f"   • Total events: {event_count}")
    print(f"   • Token chunks: {token_count}")
    print(f"   • Time elapsed: {elapsed:.2f}s")
    print(f"   • Tokens/second: {token_count/elapsed:.1f}")


# =============================================================================
# RUN ALL EXAMPLES
# =============================================================================

async def main():
    print("=" * 70)
    print("OPENAI AGENTS SDK - STREAMING BASICS")
    print("=" * 70)
    
    print("\n\n### Example 1: Basic Streaming ###\n")
    await basic_streaming_example()
    
    print("\n\n### Example 2: Explore Stream Events ###\n")
    await explore_stream_events()
    
    print("\n\n### Example 3: Token-by-Token Streaming ###\n")
    await token_streaming_example()
    
    print("\n\n### Example 4: Clean Token Extraction ###\n")
    await clean_token_streaming()
    
    print("\n\n### Example 5: Streaming with Progress ###\n")
    await streaming_with_progress()
    
    print("\n\n" + "=" * 70)
    print("✅ ALL STREAMING BASICS COMPLETE!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
