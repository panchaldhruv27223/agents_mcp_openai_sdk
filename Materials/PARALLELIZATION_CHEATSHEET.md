# OpenAI Agents SDK - Parallelization Cheatsheet

## Quick Reference

| Pattern | Use Case | Code |
|---------|----------|------|
| `asyncio.gather` | Wait for ALL results | `await asyncio.gather(task1, task2)` |
| `asyncio.as_completed` | Process as they finish | `for coro in asyncio.as_completed(tasks)` |
| `asyncio.TaskGroup` | Better error handling | `async with asyncio.TaskGroup() as tg` |
| `asyncio.wait_for` | Add timeout | `await asyncio.wait_for(gather(...), timeout=30)` |
| `asyncio.Semaphore` | Rate limiting | `async with semaphore: await task` |

---

## Pattern 1: Basic Gather (Wait for All)

```python
results = await asyncio.gather(
    Runner.run(agent1, msg),
    Runner.run(agent2, msg),
    Runner.run(agent3, msg),
)
# results = [res1, res2, res3] - in same order!
```

---

## Pattern 2: As Completed (First Come First Serve)

```python
tasks = [
    asyncio.create_task(Runner.run(agent1, msg)),
    asyncio.create_task(Runner.run(agent2, msg)),
    asyncio.create_task(Runner.run(agent3, msg)),
]

for coro in asyncio.as_completed(tasks):
    result = await coro  # Gets fastest result first!
    print(result.final_output)
```

---

## Pattern 3: TaskGroup (Python 3.11+)

```python
async with asyncio.TaskGroup() as tg:
    task1 = tg.create_task(Runner.run(agent1, msg))
    task2 = tg.create_task(Runner.run(agent2, msg))
    # If ANY fails, ALL cancelled + exception raised

results = [task1.result(), task2.result()]
```

---

## Pattern 4: With Timeout

```python
try:
    results = await asyncio.wait_for(
        asyncio.gather(
            Runner.run(agent1, msg),
            Runner.run(agent2, msg),
        ),
        timeout=30.0  # 30 seconds max
    )
except asyncio.TimeoutError:
    print("Took too long!")
```

---

## Pattern 5: Handle Errors Gracefully

```python
results = await asyncio.gather(
    Runner.run(agent1, msg),
    Runner.run(agent2, msg),  # This might fail
    Runner.run(agent3, msg),
    return_exceptions=True  # Don't crash on error!
)

for res in results:
    if isinstance(res, Exception):
        print(f"Error: {res}")
    else:
        print(res.final_output)
```

---

## Pattern 6: Fan-out/Fan-in

```python
# Fan-out: Multiple workers
results = await asyncio.gather(
    Runner.run(worker1, task),
    Runner.run(worker2, task),
    Runner.run(worker3, task),
)

# Collect outputs
outputs = [ItemHelpers.text_message_outputs(r.new_items) for r in results]

# Fan-in: Aggregator
final = await Runner.run(aggregator, f"Choose best: {outputs}")
```

---

## Pattern 7: Dynamic Parallel

```python
items = ["item1", "item2", "item3", "item4", "item5"]

# Create tasks dynamically
tasks = [Runner.run(agent, item) for item in items]

# Run all
results = await asyncio.gather(*tasks)
```

---

## Pattern 8: Rate Limiting (Semaphore)

```python
semaphore = asyncio.Semaphore(3)  # Max 3 concurrent

async def limited_run(item):
    async with semaphore:
        return await Runner.run(agent, item)

results = await asyncio.gather(*[limited_run(i) for i in items])
```

---

## Pattern 9: Pipeline (Parallel + Sequential)

```python
# Stage 1: Parallel
res1, res2 = await asyncio.gather(
    Runner.run(analyzer1, input),
    Runner.run(analyzer2, input),
)

# Stage 2: Sequential (uses parallel results)
final = await Runner.run(combiner, f"{res1.final_output}\n{res2.final_output}")
```

---

## Common Mistakes

### ❌ Wrong: Sequential (slow!)
```python
res1 = await Runner.run(agent1, msg)  # Waits
res2 = await Runner.run(agent2, msg)  # Then waits
res3 = await Runner.run(agent3, msg)  # Then waits
# Total time: t1 + t2 + t3
```

### ✅ Correct: Parallel (fast!)
```python
res1, res2, res3 = await asyncio.gather(
    Runner.run(agent1, msg),
    Runner.run(agent2, msg),
    Runner.run(agent3, msg),
)
# Total time: max(t1, t2, t3)
```

---

## Extracting Outputs

```python
# Get final output (simple)
output = result.final_output

# Get text from new_items (detailed)
output = ItemHelpers.text_message_outputs(result.new_items)

# Get last agent name
agent_name = result.last_agent.name
```

---

## With Tracing

```python
from agents import trace

async def main():
    with trace("Parallel Translation"):
        results = await asyncio.gather(
            Runner.run(spanish_agent, msg),
            Runner.run(french_agent, msg),
        )
```

---

## Decision Guide

| Scenario | Use |
|----------|-----|
| Same task, multiple agents | `gather` + Fan-in aggregator |
| Different tasks, combine results | `gather` → Sequential combiner |
| Show results ASAP | `as_completed` |
| Must complete or fail together | `TaskGroup` |
| API rate limits | `Semaphore` |
| Slow operations | `wait_for` with timeout |
| Some tasks may fail | `gather(return_exceptions=True)` |
