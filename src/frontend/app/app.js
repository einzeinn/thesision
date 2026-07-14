const form = document.getElementById('question-form');
const status = document.getElementById('status');
const graph = document.getElementById('graph');
const graphPanel = document.querySelector('.graph-panel');
const button = document.getElementById('run-button');
const detailTitle = document.getElementById('detail-title');
const details = document.getElementById('node-details');
const confidenceValue = document.getElementById('confidence-value');
const confidenceMeter = document.getElementById('confidence-meter');
const evidenceList = document.getElementById('evidence-list');
const graphMeta = document.getElementById('graph-meta');
const exportMarkdown = document.getElementById('export-markdown');
const exportJson = document.getElementById('export-json');
let activeSessionId = null;

const stageColors = { question: '#3977b5', hypothesis: '#b28a35', evidence: '#317a9d', perspectives: '#b76935', judge: '#3d9871', confidence: '#4e8d8a', conclusion: '#7654b2' };
const stageLabels = { question: 'QUESTION', hypothesis: 'HYPOTHESIS', evidence: 'EVIDENCE', perspectives: 'PERSPECTIVES', judge: 'JUDGE', confidence: 'CONFIDENCE', conclusion: 'CONCLUSION' };

function textPreview(value) {
  return value ? JSON.stringify(value, null, 2) : 'No structured output was recorded.';
}

function renderGraph(session) {
  const state = session.state;
  const stages = ['question', ...state.pipeline.filter((stage) => state[stage])];
  const positions = stages.map((stage, index) => ({ stage, x: 120 + (index % 3) * 260, y: 100 + Math.floor(index / 3) * 190 }));
  graph.replaceChildren();
  positions.slice(1).forEach((position, index) => {
    const previous = positions[index];
    graph.insertAdjacentHTML('beforeend', `<line class="edge" x1="${previous.x + 70}" y1="${previous.y + 35}" x2="${position.x - 70}" y2="${position.y + 35}" />`);
  });
  positions.forEach(({ stage, x, y }, index) => {
    const group = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    group.classList.add('node');
    if (!document.body.classList.contains('reduce-motion')) group.classList.add('node-enter');
    group.style.animationDelay = `${index * 70}ms`;
    group.dataset.stage = stage;
    group.innerHTML = `<rect x="${x - 72}" y="${y - 34}" rx="10" width="144" height="68" fill="${stageColors[stage]}"></rect><text class="stage" x="${x}" y="${y - 7}" text-anchor="middle">${stageLabels[stage]}</text><text x="${x}" y="${y + 14}" text-anchor="middle">${stage === 'question' ? 'Decision input' : 'Inspect reasoning'}</text>`;
    group.addEventListener('click', () => inspectNode(stage, session, group));
    graph.append(group);
  });
  graphMeta.textContent = `Iteration ${state.iteration || 0} / ${state.status}`;
  inspectNode('question', session, graph.querySelector('[data-stage="question"]'));
}

function inspectNode(stage, session, element) {
  graph.querySelectorAll('.node').forEach((node) => node.classList.remove('selected'));
  element?.classList.add('selected');
  detailTitle.textContent = stageLabels[stage];
  details.textContent = stage === 'question' ? session.question : textPreview(session.state[stage]);
}

function renderEvidence(state) {
  const evidence = state.evidence?.evidence || [];
  evidenceList.replaceChildren();
  if (!evidence.length) { evidenceList.innerHTML = '<li class="empty">No evidence was returned for this session.</li>'; return; }
  evidence.forEach((item) => {
    const entry = document.createElement('li');
    entry.textContent = item.claim || 'Untitled evidence';
    if (item.url) { const link = document.createElement('a'); link.href = item.url; link.target = '_blank'; link.rel = 'noreferrer'; link.textContent = item.source_title || item.url; entry.append(link); }
    evidenceList.append(entry);
  });
}

function renderConfidence(state) {
  const score = state.confidence?.score;
  confidenceValue.textContent = Number.isFinite(score) ? `${score}%` : '-';
  confidenceMeter.style.width = `${Number.isFinite(score) ? score : 0}%`;
}

function setStatus(message, state = 'running') {
  status.textContent = message;
  status.dataset.state = state;
}

document.getElementById('reduce-motion').addEventListener('change', (event) => document.body.classList.toggle('reduce-motion', event.target.checked));

async function downloadExport(format) {
  if (!activeSessionId) return;
  const response = await fetch(`/api/sessions/${activeSessionId}/exports/${format}`);
  if (!response.ok) { setStatus('Export unavailable for this session.', 'error'); return; }
  const link = document.createElement('a');
  link.href = URL.createObjectURL(await response.blob());
  link.download = `thesision-${activeSessionId}.${format === 'markdown' ? 'md' : 'json'}`;
  link.click();
  URL.revokeObjectURL(link.href);
}

exportMarkdown.addEventListener('click', () => downloadExport('markdown'));
exportJson.addEventListener('click', () => downloadExport('json'));

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  button.disabled = true;
  graphPanel.setAttribute('aria-busy', 'true');
  exportMarkdown.disabled = true; exportJson.disabled = true;
  setStatus('Building hypothesis and evaluating evidence...');
  try {
    const createResponse = await fetch('/api/sessions', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ question: document.getElementById('question').value, context: document.getElementById('context').value }) });
    if (!createResponse.ok) throw new Error((await createResponse.json()).detail || 'Unable to create the session.');
    const created = await createResponse.json();
    setStatus('Evaluating perspectives and resolving conflicts...');
    const runResponse = await fetch(`/api/sessions/${created.session_id}/run`, { method: 'POST' });
    if (!runResponse.ok) throw new Error((await runResponse.json()).detail || 'Reasoning did not complete.');
    const payload = await runResponse.json();
    renderGraph(payload.session); renderEvidence(payload.session.state); renderConfidence(payload.session.state);
    activeSessionId = created.session_id;
    exportMarkdown.disabled = false; exportJson.disabled = false;
    setStatus(`Reasoning complete / session ${created.session_id.slice(0, 8)}`, 'complete');
  } catch (error) { setStatus(`Reasoning unavailable: ${error.message}`, 'error'); }
  finally { button.disabled = false; graphPanel.setAttribute('aria-busy', 'false'); }
});
