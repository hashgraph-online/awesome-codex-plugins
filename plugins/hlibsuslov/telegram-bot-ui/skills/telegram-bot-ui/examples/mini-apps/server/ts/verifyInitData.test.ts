// node --test: the shared vectors (server/vectors.json, made by make_vectors.py) verify, tampering fails.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createPublicKey, verify } from 'node:crypto';
import { readFileSync } from 'node:fs';
import {
  InitDataError, checkString, fromAuthorization, parse, secretKey, verifyEd25519, verifyHmac,
} from './verifyInitData.ts';

const V = JSON.parse(readFileSync(new URL('../vectors.json', import.meta.url), 'utf8'));
const opts = { botToken: V.bot_token, now: V.now };
const edOpts = { botId: V.bot_id, publicKeyHex: V.ed25519_public_key, now: V.now };

function mutate(raw: string, key: string, value: string | null): string {
  const p = new URLSearchParams(raw);
  if (value === null) p.delete(key); else p.set(key, value);
  return p.toString();
}

test('HMAC: the vector verifies and decodes user', () => {
  const data = verifyHmac(V.init_data, opts);
  assert.equal((data.user as { id: number }).id, V.expect.user_id);
  assert.equal(data.start_param, V.expect.start_param);
});

test('HMAC: check string keeps signature and drops hash, sorted', () => {
  assert.equal(checkString(parse(V.init_data), ['hash']), V.hmac_check_string);
  assert.ok(V.hmac_check_string.includes('signature='));
});

test('HMAC: a derived secret key works instead of the token', () => {
  assert.ok(verifyHmac(V.init_data, { key: secretKey(V.bot_token), now: V.now }));
});

test('HMAC: tampering, a wrong token, duplicates and malformed hashes fail', () => {
  const bad = [
    mutate(V.init_data, 'start_param', 'order-9999'),
    mutate(V.init_data, 'user', '{"id":1}'),
    mutate(V.init_data, 'signature', null),
    mutate(V.init_data, 'hash', 'a'.repeat(64)),
    mutate(V.init_data, 'hash', 'zz'),
    mutate(V.init_data, 'hash', null),
    `${V.init_data}&start_param=order-1`,
  ];
  for (const raw of bad) assert.throws(() => verifyHmac(raw, opts), InitDataError, raw.slice(-40));
  assert.throws(() => verifyHmac(V.init_data, { botToken: '12345:OTHER', now: V.now }), /hash mismatch/);
  assert.throws(() => verifyHmac('', opts), /empty/);
});

test('HMAC: expiry and clock skew', () => {
  assert.throws(() => verifyHmac(V.init_data, { ...opts, now: V.now + 86400 }), /expired/);
  assert.throws(() => verifyHmac(V.init_data, { ...opts, maxAge: 60 }), /expired/);
  assert.throws(() => verifyHmac(V.init_data, { ...opts, now: V.now - 3600 }), /future/);
  assert.ok(verifyHmac(V.init_data, { ...opts, now: V.now + 86400, maxAge: null }));
});

test('Ed25519: the vector verifies without the token', () => {
  const data = verifyEd25519(V.init_data, edOpts);
  assert.equal(data.query_id, V.expect.query_id);
  assert.equal(checkString(parse(V.init_data), ['hash', 'signature']), V.ed25519_check_string.split('\n').slice(1).join('\n'));
});

test('Ed25519: wrong bot id, Telegram key instead of the test key, tampering fail', () => {
  assert.throws(() => verifyEd25519(V.init_data, { ...edOpts, botId: 54321 }), /signature mismatch/);
  assert.throws(() => verifyEd25519(V.init_data, { botId: V.bot_id, now: V.now }), /signature mismatch/); // prod key
  assert.throws(() => verifyEd25519(mutate(V.init_data, 'auth_date', String(V.now)), edOpts), /signature mismatch/);
  assert.throws(() => verifyEd25519(mutate(V.init_data, 'signature', null), edOpts), /signature missing/);
  assert.throws(() => verifyEd25519(mutate(V.init_data, 'signature', 'abc'), edOpts), /malformed/);
});

test('Ed25519: RFC 8032 vectors through node:crypto', () => {
  for (const r of V.rfc8032) {
    const key = createPublicKey({ key: Buffer.concat([Buffer.from('302a300506032b6570032100', 'hex'), Buffer.from(r.public, 'hex')]), format: 'der', type: 'spki' });
    assert.equal(verify(null, Buffer.from(r.message, 'hex'), key, Buffer.from(r.signature, 'hex')), true);
  }
});

test('Authorization header helper', () => {
  assert.ok(fromAuthorization(`tma ${V.init_data}`, V.bot_token, { now: V.now }));
  assert.throws(() => fromAuthorization(`Bearer ${V.init_data}`, V.bot_token), /Authorization/);
  assert.throws(() => fromAuthorization(undefined, V.bot_token), /Authorization/);
});

test('a newline inside a value cannot fold the next field into it (same signed text)', () => {
  const p = new URLSearchParams(V.init_data);
  const user = p.get('user')!;
  p.delete('user');
  p.set('start_param', `${p.get('start_param')}\nuser=${user}`);
  assert.throws(() => verifyHmac(p.toString(), opts), /malformed/);
  assert.throws(() => verifyEd25519(p.toString(), edOpts), /malformed/);
  assert.throws(() => verifyHmac(`${V.init_data}&Bad-Key=1`, opts), /malformed/);
});

test('signature spelling is strict', () => {
  const p = new URLSearchParams(V.init_data);
  p.set('signature', `${p.get('signature')}!`);
  assert.throws(() => verifyEd25519(p.toString(), edOpts), /malformed/);
});
