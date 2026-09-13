import type { APIRoute } from 'astro';

import { getApiBase } from '../../../lib/api';

export const prerender = false;

async function proxy(request: Request, method: 'GET' | 'PATCH') {
  const init: RequestInit = { method };
  if (method === 'PATCH') {
    init.headers = { 'Content-Type': 'application/json' };
    init.body = await request.text();
  }

  const res = await fetch(`${getApiBase()}/settings/ingestion`, init);
  return new Response(await res.text(), {
    status: res.status,
    headers: { 'Content-Type': 'application/json' },
  });
}

export const GET: APIRoute = async ({ request }) => proxy(request, 'GET');

export const PATCH: APIRoute = async ({ request }) => proxy(request, 'PATCH');
