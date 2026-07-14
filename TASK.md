# Thesision MVP Implementation Plan

> Reason Before Decision.

This plan is derived from the repository documentation and is limited to the MVP only. It excludes all Future Features.

## MVP Scope

- Engineering-focused reasoning for software engineers and AI engineers.
- Orchestrator-first multi-agent reasoning pipeline.
- Interactive reasoning graph as the primary UI.
- Markdown export.
- JSON export.
- Session persistence using SQLite and JSON-backed reasoning state.
- Confidence-based stopping logic.

## Phase 0 Status

- Status: completed
- Outcome: MVP documentation alignment confirmed and recorded.
- Deliverables: Phase 0 report created, execution log initialized, and implementation direction locked.

## Phase 1 Status

- Status: completed
- Outcome: backend skeleton, session persistence, frontend shell, and the OpenAI integration boundary are implemented for the MVP request flow. The boundary fails explicitly when its environment configuration is absent; it never fabricates AI reasoning.
- Deliverables: FastAPI session API, SQLite-backed session store, structured pipeline state, simple reasoning workspace UI, OpenAI client configuration, and verified tests for session creation and progression.

## Phase 2 Status

- Status: completed
- Outcome: the Orchestrator coordinates every documented reasoning stage and persists its complete, inspectable session state.
- Deliverables: hypothesis, evidence, perspective, judge, confidence, and conclusion stages; confidence-based stop conditions; explicit provider errors; and automated pipeline tests.

## Phase 3 Status

- Status: completed
- Outcome: the reasoning workspace now renders an interactive, inspectable graph as its primary interface.
- Deliverables: three-panel workspace, graph nodes and edges, stage-aware confidence indicator, evidence references, node inspection, and reduced-motion control.

## Phase 4 Status

- Status: completed
- Outcome: completed reasoning sessions can be exported as Markdown reports or portable JSON without diverging from their persisted state.
- Deliverables: export generator, download endpoints, workspace export controls, and equality tests for JSON session exports.

## Phase 5 Status

- Status: implementation completed; demo video pending capture
- Outcome: the MVP has documented setup and demo guidance, clear workspace states, API input limits, protected exports, and regression coverage for core contracts.
- Deliverables: demo runbook, safe local environment configuration, loading/success/failure UI states, input validation, export guards, and hardening tests.

## Out of Scope

- Chatbot-style interface.
- PDF export.
- Auth, team collaboration, plugin systems, local models, multi-provider support, VS Code integration, replay timeline, mobile-first support, and other future items documented as deferred.

## Project Phases

### Phase 0: Documentation Alignment

Goal: lock the MVP interpretation before implementation starts.

Milestones:

- Confirm the MVP pipeline order.
- Confirm the UI contract for the three-panel layout.
- Confirm accepted storage choices.
- Confirm stop conditions and output formats.

### Phase 1: Foundation

Goal: establish the application skeleton and request flow.

Milestones:

- Frontend app shell exists.
- Backend API server exists.
- Frontend can send a question to the backend.
- Backend can create and persist a reasoning session.
- End-to-end API contract is defined.
- OpenAI integration is configured through environment variables and reports missing configuration explicitly.

### Phase 2: Orchestration and Reasoning Engine

Goal: implement the core reasoning workflow.

Milestones:

- Orchestrator coordinates all reasoning stages.
- Hypothesis generation works.
- Evidence retrieval works.
- Perspective analysis works.
- Judge stage works.
- Confidence evaluation works.
- Stop condition logic works.
- Reasoning state is persisted per session.

### Phase 3: Visualization

Goal: present reasoning as an inspectable graph instead of a chat log.

Milestones:

- Graph renders the reasoning pipeline.
- Nodes and edges reflect the current reasoning state.
- Node inspection reveals details, evidence, confidence, and references.
- Reasoning progress is visible through stage-based status indicators.

### Phase 4: Output Generation

Goal: make results reusable.

Milestones:

- Markdown export works.
- JSON export works.
- Exported data matches persisted reasoning state.

### Phase 5: Polish and Hardening

Goal: make the MVP stable enough for demonstration.

Milestones:

- Error handling is consistent.
- UI states are clear for loading, progress, empty, and failure cases.
- Basic tests cover core pipeline behavior and API contracts.
- Documentation matches implementation.

## Prioritized Tasks

### P0: Must Have

1. Define the API contract between frontend, backend, orchestrator, and persistence.
2. Create the backend application skeleton with FastAPI.
3. Create the frontend application shell with the documented three-panel layout.
4. Implement session creation and session state storage.
5. Implement the orchestrator and the reasoning pipeline order.
6. Implement hypothesis generation.
7. Implement evidence retrieval.
8. Implement perspective analysis.
9. Implement judge logic.
10. Implement confidence evaluation and stop conditions.
11. Render the reasoning graph.
12. Support Markdown export.
13. Support JSON export.

### P1: Should Have

1. Improve node detail panels for reasoning inspection.
2. Add clear progress states for each reasoning stage.
3. Add robust failure handling for partial pipeline failures.
4. Add tests for orchestration, persistence, and exports.

### P2: Nice to Have Within MVP Only if Time Remains

1. Refine graph animation timing.
2. Improve metadata presentation.
3. Add small usability improvements that do not alter scope.

## Dependencies Between Tasks

- The frontend shell depends on having a stable UI contract and route structure.
- The backend API depends on the session model and persistence shape.
- The orchestrator depends on the defined reasoning pipeline and stop conditions.
- Hypothesis generation depends on the question input schema.
- Evidence retrieval depends on the hypothesis output and evidence schema.
- Perspective analysis depends on the evidence output and the shared reasoning state.
- Judge logic depends on hypotheses, evidence, and perspectives being available in structured form.
- Confidence evaluation depends on judge output and unresolved conflict tracking.
- Graph rendering depends on the persisted reasoning state and stage metadata.
- Markdown and JSON exports depend on the final session state and node schema.
- Tests for exports and visualization depend on the output schemas being stable.

## Estimated Implementation Order

1. Documentation alignment and schema definition.
2. Backend scaffolding and persistence setup.
3. Frontend scaffolding and base layout.
4. API integration between frontend and backend.
5. Orchestrator implementation.
6. Hypothesis generator.
7. Evidence retrieval.
8. Perspective analysis.
9. Judge stage.
10. Confidence evaluation and stop logic.
11. Graph rendering and node inspection.
12. Markdown and JSON exports.
13. Error handling, tests, and polish.

## Risks

### Product Risks

- Scope creep can push the MVP toward Future Features.
- A chatbot-like UI would conflict with the documented product identity.
- Overbuilding export or persistence features could delay the core reasoning demo.

### Technical Risks

- AI output variability may cause inconsistent reasoning states.
- Evidence retrieval quality may be uneven without carefully structured sources.
- Multi-stage orchestration can become brittle if schemas are not tightly defined.
- Graph visualization can become complex if state transitions are not normalized early.
- Session persistence can drift from the in-memory reasoning model if the schema is not centralized.

### Delivery Risks

- The MVP can stall if frontend and backend contracts are not agreed up front.
- Visualization work can consume too much time if done before the pipeline is stable.
- Test coverage may lag if it is deferred until the end.

## Suggested Project Structure

This structure matches the documented architecture and keeps responsibilities small.

```text
docs/
src/
  frontend/
    app/
    components/
    graph/
    panels/
    exports/
  backend/
    api/
    orchestrator/
    agents/
    state/
    services/
    models/
    storage/
    tests/
  shared/
    schemas/
    types/
```

### Structure Notes

- `frontend` should only display reasoning results and manage user input.
- `backend/api` should expose request and session endpoints.
- `backend/orchestrator` should coordinate the reasoning pipeline.
- `backend/agents` should hold one-responsibility reasoning stages.
- `backend/state` should define the session and reasoning state model.
- `backend/storage` should handle SQLite and JSON persistence.
- `shared/schemas` should centralize the request and response contracts.

## Definition of Done for the MVP

- A user can submit one engineering question.
- The system runs the documented reasoning pipeline.
- The graph visualizes the reasoning process.
- The user can inspect reasoning steps, evidence, and confidence.
- The final output can be exported as Markdown and JSON.
- The session state persists correctly.
- The implementation matches the documentation.

## Implementation Rules

Every phase must:

- compile
- run
- keep previous functionality working
- update TASK.md
- generate PHASE_REPORT.md
- stop after completion
