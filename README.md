# Thesision

> Reason Before Decision.

<p align="center">
  <img src="docs/preview/demo5.gif" width="900" alt="Thesision reasoning graph growing from question to conclusion" />
</p>

<p align="center">
  <strong>Transparent, evidence-driven reasoning for engineering decisions.</strong><br />
  Built reasoning-first, not chatbot-first.
</p>

<p align="center">
  <a href="https://thesision.onrender.com">Live demo</a> ·
  <a href="https://youtu.be/JvEz3fnC_HQ">Demo video</a> ·
  <a href="https://github.com/einzeinn/thesision">Repository</a> ·
  <a href="https://openai.devpost.com/">OpenAI Build Week</a>
</p>

Thesision is a Developer Tools project for engineers who need to make technical
decisions with incomplete evidence and competing constraints. Instead of
returning one confident chat response, it exposes the hypotheses, evidence,
perspectives, conflicts, confidence, and decision conditions behind a
recommendation.

## Why It Matters

Engineering decisions are expensive. Choosing the wrong architecture, platform,
or infrastructure approach can cost months of engineering time.

Most AI tools generate answers. Thesision generates an inspectable reasoning
record. It does not ask users to trust the model; it shows what supports a
recommendation, what remains uncertain, and what would change the result.

## What It Does

- Generates competing engineering hypotheses rather than committing to the
  first plausible answer.
- Retrieves grounded web evidence with clickable provider-returned source URLs.
- Examines maintainability, performance, and scalability perspectives.
- Makes unresolved conflicts and missing decision inputs visible.
- Produces a Judge synthesis and confidence score without hiding uncertainty.
- Uses later rounds to investigate the most important recorded gap—an
  unresolved conflict, weak evidence, perspective trade-off, or Judge
  condition—instead of repeating the original question.
- Exports a concise Markdown decision report and a portable JSON session.
- Replays, imports, and continues completed reasoning sessions.

## How Thesision Works

```text
Question
  ↓
Hypothesis Generation
  ↓
Grounded Evidence Retrieval
  ↓
Perspective Analysis
  ↓
Conflict Analysis
  ↓
Judge Synthesis
  ↓
Confidence Scoring
  ↓
Final Recommendation
```

The orchestrator may run up to three debate rounds when confidence is
insufficient or material conflicts remain. Each completed Judge result must
include a comparative synthesis and an explanation of whether conflicts remain;
incomplete Judge output is repaired once or fails explicitly rather than being
shown as an empty result.

From Round 2 onward, Thesision keeps the same visible pipeline but gives the
next Hypothesis and Evidence stages one deterministic refinement target from
the preceding canonical artifacts. It prioritizes unresolved conflicts, then
weak or missing evidence, perspective trade-offs, and finally the Judge
synthesis. This keeps continued reasoning cumulative without treating the
final recommendation as a prompt for more of the same.

The frontend renders these artifacts as a deterministic constellation graph.
Each question selects a stable layout template, so replay, imported sessions,
and continued reasoning remain readable while the graph still feels organic.

## Example Question

```text
Should an early-stage AI startup use Docker Compose, a managed container
platform, or Kubernetes for production deployment before reaching
product-market fit?
```

Thesision will generate multiple hypotheses, retrieve evidence, compare
perspectives, surface conflicts, produce a confidence-scored recommendation,
and export the result as Markdown or JSON.

## Architecture

```text
User Question
    │
    ▼
FastAPI API and Session Store
    │
    ▼
Reasoning Orchestrator
    ├── Hypothesis Generator
    ├── Evidence Retriever (grounded web search)
    ├── Perspective Analyzer
    ├── Judge and Conflict Analysis
    ├── Confidence Evaluator
    └── Conclusion Generator
    │
    ▼
Interactive Graph · Markdown Report · JSON Session Export
```

## Tech Stack

| Layer | Technology |
| --- | --- |
| Frontend | TypeScript, Vite, D3, anime.js, SVG |
| Backend | Python, FastAPI, HTTPX |
| Persistence | SQLite with JSON-backed session state |
| Reasoning | GPT-5.6 Luna through AI/ML API |
| Evidence | Perplexity Sonar web search through AI/ML API |
| Deployment | Docker, Render |
| Development | OpenAI Codex, GitHub |

## How GPT-5.6 Was Used

GPT-5.6 Luna is the structured reasoning engine, not a chatbot response
generator. It is responsible for:

- generating competing hypotheses and their assumptions;
- analyzing engineering perspectives and trade-offs;
- comparing artifacts in the Judge stage;
- synthesizing conditional conclusions;
- composing concise Markdown reports from canonical session data; and
- supporting iterative Continue Reasoning sessions focused on recorded gaps.

The application orchestrates multiple GPT-5.6 stages with structured JSON
artifacts instead of relying on one prompt. Perplexity Sonar is used only for
the Evidence stage. Thesision accepts an evidence URL only when it was returned
in Sonar search results or citations, preventing the reasoning model from
presenting recalled URLs as grounded sources.

## How Codex Was Used

Codex was an implementation collaborator throughout the project. It
accelerated:

- orchestrator-first backend structure and regression tests;
- TypeScript migration and modular frontend refactoring;
- constellation graph layout, animation, sidebar, popup, replay, and session
  continuation interactions;
- RFC-driven design and architecture documentation;
- Render deployment configuration and health checks;
- Judge/Conflict output validation, source-grounding safeguards, and Markdown
  report improvements; and
- debugging, documentation, and final submission preparation.

Human decisions remained responsible for the product direction, reasoning
architecture, acceptance criteria, and final implementation choices.

## Run Locally

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

Configure `.env` with one API key:

```dotenv
AI_PROVIDER=aimlapi
AIMLAPI_API_KEY=your-key
AIMLAPI_MODEL=openai/gpt-5.6-luna
AIMLAPI_EVIDENCE_MODEL=perplexity/sonar
```

Build and run:

```powershell
npm run build:frontend
uvicorn src.backend.app.main:app --reload
```

Open `http://127.0.0.1:8000`.

### Verify

```powershell
.\.venv\Scripts\python.exe -m pytest -q
npm run typecheck:frontend
npm run build:frontend
```

The test suite uses a fake model and does not spend API credits.

## Deployment and Judge Testing

The public demo runs at [thesision.onrender.com](https://thesision.onrender.com).
No login is required.

1. Open the live demo. A free Render instance can take about a minute to wake.
2. Enter an engineering decision question and select **Start Reasoning**.
3. Inspect Evidence, Conflict, and Judge nodes; open an evidence source link.
4. Export the completed session as Markdown or JSON.
5. Optionally import the JSON and select **Continue Reasoning** to investigate
   the highest-priority recorded gap in the imported session.

`render.yaml` defines the Docker deployment. Set `AIMLAPI_API_KEY` as the only
secret when creating the Render Blueprint. Render free-tier storage is
ephemeral, so JSON export/import provides a portable session backup.

## Project Structure

```text
src/
├── backend/
│   ├── agents/          # Hypothesis, Evidence, Perspective, Judge, Conclusion
│   ├── app/             # FastAPI routes and application entry point
│   ├── orchestrator/    # Reasoning lifecycle coordination
│   ├── services/        # Provider clients and export generation
│   └── state/           # SQLite-backed session storage
└── frontend/
    └── app/             # TypeScript graph workspace and UI modules

docs/                    # Product, architecture, RFCs, and demo guidance
tests/                   # Backend and integration regression coverage
```

## Roadmap

- Broader evidence-source coverage and stronger source diversity
- Confidence calibration from richer recorded signals
- PDF and paper ingestion
- Local knowledge-base support
- Collaborative reasoning sessions and decision history
- Graph comparison across related sessions

## License

License selection is pending. Add a license file before any use beyond hackathon
evaluation.
