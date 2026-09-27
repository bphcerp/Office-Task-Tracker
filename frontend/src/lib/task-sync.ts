import { setListItemStatus } from './task-ui';
import type { TaskStatusValue } from './types';

const STORAGE_KEY = 'task-tracker-status-patches';

function readPatches(): Record<string, TaskStatusValue> {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return {};
    return JSON.parse(raw) as Record<string, TaskStatusValue>;
  } catch {
    return {};
  }
}

export function clearStatusPatches(): void {
  sessionStorage.removeItem(STORAGE_KEY);
}

export function recordTaskStatus(taskId: number, status: TaskStatusValue): void {
  const patches = readPatches();
  patches[String(taskId)] = status;
  sessionStorage.setItem(STORAGE_KEY, JSON.stringify(patches));
}

/** Apply status patches written on the detail page. Returns true if the DOM changed. */
export function applyListPatches(root: HTMLElement): boolean {
  const patches = readPatches();
  if (Object.keys(patches).length === 0) return false;

  let changed = false;
  for (const [id, status] of Object.entries(patches)) {
    const item = root.querySelector<HTMLElement>(`[data-task-id="${id}"]`);
    if (!item) continue;
    setListItemStatus(item, status);
    changed = true;
  }

  sessionStorage.removeItem(STORAGE_KEY);
  return changed;
}
