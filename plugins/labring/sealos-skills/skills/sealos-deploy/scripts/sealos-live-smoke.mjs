#!/usr/bin/env node
import process from "node:process";

function parseArgs(argv) {
  const args = {};
  for (let index = 2; index < argv.length; index += 1) {
    const token = argv[index];
    if (!token.startsWith("--")) {
      continue;
    }
    const key = token.slice(2);
    const next = argv[index + 1];
    if (!next || next.startsWith("--")) {
      args[key] = true;
      continue;
    }
    if (args[key] === undefined) {
      args[key] = next;
    } else if (Array.isArray(args[key])) {
      args[key].push(next);
    } else {
      args[key] = [args[key], next];
    }
    index += 1;
  }
  for (const [key, value] of Object.entries({ ...args })) {
    if (!key.includes("-")) {
      continue;
    }
    const camelKey = key.replace(/-([a-z])/g, (_, char) => char.toUpperCase());
    args[camelKey] = value;
  }
  return args;
}

function fail(message, extra = {}) {
  console.log(JSON.stringify({ ok: false, error: message, ...extra }, null, 2));
  process.exit(1);
}

function joinUrl(base, path) {
  if (path === undefined || path === null || path === "") {
    return new URL(base).toString();
  }
  return new URL(path, base).toString();
}

function redact(value) {
  if (!value || typeof value !== "string") {
    return value;
  }
  if (value.length <= 8) {
    return "***";
  }
  return `${value.slice(0, 4)}...${value.slice(-4)}`;
}

function compactString(key, value) {
  const sensitivePattern = /(token|secret|password|credential|apikey|api_key|authorization|session|cookie|jwt)/i;
  const bulkyPattern = /(base64|image|captcha|validateCodeBase64)/i;
  if (sensitivePattern.test(key)) {
    return redact(value);
  }
  if (bulkyPattern.test(key) || value.startsWith("data:image/") || value.length > 500) {
    return `<redacted:${value.length} chars>`;
  }
  return value;
}

function redactJson(value, key = "") {
  if (Array.isArray(value)) {
    return value.map((item) => redactJson(item, key));
  }
  if (!value || typeof value !== "object") {
    return typeof value === "string" ? compactString(key, value) : value;
  }
  return Object.fromEntries(Object.entries(value).map(([entryKey, entry]) => [entryKey, redactJson(entry, entryKey)]));
}

function getSetCookieHeaders(headers) {
  if (typeof headers.getSetCookie === "function") {
    return headers.getSetCookie();
  }
  const value = headers.get("set-cookie");
  if (!value) {
    return [];
  }
  return value.split(/,(?=\s*[^;,=\s]+=[^;]+)/g).map((entry) => entry.trim());
}

function updateCookieJar(jar, headers) {
  for (const cookie of getSetCookieHeaders(headers)) {
    const [pair, ...attributes] = cookie.split(";");
    const separatorIndex = pair.indexOf("=");
    if (separatorIndex <= 0) {
      continue;
    }
    const name = pair.slice(0, separatorIndex).trim();
    const value = pair.slice(separatorIndex + 1).trim();
    const deleted = attributes.some((attribute) => /^max-age=0$/i.test(attribute.trim()));
    if (deleted) {
      delete jar[name];
    } else {
      jar[name] = value;
    }
  }
}

function cookieHeader(jar) {
  const entries = Object.entries(jar);
  if (entries.length === 0) {
    return null;
  }
  return entries.map(([name, value]) => `${name}=${value}`).join("; ");
}

function csrfHeadersFromCookies(jar, args) {
  const cookiePrefix = args.csrfCookiePrefix || "CSRF-Token-";
  const headerPrefix = args.csrfHeaderPrefix || "X-CSRF-Token-";
  const entry = Object.entries(jar).find(([name]) => name.startsWith(cookiePrefix));
  if (!entry) {
    return {};
  }
  const [cookieName, value] = entry;
  return { [`${headerPrefix}${cookieName.slice(cookiePrefix.length)}`]: value };
}

const FAILURE_SIGNAL_PATTERNS = [
  {
    id: "application-error",
    pattern: /Application error/i,
  },
  {
    id: "server-side-exception",
    pattern: /server-side exception/i,
  },
  {
    id: "internal-server-error",
    pattern: /Internal Server Error/i,
  },
  {
    id: "unhandled-runtime-error",
    pattern: /Unhandled Runtime Error/i,
  },
  {
    id: "next-runtime-digest",
    pattern: /\bNEXT_[A-Z0-9_]+\b/i,
  },
];

function detectFailureSignals(text) {
  return FAILURE_SIGNAL_PATTERNS.filter(({ pattern }) => pattern.test(text)).map(({ id }) => id);
}

async function requestStep(name, url, options = {}, session = null) {
  const startedAt = Date.now();
  const cookie = session ? cookieHeader(session.cookies) : null;
  const response = await fetch(url, {
    redirect: "manual",
    ...options,
    headers: {
      "user-agent": "sealos-live-smoke/1.0",
      ...(cookie ? { cookie } : {}),
      ...(options.headers || {}),
    },
  });
  if (session) {
    updateCookieJar(session.cookies, response.headers);
  }
  const text = await response.text();
  const contentType = response.headers.get("content-type") || "";
  let json = null;
  if (contentType.includes("application/json")) {
    try {
      json = JSON.parse(text);
    } catch {
      json = null;
    }
  }
  const safeJson = redactJson(json);
  const failureSignals = detectFailureSignals(text);
  return {
    name,
    url,
    status: response.status,
    ok: response.status >= 200 && response.status < 400 && failureSignals.length === 0,
    elapsedMs: Date.now() - startedAt,
    contentType,
    location: response.headers.get("location"),
    setCookie: getSetCookieHeaders(response.headers).length ? "<present>" : null,
    bodyPreview: safeJson ? JSON.stringify(safeJson).slice(0, 240) : text.slice(0, 240),
    failureSignals,
    json: safeJson,
    rawJson: json,
  };
}

function detectJsonSuccess(step) {
  const json = step.json;
  if (!json || typeof json !== "object") {
    return null;
  }
  if (typeof json.success === "boolean") {
    return json.success;
  }
  if (typeof json.ok === "boolean") {
    return json.ok;
  }
  if (typeof json.code === "number" || (typeof json.code === "string" && /^\d+$/.test(json.code))) {
    const code = Number(json.code);
    return code === 0 || (code >= 200 && code < 400);
  }
  return null;
}

const DEFAULT_TOKEN_PATHS = ["data.access_token", "access_token", "data.token", "token"];

function valuesFromArg(value) {
  if (!value) {
    return [];
  }
  const values = Array.isArray(value) ? value : [value];
  return values.flatMap((entry) => String(entry).split(",").map((item) => item.trim()).filter(Boolean));
}

function valueAtPath(value, path) {
  const normalized = String(path || "")
    .trim()
    .replace(/^\$\.?/, "")
    .replace(/\[(['"]?)([^'"\]]+)\1\]/g, ".$2");
  if (!normalized) {
    return undefined;
  }
  return normalized.split(/[./]/).filter(Boolean).reduce((current, key) => {
    if (current === null || current === undefined || typeof current !== "object") {
      return undefined;
    }
    return current[key];
  }, value);
}

function tokenPathsFromArgs(args) {
  const configured = valuesFromArg(args.tokenPath || args.tokenPaths);
  return configured.length > 0 ? configured : DEFAULT_TOKEN_PATHS;
}

function extractToken(loginStep, args) {
  const payload = loginStep?.rawJson;
  for (const path of tokenPathsFromArgs(args)) {
    const candidate = valueAtPath(payload, path);
    if (typeof candidate === "string" && candidate.length > 0) {
      return { value: candidate, path };
    }
  }
  return null;
}

function authPathsFromArgs(args) {
  return valuesFromArg(args.authPath || args.authPaths);
}

function missingPathsFromArgs(args, key) {
  return valuesFromArg(args[key]);
}

function authHeaders(args, session, token) {
  const cookieAuthHeaders = args.loginMethod === "cookie-json" ? csrfHeadersFromCookies(session.cookies, args) : {};
  return { ...(token ? { authorization: `Bearer ${token}` } : {}), ...cookieAuthHeaders };
}

function expectedProbeStep(step, expectation, probeType) {
  const ok = expectation(step);
  return {
    ...step,
    ok,
    probeType,
    expected: expectation.expected || null,
    probeFailure: ok ? null : "unexpected_status",
  };
}

function acceptsMissingPage(step) {
  if (step.failureSignals.length > 0 || step.status === 0) {
    return false;
  }
  if (step.status === 404) {
    return true;
  }
  return step.status >= 200 && step.status < 400 && step.contentType.toLowerCase().includes("text/html");
}

const args = parseArgs(process.argv);
const baseUrl = args.url;

if (!baseUrl) {
  fail("usage: node sealos-live-smoke.mjs --url <url> [--captcha-path <path>] [--login-path <path>] [--login-method json-token|cookie-json] [--username <user>] [--password <pass>] [--token-path <path>] [--auth-path <path>] [--missing-api-path <path>] [--missing-page-path <path>]");
}

const steps = [];
const session = { cookies: {} };
const authPaths = authPathsFromArgs(args);
const missingApiPaths = missingPathsFromArgs(args, "missingApiPath");
const missingPagePaths = missingPathsFromArgs(args, "missingPagePath");
let tokenInfo = null;
let tokenError = null;
try {
  steps.push(await requestStep("root", joinUrl(baseUrl, args.rootPath), {}, session));

  if (args.captchaPath) {
    steps.push(await requestStep("captcha", joinUrl(baseUrl, args.captchaPath), {}, session));
  }

  if (args.loginPath && args.username && args.password) {
    const loginMethod = args.loginMethod || "json-token";
    const body = JSON.stringify({
      username: args.username,
      password: args.password,
      email: args.username,
    });
    const extraHeaders = loginMethod === "cookie-json" ? csrfHeadersFromCookies(session.cookies, args) : {};
    steps.push(
      await requestStep("login", joinUrl(baseUrl, args.loginPath), {
        method: "POST",
        headers: { "content-type": "application/json", ...extraHeaders },
        body,
      }, session),
    );
  }

  const loginStep = steps.find((step) => step.name === "login");
  tokenInfo = extractToken(loginStep, args);
  const tokenRequired = Boolean(loginStep) && (args.loginMethod || "json-token") === "json-token";
  if (tokenRequired && !tokenInfo) {
    tokenError = "token_not_found";
  }
  const token = tokenInfo?.value || null;
  for (const path of authPaths) {
    steps.push(
      await requestStep(`auth:${path}`, joinUrl(baseUrl, path), {
        headers: authHeaders(args, session, token),
      }, session),
    );
  }
  for (const path of missingApiPaths) {
    const step = await requestStep(`missing-api:${path}`, joinUrl(baseUrl, path), {
      headers: authHeaders(args, session, token),
    }, session);
    steps.push(expectedProbeStep(step, Object.assign((candidate) => candidate.status === 404 && candidate.failureSignals.length === 0, { expected: 404 }), "api"));
  }
  for (const path of missingPagePaths) {
    const step = await requestStep(`missing-page:${path}`, joinUrl(baseUrl, path), {
      headers: authHeaders(args, session, token),
    }, session);
    steps.push(expectedProbeStep(step, Object.assign(acceptsMissingPage, { expected: "404-or-html-2xx-3xx" }), "page"));
  }
} catch (error) {
  fail(error.message, { steps: steps.map(({ rawJson, ...step }) => step) });
}

const loginStep = steps.find((step) => step.name === "login");
const captchaStep = steps.find((step) => step.name === "captcha");
const rootStep = steps.find((step) => step.name === "root");
const authSteps = steps.filter((step) => step.name.startsWith("auth:"));
const missingApiSteps = steps.filter((step) => step.name.startsWith("missing-api:"));
const missingPageSteps = steps.filter((step) => step.name.startsWith("missing-page:"));
const loginJsonSuccess = loginStep ? detectJsonSuccess(loginStep) : null;
const captchaJsonSuccess = captchaStep ? detectJsonSuccess(captchaStep) : null;
const authSuccess = authSteps.every((step) => step.ok && detectJsonSuccess(step) !== false);
const missingApiSuccess = missingApiSteps.every((step) => step.ok);
const missingPageSuccess = missingPageSteps.every((step) => step.ok);
const findings = [];
if (tokenError) {
  findings.push({ code: tokenError, message: "Authenticated JSON flow did not expose a token at any configured path" });
}
for (const step of [...missingApiSteps, ...missingPageSteps]) {
  if (!step.ok) {
    findings.push({ code: step.probeFailure, probe: step.name, expected: step.expected, status: step.status });
  }
}

const report = {
  ok:
    Boolean(rootStep?.ok) &&
    (captchaStep ? captchaStep.ok && captchaJsonSuccess !== false : true) &&
    (loginStep ? loginStep.ok && loginJsonSuccess !== false : true) &&
    authSuccess &&
    missingApiSuccess &&
    missingPageSuccess &&
    !tokenError,
  url: baseUrl,
  loginMethod: args.loginMethod || (loginStep ? "json-token" : null),
  tokenPath: tokenInfo?.path || null,
  error: tokenError,
  findings,
  credentials: args.username ? { username: args.username, password: redact(args.password) } : null,
  steps: steps.map(({ rawJson, ...step }) => step),
};

console.log(JSON.stringify(report, null, 2));
process.exitCode = report.ok ? 0 : 1;
