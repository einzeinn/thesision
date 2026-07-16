# Thesision

> Reason Before Decision.

Thesision is a Developer Tools project built for the OpenAI Build Week
Hackathon. It helps software engineers inspect an AI-assisted technical
decision as a visible reasoning graph rather than a chat transcript.

The product is intentionally narrow: a user asks an engineering question,
Thesision develops hypotheses, gathers evidence, compares trade-offs, records
confidence, and produces a conclusion that remains open to inspection.

## Why it exists

Engineering decisions are often made from a mixture of incomplete evidence,
team constraints, and competing priorities. A single generated answer hides
those inputs. Thesision makes the intermediate work visible so that an engineer
can review the basis for a recommendation rather than treating it as an answer
to accept blindly.

## What it does

- Runs an orchestrated reasoning pipeline: Question → Hypothesis → Evidence →
  Perspectives → Judge → Confidence → Conclusion.
- Renders the reasoning as an interactive, deterministic constellation graph
  that grows as stages complete. A question-seeded template keeps replay,
  imported sessions, and continued reasoning visually stable while retaining
  an organic shape.
- Shows evidence sources as graph satellites and as clickable references in
  the workspace.
- Requires every completed Judge round to include a comparative synthesis and
  a conflict explanation; incomplete Judge JSON is repaired once or fails
  explicitly instead of producing an empty result.
- Supports replay, graph inspection, session continuation, JSON import/export,
  and concise Markdown export with a scannable confidence bar and recorded
  evidence, conflict, and perspective signals.
- Keeps completed session state in SQLite locally; a JSON export can restore a
  session after an ephemeral demo deployment restarts.

Thesision is not a chatbot and does not make the final engineering decision for
the user.

## How the reasoning pipeline works

```text
Question
  ↓
Hypothesis generation
  ↓
Grounded evidence retrieval
  ↓
Maintainability, performance, and scalability perspectives
  ↓
Judge and confidence evaluation
  ↓
Conclusion
```

The orchestrator may run additional rounds when confidence is insufficient or
important conflicts remain unresolved.

Judge and Conflict remain inspectable artifacts: the Judge compares the
recorded hypotheses, evidence, and perspectives, while the Conflict node
explains whether material disagreement remains and why.

## GPT-5.6 and evidence retrieval

The default AI/ML API configuration uses one API key with two stage-specific
models:

- `openai/gpt-5.6-luna` handles hypothesis generation, perspectives, judging,
  conclusion, and concise Markdown report generation.
- `perplexity/sonar` handles only the Evidence stage and uses web search.

The Evidence adapter accepts a URL only when it appears in Sonar's returned
`citations` or `search_results`. This prevents the reasoning model from
presenting a plausible-looking but unverified URL as evidence. If the Evidence
model is unavailable, Thesision still completes the session with explicitly
labelled, unverified model-derived considerations; those items do not increase
evidence quality.

## Run locally

### Prerequisites

- Python 3.11+
- Node.js 20+
- An AI/ML API key for live reasoning

### Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
npm ci
Copy-Item .env.example .env
```

Set the key in `.env`; no second key is needed:

```dotenv
AI_PROVIDER=aimlapi
AIMLAPI_API_KEY=your-key
AIMLAPI_MODEL=openai/gpt-5.6-luna
AIMLAPI_EVIDENCE_MODEL=perplexity/sonar
```

Build the frontend and start the application:

```powershell
npm run build:frontend
uvicorn src.backend.app.main:app --reload
```

Open `http://127.0.0.1:8000`.

### Verify the project

```powershell
.\.venv\Scripts\python.exe -m pytest -q
npm run typecheck:frontend
npm run build:frontend
```

The test suite uses a fake model, so it does not spend API credits.

## Deployment on Render

`render.yaml` defines a Docker-based Render web service. Create a Render
Blueprint from this repository and provide `AIMLAPI_API_KEY` as the only secret;
the model variables are already included in the Blueprint.

The free tier has ephemeral storage. A completed session can be exported as
JSON and imported later to restore its graph, evidence, exports, and replay
state. The deployment health endpoint is `/health/live`. Before recording a
demo, open the service once to allow a free instance to wake up, then run a
complete live session and verify its evidence links.

## Suggested judge walkthrough

1. Ask an engineering question, such as whether a FastAPI service should move
   to Go.
2. Watch the Question root and subsequent stage nodes appear in a stable
   constellation as the graph grows.
3. Inspect an Evidence node and open a source link from the right panel.
4. Select nodes to compare an engineering perspective, conflict, or judge
   synthesis.
5. Review confidence and the final conclusion.
6. Export Markdown for a concise report, or JSON to preserve the full session.
7. Import a completed JSON session and choose Continue reasoning to append a
   new round without changing the original session.

## How I collaborated with Codex

Codex was used as an implementation collaborator throughout this project. It
helped turn the documented product scope into a working FastAPI and TypeScript
application, while product direction and acceptance decisions stayed explicit.

Concrete areas where Codex accelerated the work include:

- organizing the orchestrator-first session lifecycle and regression tests;
- migrating the browser application from inline JavaScript to strict
  TypeScript modules;
- implementing and refining the deterministic constellation graph layout,
  animation, sidebar, popup, replay, and continuation interactions;
- hardening local and Render deployment configuration, including health checks
  and recovery through JSON session import;
- adding the GPT-5.6 Luna and Sonar stage-specific configuration, citation
  validation, and transparent fallback behavior;
- revising exports so JSON remains portable while Markdown is concise and
  human-readable.

The dated Git history documents these implementation steps. The Codex session
used for the core build can be supplied through the hackathon submission's
`/feedback` Session ID field.

## Project structure

```text
src/backend/        FastAPI API, orchestrator, agents, session storage
src/frontend/app/   TypeScript workspace and graph renderer
docs/               Product, architecture, design, RFCs, and demo guidance
tests/              Backend and integration regression coverage
```

## Submission materials

Before final submission, add the verified public Render URL and the public
YouTube demo URL here or in the hackathon form. The demonstration should show
the working product, describe the role of Codex and GPT-5.6, and remain under
three minutes with English audio.
