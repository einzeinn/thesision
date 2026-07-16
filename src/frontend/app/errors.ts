function errorText(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

/** Keep operational details out of the reasoning workspace while retaining useful next steps. */
export function friendlyError(error: unknown, fallback: string): string {
  const message = errorText(error).toLowerCase();
  if (
    message.includes("503") ||
    message.includes("server error") ||
    message.includes("temporarily unavailable") ||
    message.includes("provider request failed")
  ) {
    return "Our AI provider is temporarily unavailable. Please try again in a moment.";
  }
  if (message.includes("429") || message.includes("rate limit")) {
    return "You've made several requests recently. Please wait a minute, then try again.";
  }
  if (
    message.includes("failed to fetch") ||
    message.includes("networkerror") ||
    message.includes("network error")
  ) {
    return "We couldn't reach Thesision right now. Check your connection and try again.";
  }
  if (message.includes("not configured") || message.includes("api key")) {
    return "The AI provider is not configured yet. Please check the server environment settings.";
  }
  if (message.includes("reasoning must complete") || message.includes("incomplete")) {
    return "This session is still running. Please wait until reasoning is complete and try again.";
  }
  if (message.includes("import") || message.includes("json")) {
    return "We couldn't read that session file. Please choose a Thesision JSON export and try again.";
  }
  return fallback;
}
