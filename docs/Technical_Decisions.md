# 07 - Technical Decisions

# Thesision

> Reason Before Decision.

---

# Overview

This document records the major engineering decisions made during the development of Thesision.

The purpose is to preserve architectural consistency and avoid repeatedly debating previously resolved decisions.

---

# Decision 01

## AI is the Core Product

Status

Accepted

Reason

Thesision cannot function without AI reasoning.

AI is responsible for:

- hypothesis generation
- evidence analysis
- perspective evaluation
- synthesis
- conclusion

AI is not an optional enhancement.

---

# Decision 02

## Orchestrator First Architecture

Status

Accepted

Reason

All AI agents communicate only through the Orchestrator.

Benefits

- easier maintenance
- modular architecture
- simple debugging
- easier future expansion

Rejected Alternative

Direct communication between agents.

Reason

Creates unnecessary complexity and tighter coupling.

---

# Decision 03

## Prompt Engineering is Invisible

Status

Accepted

Reason

Users should never need to write complex prompts.

Users only provide:

- question
- optional context

Everything else is generated internally.

Benefits

- lower cognitive load
- consistent outputs
- better user experience

---

# Decision 04

## Engineering Domain Only

Status

Accepted

Reason

A focused MVP is more valuable than supporting many domains poorly.

Future domains belong to future releases.

---

# Decision 05

## Graph Instead of Chat

Status

Accepted

Reason

Traditional chat interfaces hide reasoning.

Graph visualization exposes reasoning evolution.

Benefits

- transparency
- explainability
- easier exploration

---

# Decision 06

## Confidence-Based Stopping

Status

Accepted

Reason

Reasoning stops when:

- confidence ≥ 90%

AND

- major conflicts resolved

OR

- maximum iterations reached

Reason

Avoids endless reasoning loops.

---

# Decision 07

## Multiple Perspectives

Status

Accepted

Reason

Engineering problems rarely have one perfect answer.

Perspective agents represent different engineering priorities instead of absolute agreement or disagreement.

Examples

- maintainability
- scalability
- performance
- simplicity

---

# Decision 08

## Structured Outputs

Status

Accepted

Reason

Results should remain reusable.

Supported outputs

- Markdown
- JSON

Future

- PDF

---

# Decision 09

## Modular Agent Design

Status

Accepted

Reason

Every reasoning agent should have exactly one responsibility.

Benefits

- maintainability
- scalability
- testing

---

# Decision 10

## Human Decision Remains Final

Status

Accepted

Reason

Thesision assists reasoning.

It never replaces engineering judgment.

Users remain responsible for final decisions.

# Decision 11

## Promptless Experience

Status

Accepted

Reason

Users should interact through decisions, not prompt engineering.

Whenever possible, Thesision converts user selections into structured AI instructions internally.

The application owns the prompting strategy.

Users own the problem they want to solve.

Benefits

- consistent reasoning
- lower token waste
- better onboarding
- less prompt engineering knowledge required

---

# Deferred Decisions

The following decisions are intentionally postponed.

- Authentication
- Team Collaboration
- Local Models
- Plugin Marketplace
- VS Code Extension
- Multi Provider Support
- Cloud Synchronization

These are outside the MVP scope.

---

# Decision Policy

Every new architectural decision should answer:

1. Does it improve reasoning quality?
2. Does it improve transparency?
3. Can it remain modular?
4. Can it be implemented within the MVP?

If the answer is mostly "No",

the feature should move to Future Features.