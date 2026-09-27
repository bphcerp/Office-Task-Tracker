import type { APIRoute } from 'astro';

import { getApiBase, isValidTaskId } from '../../../lib/api';

export const prerender = false;

function taskNotFound(): Response {
  return new Response(JSON.stringify({ detail: 'Task not found' }), {
    status: 404,
    headers: { 'Content-Type': 'application/json' },
  });
}

async function proxyTaskRequest(
  id: string | undefined,
  method: 'PATCH' | 'DELETE',
  request?: Request,
): Promise<Response> {
  if (!id || !isValidTaskId(id)) {
    return taskNotFound();
  }

  const init: RequestInit = { method };
  if (method === 'PATCH' && request) {
    init.headers = { 'Content-Type': 'application/json' };
    init.body = await request.text();
  }

  const res = await fetch(`${getApiBase()}/tasks/${id}`, init);

  if (method === 'DELETE') {
    const body = res.status === 204 ? null : await res.text();
    return new Response(body, {
      status: res.status,
      headers: body ? { 'Content-Type': 'application/json' } : undefined,
    });
  }

  return new Response(await res.text(), {
    status: res.status,
    headers: { 'Content-Type': 'application/json' },
  });
}

export const PATCH: APIRoute = async ({ params, request }) =>
  proxyTaskRequest(params.id, 'PATCH', request);

export const DELETE: APIRoute = async ({ params }) =>
  proxyTaskRequest(params.id, 'DELETE');
