# Safety Gate (guardrails) — drop-in module

A self-contained Safety Gate for the AFS in-line spectroscopy assistant. It classifies
an incoming enquiry **before** it reaches the agent/RAG pipeline and tells the caller
whether to proceed, hard-block, or push back for clarification.

This folder is the guardrails feature **only** — no FastAPI app, no report builder, no
pipeline. Wire it into whatever API you already have.

## Two modes, one interface

`build_guard()` picks the mode once, from the environment:

| Mode | When | What it is |
| --- | --- | --- |
| **LLM** (primary) | `OPENAI_API_KEY` is set | OpenAI classifier labels each enquiry. |
| **Rules** (fallback) | no key present | Dependency-light, deterministic keyword/intent gate. Needs no network. |

Both return the same `GuardResult`, so your code never branches on the mode. If the LLM
call fails at runtime it degrades to the rule gate automatically.

Optional overrides: `OPENAI_MODEL` (default `gpt-4o-mini`), `OPENAI_BASE_URL`,
`GUARD_MODE=rules|llm` to force a mode.

## What it decides

```python
from safety_gate.guardrails import build_guard, GuardCategory

guard = build_guard()          # build once at startup
result = guard.check(user_text)

if result.passed:
    ...                        # on-topic -> run your pipeline
elif result.category.is_hard_block:
    ...                        # off_topic / jailbreak / injection -> refuse (out of scope)
elif result.category.is_premise_flag:
    ...                        # approval_demand / immediate_config / research_as_proof
                               # -> on-topic, but ask the clarifying questions first
reply_text = result.message    # ready-to-show refusal / push-back
```

`GuardResult` fields: `passed`, `category`, `message`, `extra` (other flags that also
fired), `engine` (`"llm"` or `"rules"`, handy for tracing).

### Categories

- **Hard blocks** (stop the request): `OFF_TOPIC`, `JAILBREAK`, `INJECTION`.
- **Premise flags** (on-topic, but a premise must be challenged first — the H04/H05/H06
  cases): `APPROVAL_DEMAND` ("approve this concept now"), `IMMEDIATE_CONFIG` ("give the
  exact method + sensor config immediately"), `RESEARCH_AS_PROOF` ("quote a research
  study as proof a new/clinical use is ready").

## Minimal wiring example (FastAPI)

```python
from safety_gate.guardrails import build_guard

GUARD = build_guard()

@app.post("/query")
def query(req: QueryRequest):
    result = GUARD.check(req.q)
    if not result.passed:
        return {"answer": result.message, "blocked": True,
                "category": result.category.value}
    return run_pipeline(req.q)   # your existing agent/RAG flow
```

## Layout

```
safety_gate/
  config.py                 # reads env, decides llm vs rules
  guardrails/
    __init__.py             # build_guard()
    base.py                 # GuardResult, GuardCategory, Guard protocol
    scope.py                # domain description + refusal/push-back messages
    rule_guard.py           # deterministic fallback gate
    llm_guard.py            # OpenAI classifier (primary)
  tests/
    verify_gate_logic.py    # dependency-free: 9/9 cases incl. H04/H05/H06
```

## Verify

```bash
cd backend
python -m safety_gate.tests.verify_gate_logic   # no deps needed
# LLM mode additionally needs:  pip install "openai>=1.30,<2.0"  and  OPENAI_API_KEY
```
