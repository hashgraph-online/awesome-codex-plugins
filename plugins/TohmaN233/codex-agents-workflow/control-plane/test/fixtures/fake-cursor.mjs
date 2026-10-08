#!/usr/bin/env node
import { createHash } from 'node:crypto';
import { appendFile, mkdir, writeFile } from 'node:fs/promises';
import http from 'node:http';
import { basename, join } from 'node:path';
import { parseFrames } from '../../connectors/websocket-client.mjs';

const args = process.argv.slice(2);
const portArg = args.find((arg) => arg.startsWith('--remote-debugging-port='));
const port = Number(portArg?.split('=')[1] || process.env.FAKE_CURSOR_PORT || 0);
const workspace = args.filter((arg) => !arg.startsWith('--')).at(-1) || process.cwd();
const workspaceName = basename(workspace).toLowerCase();
const logPath = process.env.FAKE_CURSOR_LOG;
const identityReadyAt = Date.now() + Number(process.env.FAKE_CURSOR_IDENTITY_DELAY_MS || 0);
const uiProfile = process.env.FAKE_CURSOR_UI_PROFILE || 'agents_v2';
if (logPath) await appendFile(logPath, `${JSON.stringify({ pid: process.pid, args, workspace })}\n`);

let agentCounter = 0;
const state = {
  prompt: '',
  agentId: null,
  agentState: 'unknown',
  composerStatus: null,
  stop: 0,
  messageCount: 0,
  reply: '',
  sent: false,
};
const sockets = new Set();

function serverFrame(payload, opcode = 0x1) {
  const data = Buffer.isBuffer(payload) ? payload : Buffer.from(String(payload), 'utf8');
  let header;
  if (data.length < 126) {
    header = Buffer.from([0x80 | opcode, data.length]);
  } else if (data.length <= 0xffff) {
    header = Buffer.alloc(4);
    header[0] = 0x80 | opcode;
    header[1] = 126;
    header.writeUInt16BE(data.length, 2);
  } else {
    header = Buffer.alloc(10);
    header[0] = 0x80 | opcode;
    header[1] = 127;
    header.writeBigUInt64BE(BigInt(data.length), 2);
  }
  return Buffer.concat([header, data]);
}

function send(socket, message) {
  socket.write(serverFrame(JSON.stringify(message)));
}

function runtimeValue(id, value) {
  return { id, result: { result: { type: typeof value, value } } };
}

async function finish(text = 'cursor fixture result', agentState = 'completed') {
  state.reply = text;
  state.agentState = agentState;
  state.composerStatus = agentState === 'cancelled' ? 'cancelled' : 'ready';
  state.stop = 0;
  state.messageCount = 2;
}

async function startTask() {
  if (state.sent) return;
  if (uiProfile === 'agents_panel' && !state.agentId) {
    agentCounter += 1;
    const suffix = String(agentCounter).padStart(12, '0');
    state.agentId = `local:33333333-3333-7333-8333-${suffix}`;
  }
  state.sent = true;
  state.agentState = 'running';
  state.composerStatus = 'generating';
  state.stop = 1;
  state.messageCount = 1;
  if (state.prompt.includes('CURSOR_STDERR_SECRET')) {
    process.stderr.write('Authorization: Bearer cursor-secret token=cursor-token\n');
    setTimeout(() => process.exit(9), 50);
    return;
  }
  if (state.prompt.includes('CURSOR_DROP')) {
    setTimeout(() => {
      for (const socket of sockets) socket.destroy();
    }, 80);
    return;
  }
  if (state.prompt.includes('CURSOR_HANG') || state.prompt.includes('CURSOR_WAIT_CANCEL')) return;
  if (state.prompt.includes('CURSOR_LATE_OUTSIDE')) {
    setTimeout(() => { void writeFile(join(workspace, 'outside.txt'), 'cursor late outside\n'); }, 600);
    return; // Only the exact Stop action can finish this running fixture.
  }
  if (state.prompt.includes('CURSOR_WRITE_ALLOWED')) {
    await mkdir(join(workspace, 'allowed'), { recursive: true });
    await writeFile(join(workspace, 'allowed', 'cursor.txt'), 'cursor allowed\n');
  }
  if (state.prompt.includes('CURSOR_WRITE_OUTSIDE') || state.prompt.includes('CURSOR_READONLY_WRITE')) {
    await writeFile(join(workspace, 'outside.txt'), 'cursor outside\n');
  }
  if (state.prompt.includes('CURSOR_WRITE_IGNORED')) {
    await writeFile(join(workspace, 'ignored-secret.txt'), 'cursor ignored outside\n');
    setTimeout(() => void finish(), 350);
    return;
  }
  setTimeout(() => void finish(), 120);
}

function history() {
  return state.agentId ? [{
    id: state.agentId,
    label: 'Fixture Agent',
    timestamp: Date.now(),
    selected: true,
    state: state.agentState,
  }] : [];
}

async function evaluate(expression) {
  if (expression.includes('/*sol:probe*/')) {
    if (uiProfile === 'agents_panel') {
      return JSON.stringify({
        ok: true,
        ui_flavor: 'agents_panel',
        has_input: true,
        workspace_ready: true,
        workspace_count: 1,
        available: [workspaceName],
        adapter_ready: false,
        adapter_kind: null,
        document_title: 'Cursor Agents',
      });
    }
    return JSON.stringify({
      ok: true,
      ui_flavor: 'agents_v2',
      has_input: true,
      workspace_ready: true,
      workspace_count: 1,
      available: [workspaceName],
      adapter_ready: true,
      adapter_kind: 'agents_v2',
      document_title: `Cursor Agents - ${workspaceName}`,
    });
  }
  if (expression.includes('/*sol:history*/')) {
    if (uiProfile === 'agents_panel') {
      return JSON.stringify({ ok: false, error: 'AGENT_ADAPTER_UNAVAILABLE' });
    }
    return JSON.stringify({ ok: true, kind: 'agents_v2', entries: history() });
  }
  if (expression.includes('/*sol:create-agent*/')) {
    if (uiProfile === 'agents_panel') {
      const previousComposerId = state.agentId;
      state.agentId = null;
      state.agentState = 'unknown';
      state.composerStatus = null;
      state.prompt = '';
      state.stop = 0;
      state.messageCount = 0;
      state.reply = '';
      state.sent = false;
      return JSON.stringify({
        ok: true,
        state: previousComposerId ? 'panel_new_agent_clicked' : 'panel_ready',
        deferred_identity: true,
        previous_composer_id: previousComposerId,
      });
    }
    agentCounter += 1;
    const suffix = String(agentCounter).padStart(12, '0');
    state.agentId = `local:22222222-2222-7222-8222-${suffix}`;
    state.agentState = 'unknown';
    state.composerStatus = 'ready';
    state.prompt = '';
    state.stop = 0;
    state.messageCount = 0;
    state.reply = '';
    state.sent = false;
    return JSON.stringify({ ok: true, state: 'created' });
  }
  if (expression.includes('/*sol:composer*/')) {
    return JSON.stringify(state.agentId
      ? { ok: true, id: state.agentId, status: state.composerStatus }
      : { ok: false, state: 'missing', count: 0 });
  }
  if (expression.includes('/*sol:fill*/')) {
    const payload = /\/\*sol-payload:([^*]+)\*\//.exec(expression)?.[1] || '';
    state.prompt = Buffer.from(payload, 'base64').toString('utf8');
    return 'FILLED';
  }
  if (expression.includes('/*sol:snapshot*/')) {
    let hash = 0;
    for (const char of state.reply) hash = ((hash << 5) - hash + char.charCodeAt(0)) | 0;
    return JSON.stringify({
      message_count: state.messageCount,
      reply_length: state.reply.length,
      reply_hash: hash,
      stop: state.stop,
      input_length: state.sent ? 0 : state.prompt.length,
      identity_match: state.identityLost !== true,
      visible_composer_count: state.agentId ? 1 : 0,
    });
  }
  if (expression.includes('/*sol:extract*/')) return state.reply;
  if (expression.includes('/*sol:send*/')) {
    await startTask();
    return 'CLICKED';
  }
  if (expression.includes('/*sol:open-agent*/')) {
    return state.agentId ? 'OPENED' : 'AGENT_NOT_FOUND';
  }
  if (expression.includes('/*sol:stop*/')) {
    if (state.agentState !== 'running') return JSON.stringify({ clicked: false, state: 'not_generating' });
    await finish('cursor cancelled fixture result', 'cancelled');
    if (process.env.FAKE_CURSOR_LOSE_IDENTITY_ON_STOP === '1') state.identityLost = true;
    return JSON.stringify({ clicked: true, state: 'clicked' });
  }
  return null;
}

const server = http.createServer((req, res) => {
  if (req.url === '/json/version') {
    const identityReady = Date.now() >= identityReadyAt;
    const body = JSON.stringify(identityReady
      ? { Browser: 'Chrome/Fake', 'User-Agent': 'Fake Cursor/3.16.29', 'Protocol-Version': '1.3' }
      : { Browser: 'Chrome/Fake', 'User-Agent': 'Fake Chrome/144', 'Protocol-Version': '1.3' });
    res.writeHead(200, { 'content-type': 'application/json', 'content-length': Buffer.byteLength(body) });
    res.end(body);
    return;
  }
  if (req.url === '/json/list') {
    const identityReady = Date.now() >= identityReadyAt;
    const body = JSON.stringify(identityReady ? [{
      id: 'fake-cursor-page', type: 'page', title: `Cursor Agents - ${workspaceName}`,
      url: `vscode-file://cursor/${workspaceName}`,
      webSocketDebuggerUrl: `ws://127.0.0.1:${port}/devtools/page/fake-cursor-page`,
    }] : []);
    res.writeHead(200, { 'content-type': 'application/json', 'content-length': Buffer.byteLength(body) });
    res.end(body);
    return;
  }
  res.writeHead(404); res.end();
});

server.on('upgrade', (req, socket) => {
  const key = req.headers['sec-websocket-key'];
  const accept = createHash('sha1')
    .update(`${key}258EAFA5-E914-47DA-95CA-C5AB0DC85B11`)
    .digest('base64');
  socket.write([
    'HTTP/1.1 101 Switching Protocols',
    'Upgrade: websocket',
    'Connection: Upgrade',
    `Sec-WebSocket-Accept: ${accept}`,
    '\r\n',
  ].join('\r\n'));
  sockets.add(socket);
  let buffer = Buffer.alloc(0);
  socket.on('close', () => sockets.delete(socket));
  socket.on('data', async (chunk) => {
    buffer = Buffer.concat([buffer, chunk]);
    const parsed = parseFrames(buffer);
    buffer = parsed.rest;
    for (const frame of parsed.frames) {
      if (frame.opcode === 0x8) { socket.end(); continue; }
      if (frame.opcode !== 0x1) continue;
      const message = JSON.parse(frame.payload.toString('utf8'));
      if (message.method === 'Runtime.evaluate') {
        try {
          send(socket, runtimeValue(message.id, await evaluate(message.params?.expression || '')));
        } catch (error) {
          send(socket, { id: message.id, error: { code: -32000, message: error.message } });
        }
      } else if (message.method === 'Input.dispatchKeyEvent') {
        if (message.params?.type === 'keyUp' && message.params?.key === 'Enter') await startTask();
        send(socket, { id: message.id, result: {} });
      } else {
        send(socket, { id: message.id, result: {} });
      }
    }
  });
});

await new Promise((resolveListen) => server.listen(port, '127.0.0.1', resolveListen));
function shutdown() {
  for (const socket of sockets) {
    try { socket.destroy(); } catch {}
  }
  try { server.close(); } catch {}
  process.exit(0);
}
process.on('SIGTERM', shutdown);
process.on('SIGINT', shutdown);
