// GET /api/me?ref=XXXXXX → {ref, position, invites, boost}
import { rank, json } from '../_rank.js';

export async function onRequestGet({ request, env }) {
  const ref = new URL(request.url).searchParams.get('ref')?.toUpperCase().replace(/[^0-9A-Z]/g, '').slice(0, 6);
  if (!ref) return json({ error: 'no_ref' }, 400);
  const r = await rank(env.DB, ref);
  return r ? json(r) : json({ error: 'not_found' }, 404);
}
