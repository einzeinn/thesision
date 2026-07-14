# 02 - Product Requirements Document

# Thesision

> Reason Before Decision.

---

# Overview

Thesision is an AI-native reasoning platform that helps software engineers solve complex technical questions through transparent, evidence-driven reasoning.

Unlike traditional AI assistants that directly generate answers, Thesision orchestrates multiple AI reasoning stages before producing a final conclusion.

The platform emphasizes explainability, confidence, and structured decision-making.

---

# Problem Statement

Modern LLMs are excellent at generating responses but poor at exposing their reasoning process.

This creates challenges for software engineers:

- Difficult to validate AI recommendations.
- Hidden assumptions.
- Limited confidence in important decisions.
- No structured evaluation of multiple perspectives.

Developers need reasoning, not just answers.

---

# Target Users

Primary

- Software Engineers
- AI Engineers

---

# Goals

The MVP should allow users to:

- Ask complex engineering questions.
- Generate an initial hypothesis.
- Gather supporting evidence.
- Evaluate multiple engineering perspectives.
- Resolve conflicts through iterative reasoning.
- Produce transparent conclusions.

---

# Non Goals

The MVP will NOT:

- generate production-ready code
- replace software engineers
- support every knowledge domain
- become a general chatbot

---

# User Journey

Step 1

User enters a technical question.

Example

Should I migrate my backend from FastAPI to Go?

---

Step 2

Thesision begins an autonomous reasoning workflow.

The user no longer needs to provide additional prompts.

---

Step 3

AI agents collaborate internally.

The workflow is invisible to the user.

---

Step 4

Evidence is collected and evaluated.

---

Step 5

Multiple perspectives are compared.

---

Step 6

The orchestrator determines whether another reasoning round is necessary.

---

Step 7

A transparent conclusion is generated.

---

# Core Workflow

Question

↓

Hypothesis Generator

↓

Evidence Retrieval

↓

Perspective Agent A

↓

Perspective Agent B

↓

Judge

↓

Confidence Evaluation

↓

Enough Confidence?

↓

YES → Final Conclusion

NO → Another Reasoning Round

---

# AI Agents

## Hypothesis Generator

Responsibilities

- understand the problem
- generate initial hypotheses
- identify unknowns

---

## Evidence Agent

Responsibilities

- retrieve relevant evidence
- identify supporting references
- estimate evidence quality

---

## Perspective Agents

Responsibilities

- evaluate the problem from different engineering viewpoints
- identify trade-offs
- challenge assumptions

Perspective agents are not strictly "pro" or "contra".

Each represents a realistic engineering perspective.

---

## Judge

Responsibilities

- synthesize arguments
- identify conflicts
- detect unsupported claims
- request additional reasoning when necessary

---

## Orchestrator

Responsibilities

- coordinate every agent
- manage reasoning rounds
- monitor confidence
- determine stop conditions

---

# Stop Conditions

Reasoning stops when:

- confidence ≥ 90%

AND

- no major unresolved conflict

OR

- maximum reasoning iterations reached

---

# Outputs

## Interactive Graph

Visual reasoning graph.

---

## Markdown Report

Human-readable reasoning report.

---

## JSON

Machine-readable reasoning state.

Designed for continuing future reasoning sessions.

---

# User Interface

The interface is NOT chat-based.

Instead, reasoning is visualized as a growing knowledge graph.

Nodes represent:

- hypotheses
- evidence
- perspectives
- conflicts
- conclusions

The graph gradually expands throughout the reasoning process.

The final visualization resembles a neural network.

---

# Design Principles

- Transparent
- Minimal
- Explainable
- Interactive
- Engineering-first

---

# MVP Scope

Included

- Software Engineering
- AI Engineering
- Multi-agent reasoning
- Graph visualization
- Markdown export
- JSON export

Excluded

- Scientific domains
- Medical reasoning
- Legal reasoning
- Team collaboration
- PDF export
- Plugin ecosystem

---

# Success Metrics

Users should:

- trust the reasoning process
- understand why conclusions are reached
- discover alternative perspectives
- reduce unnecessary prompt iteration

---

# Future Features

- Additional knowledge domains
- PDF paper generation
- Real-time collaboration
- Plugin system
- VS Code integration
- Local reasoning models
- Custom reasoning agents
- Replay reasoning timeline
- Interactive evidence explorer
- Knowledge graph persistence