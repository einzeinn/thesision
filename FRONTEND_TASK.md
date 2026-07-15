# Frontend TypeScript Migration Plan

> Status: in progress — Stage 1 tooling foundation completed; runtime migration has not started.

## Objective

Migrate the current browser frontend from plain JavaScript to TypeScript
without changing backend contracts, session lifecycle behavior, graph
semantics, visual language, or documented MVP scope.

## Current Frontend Scope

- `src/frontend/app/index.html` provides the application shell and inline styles.
- `src/frontend/app/app.js` contains session interaction, graph rendering,
  animation, sidebar behavior, popups, exports, and accessibility handling.
- The backend serves the static frontend and remains out of scope for this task.

## Migration Tasks

1. Decide the minimal TypeScript build strategy compatible with the existing
   FastAPI static-file serving arrangement.
2. Add TypeScript configuration (strict: true, noUncheckedIndexedAccess: true)
   and a reproducible frontend build command with a dev-mode watch script.
3. Rename and migrate app.js to app.ts without changing runtime behavior.
4. Split app.ts into modules (graph.ts, popup.ts, sidebar.ts, export.ts,
   types.ts) along existing functional boundaries — no behavior change,
   pure reorganization.
5. Define local TypeScript types for the session payload, reasoning nodes
   (as a discriminated union keyed on `type`), graph edges, satellites, and
   popup state. Add an assertNever() exhaustiveness helper and use it
   everywhere the code currently switches or looks up by node type.
6. Type DOM lookups and event handlers safely, including keyboard and
   reduced-motion paths.
7. Type the D3 and anime.js integration boundaries without changing their
   current force, animation, or reveal behavior. Add @types/d3 via npm;
   write a minimal ambient .d.ts for the window.anime global (loaded via
   CDN, not npm) covering only the API surface actually used.
8. Extract the inline <style> block from index.html into a separate
   styles.css, imported through the Vite build. No visual changes.
9. Update index.html to load only the generated browser asset.
10. Add a type-check/build verification step, retain the existing backend
    regression suite, and run a manual frontend parity checklist (submit
    a question, confirm graph render, node click/popup, sidebar collapse,
    export, and replay all behave identically to pre-migration) before
    marking migration complete.
11. Update relevant documentation and the phase report only after the
    migration has been verified.

## Completed Stage 1

- Added an isolated TypeScript project configuration and reproducible frontend
  type-check command.
- Added a migration anchor file only; `app.js` and `index.html` remain the
  active runtime frontend and have not been renamed, removed, or rewired.
- Added ignore rules for frontend dependencies and future generated assets.

## Completed Stage 2

- Enabled `noUncheckedIndexedAccess` alongside strict TypeScript checking.
- Added `npm run watch:frontend` for development-time type checking.
- Kept the active browser runtime unchanged; `app.js` and `index.html` still
  serve the application exactly as before.

## Stage 3–5 Foundation Completed

- Added `app.ts` as the TypeScript migration entrypoint while retaining the
  proven `app.js` runtime as a compatibility bridge until the generated-asset
  stage. The full DOM/D3 application body remains intentionally in `app.js`
  until Stage 6–9 can type and serve it safely.
- Extracted typed graph-data, popup, sidebar, and export boundaries into
  `graph.ts`, `popup.ts`, `sidebar.ts`, and `export.ts`.
- Added discriminated reasoning-node, satellite, graph-edge, session, and
  popup-state types plus `assertNever()` for exhaustive node handling.

## Completed Stage 6-10

- Added Vite production build and watch scripts, `@types/d3`, and a minimal
  local anime.js ambient declaration for the existing CDN global.
- Extracted the source stylesheet to `styles.css`; Vite now emits the static
  CSS asset consumed by `index.html` alongside the generated JavaScript asset.
- Moved the active runtime source from `app.js` to `app.ts`; `index.html`
  loads only Vite-generated JavaScript and CSS assets plus the existing CDN
  libraries. The source HTML shell remains required by FastAPI and is not an
  unused file.
- Verified TypeScript checking, Vite production build, and the existing
  backend regression suite. Manual browser parity remains the final human
  verification before declaring the migration complete.

## Non-Goals

- No backend, API, orchestrator, persistence, or session-state changes.
- No UI redesign or graph-physics retuning.
- No framework migration unless separately requested.
- No feature additions while the TypeScript migration is in progress.

## Definition of Done

- Frontend builds and type-checks successfully from a clean install.
- The served application preserves the current user flows: sidebar collapse,
  progressive graph rendering, satellites, anchored popups, replay, exports,
  keyboard access, and reduced motion.
- Existing automated tests continue to pass.
- Generated files and dependencies are handled correctly by `.gitignore`.
