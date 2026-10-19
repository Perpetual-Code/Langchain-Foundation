# LangGraph Reducers — Revision Notes
*Session: 16–17 Oct 2026 · Agents track (LangChain Academy, Intro to LangGraph)*

## 1. State is a TypedDict — the graph's shared memory
```python
class NewState(TypedDict):
    foo: Annotated[list[int], add]
```
- Declares which keys exist in state and their types.
- Every node receives the **whole** state dict and returns a **partial** update dict (only the keys it changes).

## 2. How `Annotated` works
- Plain Python (`typing.Annotated`), not LangGraph magic: `Annotated[type, metadata]` = the type plus a "bonus parcel" of metadata.
- Python itself ignores the parcel; libraries unwrap it with `get_type_hints(..., include_extras=True)` and act on it.
- LangGraph's convention: the parcel must be a **reducer** — a function `(old, new) -> merged`.

## 3. Reducers: merge instead of overwrite
- No `Annotated` → default is **overwrite** (last writer wins).
- With a reducer → `state[key] = reducer(current_value, node_update)`.
- `operator.add` on lists = concatenation: `add([1], [2])` → `[1, 2]`.
- The reducer runs **only on node updates** — the `invoke({...})` input is taken as-is, no reducer involved.

## 4. Custom reducers
```python
def reduce_list(left: list | None, right: list | None) -> list:
    if not right:
        right = []
    if not left:
        left = []
    return left + right
```
- `left` = what's already in state; `right` = what the node just returned.
- `left` is `None` on the **first write** to a fresh key (key absent from `invoke` input) → the guard normalizes it to `[]`.
- `right` is `None` when a node returns `{"foo": None}` (a branch that found nothing).
- `[]` is the **identity element** for concatenation — the "zero" of list-append: `[] + [2]` → `[2]`, `[1] + []` → `[1]`.
- Without the guards, `None + [2]` → TypeError (same family as the `[1] + 2` crash).
- Rule of thumb: a reducer must accept `None` on either side and always return the declared type.

## 5. The node contract (and the indexing trap)
- Node = function: state dict in, update dict out.
- The update must be **shaped for the reducer**: with `add`, return a list — `{"foo": [2]}`, not `{"foo": 2}` (`add([1], 2)` dies; `add([1], [2])` works).
- `state["foo"] + 1` is `[1] + 1` → TypeError. Index down to the element first: `state["foo"][0] + 1`.
- `[0]` reads the **first** element — stale in a loop, the counter stalls (keeps appending `2`s). `[-1]` reads the **frontier** — the counter progresses.
- The reducer's whole job is accumulating history so each step builds on the latest state — so read the latest.

## 6. Parallel branches share one snapshot (super-steps)
- Edges `node_1 → node_2` **and** `node_1 → node_3` = fan-out: node_2 and node_3 run **in parallel, in the same super-step**.
- Rule: parallel nodes all read the **same state snapshot**; none sees the others' updates until the next super-step.
- Fan-out trace (input `[1]`): `[1]` → node_1 → `[1, 2]` → node_2 & node_3 both read `[1, 2]`, both append `[3]` → **`[1, 2, 3, 3]`**.
- Chain trace (`node_1 → node_2 → node_3`): `[1]` → `[1, 2]` → `[1, 2, 3]` → **`[1, 2, 3, 4]`**.
- Same nodes, same reducer — the **edges alone** decided the outcome.
- Design rule: parallel fan-out is for **independent** work. Branches writing to the **same key** duplicate/clobber each other. Give each branch its own key (`company_dossier`, `person_dossier`) and merge downstream.

## 7. Watching state evolve
- `graph.stream(input, stream_mode="updates")` — each node's update per super-step. Parallel updates arrive in **one chunk** — that's the snapshot rule made visible.
- `stream_mode="values"` — full state after each super-step. Fan-out: `[1]` → `[1, 2]` → `[1, 2, 3, 3]` (note: `[1, 2, 3]` never exists as a state).
- `graph.get_state_history()` — walk every checkpoint after a run.
- LangGraph Studio (`langgraph dev`) — visual graph, click each step, inspect state in/out, time-travel.
- `print(state)` inside a node — the humble standby.

## 8. Reducer use cases
| Use case | Reducer | Why it fits |
|---|---|---|
| Chat history in an agent loop | `add_messages` | Every turn appends Human/AI/Tool messages; the model always sees full history |
| Fan-out / fan-in collection | `add` on lists | Parallel branches each append findings; a merge node reads the accumulated list |
| Counters | `add` on ints (`Annotated[int, add]`) | Loop iteration count, retry count, tool-call budget in the agent loop |
| Running totals | `add` on ints/floats | Accumulated API cost, summed relevance scores across rounds |
| Merging parallel dicts | custom dict-merge | `company_dossier` + `person_dossier` branches merged into one dossier |
| Collecting unique IDs | custom set-union | Doc IDs gathered across retrieval rounds, deduplicated |
| Keep-the-best | custom max reducer | Highest score kept across reranker passes |
| SDR agent dossier | `add` on list of findings | Each research step appends; later steps read `[-1]` (the frontier, not the past) |
| Corrective-RAG loop | `add` on candidate lists | Each retrieval round appends candidates; the reranker reads the accumulated pool |

## 9. Test yourself
1. State `foo = [1]`, reducer `add`. A node returns `{"foo": 2}`. What happens — and what's the fix?
2. A loop node returns `{"foo": [state["foo"][0] + 1]}` starting from `[1, 2, 3]`. What is `foo` after 3 iterations? What if it used `[-1]`?
3. Fan-out (`1→2, 1→3`) vs chain (`1→2→3`); every node appends `[-1] + 1`; input `[1]`. Final `foo` in each case — and why do they differ?
4. In `reduce_list`, which guard protects the first write to a fresh key, and what breaks without it?
5. `stream_mode="values"` on the fan-out graph shows which states — and why does `[1, 2, 3]` never appear?

### Answer key
1. TypeError — `add([1], 2)`. Fix: return a list, `{"foo": [2]}`.
2. `[0]`: `[1, 2, 3, 2, 2, 2]` — stalls, keeps appending `2`. `[-1]`: `[1, 2, 3, 4, 5, 6]` — progresses.
3. Fan-out: `[1, 2, 3, 3]` — both branches read the same `[1, 2]` snapshot, duplicate `3`. Chain: `[1, 2, 3, 4]` — each node sees the latest state.
4. The `left` guard. First write calls `reduce_list(None, [2])`; without it, `None + [2]` → TypeError.
5. `[1]` → `[1, 2]` → `[1, 2, 3, 3]`. node_2 and node_3 share one super-step, so both updates land together — `[1, 2, 3]` never exists as a state.

---
*Next up: conditional edges / routing — your SDR score-threshold as a conditional edge.*
