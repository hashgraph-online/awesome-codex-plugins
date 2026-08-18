#!/usr/bin/env node
const process = require("node:process");

let fixture;
try {
  fixture = JSON.parse(process.env.SEALOS_KUBECTL_FIXTURE_JSON || "{}");
} catch (error) {
  process.stderr.write(`Invalid SEALOS_KUBECTL_FIXTURE_JSON: ${error.message}\n`);
  process.exit(2);
}

const args = process.argv.slice(2);
const getIndex = args.indexOf("get");
const logsIndex = args.indexOf("logs");

if (getIndex >= 0) {
  const resource = args[getIndex + 1];
  const failure = fixture.failures?.[resource];
  if (failure) {
    process.stderr.write(`${failure}\n`);
    process.exit(1);
  }
  process.stdout.write(JSON.stringify({ items: fixture[resource] || [] }));
  process.exit(0);
}

if (logsIndex >= 0) {
  const pod = String(args[logsIndex + 1] || "").replace(/^pod\//, "");
  const containerIndex = args.indexOf("-c");
  const container = containerIndex >= 0 ? args[containerIndex + 1] : "";
  const stream = args.includes("--previous") ? "previous" : "current";
  const key = `${pod}/${container}/${stream}`;
  const failure = fixture.logFailures?.[key];
  if (failure) {
    process.stderr.write(`${failure}\n`);
    process.exit(1);
  }
  process.stdout.write(fixture.logs?.[key] || "");
  process.exit(0);
}

process.stderr.write(`Unsupported kubectl fixture command: ${args.join(" ")}\n`);
process.exit(1);
