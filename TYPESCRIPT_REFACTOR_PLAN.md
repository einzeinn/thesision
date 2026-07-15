# Strict TypeScript Runtime Refactor Plan

> Status: planned. Execute one stage at a time and do not advance until its
> verification commands pass.

## Objective

Replace the temporary `@ts-nocheck` runtime bridge in `src/frontend/app/app.ts`
with genuinely strict TypeScript while preserving the existing frontend behavior
and frontend/backend contract.

## Guardrails

- Keep `strict` and `noUncheckedIndexedAccess` enabled.
- Do not use `@ts-nocheck`, `@ts-ignore`, or `any` casts to bypass errors.
- Preserve force values, animation timing, styling, API routes, and session
  lifecycle behavior.
- `index.html` remains required because FastAPI serves it as the document shell.
- Do not change more than one runtime responsibility per stage.

## Baseline Commands

Run before and after every stage:

```powershell
npm run typecheck:frontend
npm run build:frontend
.\.venv\Scripts\python.exe -m pytest -q
```

## Stage 0 — Baseline and Boundary Inventory

1. Record the current type errors after temporarily auditing `app.ts` without
   suppression; do not commit a broken intermediate state.
2. List each runtime responsibility currently duplicated in `app.ts`:
   DOM bootstrap, graph rendering, popup interaction, sidebar control, exports,
   polling, and form orchestration.
3. Confirm the current browser behavior manually before changing code.

**Exit condition:** error categories and module ownership are documented.

### Stage 0 Record — Completed

- Strict audit categories are confirmed: DOM nullability/event narrowing,
  untyped application state, untyped D3 simulation data, popup/graph geometry,
  and `unknown` API error handling.
- `app.ts` currently owns all runtime responsibilities. The target ownership is:
  `sidebar.ts` (collapse), `export.ts` (downloads), `popup.ts` (labels and
  persistent/transient popups), `graph.ts` (graph data and rendering), and
  `app.ts` (DOM bootstrap, polling, session orchestration, and panels).
- The only suppression directive is the temporary `@ts-nocheck` in `app.ts`;
  it remains in place until Stage 5 prevents an intentionally broken build
  between staged refactors.

## Stage 1 — Typed DOM and Runtime Primitives

1. Add a fail-fast `requireElement<T>()` helper for all DOM references.
2. Add typed application state: active session, active ID, graph signature,
   revealed nodes, and popup state.
3. Define narrow browser-global declarations for the actual D3/anime surface.
4. Remove only DOM/nullability and event-type errors; leave rendering logic in
   place for this stage.

**Exit condition:** app bootstrap has no nullable DOM or implicit-state errors.

## Stage 2 — Sidebar and Export Wiring

1. Make `sidebar.ts` the only implementation of collapse/toggle behavior.
2. Make `export.ts` the only implementation of export download behavior.
3. Replace corresponding inline functions/event wiring in `app.ts` with imports.

**Exit condition:** sidebar toggle, automatic collapse, and both exports retain
their behavior; typecheck/build/tests pass.

## Stage 3 — Popup Module Completion

1. Move popup positioning, persistent popup, transient reveal popup, label
   placement, and popup cleanup into `popup.ts`.
2. Keep popup accessibility and click/keyboard semantics unchanged.
3. Remove all popup and label rendering implementations from `app.ts`.

**Exit condition:** node click, repeated click close, empty-space close, hover
label, keyboard activation, and auto-popup reveal work identically.

### Stage 3 Record — Completed

- `popup.ts` is now the sole owner of label placement, persistent/transient
  popup rendering, positioning, cleanup, and accessibility announcements.
- The inactive inline popup implementation was removed from `app.ts`; its
  remaining calls are thin delegates to the popup controller.
- The user manually verified the rendered behavior before this cleanup.

## Stage 4 — Graph Renderer Completion

1. Move SVG creation, D3 simulation, edge drawing, node rendering, satellite
   nodes, and animation scheduling into `graph.ts`.
2. Use the existing discriminated node union and `assertNever()` for node
   labels, summaries, radii, and satellite behavior.
3. Keep simulation values and animation durations exactly unchanged.

**Exit condition:** no graph-building/rendering implementation remains in
`app.ts`; one- and three-round graphs retain visual parity.

## Stage 5 — App Orchestration and Strict Gate

1. Reduce `app.ts` to typed DOM setup, module construction, polling, progress,
   form orchestration, replay, and session-level panel updates.
2. Remove `@ts-nocheck` permanently only when all strict errors are resolved.
3. Confirm each module is imported by the active runtime and no duplicate
   implementation remains.

**Exit condition:** zero TypeScript errors with no suppression directives.

## Stage 6 — Manual Parity and Handoff

1. Run the baseline commands.
2. Manually verify submit, progressive graph, satellites, node popup, sidebar,
   replay, exports, keyboard interaction, and reduced motion.
3. Update `FRONTEND_TASK.md` and phase documentation with evidence only after
   all checks pass.
4. Commit and push only after user approval or an explicit request to publish.

## Rollback Rule

If a stage changes visible behavior or fails its verification, revert only that
stage's uncommitted edits using a targeted patch, then fix the type boundary
before continuing. Never reset unrelated project history.
