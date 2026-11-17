#!/usr/bin/env node
// Prints a request file for scripts/probe.mjs that carries one correctly signed test event.
// The "webhook" and "postback" formulas are examples: replace them with the scheme the
// endpoint under test verifies. The provider modes follow the schemes in the provider
// references of this skill. Keep the secret in the environment: it must be the test secret
// from the local configuration, never a live one.
//
//   WEBHOOK_TEST_SECRET=... node sign-test-event.mjs webhook <type> '<data json>' [age in seconds]
//   WEBHOOK_TEST_SECRET=... node sign-test-event.mjs stripe <type> '<data.object json>' [age in seconds]
//   WEBHOOK_TEST_SECRET=... node sign-test-event.mjs paddle <event_type> '<data json>' [age in seconds]
//   WEBHOOK_TEST_SECRET=... node sign-test-event.mjs lemonsqueezy <event_name> '<data json>' ['<custom_data json>']
//   WEBHOOK_TEST_SECRET=... node sign-test-event.mjs revenuecat <type> '<event fields json>' [age in seconds]
//   POSTBACK_TEST_KEY=...   node sign-test-event.mjs postback user_id=42 tx=tx-1001 reward=200 status=1
//
// WEBHOOK_URL, POSTBACK_URL and SIGNATURE_HEADER override the defaults. EVENT_ID fixes the
// event id, so that the same event can be signed again later with a fresh timestamp.
import { createHmac, randomUUID } from 'node:crypto';
import { pathToFileURL } from 'node:url';

const USAGE = `usage: sign-test-event.mjs webhook <type> <data json> [age in seconds]
       sign-test-event.mjs stripe <type> <data.object json> [age in seconds]
       sign-test-event.mjs paddle <event_type> <data json> [age in seconds]
       sign-test-event.mjs lemonsqueezy <event_name> <data json> [custom_data json]
       sign-test-event.mjs revenuecat <type> <event fields json> [age in seconds]
       sign-test-event.mjs postback name=value [name=value ...]`;

class UsageError extends Error {}

const hmacHex = (secret, text) => createHmac('sha256', secret).update(text).digest('hex');

// t=<unix seconds>,v1=<hex HMAC-SHA256 of "<t>.<raw body>">. The generic example scheme,
// and the form of Stripe-Signature and of X-RevenueCat-Webhook-Signature.
export function timestampedHeader(secret, t, rawBody) {
  return `t=${t},v1=${hmacHex(secret, `${t}.${rawBody}`)}`;
}

// Paddle-Signature: ts=<unix seconds>;h1=<hex HMAC-SHA256 of "<ts>:<raw body>">.
export function paddleHeader(secret, ts, rawBody) {
  return `ts=${ts};h1=${hmacHex(secret, `${ts}:${rawBody}`)}`;
}

// X-Signature: <hex HMAC-SHA256 of the raw body>. Lemon Squeezy signs no timestamp.
export function lemonSqueezySignature(secret, rawBody) {
  return hmacHex(secret, rawBody);
}

// hash=<hex HMAC-SHA256 of the values, in the order given, joined by ":">.
export function postbackHash(key, values) {
  return hmacHex(key, values.join(':'));
}

function need(name) {
  const value = process.env[name];
  if (!value) throw new UsageError(`${name} is not set`);
  return value;
}

function parseJson(text, what) {
  try {
    const value = JSON.parse(text);
    if (typeof value === 'object' && value !== null && !Array.isArray(value)) return value;
  } catch {
    // reported below
  }
  throw new UsageError(`the ${what} argument is not a JSON object`);
}

function signedAt(age = '0') {
  if (!/^\d{1,9}$/.test(String(age))) throw new UsageError('the age must be a whole number of seconds');
  return Math.floor(Date.now() / 1000) - Number(age);
}

function request(path, headers, rawBody) {
  return {
    method: 'POST',
    url: process.env.WEBHOOK_URL ?? `http://127.0.0.1:3000${path}`,
    headers: { 'content-type': 'application/json', ...headers },
    rawBody,
  };
}

const eventId = (prefix) => process.env.EVENT_ID || `${prefix}${randomUUID()}`;

const modes = {
  webhook([type, dataJson, age]) {
    if (!type || !dataJson) throw new UsageError('webhook needs a type and a data object');
    const data = parseJson(dataJson, 'data');
    const rawBody = JSON.stringify({ id: eventId('evt_test_'), type, data });
    const header = timestampedHeader(need('WEBHOOK_TEST_SECRET'), signedAt(age), rawBody);
    return request('/webhooks/payments', { [process.env.SIGNATURE_HEADER ?? 'x-signature']: header }, rawBody);
  },

  stripe([type, objectJson, age]) {
    if (!type || !objectJson) throw new UsageError('stripe needs an event type and a data.object');
    const object = parseJson(objectJson, 'data.object');
    const t = signedAt(age);
    const rawBody = JSON.stringify({ id: eventId('evt_test_'), object: 'event', type, created: t, livemode: false, data: { object } });
    return request('/webhooks/stripe', { 'stripe-signature': timestampedHeader(need('WEBHOOK_TEST_SECRET'), t, rawBody) }, rawBody);
  },

  paddle([eventType, dataJson, age]) {
    if (!eventType || !dataJson) throw new UsageError('paddle needs an event type and a data object');
    const data = parseJson(dataJson, 'data');
    const ts = signedAt(age);
    const rawBody = JSON.stringify({
      event_id: eventId('evt_test_'),
      event_type: eventType,
      occurred_at: new Date(ts * 1000).toISOString(),
      notification_id: `ntf_test_${randomUUID()}`,
      data,
    });
    return request('/webhooks/paddle', { 'paddle-signature': paddleHeader(need('WEBHOOK_TEST_SECRET'), ts, rawBody) }, rawBody);
  },

  lemonsqueezy([eventName, dataJson, customJson]) {
    if (!eventName || !dataJson) throw new UsageError('lemonsqueezy needs an event name and a data object');
    const meta = { event_name: eventName };
    if (customJson) meta.custom_data = parseJson(customJson, 'custom_data');
    const rawBody = JSON.stringify({ meta, data: parseJson(dataJson, 'data') });
    return request(
      '/webhooks/lemonsqueezy',
      { 'x-event-name': eventName, 'x-signature': lemonSqueezySignature(need('WEBHOOK_TEST_SECRET'), rawBody) },
      rawBody,
    );
  },

  revenuecat([type, fieldsJson, age]) {
    if (!type || !fieldsJson) throw new UsageError('revenuecat needs an event type and the event fields');
    const t = signedAt(age);
    const event = { environment: 'SANDBOX', ...parseJson(fieldsJson, 'event fields'), id: eventId(''), type, event_timestamp_ms: t * 1000 };
    const rawBody = JSON.stringify({ api_version: '1.0', event });
    const headers = { 'x-revenuecat-webhook-signature': timestampedHeader(need('WEBHOOK_TEST_SECRET'), t, rawBody) };
    if (process.env.WEBHOOK_AUTHORIZATION) headers.authorization = process.env.WEBHOOK_AUTHORIZATION;
    return request('/webhooks/revenuecat', headers, rawBody);
  },

  postback(pairs) {
    if (pairs.length === 0) throw new UsageError('postback needs at least one name=value pair');
    const url = new URL(process.env.POSTBACK_URL ?? 'http://127.0.0.1:3000/postback');
    const values = [];
    for (const pair of pairs) {
      const at = pair.indexOf('=');
      if (at < 1) throw new UsageError(`"${pair}" is not name=value`);
      url.searchParams.set(pair.slice(0, at), pair.slice(at + 1));
      values.push(pair.slice(at + 1));
    }
    url.searchParams.set('hash', postbackHash(need('POSTBACK_TEST_KEY'), values));
    return { method: 'GET', url: url.toString() };
  },
};

export function buildRequest(mode, args) {
  if (!Object.hasOwn(modes, mode)) throw new UsageError(`unknown mode "${mode ?? ''}"`);
  return modes[mode](args);
}

if (import.meta.url === pathToFileURL(process.argv[1] || '').href) {
  const [mode, ...args] = process.argv.slice(2);
  try {
    if (!mode) throw new UsageError('no mode given');
    console.log(JSON.stringify(buildRequest(mode, args)));
  } catch (err) {
    if (!(err instanceof UsageError)) throw err;
    console.error(`sign-test-event: ${err.message}`);
    console.error(USAGE);
    process.exitCode = 2;
  }
}
