# LangGraph Module 2 — State, Reducers, Schemas & Memory
*Revision notes · LangChain Academy, Intro to LangGraph · notebooks 01–06 · compiled 21 Oct 2026*

## 1. State schemas: three ways to declare state
- **TypedDict** — a dict contract. No runtime validation.
- **dataclass** — attribute access (`state.name`), defaults allowed. Still no strict validation.
- **Pydantic `BaseModel`** — real validation, with one hard boundary (learned by debugging): **LangGraph validates the invoke input against the schema; node return values are merged channel-by-channel through reducers and are NOT re-validated against the model.** node_3's hardcoded `"sad"` was stored even though `mood: Literal["happy", "mad"]` — the invalid value entered through a node update, not the door.
- A `@field_validator` must live **inside** the class body. Defined at module level, it's dead code — Pydantic never registers it.
- Optional keys: `NotRequired[...]` / `total=False` / `Optional[...] = None` — the key may simply not exist in state yet.

## 2. Reducers (summary — full notes in `langgraph-reducers-revision-notes.md`)
- Default behavior is **overwrite**; two parallel nodes writing the same key in one super-step → `InvalidUpdateError`.
- A reducer in `Annotated[key, fn]` merges instead: `new = fn(old, update)`. `operator.add` on lists = concatenation.
- Parallel branches read the **same snapshot**: fan-out from `[1]` → `[1, 2, 3, 3]`; chain → `[1, 2, 3, 4]`.
- Custom reducers must accept `None` on either side (first write to a fresh key); `[]` is the identity element for concatenation.
- Nodes read the frontier (`[-1]`), and return updates **shaped for the reducer** (list-wrapped for `add`).

## 3. Multiple schemas
- One schema for everything = two risks: **input pollution** (caller can inject `icp_score: 100`) and **internal leakage** (caller sees research notes, drafts, traces).
- `StateGraph(OverallState, input_schema=InputState, output_schema=OutputState)`:
  - Input keys outside `InputState` are **dropped at the door** on invoke.
  - Only `OutputState` keys are returned; overall-only keys (dossier, score) stay private.
  - Nodes always see and write the **overall** state.
- Pattern: `class OverallState(InputState, OutputState)` — inherits both, no repeated keys. Output keys must exist in the overall state or no node can write them.
- **The schema passed to `StateGraph` is the contract.** In notebooks 05/06 the graph was first built with `StateGraph(MessagesState)` while the nodes used the `State` subclass's `summary` key — fixed to `StateGraph(State)`. If a key isn't in the built schema, it doesn't exist as far as the graph is concerned.
- SDR split: Input = caller identifiers (name, email, profile links) · Output = draft email · Private = research findings, dossier, ICP score.

## 4. Filtering & trimming messages
- `MessagesState` carries `messages: Annotated[list, add_messages]` — updates are **appended**, never overwritten. (A returned message whose id already exists *replaces* that message — that's how in-place edits work.)
- **Filtering = deletion via `RemoveMessage`**: return `[RemoveMessage(id=m.id) for m in state["messages"][:-1]]` to delete everything except the last message (`[:-2]` keeps the last two).
- Trimming is cheap and dumb: the deleted content is simply gone.

## 5. Chatbot with summary (the smarter alternative to trimming)
- State extends `MessagesState` with `summary: str`.
- `call_llm`: if a summary exists, prepend it as a `SystemMessage`, then the surviving messages.
- **Conditional edge** — `should_summarize(state)`: `len(messages) > 6` → `"summarize_conversation"`, else `END`. Registered with `add_conditional_edges("call_llm", should_summarize, ["summarize_conversation", END])`. The router returns a node name (or `END`); the graph follows it.
- `summarize_conversation`: the LLM folds the old summary + current messages into a new summary; `RemoveMessage` deletes all but the last 2 messages; returns `{"summary": new_summary, "messages": [RemoveMessage, ...]}`.
- Trade-off: trimming loses information silently; summarizing costs one LLM call but keeps the gist. Filter when the old turns are worthless, summarize when they're not.

## 6. Persistence: checkpointers & threads
- `compile(checkpointer=...)` saves state after every step — this is what makes multi-turn conversations (and breakpoints) possible.
- `MemorySaver` — in-process; state dies with the process. `SqliteSaver(sqlite3.connect(path, check_same_thread=False))` — on disk, survives restarts. (Postgres saver = the production version of the same idea.)
- `thread_id` selects the conversation: `config = {"configurable": {"thread_id": "1"}}`. Same graph, many independent threads — the checkpointer loads the right one.
- Inspect: `graph.get_state(config)` → current `.values` and `.next`; `graph.get_state_history(config)` → every checkpoint.

## Q&A (from your questions)
**Why does `invoke` look different in different places?** It's always the same argument — the input update — in different shapes: (a) a dict of partial state updates, `{"name": "lance"}`; (b) a schema instance when the schema is a dataclass/Pydantic class, `DataclassState(name="lance")`; (c) messages shorthand — the `messages` channel coerces a string into a `HumanMessage` and a single message into a one-item list, so `{"messages": "multiply 2 and 3"}` works; (d) `None` — not input at all, it means "resume from checkpoint" (Module 3).

**`state.get("x")` vs `state["x"]`?** `state["x"]` raises `KeyError` if the key is absent — use it when the key is guaranteed present (`messages`). `state.get("x")` returns `None` — use it for keys that may not have been written yet. Your chatbot proves the rule: on turn 1 there is no `summary` key, so `call_llm` must use `state.get("summary")` or the first invoke crashes.

## Test yourself
1. Your Pydantic state forbids `mood="sad"`, yet a run stored it. Where did the value enter, and why was there no error?
2. A graph is built with `StateGraph(MessagesState)`, and a node returns `{"summary": "..."}`. What happens to `summary`?
3. With the `add` reducer, fan-out vs chain from `foo=[1]` (each node appends `[-1]+1`) — final `foo` each way, and why?
4. Why must `call_llm` in the summary chatbot use `state.get("summary")` instead of `state["summary"]`?
5. Two users chat with the same compiled graph at the same time. What keeps their states from mixing?

### Answer key
1. Through a node update (node_3's hardcoded return). LangGraph validates invoke input against the schema, but merges node updates per-channel without re-validating against the model.
2. Nothing good — `summary` isn't in the built schema, so it isn't a channel the graph tracks. The schema passed to `StateGraph` is the contract; build with the class that declares the key (`StateGraph(State)`).
3. Fan-out: `[1, 2, 3, 3]` — both branches read the same `[1, 2]` snapshot. Chain: `[1, 2, 3, 4]` — each node sees the previous node's write.
4. `summary` doesn't exist in state until the first summarization runs; `state["summary"]` would raise `KeyError` on the first turn.
5. The `thread_id` in the config — each thread has its own checkpointed state.
