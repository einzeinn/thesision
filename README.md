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

Configure one provider in `.env` before running reasoning. AI/ML API is supported through its OpenAI-compatible chat-completions endpoint:

```powershell
$env:AI_PROVIDER = "aimlapi"
$env:AIMLAPI_API_KEY = "your-key"
# Optional: $env:AIMLAPI_MODEL = "gpt-4o"
```

```powershell
uvicorn src.backend.app.main:app --reload
```

### Run tests

```powershell
pytest -q
```

## Project Principles

- Reasoning first, not chatbot-first.
- Secrets must be provided via environment variables.
- The architecture remains modular and orchestrator-first.
