import type { APIRoute } from 'astro';

import { getApiBase } from '../../../lib/api';

export const prerender = false;

/** Proxy ingest requests to the backend (prod). Dev vite proxy hits the backend directly. */
export const POST: APIRoute = async ({ request }) => {
  const body = await request.text();

  const res = await fetch(`${getApiBase()}/tasks/ingest`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: body || JSON.stringify({ limit: 25 }),
  });

  return new Response(await res.text(), {
    status: res.status,
    headers: { 'Content-Type': 'application/json' },
  });
};
