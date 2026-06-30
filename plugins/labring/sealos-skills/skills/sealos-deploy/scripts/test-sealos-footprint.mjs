#!/usr/bin/env node
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";

const SCRIPT_DIR = dirname(fileURLToPath(import.meta.url));

function runFootprint(fixtures) {
  const dir = mkdtempSync(join(tmpdir(), "sealos-footprint-test-"));
  const kubectl = join(dir, "kubectl");
  const script = `#!/usr/bin/env node
const fs = require("fs");
const path = require("path");
const args = process.argv;
const type = args[args.indexOf("get") + 1];
const fixtures = ${JSON.stringify(fixtures)};
if (!(type in fixtures)) {
  process.stdout.write(JSON.stringify({ items: [] }));
  process.exit(0);
}
process.stdout.write(JSON.stringify({ items: fixtures[type] }));
`;
  writeFileSync(kubectl, script, { mode: 0o755 });
  const result = spawnSync(process.execPath, [join(SCRIPT_DIR, "sealos-footprint.mjs"), "--namespace", "ns", "--app", "demo"], {
    env: { ...process.env, PATH: `${dir}:${process.env.PATH}` },
    encoding: "utf8",
  });
  rmSync(dir, { recursive: true, force: true });
  return result;
}

test("footprint reports workload readiness and pod container readiness", () => {
  const deployment = {
    metadata: { name: "demo", labels: { app: "demo" }, creationTimestamp: "2026-06-29T00:00:00Z" },
    spec: { replicas: 1 },
    status: { readyReplicas: 1, availableReplicas: 1, updatedReplicas: 1, replicas: 1 },
  };
  const pod = {
    metadata: { name: "demo-0", labels: { app: "demo" }, creationTimestamp: "2026-06-29T00:00:01Z" },
    status: {
      phase: "Running",
      conditions: [{ type: "Ready", status: "True" }],
      containerStatuses: [{ name: "demo", ready: true }],
    },
  };

  const result = runFootprint({ deployment: [deployment], pod: [pod] });
  assert.equal(result.status, 0, result.stderr || result.stdout);
  const report = JSON.parse(result.stdout);
  assert.equal(report.ok, true);
  const workload = report.resources.find((item) => item.type === "deployment");
  const podSummary = report.resources.find((item) => item.type === "pod");
  assert.equal(workload.ready, 1);
  assert.equal(workload.desired, 1);
  assert.equal(workload.readiness, "1/1");
  assert.equal(podSummary.ready, "True");
  assert.equal(podSummary.readiness, "True");
  assert.equal(podSummary.containersReady, "1/1");
});
