#!/usr/bin/env node
import assert from "node:assert/strict";
import test from "node:test";

import { main } from "./sealos-launchpad-network.mjs";

function network(overrides = {}) {
  return {
    serviceName: "demo",
    networkName: "demo",
    portName: "http",
    port: 3000,
    protocol: "TCP",
    appProtocol: "HTTP",
    openPublicDomain: true,
    publicDomain: "demo-public",
    customDomain: "",
    domain: "usw-1.sealos.app",
    ...overrides,
  };
}

async function runWithResponse(body, options = {}) {
  let request;
  const dependencies = {
    homeDir: "/tmp/sealos-launchpad-test",
    env: {},
    readFileText(path) {
      if (path.endsWith("auth.json")) {
        return JSON.stringify({ region: "https://usw-1.sealos.io" });
      }
      if (path.endsWith("kubeconfig")) {
        return "test-kubeconfig-secret";
      }
      throw new Error(`unexpected path: ${path}`);
    },
    async fetchImpl(url, fetchOptions) {
      request = { url: String(url), options: fetchOptions };
      return {
        status: options.httpStatus ?? 200,
        async json() {
          return body;
        },
      };
    },
  };
  const args = options.args || [
    "--app",
    "demo",
    "--app-url",
    "https://demo-public.usw-1.sealos.app/admin",
    "--expected-port",
    "3000",
  ];
  const result = await main(args, dependencies);
  return { ...result, request };
}

test("accepts a matching Launchpad public domain and encodes kubeconfig authorization", async () => {
  const result = await runWithResponse({ code: 200, data: { networks: [network()] } });
  assert.equal(result.exitCode, 0);
  assert.equal(result.report.ok, true);
  assert.equal(result.report.networks[0].port, 3000);
  assert.equal(result.request.options.headers.Authorization, encodeURIComponent("test-kubeconfig-secret"));
  assert.match(result.request.url, /applaunchpad\.usw-1\.sealos\.io\/api\/getAppByAppName\?appName=demo/);
});

test("accepts a matching custom domain", async () => {
  const result = await runWithResponse(
    {
      code: 200,
      data: {
        networks: [network({ publicDomain: "", domain: "", customDomain: "demo.example.com" })],
      },
    },
    {
      args: ["--app", "demo", "--app-url", "https://demo.example.com", "--expected-port", "3000"],
    },
  );
  assert.equal(result.exitCode, 0);
  assert.equal(result.report.ok, true);
});

test("reports a missing public network", async () => {
  const result = await runWithResponse({ code: 200, data: { networks: [] } });
  assert.equal(result.exitCode, 1);
  assert.equal(result.report.ok, false);
  assert.ok(result.report.findings.some((finding) => finding.code === "public_network_missing"));
});

test("reports a Launchpad API error", async () => {
  const result = await runWithResponse({ code: 500, message: "Server error" });
  assert.equal(result.exitCode, 1);
  assert.ok(result.report.findings.some((finding) => finding.code === "launchpad_api_error"));
});

test("reports an expected port mismatch", async () => {
  const result = await runWithResponse({
    code: 200,
    data: { networks: [network({ port: 8080 })] },
  });
  assert.equal(result.exitCode, 1);
  assert.ok(result.report.findings.some((finding) => finding.code === "expected_port_missing"));
});

test("reports an App URL host mismatch", async () => {
  const result = await runWithResponse(
    { code: 200, data: { networks: [network()] } },
    {
      args: ["--app", "demo", "--app-url", "https://stale.usw-1.sealos.app", "--expected-port", "3000"],
    },
  );
  assert.equal(result.exitCode, 1);
  assert.ok(result.report.findings.some((finding) => finding.code === "app_url_host_mismatch"));
});

test("keeps sensitive raw response fields out of the report", async () => {
  const result = await runWithResponse({
    code: 200,
    data: {
      envs: [{ key: "PASSWORD", value: "raw-password-secret" }],
      secret: { password: "raw-registry-secret" },
      networks: [network()],
    },
  });
  const serialized = JSON.stringify(result.report);
  assert.doesNotMatch(serialized, /raw-password-secret|raw-registry-secret|test-kubeconfig-secret/);
  assert.deepEqual(Object.keys(result.report), ["ok", "app", "apiCode", "networks", "findings"]);
});

test("uses exit code 2 for invalid input", async () => {
  const result = await main([], {});
  assert.equal(result.exitCode, 2);
  assert.equal(result.report.findings[0].code, "input_error");
});

test("requires an App URL for host matching", async () => {
  const result = await main(["--app", "demo"], {});
  assert.equal(result.exitCode, 2);
  assert.equal(result.report.findings[0].code, "input_error");
  assert.match(result.report.findings[0].message, /--app-url is required/);
});
