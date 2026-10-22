#!/usr/bin/env node
// Minimal stdio MCP client for figma-console-mcp, fronted by a local HTTP endpoint.
// Keeps ONE server process alive so the Figma plugin keeps its WebSocket pairing.
//
// Environment:
//   WS_PORT             WebSocket port handed to the server as FIGMA_WS_PORT (default 9231)
//   HTTP_PORT           local HTTP port of this daemon (default 8791); fx.py and shot.py read the same variable
//   FIGMA_MCP_ENTRY     path to figma-console-mcp's dist/local.js, to skip the npx cache lookup
//   FIGMA_ACCESS_TOKEN  Figma personal access token, inherited by the server as is. Needed for
//                       REST backed tools such as comments. Never printed, never written to a file.
//   FIGMA_MAXXING_STATE_DIR  state dir shared with the other scripts of this skill
//                       (default ~/.config/figma-maxxing); the daemon token file lives there
//
// The HTTP endpoint listens on 127.0.0.1 only, and every request must pass three checks:
//   1. no `Origin` header (403). Browsers send Origin on cross-site POSTs; fx.py, shot.py
//      and curl do not. This stops a web page open in the browser from reaching the daemon.
//   2. `content-type: application/json` on anything but GET (415). A browser can only send
//      that content type cross-site after a CORS preflight, and the daemon never answers one.
//   3. `Authorization: Bearer <token>` (401). The token is random per boot and is written,
//      mode 0600, to <state-dir>/mcp-direct-<HTTP_PORT>.token once the port is bound. The
//      file is removed when the daemon exits. fx.py and shot.py read it from there.
// Any process running as the same user can still read the token file. Stop the daemon when
// the work is done.
import { spawn, execFileSync } from 'node:child_process';
import { randomBytes, timingSafeEqual } from 'node:crypto';
import http from 'node:http';
import {
  readFileSync, existsSync, readdirSync, mkdirSync, writeFileSync, chmodSync, renameSync, unlinkSync,
} from 'node:fs';
import { homedir } from 'node:os';
import { join } from 'node:path';

const SERVER = process.env.FIGMA_MCP_ENTRY || (() => {
  // The npx cache hash changes on every reinstall, and the npm cache dir differs per
  // machine, so resolve both at boot.
  // Do NOT sort by mtime: a `ls -t` lookup once picked a 1.35.0 cache (newest mtime, OLDEST
  // version; field note, 2026-09), its server rewrote ~/.figma-console-mcp/plugin/ with the
  // old bundle, and the plugin in Figma started announcing "update available". Sort by SEMVER.
  // npm exports npm_config_cache to the processes it starts; read it first and ask npm only
  // when it is absent. npm runs through execFileSync with a fixed argument list and no shell.
  // Set FIGMA_MCP_ENTRY to skip this lookup entirely.
  let npmCache = process.env.npm_config_cache || '';
  if (!npmCache) {
    try {
      npmCache = execFileSync('npm', ['config', 'get', 'cache'], {
        encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'], timeout: 15000,
      }).trim();
    } catch { /* npm not on PATH: fall back to npm's default cache dir */ }
  }
  if (!npmCache) npmCache = join(homedir(), '.npm');
  const npxDir = join(npmCache, '_npx');
  let hashes = [];
  try { hashes = readdirSync(npxDir); } catch { /* no npx cache yet */ }
  const cand = [];
  for (const hash of hashes) {
    const dir = join(npxDir, hash, 'node_modules', 'figma-console-mcp');
    let v;
    try { v = JSON.parse(readFileSync(join(dir, 'package.json'), 'utf8')).version; } catch { continue; }
    const entry = join(dir, 'dist', 'local.js');
    if (!existsSync(entry)) continue;
    const parts = String(v).split('.').map(Number);
    if (parts.length !== 3 || parts.some(Number.isNaN)) continue;
    cand.push({ entry, v, rank: parts[0] * 1e6 + parts[1] * 1e3 + parts[2] });
  }
  if (!cand.length) {
    throw new Error(
      `figma-console-mcp not found in the npx cache (${npxDir}). ` +
      'Run the server once through npx so the cache exists, or set FIGMA_MCP_ENTRY to its dist/local.js.'
    );
  }
  cand.sort((a, b) => b.rank - a.rank);
  console.error(`mcp-direct: using figma-console-mcp ${cand[0].v} (${cand.length} in cache)`);
  return cand[0].entry;
})();
const WS_PORT = process.env.WS_PORT || '9231';
const HTTP_PORT = Number(process.env.HTTP_PORT || 8791);

// Same state dir and default as the shell scripts of this skill. One token file per HTTP
// port, so two daemons on two ports never overwrite each other's token.
const STATE_DIR = process.env.FIGMA_MAXXING_STATE_DIR || join(homedir(), '.config', 'figma-maxxing');
const TOKEN_FILE = join(STATE_DIR, `mcp-direct-${HTTP_PORT}.token`);
const TOKEN = randomBytes(32).toString('hex');

function writeTokenFile() {
  mkdirSync(STATE_DIR, { recursive: true, mode: 0o700 });
  const tmp = `${TOKEN_FILE}.${process.pid}.tmp`;
  writeFileSync(tmp, TOKEN + '\n', { mode: 0o600 });
  chmodSync(tmp, 0o600); // the mode above only applies when the file is created
  renameSync(tmp, TOKEN_FILE);
}

function removeTokenFile() {
  // Only remove the file this daemon wrote: a daemon that failed to bind must not delete
  // the token of the daemon that owns the port.
  try {
    if (readFileSync(TOKEN_FILE, 'utf8').trim() === TOKEN) unlinkSync(TOKEN_FILE);
  } catch { /* already gone */ }
}
process.on('exit', removeTokenFile);
for (const sig of ['SIGTERM', 'SIGINT', 'SIGHUP']) process.on(sig, () => process.exit(0));

function bearerOk(header) {
  const m = /^Bearer\s+(\S+)\s*$/i.exec(header || '');
  if (!m) return false;
  const got = Buffer.from(m[1]);
  const want = Buffer.from(TOKEN);
  return got.length === want.length && timingSafeEqual(got, want);
}

// Returns [status, message] for a request that must be refused, or null.
function refusal(req) {
  if (req.headers.origin !== undefined) return [403, 'requests with an Origin header are refused'];
  if (req.method !== 'GET') {
    const type = String(req.headers['content-type'] || '').split(';')[0].trim().toLowerCase();
    if (type !== 'application/json') return [415, 'content-type must be application/json'];
  }
  if (!bearerOk(req.headers.authorization)) {
    return [401, 'missing or wrong bearer token: read it from <state-dir>/mcp-direct-<HTTP_PORT>.token'];
  }
  return null;
}

// A fixed message per failure class, so no error text or stack trace reaches the client.
function clientError(e) {
  if (e instanceof SyntaxError) return 'request body is not valid JSON';
  if (e instanceof Error && e.message.startsWith('timeout ')) return 'the figma-console server did not answer in time';
  return 'internal error: the detail is in the daemon log (stderr)';
}

// The Figma token is not read here: FIGMA_ACCESS_TOKEN reaches the server through the
// inherited environment. No secrets loader, no shell profile.
const child = spawn(process.execPath, [SERVER], {
  env: { ...process.env, FIGMA_WS_PORT: String(WS_PORT) },
  stdio: ['pipe', 'pipe', 'pipe'],
});

let buf = '';
const pending = new Map();
let nextId = 1;

child.stdout.on('data', (d) => {
  buf += d.toString();
  let i;
  while ((i = buf.indexOf('\n')) >= 0) {
    const line = buf.slice(0, i).trim();
    buf = buf.slice(i + 1);
    if (!line) continue;
    let msg;
    try { msg = JSON.parse(line); } catch { continue; }
    if (msg.id && pending.has(msg.id)) {
      const { resolve } = pending.get(msg.id);
      pending.delete(msg.id);
      resolve(msg);
    }
  }
});
child.stderr.on('data', (d) => process.stderr.write('[srv] ' + d.toString()));
child.on('exit', (c) => { console.error('server exited', c); process.exit(1); });

function rpc(method, params, timeoutMs = 180000) {
  const id = nextId++;
  const payload = JSON.stringify({ jsonrpc: '2.0', id, method, params }) + '\n';
  return new Promise((resolve, reject) => {
    const t = setTimeout(() => { pending.delete(id); reject(new Error('timeout ' + method)); }, timeoutMs);
    pending.set(id, { resolve: (m) => { clearTimeout(t); resolve(m); } });
    child.stdin.write(payload);
  });
}
function notify(method, params) {
  child.stdin.write(JSON.stringify({ jsonrpc: '2.0', method, params }) + '\n');
}

async function boot() {
  await rpc('initialize', {
    protocolVersion: '2024-11-05',
    capabilities: {},
    clientInfo: { name: 'mcp-direct', version: '1.0.0' },
  });
  notify('notifications/initialized', {});
  const tools = await rpc('tools/list', {});
  console.error('tools:', (tools.result?.tools || []).map(t => t.name).join(','));
}

const server = http.createServer((req, res) => {
  const refused = refusal(req);
  if (refused) {
    const headers = { 'content-type': 'application/json' };
    if (refused[0] === 401) headers['www-authenticate'] = 'Bearer';
    res.writeHead(refused[0], headers);
    res.end(JSON.stringify({ error: refused[1] }));
    req.resume(); // drain the unread body
    return;
  }
  let body = '';
  req.on('data', (c) => (body += c));
  req.on('end', async () => {
    try {
      if (req.url === '/tools') {
        const r = await rpc('tools/list', {});
        res.writeHead(200, { 'content-type': 'application/json' });
        return res.end(JSON.stringify(r.result?.tools?.map(t => ({ name: t.name, schema: t.inputSchema })) ?? r));
      }
      const { name, arguments: args } = JSON.parse(body || '{}');
      const r = await rpc('tools/call', { name, arguments: args || {} });
      res.writeHead(200, { 'content-type': 'application/json' });
      res.end(JSON.stringify(r.result ?? r.error ?? r));
    } catch (e) {
      // The detail stays in this daemon's stderr; the client only gets a fixed message.
      console.error('mcp-direct: request failed:', e);
      res.writeHead(500, { 'content-type': 'application/json' });
      res.end(JSON.stringify({ error: clientError(e) }));
    }
  });
});

boot().then(() => {
  server.listen(HTTP_PORT, '127.0.0.1', () => {
    // Written only after the port is bound, so a second daemon that fails with
    // EADDRINUSE never replaces the token of the one that owns the port.
    writeTokenFile();
    console.error('daemon ready on ' + HTTP_PORT + ' ws=' + WS_PORT + ' token file ' + TOKEN_FILE);
  });
}).catch((e) => { console.error('boot failed', e); process.exit(1); });
