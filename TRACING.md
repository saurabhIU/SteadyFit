# LangSmith tracing (SteadyFit)

SteadyFit sends one LangSmith **trace tree per chat/weekly-review turn** when tracing is enabled. Traces are optional: missing keys or LangSmith downtime must never break chat.

## Enable locally

In `.env` (see `.env.example`):

```bash
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=lsv2_pt_...
LANGSMITH_PROJECT=steadyfit-dev   # use a different name per env
```

Legacy aliases also work: `LANGCHAIN_TRACING_V2`, `LANGCHAIN_API_KEY`, `LANGCHAIN_PROJECT`.

Restart the API after changing env (`uv run uvicorn app.main:app --reload --port 8000`). On startup you should see `langsmith_tracing_on project=…` in logs.

## Open the project

1. Go to [https://smith.langchain.com](https://smith.langchain.com)
2. Select project **`steadyfit-dev`** (or whatever `LANGSMITH_PROJECT` you set)
3. Open **Tracing** → latest runs

## Filter by profile

Every `graph.invoke` attaches:

- **metadata:** `user_id`, `endpoint` (`api/chat` | `api/approve` | `internal/weekly-review`)
- **tags:** `[user_id]` (e.g. `demo-veteran`)

In the UI: filter by tag `demo-veteran`, or metadata `user_id=demo-veteran`.

## How to read one chat trace

A typical `/api/chat` tree looks like:

```
LangGraph          ← parent graph.invoke
├─ scope_gate      ← verdict: in_scope | out_of_scope | bypassed_pending_state
├─ coach           ← intent routing LLM (schedule / nutrition / …)
├─ scheduler|nutrition|adherence|knowledge
│  ├─ ChatOpenAI (+ tool_calls)
│  ├─ calendar_conflicts / usda_food_lookup / web_search_fitness   (@tool)
│  ├─ find_exercises / get_substitutions                           (tool)
│  ├─ retrieve_kb / retrieve_personal / retrieve_memory            (retriever)
│  └─ …
├─ coaching_team   ← council merge LLM
└─ memory_write / weekly_summary   (weekly-review turns only)
```

**Retrievers** expose query + filters in inputs, and chunk **sources** (`source_file`, `kb_id`, score) in outputs — not full chunk text.

**Scope gate** output includes `verdict` so you can see why a turn was blocked, allowed, or bypassed (approve / intake).

## Production (Render)

`render.yaml` lists `LANGSMITH_TRACING`, `LANGSMITH_API_KEY`, and `LANGSMITH_PROJECT` (default `steadyfit-prod`). Set the key in the Render dashboard; leave tracing `false` if you do not want prod traffic traced.
