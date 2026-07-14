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
pip install fastapi uvicorn pytest httpx
```

### Run the backend

Set the OpenAI key in the current PowerShell session before running reasoning:

```powershell
$env:OPENAI_API_KEY = "your-key"
# Optional: $env:OPENAI_MODEL = "gpt-4.1-mini"
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
