import http from 'node:http';
import { readdir, readFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
export const UPLOADS = path.join(here, 'uploads');

function send(res, status, body, type = 'text/plain; charset=utf-8') {
  res.writeHead(status, { 'content-type': type });
  res.end(body);
}

export async function handle(req, res) {
  const url = new URL(req.url, 'http://localhost');

  if (req.method === 'GET' && url.pathname === '/') {
    const names = (await readdir(UPLOADS)).sort();
    const links = names.map((n) => `/files/${encodeURIComponent(n)}`);
    return send(res, 200, JSON.stringify({ files: names, links }, null, 2), 'application/json');
  }

  if (req.method === 'GET' && url.pathname.startsWith('/files/')) {
    const name = url.pathname.slice('/files/'.length);
    if (name === '' || name.includes('..') || name.includes('/')) {
      return send(res, 400, 'bad file name\n');
    }
    try {
      const body = await readFile(path.join(UPLOADS, name));
      return send(res, 200, body, 'application/octet-stream');
    } catch {
      return send(res, 404, 'not found\n');
    }
  }

  return send(res, 404, 'not found\n');
}

export function createServer() {
  return http.createServer((req, res) => {
    handle(req, res).catch(() => send(res, 500, 'server error\n'));
  });
}

if (process.argv[1] && fileURLToPath(import.meta.url) === path.resolve(process.argv[1])) {
  const port = Number(process.env.PORT ?? 3000);
  createServer().listen(port, '127.0.0.1', () => console.log(`files server on http://127.0.0.1:${port}`));
}
