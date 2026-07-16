import { friendlyError } from './errors';

export async function downloadSessionExport(sessionId: string | null, format: 'markdown' | 'json', setStatus: (message: string, state?: string) => void) {
  if (!sessionId) return;
  try {
    const response = await fetch(`/api/sessions/${sessionId}/exports/${format}`);
    if (!response.ok) {
      const detail = await response.text();
      setStatus(friendlyError(new Error(detail || response.statusText), "We couldn't prepare that export. Please try again."), 'error');
      return;
    }

    const objectUrl = URL.createObjectURL(await response.blob());
    const link = document.createElement('a');
    link.href = objectUrl;
    link.download = `thesision-${sessionId}.${format === 'markdown' ? 'md' : 'json'}`;
    link.hidden = true;
    document.body.append(link);
    link.click();
    link.remove();

    // Some browsers only begin consuming the Blob URL after the click task ends.
    window.setTimeout(() => URL.revokeObjectURL(objectUrl), 1_000);
    setStatus(`${format === 'markdown' ? 'Markdown' : 'JSON'} export downloaded.`, 'complete');
  } catch (error) {
    setStatus(friendlyError(error, "We couldn't prepare that export. Please try again."), 'error');
  }
}
