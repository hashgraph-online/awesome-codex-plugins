// Local server for the animatic: static files + save/export of camera edits.
//   bun serve.ts [port]           -> http://localhost:8777/
//   POST /api/save   edits JSON   -> data/edits.json (+ a timestamped copy in data/history/)
//   POST /api/export {name, text} -> camera_plan.md / camera_plan.json in this folder
// Read-only alternative without Bun: python3 -m http.server 8777 (saving then downloads files instead).
import { mkdir } from 'node:fs/promises';
import { join, normalize, basename } from 'node:path';

const ROOT = import.meta.dir;
const PORT = Number(process.argv[2] || process.env.PORT || 8777);
const EXPORTS = new Set(['camera_plan.md', 'camera_plan.json']);
const json = (obj: unknown, status = 200) => Response.json(obj, { status, headers: { 'Cache-Control': 'no-store' } });

Bun.serve({
  port: PORT,
  hostname: '127.0.0.1', // local only
  async fetch(req) {
    const url = new URL(req.url);
    if (req.method === 'POST') {
      let body: any;
      try { body = await req.json(); } catch (e) { return json({ error: `bad json: ${e}` }, 400); }
      if (url.pathname === '/api/save') {
        const text = JSON.stringify(body, null, 1);
        await mkdir(join(ROOT, 'data', 'history'), { recursive: true });
        await Bun.write(join(ROOT, 'data', 'edits.json'), text);
        const stamp = new Date().toISOString().replace(/[-:]/g, '').replace('T', '-').slice(0, 15);
        await Bun.write(join(ROOT, 'data', 'history', `edits_${stamp}.json`), text);
        return json({ ok: true, path: 'data/edits.json' });
      }
      if (url.pathname === '/api/export') {
        const name = basename(String(body?.name || ''));
        if (!EXPORTS.has(name)) return json({ error: `only ${[...EXPORTS].join(', ')}` }, 400);
        await Bun.write(join(ROOT, name), String(body?.text ?? ''));
        return json({ ok: true, path: name });
      }
      return json({ error: 'unknown endpoint' }, 404);
    }
    // static, confined to ROOT
    const rel = normalize(decodeURIComponent(url.pathname)).replace(/^(\.\.[/\\])+/, '');
    let path = join(ROOT, rel);
    if (!path.startsWith(ROOT)) return new Response('forbidden', { status: 403 });
    if (rel.endsWith('/')) path = join(path, 'index.html');
    const file = Bun.file(path);
    if (!(await file.exists())) return new Response('not found', { status: 404 });
    return new Response(file, { headers: { 'Cache-Control': 'no-store' } });
  },
});
console.log(`animatic: http://localhost:${PORT}/   (clean export view: http://localhost:${PORT}/?export=1)`);
