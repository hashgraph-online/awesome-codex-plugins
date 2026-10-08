#!/usr/bin/env node
import readline from 'node:readline';
import { writeFile } from 'node:fs/promises';
import { join } from 'node:path';

const args = process.argv.slice(2);
if (args[0] === 'agent' && args[1] === 'leader') {
  process.on('SIGTERM', () => process.exit(0));
  process.on('SIGINT', () => process.exit(0));
  const exitMs = Number(process.env.FAKE_GROK_LEADER_EXIT_MS || 0);
  if (exitMs > 0) setTimeout(() => process.exit(17), exitMs);
  setInterval(() => {}, 1000);
} else if (args[0] === 'leader' && args.includes('info') && args.includes('--json')) {
  process.stdout.write(`${JSON.stringify({ pid: process.pid, status: 'ready' })}\n`);
  process.exit(0);
} else if (args[0] === 'leader' && args.at(-1) === 'kill') {
  process.exit(0);
} else if (args.includes('stdio')) {
  const rl = readline.createInterface({ input: process.stdin, crlfDelay: Infinity });
  let promptRequest = null;
  let nextClientRequestId = 900;
  let pendingAction = null;
  const send = (message) => process.stdout.write(`${JSON.stringify(message)}\n`);
  const respond = (id, result) => send({ jsonrpc: '2.0', id, result });
  const complete = (text = 'fixture result', stopReason = 'end_turn') => {
    send({ jsonrpc: '2.0', method: 'session/update', params: {
      sessionId: '11111111-1111-7111-8111-111111111111',
      update: { sessionUpdate: 'agent_message_chunk', content: { type: 'text', text } },
    } });
    const requestId = promptRequest;
    promptRequest = null;
    if (requestId) setTimeout(() => respond(requestId, { stopReason }), 10);
  };
  rl.on('line', async (line) => {
    const msg = JSON.parse(line);
    if (!msg.method && Object.hasOwn(msg, 'id')) {
      if (msg.id >= 900 && promptRequest && msg.result) {
        const outcome = msg.result?.outcome?.outcome;
        if (pendingAction?.kind === 'write' && outcome === 'selected') {
          const target = join(process.cwd(), pendingAction.path);
          await writeFile(target, pendingAction.text || 'grok allowed\n');
          complete('approved fixture write result');
        } else if (outcome === 'cancelled') {
          complete('permission denied fixture result');
        } else {
          complete('approved fixture result');
        }
        pendingAction = null;
      }
      return;
    }
    if (msg.method === 'initialize') {
      const delay = Number(process.env.FAKE_GROK_INIT_DELAY_MS || 0);
      if (delay) await new Promise(resolve => setTimeout(resolve, delay));
      respond(msg.id, { protocolVersion: 1, agentCapabilities: { loadSession: true } });
    } else if (msg.method === 'session/new') {
      respond(msg.id, { sessionId: '11111111-1111-7111-8111-111111111111' });
    } else if (msg.method === 'session/load') {
      respond(msg.id, {});
    } else if (msg.method === 'session/prompt') {
      promptRequest = msg.id;
      const text = msg.params?.prompt?.[0]?.text || '';
      if (text.includes('ASK_PERMISSION')) {
        send({ jsonrpc: '2.0', id: nextClientRequestId++, method: 'session/request_permission', params: {
          sessionId: '11111111-1111-7111-8111-111111111111',
          toolCall: { title: 'Fixture permission', toolCallId: 'fixture-tool' },
          options: [{ optionId: 'allow-once', name: 'Allow once', kind: 'allow_once' }],
        } });
      } else if (text.includes('GROK_WRITE_ALLOWED')) {
        pendingAction = { kind: 'write', path: 'allowed/grok.txt', text: 'grok allowed\n' };
        await import('node:fs/promises').then(({ mkdir }) => mkdir(join(process.cwd(), 'allowed'), { recursive: true }));
        send({ jsonrpc: '2.0', id: nextClientRequestId++, method: 'session/request_permission', params: {
          sessionId: '11111111-1111-7111-8111-111111111111',
          toolCall: { title: 'Write file', kind: 'write', path: 'allowed/grok.txt', toolCallId: 'grok-write-allowed' },
          options: [{ optionId: 'allow-once', name: 'Allow once', kind: 'allow_once' }],
        } });
      } else if (text.includes('GROK_WRITE_IGNORED_DIRECT')) {
        await writeFile(join(process.cwd(), 'ignored-grok.txt'), 'grok ignored outside\n');
        setTimeout(() => complete('wrote ignored outside file'), 350);
      } else if (text.includes('GROK_WRITE_OUTSIDE')) {
        pendingAction = { kind: 'write', path: 'outside-grok.txt', text: 'outside\n' };
        send({ jsonrpc: '2.0', id: nextClientRequestId++, method: 'session/request_permission', params: {
          sessionId: '11111111-1111-7111-8111-111111111111',
          toolCall: { title: 'Write file', kind: 'write', path: 'outside-grok.txt', toolCallId: 'grok-write-outside' },
          options: [{ optionId: 'allow-once', name: 'Allow once', kind: 'allow_once' }],
        } });
      } else if (text.includes('ASK_INPUT')) {
        send({ jsonrpc: '2.0', id: nextClientRequestId++, method: 'elicitation/create', params: {
          mode: 'form', sessionId: '11111111-1111-7111-8111-111111111111',
          message: 'Choose fixture value', requestedSchema: { type: 'object', properties: { value: { type: 'string' } }, required: ['value'] },
        } });
      } else if (text.includes('STDERR_SECRET')) {
        process.stderr.write('Authorization: Bearer fixture-secret token=fixture-token\n');
        process.exit(7);
      } else if (text.includes('WRITE_FILE')) {
        await writeFile(join(process.cwd(), 'unexpected.txt'), 'changed\n');
        complete('wrote unexpected file');
      } else if (text.includes('ACTIVITY_THEN_COMPLETE')) {
        let count = 0;
        const timer = setInterval(() => {
          count += 1;
          send({ jsonrpc: '2.0', method: 'session/update', params: {
            sessionId: '11111111-1111-7111-8111-111111111111',
            update: { sessionUpdate: 'tool_call_update', toolCallId: 'fixture-active-tool', status: 'in_progress' },
          } });
          if (count === 4) {
            clearInterval(timer);
            complete('active fixture result');
          }
        }, 400);
      } else if (!text.includes('HANG') && !text.includes('WAIT_FOR_CANCEL')) {
        complete();
      }
    } else if (msg.method === 'session/cancel') {
      if (process.env.FAKE_GROK_IGNORE_CANCEL === '1') return;
      complete('cancelled fixture result', 'cancelled');
    }
  });
} else {
  process.stderr.write(`unsupported fake grok args: ${JSON.stringify(args)}\n`);
  process.exit(2);
}
