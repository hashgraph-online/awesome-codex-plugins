#!/usr/bin/env node
import { spawnSync } from "node:child_process";
import { existsSync, readFileSync } from "node:fs";
import { homedir } from "node:os";

const SIGNALS = [
  { id: "traceback", pattern: /Traceback \(most recent call last\):/ },
  { id: "http_exception", pattern: /\bHTTPException\b/ },
  { id: "not_found", pattern: /werkzeug\.exceptions\.NotFound|\bNotFound\b|404 Not Found/i },
  { id: "warning", pattern: /\bWARNING\b|:WARNING:/ },
  { id: "deprecation", pattern: /\bDeprecationWarning\b|\bdeprecated\b/i },
  { id: "error", pattern: /\bERROR\b|:ERROR:/ },
  { id: "critical", pattern: /\bCRITICAL\b|:CRITICAL:/ },
  { id: "oom_killed", pattern: /\bOOMKilled\b|exit code 137|\bKilled\b/i },
  { id: "backoff", pattern: /\bBackOff\b|\bCrashLoopBackOff\b|\bImagePullBackOff\b/ },
  { id: "migration_failure", pattern: /migration.*failed|failed.*migration/i },
  { id: "bootstrap_failure", pattern: /bootstrap.*failed|failed.*bootstrap/i },
  { id: "auth_failure", pattern: /authentication failed|permission denied|access denied|unauthorized/i },
];

const USAGE = [
  "Usage:",
  "  node sealos-log-scan.mjs --namespace <ns> --app <app> [--since 10m] [--tail 300]",
  "    [--baseline <report.json|json>] [--min-window-seconds 60]",
  "",
  "Run once without --baseline to capture a sample, then compare after the stability window.",
].join("\n");

function argumentValue(argv, index, option) {
  const value = argv[index + 1];
  if (!value || value.startsWith("--")) {
    throw new Error(`${option} requires a value`);
  }
  return value;
}

function parseArgs(argv) {
  const args = {
    namespace: "",
    app: "",
    since: "10m",
    tail: "300",
    baseline: "",
    minWindowSeconds: "60",
    dryRun: false,
    help: false,
  };

  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--help" || arg === "-h") {
      args.help = true;
    } else if (arg === "--dry-run") {
      args.dryRun = true;
    } else if (arg === "--namespace" || arg === "-n") {
      args.namespace = argumentValue(argv, i, arg);
      i += 1;
    } else if (arg === "--app") {
      args.app = argumentValue(argv, i, arg);
      i += 1;
    } else if (arg === "--since") {
      args.since = argumentValue(argv, i, arg);
      i += 1;
    } else if (arg === "--tail") {
      args.tail = argumentValue(argv, i, arg);
      i += 1;
    } else if (arg === "--baseline") {
      args.baseline = argumentValue(argv, i, arg);
      i += 1;
    } else if (arg === "--min-window-seconds") {
      args.minWindowSeconds = argumentValue(argv, i, arg);
      i += 1;
    } else {
      throw new Error(`Unknown argument: ${arg}`);
    }
  }

  return args;
}

function strictInteger(value) {
  if (!/^\d+$/.test(String(value))) {
    return null;
  }
  const parsed = Number(value);
  return Number.isSafeInteger(parsed) ? parsed : null;
}

function baseResult(args) {
  const minWindowSeconds = strictInteger(args.minWindowSeconds);
  return {
    tool: "sealos-log-scan",
    generatedAt: new Date().toISOString(),
    namespace: args.namespace,
    app: args.app,
    since: args.since,
    tail: strictInteger(args.tail),
    minWindowSeconds,
    baseline: {
      provided: Boolean(args.baseline),
      generatedAt: null,
      elapsedSeconds: null,
      complete: false,
    },
    ok: false,
    dryRun: args.dryRun,
    pods: [],
    events: [],
    eventSummary: {
      observed: 0,
      "historical-transient": 0,
      "active-failure": 0,
    },
    findings: [],
    observations: [],
    errors: [],
  };
}

function printJson(result, exitCode = 0) {
  process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
  process.exitCode = exitCode;
}

function kubectl(args) {
  const env = { ...process.env };
  if (!env.KUBECONFIG) {
    env.KUBECONFIG = `${homedir()}/.sealos/kubeconfig`;
  }

  const fullArgs = ["--insecure-skip-tls-verify", ...args];
  const child = spawnSync("kubectl", fullArgs, {
    env,
    encoding: "utf8",
    maxBuffer: 20 * 1024 * 1024,
  });

  return {
    ok: child.status === 0 && !child.error,
    status: child.status,
    stdout: child.stdout || "",
    stderr: child.error?.message || child.stderr || "",
    command: `kubectl ${fullArgs.join(" ")}`,
  };
}

function normalize(value) {
  return String(value || "").toLowerCase();
}

function toTimestamp(value) {
  const timestamp = value ? Date.parse(value) : Number.NaN;
  return Number.isFinite(timestamp) ? timestamp : null;
}

function podMatchesApp(pod, appName) {
  const app = normalize(appName);
  const name = normalize(pod.metadata?.name);
  const labels = pod.metadata?.labels || {};
  const ownerRefs = pod.metadata?.ownerReferences || [];

  if (name.includes(app)) {
    return true;
  }

  const labelValues = [
    labels.app,
    labels["app.kubernetes.io/name"],
    labels["app.kubernetes.io/instance"],
    labels["cloud.sealos.io/app-deploy-manager"],
    labels["app.kubernetes.io/component"],
  ];

  if (labelValues.some((value) => normalize(value) === app || normalize(value).includes(app))) {
    return true;
  }

  return ownerRefs.some((owner) => normalize(owner.name).includes(app));
}

function eventReference(event) {
  return event.regarding || event.involvedObject || {};
}

function eventMatchesApp(event, appName, pods) {
  const reference = eventReference(event);
  const referenceName = normalize(reference.name);
  const referenceUid = reference.uid || "";
  const app = normalize(appName);
  const labels = event.metadata?.labels || {};
  const labelValues = [
    labels.app,
    labels["app.kubernetes.io/name"],
    labels["app.kubernetes.io/instance"],
    labels["cloud.sealos.io/app-deploy-manager"],
  ];

  return (
    referenceName.includes(app) ||
    pods.some((pod) => pod.metadata?.uid === referenceUid || normalize(pod.metadata?.name) === referenceName) ||
    labelValues.some((value) => normalize(value) === app || normalize(value).includes(app))
  );
}

function eventCount(event) {
  const value = event.series?.count ?? event.count ?? event.deprecatedCount ?? 1;
  const count = Number.parseInt(value, 10);
  return Number.isInteger(count) && count > 0 ? count : 1;
}

function eventFirstSeen(event) {
  return (
    event.firstTimestamp ||
    event.deprecatedFirstTimestamp ||
    event.eventTime ||
    event.metadata?.creationTimestamp ||
    null
  );
}

function eventLastSeen(event) {
  return (
    event.series?.lastObservedTime ||
    event.lastTimestamp ||
    event.deprecatedLastTimestamp ||
    event.eventTime ||
    event.metadata?.creationTimestamp ||
    null
  );
}

function eventFingerprint(event) {
  const reference = eventReference(event);
  const identity = reference.uid || `${reference.kind || "Object"}/${reference.name || "unknown"}`;
  return [identity, event.reason || "Unknown", event.message || event.note || ""].join("|");
}

function missingSecretName(message) {
  const quoted = String(message || "").match(/secret\s+["']([^"']+)["']\s+not found/i);
  if (quoted) {
    return quoted[1];
  }
  const unquoted = String(message || "").match(/secret\s+([a-z0-9](?:[-a-z0-9.]*[a-z0-9])?)\s+not found/i);
  return unquoted?.[1] || null;
}

function normalizeWarningEvent(event) {
  const reference = eventReference(event);
  const message = event.message || event.note || "";
  return {
    fingerprint: eventFingerprint(event),
    uid: event.metadata?.uid || null,
    type: event.type || event.deprecatedType || "Warning",
    reason: event.reason || "Unknown",
    message,
    count: eventCount(event),
    firstSeen: eventFirstSeen(event),
    lastSeen: eventLastSeen(event),
    involvedObject: {
      kind: reference.kind || null,
      name: reference.name || null,
      uid: reference.uid || null,
    },
    missingSecret: missingSecretName(message),
  };
}

function trimLine(line) {
  const text = String(line || "").trim();
  return text.length > 240 ? `${text.slice(0, 237)}...` : text;
}

function scanText(text) {
  const lines = text.split(/\r?\n/);
  const bySignal = new Map();

  for (let index = 0; index < lines.length; index += 1) {
    const line = lines[index];
    for (const signal of SIGNALS) {
      if (signal.pattern.test(line)) {
        if (!bySignal.has(signal.id)) {
          bySignal.set(signal.id, { id: signal.id, count: 0, examples: [] });
        }
        const hit = bySignal.get(signal.id);
        hit.count += 1;
        if (hit.examples.length < 5) {
          hit.examples.push({ line: index + 1, text: trimLine(line) });
        }
      }
    }
  }

  return Array.from(bySignal.values());
}

function statusSignals(status) {
  if (!status) {
    return [];
  }
  const text = JSON.stringify({
    state: status.state,
    lastState: status.lastState,
    restartCount: status.restartCount,
  });
  return scanText(text);
}

function containerSpecs(pod, field) {
  return pod.spec?.[field] || [];
}

function containerStatuses(pod, field) {
  return pod.status?.[field] || [];
}

function allContainerStatuses(pod) {
  return [
    ...containerStatuses(pod, "initContainerStatuses"),
    ...containerStatuses(pod, "containerStatuses"),
  ];
}

function collectContainers(pod) {
  const containers = [];
  const add = (spec, status, type) => {
    const terminated = status?.state?.terminated || null;
    containers.push({
      name: spec.name,
      type,
      ready: Boolean(status?.ready),
      restartCount: status?.restartCount || 0,
      state: status?.state || null,
      lastState: status?.lastState || null,
      completionTime: terminated?.finishedAt || null,
      exitCode: Number.isInteger(terminated?.exitCode) ? terminated.exitCode : null,
      terminationReason: terminated?.reason || null,
      historicalCompletedInit: false,
    });
  };

  const initStatuses = new Map(containerStatuses(pod, "initContainerStatuses").map((item) => [item.name, item]));
  const mainStatuses = new Map(containerStatuses(pod, "containerStatuses").map((item) => [item.name, item]));

  for (const spec of containerSpecs(pod, "initContainers")) {
    add(spec, initStatuses.get(spec.name), "init");
  }
  for (const spec of containerSpecs(pod, "containers")) {
    add(spec, mainStatuses.get(spec.name), "main");
  }

  return containers;
}

function summarizePodState(pod) {
  const readyCondition = (pod.status?.conditions || []).find((condition) => condition.type === "Ready");
  const statuses = allContainerStatuses(pod);
  const terminated = statuses.filter((status) => status.state?.terminated);
  const failedTermination = terminated.find((status) => status.state.terminated.exitCode !== 0);
  const completed =
    pod.status?.phase === "Succeeded" &&
    terminated.length > 0 &&
    terminated.length === statuses.length &&
    terminated.every((status) => status.state.terminated.exitCode === 0);
  const failed = pod.status?.phase === "Failed" || Boolean(failedTermination);
  return {
    uid: pod.metadata?.uid || null,
    name: pod.metadata?.name || "",
    phase: pod.status?.phase || "",
    ready: readyCondition?.status === "True",
    completed,
    failed,
    lifecycle: completed ? "completed" : failed ? "failed" : pod.status?.phase || "unknown",
    ownerKind: pod.metadata?.ownerReferences?.find((owner) => ["Job", "CronJob"].includes(owner.kind))?.kind || null,
    readyTransitionTime: readyCondition?.lastTransitionTime || null,
    restartCount: statuses.reduce((total, status) => total + (status.restartCount || 0), 0),
  };
}

function baselinePodFor(baseline, podState) {
  if (!baseline) {
    return null;
  }
  return (
    baseline.pods?.find((pod) => podState.uid && pod.uid === podState.uid) ||
    baseline.pods?.find((pod) => pod.name === podState.name) ||
    null
  );
}

function baselineContainerFor(baselinePod, container) {
  return baselinePod?.containers?.find(
    (candidate) => candidate.name === container.name && candidate.type === container.type,
  ) || null;
}

function isHistoricalCompletedInit(container, baselineContainer, baseline, podState) {
  if (
    container.type !== "init" ||
    !baselineContainer ||
    podState.replaced ||
    podState.restartDelta > 0 ||
    container.restartCount !== baselineContainer.restartCount
  ) {
    return false;
  }

  const currentTerminated = container.state?.terminated;
  const baselineTerminated = baselineContainer.state?.terminated;
  const currentFinishedAt = toTimestamp(currentTerminated?.finishedAt);
  const baselineFinishedAt = toTimestamp(baselineTerminated?.finishedAt);
  const baselineGeneratedAt = toTimestamp(baseline?.generatedAt);

  return Boolean(
    currentTerminated?.exitCode === 0 &&
      baselineTerminated?.exitCode === 0 &&
      currentFinishedAt !== null &&
      baselineFinishedAt !== null &&
      baselineGeneratedAt !== null &&
      currentFinishedAt === baselineFinishedAt &&
      currentFinishedAt <= baselineGeneratedAt,
  );
}

function scanLogStream(namespace, podName, containerName, since, tail, previous = false, sinceTime = null) {
  const args = [
    "-n",
    namespace,
    "logs",
    `pod/${podName}`,
    "-c",
    containerName,
    `--tail=${tail}`,
  ];

  if (sinceTime) {
    args.push(`--since-time=${sinceTime}`);
  } else if (since) {
    args.push(`--since=${since}`);
  }
  if (previous) {
    args.push("--previous");
  }

  return kubectl(args);
}

const ALWAYS_BLOCKING_SIGNALS = new Set([
  "traceback",
  "http_exception",
  "critical",
  "oom_killed",
  "backoff",
  "migration_failure",
  "bootstrap_failure",
]);

const OBSERVATION_RULES = {
  warning: { rule: "startup-warning", reason: "warning signal observed in the log stream" },
  not_found: { rule: "expected-probe-path", reason: "not-found output may come from an expected probe path" },
  auth_failure: { rule: "expected-auth-probe", reason: "authentication output may come from an expected probe" },
};

function baselineSignalFor(baselinePod, containerName, containerType, stream, signalId) {
  const baselineContainer = baselinePod?.containers?.find(
    (candidate) => candidate.name === containerName && candidate.type === containerType,
  );
  if (stream === "status") {
    return baselineContainer?.statusSignals?.find((signal) => signal.id === signalId) || null;
  }
  const baselineStream = baselineContainer?.streams?.find((entry) => entry.name === stream);
  return baselineStream?.signals?.find((signal) => signal.id === signalId) || null;
}

function appendFindings(result, podName, containerName, containerType, stream, signals, context = {}) {
  for (const signal of signals) {
    const previous = baselineSignalFor(context.baselinePod, containerName, containerType, stream, signal.id);
    const delta = previous ? Math.max(0, signal.count - (previous.count || 0)) : signal.count;
    const rule = OBSERVATION_RULES[signal.id] || null;
    const stable = Boolean(context.baselineComplete && previous && delta === 0);
    const historical = Boolean(context.historicalCompletedInit && stable);
    const observation = rule && (stable || !context.baselineComplete || !previous);

    if (historical || observation) {
      result.observations.push({
        source: "log",
        pod: podName,
        container: containerName,
        containerType,
        stream,
        signal: signal.id,
        count: signal.count,
        delta: context.baseline ? delta : null,
        rule: historical ? "historical-completed-init" : rule.rule,
        reason: historical ? "completed init output predates the baseline" : rule.reason,
        historicalCompletedInit: historical,
        examples: signal.examples,
      });
      continue;
    }

    if (stable && !ALWAYS_BLOCKING_SIGNALS.has(signal.id)) {
      result.observations.push({
        source: "log",
        pod: podName,
        container: containerName,
        containerType,
        stream,
        signal: signal.id,
        count: signal.count,
        delta,
        rule: "stable-log-signal",
        reason: "signal count is unchanged after the stability window",
        historicalCompletedInit: false,
        examples: signal.examples,
      });
      continue;
    }

    result.findings.push({
      source: "log",
      pod: podName,
      container: containerName,
      containerType,
      stream,
      signal: signal.id,
      count: signal.count,
      baseline: previous ? { count: previous.count } : null,
      delta: context.baseline ? delta : null,
      examples: signal.examples,
    });
  }
}

function scanPodLogs(result, pod, args, baseline) {
  const state = summarizePodState(pod);
  const baselinePod = baselinePodFor(baseline, state);
  const replaced = Boolean(baselinePod?.uid && state.uid && baselinePod.uid !== state.uid);
  const restartDelta = baselinePod && !replaced ? Math.max(0, state.restartCount - (baselinePod.restartCount || 0)) : 0;
  const baselineReadyTime = toTimestamp(baselinePod?.readyTransitionTime);
  const currentReadyTime = toTimestamp(state.readyTransitionTime);
  const readyTransitionChanged = Boolean(
    baselinePod &&
      baselineReadyTime !== null &&
      currentReadyTime !== null &&
      currentReadyTime > baselineReadyTime,
  );
  const podResult = {
    ...state,
    restartDelta,
    replaced,
    readyTransitionChanged,
    labels: pod.metadata?.labels || {},
    containers: [],
  };
  const baselineSinceTime = baseline?.generatedAt || null;
  const findingContext = {
    baseline,
    baselineComplete: result.baseline.complete,
    baselinePod,
  };

  if (!state.ready && !state.completed && !state.failed) {
    result.findings.push({ source: "pod", pod: state.name, signal: "pod_not_ready" });
  }
  if (state.failed) {
    result.findings.push({ source: "pod", pod: state.name, signal: "pod_failed", lifecycle: state.lifecycle });
  }
  if (baseline && restartDelta > 0) {
    result.findings.push({ source: "pod", pod: state.name, signal: "restart_delta", count: restartDelta });
  }
  if (baseline && replaced) {
    result.findings.push({ source: "pod", pod: state.name, signal: "pod_replaced" });
  }
  if (baseline && readyTransitionChanged) {
    result.findings.push({ source: "pod", pod: state.name, signal: "ready_transition_changed" });
  }

  for (const container of collectContainers(pod)) {
    const historicalCompletedInit = isHistoricalCompletedInit(
      container,
      baselineContainerFor(baselinePod, container),
      baseline,
      podResult,
    );
    const containerResult = {
      ...container,
      historicalCompletedInit,
      statusSignals: statusSignals(container),
      streams: [],
    };
    appendFindings(
      result,
      state.name,
      container.name,
      container.type,
      "status",
      containerResult.statusSignals,
      { ...findingContext, historicalCompletedInit },
    );

    const current = scanLogStream(
      args.namespace,
      state.name,
      container.name,
      args.since,
      args.tail,
      false,
      baselineSinceTime,
    );
    const currentSignals = current.ok ? scanText(current.stdout) : [];
    containerResult.streams.push({
      name: "current",
      ok: current.ok,
      lineCount: current.stdout ? current.stdout.split(/\r?\n/).filter(Boolean).length : 0,
      signals: currentSignals,
      error: current.ok ? null : trimLine(current.stderr || "kubectl logs failed"),
    });
    appendFindings(
      result,
      state.name,
      container.name,
      container.type,
      "current",
      currentSignals,
      { ...findingContext, historicalCompletedInit },
    );

    if (!current.ok) {
      result.errors.push({
        pod: state.name,
        container: container.name,
        stream: "current",
        message: trimLine(current.stderr || "kubectl logs failed"),
      });
    }

    if (container.restartCount > 0 && (!baseline || restartDelta > 0)) {
      const previous = scanLogStream(
        args.namespace,
        state.name,
        container.name,
        args.since,
        args.tail,
        true,
        baselineSinceTime,
      );
      const previousSignals = previous.ok ? scanText(previous.stdout) : [];
      containerResult.streams.push({
        name: "previous",
        ok: previous.ok,
        lineCount: previous.stdout ? previous.stdout.split(/\r?\n/).filter(Boolean).length : 0,
        signals: previousSignals,
        error: previous.ok ? null : trimLine(previous.stderr || "kubectl logs --previous failed"),
      });
      appendFindings(
        result,
        state.name,
        container.name,
        container.type,
        "previous",
        previousSignals,
        { ...findingContext, historicalCompletedInit },
      );
    }

    podResult.containers.push(containerResult);
  }

  result.pods.push(podResult);
}

function parseItems(command, resource, result) {
  if (!command.ok) {
    result.errors.push({ source: "kubectl", resource, message: trimLine(command.stderr || `kubectl get ${resource} failed`) });
    return [];
  }
  try {
    return JSON.parse(command.stdout).items || [];
  } catch (error) {
    result.errors.push({ source: "kubectl", resource, message: `Unable to parse ${resource} JSON: ${error.message}` });
    return [];
  }
}

function loadBaseline(value) {
  let source = value;
  if (existsSync(value)) {
    source = readFileSync(value, "utf8");
  }
  let baseline;
  try {
    baseline = JSON.parse(source);
  } catch (error) {
    throw new Error(`Unable to parse --baseline JSON: ${error.message}`);
  }
  if (baseline?.tool !== "sealos-log-scan" || !Array.isArray(baseline.pods) || !Array.isArray(baseline.events)) {
    throw new Error("--baseline must be a sealos-log-scan JSON report");
  }
  return baseline;
}

function baselineEventMap(baseline) {
  return new Map((baseline?.events || []).map((event) => [event.fingerprint, event]));
}

function podForEvent(event, pods) {
  const reference = event.involvedObject || {};
  return (
    pods.find((pod) => reference.uid && pod.uid === reference.uid) ||
    pods.find((pod) => reference.name && pod.name === reference.name) ||
    null
  );
}

function classifyEvents(result, warnings, baseline, secretNames) {
  const previousEvents = baselineEventMap(baseline);
  for (const warning of warnings) {
    const previous = previousEvents.get(warning.fingerprint) || null;
    const pod = podForEvent(warning, result.pods);
    const countDelta = previous ? Math.max(0, warning.count - (previous.count || 0)) : warning.count;
    const previousLastSeen = toTimestamp(previous?.lastSeen);
    const currentLastSeen = toTimestamp(warning.lastSeen);
    const lastSeenAdvanced = previous
      ? currentLastSeen !== null && (previousLastSeen === null || currentLastSeen > previousLastSeen)
      : true;
    const recurred = Boolean(baseline && (!previous || countDelta > 0 || lastSeenAdvanced));
    const secretExists = warning.missingSecret ? secretNames.has(warning.missingSecret) : null;
    const readyTransitionTime = toTimestamp(pod?.readyTransitionTime);
    const occurredBeforeReady = Boolean(
      currentLastSeen !== null && readyTransitionTime !== null && currentLastSeen <= readyTransitionTime,
    );
    const activeFailure = Boolean(
      baseline &&
        (recurred ||
          secretExists === false ||
          (pod?.ready === false && !pod?.completed) ||
          pod?.failed ||
          (pod?.restartDelta || 0) > 0 ||
          pod?.replaced ||
          pod?.readyTransitionChanged),
    );
    let classification = "observed";
    if (activeFailure) {
      classification = "active-failure";
    } else if (baseline && result.baseline.complete) {
      classification = "historical-transient";
    }

    const normalized = {
      ...warning,
      classification,
      baseline: previous ? { count: previous.count, lastSeen: previous.lastSeen } : null,
      delta: {
        count: baseline ? countDelta : null,
        lastSeenAdvanced: baseline ? lastSeenAdvanced : null,
        restartCount: baseline ? pod?.restartDelta ?? null : null,
        readyTransitionChanged: baseline ? pod?.readyTransitionChanged ?? null : null,
      },
      podReady: pod?.ready ?? null,
      readyTransitionTime: pod?.readyTransitionTime || null,
      occurredBeforeReady,
      secret: warning.missingSecret ? { name: warning.missingSecret, exists: secretExists } : null,
    };
    result.events.push(normalized);
    result.eventSummary[classification] += 1;

    if (classification === "active-failure") {
      result.findings.push({
        source: "event",
        signal: "active_warning_event",
        reason: warning.reason,
        involvedObject: warning.involvedObject,
        countDelta,
        lastSeenAdvanced,
        secret: normalized.secret,
      });
    }
  }
}

function validateArgs(args, result) {
  if (!args.namespace || !args.app) {
    throw new Error("--namespace and --app are required");
  }
  if (!Number.isSafeInteger(result.tail) || result.tail <= 0) {
    throw new Error("--tail must be a positive integer");
  }
  if (!Number.isSafeInteger(result.minWindowSeconds) || result.minWindowSeconds < 60) {
    throw new Error("--min-window-seconds must be an integer of at least 60");
  }
}

function main() {
  let args;
  try {
    args = parseArgs(process.argv.slice(2));
  } catch (error) {
    const result = baseResult({
      namespace: "",
      app: "",
      since: "10m",
      tail: "300",
      baseline: "",
      minWindowSeconds: "60",
      dryRun: false,
    });
    result.errors.push({ message: error.message, usage: USAGE });
    printJson(result, 2);
    return;
  }

  const result = baseResult(args);
  if (args.help) {
    result.ok = true;
    result.usage = USAGE;
    printJson(result);
    return;
  }

  let baseline = null;
  try {
    validateArgs(args, result);
    baseline = args.baseline ? loadBaseline(args.baseline) : null;
    if (baseline && (baseline.namespace !== args.namespace || baseline.app !== args.app)) {
      throw new Error("--baseline namespace and app must match the current scan");
    }
    if (baseline) {
      const generatedAt = toTimestamp(baseline.generatedAt);
      if (generatedAt === null) {
        throw new Error("--baseline generatedAt must be a valid timestamp");
      }
      result.baseline.generatedAt = baseline.generatedAt;
      result.baseline.elapsedSeconds = Math.max(0, Math.floor((toTimestamp(result.generatedAt) - generatedAt) / 1000));
      result.baseline.complete = result.baseline.elapsedSeconds >= result.minWindowSeconds;
    }
  } catch (error) {
    result.errors.push({ message: error.message, usage: USAGE });
    printJson(result, 2);
    return;
  }

  if (args.dryRun) {
    result.ok = true;
    printJson(result);
    return;
  }

  if (baseline && !result.baseline.complete) {
    result.findings.push({
      source: "convergence",
      signal: "stability_window_too_short",
      elapsedSeconds: result.baseline.elapsedSeconds,
      requiredSeconds: result.minWindowSeconds,
    });
  }

  const pods = parseItems(
    kubectl(["-n", args.namespace, "get", "pods", "-o", "json"]),
    "pods",
    result,
  );
  const matchedPods = pods.filter((pod) => podMatchesApp(pod, args.app));
  if (matchedPods.length === 0) {
    result.findings.push({
      source: "pod",
      signal: "no_pods",
      count: 1,
      examples: [{ line: 0, text: `No pods matched app '${args.app}' in namespace '${args.namespace}'` }],
    });
  }

  for (const pod of matchedPods) {
    scanPodLogs(result, pod, args, baseline);
  }

  const allEvents = parseItems(
    kubectl(["-n", args.namespace, "get", "events", "-o", "json"]),
    "events",
    result,
  );
  const warnings = allEvents
    .filter((event) => normalize(event.type || event.deprecatedType) === "warning")
    .filter((event) => eventMatchesApp(event, args.app, matchedPods))
    .map(normalizeWarningEvent);
  const referencedSecrets = new Set(warnings.map((event) => event.missingSecret).filter(Boolean));
  let secretNames = new Set();
  if (referencedSecrets.size > 0) {
    const secrets = parseItems(
      kubectl(["-n", args.namespace, "get", "secrets", "-o", "json"]),
      "secrets",
      result,
    );
    secretNames = new Set(secrets.map((secret) => secret.metadata?.name).filter(Boolean));
  }
  classifyEvents(result, warnings, baseline, secretNames);

  result.ok = result.errors.length === 0 && result.findings.length === 0;
  printJson(result, result.ok ? 0 : 1);
}

main();
