# Thesision

Thesision is an AI reasoning platform focused on transparent, evidence-driven reasoning for software engineers.

## Overview

This project implements an orchestrator-first reasoning workflow with:

- a FastAPI backend,
- SQLite-backed session persistence,
- a lightweight reasoning workspace UI,
- and a structured reasoning state for future orchestration stages.

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

### Run the backend

Configure OpenAI in `.env` before running reasoning. The Evidence stage uses OpenAI hosted web search and only retains URLs returned as search citations:

```powershell
$env:AI_PROVIDER = "openai"
$env:OPENAI_API_KEY = "your-key"
# Optional: $env:OPENAI_MODEL = "gpt-4.1-mini"
```

AI/ML API remains available for non-grounded reasoning stages, but it is deliberately rejected for Evidence retrieval until equivalent hosted-search support is verified.

```powershell
uvicorn src.backend.app.main:app --reload
```

### Run tests

```powershell
pytest -q
```

## Deployment with Docker

1. Copy .env.example to .env and set provider credentials. OpenAI is the
   recommended production provider because it can ground Evidence with hosted
   web search. AI/ML API defaults to openai/gpt-5.6-luna for reasoning, but
   does not provide verified evidence URLs until search compatibility is proven.
2. Build with: docker build -t thesision .
3. Run with persistent sessions:
   docker run --env-file .env -p 8000:8000 -v thesision-data:/app/data thesision
4. Verify readiness at http://127.0.0.1:8000/health/ready.
5. Open http://127.0.0.1:8000.

## Deployment on Render Free

This repository includes render.yaml and deploys as a Docker web service, so
the frontend build is created inside the image. In Render, create the Blueprint
from this repository and enter AIMLAPI_API_KEY as the only required secret.
The service uses openai/gpt-5.6-luna through AI/ML API.

Render free storage is ephemeral. Sessions and SQLite data can disappear after
a restart or a free-tier spin-down, so this target is appropriate for demos,
not durable session history. The service health check is /health/live.

For production evidence URLs that are verified by hosted web search, override
the Blueprint variables with AI_PROVIDER=openai and set OPENAI_API_KEY. The
AI/ML model path continues reasoning but explicitly marks evidence as
unverified when grounded web search is unavailable.

Render sits behind a managed proxy, so the Blueprint enables
TRUST_PROXY_HEADERS=true for per-client rate limiting. Keep that setting false
outside a trusted proxy; otherwise clients can spoof forwarded IP headers.

## Project Principles

- Reasoning first, not chatbot-first.
- Secrets must be provided via environment variables.
- The architecture remains modular and orchestrator-first.
