import type { APIRoute } from 'astro';

import { getApiBase, isValidTaskId } from '../../../lib/api';

export const prerender = false;

export const PATCH: APIRoute = async ({ params, request }) => {
  const id = params.id;
  if (!id || !isValidTaskId(id)) {
    return new Response(JSON.stringify({ detail: 'Task not found' }), {
      status: 404,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  const body = await request.text();

  const res = await fetch(`${getApiBase()}/tasks/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body,
  });

  return new Response(await res.text(), {
    status: res.status,
    headers: { 'Content-Type': 'application/json' },
  });
};
