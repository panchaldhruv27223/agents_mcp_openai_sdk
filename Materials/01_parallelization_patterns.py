"""
=============================================================================
OPENAI AGENTS SDK - PARALLELIZATION PATTERNS
=============================================================================

Patterns covered:
1. asyncio.gather - Run multiple agents, wait for ALL
2. asyncio.as_completed - Process results as they finish
3. asyncio.TaskGroup - Better error handling (Python 3.11+)
4. Parallel with timeout - Don't wait forever
5. Parallel with streaming - Stream multiple agents
6. Fan-out/Fan-in - Multiple workers → Aggregator
7. Parallel different agents - Different tasks simultaneously
8. Conditional parallelization - Dynamic parallel execution
"""

import asyncio
from agents import Agent, Runner, ItemHelpers, trace
from dotenv import load_dotenv

load_dotenv()


# =============================================================================
# SETUP: Create agents for demos
# =============================================================================

spanish_agent = Agent(
    name="SpanishTranslator",
    instructions="Translate the user's message to Spanish. Be creative.",
)

french_agent = Agent(
    name="FrenchTranslator", 
    instructions="Translate the user's message to French. Be creative.",
)

german_agent = Agent(
    name="GermanTranslator",
    instructions="Translate the user's message to German. Be creative.",
)

picker_agent = Agent(
    name="TranslationPicker",
    instructions="Pick the best translation from the options and explain why.",
)

summarizer_agent = Agent(
    name="Summarizer",
    instructions="Summarize the given content concisely.",
)

critic_agent = Agent(
    name="Critic",
    instructions="Critique the given content. Find issues and suggest improvements.",
)

improver_agent = Agent(
    name="Improver",
    instructions="Improve the given content based on the critique.",
)


# =============================================================================
# PATTERN 1: asyncio.gather - Wait for ALL results
# =============================================================================

async def pattern_gather():
    """
    Basic pattern: Run multiple agents in parallel, wait for all.
    
    ┌─────────────────────────────────────────────────────────────┐
    │                    asyncio.gather                           │
    │                                                             │
    │    ┌──────────┐                                             │
    │    │ Agent 1  │────┐                                        │
    │    └──────────┘    │                                        │
    │                    │                                        │
    │    ┌──────────┐    ├───► Wait for ALL ───► [res1, res2, res3]
    │    │ Agent 2  │────┤                                        │
    │    └──────────┘    │                                        │
    │                    │                                        │
    │    ┌──────────┐    │                                        │
    │    │ Agent 3  │────┘                                        │
    │    └──────────┘                                             │
    │                                                             │
    └─────────────────────────────────────────────────────────────┘
    """
    print("=" * 60)
    print("PATTERN 1: asyncio.gather")
    print("=" * 60)
    
    msg = "Hello, my name is Dhruv."
    
    # Run 3 translations in parallel
    results = await asyncio.gather(
        Runner.run(spanish_agent, msg),
        Runner.run(french_agent, msg),
        Runner.run(german_agent, msg),
    )
    
    for i, res in enumerate(results):
        print(f"\nResult {i+1}: {res.final_output}")
    
    return results


# =============================================================================
# PATTERN 2: asyncio.as_completed - Process as they finish
# =============================================================================

async def pattern_as_completed():
    """
    Process results as soon as each agent finishes (not waiting for all).
    
    ┌─────────────────────────────────────────────────────────────┐
    │                  asyncio.as_completed                       │
    │                                                             │
    │    ┌──────────┐                                             │
    │    │ Agent 1  │──── (3 sec) ────► Process immediately      │
    │    └──────────┘                                             │
    │                                                             │
    │    ┌──────────┐                                             │
    │    │ Agent 2  │──── (1 sec) ────► Process FIRST! (fastest) │
    │    └──────────┘                                             │
    │                                                             │
    │    ┌──────────┐                                             │
    │    │ Agent 3  │──── (2 sec) ────► Process second           │
    │    └──────────┘                                             │
    │                                                             │
    └─────────────────────────────────────────────────────────────┘
    
    Good for: Showing results to user as they arrive
    """
    print("\n" + "=" * 60)
    print("PATTERN 2: asyncio.as_completed")
    print("=" * 60)
    
    msg = "Explain quantum computing in one sentence."
    
    # Create tasks with names for identification
    tasks = {
        asyncio.create_task(Runner.run(spanish_agent, msg)): "Spanish",
        asyncio.create_task(Runner.run(french_agent, msg)): "French",
        asyncio.create_task(Runner.run(german_agent, msg)): "German",
    }
    
    # Process as each completes
    print("\nResults arriving in completion order:\n")
    
    for i, coro in enumerate(asyncio.as_completed(tasks.keys()), 1):
        result = await coro
        # Find which agent this was
        agent_name = result.last_agent.name
        print(f"#{i} Finished: {agent_name}")
        print(f"   Output: {result.final_output[:80]}...\n")


# =============================================================================
# PATTERN 3: asyncio.TaskGroup - Better error handling (Python 3.11+)
# =============================================================================

async def pattern_taskgroup():
    """
    TaskGroup provides better error handling - if one fails, all are cancelled.
    
    ┌─────────────────────────────────────────────────────────────┐
    │                   asyncio.TaskGroup                         │
    │                                                             │
    │    ┌──────────┐                                             │
    │    │ Agent 1  │────┐                                        │
    │    └──────────┘    │                                        │
    │                    │    If ANY fails,                       │
    │    ┌──────────┐    ├───► ALL are cancelled                  │
    │    │ Agent 2  │────┤    and exception raised                │
    │    └──────────┘    │                                        │
    │                    │                                        │
    │    ┌──────────┐    │                                        │
    │    │ Agent 3  │────┘                                        │
    │    └──────────┘                                             │
    │                                                             │
    └─────────────────────────────────────────────────────────────┘
    """
    print("\n" + "=" * 60)
    print("PATTERN 3: asyncio.TaskGroup")
    print("=" * 60)
    
    msg = "What is machine learning?"
    
    results = []
    
    async with asyncio.TaskGroup() as tg:
        task1 = tg.create_task(Runner.run(spanish_agent, msg))
        task2 = tg.create_task(Runner.run(french_agent, msg))
        task3 = tg.create_task(Runner.run(german_agent, msg))
    
    # All completed successfully (or exception was raised)
    results = [task1.result(), task2.result(), task3.result()]
    
    print(f"\n✅ All {len(results)} tasks completed successfully")
    for res in results:
        print(f"  - {res.last_agent.name}: {res.final_output[:50]}...")


# =============================================================================
# PATTERN 4: Parallel with Timeout
# =============================================================================

async def pattern_with_timeout():
    """
    Don't wait forever - set a timeout for parallel operations.
    
    ┌─────────────────────────────────────────────────────────────┐
    │                   With Timeout                              │
    │                                                             │
    │    ┌──────────┐                                             │
    │    │ Agent 1  │──── Done in 2s ────► ✅ Got result         │
    │    └──────────┘                                             │
    │                         │                                   │
    │    ┌──────────┐         │ TIMEOUT                           │
    │    │ Agent 2  │─────────┼──── Still running... ► ❌ Cancelled
    │    └──────────┘         │ (5 sec)                           │
    │                         │                                   │
    │    ┌──────────┐         │                                   │
    │    │ Agent 3  │──── Done in 3s ────► ✅ Got result         │
    │    └──────────┘                                             │
    │                                                             │
    └─────────────────────────────────────────────────────────────┘
    """
    print("\n" + "=" * 60)
    print("PATTERN 4: Parallel with Timeout")
    print("=" * 60)
    
    msg = "Translate: Hello world"
    
    try:
        # Set 30 second timeout for all operations
        results = await asyncio.wait_for(
            asyncio.gather(
                Runner.run(spanish_agent, msg),
                Runner.run(french_agent, msg),
                Runner.run(german_agent, msg),
            ),
            timeout=30.0
        )
        print(f"\n✅ All completed within timeout")
        for res in results:
            print(f"  - {res.last_agent.name}: {res.final_output}")
            
    except asyncio.TimeoutError:
        print("\n⏰ Timeout! Some agents took too long.")


# =============================================================================
# PATTERN 5: Parallel with return_exceptions
# =============================================================================

async def pattern_handle_errors():
    """
    Continue even if some agents fail.
    
    ┌─────────────────────────────────────────────────────────────┐
    │              gather(return_exceptions=True)                 │
    │                                                             │
    │    ┌──────────┐                                             │
    │    │ Agent 1  │────► ✅ Success ────► result               │
    │    └──────────┘                                             │
    │                                                             │
    │    ┌──────────┐                                             │
    │    │ Agent 2  │────► ❌ Error ────► Exception object       │
    │    └──────────┘                                             │
    │                                                             │
    │    ┌──────────┐                                             │
    │    │ Agent 3  │────► ✅ Success ────► result               │
    │    └──────────┘                                             │
    │                                                             │
    │    Results: [result, Exception, result]                     │
    │                                                             │
    └─────────────────────────────────────────────────────────────┘
    """
    print("\n" + "=" * 60)
    print("PATTERN 5: Handle Errors Gracefully")
    print("=" * 60)
    
    msg = "Hello world"
    
    # return_exceptions=True means errors don't stop other tasks
    results = await asyncio.gather(
        Runner.run(spanish_agent, msg),
        Runner.run(french_agent, msg),
        Runner.run(german_agent, msg),
        return_exceptions=True  # Key!
    )
    
    # Process results, handling errors
    for i, res in enumerate(results):
        if isinstance(res, Exception):
            print(f"❌ Task {i+1} failed: {res}")
        else:
            print(f"✅ Task {i+1}: {res.final_output}")


# =============================================================================
# PATTERN 6: Fan-out/Fan-in (Your pattern, enhanced)
# =============================================================================

async def pattern_fan_out_fan_in():
    """
    Multiple workers → Aggregator
    
    ┌─────────────────────────────────────────────────────────────┐
    │                    Fan-out / Fan-in                         │
    │                                                             │
    │                    ┌──────────────┐                         │
    │               ┌───►│ Spanish      │───┐                     │
    │               │    └──────────────┘   │                     │
    │               │                       │                     │
    │    Input ─────┼───►┌──────────────┐   ├───► Aggregator ───► Output
    │               │    │ French       │───┤                     │
    │               │    └──────────────┘   │                     │
    │               │                       │                     │
    │               └───►┌──────────────┐   │                     │
    │                    │ German       │───┘                     │
    │                    └──────────────┘                         │
    │                                                             │
    │    "Fan out" to workers    "Fan in" to aggregator          │
    │                                                             │
    └─────────────────────────────────────────────────────────────┘
    """
    print("\n" + "=" * 60)
    print("PATTERN 6: Fan-out/Fan-in")
    print("=" * 60)
    
    msg = "The future of AI is collaboration between humans and machines."
    
    # Fan-out: Run all translators in parallel
    print("\n📤 Fan-out: Running 3 translators in parallel...")
    
    results = await asyncio.gather(
        Runner.run(spanish_agent, msg),
        Runner.run(french_agent, msg),
        Runner.run(german_agent, msg),
    )
    
    # Collect outputs
    translations = []
    for res in results:
        output = ItemHelpers.text_message_outputs(res.new_items)
        translations.append(f"[{res.last_agent.name}]: {output}")
    
    # Fan-in: Aggregator picks the best
    print("📥 Fan-in: Picker agent choosing best translation...")
    
    picker_input = f"""
Original: {msg}

Translations:
{chr(10).join(translations)}

Pick the best translation and explain why.
"""
    
    final_result = await Runner.run(picker_agent, picker_input)
    
    print(f"\n🏆 Best Translation:\n{final_result.final_output}")


# =============================================================================
# PATTERN 7: Parallel Different Tasks
# =============================================================================

async def pattern_different_tasks():
    """
    Run completely different agents/tasks in parallel.
    
    ┌─────────────────────────────────────────────────────────────┐
    │              Parallel Different Tasks                       │
    │                                                             │
    │    ┌────────────────┐                                       │
    │    │ Summarizer     │───► Summary                          │
    │    └────────────────┘                                       │
    │                                                             │
    │    ┌────────────────┐                                       │
    │    │ Critic         │───► Critique                         │
    │    └────────────────┘                                       │
    │                                                             │
    │    ┌────────────────┐                                       │
    │    │ Translator     │───► Translation                      │
    │    └────────────────┘                                       │
    │                                                             │
    │    All run simultaneously on SAME input!                    │
    │                                                             │
    └─────────────────────────────────────────────────────────────┘
    """
    print("\n" + "=" * 60)
    print("PATTERN 7: Different Tasks in Parallel")
    print("=" * 60)
    
    content = """
    Artificial Intelligence is transforming every industry. 
    From healthcare to finance, AI systems are making decisions 
    that were once the exclusive domain of human experts.
    """
    
    # Run different analyses in parallel
    summary_task, critique_task, translate_task = await asyncio.gather(
        Runner.run(summarizer_agent, f"Summarize this: {content}"),
        Runner.run(critic_agent, f"Critique this: {content}"),
        Runner.run(spanish_agent, f"Translate this: {content}"),
    )
    
    print(f"\n📝 Summary:\n{summary_task.final_output}")
    print(f"\n🔍 Critique:\n{critique_task.final_output}")
    print(f"\n🇪🇸 Spanish:\n{translate_task.final_output}")


# =============================================================================
# PATTERN 8: Pipeline with Parallel Stages
# =============================================================================

async def pattern_pipeline():
    """
    Some stages parallel, some sequential.
    
    ┌─────────────────────────────────────────────────────────────┐
    │                 Pipeline with Parallel Stages               │
    │                                                             │
    │                        STAGE 1 (Parallel)                   │
    │                    ┌──────────────────────┐                 │
    │                    │  ┌────────────────┐  │                 │
    │                    │  │ Summarizer     │  │                 │
    │    Input ──────────┤  └────────────────┘  ├────┐            │
    │                    │  ┌────────────────┐  │    │            │
    │                    │  │ Critic         │  │    │            │
    │                    │  └────────────────┘  │    │            │
    │                    └──────────────────────┘    │            │
    │                                                │            │
    │                        STAGE 2 (Sequential)    │            │
    │                    ┌──────────────────────┐    │            │
    │                    │                      │◄───┘            │
    │                    │  Improver            │                 │
    │                    │  (uses both outputs) │                 │
    │                    │                      │────► Final      │
    │                    └──────────────────────┘                 │
    │                                                             │
    └─────────────────────────────────────────────────────────────┘
    """
    print("\n" + "=" * 60)
    print("PATTERN 8: Pipeline with Parallel Stages")
    print("=" * 60)
    
    content = "AI will replace all human jobs by 2030."
    
    # Stage 1: Parallel analysis
    print("\n🔄 Stage 1: Parallel analysis...")
    summary_res, critique_res = await asyncio.gather(
        Runner.run(summarizer_agent, f"Summarize the argument: {content}"),
        Runner.run(critic_agent, f"Critique this claim: {content}"),
    )
    
    # Stage 2: Sequential improvement using both outputs
    print("🔄 Stage 2: Sequential improvement...")
    
    improver_input = f"""
Original claim: {content}

Summary: {summary_res.final_output}

Critique: {critique_res.final_output}

Based on the summary and critique, write an improved, more nuanced version.
"""
    
    final_res = await Runner.run(improver_agent, improver_input)
    
    print(f"\n📝 Original: {content}")
    print(f"\n✨ Improved:\n{final_res.final_output}")


# =============================================================================
# PATTERN 9: Dynamic Parallel Execution
# =============================================================================

async def pattern_dynamic_parallel():
    """
    Dynamically decide how many parallel tasks based on input.
    
    ┌─────────────────────────────────────────────────────────────┐
    │                Dynamic Parallel Execution                   │
    │                                                             │
    │    Input: ["task1", "task2", "task3", "task4", "task5"]    │
    │                                                             │
    │         ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐           │
    │         │ T1  │ │ T2  │ │ T3  │ │ T4  │ │ T5  │           │
    │         └──┬──┘ └──┬──┘ └──┬──┘ └──┬──┘ └──┬──┘           │
    │            │       │       │       │       │               │
    │            └───────┴───────┼───────┴───────┘               │
    │                            │                               │
    │                            ▼                               │
    │                    [results array]                         │
    │                                                             │
    └─────────────────────────────────────────────────────────────┘
    """
    print("\n" + "=" * 60)
    print("PATTERN 9: Dynamic Parallel Execution")
    print("=" * 60)
    
    # Dynamic list of items to process
    items_to_translate = [
        "Hello",
        "Goodbye", 
        "Thank you",
        "Please",
        "How are you?",
    ]
    
    print(f"\n📋 Processing {len(items_to_translate)} items in parallel...")
    
    # Create tasks dynamically
    tasks = [
        Runner.run(spanish_agent, f"Translate to Spanish: {item}")
        for item in items_to_translate
    ]
    
    # Run all in parallel
    results = await asyncio.gather(*tasks)
    
    # Display results
    print("\n📤 Results:")
    for item, res in zip(items_to_translate, results):
        print(f"  {item} → {res.final_output}")


# =============================================================================
# PATTERN 10: Semaphore - Limit Concurrent Requests
# =============================================================================

async def pattern_semaphore():
    """
    Limit how many agents run at once (rate limiting).
    
    ┌─────────────────────────────────────────────────────────────┐
    │            Semaphore (Max 2 concurrent)                     │
    │                                                             │
    │    Queue: [T1, T2, T3, T4, T5, T6]                         │
    │                                                             │
    │    Time 0:  ┌────┐ ┌────┐                                  │
    │             │ T1 │ │ T2 │  ← Only 2 running                │
    │             └────┘ └────┘                                  │
    │                                                             │
    │    Time 1:  ┌────┐ ┌────┐                                  │
    │             │ T3 │ │ T4 │  ← T1, T2 done, T3, T4 start    │
    │             └────┘ └────┘                                  │
    │                                                             │
    │    Time 2:  ┌────┐ ┌────┐                                  │
    │             │ T5 │ │ T6 │  ← T3, T4 done, T5, T6 start    │
    │             └────┘ └────┘                                  │
    │                                                             │
    └─────────────────────────────────────────────────────────────┘
    
    Good for: API rate limits, resource constraints
    """
    print("\n" + "=" * 60)
    print("PATTERN 10: Semaphore (Rate Limiting)")
    print("=" * 60)
    
    items = ["Hello", "World", "AI", "Future", "Code", "Learn"]
    
    # Only allow 2 concurrent requests
    semaphore = asyncio.Semaphore(2)
    
    async def limited_run(item: str):
        async with semaphore:  # Wait for slot
            print(f"  🟢 Starting: {item}")
            result = await Runner.run(spanish_agent, f"Translate: {item}")
            print(f"  🔴 Finished: {item}")
            return result
    
    print(f"\n📋 Processing {len(items)} items (max 2 concurrent):\n")
    
    # All tasks created, but semaphore limits concurrency
    results = await asyncio.gather(*[limited_run(item) for item in items])
    
    print(f"\n✅ All {len(results)} completed!")


# =============================================================================
# RUN ALL PATTERNS
# =============================================================================

async def main():
    print("=" * 60)
    print("OPENAI AGENTS SDK - PARALLELIZATION PATTERNS")
    print("=" * 60)
    
    await pattern_gather()
    await pattern_as_completed()
    await pattern_taskgroup()
    await pattern_with_timeout()
    await pattern_handle_errors()
    await pattern_fan_out_fan_in()
    await pattern_different_tasks()
    await pattern_pipeline()
    await pattern_dynamic_parallel()
    await pattern_semaphore()
    
    print("\n" + "=" * 60)
    print("✅ ALL PATTERNS DEMONSTRATED!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
