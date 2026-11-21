#!/usr/bin/env node
// probe.mjs: send one HTTP request once, several times in a row, or several times at once,
// and report what the server answered and how a watched number (a balance) moved.
// It is for testing your own app on your own machine: targets must be loopback addresses
// unless you name the host with --allow-host. No dependencies, Node 20 or newer.
import { readFileSync, writeFileSync } from 'node:fs';
import { pathToFileURL } from 'node:url';

const MAX_TIMES = 20;
const MAX_PARALLEL = 50;
const TIMEOUT_MS = 15_000;

const USAGE = `Usage:
  node probe.mjs send   <request.json> [options]      one request
  node probe.mjs replay <request.json> --times 2      the same request again and again, in order
  node probe.mjs race   <request.json> --parallel 10  the same request many times at once

<request.json> is a file (or inline JSON) with:
  { "method": "POST", "url": "http://127.0.0.1:3000/api/spend",
    "headers": { "authorization": "Bearer ..." },
    "body": { "item": "boost" } }            or "rawBody": "exact text" for signed payloads

Options:
  --set-header name=value   add or replace a header (repeatable)
  --drop-header name        remove a header (repeatable)
  --set-query name=value    add or replace a query parameter (repeatable)
  --drop-query name         remove a query parameter (repeatable)
  --set-body path=value     set a JSON body field, dots for nesting (repeatable)
  --drop-body path          remove a JSON body field (repeatable)
  --observe <observe.json>  a request plus "path": the number at that JSON path in the
                            response is read before and after, and the change is reported
                            (repeatable; "path" may end in .length to count a list)
  --var NAME=value          replace {{NAME}} in the request and observe specs, so tokens and
                            keys stay out of files; the output shows {{NAME}}, not the value
  {{i}}                     in the request or an edit, the number of each request: 1 to N for
                            replay and race, 1 for send (an idempotency key or account per request)
  --extract path            print only the value at that JSON path of the response, for
                            passing a token or an id from one call to the next
  --times N                 for replay, 2 to ${MAX_TIMES} (default 2)
  --parallel N              for race, 2 to ${MAX_PARALLEL} (default 10)
  --allow-host <hostname>   allow one non-loopback host that you own and may test
  --out <file>              also write the result to a file
`;

class UsageError extends Error {}

function parseArgs(argv) {
  const [mode, requestArg, ...rest] = argv;
  if (!['send', 'replay', 'race'].includes(mode) || !requestArg) throw new UsageError(USAGE);
  const options = { mode, requestArg, edits: [], observe: [], vars: {}, times: 2, parallel: 10 };
  const editFlags = ['set-header', 'drop-header', 'set-query', 'drop-query', 'set-body', 'drop-body'];
  for (let i = 0; i < rest.length; i += 2) {
    const flag = rest[i].replace(/^--/, '');
    const value = rest[i + 1];
    if (!rest[i].startsWith('--') || value === undefined) throw new UsageError(`Bad option near "${rest[i]}".\n\n${USAGE}`);
    if (editFlags.includes(flag)) options.edits.push({ flag, value });
    else if (flag === 'observe') options.observe.push(value);
    else if (flag === 'var') {
      const [name, v] = splitPair(value, flag);
      if (!/^\w+$/.test(name)) throw new UsageError(`--var names use letters, digits and underscores, got "${name}".`);
      if (name === 'i') throw new UsageError('{{i}} is the number of each request. Name the variable something else.');
      options.vars[name] = v;
    } else if (flag === 'extract') options.extract = value;
    else if (flag === 'times') options.times = Number(value);
    else if (flag === 'parallel') options.parallel = Number(value);
    else if (flag === 'allow-host') options.allowHost = value.toLowerCase();
    else if (flag === 'out') options.out = value;
    else throw new UsageError(`Unknown option --${flag}.\n\n${USAGE}`);
  }
  if (!Number.isInteger(options.times) || options.times < 2 || options.times > MAX_TIMES) {
    throw new UsageError(`--times must be a whole number from 2 to ${MAX_TIMES}.`);
  }
  if (!Number.isInteger(options.parallel) || options.parallel < 2 || options.parallel > MAX_PARALLEL) {
    throw new UsageError(`--parallel must be a whole number from 2 to ${MAX_PARALLEL}.`);
  }
  return options;
}

function loadSpec(arg, what, vars = {}, numbered = false) {
  let text = arg;
  if (!arg.trim().startsWith('{')) {
    try {
      text = readFileSync(arg, 'utf8');
    } catch {
      throw new UsageError(`Cannot read the ${what} file "${arg}".`);
    }
  }
  let spec;
  try {
    spec = JSON.parse(text);
  } catch (err) {
    throw new UsageError(`The ${what} is not valid JSON: ${err.message}`);
  }
  // {{NAME}} is filled in after parsing, so a value can never change the shape of the
  // spec. Inside the URL the value is percent-encoded, except a placeholder at the very
  // start, which stands for the base URL ("{{BASE}}/api/me") and is used as written.
  // {{i}} stays for now: each request gets its own number when it is sent.
  const fill = (node, encode) => {
    if (typeof node === 'string') {
      return node.replace(/\{\{(\w+)\}\}/g, (match, name, at) => {
        if (name === 'i') {
          if (numbered) return match;
          throw new UsageError(`{{i}} numbers the requests that are sent. The ${what} cannot use it.`);
        }
        if (!Object.hasOwn(vars, name)) throw new UsageError(`The ${what} uses {{${name}}}. Pass --var ${name}=value.`);
        return encode && at > 0 ? encodeURIComponent(vars[name]) : vars[name];
      });
    }
    if (Array.isArray(node)) return node.map((item) => fill(item, false));
    if (typeof node === 'object' && node !== null) {
      return Object.fromEntries(Object.entries(node).map(([key, value]) => [key, fill(value, node === spec && key === 'url')]));
    }
    return node;
  };
  spec = fill(spec, false);
  if (typeof spec.url !== 'string') throw new UsageError(`The ${what} needs a "url".`);
  if (!URL.canParse(spec.url)) throw new UsageError(`The ${what} has a "url" that is not a full URL: ${redactor(vars)(spec.url)}`);
  if (spec.body !== undefined && spec.rawBody !== undefined) {
    throw new UsageError(`The ${what} has both "body" and "rawBody". Use one.`);
  }
  return { method: 'GET', headers: {}, ...spec };
}

function isLoopback(hostname) {
  const host = hostname.replace(/^\[|\]$/g, '').toLowerCase();
  return host === 'localhost' || host === '::1' || /^127(\.\d{1,3}){3}$/.test(host);
}

function checkTarget(url, allowHost) {
  const { protocol, hostname } = new URL(url);
  if (protocol !== 'http:' && protocol !== 'https:') throw new UsageError(`Unsupported URL: ${url}`);
  if (isLoopback(hostname) || hostname.toLowerCase() === allowHost) return;
  throw new UsageError(
    `Refusing to send to ${hostname}. This tool is for apps running on your own machine.\n` +
      `If ${hostname} is a test system you own, repeat the command with --allow-host ${hostname}`,
  );
}

function splitPair(value, flag) {
  const at = value.indexOf('=');
  if (at < 1) throw new UsageError(`--${flag} expects name=value, got "${value}".`);
  return [value.slice(0, at), value.slice(at + 1)];
}

function literal(text) {
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

function editBody(body, pathText, value, remove) {
  const keys = pathText.split('.');
  let node = body;
  for (const key of keys.slice(0, -1)) {
    if (typeof node[key] !== 'object' || node[key] === null) node[key] = {};
    node = node[key];
  }
  if (remove) delete node[keys.at(-1)];
  else node[keys.at(-1)] = value;
}

function applyEdits(spec, edits) {
  const url = new URL(spec.url);
  const headers = Object.fromEntries(Object.entries(spec.headers).map(([k, v]) => [k.toLowerCase(), String(v)]));
  let body = spec.body === undefined ? undefined : structuredClone(spec.body);
  let rawBody = spec.rawBody;
  const bodyEdits = edits.filter((e) => e.flag.endsWith('-body'));
  if (bodyEdits.length && body === undefined) {
    try {
      body = JSON.parse(rawBody ?? '');
      rawBody = undefined;
    } catch {
      throw new UsageError('Body edits need a JSON body. This request has none, or its rawBody is not JSON.');
    }
  }
  for (const { flag, value } of edits) {
    if (flag === 'set-header') {
      const [name, v] = splitPair(value, flag);
      headers[name.toLowerCase()] = v;
    } else if (flag === 'drop-header') delete headers[value.toLowerCase()];
    else if (flag === 'set-query') url.searchParams.set(...splitPair(value, flag));
    else if (flag === 'drop-query') url.searchParams.delete(value);
    else if (flag === 'set-body') {
      const [pathText, v] = splitPair(value, flag);
      editBody(body, pathText, literal(v), false);
    } else if (flag === 'drop-body') editBody(body, value, undefined, true);
  }
  if (body !== undefined) {
    rawBody = JSON.stringify(body);
    headers['content-type'] ??= 'application/json';
  }
  return { method: String(spec.method).toUpperCase(), url: url.toString(), headers, rawBody };
}

// {{i}} survives the URL parser as %7B%7Bi%7D%7D.
const INDEX = /\{\{i\}\}|%7B%7Bi%7D%7D/gi;
function withIndex(request, n) {
  const put = (text) => text.replace(INDEX, String(n));
  return {
    ...request,
    url: put(request.url),
    headers: Object.fromEntries(Object.entries(request.headers).map(([k, v]) => [k, put(v)])),
    rawBody: request.rawBody === undefined ? undefined : put(request.rawBody),
  };
}

async function fire(request) {
  const started = performance.now();
  try {
    const res = await fetch(request.url, {
      method: request.method,
      headers: request.headers,
      body: ['GET', 'HEAD'].includes(request.method) ? undefined : request.rawBody,
      redirect: 'manual',
      signal: AbortSignal.timeout(TIMEOUT_MS),
    });
    return { status: res.status, body: await res.text(), ms: Math.round(performance.now() - started) };
  } catch (err) {
    return { status: 0, body: `no response: ${err.cause?.code || err.name}`, ms: Math.round(performance.now() - started) };
  }
}

const SENSITIVE_HEADER = /key|token|secret|auth|signature|cookie/i;
const SENSITIVE_FIELD = /"([^"]*(?:token|secret|password|api_?key)[^"]*)"\s*:\s*"[^"]*"/gi;
// A valid signature in a query string stays valid for that request, so it is not echoed either.
const SENSITIVE_QUERY = /([?&\s](?:hash|sig|signature|token|key|secret)[\w.-]*=)(?!\{\{)[^&\s]*/gi;
const maskQuery = (text) => text.replace(SENSITIVE_QUERY, '$1***');
// A sign-up or login answers with a fresh session token. It is shown masked, so saved output stays safe to keep.
const maskFields = (text) => text.replace(SENSITIVE_FIELD, '"$1":"***"');

// Nothing a caller passed as a variable, and no credential header, is echoed back.
function redactor(vars) {
  const values = Object.entries(vars).filter(([, v]) => v.length >= 4).sort((a, b) => b[1].length - a[1].length);
  return (text) => values.reduce((out, [name, v]) => out.split(v).join(`{{${name}}}`).split(encodeURIComponent(v)).join(`{{${name}}}`), String(text));
}

function describeEdit({ flag, value }, redact) {
  if (flag === 'set-header') {
    const [name, v] = splitPair(value, flag);
    return `${flag} ${name}=${SENSITIVE_HEADER.test(name) ? '***' : redact(v)}`;
  }
  return flag === 'set-query' ? maskQuery(`${flag} ${redact(value)}`) : `${flag} ${redact(value)}`;
}

const atPath = (node, pathText) => String(pathText).split('.').reduce((n, key) => n?.[key], node);

async function readNumber(observe) {
  const res = await fire(applyEdits(observe, []));
  if (res.status < 200 || res.status > 299) {
    throw new UsageError(`The --observe request answered ${res.status || res.body}. It must succeed.`);
  }
  let value;
  try {
    value = atPath(JSON.parse(res.body), observe.path);
  } catch {
    value = undefined;
  }
  if (typeof value !== 'number') throw new UsageError(`No number at "${observe.path}" in the --observe response.`);
  return value;
}

export async function runProbe(options) {
  const vars = options.vars ?? {};
  const redact = redactor(vars);
  const spec = loadSpec(options.requestArg, 'request', vars, true);
  const request = applyEdits(spec, options.edits);
  checkTarget(request.url, options.allowHost);
  const observes = [options.observe ?? []].flat().map((arg) => {
    const observe = loadSpec(arg, '--observe request', vars);
    if (typeof observe.path !== 'string') throw new UsageError('The --observe request needs a "path".');
    checkTarget(observe.url, options.allowHost);
    return observe;
  });

  const before = [];
  for (const observe of observes) before.push(await readNumber(observe));
  const started = performance.now();
  let results;
  if (options.mode === 'send') results = [await fire(withIndex(request, 1))];
  else if (options.mode === 'replay') {
    results = [];
    for (let i = 1; i <= options.times; i += 1) results.push(await fire(withIndex(request, i)));
  } else {
    results = await Promise.all(Array.from({ length: options.parallel }, (_, i) => fire(withIndex(request, i + 1))));
  }
  const ms = Math.round(performance.now() - started);
  const after = [];
  for (const observe of observes) after.push(await readNumber(observe));

  const statuses = {};
  const samples = [];
  for (const r of results) {
    statuses[r.status] = (statuses[r.status] || 0) + 1;
    const shown = maskFields(redact(r.body));
    const body = shown.length > 300 ? `${shown.slice(0, 300)}...` : shown;
    if (samples.length < 4 && !samples.some((s) => s.status === r.status && s.body === body)) {
      samples.push({ status: r.status, body });
    }
  }
  const result = {
    probe: options.mode,
    request: maskQuery(redact(`${request.method} ${request.url.replace(INDEX, '{{i}}')}`)),
    edits: options.edits.map((e) => describeEdit(e, redact)),
    sent: results.length,
    statuses,
    samples,
    ms,
  };
  const observed = observes.map((observe, i) => ({
    ...(observe.name ? { name: String(observe.name) } : {}),
    path: observe.path,
    before: before[i],
    after: after[i],
    delta: Number((after[i] - before[i]).toFixed(6)),
  }));
  if (observed.length) result.observed = observed.length === 1 ? observed[0] : observed;
  if (options.extract) {
    let value;
    try {
      value = atPath(JSON.parse(results[0].body), options.extract);
    } catch {
      value = undefined;
    }
    if (value === undefined) {
      throw new UsageError(`No value at "${options.extract}" in the response (status ${results[0].status}): ${maskFields(redact(results[0].body)).slice(0, 200)}`);
    }
    result.extracted = value;
  }
  return result;
}

async function main() {
  try {
    const options = parseArgs(process.argv.slice(2));
    const { extracted, ...result } = await runProbe(options);
    const text = JSON.stringify(result, null, 2);
    if (options.out) writeFileSync(options.out, `${text}\n`);
    if (options.extract) console.log(typeof extracted === 'string' ? extracted : JSON.stringify(extracted));
    else console.log(text);
  } catch (err) {
    if (!(err instanceof UsageError)) throw err;
    console.error(err.message);
    process.exitCode = 2;
  }
}

if (import.meta.url === pathToFileURL(process.argv[1] || '').href) await main();
