export interface FetchRetryOptions {
  /** Number of retries after the initial attempt (default: 2 → 3 attempts total). */
  maxRetries?: number;
  /** Base delay in ms for exponential backoff (default: 300). */
  baseDelayMs?: number;
}

function isRetryableStatus(status: number): boolean {
  return status >= 500;
}

function backoffDelayMs(attempt: number, baseDelayMs: number): number {
  return baseDelayMs * 2 ** attempt;
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * fetch with retries on transient failures (5xx responses and network errors).
 * 4xx responses are returned immediately — they won't succeed on retry.
 */
export async function fetchWithRetry(
  url: string,
  init?: RequestInit,
  { maxRetries = 2, baseDelayMs = 300 }: FetchRetryOptions = {},
): Promise<Response> {
  let lastError: unknown;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      const response = await fetch(url, init);
      if (!isRetryableStatus(response.status) || attempt === maxRetries) {
        return response;
      }
    } catch (error) {
      lastError = error;
      if (attempt === maxRetries) break;
    }

    await sleep(backoffDelayMs(attempt, baseDelayMs));
  }

  throw lastError instanceof Error ? lastError : new Error('Failed to reach backend');
}
