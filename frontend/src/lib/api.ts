import type { Task } from './types';
import { fetchWithRetry } from './fetch-retry';

/** Base URL for server-side API calls (see BACKEND_UPSTREAM in .env.example). */
export function getApiBase(): string {
  const upstream = process.env.BACKEND_UPSTREAM ?? 'http://localhost:8000';
  return `${upstream.replace(/\/$/, '')}/api`;
}

function isValidTaskId(id: string): boolean {
  return /^\d+$/.test(id) && Number(id) > 0;
}

export async function fetchTasks(): Promise<Task[]> {
  const res = await fetchWithRetry(`${getApiBase()}/tasks`);
  if (!res.ok) {
    throw new Error(`Failed to load tasks (HTTP ${res.status})`);
  }
  return res.json();
}

export async function fetchTask(id: string): Promise<Task | null> {
  if (!isValidTaskId(id)) return null;

  const res = await fetchWithRetry(`${getApiBase()}/tasks/${id}`);
  // 404 = missing task; 422 = FastAPI rejected a non-integer path param.
  if (res.status === 404 || res.status === 422) return null;
  if (!res.ok) {
    throw new Error(`Failed to load task (HTTP ${res.status})`);
  }
  return res.json();
}
