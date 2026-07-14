# 13 - Design

# Thesision

> Reason Before Decision.

---

# Purpose

This document defines the visual identity and interaction principles of Thesision.

Its purpose is to ensure that every UI implementation remains consistent with the product philosophy.

The interface should communicate reasoning, not conversation.

---

# Core Principle

Thesision is NOT a chatbot.

The interface should never resemble:

- ChatGPT
- Claude
- Gemini
- WhatsApp
- Discord
- Slack

Reasoning should be visualized, not hidden inside messages.

---

# Design Philosophy

Minimal

Clean

Focused

Scientific

Interactive

Transparent

The UI should feel like observing a thinking machine rather than chatting with one.

---

# Visual Identity

Keywords

- Neural Network
- Knowledge Graph
- Digital Laboratory
- Blueprint
- Research Workspace

Avoid

- Social media aesthetics
- Chat bubbles
- Large assistant avatars
- Cartoon illustrations

---

# Layout

Three-panel layout.

Left

Input and session controls.

Center

Interactive reasoning graph.

Right

Evidence, node details, exports, and metadata.

## Initial state

Before a question is submitted, the interface should show almost nothing:

- Center: a single Question bubble, empty, centered, waiting for input. This is the only node visible.
- Left panel: the question input field and the Reason button. Treat it like a collapsed sidebar — minimal, no progress list, no session history taking up space, since there's nothing to show yet.
- Right panel: hidden or collapsed. Nothing to inspect yet, so don't show an empty panel.

This matters because the "growing" animation only reads as growth if the starting point is nearly bare. If the full three-panel chrome is already busy before reasoning starts, the graph appearing afterward doesn't feel like emergence — it feels like a section filling in.

## After clicking Reason

- The Question bubble the user just filled in stays in place (it becomes the round-0 center node).
- The left panel's progress list appears (Building hypothesis… / Searching evidence… / etc., as in Progress below) — this is when the collapsed sidebar expands.
- Nodes and links begin appearing one at a time, staggered, exactly as described in Graph Behavior and Center Workspace.
- The right panel stays hidden until there's something to show it (see Interaction).

---

# Center Workspace

The graph is the heart of the application.

Everything should visually grow from the user's question.

The graph is NOT a fixed flowchart. It is a constrained force-directed layout that grows organically during reasoning, expanding radially outward from the Question node without sacrificing the readable reasoning order.

Implementation: `d3-force` (or equivalent physics simulation library).

- `forceLink` — draws each connection.
- `forceManyBody` — repels nodes so they don't overlap.
- `forceRadial(round * R, centerX, centerY)` — pulls each node to a radius proportional to its debate round. This single force is what produces the "growing outward" feeling: round 1 sits close to the Question, round 3 sits further out.
- `forceCollide` — prevents node overlap as the graph settles.
- `forceX` / `forceY` — pull each node type toward a stable clockwise lane, keeping flow connections short and readable.

Nodes gradually connect together until they resemble a neural network. This is a direct consequence of round count, not a separate visual effect:

- 1 round, debate resolved immediately → small, sparse shape (Question + one shell of Hypothesis / Evidence / Perspectives / Conflict / Judge + Conclusion).
- 3 rounds, debate escalates fully → dense, many-node structure that visually reads as a neural network, because each round adds a full shell of nodes plus cross-round connections.

Maximum debate length is 3 rounds. The backend/agent decides how many rounds occur (a round ends early once Judge marks the debate resolved); the frontend only renders however many rounds it's given.

---

# Graph Data Model

Every node carries:

- `id`
- `type` — question / hypothesis / evidence / perspective / conflict / judge / conclusion
- `round` — 0 for Question, 1–3 for debate rounds, round + 1 for Conclusion
- `threadId` (future) — which topic/argument line this node belongs to, for sessions with more than one parallel hypothesis

Every connection carries a `kind`:

- `flow` — the normal reasoning sequence within a round (Question → Hypothesis → Evidence → Perspectives → Conflict → Judge → Conclusion). Solid line, colored by the node type it points to.
- `continuation` — from one round's Judge to the next round's Hypothesis. Solid line, same color rule as `flow`.
- `thread` — connects a node to the same-type node in the adjacent round (e.g. Perspective round 1 → Perspective round 2), showing that the same argument line is continuing rather than a new one starting. Dashed line, neutral/gray, thinner and lower-opacity than `flow`/`continuation` lines.

If a session ever supports multiple parallel hypotheses, `thread` links should key off `threadId` instead of `type`, so cross-links track the actual argument line rather than just the node category.

---

# Graph Behavior

Connections should grow instead of appearing instantly:

- Nodes fade in with a staggered delay (small, incremental delay per node — not simultaneous). Reveal animation must never overwrite the SVG transform that stores a node's settled position.
- Links fade in independently, staggered slightly ahead of or alongside the nodes they connect.
- On mount, the simulation should already be settled (run enough ticks server-side or synchronously before first paint) so nodes don't visibly jitter into place — only the fade/stagger reveal should be visible, not the physics settling.

---

# Animations

Use subtle motion.

Animation library: anime.js.

Recommended

- fade
- opacity-only reveal for positioned graph nodes
- line drawing (animate `stroke-dashoffset` on connection paths for a "being drawn" feel)
- staggered reveal (`anime.stagger()`) for both nodes and links when a new round of reasoning appears
- smooth expand/collapse (animate `height` from `0` to measured content height, then set to `auto` on completion so it stays responsive to dynamic content)

Timing: keep durations short, roughly 350–550ms, easing `easeOutQuad` / `easeInOutQuad`. Nothing should feel slow or springy.

Avoid

- excessive bouncing
- flashy transitions
- distracting effects

Animations should communicate thinking.

---

# Node Types

Question

Hypothesis

Evidence

Perspective

Conflict

Judge

Conclusion

Every node type should have a unique visual identity, carried primarily through color (see Color Philosophy), not through shape.

Visual style is line-art, not filled illustration: thin strokes (around 1px), minimal or no fill, flat and technical — closer to a schematic than a rendered chat bubble. Reference aesthetic: anime.js's own site (animejs.com) — monochrome line drawing, small mono-spaced labels, thin connecting lines.

All graph nodes render as circles in every graph state (color = type). Question and Conclusion render larger than the rest, since they are the anchors of the whole structure. Cards must not be used as graph nodes because they visually detach a node from its connecting edges.

---

# Color Philosophy

Use color to represent meaning.

Example

Blue

Evidence

Green

Validated reasoning

Yellow

Hypothesis

Orange

Alternative perspective

Red

Conflict

Purple

Final conclusion

The exact color palette may change.

The semantic meaning should remain.

Reference implementation values (adjust to taste, keep the mapping):

- Evidence — blue `#185FA5`
- Judge / validated reasoning — green `#3B6D11`
- Hypothesis — amber `#BA7517`
- Perspective (supporting and alternative both use this color; do not give them different colors, they are the same node type) — coral `#993C1D`
- Conflict — red `#A32D2D`
- Conclusion — purple `#534AB7`
- Question and other neutral/structural elements — gray `#5F5E5A`

Given the line-art direction: color shows up as thin strokes, small accent bars, and filled circles/dots — never as large filled blocks or backgrounds. Color marks meaning, it doesn't paint the UI.

---

# Background

The workspace should feel technical.

Possible inspirations

- engineering blueprint
- subtle grid
- research board
- animejs.com's own marketing page (thin line-art diagram, monospace labels, muted paper-like neutral background, no color noise outside the diagram itself)

Avoid empty white space.

Avoid decorative backgrounds.

Avoid gradients, shadows, and glow — the technical feeling comes from thin strokes and grid structure, not from depth effects.

---

# Typography

Readable.

Minimal.

No decorative fonts.

Hierarchy should clearly separate:

- reasoning
- evidence
- metadata

---

# Interaction

Clicking a node opens its details. Users can inspect:

- reasoning
- evidence
- confidence
- references

Nothing should feel hidden.

Clicking any circle surfaces its details in a lightweight info strip anchored to the graph — type, round, and a one-line reasoning summary. Multiple nodes can be inspected in sequence without the graph re-laying itself out. The right-hand panel from the original three-panel layout still exists for evidence/exports/metadata at the session level, but per-node reasoning lives in the info strip, not the right panel — the right panel would be too far from the node to feel connected to it.

---

# Progress

Do not display

"AI is typing..."

Instead display

Building hypothesis...

Searching evidence...

Evaluating perspectives...

Resolving conflicts...

Synthesizing conclusion...

The system should communicate reasoning progress.

---

# Reasoning Replay

When reasoning finishes (Conclusion node has appeared), show a Replay control near the graph.

Replay rebuilds the graph from scratch, gradually, node by node and link by link — the same staggered growth animation used the first time, not an instant redraw. This reuses the exact animation logic from initial generation; replay is not a separate system, it's the same reveal sequence played again on already-known data.

This ships as part of the core completion state, not deferred to a later version — it's one of the two actions available once a debate resolves (the other is Export).

---

# Export

Users can export

Markdown

JSON

Future

PDF

Export becomes available at the same moment as Replay — once the Conclusion node appears. Before that, there's nothing finished to export, so don't show the controls yet.

---

# Responsive Design

Desktop is the primary target.

Tablet support is optional.

Mobile support belongs to future versions.

---

# Accessibility

Animations should never block interaction.

Users should be able to disable animations.

High contrast should remain readable.

---

# Inspiration

Research tools

Knowledge graphs

Engineering dashboards

Scientific visualization

NOT chat applications.

---

# Design Rules

If a UI element makes Thesision feel like a chatbot,

remove it.

If a visualization improves reasoning transparency,

keep it.

Every screen should answer one question:

"Can users understand how the AI reached this conclusion?"
