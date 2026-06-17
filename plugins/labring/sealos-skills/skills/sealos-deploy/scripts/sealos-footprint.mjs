#!/usr/bin/env node
import { spawnSync } from "node:child_process";
import process from "node:process";

const RESOURCE_TYPES = [
  "instances.app.sealos.io",
  "apps.app.sealos.io",
  "deployment",
  "statefulset",
  "daemonset",
  "cronjob",
  "job",
  "svc",
  "ingress",
  "pvc",
  "pod",
  "clusters.apps.kubeblocks.io",
];

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
    args[key] = next;
    index += 1;
  }
  return args;
}

function fail(message, extra = {}) {
  console.log(JSON.stringify({ ok: false, error: message, ...extra }, null, 2));
  process.exit(1);
}

function runKubectl(namespace, type) {
  const result = spawnSync(
    "kubectl",
    [
      "--insecure-skip-tls-verify",
      "-n",
      namespace,
      "get",
      type,
      "-o",
      "json",
      "--ignore-not-found",
    ],
    {
      env: { ...process.env, KUBECONFIG: process.env.KUBECONFIG || `${process.env.HOME}/.sealos/kubeconfig` },
      encoding: "utf8",
    },
  );

  if (result.error) {
    return { type, ok: false, error: result.error.message, items: [] };
  }
  if (result.status !== 0) {
    return { type, ok: false, error: result.stderr.trim() || result.stdout.trim(), items: [] };
  }
  if (!result.stdout.trim()) {
    return { type, ok: true, items: [] };
  }

  try {
    const parsed = JSON.parse(result.stdout);
    return { type, ok: true, items: parsed.items || [] };
  } catch (error) {
    return { type, ok: false, error: `invalid kubectl JSON: ${error.message}`, items: [] };
  }
}

function itemMatches(item, app) {
  const name = item.metadata?.name || "";
  const labels = item.metadata?.labels || {};
  const owners = item.metadata?.ownerReferences || [];
  return (
    name.includes(app) ||
    labels.app === app ||
    labels["cloud.sealos.io/app-deploy-manager"] === app ||
    labels["app.kubernetes.io/instance"] === app ||
    owners.some((owner) => owner.name?.includes(app))
  );
}

function summarizeItem(type, item) {
  return {
    type,
    name: item.metadata?.name,
    phase: item.status?.phase,
    ready: item.status?.readyReplicas ?? item.status?.numberReady ?? item.status?.availableReplicas,
    desired: item.spec?.replicas ?? item.status?.replicas,
    labels: item.metadata?.labels || {},
    ageTimestamp: item.metadata?.creationTimestamp,
  };
}

const args = parseArgs(process.argv);
const namespace = args.namespace || args.n;
const app = args.app || args.name;

if (!namespace || !app) {
  fail("usage: node sealos-footprint.mjs --namespace <namespace> --app <app>");
}

const resources = [];
const errors = [];

for (const type of RESOURCE_TYPES) {
  const result = runKubectl(namespace, type);
  if (!result.ok) {
    errors.push({ type, error: result.error });
    continue;
  }
  for (const item of result.items.filter((entry) => itemMatches(entry, app))) {
    resources.push(summarizeItem(type, item));
  }
}

console.log(
  JSON.stringify(
    {
      ok: errors.length === 0,
      namespace,
      app,
      resources,
      errors,
      cleanupComplete: errors.length === 0 && resources.length === 0,
    },
    null,
    2,
  ),
);
