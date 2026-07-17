import {
  assertNever,
  type EvidenceItem,
  type GraphData,
  type GraphEdge,
  type PerspectiveItem,
  type PositionedNode,
  type ReasoningNode,
  type SessionPayload,
} from "./types";

const flowOrder = [
  "hypothesis",
  "evidence",
  "perspective",
  "conflict",
  "judge",
] as const;
function normaliseNode(node: {
  id: string;
  type: string;
  round: number;
  data: unknown;
}): ReasoningNode | null {
  switch (node.type) {
    case "hypothesis":
      return {
        ...node,
        type: "hypothesis",
        data: node.data as { hypotheses?: Array<{ claim?: string }> },
      };
    case "evidence":
      return {
        ...node,
        type: "evidence",
        data: node.data as { evidence?: EvidenceItem[] },
      };
    case "perspective":
    case "perspectives":
      return {
        ...node,
        type: "perspective",
        data: node.data as { perspectives?: PerspectiveItem[] },
      };
    case "conflict":
      return {
        ...node,
        type: "conflict",
        data: node.data as { summary?: string; conflicts?: string[] },
      };
    case "judge":
      return {
        ...node,
        type: "judge",
        data: node.data as { synthesis?: string; conflict_summary?: string; validated_claims?: string[]; conflicts?: string[]; unresolved_conflicts?: string[] },
      };
    case "conclusion":
      return {
        ...node,
        type: "conclusion",
        data: node.data as { conclusion?: string },
      };
    case "confidence":
      return null;
    default:
      return null;
  }
}
function satellites(node: ReasoningNode): ReasoningNode[] {
  switch (node.type) {
    case "evidence":
      return (node.data.evidence || []).map((item, index) => ({
        ...node,
        id: `${node.id}-source-${index}`,
        type: "satellite",
        satellite: true,
        parentId: node.id,
        parentType: "evidence",
        data: item,
      }));
    case "perspective":
      return (node.data.perspectives || []).map((item, index) => ({
        ...node,
        id: `${node.id}-point-${index}`,
        type: "satellite",
        satellite: true,
        parentId: node.id,
        parentType: "perspective",
        data: item,
      }));
    case "question":
    case "hypothesis":
    case "conflict":
    case "judge":
    case "conclusion":
    case "satellite":
      return [];
    default:
      return assertNever(node);
  }
}
export function buildGraphData(session: SessionPayload): GraphData {
  const question: ReasoningNode = {
    id: "question-0",
    type: "question",
    round: 0,
    data: { question: session.question },
  };
  const primary = [
    question,
    ...(session.state.nodes || [])
      .map(normaliseNode)
      .filter((node): node is ReasoningNode => node !== null),
  ].sort((a, b) => a.round - b.round || a.id.localeCompare(b.id));
  const byRound = new Map<number, Map<string, ReasoningNode>>();
  primary.forEach((node) => {
    if (!byRound.has(node.round)) byRound.set(node.round, new Map());
    byRound.get(node.round)?.set(node.type, node);
  });
  const edges: GraphData["edges"] = [];
  const rounds = session.state.iteration || 1;
  for (let round = 1; round <= rounds; round += 1) {
    const current = byRound.get(round);
    const previous = byRound.get(round - 1);
    const hypothesis = current?.get("hypothesis");
    if (hypothesis)
      edges.push({
        source:
          round === 1 ? question.id : previous?.get("judge")?.id || question.id,
        target: hypothesis.id,
        kind: round === 1 ? "flow" : "continuation",
      });
    flowOrder.slice(1).forEach((type, index) => {
      const sourceType = flowOrder[index];
      if (!sourceType) return;
      const source = current?.get(sourceType);
      const target = current?.get(type);
      if (source && target)
        edges.push({ source: source.id, target: target.id, kind: "flow" });
    });
    if (previous)
      flowOrder.forEach((type) => {
        const source = previous.get(type);
        const target = current?.get(type);
        if (source && target)
          edges.push({ source: source.id, target: target.id, kind: "thread" });
      });
  }
  const conclusion = primary.find((node) => node.type === "conclusion");
  const judge = byRound.get(rounds)?.get("judge");
  if (conclusion && judge)
    edges.push({ source: judge.id, target: conclusion.id, kind: "flow" });
  const satelliteNodes = primary.flatMap(satellites);
  satelliteNodes.forEach((node) => {
    if (node.type === "satellite")
      edges.push({ source: node.parentId, target: node.id, kind: "satellite" });
  });
  return { nodes: [...primary, ...satelliteNodes], edges, rounds, layoutSeed: session.question };
}

const colors = {
  question: "#5F5E5A",
  hypothesis: "#BA7517",
  evidence: "#185FA5",
  perspective: "#993C1D",
  conflict: "#A32D2D",
  judge: "#3B6D11",
  conclusion: "#534AB7",
} as const;
const labels = {
  question: "QUESTION",
  hypothesis: "HYPOTHESIS",
  evidence: "EVIDENCE",
  perspective: "PERSPECTIVE",
  conflict: "CONFLICT",
  judge: "JUDGE",
  conclusion: "CONCLUSION",
} as const;
export function nodeSummary(node: ReasoningNode): string {
  if (node.type === "satellite") {
    if (node.parentType === "evidence") {
      const data = node.data as EvidenceItem;
      return data.claim || data.source_title || data.url || "Evidence source.";
    }
    const data = node.data as PerspectiveItem;
    return data.analysis || data.point || data.position || "Perspective point.";
  }
  switch (node.type) {
    case "question":
      return node.data.question;
    case "hypothesis":
      return node.data.hypotheses?.[0]?.claim || "Hypothesis generated.";
    case "evidence":
      return node.data.evidence?.[0]?.claim || "Evidence evaluated.";
    case "perspective":
      return node.data.perspectives?.[0]?.analysis || "Trade-offs analyzed.";
    case "conflict":
      return (
        node.data.summary ||
        node.data.conflicts?.[0] ||
        "Conflict analysis completed."
      );
    case "judge":
      return node.data.synthesis || "Reasoning judged.";
    case "conclusion":
      return node.data.conclusion || "Conclusion synthesized.";
    default:
      return assertNever(node);
  }
}
export function nodeTitle(node: ReasoningNode): string {
  if (node.type === "satellite")
    return node.parentType === "evidence"
      ? "EVIDENCE SOURCE"
      : "PERSPECTIVE POINT";
  if (node.type === "conclusion")
    return `CONCLUSION / AFTER ROUND ${Math.max(1, node.round - 1)}`;
  return `${labels[node.type]} / ROUND ${node.round}`;
}
export function nodeRadius(node: ReasoningNode): number {
  return node.type === "satellite"
    ? 6
    : node.type === "question" || node.type === "conclusion"
      ? 16
      : 10;
}
function nodeMarker(node: ReasoningNode): string {
  if (node.type === "satellite") return "";
  if (node.type === "question") return "Q";
  if (node.type === "conclusion") return "✓";
  return (
    {
      hypothesis: "H",
      evidence: "E",
      perspective: "P",
      conflict: "C",
      judge: "J",
    } as const
  )[node.type];
}

type ConstellationPoint = Readonly<{ x: number; y: number }>;
type ConstellationStages = Readonly<Record<(typeof flowOrder)[number], ConstellationPoint>>;
type ConstellationTemplate = Readonly<{ question: ConstellationPoint; stages: ConstellationStages }>;

const constellationBases: readonly ConstellationStages[] = [
  { hypothesis: { x: 0, y: -42 }, evidence: { x: 52, y: -82 }, perspective: { x: 30, y: 24 }, conflict: { x: 98, y: 54 }, judge: { x: 152, y: -6 } },
  { hypothesis: { x: 8, y: -62 }, evidence: { x: 66, y: -42 }, perspective: { x: 18, y: 22 }, conflict: { x: 102, y: 66 }, judge: { x: 154, y: 12 } },
  { hypothesis: { x: -6, y: -30 }, evidence: { x: 48, y: -70 }, perspective: { x: 54, y: 16 }, conflict: { x: 114, y: 42 }, judge: { x: 162, y: -18 } },
  { hypothesis: { x: 10, y: -56 }, evidence: { x: 76, y: -78 }, perspective: { x: 22, y: 42 }, conflict: { x: 92, y: 70 }, judge: { x: 156, y: -2 } },
  { hypothesis: { x: -8, y: -66 }, evidence: { x: 48, y: -28 }, perspective: { x: 64, y: 14 }, conflict: { x: 120, y: 60 }, judge: { x: 168, y: 4 } },
];

const questionAnchors: readonly ConstellationPoint[] = [
  { x: 54, y: 0 },
  { x: 282, y: -132 },
  { x: 302, y: 124 },
  { x: 178, y: -152 },
  { x: 192, y: 154 },
  { x: 362, y: -104 },
];

const constellationTemplates: readonly ConstellationTemplate[] = Array.from(
  { length: 30 },
  (_, index) => {
    const base = constellationBases[index % constellationBases.length] ?? constellationBases[0]!;
    const variation = Math.floor(index / constellationBases.length) - 2;
    const question = questionAnchors[index % questionAnchors.length] ?? questionAnchors[0]!;
    return {
      question: { x: question.x + variation * 4, y: question.y - variation * 3 },
      stages: Object.fromEntries(
        flowOrder.map((stage, stageIndex) => [
          stage,
          {
            x: base[stage].x + variation * ((stageIndex % 2 === 0 ? 3 : -2)),
            y: base[stage].y + variation * ((stageIndex % 2 === 0 ? 4 : -3)),
          },
        ]),
      ) as ConstellationStages,
    };
  },
);

function organicOffset(id: string, magnitude: number): number {
  let hash = 2166136261;
  for (let index = 0; index < id.length; index += 1) {
    hash ^= id.charCodeAt(index);
    hash = Math.imul(hash, 16777619);
  }
  return ((hash >>> 0) / 0xffffffff - 0.5) * magnitude * 2;
}

function selectConstellation(seed: string): ConstellationTemplate {
  let hash = 2166136261;
  for (let index = 0; index < seed.length; index += 1) {
    hash ^= seed.charCodeAt(index);
    hash = Math.imul(hash, 16777619);
  }
  return constellationTemplates[(hash >>> 0) % constellationTemplates.length] ?? constellationTemplates[0]!;
}

function clampY(y: number, height: number, padding: number): number {
  return Math.max(padding, Math.min(height - padding, y));
}

interface GraphRendererOptions {
  graph: HTMLElement;
  popup: HTMLElement;
  onClose: () => void;
  onShow: (node: PositionedNode, group: SVGGElement) => void;
  onPreview: (node: PositionedNode, group: SVGGElement) => void;
  onRemovePreview: (group: SVGGElement) => void;
  onNodes: (nodes: PositionedNode[]) => void;
  onAutoPopup: (node: PositionedNode, delay: number, duration: number) => void;
  reducedMotion: () => boolean;
}
interface PositionedEdge extends Omit<GraphEdge, "source" | "target"> {
  source: PositionedNode;
  target: PositionedNode;
}
export function createGraphRenderer(options: GraphRendererOptions) {
  type Viewport = { x: number; y: number; width: number; height: number };
  let svg: SVGSVGElement | null = null;
  let viewport: Viewport | null = null;
  let baseWidth = 0;
  let baseHeight = 0;
  let manualFollowUntil = 0;
  let cameraFrame: number | null = null;

  const straightPath = (edge: PositionedEdge) =>
    `M ${edge.source.x} ${edge.source.y} L ${edge.target.x} ${edge.target.y}`;
  const finishEdge = (edge: SVGPathElement) => {
    edge.style.opacity = "1";
    edge.setAttribute("stroke-dashoffset", "0");
    if (edge.dataset.thread === "true")
      edge.setAttribute("stroke-dasharray", "4 4");
  };
  const applyViewport = () => {
    if (!svg || !viewport) return;
    svg.setAttribute("viewBox", [viewport.x, viewport.y, viewport.width, viewport.height].join(" "));
  };
  const pauseFollow = () => {
    manualFollowUntil = Date.now() + 2400;
    if (cameraFrame !== null) {
      cancelAnimationFrame(cameraFrame);
      cameraFrame = null;
    }
  };
  const enableViewportControls = (canvas: SVGSVGElement) => {
    let drag: { x: number; y: number; viewX: number; viewY: number } | null = null;
    canvas.addEventListener("wheel", (event) => {
      if (!viewport || !baseWidth || !baseHeight) return;
      event.preventDefault();
      pauseFollow();
      const box = canvas.getBoundingClientRect();
      const pointerX = viewport.x + (event.clientX - box.left) * (viewport.width / box.width);
      const pointerY = viewport.y + (event.clientY - box.top) * (viewport.height / box.height);
      const factor = event.deltaY > 0 ? 1.12 : 0.88;
      const nextWidth = Math.max(baseWidth * 0.45, Math.min(baseWidth * 2.5, viewport.width * factor));
      const nextHeight = nextWidth * (baseHeight / baseWidth);
      viewport.x = pointerX - ((pointerX - viewport.x) * nextWidth) / viewport.width;
      viewport.y = pointerY - ((pointerY - viewport.y) * nextHeight) / viewport.height;
      viewport.width = nextWidth;
      viewport.height = nextHeight;
      applyViewport();
    }, { passive: false });
    canvas.addEventListener("pointerdown", (event) => {
      if (event.target !== canvas || !viewport) return;
      pauseFollow();
      drag = { x: event.clientX, y: event.clientY, viewX: viewport.x, viewY: viewport.y };
      canvas.setPointerCapture(event.pointerId);
    });
    canvas.addEventListener("pointermove", (event) => {
      if (!drag || !viewport) return;
      const box = canvas.getBoundingClientRect();
      viewport.x = drag.viewX - (event.clientX - drag.x) * (viewport.width / box.width);
      viewport.y = drag.viewY - (event.clientY - drag.y) * (viewport.height / box.height);
      applyViewport();
    });
    canvas.addEventListener("pointerup", () => { drag = null; });
  };
  const animate = (
    items: Array<{ node: PositionedNode; visual: SVGGElement }>,
    edges: SVGPathElement[],
    replay = options.graph.dataset.replay === "true",
  ) => {
    const anime = window.anime;
    if (options.reducedMotion() || !anime) {
      edges.forEach(finishEdge);
      items.forEach(({ visual }) => {
        visual.style.opacity = "1";
        visual.style.transform = "scale(1)";
      });
      return;
    }
    const nodeDuration = replay ? 520 : 430;
    const nodeStagger = replay ? 900 : 42;
    const popupDuration = replay ? 760 : 900;
    anime({
      targets: edges,
      strokeDashoffset: (edge) => [Number(edge.dataset.length), 0],
      opacity: [0.45, 1],
      duration: replay ? 520 : 430,
      easing: "easeInOutQuad",
      delay: anime.stagger(replay ? 120 : 34),
      complete: (animation) =>
        animation.animatables.forEach(({ target }) =>
          finishEdge(target as SVGPathElement),
        ),
    });
    anime({
      targets: items.map(({ visual }) => visual),
      opacity: [0, 1],
      scale: [0.8, 1],
      duration: nodeDuration,
      easing: "easeOutQuad",
      delay: anime.stagger(nodeStagger),
    });
    items.forEach(({ node }, index) =>
      options.onAutoPopup(
        node,
        nodeDuration + index * nodeStagger,
        popupDuration,
      ),
    );
  };
  const resetCanvas = (width: number, height: number) => {
    options.onClose();
    options.popup.hidden = true;
    options.popup.replaceChildren();
    options.graph.querySelectorAll(".auto-popup").forEach((popup) => popup.remove());
    svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    viewport = { x: 0, y: 0, width, height };
    baseWidth = width;
    baseHeight = height;
    applyViewport();
    const edgeLayer = document.createElementNS("http://www.w3.org/2000/svg", "g");
    edgeLayer.classList.add("edge-layer");
    const nodeLayer = document.createElementNS("http://www.w3.org/2000/svg", "g");
    nodeLayer.classList.add("node-layer");
    svg.append(edgeLayer, nodeLayer);
    options.graph.replaceChildren(svg, options.popup);
    enableViewportControls(svg);
    svg.addEventListener("click", (event) => {
      if (!(event.target instanceof Element) || !event.target.closest(".graph-node")) options.onClose();
    });
  };
  const followIncomingPrimary = (nodes: PositionedNode[], canvas: SVGSVGElement) => {
    const target = nodes.find((node) => node.type !== "satellite");
    if (!target || !viewport || options.reducedMotion() || Date.now() < manualFollowUntil) return;
    const marginX = viewport.width * 0.2;
    const marginY = viewport.height * 0.2;
    const visible = target.x >= viewport.x + marginX && target.x <= viewport.x + viewport.width - marginX && target.y >= viewport.y + marginY && target.y <= viewport.y + viewport.height - marginY;
    if (visible) return;
    const nextX = target.x - viewport.width / 2;
    const nextY = target.y - viewport.height / 2;
    if (cameraFrame !== null) cancelAnimationFrame(cameraFrame);
    const initialX = viewport.x;
    const initialY = viewport.y;
    const startedAt = performance.now();
    const step = (now: number) => {
      if (!viewport || svg !== canvas) return;
      const progress = Math.min(1, (now - startedAt) / 320);
      const eased = progress < 0.5 ? 2 * progress * progress : 1 - ((-2 * progress + 2) ** 2) / 2;
      viewport.x = initialX + (nextX - initialX) * eased;
      viewport.y = initialY + (nextY - initialY) * eased;
      applyViewport();
      cameraFrame = progress < 1 ? requestAnimationFrame(step) : null;
    };
    cameraFrame = requestAnimationFrame(step);
  };
  const render = (data: GraphData, incoming: Set<string>, reset = false) => {
    const width = options.graph.clientWidth || 700;
    const height = options.graph.clientHeight || 590;
    const needsReset = reset || !svg || !options.graph.contains(svg);
    if (needsReset) resetCanvas(width, height);
    if (!svg) return;
    const canvas = svg;
    const edgeLayer = canvas.querySelector<SVGGElement>(".edge-layer");
    const nodeLayer = canvas.querySelector<SVGGElement>(".node-layer");
    if (!edgeLayer || !nodeLayer) return;
    const centerY = height / 2;
    // A stable template makes replay and imported sessions readable and repeatable.
    const rounds = Math.max(1, data.rounds);
    const horizontalPadding = 54;
    const verticalPadding = 42;
    const template = selectConstellation(data.layoutSeed);
    const regionWidth = 212;
    const roundYOffset = [0, 68, -46];
    const primaryNodes = data.nodes.filter((node) => node.type !== "satellite");
    const primaryPositions = new Map<string, { x: number; y: number }>();
    primaryNodes.forEach((node) => {
      if (node.type === "question") {
        primaryPositions.set(node.id, {
          x: template.question.x,
          y: clampY(centerY + template.question.y, height, verticalPadding),
        });
        return;
      }
      const round = node.type === "conclusion" ? rounds : node.round;
      const regionX = 128 + (Math.max(1, round) - 1) * regionWidth;
      const regionY = centerY + (roundYOffset[(Math.max(1, round) - 1) % roundYOffset.length] ?? 0);
      const point = node.type === "conclusion"
        ? { x: template.stages.judge.x + 70, y: template.stages.judge.y + 54 }
        : template.stages[node.type];
      primaryPositions.set(node.id, {
        x: regionX + point.x + organicOffset(`${node.id}-x`, 4),
        y: clampY(regionY + point.y + organicOffset(`${node.id}-y`, 4), height, verticalPadding),
      });
    });
    const satellitesByParent = new Map<string, ReasoningNode[]>();
    data.nodes.forEach((node) => {
      if (node.type !== "satellite") return;
      const siblings = satellitesByParent.get(node.parentId) || [];
      siblings.push(node);
      satellitesByParent.set(node.parentId, siblings);
    });
    const nodes: PositionedNode[] = data.nodes.map((node) => {
      if (node.type !== "satellite") {
        const position = primaryPositions.get(node.id) || { x: horizontalPadding, y: centerY };
        return { ...node, ...position };
      }
      const parent = primaryPositions.get(node.parentId) || { x: horizontalPadding, y: centerY };
      const siblings = satellitesByParent.get(node.parentId) || [];
      const index = siblings.findIndex((sibling) => sibling.id === node.id);
      const phase = organicOffset(node.parentId, Math.PI);
      const angle = phase + (index / Math.max(1, siblings.length)) * Math.PI * 2;
      const satelliteDistance = node.parentType === "evidence" ? 42 : 34;
      return {
        ...node,
        x: node.parentType === "evidence"
          ? parent.x + Math.cos(angle) * satelliteDistance
          : parent.x + 26 + organicOffset(`${node.id}-x`, 6),
        y: node.parentType === "evidence"
          ? clampY(parent.y + Math.sin(angle) * satelliteDistance, height, verticalPadding)
          : clampY(parent.y + (index - (siblings.length - 1) / 2) * 24, height, verticalPadding),
      };
    });
    const preferredY = new Map(nodes.map((node) => [node.id, node.y]));
    // A small deterministic relaxation separates future same-stage siblings on Y only.
    for (let iteration = 0; iteration < 10; iteration += 1) {
      nodes.forEach((node) => {
        const target = preferredY.get(node.id) ?? node.y;
        node.y = clampY(node.y + (target - node.y) * 0.22, height, verticalPadding);
      });
      for (let first = 0; first < nodes.length; first += 1) {
        const source = nodes[first];
        if (!source) continue;
        for (let second = first + 1; second < nodes.length; second += 1) {
          const target = nodes[second];
          if (!target) continue;
          const minimumDistance = nodeRadius(source) + nodeRadius(target) + 8;
          if (Math.abs(source.x - target.x) >= minimumDistance) continue;
          const overlap = minimumDistance - Math.abs(source.y - target.y);
          if (overlap <= 0) continue;
          const direction = source.y <= target.y ? -1 : 1;
          source.y = clampY(source.y + direction * overlap / 2, height, verticalPadding);
          target.y = clampY(target.y - direction * overlap / 2, height, verticalPadding);
        }
      }
    }
    const byId = new Map(nodes.map((node) => [node.id, node]));
    const links: PositionedEdge[] = data.edges.flatMap((edge) => {
      const source =
        typeof edge.source === "string"
          ? byId.get(edge.source)
          : byId.get(edge.source.id);
      const target =
        typeof edge.target === "string"
          ? byId.get(edge.target)
          : byId.get(edge.target.id);
      return source && target ? [{ ...edge, source, target }] : [];
    });
    options.onNodes(nodes);
    const nodeIds = new Set(nodes.map((node) => node.id));
    const edgeId = (edge: PositionedEdge) => `${edge.kind}:${edge.source.id}->${edge.target.id}`;
    const currentEdges = new Map(Array.from(edgeLayer.querySelectorAll<SVGPathElement>("path.edge")).map((path) => [path.dataset.edgeId || "", path]));
    const currentNodes = new Map(Array.from(nodeLayer.querySelectorAll<SVGGElement>(".graph-node")).map((group) => [group.dataset.nodeId || "", group]));
    currentNodes.forEach((group, id) => { if (!nodeIds.has(id)) group.remove(); });
    const linkIds = new Set(links.map(edgeId));
    currentEdges.forEach((path, id) => { if (!linkIds.has(id)) path.remove(); });
    const newEdges: SVGPathElement[] = [];
    links.forEach((edge) => {
      const id = edgeId(edge);
      let path = currentEdges.get(id);
      const isNew = !path;
      if (!path) {
        path = document.createElementNS("http://www.w3.org/2000/svg", "path");
        path.classList.add("edge", edge.kind);
        path.dataset.edgeId = id;
        edgeLayer.append(path);
      }
      path.setAttribute("d", straightPath(edge));
      path.setAttribute("stroke", edge.kind === "thread" ? "#8e8b84" : colors[edge.target.type === "satellite" ? edge.target.parentType : edge.target.type]);
      const length = path.getTotalLength();
      path.dataset.length = String(length);
      path.dataset.thread = String(edge.kind === "thread");
      if (isNew) {
        path.setAttribute("stroke-dasharray", `${length} ${length}`);
        path.setAttribute("stroke-dashoffset", String(length));
        path.style.opacity = edge.kind === "satellite" ? ".35" : ".45";
        newEdges.push(path);
      }
    });
    const newItems: Array<{ node: PositionedNode; visual: SVGGElement }> = [];
    nodes.forEach((node) => {
      let group = currentNodes.get(node.id);
      const isNew = !group;
      if (!group) {
        group = document.createElementNS("http://www.w3.org/2000/svg", "g");
        group.classList.add("graph-node", node.type === "satellite" ? "satellite" : node.type);
        group.dataset.nodeId = node.id;
        group.tabIndex = 0;
        group.setAttribute("role", "button");
        const visual = document.createElementNS("http://www.w3.org/2000/svg", "g");
        visual.classList.add("node-visual");
        const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
        circle.setAttribute("r", String(nodeRadius(node)));
        circle.setAttribute("stroke", colors[node.type === "satellite" ? node.parentType : node.type]);
        const marker = nodeMarker(node);
        if (marker) {
          const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
          text.classList.add("node-marker");
          text.setAttribute("text-anchor", "middle");
          text.setAttribute("dominant-baseline", "central");
          text.textContent = marker;
          visual.append(circle, text);
        } else visual.append(circle);
        group.append(visual);
        const show = () => options.onShow(node, group!);
        group.addEventListener("click", (event) => { event.stopPropagation(); show(); });
        group.addEventListener("keydown", (event) => {
          if (event.key === "Enter" || event.key === " ") { event.preventDefault(); show(); }
        });
        group.addEventListener("pointerenter", () => {
          if (window.matchMedia("(pointer: fine)").matches && !group!.classList.contains("selected")) options.onPreview(node, group!);
        });
        group.addEventListener("pointerleave", () => options.onRemovePreview(group!));
        nodeLayer.append(group);
      }
      group.setAttribute("transform", `translate(${node.x},${node.y})`);
      group.setAttribute("aria-label", `${nodeTitle(node)}: ${nodeSummary(node)}`);
      const visual = group.querySelector<SVGGElement>(".node-visual");
      if (isNew && visual) newItems.push({ node, visual });
    });
    animate(newItems, newEdges, options.graph.dataset.replay === "true");
    if (!needsReset)
      window.setTimeout(() => followIncomingPrimary(newItems.map((item) => item.node), canvas), 120);
  };
  return {
    render,
    renderPendingQuestion: (question = "") => {
      svg = null;
      viewport = null;
      const width = options.graph.clientWidth || 700;
      const height = options.graph.clientHeight || 590;
      options.graph.innerHTML = `<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="Question node waiting for reasoning"><g class="graph-node question" transform="translate(${width / 2},${height / 2})"><circle r="24" stroke="${colors.question}"></circle><text x="0" y="-35" text-anchor="middle">QUESTION</text><text x="0" y="42" text-anchor="middle">${question ? question.slice(0, 38) : "waiting for input"}</text></g></svg>`;
      options.onClose();
    },
  };
}
