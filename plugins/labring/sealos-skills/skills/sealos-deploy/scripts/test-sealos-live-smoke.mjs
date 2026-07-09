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
