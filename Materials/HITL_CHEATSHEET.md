# Production HITL (Human-in-the-Loop) Cheatsheet

## The Pattern

```
Request 1: "Delete important.txt"
─────────────────────────────────────────────────
Frontend ──► Backend ──► Agent ──► Tool checks:
                                   "Is token confirmed?"
                                        │
                                       NO
                                        │
                         Create pending confirmation
                                        │
                         Return: { pending_confirmations: [...] }
                                        │
Frontend shows: ┌─────────────────────────────┐
                │ ⚠️ Confirm Delete?          │
                │ File: important.txt         │
                │ [Cancel]  [Confirm]         │
                └─────────────────────────────┘
                                        │
                              User clicks Confirm
                                        │
Request 2: Same message + confirmed_token
─────────────────────────────────────────────────
Frontend ──► Backend ──► Agent ──► Tool checks:
                                   "Is token confirmed?"
                                        │
                                       YES
                                        │
                                   EXECUTE!
                                        │
                         Return: { status: "success" }
```

## Key Components

### 1. Context with Confirmation State

```python
@dataclass
class UserContext:
    user_id: str
    confirmed_tokens: list[str] = field(default_factory=list)
    pending_confirmations: list[dict] = field(default_factory=list)
```

### 2. Tool with Confirmation Check

```python
@function_tool
async def delete_file(
    context: RunContextWrapper[UserContext],
    filename: str
) -> str:
    ctx = context.context
    
    # Check for confirmed token
    for token in ctx.confirmed_tokens:
        if is_valid_token(token, "delete_file"):
            consume_token(token)
            return f"✅ Deleted {filename}"
    
    # Not confirmed - create pending
    token = create_pending_confirmation(
        user_id=ctx.user_id,
        tool="delete_file",
        args={"filename": filename},
    )
    
    ctx.pending_confirmations.append({
        "token": token,
        "description": f"Delete {filename}?",
    })
    
    return f"⏳ Needs confirmation to delete {filename}"
```

### 3. API Response with Pending Confirmations

```python
@app.post("/chat")
async def chat(request: ChatRequest):
    ctx = UserContext(
        user_id=request.user_id,
        confirmed_tokens=request.confirmed_tokens,  # From frontend
    )
    
    result = await Runner.run(agent, request.message, context=ctx)
    
    if ctx.pending_confirmations:
        return {
            "status": "confirmation_required",
            "message": result.final_output,
            "pending_confirmations": ctx.pending_confirmations,
        }
    
    return {"status": "success", "message": result.final_output}
```

### 4. Frontend Flow

```javascript
// Send message
const response = await fetch('/chat', {
  method: 'POST',
  body: JSON.stringify({
    message: userMessage,
    user_id: userId,
    confirmed_tokens: confirmedTokens,  // Previously confirmed
  }),
});

const data = await response.json();

if (data.status === 'confirmation_required') {
  // Show confirmation modal
  showModal(data.pending_confirmations);
} else {
  // Show response
  displayMessage(data.message);
}

// When user confirms
async function onConfirm(token) {
  await fetch('/confirm', { body: JSON.stringify({ token }) });
  
  // Retry with confirmed token
  confirmedTokens.push(token);
  sendMessage(originalMessage);  // Retry!
}
```

## For MCP Tools

Same pattern - wrap MCP calls in a function tool that checks confirmation:

```python
@function_tool
async def safe_mcp_call(
    context: RunContextWrapper[UserContext],
    tool_name: str,
    arguments: dict
) -> str:
    ctx = context.context
    
    if tool_name in SENSITIVE_MCP_TOOLS:
        # Check confirmation
        for token in ctx.confirmed_tokens:
            if is_valid(token, tool_name):
                # Execute MCP tool
                return await mcp_server.call_tool(tool_name, arguments)
        
        # Need confirmation
        token = create_pending(tool_name, arguments)
        ctx.pending_confirmations.append(...)
        return "⏳ Needs confirmation"
    
    # Safe tool - execute directly
    return await mcp_server.call_tool(tool_name, arguments)
```

## Token Storage (Production)

```python
# Use Redis for token storage
import redis

r = redis.Redis()

def create_confirmation(user_id, tool, args, ttl=300):
    token = str(uuid.uuid4())
    r.setex(
        f"confirm:{token}",
        ttl,
        json.dumps({"user_id": user_id, "tool": tool, "args": args})
    )
    return token

def confirm_token(token, user_id):
    data = r.get(f"confirm:{token}")
    if data:
        info = json.loads(data)
        if info["user_id"] == user_id:
            r.delete(f"confirm:{token}")
            r.setex(f"confirmed:{token}", 60, "1")  # Valid for 1 min
            return True
    return False

def is_confirmed(token):
    return r.exists(f"confirmed:{token}")
```

## Summary

| Component | Purpose |
|-----------|---------|
| `UserContext` | Carry confirmation state through agent run |
| `confirmed_tokens` | Tokens user has approved (from frontend) |
| `pending_confirmations` | Actions waiting for approval |
| Token Store (Redis) | Persist tokens across requests |
| `/confirm` endpoint | Mark token as confirmed |
| Frontend modal | Show confirmation UI |

## vs CLI Demo Patterns

| CLI Demo | Production |
|----------|------------|
| `input("y/n")` | Frontend modal + token |
| `raise Exception` | Return pending confirmations |
| Blocking | Async, multi-request |
| Single process | Distributed (Redis) |
