# 🚀 OpenAI Agents SDK - Streaming Cheat Sheet

## Quick Start

```python
from agents import Agent, Runner

agent = Agent(name="Bot", instructions="Be helpful")

# NON-STREAMING (waits for full response)
result = await Runner.run(agent, input="Hello")
print(result.final_output)

# STREAMING (real-time tokens)
result = Runner.run_streamed(agent, input="Hello")
async for event in result.stream_events():
    if event.type == "raw_response_event":
        # Process tokens as they arrive
        pass
```

---

## Stream Event Types

| Event Type | When It Fires | What It Contains |
|------------|---------------|------------------|
| `raw_response_event` | New token(s) received | Raw API response with delta content |
| `agent_updated_event` | Agent state changed | Current agent reference |
| `run_item_created` | New item started | Item type (message, tool_call, handoff) |
| `run_item_updated` | Item modified | Updated item data |
| `run_item_completed` | Item finished | Final item data |

---

## Extract Tokens

```python
def extract_text(event) -> str:
    """Extract text from raw_response_event."""
    try:
        data = event.data
        if hasattr(data, 'delta') and hasattr(data.delta, 'content'):
            return data.delta.content or ""
        return ""
    except:
        return ""

# Usage
async for event in result.stream_events():
    if event.type == "raw_response_event":
        text = extract_text(event)
        if text:
            print(text, end="", flush=True)
```

---

## Streaming with Tools

```python
@function_tool
def get_weather(city: str) -> str:
    return f"Weather in {city}: Sunny, 22°C"

agent = Agent(
    name="WeatherBot",
    tools=[get_weather],
    model="gpt-4o-mini"
)

result = Runner.run_streamed(agent, input="Weather in Tokyo?")

async for event in result.stream_events():
    if event.type == "raw_response_event":
        text = extract_text(event)
        print(text, end="", flush=True)
        
    elif event.type == "run_item_created":
        if getattr(event.item, 'type', '') == "tool_call":
            print(f"\n🔧 Calling tool: {event.item.name}")
            
    elif event.type == "run_item_completed":
        if getattr(event.item, 'type', '') == "tool_result":
            print(f"📤 Result: {event.item.output}")
```

---

## Streaming with Handoffs

```python
agent_a = Agent(name="AgentA", handoffs=[agent_b])

result = Runner.run_streamed(agent_a, input="Help me")
current_agent = "AgentA"

async for event in result.stream_events():
    if event.type == "agent_updated_event":
        new_agent = event.agent.name
        if new_agent != current_agent:
            print(f"\n🔀 Handoff: {current_agent} → {new_agent}")
            current_agent = new_agent
    
    elif event.type == "raw_response_event":
        print(extract_text(event), end="", flush=True)
```

---

## FastAPI Integration

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import json

app = FastAPI()

async def stream_generator(agent, messages):
    result = Runner.run_streamed(agent, input=messages)
    
    async for event in result.stream_events():
        if event.type == "raw_response_event":
            text = extract_text(event)
            if text:
                yield f"data: {json.dumps({'type': 'token', 'content': text})}\n\n"
    
    yield f"data: {json.dumps({'type': 'done'})}\n\n"

@app.post("/chat/stream")
async def chat_stream(message: str):
    return StreamingResponse(
        stream_generator(agent, [{"role": "user", "content": message}]),
        media_type="text/event-stream"
    )
```

---

## Frontend (JavaScript)

```javascript
async function streamChat(message, onToken) {
    const response = await fetch('/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message })
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const lines = decoder.decode(value).split('\n\n');
        for (const line of lines) {
            if (line.startsWith('data: ')) {
                const data = JSON.parse(line.slice(6));
                if (data.type === 'token') {
                    onToken(data.content);
                }
            }
        }
    }
}

// Usage
streamChat("Hello!", (token) => {
    document.getElementById('output').textContent += token;
});
```

---

## Stream Handler Class

```python
class StreamHandler:
    def __init__(self):
        self.tokens = []
        self.tools = []
        
    async def process(self, agent, input_text):
        result = Runner.run_streamed(agent, input=input_text)
        
        async for event in result.stream_events():
            yield await self.handle_event(event)
    
    async def handle_event(self, event):
        if event.type == "raw_response_event":
            text = extract_text(event)
            if text:
                self.tokens.append(text)
                return {"type": "token", "content": text}
                
        elif event.type == "run_item_created":
            if getattr(event.item, 'type', '') == "tool_call":
                self.tools.append(event.item.name)
                return {"type": "tool_start", "name": event.item.name}
        
        return None
    
    def get_response(self) -> str:
        return "".join(self.tokens)
```

---

## Progress Tracking

```python
import asyncio

async def stream_with_progress(agent, input_text):
    result = Runner.run_streamed(agent, input=input_text)
    
    token_count = 0
    start = asyncio.get_event_loop().time()
    
    async for event in result.stream_events():
        if event.type == "raw_response_event":
            text = extract_text(event)
            if text:
                token_count += 1
                print(text, end="", flush=True)
    
    elapsed = asyncio.get_event_loop().time() - start
    print(f"\n\n📊 {token_count} tokens in {elapsed:.2f}s ({token_count/elapsed:.1f} t/s)")
```

---

## Common Patterns

### 1. Collect Full Response

```python
async def get_full_response(agent, message):
    result = Runner.run_streamed(agent, input=message)
    tokens = []
    
    async for event in result.stream_events():
        if event.type == "raw_response_event":
            text = extract_text(event)
            if text:
                tokens.append(text)
    
    return "".join(tokens)
```

### 2. Stream to UI Callback

```python
async def stream_to_callback(agent, message, on_token):
    result = Runner.run_streamed(agent, input=message)
    
    async for event in result.stream_events():
        if event.type == "raw_response_event":
            text = extract_text(event)
            if text:
                await on_token(text)  # Call UI update
```

### 3. Timeout Handling

```python
async def stream_with_timeout(agent, message, timeout=30):
    result = Runner.run_streamed(agent, input=message)
    
    try:
        async for event in asyncio.wait_for(
            result.stream_events().__aiter__().__anext__(),
            timeout=timeout
        ):
            # Process event
            pass
    except asyncio.TimeoutError:
        print("⏰ Stream timeout!")
```

---

## Key Points

1. **Use `run_streamed()`** instead of `run()` for streaming
2. **`raw_response_event`** contains the actual tokens
3. **Always use `flush=True`** when printing tokens
4. **Tool calls** fire `run_item_created` → `run_item_completed`
5. **Handoffs** trigger `agent_updated_event`
6. **SSE format** for web: `data: {json}\n\n`
7. **Collect all tokens** by appending to a list

---

## Files in This Guide

| File | Description |
|------|-------------|
| `01_streaming_basics.py` | Basic streaming, event types, token extraction |
| `02_streaming_with_tools.py` | Tools, multi-tool, event handling |
| `03_streaming_handoffs.py` | Handoffs, multi-agent, tracking |
| `04_fastapi_streaming.py` | FastAPI integration, SSE, NDJSON |
| `05_frontend_client.js` | JavaScript client, React hook, HTML |

---

## Run Examples

```bash
# Install dependencies
pip install openai-agents fastapi uvicorn

# Run basic examples
python 01_streaming_basics.py

# Run FastAPI server
python 04_fastapi_streaming.py
# Then open http://localhost:8000/docs
```
