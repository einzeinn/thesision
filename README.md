# Thesision

**Transparent, evidence-driven reasoning for engineering decisions — built reasoning-first, not chatbot-first.**

Thesision is an AI reasoning platform that doesn't just answer engineering questions — it shows its work. Every conclusion comes with the hypotheses it considered, the evidence it pulled and rated, the debate it ran across multiple perspectives, an honest confidence score, and the exact conditions that would change its mind.

> Built for [OpenAI Hackathon submission] · [Devpost](https://openai.devpost.com/) · [Live demo](https://thesision.onrender.com)

---

## Why

Most AI chatbots answer engineering questions instantly and confidently — with no visible evidence, no stated uncertainty, and no way to know when the answer might be wrong. For decisions that shape a codebase or a team for months (architecture, tooling, trade-offs), that's not good enough.

Thesision treats a question as something to *reason through*, not autocomplete:

- Generates multiple competing hypotheses instead of committing to the first plausible answer
- Pulls real evidence from the web and rates source strength
- Runs multi-round internal debate across distinct perspectives (e.g. engineering velocity, debugging complexity, deployment risk)
- Reports an honest confidence score instead of false certainty
- States explicitly what would change the conclusion — a core assumption disproved, an unresolved conflict resolved, a key unknown answered

A completed session can be exported as JSON and re-imported to push the reasoning deeper — more debate rounds, more perspectives, more evidence — or handed off to another AI system entirely. Every conclusion also exports to a clean Markdown report for human review.

## Example Output

Reasoning unfolds live as an interactive graph, where each node is a step in the process:

| Node | Meaning |
| --- | --- |
| `H` | Hypothesis |
| `E` | Evidence |
| `P` | Perspective |
| `C` | Conflict |
| `J` | Judge |
| `✓` | Conclusion |

The sidebar tracks progress in plain language as it happens — *Building hypothesis → Searching evidence → Evaluating perspectives → Resolving conflicts → Synthesizing conclusion* — alongside a live confidence bar and the evidence references the session pulled in, each linked back to its source.

Once complete, a session exports to:

- **Markdown** — a structured report (confidence score, evidence table, reasoning trace, trade-offs, caveats, "decision would change if", final recommendation) for human review
- **JSON** — the full session state, importable back into Thesision to continue reasoning, or into another AI system entirely

## Features

- **Live reasoning graph** — hypotheses, evidence, perspectives, conflicts, and the judge's synthesis render as a connected, animated graph as the session runs, not just a spinner
- **Evidence retrieval & rating** — sources are pulled, deduplicated, linked, and rated by strength rather than presented as unverified fact
- **Multi-perspective debate** — the same question is argued from multiple angles before a judge synthesizes a conclusion
- **Honest confidence scoring** — a live confidence bar computed from evidence quality, unresolved conflicts, and perspective coverage, not asserted
- **Engineering context input** — constraints, workload, and other project context can be supplied alongside the question to ground the reasoning
- **Session import/export** — export a session as JSON to continue reasoning later, feed it to another AI system, or import a prior session back in
- **Markdown export** — every session renders as a clean, human-readable report

## Architecture

- **Backend:** FastAPI, orchestrator-first — every reasoning session is a structured, persisted state, not a black box
- **Persistence:** SQLite-backed session storage
- **Frontend:** lightweight reasoning workspace UI with a live SVG graph view of the reasoning process
- **Design principle:** reasoning first, not chatbot-first — the system is built to add further orchestration stages (more debate strategies, more evidence sources) over time

## Getting Started

### Prerequisites

- Python 3.11+
- Virtual environment support

### Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

### Configure a provider

Thesision needs one LLM provider configured in `.env` before it can reason. AI/ML API is supported via its OpenAI-compatible chat-completions endpoint:

```powershell
$env:AI_PROVIDER = "aimlapi"
$env:AIMLAPI_API_KEY = "your-key"
# Optional: $env:AIMLAPI_MODEL = "gpt-4o"
```

### Run the backend

```powershell
uvicorn src.backend.app.main:app --reload
```

### Run tests

```powershell
pytest -q
```

## Project Principles

- Reasoning first, not chatbot-first.
- Secrets are provided via environment variables only — never committed.
- The architecture stays modular and orchestrator-first, so new reasoning stages can be added without rewriting the core.

## Project Status

Actively developed as a hackathon MVP. Current state: reasoning workspace, evidence rating, multi-perspective debate, confidence scoring, and Continue Reasoning are implemented and covered by a regression test suite (`pytest`). See `PHASE_REPORT.md` for the latest phase notes.

## Roadmap

- Additional evidence sources beyond web search
- More debate/orchestration strategies
- Session comparison (re-run the same question, diff the reasoning)
- Public demo deployment

## License

_Not yet specified — add a `LICENSE` file (MIT is a common default for hackathon projects) before making the repo public-facing for judging, so reviewers know how they're allowed to use the code._

## Links

- Repository: [github.com/einzeinn/thesision](https://github.com/einzeinn/thesision)
- Devpost: [openai.devpost.com](https://openai.devpost.com/)