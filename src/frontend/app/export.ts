export async function downloadSessionExport(sessionId: string | null, format: 'markdown' | 'json', setStatus: (message: string, state?: string) => void) {
  if (!sessionId) return;
  const response = await fetch(`/api/sessions/${sessionId}/exports/${format}`);
  if (!response.ok) { setStatus('Export unavailable for this session.', 'error'); return; }
  const link = document.createElement('a'); link.href = URL.createObjectURL(await response.blob()); link.download = `thesision-${sessionId}.${format === 'markdown' ? 'md' : 'json'}`; link.click(); URL.revokeObjectURL(link.href);
}
