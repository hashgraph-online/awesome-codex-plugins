#!/usr/bin/env node
import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import http from "node:http";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";

const SCRIPT_DIR = dirname(fileURLToPath(import.meta.url));

function listen(handler) {
  const server = http.createServer(handler);
  return new Promise((resolve) => {
    server.listen(0, "127.0.0.1", () => resolve(server));
  });
}

function close(server) {
  return new Promise((resolve, reject) => {
    server.close((error) => (error ? reject(error) : resolve()));
  });
}

function runSmoke(args) {
  return new Promise((resolve) => {
    const child = spawn(process.execPath, [join(SCRIPT_DIR, "sealos-live-smoke.mjs"), ...args], {
      stdio: ["ignore", "pipe", "pipe"],
    });
    let stdout = "";
    let stderr = "";
    child.stdout.on("data", (chunk) => {
      stdout += chunk;
    });
    child.stderr.on("data", (chunk) => {
      stderr += chunk;
    });
    child.on("close", (code) => resolve({ code, stdout, stderr }));
  });
}

test("cookie-json login sends dynamic CSRF header and keeps session cookies", async () => {
  const requests = [];
  const server = await listen((request, response) => {
    requests.push({
      method: request.method,
      url: request.url,
      cookie: request.headers.cookie || "",
      csrf: request.headers["x-csrf-token-device"] || "",
    });

    if (request.url === "/") {
      response.setHeader("set-cookie", ["CSRF-Token-device=csrf-value; Path=/"]);
      response.end("<form id=\"login\"></form>");
      return;
    }

    if (request.url === "/rest/noauth/auth/password" && request.method === "POST") {
      assert.match(request.headers.cookie || "", /CSRF-Token-device=csrf-value/);
      assert.equal(request.headers["x-csrf-token-device"], "csrf-value");
      response.statusCode = 204;
      response.setHeader("set-cookie", ["sessionid=session-value; Path=/"]);
      response.end();
      return;
    }

    if (request.url === "/rest/system/status") {
      assert.match(request.headers.cookie || "", /sessionid=session-value/);
      assert.equal(request.headers["x-csrf-token-device"], "csrf-value");
      response.setHeader("content-type", "application/json");
      response.end(JSON.stringify({ ok: true }));
      return;
    }

    response.statusCode = 404;
    response.end("missing");
  });

  try {
    const address = server.address();
    const result = await runSmoke([
      "--url",
      `http://127.0.0.1:${address.port}`,
      "--login-method",
      "cookie-json",
      "--csrf-cookie-prefix",
      "CSRF-Token-",
      "--csrf-header-prefix",
      "X-CSRF-Token-",
      "--login-path",
      "/rest/noauth/auth/password",
      "--username",
      "admin",
      "--password",
      "secret",
      "--auth-path",
      "/rest/system/status",
    ]);

    assert.equal(result.code, 0, result.stderr || result.stdout);
    const report = JSON.parse(result.stdout);
    assert.equal(report.ok, true);
    assert.equal(report.loginMethod, "cookie-json");
    assert.deepEqual(
      requests.map((entry) => `${entry.method} ${entry.url}`),
      ["GET /", "POST /rest/noauth/auth/password", "GET /rest/system/status"],
    );
  } finally {
    await close(server);
  }
});

test("json-token login accepts code 0, repeated token paths, and authenticated missing probes", async () => {
  const requests = [];
  const token = "sub2api-access-token-secret";
  const server = await listen((request, response) => {
    requests.push({ method: request.method, url: request.url, authorization: request.headers.authorization || "" });

    if (request.url === "/") {
      response.end("<html><body>SPA</body></html>");
      return;
    }
    if (request.url === "/login" && request.method === "POST") {
      response.setHeader("content-type", "application/json");
      response.end(JSON.stringify({ code: 0, data: { access_token: token } }));
      return;
    }
    if (request.url === "/api/me") {
      assert.equal(request.headers.authorization, `Bearer ${token}`);
      response.setHeader("content-type", "application/json");
      response.end(JSON.stringify({ code: 0, data: { user: "smoke" } }));
      return;
    }
    if (request.url === "/api/missing") {
      assert.equal(request.headers.authorization, `Bearer ${token}`);
      response.statusCode = 404;
      response.setHeader("content-type", "application/json");
      response.end(JSON.stringify({ code: 404, message: "missing" }));
      return;
    }
    if (request.url === "/page/missing") {
      response.statusCode = 200;
      response.setHeader("content-type", "text/html");
      response.end("<html><body>SPA fallback</body></html>");
      return;
    }
    response.statusCode = 404;
    response.end("missing");
  });

  try {
    const address = server.address();
    const result = await runSmoke([
      "--url",
      `http://127.0.0.1:${address.port}`,
      "--login-path",
      "/login",
      "--login-method",
      "json-token",
      "--username",
      "admin",
      "--password",
      "secret",
      "--token-path",
      "data.missing",
      "--token-path",
      "data.access_token",
      "--auth-path",
      "/api/me",
      "--missing-api-path",
      "/api/missing",
      "--missing-page-path",
      "/page/missing",
    ]);

    assert.equal(result.code, 0, result.stderr || result.stdout);
    const report = JSON.parse(result.stdout);
    assert.equal(report.ok, true);
    assert.equal(report.error, null);
    assert.equal(report.tokenPath, "data.access_token");
    assert.equal(report.steps.find((step) => step.name === "missing-api:/api/missing").status, 404);
    assert.equal(report.steps.find((step) => step.name === "missing-api:/api/missing").probeType, "api");
    assert.equal(report.steps.find((step) => step.name === "missing-page:/page/missing").status, 200);
    assert.equal(report.steps.find((step) => step.name === "missing-page:/page/missing").probeType, "page");
    assert.equal(result.stdout.includes(token), false);
    assert.ok(requests.some((request) => request.url === "/api/me" && request.authorization === `Bearer ${token}`));
  } finally {
    await close(server);
  }
});

test("reports token_not_found when an authenticated JSON login has no configured token", async () => {
  const server = await listen((request, response) => {
    if (request.url === "/") {
      response.end("ok");
      return;
    }
    if (request.url === "/login" && request.method === "POST") {
      response.setHeader("content-type", "application/json");
      response.end(JSON.stringify({ code: 0, data: { message: "logged in" } }));
      return;
    }
    response.statusCode = 401;
    response.end("unauthorized");
  });

  try {
    const address = server.address();
    const result = await runSmoke([
      "--url",
      `http://127.0.0.1:${address.port}`,
      "--login-path",
      "/login",
      "--username",
      "admin",
      "--password",
      "secret",
      "--auth-path",
      "/api/me",
    ]);
    assert.equal(result.code, 1);
    const report = JSON.parse(result.stdout);
    assert.equal(report.ok, false);
    assert.equal(report.error, "token_not_found");
    assert.equal(result.stdout.includes("logged in"), true);
  } finally {
    await close(server);
  }
});

test("reports token_not_found for a JSON login even without follow-up probes", async () => {
  const server = await listen((request, response) => {
    if (request.url === "/") {
      response.end("ok");
      return;
    }
    if (request.url === "/login" && request.method === "POST") {
      response.setHeader("content-type", "application/json");
      response.end(JSON.stringify({ code: 0, data: { message: "logged in" } }));
      return;
    }
    response.statusCode = 404;
    response.end("missing");
  });

  try {
    const address = server.address();
    const result = await runSmoke([
      "--url",
      `http://127.0.0.1:${address.port}`,
      "--login-path",
      "/login",
      "--username",
      "admin",
      "--password",
      "secret",
    ]);
    assert.equal(result.code, 1);
    const report = JSON.parse(result.stdout);
    assert.equal(report.error, "token_not_found");
    assert.ok(report.findings.some((finding) => finding.code === "token_not_found"));
  } finally {
    await close(server);
  }
});

test("rejects a missing-page probe that returns a non-HTML success body", async () => {
  const server = await listen((request, response) => {
    if (request.url === "/") {
      response.end("ok");
      return;
    }
    if (request.url === "/page/missing") {
      response.setHeader("content-type", "application/json");
      response.end(JSON.stringify({ ok: true }));
      return;
    }
    response.statusCode = 404;
    response.end("missing");
  });

  try {
    const address = server.address();
    const result = await runSmoke([
      "--url",
      `http://127.0.0.1:${address.port}`,
      "--missing-page-path",
      "/page/missing",
    ]);
    assert.equal(result.code, 1);
    const report = JSON.parse(result.stdout);
    assert.equal(report.ok, false);
    assert.equal(report.findings[0].probe, "missing-page:/page/missing");
  } finally {
    await close(server);
  }
});
