import type { PositionedNode, PopupState, ReasoningNode } from './types';

export interface PopupControllerOptions {
  graph: HTMLElement;
  popup: HTMLElement;
  live: HTMLElement;
  state: PopupState;
  title: (node: ReasoningNode) => string;
  summary: (node: ReasoningNode) => string;
  radius: (node: ReasoningNode) => number;
  reducedMotion: () => boolean;
}

export function createPopupController(options: PopupControllerOptions) {
  let nodes: PositionedNode[] = [];
  let transientPopup: HTMLElement | null = null;
  const clearLabels = () => options.graph.querySelectorAll('.node-label').forEach((label) => label.remove());
  const clearSelected = () => options.graph.querySelectorAll('.graph-node.selected').forEach((node) => node.classList.remove('selected'));
  const placement = (node: PositionedNode) => {
    const text = options.title(node).replace(' / ', ' · '); const width = Math.max(76, text.length * 6.2 + 16); const height = 18;
    const originX = options.graph.clientWidth / 2; const originY = options.graph.clientHeight / 2; const distance = Math.hypot(node.x - originX, node.y - originY) || 1;
    const base = { x: (node.x - originX) / distance, y: (node.y - originY) / distance }; const candidates = [base, { x: -base.x, y: -base.y }, { x: 1, y: 0 }, { x: -1, y: 0 }, { x: 0, y: 1 }, { x: 0, y: -1 }];
    return candidates.map((direction) => { const offset = options.radius(node) + width / 2 + 10; const x = node.x + direction.x * offset; const y = node.y + direction.y * offset; const left = x - width / 2; const right = x + width / 2; const top = y - height / 2; const bottom = y + height / 2; const clearance = Math.min(...nodes.filter((other) => other.id !== node.id).map((other) => { const nearX = Math.max(left, Math.min(other.x, right)); const nearY = Math.max(top, Math.min(other.y, bottom)); return Math.hypot(other.x - nearX, other.y - nearY) - options.radius(other) - 3; }), 999); return { x, y, width, height, clearance }; }).sort((a, b) => b.clearance - a.clearance)[0]!;
  };
  const showLabel = (node: PositionedNode, group: SVGGElement, preview = false) => {
    clearLabels(); const position = placement(node); const wrapper = document.createElementNS('http://www.w3.org/2000/svg', 'g'); wrapper.classList.add('node-label'); if (preview) wrapper.classList.add('preview'); wrapper.setAttribute('transform', `translate(${position.x - node.x},${position.y - node.y})`);
    const visual = document.createElementNS('http://www.w3.org/2000/svg', 'g'); const backplate = document.createElementNS('http://www.w3.org/2000/svg', 'rect'); backplate.setAttribute('x', String(-position.width / 2)); backplate.setAttribute('y', String(-position.height / 2)); backplate.setAttribute('width', String(position.width)); backplate.setAttribute('height', String(position.height)); backplate.setAttribute('rx', '2'); const text = document.createElementNS('http://www.w3.org/2000/svg', 'text'); text.setAttribute('text-anchor', 'middle'); text.setAttribute('y', '3'); text.textContent = options.title(node).replace(' / ', ' · '); visual.append(backplate, text); wrapper.append(visual); group.append(wrapper);
    const anime = window.anime; if (preview) requestAnimationFrame(() => { wrapper.style.opacity = '.6'; }); else if (anime && !options.reducedMotion()) anime({ targets: visual, opacity: [0, 1], scale: [.85, 1], duration: 200, easing: 'easeOutQuad' });
  };
  const popupPosition = (node: PositionedNode) => { const svg = options.graph.querySelector('svg'); if (!(svg instanceof SVGSVGElement) || !svg.viewBox.baseVal.width) return { left: 8, top: 8 }; const box = svg.getBoundingClientRect(); const viewBox = svg.viewBox.baseVal; const scaleX = box.width / viewBox.width; const scaleY = box.height / viewBox.height; const anchorX = (node.x - viewBox.x) * scaleX; const anchorY = (node.y - viewBox.y) * scaleY; const width = 230; const height = 98; const inset = 10; const candidates: ReadonlyArray<readonly [number, number]> = [[20, 20], [20, -height - 20], [-width - 20, 20], [-width - 20, -height - 20], [32, -height / 2], [-width - 32, -height / 2]]; return candidates.map(([offsetX, offsetY]) => { const left = Math.max(inset, Math.min(options.graph.clientWidth - width - inset, anchorX + offsetX)); const top = Math.max(inset, Math.min(options.graph.clientHeight - height - inset, anchorY + offsetY)); const clearance = Math.min(...nodes.filter(other => other.id !== node.id).map(other => { const x = (other.x - viewBox.x) * scaleX; const y = (other.y - viewBox.y) * scaleY; const nearX = Math.max(left, Math.min(x, left + width)); const nearY = Math.max(top, Math.min(y, top + height)); return Math.hypot(x - nearX, y - nearY) - options.radius(other) * Math.max(scaleX, scaleY); }), 999); return { left, top, clearance }; }).sort((a, b) => b.clearance - a.clearance)[0]!;
  };
  const populate = (popup: HTMLElement, node: PositionedNode) => { const position = popupPosition(node); popup.style.left = `${position.left}px`; popup.style.top = `${position.top}px`; popup.replaceChildren(); const title = document.createElement('strong'); title.textContent = options.title(node); const summary = document.createElement('p'); summary.textContent = options.summary(node); popup.append(title, summary); if (node.type === 'satellite' && node.parentType === 'evidence') { const source = node.data as { url?: string; source_title?: string }; if (source.url) { const link = document.createElement('a'); link.href = source.url; link.target = '_blank'; link.rel = 'noreferrer'; link.textContent = source.source_title || 'Open evidence source'; popup.append(link); } } };
  const close = () => { options.state.selectedNodeId = null; options.popup.hidden = true; options.popup.replaceChildren(); clearLabels(); clearSelected(); };
  const show = (node: PositionedNode, group: SVGGElement) => { if (options.state.selectedNodeId === node.id) { close(); return; } clearSelected(); options.state.selectedNodeId = node.id; group.classList.add('selected'); showLabel(node, group); populate(options.popup, node); options.popup.hidden = false; options.live.textContent = `${options.title(node)}. ${options.summary(node)}`; const anime = window.anime; if (anime && !options.reducedMotion()) anime({ targets: options.popup, opacity: [0, 1], scale: [.85, 1], duration: 200, easing: 'easeOutQuad' }); };
  const showAutomatic = (node: PositionedNode, displayDuration = 900) => { transientPopup?.remove(); const transient = document.createElement('article'); transientPopup = transient; transient.className = 'graph-popup auto-popup'; transient.setAttribute('aria-hidden', 'true'); options.graph.append(transient); populate(transient, node); const remove = () => { if (transientPopup === transient) transientPopup = null; transient.remove(); }; const anime = window.anime; if (anime && !options.reducedMotion()) anime({ targets: transient, opacity: [0, 1], scale: [.85, 1], duration: 200, easing: 'easeOutQuad', complete: () => setTimeout(() => anime({ targets: transient, opacity: [1, 0], duration: 160, easing: 'easeOutQuad', complete: remove }), displayDuration) }); else setTimeout(remove, displayDuration); };
  return { close, setNodes: (next: PositionedNode[]) => { nodes = next; }, show, showAutomatic, showLabel, removePreview: (group: SVGGElement) => group.querySelector('.node-label.preview')?.remove() };
}
