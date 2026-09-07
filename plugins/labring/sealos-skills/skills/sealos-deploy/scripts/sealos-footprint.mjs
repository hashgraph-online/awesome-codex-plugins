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
  "objectstoragebuckets.objectstorage.sealos.io",
];

const RESOURCE_ALIASES = {
  "objectstoragebuckets.objectstorage.sealos.io": ["objectstoragebucket"],
};

const RESOURCE_KINDS = {
  "instances.app.sealos.io": "Instance",
  "apps.app.sealos.io": "App",
  deployment: "Deployment",
  statefulset: "StatefulSet",
  daemonset: "DaemonSet",
  cronjob: "CronJob",
  job: "Job",
  svc: "Service",
  ingress: "Ingress",
  pvc: "PersistentVolumeClaim",
  pod: "Pod",
  "clusters.apps.kubeblocks.io": "Cluster",
  "objectstoragebuckets.objectstorage.sealos.io": "ObjectStorageBucket",
};

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

function condition(item, type) {
  return item.status?.conditions?.find((entry) => entry.type === type) || null;
}

function conditionSummaries(item) {
  return (item.status?.conditions || []).map((entry) => ({
    type: entry.type || null,
    status: entry.status || null,
    reason: entry.reason || null,
    message: entry.message || null,
    lastTransitionTime: entry.lastTransitionTime || null,
  }));
}

function numeric(value) {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function podContainerReadiness(item) {
  const statuses = item.status?.containerStatuses || [];
  if (statuses.length === 0) {
    return null;
  }
  const ready = statuses.filter((status) => status.ready).length;
  return `${ready}/${statuses.length}`;
}

function podRestartCount(item) {
  const statuses = [
    ...(item.status?.initContainerStatuses || []),
    ...(item.status?.containerStatuses || []),
  ];
  return statuses.reduce((total, status) => total + (status.restartCount || 0), 0);
}

function workloadReadyCount(type, item) {
  if (type === "daemonset") {
    return numeric(item.status?.numberReady);
  }
  return numeric(item.status?.readyReplicas ?? item.status?.availableReplicas);
}

function workloadDesiredCount(type, item) {
  if (type === "daemonset") {
    return numeric(item.status?.desiredNumberScheduled);
  }
  if (type === "job") {
    return numeric(item.spec?.completions ?? 1);
  }
  return numeric(item.spec?.replicas ?? item.status?.replicas ?? 1);
}

function workloadStatus(type, item) {
  const ready = workloadReadyCount(type, item);
  const desired = workloadDesiredCount(type, item);
  const failed = numeric(item.status?.failed) ?? 0;
  const complete = desired !== null && ready !== null && ready >= desired && failed === 0;
  return {
    phase: item.status?.phase || null,
    desiredReplicas: desired,
    replicas: numeric(item.status?.replicas),
    readyReplicas: ready,
    availableReplicas: numeric(item.status?.availableReplicas),
    updatedReplicas: numeric(item.status?.updatedReplicas ?? item.status?.updatedNumberScheduled),
    failed,
    ready: complete,
    conditions: conditionSummaries(item),
  };
}

function jobStatus(item) {
  const succeeded = numeric(item.status?.succeeded) ?? 0;
  const failed = numeric(item.status?.failed) ?? 0;
  const completions = numeric(item.spec?.completions ?? item.status?.completions ?? 1);
  const completeCondition = condition(item, "Complete");
  const failedCondition = condition(item, "Failed");
  const complete = completeCondition?.status === "True" || (completions !== null && succeeded >= completions);
  const failedState = failedCondition?.status === "True" || failed > 0;
  return {
    phase: item.status?.phase || (complete ? "Complete" : failedState ? "Failed" : null),
    succeeded,
    failed,
    completions,
    complete,
    failedState,
    condition: complete ? "Complete" : failedState ? "Failed" : null,
    conditions: conditionSummaries(item),
  };
}

function controllerStatus(item) {
  const readyCondition = condition(item, "Ready") || condition(item, "Available") || condition(item, "ReadyForDeployment");
  const phase = item.status?.phase || item.status?.state || null;
  const ready = readyCondition?.status === "True" || ["Running", "Ready", "Healthy", "Succeeded"].includes(phase);
  const failed = readyCondition?.status === "False" && ["Failed", "Degraded", "Error"].includes(readyCondition?.reason);
  return {
    phase,
    state: item.status?.state || null,
    ready,
    failed,
    conditions: conditionSummaries(item),
  };
}

function summarizeItem(type, item) {
  const kind = item.kind || RESOURCE_KINDS[type] || type;
  let ready = null;
  let desired = null;
  let readiness = "unknown";
  let runtimeReady = null;
  let status;
  let completion = null;

  if (["deployment", "statefulset", "daemonset"].includes(type)) {
    status = workloadStatus(type, item);
    ready = status.readyReplicas;
    desired = status.desiredReplicas;
    readiness = ready !== null && desired !== null ? `${ready}/${desired}` : "unknown";
    runtimeReady = status.ready;
  } else if (type === "job") {
    status = jobStatus(item);
    ready = status.succeeded;
    desired = status.completions;
    completion = status.condition;
    readiness = status.condition || (ready !== null && desired !== null ? `${ready}/${desired}` : "unknown");
    runtimeReady = status.complete ? true : status.failedState ? false : null;
  } else if (type === "pod") {
    const readyCondition = condition(item, "Ready");
    const completed = item.status?.phase === "Succeeded" && (item.status?.containerStatuses || []).every((entry) => entry.state?.terminated?.exitCode === 0);
    status = {
      phase: item.status?.phase || null,
      ready: readyCondition?.status === "True" || completed,
      completed,
      conditions: conditionSummaries(item),
    };
    ready = readyCondition?.status || (completed ? "True" : null);
    desired = 1;
    readiness = ready || "unknown";
    runtimeReady = status.ready;
  } else if (type === "pvc") {
    const phase = item.status?.phase || null;
    status = { phase, bound: phase === "Bound", conditions: conditionSummaries(item) };
    readiness = phase || "unknown";
    runtimeReady = phase === "Bound" ? true : ["Lost", "Failed"].includes(phase) ? false : null;
  } else if (type === "clusters.apps.kubeblocks.io" || type === "instances.app.sealos.io" || type === "apps.app.sealos.io" || type === "objectstoragebuckets.objectstorage.sealos.io") {
    status = controllerStatus(item);
    readiness = status.ready === true ? "Ready" : status.failed ? "Failed" : status.phase || "unknown";
    runtimeReady = status.failed ? false : status.ready === true ? true : null;
  } else {
    status = controllerStatus(item);
  }

  return {
    type,
    kind,
    resourceType: kind,
    name: item.metadata?.name,
    phase: item.status?.phase || status.phase || null,
    ready,
    desired,
    readiness,
    runtimeReady,
    completion,
    status,
    objectStorageBucket: kind === "ObjectStorageBucket",
    containersReady: type === "pod" ? podContainerReadiness(item) : null,
    restartCount: type === "pod" ? podRestartCount(item) : null,
    updated: item.status?.updatedReplicas ?? item.status?.updatedNumberScheduled,
    available: item.status?.availableReplicas ?? item.status?.numberAvailable,
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
  let result = runKubectl(namespace, type);
  if (result.ok && result.items.length === 0) {
    for (const alias of RESOURCE_ALIASES[type] || []) {
      const aliasResult = runKubectl(namespace, alias);
      if (!aliasResult.ok || aliasResult.items.length > 0) {
        result = aliasResult;
        break;
      }
    }
  }
  if (!result.ok) {
    errors.push({ type, error: result.error });
    continue;
  }
  for (const item of result.items.filter((entry) => itemMatches(entry, app))) {
    const summary = summarizeItem(type, item);
    const identity = `${summary.kind}/${summary.name}/${item.metadata?.uid || ""}`;
    if (!resources.some((entry) => `${entry.kind}/${entry.name}/${entry.uid || ""}` === identity)) {
      resources.push({ ...summary, uid: item.metadata?.uid || null });
    }
  }
}

const collectionOk = errors.length === 0;
const runtimeSignals = resources.map((resource) => resource.runtimeReady).filter((value) => value !== null);
const runtimeReady = collectionOk && runtimeSignals.length > 0 ? runtimeSignals.every(Boolean) : null;
const counts = resources.reduce((summary, resource) => {
  summary[resource.type] = (summary[resource.type] || 0) + 1;
  return summary;
}, {});

const report = {
  ok: collectionOk && runtimeReady !== false,
  collectionOk,
  runtimeReady,
  namespace,
  app,
  resources,
  errors,
  counts,
  cleanupComplete: collectionOk && resources.length === 0,
};

console.log(JSON.stringify(report, null, 2));
process.exitCode = report.ok ? 0 : 1;
