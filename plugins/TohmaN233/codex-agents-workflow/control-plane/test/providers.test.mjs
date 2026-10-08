import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { mkdtemp } from 'node:fs/promises';
import { tmpdir } from './physical-tempdir.mjs';
import { join } from 'node:path';
import test from 'node:test';

import { loadConfig, saveConfig, validateEndpoint } from '../lib/config.mjs';
import { invokeSelection } from '../lib/control.mjs';
import { invokeOpenAICompatible } from '../lib/providers.mjs';
import { DEFAULT_CONFIG_PATH } from '../server.mjs';

test('endpoint validation requires HTTPS except loopback HTTP', () => {
  assert.equal(validateEndpoint('https://api.example.com/v1/chat/completions'), 'https://api.example.com/v1/chat/completions');
  assert.match(validateEndpoint('http://127.0.0.1:11434/v1/chat/completions'), /^http:\/\/127\.0\.0\.1/);
  assert.throws(() => validateEndpoint('http://api.example.com/v1/chat/completions'), /must use HTTPS/);
  assert.throws(() => validateEndpoint('https://user:pass@example.com/v1/chat/completions'), /must not contain credentials/);
  assert.throws(() => validateEndpoint('https://api.example.com/v1/chat/completions?key=bad'), /must not contain a query/);
});

test('direct OpenAI-compatible invocation is text-only and env-authenticated', async (t) => {
  let requestBody = null;
  let authorization = null;
  const mock = createServer(async (req, res) => {
    authorization = req.headers.authorization;
    const chunks = [];
    for await (const chunk of req) chunks.push(chunk);
    requestBody = JSON.parse(Buffer.concat(chunks).toString('utf8'));
    const body = JSON.stringify({
      id: 'mock-response',
      model: 'mock-model',
      choices: [{ message: { content: 'Advisory result' } }],
      usage: { total_tokens: 12 },
    });
    res.writeHead(200, { 'content-type': 'application/json', 'content-length': Buffer.byteLength(body) });
    res.end(body);
  });
  await new Promise((resolve) => mock.listen(0, '127.0.0.1', resolve));
  t.after(() => new Promise((resolve) => mock.close(resolve)));
  const address = mock.address();

  const dir = await mkdtemp(join(tmpdir(), 'sol-control-provider-'));
  const configPath = join(dir, 'control-plane.json');
  const config = await loadConfig({ configPath, defaultConfigPath: DEFAULT_CONFIG_PATH });
  config.global.allow_direct_api = true;
  const provider = config.providers.find((item) => item.id === 'custom-openai-compatible');
  provider.enabled = true;
  provider.config.endpoint = `http://127.0.0.1:${address.port}/v1/chat/completions`;
  provider.config.model = 'mock-model';
  const stage = config.task_types.find((item) => item.id === 'brainstorm').stages[0];
  stage.provider_id = provider.id;
  stage.requires_user_approval = true;
  await saveConfig(config, { configPath });

  const result = await invokeSelection({
    task_type_id: 'brainstorm',
    stage_id: 'implementation',
    task: 'Compare two parser designs.',
    context: 'Observed facts only.',
    constraints: 'No file changes.',
    verification: 'Return a discriminating check.',
    user_approved: true,
  }, {
    configPath,
    defaultConfigPath: DEFAULT_CONFIG_PATH,
    env: { CODEX_WORKFLOW_CUSTOM_API_KEY: 'example-fixture-secret' },
  });

  assert.equal(result.response.text, 'Advisory result');
  assert.equal(result.advisory_only, true);
  assert.equal(authorization, 'Bearer example-fixture-secret');
  assert.equal(requestBody.model, 'mock-model');
  assert.equal(requestBody.messages.at(-1).role, 'user');
  assert.match(requestBody.messages.at(-1).content, /Compare two parser designs/);
  assert.equal('tools' in requestBody, false);
  assert.doesNotMatch(JSON.stringify(result), /example-fixture-secret/);
});

test('direct API stays disabled until both provider and global switch allow it', async () => {
  const dir = await mkdtemp(join(tmpdir(), 'sol-control-provider-off-'));
  const configPath = join(dir, 'control-plane.json');
  const config = await loadConfig({ configPath, defaultConfigPath: DEFAULT_CONFIG_PATH });
  const provider = config.providers.find((item) => item.id === 'custom-openai-compatible');
  provider.enabled = true;
  const stage = config.task_types.find((item) => item.id === 'brainstorm').stages[0];
  stage.provider_id = provider.id;
  await saveConfig(config, { configPath });
  await assert.rejects(
    invokeSelection({
      task_type_id: 'brainstorm',
      stage_id: 'implementation',
      task: 'Advise.',
      user_approved: true,
    }, {
      configPath,
      defaultConfigPath: DEFAULT_CONFIG_PATH,
      env: { CODEX_WORKFLOW_CUSTOM_API_KEY: 'example-fixture-secret' },
    }),
    /direct API invocation is disabled/,
  );
});

test('direct API deadline also bounds a response body that stalls after headers', async () => {
  const dir = await mkdtemp(join(tmpdir(), 'sol-control-provider-body-timeout-'));
  const configPath = join(dir, 'control-plane.json');
  const config = await loadConfig({ configPath, defaultConfigPath: DEFAULT_CONFIG_PATH });
  const provider = config.providers.find((item) => item.id === 'custom-openai-compatible');
  provider.config.timeout_ms = 1000;
  const body = {
    getReader() {
      return {
        read: () => new Promise(() => {}),
        cancel: async () => {},
        releaseLock() {},
      };
    },
  };
  const started = Date.now();
  await assert.rejects(
    invokeOpenAICompatible(provider, 'body timeout', {
      env: { CODEX_WORKFLOW_CUSTOM_API_KEY: 'example-fixture-secret' },
      fetchImpl: async () => ({ ok: true, status: 200, headers: new Headers(), body }),
    }),
    /timed out after 1000ms/,
  );
  assert(Date.now() - started < 3000, `body timeout exceeded bound: ${Date.now() - started}ms`);
});

test('direct API cancels a response body rejected by declared size', async () => {
  let cancelled = 0;
  const body = {
    cancel: async () => { cancelled += 1; },
    getReader() { throw new Error('reader must not be acquired for an oversized declaration'); },
  };
  const dir = await mkdtemp(join(tmpdir(), 'sol-control-provider-size-'));
  const configPath = join(dir, 'control-plane.json');
  const config = await loadConfig({ configPath, defaultConfigPath: DEFAULT_CONFIG_PATH });
  const provider = config.providers.find((item) => item.id === 'custom-openai-compatible');
  await assert.rejects(
    invokeOpenAICompatible(provider, 'oversized response', {
      env: { CODEX_WORKFLOW_CUSTOM_API_KEY: 'example-fixture-secret' },
      fetchImpl: async () => ({
        ok: true,
        status: 200,
        headers: new Headers({ 'content-length': String(3 * 1024 * 1024) }),
        body,
      }),
    }),
    /provider response exceeds 2097152 bytes/,
  );
  assert.equal(cancelled, 1);
});
