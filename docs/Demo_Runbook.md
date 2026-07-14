# Demo Runbook

## Purpose

Use this short flow to demonstrate Thesision as a transparent engineering reasoning workspace rather than a chatbot.

## Setup

1. Copy `.env.example` to `.env`.
2. Set `OPENAI_API_KEY` in `.env`.
3. Install dependencies with `pip install -r requirements.txt`.
4. Run `uvicorn src.backend.app.main:app --reload`.

## Demo Flow

1. Open the workspace at `http://127.0.0.1:8000`.
2. Enter: `Should I migrate my backend from FastAPI to Go?`
3. Add context such as current workload, team expertise, and latency constraints.
4. Start reasoning and narrate the visible stage-based progress.
5. Inspect the graph nodes to show hypotheses, evidence, perspectives, the judge, and confidence.
6. Open evidence references in the right panel.
7. Export the completed session as Markdown and JSON.

## Expected Takeaway

The user sees the evidence, trade-offs, confidence, and conclusion that support an engineering decision. The final decision remains with the human.
