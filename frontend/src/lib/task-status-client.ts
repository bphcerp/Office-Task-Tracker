import type { Task, TaskStatusValue } from './types';

export async function updateTaskStatus(
  taskId: number,
  status: TaskStatusValue,
): Promise<Task> {
  const res = await fetch(`/api/tasks/${taskId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status }),
  });

  if (!res.ok) {
    throw new Error(`Failed to update status (HTTP ${res.status})`);
  }

  return res.json();
}
