"""
🏭 PRODUCTION EXAMPLE: Customer Support Agent
==============================================

This demonstrates a real-world pattern combining:
- Context: User data, permissions, API clients
- Sessions: Conversation history
- State: Ticket tracking, action logging

Run: python production_support_agent.py
"""

import asyncio
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from enum import Enum

from openai import AsyncOpenAI
from agents import (
    Agent, Runner, RunConfig,
    OpenAIChatCompletionsModel,
    function_tool,
    RunContextWrapper,
    SQLiteSession,
)


# ============================================
# CONFIGURATION
# ============================================

client = AsyncOpenAI(
    api_key=os.getenv("OLLAMA_API_KEY", "ollama"),
    base_url="http://localhost:11434/v1"
)

def create_model():
    return OpenAIChatCompletionsModel(
        model="mistral:7b",
        openai_client=client
    )

config = RunConfig(tracing_disabled=True)


# ============================================
# DOMAIN MODELS
# ============================================

class TicketPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TicketStatus(Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


@dataclass
class Ticket:
    id: str
    title: str
    description: str
    priority: TicketPriority
    status: TicketStatus
    created_at: datetime
    

@dataclass
class CustomerContext:
    """
    Production context containing:
    - User identity and permissions
    - Current state (active ticket, actions taken)
    - Simulated dependencies (would be real services in production)
    """
    # Identity
    customer_id: str
    customer_name: str
    email: str
    
    # Account info
    subscription_tier: str  # "free", "pro", "enterprise"
    account_created: datetime
    
    # Current support state
    active_ticket: Optional[Ticket] = None
    
    # Action tracking (mutable state)
    actions_taken: List[str] = field(default_factory=list)
    escalation_requested: bool = False
    
    # Simulated services (in production, these would be real clients)
    # db: DatabaseClient = None
    # email_service: EmailClient = None
    # slack_notifier: SlackClient = None
    
    def log_action(self, action: str):
        """Log an action with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.actions_taken.append(f"[{timestamp}] {action}")
    
    def get_priority_sla(self) -> str:
        """Get SLA based on subscription tier"""
        slas = {
            "free": "48 hours",
            "pro": "24 hours", 
            "enterprise": "4 hours"
        }
        return slas.get(self.subscription_tier, "48 hours")


# ============================================
# TOOLS
# ============================================

@function_tool
async def get_customer_info(ctx: RunContextWrapper[CustomerContext]) -> str:
    """Get current customer's account information"""
    c = ctx.context
    c.log_action("Viewed account info")
    
    return f"""
📋 Customer Information:
━━━━━━━━━━━━━━━━━━━━━━━
• Name: {c.customer_name}
• Email: {c.email}
• Customer ID: {c.customer_id}
• Subscription: {c.subscription_tier.upper()}
• Member since: {c.account_created.strftime('%Y-%m-%d')}
• Support SLA: {c.get_priority_sla()}
"""


@function_tool
async def create_ticket(
    ctx: RunContextWrapper[CustomerContext],
    title: str,
    description: str,
    priority: str = "medium"
) -> str:
    """Create a new support ticket"""
    c = ctx.context
    
    # Validate priority
    try:
        ticket_priority = TicketPriority(priority.lower())
    except ValueError:
        return f"❌ Invalid priority. Use: low, medium, high, urgent"
    
    # Enterprise gets priority boost
    if c.subscription_tier == "enterprise" and ticket_priority == TicketPriority.MEDIUM:
        ticket_priority = TicketPriority.HIGH
    
    # Create ticket
    ticket = Ticket(
        id=f"TKT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        title=title,
        description=description,
        priority=ticket_priority,
        status=TicketStatus.OPEN,
        created_at=datetime.now()
    )
    
    c.active_ticket = ticket
    c.log_action(f"Created ticket {ticket.id}: {title}")
    
    return f"""
✅ Ticket Created Successfully!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Ticket ID: {ticket.id}
• Title: {ticket.title}
• Priority: {ticket.priority.value.upper()}
• Status: {ticket.status.value}
• SLA: {c.get_priority_sla()}

We'll get back to you within {c.get_priority_sla()}.
"""


@function_tool
async def get_ticket_status(ctx: RunContextWrapper[CustomerContext]) -> str:
    """Get status of the current active ticket"""
    c = ctx.context
    c.log_action("Checked ticket status")
    
    if not c.active_ticket:
        return "ℹ️ No active ticket found. Would you like to create one?"
    
    t = c.active_ticket
    return f"""
📋 Ticket Status:
━━━━━━━━━━━━━━━━
• ID: {t.id}
• Title: {t.title}
• Priority: {t.priority.value.upper()}
• Status: {t.status.value.replace('_', ' ').title()}
• Created: {t.created_at.strftime('%Y-%m-%d %H:%M')}
"""


@function_tool
async def update_ticket_priority(
    ctx: RunContextWrapper[CustomerContext],
    new_priority: str
) -> str:
    """Update the priority of the active ticket"""
    c = ctx.context
    
    if not c.active_ticket:
        return "❌ No active ticket to update."
    
    try:
        priority = TicketPriority(new_priority.lower())
    except ValueError:
        return f"❌ Invalid priority. Use: low, medium, high, urgent"
    
    old_priority = c.active_ticket.priority
    c.active_ticket.priority = priority
    c.log_action(f"Updated priority: {old_priority.value} → {priority.value}")
    
    return f"✅ Ticket priority updated to {priority.value.upper()}"


@function_tool
async def escalate_to_human(
    ctx: RunContextWrapper[CustomerContext],
    reason: str
) -> str:
    """Escalate the conversation to a human support agent"""
    c = ctx.context
    c.escalation_requested = True
    c.log_action(f"Escalation requested: {reason}")
    
    # In production: notify support team via Slack, email, etc.
    
    return f"""
🔔 Escalation Requested
━━━━━━━━━━━━━━━━━━━━━━
Your request has been escalated to our support team.

Reason: {reason}
Customer: {c.customer_name} ({c.subscription_tier})
Priority: {"HIGH" if c.subscription_tier == "enterprise" else "NORMAL"}

A human agent will contact you shortly at {c.email}.
"""


@function_tool
async def check_known_issues(
    ctx: RunContextWrapper[CustomerContext],
    keywords: str
) -> str:
    """Search for known issues matching keywords"""
    c = ctx.context
    c.log_action(f"Searched known issues: {keywords}")
    
    # Simulated knowledge base
    known_issues = {
        "login": "🔧 Login issues: Try clearing browser cache and cookies. If using SSO, ensure your identity provider is working.",
        "slow": "🔧 Performance issues: We're aware of slowness affecting some users. Our team is actively working on it.",
        "payment": "🔧 Payment issues: Verify your card details. Contact billing@example.com for refunds.",
        "api": "🔧 API issues: Check status.example.com for any outages. Ensure your API key is valid.",
    }
    
    for key, solution in known_issues.items():
        if key in keywords.lower():
            return solution
    
    return "ℹ️ No known issues found matching your description. Let me create a ticket for you."


@function_tool
async def get_session_summary(ctx: RunContextWrapper[CustomerContext]) -> str:
    """Get a summary of actions taken in this support session"""
    c = ctx.context
    
    if not c.actions_taken:
        return "No actions recorded in this session yet."
    
    summary = "📊 Session Summary:\n" + "━" * 30 + "\n"
    for action in c.actions_taken:
        summary += f"• {action}\n"
    
    if c.active_ticket:
        summary += f"\n🎫 Active Ticket: {c.active_ticket.id}"
    
    if c.escalation_requested:
        summary += "\n⚠️ Escalation has been requested"
    
    return summary


# ============================================
# AGENT SETUP
# ============================================

def create_support_agent() -> Agent[CustomerContext]:
    """Create the customer support agent"""
    
    return Agent[CustomerContext](
        name="SupportBot",
        instructions="""You are a helpful customer support agent for TechCorp.

Your capabilities:
1. Look up customer information
2. Search for known issues
3. Create and manage support tickets
4. Escalate to human agents when needed

Guidelines:
- Always greet the customer by name
- Check for known issues before creating tickets
- For billing/refund requests, always escalate to human
- Enterprise customers get priority support
- Be empathetic and professional

Remember the conversation context across messages.""",
        model=create_model(),
        tools=[
            get_customer_info,
            check_known_issues,
            create_ticket,
            get_ticket_status,
            update_ticket_priority,
            escalate_to_human,
            get_session_summary,
        ],
    )


# ============================================
# MAIN APPLICATION
# ============================================

async def support_session(customer_id: str, customer_name: str, tier: str = "pro"):
    """Run an interactive support session"""
    
    # Create customer context
    context = CustomerContext(
        customer_id=customer_id,
        customer_name=customer_name,
        email=f"{customer_name.lower()}@example.com",
        subscription_tier=tier,
        account_created=datetime(2023, 1, 15),
    )
    
    # Create session for conversation history
    session = SQLiteSession(
        session_id=f"support_{customer_id}",
        db_path="support_conversations.db"
    )
    
    # Create agent
    agent = create_support_agent()
    
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║  🎧 TechCorp Customer Support                                 ║
╠══════════════════════════════════════════════════════════════╣
║  Customer: {customer_name:<20} Tier: {tier.upper():<15}     ║
║  Session ID: support_{customer_id:<36}  ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    print("Type 'quit' to end session, 'summary' to see session summary.\n")
    
    while True:
        try:
            user_input = input("👤 You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() == 'quit':
                # Show final summary
                print("\n📊 Final Session Summary:")
                print("-" * 40)
                for action in context.actions_taken:
                    print(f"  {action}")
                if context.active_ticket:
                    print(f"\n  🎫 Ticket: {context.active_ticket.id}")
                print("\n👋 Thank you for contacting TechCorp Support!")
                break
            
            if user_input.lower() == 'summary':
                print("\n📊 Current Session:")
                for action in context.actions_taken:
                    print(f"  {action}")
                print()
                continue
            
            # Run agent
            result = await Runner.run(
                agent,
                user_input,
                context=context,
                session=session,
                run_config=config,
            )
            
            print(f"\n🤖 Support: {result.final_output}\n")
            
        except KeyboardInterrupt:
            print("\n\n👋 Session ended. Goodbye!")
            break


async def demo_mode():
    """Run a scripted demo"""
    
    print("""
╔══════════════════════════════════════════════════════════════╗
║  🎧 TechCorp Customer Support - DEMO MODE                     ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Create context
    context = CustomerContext(
        customer_id="cust_001",
        customer_name="Dhruv",
        email="dhruv@example.com",
        subscription_tier="enterprise",
        account_created=datetime(2023, 1, 15),
    )
    
    # Create session
    session = SQLiteSession("demo_session")
    
    # Create agent
    agent = create_support_agent()
    
    # Demo conversation
    demo_messages = [
        "Hi, I'm having trouble logging into my account",
        "I already tried that. Can you create a ticket for me?",
        "What's the status of my ticket?",
        "Actually, this is urgent. Can you escalate it?",
        "Give me a summary of what we did",
    ]
    
    for msg in demo_messages:
        print(f"\n👤 Customer: {msg}")
        
        result = await Runner.run(
            agent,
            msg,
            context=context,
            session=session,
            run_config=config,
        )
        
        print(f"\n🤖 Support: {result.final_output}")
        print("-" * 60)
        
        await asyncio.sleep(1)  # Pause for readability
    
    # Final summary
    print("\n" + "=" * 60)
    print("📊 DEMO SESSION COMPLETE")
    print("=" * 60)
    print("\n📋 Actions Taken:")
    for action in context.actions_taken:
        print(f"  {action}")
    print(f"\n🎫 Active Ticket: {context.active_ticket.id if context.active_ticket else 'None'}")
    print(f"⚠️ Escalation: {'Yes' if context.escalation_requested else 'No'}")


async def main():
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        await demo_mode()
    else:
        # Interactive mode
        await support_session(
            customer_id="cust_dhruv_001",
            customer_name="Dhruv",
            tier="enterprise"
        )


if __name__ == "__main__":
    asyncio.run(main())
