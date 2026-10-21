# LangGraph Module 3 — Streaming & Human-in-the-Loop
*Revision notes · LangChain Academy, Intro to LangGraph · notebooks 01-streaming, 03-editing-state-human-feedback, 04-dynamic_breakpoints · compiled 21 Oct 2026*

## 1. Streaming
- `graph.stream(input, config, stream_mode=...)` yields output *as the graph runs* instead of one final result.
- `stream_mode="values"` — full state after each super-step. `"updates"` — each node's update. `"messages"` — token-level LLM output (for chat UIs).
- The snapshot rule is visible in the stream: parallel branches' updates land together in one step.

## 2. Static breakpoints (pause at a fixed place)
- `compile(interrupt_before=["tools"], checkpointer=memory)` — the graph pauses **before** the named node, every time it's reached. (`interrupt_after` also exists.)
- A breakpoint **requires a checkpointer** — the paused state has to live somewhere.
- While paused: `graph.get_state(config).next` shows which node is queued; `.values` holds everything so far.
- **Resume:** `graph.stream(None, config)` — `None` means *no new input, continue this thread from its checkpoint*.
- Canonical use: **approval gates** — pause before the `tools` node so a human can approve/reject the tool call before it executes. (Your SDR agent's "approve before sending the email" is exactly this shape.)

## 3. Editing state & human feedback
- `graph.update_state(config, values, as_node=...)` rewrites state mid-flight. Values pass through the reducers like a node update — so for `messages`, the new message is **appended**, not substituted. (Your 3×6 → 6×7 edit left both human messages in state; the assistant obeyed the newest because it's last in the list.)
- **`as_node="human_feedback"`** — the update is recorded *as if that node produced it*, so on resume, execution follows **that node's outgoing edges**. Needed when the graph can't infer the source — e.g., the node never ran because you paused before it.
- **Dummy-node pattern:** `human_feedback` is a pass-through node (`pass`) that exists so a breakpoint has somewhere to sit *inside a loop*: `tools → human_feedback → assistant`, pausing for a human on every iteration. A node must have some callable, even a trivial one.
- Alternatives: `interrupt_before` on the next real node for a one-off pause/edit; dynamic `interrupt()` when whether to pause depends on the data (§4).

## 4. Dynamic breakpoints (pause decided by the data)
- `from langgraph.types import interrupt` — calling `interrupt(value)` **inside a node** pauses execution right there, mid-node, when a runtime condition holds (your notebook: `len(input) > 3` in node_2).
- The pause surfaces as `__interrupt__` in the stream output and in `state.tasks[].interrupts`.
- **Resume:** fix the state with `update_state` (you replaced `"hello world"` with `"hi"`), then `stream(None, config)`. The interrupted node **re-runs from its start**; nodes before it do not (node_1 didn't re-run, node_2 and node_3 did).
- Static vs dynamic: static = pause location fixed at compile time; dynamic = pause decided at run time, by the data flowing through the node.

## Q&A (from your questions)
**What is `as_node` in `update_state`?** It declares which node the manual update counts as coming from. Two effects: the update is written through that node's channels, and resume continues along that node's outgoing edges. Without it, LangGraph infers the source from history — and at a breakpoint before a node that never ran, there is nothing to infer from.

**Can you skip the dummy `human_feedback` node?** The node needs *a* function (even `pass`), but the placeholder pattern itself is optional. Use `interrupt_before` on a real node when the pause is a one-off edit point; use `interrupt()` inside a real node when the pause is conditional. Keep the dummy when the human checkpoint is a recurring step in a loop — that's the case it was invented for.

## Test yourself
1. Why does a breakpoint require a checkpointer?
2. State shows `.next == ("tools",)` and you call `stream(None, config)`. What does `None` mean here, and what runs next?
3. After your `update_state` edit, both the old and new human messages were in state — yet the assistant multiplied 6×7, not 3×6. Why?
4. `interrupt_before` vs `interrupt()` — which is decided at compile time and which at run time? Give one SDR-agent use for each.
5. In the dynamic-breakpoint run, why did node_1 not re-run on resume but node_2 did?

### Answer key
1. Pausing means freezing a half-finished execution and resuming it later — the state (and where execution stopped) must be persisted. No checkpointer, nowhere for the pause to live.
2. `None` = resume this thread with no new input. The `tools` node runs — the breakpoint was *before* it, so it's next.
3. `update_state` writes go through the `add_messages` reducer, which appends (the new message had a fresh id, so nothing was replaced). The LLM simply follows the most recent instruction in the list.
4. `interrupt_before` = compile time (fixed node, every pass). `interrupt()` = run time (condition on the data). SDR: `interrupt_before` the send node for a standing approval gate; `interrupt()` inside the scoring node when `icp_score` hits a suspicious 100 and a human should verify.
5. Resume restarts the *interrupted* node from its beginning; nodes that already completed in earlier super-steps are checkpointed and not re-executed.
