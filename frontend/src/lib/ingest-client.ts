import type { IngestResult } from './types';

/** POST /api/tasks/ingest. Uses batch_limit from ingestion settings unless overridden. */
export async function ingestEmails(): Promise<IngestResult> {
  const res = await fetch('/api/tasks/ingest', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({}),
  });

  if (!res.ok) {
    throw new Error(`Ingest failed (HTTP ${res.status})`);
  }

  return res.json();
}

export function formatIngestResult(result: IngestResult): string {
  const tasks = result.created_tasks === 1 ? 'task' : 'tasks';
  return `Scraped ${result.scraped}, classified ${result.classified}, created ${result.created_tasks} ${tasks}.`;
}
