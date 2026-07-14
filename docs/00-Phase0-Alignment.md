# 00 - Phase 0 Alignment

# Thesision

> Reason Before Decision.

---

# Purpose

This document records the MVP alignment decisions confirmed during Phase 0.

It exists to keep the implementation phase anchored to the documented scope before any code is written.

---

# Confirmed MVP Scope

- Engineering-focused reasoning for software engineers and AI engineers.
- Orchestrator-first multi-agent reasoning pipeline.
- Interactive reasoning graph as the primary UI.
- Markdown export.
- JSON export.
- Session persistence with SQLite and JSON-backed reasoning state.
- Confidence-based stop conditions.

---

# Confirmed Pipeline Order

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

The orchestrator may repeat the reasoning loop when confidence is insufficient or major conflicts remain unresolved.

---

# Confirmed UI Contract

- The UI must not resemble a chatbot.
- The graph is the primary interface.
- The layout follows the documented three-panel structure:
  - Left: input and session controls.
  - Center: interactive reasoning graph.
  - Right: evidence, node details, exports, and metadata.
- Users should inspect reasoning, evidence, confidence, and references directly from graph nodes or details panels.

---

# Confirmed Output Contract

- Markdown export is in scope for the MVP.
- JSON export is in scope for the MVP.
- PDF export is excluded from the MVP.

---

# Confirmed Storage Direction

- SQLite is the accepted MVP persistence layer.
- JSON is the accepted reasoning-state format.
- Session state must survive beyond a single request.

---

# Confirmed Stop Conditions

Reasoning stops when:

- confidence reaches the documented threshold and major conflicts are resolved, or
- the maximum reasoning iteration budget is reached.

---

# Confirmed Exclusions

- Chatbot-style conversation UI.
- PDF export.
- Authentication.
- Team collaboration.
- Plugin systems.
- Local models.
- Multi-provider support.
- VS Code integration.
- Replay timeline.
- Mobile-first support.
- Any other future-only features documented in the repo.

---

# Documentation Cleanup

- `AGENTS.md` now references `docs/AIInstructions.md`, which matches the actual repository file.

