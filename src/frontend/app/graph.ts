import { assertNever, type EvidenceItem, type GraphData, type PerspectiveItem, type ReasoningNode, type SessionPayload } from './types';

const flowOrder = ['hypothesis', 'evidence', 'perspective', 'conflict', 'judge'] as const;
function normaliseNode(node: { id: string; type: string; round: number; data: unknown }): ReasoningNode | null {
  switch (node.type) {
    case 'hypothesis': return { ...node, type: 'hypothesis', data: node.data as { hypotheses?: Array<{ claim?: string }> } };
    case 'evidence': return { ...node, type: 'evidence', data: node.data as { evidence?: EvidenceItem[] } };
    case 'perspective': case 'perspectives': return { ...node, type: 'perspective', data: node.data as { perspectives?: PerspectiveItem[] } };
    case 'conflict': return { ...node, type: 'conflict', data: node.data as { summary?: string; conflicts?: string[] } };
    case 'judge': return { ...node, type: 'judge', data: node.data as { synthesis?: string } };
    case 'conclusion': return { ...node, type: 'conclusion', data: node.data as { conclusion?: string } };
    case 'confidence': return null;
    default: return null;
  }
}
function satellites(node: ReasoningNode): ReasoningNode[] { switch (node.type) { case 'evidence': return (node.data.evidence || []).map((item, index) => ({ ...node, id: `${node.id}-source-${index}`, type: 'satellite', satellite: true, parentId: node.id, parentType: 'evidence', data: item })); case 'perspective': return (node.data.perspectives || []).map((item, index) => ({ ...node, id: `${node.id}-point-${index}`, type: 'satellite', satellite: true, parentId: node.id, parentType: 'perspective', data: item })); case 'question': case 'hypothesis': case 'conflict': case 'judge': case 'conclusion': case 'satellite': return []; default: return assertNever(node); } }
export function buildGraphData(session: SessionPayload): GraphData {
  const question: ReasoningNode = { id: 'question-0', type: 'question', round: 0, data: { question: session.question } }; const primary = [question, ...(session.state.nodes || []).map(normaliseNode).filter((node): node is ReasoningNode => node !== null)].sort((a, b) => a.round - b.round || a.id.localeCompare(b.id)); const byRound = new Map<number, Map<string, ReasoningNode>>(); primary.forEach((node) => { if (!byRound.has(node.round)) byRound.set(node.round, new Map()); byRound.get(node.round)?.set(node.type, node); }); const edges: GraphData['edges'] = []; const rounds = session.state.iteration || 1;
  for (let round = 1; round <= rounds; round += 1) { const current = byRound.get(round); const previous = byRound.get(round - 1); const hypothesis = current?.get('hypothesis'); if (hypothesis) edges.push({ source: round === 1 ? question.id : previous?.get('judge')?.id || question.id, target: hypothesis.id, kind: round === 1 ? 'flow' : 'continuation' }); flowOrder.slice(1).forEach((type, index) => { const sourceType = flowOrder[index]; if (!sourceType) return; const source = current?.get(sourceType); const target = current?.get(type); if (source && target) edges.push({ source: source.id, target: target.id, kind: 'flow' }); }); if (previous) flowOrder.forEach((type) => { const source = previous.get(type); const target = current?.get(type); if (source && target) edges.push({ source: source.id, target: target.id, kind: 'thread' }); }); }
  const conclusion = primary.find((node) => node.type === 'conclusion'); const judge = byRound.get(rounds)?.get('judge'); if (conclusion && judge) edges.push({ source: judge.id, target: conclusion.id, kind: 'flow' }); const satelliteNodes = primary.flatMap(satellites); satelliteNodes.forEach((node) => { if (node.type === 'satellite') edges.push({ source: node.parentId, target: node.id, kind: 'satellite' }); }); return { nodes: [...primary, ...satelliteNodes], edges, rounds };
}
