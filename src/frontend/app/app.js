const form = document.getElementById('question-form');
const status = document.getElementById('status');
const output = document.getElementById('session-output');

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  const question = document.getElementById('question').value;
  const context = document.getElementById('context').value;

  status.textContent = 'Creating session...';
  const createResponse = await fetch('/api/sessions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, context }),
  });

  const created = await createResponse.json();
  status.textContent = `Session created: ${created.session_id}`;
  output.textContent = JSON.stringify(created, null, 2);

  const runResponse = await fetch(`/api/sessions/${created.session_id}/run`, {
    method: 'POST',
  });
  const runPayload = await runResponse.json();
  output.textContent = JSON.stringify(runPayload, null, 2);
  status.textContent = `Reasoning completed for ${created.session_id}`;
});
