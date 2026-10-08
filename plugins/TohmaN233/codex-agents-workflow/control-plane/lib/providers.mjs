import { validateEndpoint } from './config.mjs';
import { nativeSpawnConfig } from './native-binding.mjs';

const MAX_RESPONSE_BYTES = 2 * 1024 * 1024;

function endpointClass(endpoint) {
  const parsed = new URL(endpoint);
  const loopback = ['localhost', '127.0.0.1', '::1', '[::1]'].includes(parsed.hostname);
  return loopback ? 'loopback' : 'https';
}

export function buildProviderAdapter(provider, stage, { env = process.env, allowDirectApi = false } = {}) {
  const base = {
    provider_id: provider.id,
    provider_name: provider.name,
    kind: provider.kind,
    read_only: stage.access === 'read_only',
    capabilities: provider.capabilities,
    requires_user_approval: Boolean(
      provider.requires_user_approval || stage.requires_user_approval,
    ),
  };

  if (provider.kind === 'native_agent') {
    const spawn = nativeSpawnConfig(provider);
    return {
      ...base,
      execution: 'native_agent',
      agent_type: provider.config.agent_type,
      fork_turns: spawn.fork_turns,
      spawn_config: spawn,
      role: provider.config.role,
      expected_model: provider.config.model,
      expected_reasoning_effort: provider.config.reasoning_effort,
      requested_sandbox: stage.access === 'read_only' ? 'read-only' : 'workspace-write',
    };
  }

  if (provider.kind === 'builtin_connector') {
    const identityFields = provider.config.connector === 'grok_acp'
      ? ['task_id', 'session_id', 'run_id']
      : provider.config.connector === 'cursor_cdp'
        ? ['task_id', 'agent_id', 'target_id']
        : ['task_id'];
    return {
      ...base,
      execution: 'builtin_connector',
      connector: provider.config.connector,
      transport: provider.config.transport,
      prompt_delivery: 'internal',
      operations: {
        probe: 'codex_agents_workflow_connector_probe',
        start: 'codex_agents_workflow_connector_start',
        status: 'codex_agents_workflow_connector_status',
        control: 'codex_agents_workflow_connector_control',
      },
      identity_fields: identityFields,
      connection_state: 'unprobed',
    };
  }

  if (provider.kind === 'external_mcp' || provider.kind === 'mcp_tool') {
    return {
      ...base,
      execution: 'external_mcp',
      availability: 'unverified',
      protocol: provider.config.protocol,
      model_label: provider.config.model_label,
      tools: provider.config.tools,
      defaults: provider.config.defaults,
      notes: provider.config.notes || null,
    };
  }

  if (provider.kind === 'web_review') {
    return {
      ...base,
      execution: 'packet_review',
      skill: provider.config.skill,
      source_repository: provider.config.source_repository || null,
      review_path: provider.config.path,
      review_route: 'packet.inspect',
      packet_format: 'zip',
      review_role: 'reviewer',
      reviewer: provider.config.reviewer,
      model_label: provider.config.model_label || null,
      ambient_repository_access: false,
      can_write: false,
    };
  }

  if (provider.kind === 'openai_compatible') {
    const credentialReady = provider.config.auth_type === 'none'
      || Boolean(env[provider.config.api_key_env]);
    return {
      ...base,
      execution: 'direct_api',
      model: provider.config.model,
      endpoint_class: endpointClass(provider.config.endpoint),
      direct_invoke_enabled: Boolean(allowDirectApi),
      credential_ready: credentialReady,
      text_only: true,
      can_write: false,
    };
  }

  throw new Error(`unsupported provider kind: ${provider.kind}`);
}

export function buildCodexThreadAdapter(provider, envelope, options = {}) {
  const native = buildProviderAdapter(provider, { access: envelope.access }, options);
  if (native.execution !== 'native_agent') {
    const error = new Error('Codex task threads require a registered native Codex Provider');
    error.code = 'THREAD_PROVIDER_UNSUPPORTED';
    throw error;
  }
  return {
    ...native,
    execution: 'codex_thread',
    lifecycle: envelope.thread.lifecycle,
    ...(envelope.thread.lifecycle === 'continue' ? { thread_id: envelope.thread.source.thread_id } : {}),
  };
}

function extractText(payload) {
  const messageContent = payload?.choices?.[0]?.message?.content;
  if (typeof messageContent === 'string') return messageContent;
  if (Array.isArray(messageContent)) {
    const text = messageContent
      .map((part) => {
        if (typeof part === 'string') return part;
        if (part && typeof part.text === 'string') return part.text;
        return '';
      })
      .filter(Boolean)
      .join('\n');
    if (text) return text;
  }
  if (typeof payload?.choices?.[0]?.text === 'string') return payload.choices[0].text;
  if (typeof payload?.output_text === 'string') return payload.output_text;
  throw new Error('OpenAI-compatible response did not contain text content');
}

function abortError() {
  const error = new Error('provider response body read aborted');
  error.name = 'AbortError';
  return error;
}

function awaitWithAbort(value, signal) {
  if (!signal) return Promise.resolve(value);
  if (signal.aborted) return Promise.reject(abortError());
  return new Promise((resolve, reject) => {
    const onAbort = () => { cleanup(); reject(abortError()); };
    const cleanup = () => signal.removeEventListener('abort', onAbort);
    signal.addEventListener('abort', onAbort, { once: true });
    Promise.resolve(value).then(result => { cleanup(); resolve(result); }, error => { cleanup(); reject(error); });
  });
}

async function readBoundedBody(response, signal) {
  const declared = Number(response.headers.get('content-length') || '0');
  if (declared > MAX_RESPONSE_BYTES) {
    try { await response.body?.cancel?.('response too large'); } catch {}
    throw new Error(`provider response exceeds ${MAX_RESPONSE_BYTES} bytes`);
  }
  if (!response.body || typeof response.body.getReader !== 'function') {
    const text = await awaitWithAbort(response.text(), signal);
    if (Buffer.byteLength(text, 'utf8') > MAX_RESPONSE_BYTES) {
      throw new Error(`provider response exceeds ${MAX_RESPONSE_BYTES} bytes`);
    }
    return text;
  }
  const reader = response.body.getReader();
  const chunks = [];
  let total = 0;
  try {
    while (true) {
      const { done, value } = await awaitWithAbort(reader.read(), signal);
      if (done) break;
      total += value.byteLength;
      if (total > MAX_RESPONSE_BYTES) {
        await reader.cancel('response too large').catch(() => {});
        throw new Error(`provider response exceeds ${MAX_RESPONSE_BYTES} bytes`);
      }
      chunks.push(Buffer.from(value));
    }
  } finally {
    reader.releaseLock();
  }
  return Buffer.concat(chunks, total).toString('utf8');
}

export async function invokeOpenAICompatible(provider, prompt, {
  env = process.env,
  fetchImpl = globalThis.fetch,
  signal,
  assertActive,
} = {}) {
  if (provider.kind !== 'openai_compatible') {
    throw new Error('direct invocation supports only openai_compatible providers');
  }
  if (typeof fetchImpl !== 'function') throw new Error('fetch is unavailable in this Node runtime');
  const config = provider.config;
  const endpoint = validateEndpoint(config.endpoint);
  const headers = {
    'content-type': 'application/json',
    accept: 'application/json',
    ...config.headers,
  };
  if (config.auth_type !== 'none') {
    const apiKey = String(env[config.api_key_env] || '').trim();
    if (!apiKey) throw new Error(`required credential environment variable is not set: ${config.api_key_env}`);
    if (config.auth_type === 'bearer') headers.authorization = `Bearer ${apiKey}`;
    if (config.auth_type === 'x-api-key') headers['x-api-key'] = apiKey;
  }

  const messages = [];
  if (config.system_prompt) messages.push({ role: 'system', content: config.system_prompt });
  messages.push({ role: 'user', content: prompt });
  const body = {
    model: config.model,
    messages,
    temperature: config.temperature,
    [config.max_tokens_field]: config.max_output_tokens,
  };

  assertActive?.();
  if (signal?.aborted) throw Object.assign(new Error('Provider request was cancelled before submission'), { code: 'DIRECT_API_CANCELLED' });
  const controller = new AbortController();
  const abortExternal = () => controller.abort(signal.reason ?? new Error('Run cancelled'));
  signal?.addEventListener('abort', abortExternal, { once: true });
  const timeout = setTimeout(() => controller.abort(), config.timeout_ms);
  let response;
  try {
    response = await fetchImpl(endpoint, {
      method: 'POST',
      headers,
      body: JSON.stringify(body),
      signal: controller.signal,
      redirect: 'error',
    });
    // Keep the same abort signal active through body consumption. A provider
    // that sends headers and then stalls must still be bounded by timeout_ms.
    const raw = await readBoundedBody(response, controller.signal);
    let payload;
    try {
      payload = JSON.parse(raw);
    } catch (error) {
      throw new Error(`provider returned non-JSON response (${response.status}): ${error.message}`);
    }
    if (!response.ok) {
      const detail = payload?.error?.message || payload?.message || `HTTP ${response.status}`;
      throw new Error(`provider rejected request: ${detail}`);
    }
    return {
      text: extractText(payload).trim(),
      model: payload.model || config.model,
      usage: payload.usage || null,
      provider_response_id: payload.id || null,
    };
  } catch (error) {
    if (signal?.aborted) {
      try { await response?.body?.cancel?.('Run cancelled provider request'); } catch {}
      throw Object.assign(new Error('Provider request was cancelled with its Run'), { code: 'DIRECT_API_CANCELLED' });
    }
    if (controller.signal.aborted || error?.name === 'AbortError') {
      try { await response?.body?.cancel?.('provider request timed out'); } catch {}
      throw new Error(`provider request timed out after ${config.timeout_ms}ms`);
    }
    if (!response) throw new Error(`provider request failed: ${error.message}`);
    throw error;
  } finally {
    clearTimeout(timeout);
    signal?.removeEventListener('abort', abortExternal);
  }
}
