# 14 - AI Instructions

# Thesision

> Instructions for AI Coding Agents

---

# Purpose

This document defines the rules that every AI coding agent must follow while contributing to Thesision.

These instructions apply to Codex, Claude Code, GPT, and any future coding agents.

The goal is to maintain architectural consistency, code quality, and documentation integrity.

---

# Rule 1

Read Before Coding

Before writing any code, read every document inside the /docs directory.

Never make implementation decisions based on assumptions.

Documentation is the source of truth.

---

# Rule 2

Documentation Has Priority

If implementation conflicts with documentation,

documentation wins.

If documentation is incorrect,

update the documentation first,

then update the implementation.

---

# Rule 3

Do Not Change Architecture

Never redesign the system architecture without explicit approval.

The Orchestrator-first architecture is mandatory.

---

# Rule 4

Respect MVP

Always prioritize MVP.

If a requested feature belongs to Future Features,

do not implement it unless explicitly instructed.

---

# Rule 5

No Hidden Features

Do not silently introduce:

- new services
- new databases
- new frameworks
- new APIs

Every architectural change must be documented.

---

# Rule 6

Keep Components Small

Every module should have one responsibility.

Avoid large files with multiple unrelated concerns.

---

# Rule 7

Frontend Rules

Never build a chatbot interface.

The UI must remain a reasoning visualization platform.

The graph is the primary interface.

---

# Rule 8

Backend Rules

Business logic belongs in the backend.

The frontend should only display reasoning results.

---

# Rule 9

Reasoning Pipeline

Maintain this order.

Question

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

Do not change the pipeline without documentation updates.

---

# Rule 10

Explainability First

Every reasoning output should remain inspectable.

Never hide important reasoning steps.

---

# Rule 11

Keep Prompting Internal

Users should never interact through prompt engineering.

The application owns prompt construction.

Users only describe the problem.

---

# Rule 12

Do Not Fake AI

Never create placeholder reasoning pretending to be AI-generated.

If AI is unavailable,

return an explicit error.

Never fabricate reasoning.

---

# Rule 13

Avoid Premature Optimization

Prefer readable code over clever code.

Optimization comes after correctness.

---

# Rule 14

Dependencies

Do not install additional dependencies unless necessary.

Always prefer existing project libraries.

---

# Rule 15

Code Quality

Write code that is:

- modular
- maintainable
- typed where appropriate
- documented
- testable

Avoid unnecessary abstraction.

---

# Rule 16

Comments

Explain why.

Not what.

Bad

Increment x by 1.

Good

Retry counter prevents infinite reasoning loops.

---

# Rule 17

Naming

Use descriptive names.

Avoid abbreviations.

Good

ReasoningPipeline

EvidenceRetriever

ConfidenceEvaluator

Bad

Pipe

Manager2

Helper

Util

---

# Rule 18

Error Handling

Every external operation should fail gracefully.

Never crash the reasoning pipeline because of one failed component.

---

# Rule 19

Future Features

If implementation ideas exceed MVP,

move them into documentation instead of implementing immediately.

---

# Rule 20

Project Philosophy

Always remember.

Thesision is NOT a chatbot.

Thesision is an AI reasoning platform.

Every implementation should reinforce this identity.

---

# Rule 21

Secrets Must Use Environment Variables

For Thesision, all secrets and sensitive configuration must be provided through environment variables.

Never hardcode:

- API keys
- tokens
- passwords
- private endpoints
- provider credentials

If a value is secret, it must be read from the environment at runtime.

This rule applies to local development, tests, and deployment configuration.

---

# Final Instruction

When uncertain,

stop coding,

re-read the documentation,

then continue.

Never guess.

Reason before implementation.