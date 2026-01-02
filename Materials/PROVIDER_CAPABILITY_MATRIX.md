# 🗂️ OpenAI Agents SDK: Provider & Model Capability Matrix

> **Last Updated:** December 2024  
> **SDK Version:** openai-agents 0.1.x

---

## ⚠️ Important Clarification

**Gemini DOES support tool calling!** Most providers support tool/function calling. The main differences are:

| Feature | Who Supports |
|---------|--------------|
| **Tool Calling** | Almost everyone (OpenAI, Gemini, Ollama, Groq, etc.) |
| **Web Search (Built-in)** | OpenAI ONLY |
| **File Search (Built-in)** | OpenAI ONLY |
| **Code Interpreter** | OpenAI ONLY |

---

## 📊 Master Capability Matrix

### Legend
- ✅ = Fully Supported
- ⚠️ = Partial / Model-dependent
- ❌ = Not Supported
- 🔸 = Requires specific model

---

## 1️⃣ OpenAI

| Model | API Type | Chat | Tools | Vision | Streaming | Structured | Web Search | File Search | Code Interpreter |
|-------|----------|------|-------|--------|-----------|------------|------------|-------------|------------------|
| `gpt-4o` | Responses | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `gpt-4o-mini` | Responses | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `gpt-4-turbo` | Responses | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `gpt-3.5-turbo` | Responses | ✅ | ✅ | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ |
| `o1` | Responses | ✅ | ⚠️ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ |
| `o1-mini` | Responses | ✅ | ⚠️ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |

**OpenAI Setup:**
```python
# Default - no special setup needed
from agents import Agent
agent = Agent(name="Bot", model="gpt-4o")
```

**Exclusive Features:**
- Web Search: `WebSearchTool()`
- File Search: `FileSearchTool()`
- Code Interpreter: `CodeInterpreterTool()`

---

## 2️⃣ Google Gemini

| Model | API Type | Chat | Tools | Vision | Streaming | Structured | Web Search | File Search | Code Interpreter |
|-------|----------|------|-------|--------|-----------|------------|------------|-------------|------------------|
| `gemini-2.0-flash` | Chat Completions | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| `gemini-2.0-flash-lite` | Chat Completions | ✅ | ✅ | ✅ | ✅ | ⚠️ | ❌ | ❌ | ❌ |
| `gemini-1.5-flash` | Chat Completions | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| `gemini-1.5-pro` | Chat Completions | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| `gemini-1.0-pro` | Chat Completions | ✅ | ✅ | ❌ | ✅ | ⚠️ | ❌ | ❌ | ❌ |

**Gemini Setup:**
```python
from openai import AsyncOpenAI
from agents import Agent, OpenAIChatCompletionsModel

client = AsyncOpenAI(
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    api_key=os.getenv("GEMINI_API_KEY"),
)

agent = Agent(
    name="Bot",
    model=OpenAIChatCompletionsModel(model="gemini-2.0-flash", openai_client=client),
)
```

**What Works:**
- ✅ Function/Tool calling (MCP servers work!)
- ✅ Multi-turn conversations
- ✅ Image input (vision models)
- ✅ Streaming responses
- ✅ JSON mode / structured output

**What Doesn't Work:**
- ❌ OpenAI's hosted tools (web_search, file_search, code_interpreter)
- ❌ Responses API features

---

## 3️⃣ Ollama (Local)

| Model | API Type | Chat | Tools | Vision | Streaming | Structured | Web Search | File Search | Code Interpreter |
|-------|----------|------|-------|--------|-----------|------------|------------|-------------|------------------|
| `llama3.2` | Chat Completions | ✅ | ✅ | ❌ | ✅ | ⚠️ | ❌ | ❌ | ❌ |
| `llama3.2-vision` | Chat Completions | ✅ | ✅ | ✅ | ✅ | ⚠️ | ❌ | ❌ | ❌ |
| `llama3.1:70b` | Chat Completions | ✅ | ✅ | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ |
| `mistral` | Chat Completions | ✅ | ✅ | ❌ | ✅ | ⚠️ | ❌ | ❌ | ❌ |
| `mixtral` | Chat Completions | ✅ | ✅ | ❌ | ✅ | ⚠️ | ❌ | ❌ | ❌ |
| `codellama` | Chat Completions | ✅ | ⚠️ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| `phi3` | Chat Completions | ✅ | ⚠️ | ❌ | ✅ | ⚠️ | ❌ | ❌ | ❌ |
| `qwen2.5` | Chat Completions | ✅ | ✅ | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ |
| `deepseek-r1` | Chat Completions | ✅ | ⚠️ | ❌ | ✅ | ⚠️ | ❌ | ❌ | ❌ |

**Ollama Setup:**
```python
from openai import AsyncOpenAI
from agents import Agent, OpenAIChatCompletionsModel

client = AsyncOpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama",  # Dummy key
)

agent = Agent(
    name="Bot",
    model=OpenAIChatCompletionsModel(model="llama3.2", openai_client=client),
)
```

**Notes:**
- Tool calling quality varies by model (Llama 3.1+ is best)
- Must have model downloaded: `ollama pull llama3.2`
- Runs 100% locally - good for privacy

---

## 4️⃣ Groq (Fast Cloud Inference)

| Model | API Type | Chat | Tools | Vision | Streaming | Structured | Web Search | File Search | Code Interpreter |
|-------|----------|------|-------|--------|-----------|------------|------------|-------------|------------------|
| `llama-3.3-70b-versatile` | Chat Completions | ✅ | ✅ | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ |
| `llama-3.1-8b-instant` | Chat Completions | ✅ | ✅ | ❌ | ✅ | ⚠️ | ❌ | ❌ | ❌ |
| `llama-3.2-90b-vision-preview` | Chat Completions | ✅ | ✅ | ✅ | ✅ | ⚠️ | ❌ | ❌ | ❌ |
| `mixtral-8x7b-32768` | Chat Completions | ✅ | ✅ | ❌ | ✅ | ⚠️ | ❌ | ❌ | ❌ |
| `gemma2-9b-it` | Chat Completions | ✅ | ⚠️ | ❌ | ✅ | ⚠️ | ❌ | ❌ | ❌ |

**Groq Setup:**
```python
from openai import AsyncOpenAI
from agents import Agent, OpenAIChatCompletionsModel

client = AsyncOpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.getenv("GROQ_API_KEY"),
)

agent = Agent(
    name="Bot",
    model=OpenAIChatCompletionsModel(model="llama-3.3-70b-versatile", openai_client=client),
)
```

**Why Groq:**
- Extremely fast inference (fastest in market)
- Free tier available
- Good for real-time applications

---

## 5️⃣ Together AI

| Model | API Type | Chat | Tools | Vision | Streaming | Structured | Web Search | File Search | Code Interpreter |
|-------|----------|------|-------|--------|-----------|------------|------------|-------------|------------------|
| `meta-llama/Llama-3.3-70B-Instruct-Turbo` | Chat Completions | ✅ | ✅ | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ |
| `meta-llama/Llama-3.2-11B-Vision-Instruct-Turbo` | Chat Completions | ✅ | ✅ | ✅ | ✅ | ⚠️ | ❌ | ❌ | ❌ |
| `mistralai/Mixtral-8x22B-Instruct-v0.1` | Chat Completions | ✅ | ✅ | ❌ | ✅ | ⚠️ | ❌ | ❌ | ❌ |
| `Qwen/Qwen2.5-72B-Instruct-Turbo` | Chat Completions | ✅ | ✅ | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ |
| `deepseek-ai/DeepSeek-R1` | Chat Completions | ✅ | ⚠️ | ❌ | ✅ | ⚠️ | ❌ | ❌ | ❌ |

**Together AI Setup:**
```python
from openai import AsyncOpenAI
from agents import Agent, OpenAIChatCompletionsModel

client = AsyncOpenAI(
    base_url="https://api.together.xyz/v1",
    api_key=os.getenv("TOGETHER_API_KEY"),
)

agent = Agent(
    name="Bot",
    model=OpenAIChatCompletionsModel(
        model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
        openai_client=client
    ),
)
```

---

## 6️⃣ Azure OpenAI

| Model | API Type | Chat | Tools | Vision | Streaming | Structured | Web Search | File Search | Code Interpreter |
|-------|----------|------|-------|--------|-----------|------------|------------|-------------|------------------|
| `gpt-4o` (deployment) | Chat Completions | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| `gpt-4o-mini` (deployment) | Chat Completions | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| `gpt-35-turbo` (deployment) | Chat Completions | ✅ | ✅ | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ |

**Azure Setup:**
```python
from openai import AsyncAzureOpenAI
from agents import Agent, OpenAIChatCompletionsModel

client = AsyncAzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-02-15-preview",
)

agent = Agent(
    name="Bot",
    model=OpenAIChatCompletionsModel(
        model="your-deployment-name",  # Not model name, deployment name!
        openai_client=client
    ),
)
```

**Notes:**
- Uses deployment names, not model names
- No Responses API (use Chat Completions)
- No hosted tools (web search, etc.)

---

## 7️⃣ Anthropic Claude (via OpenAI-compatible gateway)

| Model | API Type | Chat | Tools | Vision | Streaming | Structured | Web Search | File Search | Code Interpreter |
|-------|----------|------|-------|--------|-----------|------------|------------|-------------|------------------|
| `claude-sonnet-4-20250514` | Chat Completions | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| `claude-opus-4-20250514` | Chat Completions | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| `claude-haiku-4-20250514` | Chat Completions | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |

**Note:** Anthropic's native API is NOT OpenAI-compatible. You need:
- LiteLLM proxy, or
- OpenRouter, or
- Another gateway

**Via LiteLLM:**
```python
# Install: pip install "openai-agents[litellm]"
from agents import Agent

agent = Agent(
    name="Bot",
    model="litellm/anthropic/claude-sonnet-4-20250514",
)
```

---

## 8️⃣ OpenRouter (Multi-Provider Gateway)

| Model | API Type | Chat | Tools | Vision | Streaming | Structured |
|-------|----------|------|-------|--------|-----------|------------|
| `openai/gpt-4o` | Chat Completions | ✅ | ✅ | ✅ | ✅ | ✅ |
| `anthropic/claude-3.5-sonnet` | Chat Completions | ✅ | ✅ | ✅ | ✅ | ✅ |
| `google/gemini-2.0-flash` | Chat Completions | ✅ | ✅ | ✅ | ✅ | ✅ |
| `meta-llama/llama-3.3-70b` | Chat Completions | ✅ | ✅ | ❌ | ✅ | ⚠️ |

**OpenRouter Setup:**
```python
from openai import AsyncOpenAI
from agents import Agent, OpenAIChatCompletionsModel

client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

agent = Agent(
    name="Bot",
    model=OpenAIChatCompletionsModel(
        model="anthropic/claude-3.5-sonnet",  # Any model!
        openai_client=client
    ),
)
```

**Why OpenRouter:**
- Single API key for all providers
- Automatic fallbacks
- Pay per use

---

## 📋 Quick Decision Table

| I Need... | Use Provider | Model |
|-----------|--------------|-------|
| **Best overall** | OpenAI | `gpt-4o` |
| **Cheapest good quality** | Gemini | `gemini-2.0-flash` |
| **Fastest inference** | Groq | `llama-3.3-70b-versatile` |
| **100% Local/Private** | Ollama | `llama3.2` |
| **Web search built-in** | OpenAI | `gpt-4o` |
| **Code interpreter** | OpenAI | `gpt-4o` |
| **Vision + Tools** | Gemini | `gemini-2.0-flash` |
| **Enterprise/Compliance** | Azure | `gpt-4o` deployment |
| **Multi-provider flexibility** | OpenRouter | Any |

---

## 🔧 API Type Summary

| API Type | Providers | Use Case |
|----------|-----------|----------|
| **Responses API** | OpenAI only | Full features (web search, file search, code interpreter) |
| **Chat Completions** | Everyone else | Standard chat + tool calling |

**Code Pattern:**
```python
# OpenAI (Responses API) - Default
agent = Agent(model="gpt-4o")

# Everyone else (Chat Completions) - Explicit
agent = Agent(
    model=OpenAIChatCompletionsModel(model="...", openai_client=client)
)
```

---

## ❓ Common Confusions Clarified

### "Gemini doesn't support tool calling"
**FALSE!** Gemini fully supports tool calling. MCP servers work perfectly.

### "I need OpenAI for agents"
**FALSE!** Any provider with tool calling works for agents.

### "Chat Completions = No tools"
**FALSE!** Chat Completions API supports function/tool calling.

### "Responses API = Chat Completions"
**FALSE!** They're different APIs. Responses is OpenAI-exclusive with extra features.

---

## 🎯 What's ACTUALLY OpenAI-Exclusive

Only these features require OpenAI:

1. **Web Search Tool** - Built-in web browsing
2. **File Search Tool** - Built-in RAG/vector search
3. **Code Interpreter** - Built-in Python execution
4. **Responses API** - Stateful conversations with persistence

Everything else (chat, tools, vision, streaming) works with most providers!

---

## 📚 API Keys Reference

| Provider | Env Variable | Get Key |
|----------|--------------|---------|
| OpenAI | `OPENAI_API_KEY` | https://platform.openai.com/api-keys |
| Gemini | `GEMINI_API_KEY` | https://aistudio.google.com/apikey |
| Groq | `GROQ_API_KEY` | https://console.groq.com/keys |
| Together | `TOGETHER_API_KEY` | https://api.together.xyz/settings/api-keys |
| OpenRouter | `OPENROUTER_API_KEY` | https://openrouter.ai/keys |
| Anthropic | `ANTHROPIC_API_KEY` | https://console.anthropic.com/ |
| Azure | `AZURE_OPENAI_API_KEY` | Azure Portal |
| Ollama | None needed | Local installation |
