"""
=============================================================================
PRODUCTION-READY HUMAN-IN-THE-LOOP (HITL)
=============================================================================

Real implementation for web apps with:
- FastAPI backend
- Non-blocking confirmation flow
- Token-based confirmation
- Works with both regular tools AND MCP tools
"""

import asyncio
import uuid
import time
from dataclasses import dataclass, field
from typing import Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agents import Agent, Runner, function_tool, RunContextWrapper
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# CONFIRMATION STORE (Use Redis in production)
# =============================================================================

class PendingConfirmation(BaseModel):
    """A pending confirmation request."""
    token: str
    action: str
    tool_name: str
    arguments: dict
    description: str
    created_at: float
    expires_at: float
    user_id: str


# In production, use Redis or database
PENDING_CONFIRMATIONS: dict[str, PendingConfirmation] = {}
CONFIRMED_TOKENS: set[str] = set()


def create_confirmation(
    user_id: str,
    tool_name: str,
    arguments: dict,
    description: str,
    ttl_seconds: int = 300  # 5 minutes
) -> PendingConfirmation:
    """Create a pending confirmation."""
    token = str(uuid.uuid4())
    now = time.time()
    
    confirmation = PendingConfirmation(
        token=token,
        action=f"{tool_name}_{token[:8]}",
        tool_name=tool_name,
        arguments=arguments,
        description=description,
        created_at=now,
        expires_at=now + ttl_seconds,
        user_id=user_id,
    )
    
    PENDING_CONFIRMATIONS[token] = confirmation
    return confirmation


def confirm_token(token: str, user_id: str) -> bool:
    """Confirm a pending action."""
    if token not in PENDING_CONFIRMATIONS:
        return False
    
    confirmation = PENDING_CONFIRMATIONS[token]
    
    # Check ownership
    if confirmation.user_id != user_id:
        return False
    
    # Check expiry
    if time.time() > confirmation.expires_at:
        del PENDING_CONFIRMATIONS[token]
        return False
    
    # Mark as confirmed
    CONFIRMED_TOKENS.add(token)
    return True


def is_confirmed(token: str) -> bool:
    """Check if a token is confirmed."""
    return token in CONFIRMED_TOKENS


def consume_confirmation(token: str) -> Optional[PendingConfirmation]:
    """Consume a confirmed token (one-time use)."""
    if token in CONFIRMED_TOKENS:
        CONFIRMED_TOKENS.remove(token)
        if token in PENDING_CONFIRMATIONS:
            confirmation = PENDING_CONFIRMATIONS.pop(token)
            return confirmation
    return None


# =============================================================================
# CONTEXT WITH CONFIRMATION STATE
# =============================================================================

@dataclass
class UserContext:
    """Context passed through the agent run."""
    user_id: str
    session_id: str
    confirmed_tokens: list[str] = field(default_factory=list)
    pending_confirmations: list[PendingConfirmation] = field(default_factory=list)
    

# =============================================================================
# TOOLS WITH CONFIRMATION LOGIC
# =============================================================================

# Define which tools need confirmation
TOOLS_REQUIRING_CONFIRMATION = {
    "delete_file": "Delete a file permanently",
    "send_email": "Send an email on your behalf", 
    "make_payment": "Make a payment from your account",
    "delete_user_data": "Delete user data permanently",
    "execute_sql": "Execute SQL query on database",
}


class ConfirmationRequired(Exception):
    """Raised when a tool needs confirmation."""
    def __init__(self, confirmation: PendingConfirmation):
        self.confirmation = confirmation
        super().__init__(f"Confirmation required: {confirmation.description}")


@function_tool
async def delete_file(
    context: RunContextWrapper[UserContext],
    filename: str
) -> str:
    """Delete a file permanently."""
    
    ctx = context.context
    tool_name = "delete_file"
    
    # Check if we have a confirmed token for this action
    for token in ctx.confirmed_tokens:
        confirmation = consume_confirmation(token)
        if confirmation and confirmation.tool_name == tool_name:
            # Token valid - execute!
            return f"✅ File '{filename}' deleted successfully"
    
    # No confirmation - create pending request
    confirmation = create_confirmation(
        user_id=ctx.user_id,
        tool_name=tool_name,
        arguments={"filename": filename},
        description=f"Delete file: {filename}",
    )
    
    ctx.pending_confirmations.append(confirmation)
    
    # Return message (don't raise - let agent respond naturally)
    return f"⏳ CONFIRMATION_REQUIRED: Delete '{filename}'? [token:{confirmation.token}]"


@function_tool
async def send_email(
    context: RunContextWrapper[UserContext],
    to: str,
    subject: str,
    body: str
) -> str:
    """Send an email."""
    
    ctx = context.context
    tool_name = "send_email"
    
    for token in ctx.confirmed_tokens:
        confirmation = consume_confirmation(token)
        if confirmation and confirmation.tool_name == tool_name:
            return f"✅ Email sent to {to}"
    
    confirmation = create_confirmation(
        user_id=ctx.user_id,
        tool_name=tool_name,
        arguments={"to": to, "subject": subject, "body": body},
        description=f"Send email to {to}: {subject}",
    )
    
    ctx.pending_confirmations.append(confirmation)
    return f"⏳ CONFIRMATION_REQUIRED: Send email to {to}? [token:{confirmation.token}]"


@function_tool
async def read_file(
    context: RunContextWrapper[UserContext],
    filename: str
) -> str:
    """Read a file (no confirmation needed)."""
    return f"Contents of {filename}: Hello World!"


@function_tool
async def list_files(
    context: RunContextWrapper[UserContext],
    directory: str
) -> str:
    """List files in directory (no confirmation needed)."""
    return f"Files in {directory}: file1.txt, file2.txt, file3.txt"


# =============================================================================
# AGENT
# =============================================================================

file_agent = Agent(
    name="FileManager",
    instructions="""You help users manage files.

When a tool returns CONFIRMATION_REQUIRED:
- Tell the user what action needs confirmation
- Let them know they need to approve it
- Don't pretend the action was completed

When a tool succeeds (✅):
- Confirm the action was completed""",
    tools=[delete_file, send_email, read_file, list_files],
)


# =============================================================================
# API MODELS
# =============================================================================

class ChatRequest(BaseModel):
    message: str
    user_id: str
    session_id: str
    confirmed_tokens: list[str] = []  # Tokens user has confirmed


class ConfirmationInfo(BaseModel):
    token: str
    tool_name: str
    description: str
    arguments: dict


class ChatResponse(BaseModel):
    status: str  # "success" | "confirmation_required"
    message: str
    pending_confirmations: list[ConfirmationInfo] = []


class ConfirmRequest(BaseModel):
    token: str
    user_id: str


class ConfirmResponse(BaseModel):
    success: bool
    message: str


# =============================================================================
# API ENDPOINTS
# =============================================================================

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main chat endpoint."""
    
    # Create context with any confirmed tokens
    ctx = UserContext(
        user_id=request.user_id,
        session_id=request.session_id,
        confirmed_tokens=request.confirmed_tokens,
    )
    
    # Run agent
    result = await Runner.run(
        file_agent,
        request.message,
        context=ctx,
    )
    
    # Check for pending confirmations
    if ctx.pending_confirmations:
        return ChatResponse(
            status="confirmation_required",
            message=result.final_output,
            pending_confirmations=[
                ConfirmationInfo(
                    token=c.token,
                    tool_name=c.tool_name,
                    description=c.description,
                    arguments=c.arguments,
                )
                for c in ctx.pending_confirmations
            ],
        )
    
    return ChatResponse(
        status="success",
        message=result.final_output,
    )


@app.post("/confirm", response_model=ConfirmResponse)
async def confirm_action(request: ConfirmRequest):
    """Confirm a pending action."""
    
    success = confirm_token(request.token, request.user_id)
    
    if success:
        return ConfirmResponse(
            success=True,
            message="Action confirmed. You can now retry your request.",
        )
    else:
        return ConfirmResponse(
            success=False,
            message="Invalid or expired confirmation token.",
        )


@app.get("/pending/{user_id}")
async def get_pending(user_id: str):
    """Get pending confirmations for a user."""
    
    pending = [
        ConfirmationInfo(
            token=c.token,
            tool_name=c.tool_name,
            description=c.description,
            arguments=c.arguments,
        )
        for c in PENDING_CONFIRMATIONS.values()
        if c.user_id == user_id and time.time() < c.expires_at
    ]
    
    return {"pending": pending}


# =============================================================================
# FRONTEND EXAMPLE (React)
# =============================================================================

FRONTEND_EXAMPLE = """
// React Component for Chat with Confirmation

import React, { useState } from 'react';

function ChatWithConfirmation() {
  const [message, setMessage] = useState('');
  const [response, setResponse] = useState(null);
  const [pendingConfirmations, setPendingConfirmations] = useState([]);
  const [confirmedTokens, setConfirmedTokens] = useState([]);
  
  const userId = 'user_123';
  const sessionId = 'session_456';
  
  const sendMessage = async (text, tokens = []) => {
    const res = await fetch('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: text,
        user_id: userId,
        session_id: sessionId,
        confirmed_tokens: tokens,
      }),
    });
    
    const data = await res.json();
    setResponse(data);
    
    if (data.status === 'confirmation_required') {
      setPendingConfirmations(data.pending_confirmations);
    } else {
      setPendingConfirmations([]);
    }
  };
  
  const confirmAction = async (token) => {
    // Call confirm endpoint
    await fetch('/confirm', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token, user_id: userId }),
    });
    
    // Add to confirmed tokens and retry
    const newTokens = [...confirmedTokens, token];
    setConfirmedTokens(newTokens);
    
    // Retry the original message with confirmation
    await sendMessage(message, newTokens);
  };
  
  const rejectAction = (token) => {
    setPendingConfirmations(prev => 
      prev.filter(c => c.token !== token)
    );
    setResponse({ message: 'Action cancelled.' });
  };
  
  return (
    <div>
      <input
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        placeholder="Type a message..."
      />
      <button onClick={() => sendMessage(message)}>Send</button>
      
      {response && (
        <div className="response">
          {response.message}
        </div>
      )}
      
      {/* Confirmation Modal */}
      {pendingConfirmations.map(confirmation => (
        <div key={confirmation.token} className="modal">
          <h3>⚠️ Confirmation Required</h3>
          <p>{confirmation.description}</p>
          <p>Tool: {confirmation.tool_name}</p>
          <pre>{JSON.stringify(confirmation.arguments, null, 2)}</pre>
          <button onClick={() => confirmAction(confirmation.token)}>
            ✅ Confirm
          </button>
          <button onClick={() => rejectAction(confirmation.token)}>
            ❌ Cancel
          </button>
        </div>
      ))}
    </div>
  );
}
"""


# =============================================================================
# MCP TOOL CONFIRMATION (Same Pattern)
# =============================================================================

MCP_EXAMPLE = """
# For MCP tools, use the same pattern!

from agents import Agent
from agents.mcp import MCPServerStdio

async def create_mcp_agent_with_confirmation():
    
    # MCP Server
    mcp_server = MCPServerStdio(
        name="DatabaseMCP",
        command="python",
        args=["mcp_server.py"],
    )
    
    # Wrap MCP tools that need confirmation
    MCP_TOOLS_REQUIRING_CONFIRMATION = {
        "delete_record",
        "drop_table", 
        "execute_sql",
        "send_notification",
    }
    
    async with mcp_server:
        # Get original tools
        original_tools = await mcp_server.list_tools()
        
        # The key: Your regular function tools handle confirmation
        # MCP tools just execute - you gate them with a wrapper tool
        
        @function_tool
        async def safe_mcp_execute(
            context: RunContextWrapper[UserContext],
            tool_name: str,
            arguments: str  # JSON string
        ) -> str:
            '''Execute an MCP tool with confirmation if needed.'''
            
            import json
            args = json.loads(arguments)
            ctx = context.context
            
            # Check if this MCP tool needs confirmation
            if tool_name in MCP_TOOLS_REQUIRING_CONFIRMATION:
                
                # Check for confirmed token
                for token in ctx.confirmed_tokens:
                    confirmation = consume_confirmation(token)
                    if confirmation and confirmation.tool_name == f"mcp_{tool_name}":
                        # Execute MCP tool
                        result = await mcp_server.call_tool(tool_name, args)
                        return f"✅ {result}"
                
                # Need confirmation
                confirmation = create_confirmation(
                    user_id=ctx.user_id,
                    tool_name=f"mcp_{tool_name}",
                    arguments=args,
                    description=f"Execute MCP tool: {tool_name}",
                )
                ctx.pending_confirmations.append(confirmation)
                return f"⏳ CONFIRMATION_REQUIRED: {tool_name}? [token:{confirmation.token}]"
            
            else:
                # Safe tool - execute directly
                result = await mcp_server.call_tool(tool_name, args)
                return str(result)
        
        
        agent = Agent(
            name="MCPAgent",
            instructions='''You can execute MCP tools via safe_mcp_execute.
            Available MCP tools: delete_record, query_database, etc.
            Some tools require confirmation.''',
            tools=[safe_mcp_execute],  # Wrapper handles confirmation
            mcp_servers=[mcp_server],  # Or use directly for safe tools
        )
        
        return agent
"""


# =============================================================================
# RUN SERVER
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print("=" * 60)
    print("Production HITL Server")
    print("=" * 60)
    print("\nEndpoints:")
    print("  POST /chat     - Send message")
    print("  POST /confirm  - Confirm pending action")
    print("  GET /pending   - Get pending confirmations")
    print("\n" + "=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
