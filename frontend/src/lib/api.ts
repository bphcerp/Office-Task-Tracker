import type { Task } from './types';

/** Base URL for server-side API calls (see BACKEND_UPSTREAM in .env.example). */
function apiBase(): string {
  const upstream = process.env.BACKEND_UPSTREAM ?? 'http://localhost:8000';
  return `${upstream.replace(/\/$/, '')}/api`;
}

export async function fetchTasks(): Promise<Task[]> {
  const res = await fetch(`${apiBase()}/tasks`);
  if (!res.ok) {
    throw new Error(`Failed to load tasks (HTTP ${res.status})`);
  }
  return res.json();
}

export async function fetchTask(id: string): Promise<Task | null> {
  const res = await fetch(`${apiBase()}/tasks/${id}`);
  if (res.status === 404) return null;
  if (!res.ok) {
    throw new Error(`Failed to load task (HTTP ${res.status})`);
  }
  return res.json();
}
