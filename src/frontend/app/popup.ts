import type { PositionedNode, PopupState, ReasoningNode } from './types';

export function createPopupController(graph: HTMLElement, popup: HTMLElement, live: HTMLElement, state: PopupState, title: (node: ReasoningNode) => string, summary: (node: ReasoningNode) => string) {
  const position = (node: PositionedNode) => { const svg = graph.querySelector('svg'); if (!svg?.viewBox.baseVal.width) return { left: 8, top: 8 }; const box = svg.getBoundingClientRect(); const viewBox = svg.viewBox.baseVal; let left = node.x * (box.width / viewBox.width) + 16; let top = node.y * (box.height / viewBox.height) + 16; if (left + 230 > graph.clientWidth - 8) left -= 246; if (top + 98 > graph.clientHeight - 8) top -= 114; return { left: Math.max(8, left), top: Math.max(8, top) }; };
  const close = () => { state.selectedNodeId = null; popup.hidden = true; popup.replaceChildren(); };
  const show = (node: PositionedNode) => { const coordinates = position(node); state.selectedNodeId = node.id; popup.style.left = `${coordinates.left}px`; popup.style.top = `${coordinates.top}px`; popup.innerHTML = `<strong>${title(node)}</strong><p>${summary(node)}</p>`; popup.hidden = false; live.textContent = `${title(node)}. ${summary(node)}`; };
  return { close, show };
}
