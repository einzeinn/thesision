const form = document.getElementById('question-form');
const workspace = document.querySelector('.workspace');
const status = document.getElementById('status');
const graph = document.getElementById('graph');
const graphPanel = document.querySelector('.graph-panel');
const detailStrip = document.getElementById('detail-strip');
const button = document.getElementById('run-button');
const confidenceValue = document.getElementById('confidence-value');
const confidenceMeter = document.getElementById('confidence-meter');
const evidenceList = document.getElementById('evidence-list');
const sessionMeta = document.getElementById('session-meta');
const graphMeta = document.getElementById('graph-meta');
const exportMarkdown = document.getElementById('export-markdown');
const exportJson = document.getElementById('export-json');
const exportsSection = document.getElementById('exports');
const replayButton = document.getElementById('replay-button');
const progressList = document.getElementById('progress-list');
let activeSessionId = null;
let activeSession = null;
let lastGraphSignature = null;

const colors = { question: '#5F5E5A', hypothesis: '#BA7517', evidence: '#185FA5', perspective: '#993C1D', conflict: '#A32D2D', judge: '#3B6D11', conclusion: '#534AB7' };
const labels = { question: 'QUESTION', hypothesis: 'HYPOTHESIS', evidence: 'EVIDENCE', perspective: 'PERSPECTIVE', conflict: 'CONFLICT', judge: 'JUDGE', conclusion: 'CONCLUSION' };
const flowOrder = ['hypothesis', 'evidence', 'perspective', 'conflict', 'judge'];

function setStatus(message, state = 'running') { status.textContent = message; status.dataset.state = state; }
function setProgress(activeIndex, complete = false) {
  progressList.hidden = false;
  [...progressList.children].forEach((item, index) => {
    item.classList.toggle('active', index === activeIndex && !complete);
    item.classList.toggle('complete', complete || index < activeIndex);
  });
}
function renderPendingQuestion(question = '') {
  const width = graph.clientWidth || 700; const height = graph.clientHeight || 590; const x = width / 2; const y = height / 2;
  graph.innerHTML = `<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="Question node waiting for reasoning"><g class="graph-node question" transform="translate(${x},${y})"><circle r="24" stroke="${colors.question}"></circle><text x="0" y="-35" text-anchor="middle">QUESTION</text><text x="0" y="42" text-anchor="middle">${question ? question.slice(0, 38) : 'waiting for input'}</text></g></svg>`;
}
function summary(node) {
  const data = node.data || {};
  if (node.type === 'question') return node.data.question;
  if (node.type === 'hypothesis') return data.hypotheses?.[0]?.claim || 'Hypothesis generated.';
  if (node.type === 'evidence') return data.evidence?.[0]?.claim || 'Evidence evaluated.';
  if (node.type === 'perspective') return data.perspectives?.[0]?.analysis || 'Trade-offs analyzed.';
  if (node.type === 'conflict') return data.summary || data.conflicts?.[0] || 'Conflict analysis completed.';
  if (node.type === 'judge') return data.synthesis || 'Reasoning judged.';
  if (node.type === 'conclusion') return data.conclusion || 'Conclusion synthesized.';
  return 'Reasoning stage completed.';
}

function graphData(session) {
  const stageNodes = (session.state.nodes || []).filter((node) => node.type !== 'confidence').map((node) => ({ ...node, type: node.type === 'perspectives' ? 'perspective' : node.type }));
  const question = { id: 'question-0', type: 'question', round: 0, data: { question: session.question } };
  const nodes = [question, ...stageNodes].sort((a, b) => a.round - b.round || flowOrder.indexOf(a.type) - flowOrder.indexOf(b.type));
  const byRound = new Map();
  nodes.forEach((node) => { if (!byRound.has(node.round)) byRound.set(node.round, new Map()); byRound.get(node.round).set(node.type, node); });
  const edges = [];
  [...byRound.keys()].filter((round) => round > 0).sort().forEach((round) => {
    const current = byRound.get(round); const previous = byRound.get(round - 1);
    const first = current.get('hypothesis');
    if (first) edges.push({ source: round === 1 ? question.id : previous?.get('judge')?.id, target: first.id, kind: round === 1 ? 'flow' : 'continuation' });
    flowOrder.slice(1).forEach((type, index) => { const source = current.get(flowOrder[index]); const target = current.get(type); if (source && target) edges.push({ source: source.id, target: target.id, kind: 'flow' }); });
    if (previous) flowOrder.forEach((type) => { const source = previous.get(type); const target = current.get(type); if (source && target) edges.push({ source: source.id, target: target.id, kind: 'thread' }); });
  });
  const conclusion = nodes.find((node) => node.type === 'conclusion'); const lastJudge = byRound.get(session.state.iteration)?.get('judge');
  if (conclusion && lastJudge) edges.push({ source: lastJudge.id, target: conclusion.id, kind: 'flow' });
  return { nodes, edges, rounds: session.state.iteration || 1 };
}

function reveal(target, delay = 0) {
  if (document.body.classList.contains('reduce-motion')) return;
  target.style.opacity = '0';
  target.animate([{ opacity: 0 }, { opacity: 1 }], { duration: 360, delay, easing: 'ease-out', fill: 'forwards' });
}
function selectDenseNode(node, element) { document.querySelectorAll('.graph-node').forEach((item) => item.classList.remove('selected')); element.classList.add('selected'); detailStrip.innerHTML = `<strong>${labels[node.type]} / ROUND ${node.round}</strong><p>${summary(node)}</p>`; }

function lanePosition(node, centerX, centerY) {
  const angles = { hypothesis: -120, evidence: -72, perspective: -24, conflict: 24, judge: 72, conclusion: 132 };
  if (node.type === 'question') return { x: centerX, y: centerY };
  const radius = node.type === 'conclusion' ? (node.round + .25) * 108 : node.round * 108;
  const angle = (angles[node.type] ?? 0) * Math.PI / 180;
  return { x: centerX + Math.cos(angle) * radius, y: centerY + Math.sin(angle) * radius };
}
function continuationPath(edge, centerX, centerY) {
  const middleX = (edge.source.x + edge.target.x) / 2; const middleY = (edge.source.y + edge.target.y) / 2;
  const distance = Math.hypot(middleX - centerX, middleY - centerY) || 1;
  const reach = Math.max(Math.hypot(edge.source.x - centerX, edge.source.y - centerY), Math.hypot(edge.target.x - centerX, edge.target.y - centerY)) + 42;
  const controlX = centerX + ((middleX - centerX) / distance) * reach; const controlY = centerY + ((middleY - centerY) / distance) * reach;
  return `M ${edge.source.x} ${edge.source.y} Q ${controlX} ${controlY} ${edge.target.x} ${edge.target.y}`;
}

function renderGraphLayout(data) {
  graph.replaceChildren(); const width = graph.clientWidth || 700; const height = graph.clientHeight || 590; const centerX = width / 2; const centerY = height / 2;
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg'); svg.setAttribute('viewBox', `0 0 ${width} ${height}`); graph.append(svg);
  const nodes = data.nodes.map((node) => ({ ...node, ...lanePosition(node, centerX, centerY) })); const byId = new Map(nodes.map((node) => [node.id, node])); const links = data.edges.filter((edge) => byId.has(edge.source) && byId.has(edge.target)).map((edge) => ({ ...edge, source: byId.get(edge.source), target: byId.get(edge.target) }));
  if (window.d3?.forceSimulation) {
    const simulation = window.d3.forceSimulation(nodes).force('link', window.d3.forceLink(links).id((node) => node.id).distance(76).strength(.08)).force('charge', window.d3.forceManyBody().strength(-24)).force('x', window.d3.forceX((node) => lanePosition(node, centerX, centerY).x).strength(.8)).force('y', window.d3.forceY((node) => lanePosition(node, centerX, centerY).y).strength(.8)).force('collide', window.d3.forceCollide((node) => node.type === 'question' || node.type === 'conclusion' ? 24 : 18).iterations(2)).stop();
    const question = nodes.find((node) => node.type === 'question'); if (question) { question.fx = centerX; question.fy = centerY; } for (let tick = 0; tick < 180; tick += 1) simulation.tick();
  }
  links.forEach((edge, index) => { const line = document.createElementNS('http://www.w3.org/2000/svg', edge.kind === 'continuation' ? 'path' : 'line'); line.classList.add('edge', edge.kind); if (edge.kind === 'continuation') line.setAttribute('d', continuationPath(edge, centerX, centerY)); else { line.setAttribute('x1', edge.source.x); line.setAttribute('y1', edge.source.y); line.setAttribute('x2', edge.target.x); line.setAttribute('y2', edge.target.y); } line.setAttribute('stroke', edge.kind === 'thread' ? '#8e8b84' : colors[edge.target.type]); svg.append(line); reveal(line, index * 28); });
  nodes.forEach((node, index) => { const group = document.createElementNS('http://www.w3.org/2000/svg', 'g'); group.classList.add('graph-node', node.type); group.setAttribute('transform', `translate(${node.x},${node.y})`); const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle'); const radius = node.type === 'question' || node.type === 'conclusion' ? 16 : 10; circle.setAttribute('r', radius); circle.setAttribute('stroke', colors[node.type]); const text = document.createElementNS('http://www.w3.org/2000/svg', 'text'); text.setAttribute('x', radius + 7); text.setAttribute('y', 3); text.textContent = labels[node.type]; group.append(circle, text); group.addEventListener('click', () => selectDenseNode(node, group)); svg.append(group); reveal(group, 90 + index * 42); });
  detailStrip.innerHTML = '<strong>REASONING GRAPH</strong><p>Select a circle to inspect its stage, round, and reasoning summary.</p>';
}

function renderGraph(session, force = false) { const data = graphData(session); const signature = data.nodes.map((node) => node.id).join('|'); if (!force && signature === lastGraphSignature) return; lastGraphSignature = signature; graphMeta.textContent = `${data.rounds} round${data.rounds === 1 ? '' : 's'} / ${session.state.status}`; renderGraphLayout(data); }
function renderEvidence(state) { const evidence = state.evidence?.evidence || []; evidenceList.replaceChildren(); if (!evidence.length) { evidenceList.innerHTML = '<li class="empty">No evidence was returned for this session.</li>'; return; } evidence.forEach((item) => { const entry = document.createElement('li'); entry.textContent = item.claim || 'Untitled evidence'; if (item.url) { const link = document.createElement('a'); link.href = item.url; link.target = '_blank'; link.rel = 'noreferrer'; link.textContent = item.source_title || item.url; entry.append(link); } evidenceList.append(entry); }); }
function renderConfidence(state) { const score = state.confidence?.score; confidenceValue.textContent = Number.isFinite(score) ? `${score}%` : '-'; confidenceMeter.style.width = `${Number.isFinite(score) ? score : 0}%`; }
async function responseDetail(response, fallback) { const body = await response.text(); try { return JSON.parse(body).detail || fallback; } catch { return body || fallback; } }
document.getElementById('reduce-motion').addEventListener('change', (event) => document.body.classList.toggle('reduce-motion', event.target.checked));
async function downloadExport(format) { if (!activeSessionId) return; const response = await fetch(`/api/sessions/${activeSessionId}/exports/${format}`); if (!response.ok) { setStatus('Export unavailable for this session.', 'error'); return; } const link = document.createElement('a'); link.href = URL.createObjectURL(await response.blob()); link.download = `thesision-${activeSessionId}.${format === 'markdown' ? 'md' : 'json'}`; link.click(); URL.revokeObjectURL(link.href); }
exportMarkdown.addEventListener('click', () => downloadExport('markdown')); exportJson.addEventListener('click', () => downloadExport('json'));
replayButton.addEventListener('click', () => { if (activeSession) { lastGraphSignature = null; renderGraph(activeSession, true); } });
renderPendingQuestion();
const stageProgress = { hypothesis: 0, evidence: 1, perspectives: 2, judge: 3, confidence: 3, conclusion: 4 };
const delay = (milliseconds) => new Promise((resolve) => setTimeout(resolve, milliseconds));
async function pollReasoning(sessionId) {
  while (true) {
    await delay(300);
    const response = await fetch(`/api/sessions/${sessionId}`);
    if (!response.ok) throw new Error(await responseDetail(response, 'Unable to read reasoning progress.'));
    const session = await response.json(); const state = session.state;
    if (state.nodes?.length) renderGraph(session);
    setProgress(stageProgress[state.current_stage] ?? 0);
    if (state.status === 'failed') throw new Error(state.errors?.at(-1) || 'Reasoning did not complete.');
    if (state.status === 'completed') return session;
  }
}
form.addEventListener('submit', async (event) => { event.preventDefault(); const question = document.getElementById('question').value; button.disabled = true; graphPanel.setAttribute('aria-busy', 'true'); exportMarkdown.disabled = true; exportJson.disabled = true; exportsSection.hidden = true; replayButton.hidden = true; workspace.classList.remove('session-complete'); lastGraphSignature = null; renderPendingQuestion(question); setProgress(0); setStatus('Building hypothesis...'); try { const createResponse = await fetch('/api/sessions', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ question, context: document.getElementById('context').value }) }); if (!createResponse.ok) throw new Error(await responseDetail(createResponse, 'Unable to create the session.')); const created = await createResponse.json(); const startResponse = await fetch(`/api/sessions/${created.session_id}/start`, { method: 'POST' }); if (!startResponse.ok) throw new Error(await responseDetail(startResponse, 'Unable to start reasoning.')); activeSession = await pollReasoning(created.session_id); renderGraph(activeSession, true); renderEvidence(activeSession.state); renderConfidence(activeSession.state); activeSessionId = created.session_id; sessionMeta.textContent = `Session ${activeSessionId.slice(0, 8)} / ${activeSession.state.iteration} reasoning round(s)`; workspace.classList.add('session-complete'); exportsSection.hidden = false; replayButton.hidden = false; exportMarkdown.disabled = false; exportJson.disabled = false; setProgress(4, true); setStatus(`Reasoning complete / session ${activeSessionId.slice(0, 8)}`, 'complete'); } catch (error) { setStatus(`Reasoning unavailable: ${error.message}`, 'error'); } finally { button.disabled = false; graphPanel.setAttribute('aria-busy', 'false'); } });
