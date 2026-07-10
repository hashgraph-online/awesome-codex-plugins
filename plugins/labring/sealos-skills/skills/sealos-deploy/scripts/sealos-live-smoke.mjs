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
  const sensitivePattern = /(token|secret|password|credential|apikey|api_key|authorization|session|cookie)/i;
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
  if (typeof json.code === "number") {
    return json.code >= 200 && json.code < 400;
  }
  return null;
}

function extractToken(loginStep) {
  const data = loginStep?.rawJson?.data;
  if (data?.token && typeof data.token === "string") {
    return data.token;
  }
  if (loginStep?.rawJson?.token && typeof loginStep.rawJson.token === "string") {
    return loginStep.rawJson.token;
  }
  return null;
}

function authPathsFromArgs(args) {
  const authPath = args.authPath || args.authPaths;
  if (!authPath) {
    return [];
  }
  return Array.isArray(authPath) ? authPath : String(authPath).split(",").filter(Boolean);
}

const args = parseArgs(process.argv);
const baseUrl = args.url;

if (!baseUrl) {
  fail("usage: node sealos-live-smoke.mjs --url <url> [--captcha-path <path>] [--login-path <path>] [--login-method json-token|cookie-json] [--username <user>] [--password <pass>] [--auth-path <path>]");
}

const steps = [];
const session = { cookies: {} };
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
  const token = extractToken(loginStep);
  for (const path of authPathsFromArgs(args)) {
    const cookieAuthHeaders = args.loginMethod === "cookie-json" ? csrfHeadersFromCookies(session.cookies, args) : {};
    steps.push(
      await requestStep(`auth:${path}`, joinUrl(baseUrl, path), {
        headers: { ...(token ? { authorization: `Bearer ${token}` } : {}), ...cookieAuthHeaders },
      }, session),
    );
  }
} catch (error) {
  fail(error.message, { steps: steps.map(({ rawJson, ...step }) => step) });
}

const loginStep = steps.find((step) => step.name === "login");
const captchaStep = steps.find((step) => step.name === "captcha");
const rootStep = steps.find((step) => step.name === "root");
const authSteps = steps.filter((step) => step.name.startsWith("auth:"));
const loginJsonSuccess = loginStep ? detectJsonSuccess(loginStep) : null;
const captchaJsonSuccess = captchaStep ? detectJsonSuccess(captchaStep) : null;
const authSuccess = authSteps.every((step) => step.ok && detectJsonSuccess(step) !== false);

console.log(
  JSON.stringify(
    {
      ok:
        Boolean(rootStep?.ok) &&
        (captchaStep ? captchaStep.ok && captchaJsonSuccess !== false : true) &&
        (loginStep ? loginStep.ok && loginJsonSuccess !== false : true) &&
        authSuccess,
      url: baseUrl,
      loginMethod: args.loginMethod || (loginStep ? "json-token" : null),
      credentials: args.username ? { username: args.username, password: redact(args.password) } : null,
      steps: steps.map(({ rawJson, ...step }) => step),
    },
    null,
    2,
  ),
);
