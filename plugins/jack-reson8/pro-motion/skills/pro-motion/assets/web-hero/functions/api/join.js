// POST /api/join {email, ref?, lang?} → {ref, position, invites, boost}
import { newRef, rank, json } from '../_rank.js';

const EMAIL = /^[^\s@]{1,64}@[^\s@]{1,190}\.[^\s@]{2,24}$/;

export async function onRequestPost({ request, env }) {
  let body;
  try { body = await request.json(); } catch { return json({ error: 'bad_json' }, 400); }
  const email = String(body.email || '').trim().toLowerCase();
  if (!EMAIL.test(email)) return json({ error: 'bad_email' }, 400);
  const lang = String(body.lang || '').slice(0, 12);
  let by = String(body.ref || '').toUpperCase().replace(/[^0-9A-Z]/g, '').slice(0, 6) || null;
  if (by && !(await env.DB.prepare('SELECT 1 FROM waitlist WHERE ref = ?1').bind(by).first())) by = null;

  const old = await env.DB.prepare('SELECT ref FROM waitlist WHERE email = ?1').bind(email).first();
  if (old) return json({ ...(await rank(env.DB, old.ref)), again: true });

  for (let i = 0; i < 5; i++) {
    const ref = newRef();
    try {
      await env.DB.prepare('INSERT INTO waitlist (email, ref, referred_by, lang, created_at) VALUES (?1, ?2, ?3, ?4, ?5)')
        .bind(email, ref, by, lang, Date.now()).run();
      return json(await rank(env.DB, ref));
    } catch (e) {
      if (!String(e).includes('UNIQUE')) return json({ error: 'db' }, 500);
      const again = await env.DB.prepare('SELECT ref FROM waitlist WHERE email = ?1').bind(email).first();
      if (again) return json({ ...(await rank(env.DB, again.ref)), again: true });
    }
  }
  return json({ error: 'busy' }, 503);
}
