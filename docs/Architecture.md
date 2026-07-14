# 06 - Architecture

# Thesision

> Reason Before Decision.

---

# Overview

Thesision is built around an orchestration-first architecture.

Instead of sending one prompt to one model, every user request passes through multiple reasoning stages coordinated by an Orchestrator.

Each component has a single responsibility.

The architecture is designed to remain modular, explainable, and extensible.

---

# High Level Architecture

User

↓

Frontend

↓

API

↓

Orchestrator

↓

Reasoning Pipeline

↓

Outputs

---

# System Components

## Frontend

Responsibilities

- Collect user questions
- Display reasoning graph
- Show evidence
- Render final conclusion
- Export Markdown
- Export JSON

The frontend never performs reasoning.

---

## Backend API

Responsibilities

- Receive requests
- Manage sessions
- Trigger orchestration
- Store reasoning state
- Return structured outputs

---

## Orchestrator

The Orchestrator is the brain of the application.

Responsibilities

- Build reasoning pipeline
- Coordinate every AI agent
- Track reasoning progress
- Control iterations
- Manage confidence score
- Decide when reasoning stops

The Orchestrator is the only component allowed to communicate with every reasoning agent.

---

# Reasoning Pipeline

Question

↓

Hypothesis Generator

↓

Evidence Retrieval

↓

Perspective Analysis

↓

Judge

↓

Confidence Evaluation

↓

Need Another Round?

↓

Yes

↓

Repeat

↓

No

↓

Conclusion

---

# AI Agents

## Hypothesis Generator

Purpose

Generate possible explanations before evidence collection begins.

Output

- hypotheses
- assumptions
- unknown variables

---

## Evidence Retrieval

Purpose

Collect reliable engineering references.

Possible sources

- Official Documentation
- GitHub
- RFCs
- Technical Articles
- Stack Overflow

Future

Academic papers.

---

## Perspective Agent

Purpose

Evaluate engineering trade-offs.

Example

Perspective A

Prioritizes performance.

Perspective B

Prioritizes maintainability.

Perspective C

Prioritizes scalability.

Agents represent different engineering viewpoints.

Not simply "correct" vs "incorrect".

---

## Judge

Purpose

Compare reasoning quality.

Responsibilities

- detect contradictions
- remove weak claims
- identify unsupported arguments
- merge compatible reasoning

---

## Confidence Evaluator

Purpose

Estimate reasoning confidence.

Inputs

- evidence quality
- agreement level
- unresolved conflicts
- reasoning consistency

Output

Confidence Score

0–100

---

# State Manager

Stores reasoning progress.

Responsibilities

- current iteration
- graph state
- evidence
- agent outputs
- confidence score

Supports continuation in future sessions.

---

# Output Generator

Produces

- Interactive Graph
- Markdown
- JSON

Future

PDF.

---

# Data Flow

User

↓

API

↓

Orchestrator

↓

Hypothesis

↓

Evidence

↓

Perspectives

↓

Judge

↓

Confidence

↓

Conclusion

↓

Frontend

---

# Design Principles

Single Responsibility

Every module has one purpose.

Loose Coupling

Agents should remain independent.

Extensibility

New reasoning agents can be added later.

Transparency

Every important reasoning step is observable.

Maintainability

Business logic remains inside the backend.

---

# Technology Direction

Frontend

React

Next.js

React Flow

Anime.js

Backend

Python

FastAPI

Reasoning

OpenAI GPT Models

Storage

JSON

SQLite (MVP)

Future

PostgreSQL

Supabase

---

# Future Architecture

Future versions may introduce

- Memory Layer
- Plugin System
- Local Models
- Team Collaboration
- Distributed Agent Execution
- Multiple Model Providers

These components are intentionally excluded from the MVP.