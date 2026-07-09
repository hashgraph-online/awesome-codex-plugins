#!/usr/bin/env node
import { spawnSync } from "node:child_process";
import { homedir } from "node:os";

const SIGNALS = [
  { id: "traceback", pattern: /Traceback \(most recent call last\):/ },
  { id: "http_exception", pattern: /\bHTTPException\b/ },
  { id: "not_found", pattern: /werkzeug\.exceptions\.NotFound|\bNotFound\b|404 Not Found/i },
  { id: "warning", pattern: /\bWARNING\b|:WARNING:/ },
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
  "",
  "Read-only log scanner for Sealos runtime smoke tests.",
].join("\n");

function parseArgs(argv) {
  const args = {
    namespace: "",
    app: "",
    since: "10m",
    tail: "300",
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
      args.namespace = argv[++i] || "";
    } else if (arg === "--app") {
      args.app = argv[++i] || "";
    } else if (arg === "--since") {
      args.since = argv[++i] || "";
    } else if (arg === "--tail") {
      args.tail = argv[++i] || "";
    } else {
      throw new Error(`Unknown argument: ${arg}`);
    }
  }

  return args;
}

function baseResult(args) {
  return {
    tool: "sealos-log-scan",
    generatedAt: new Date().toISOString(),
    namespace: args.namespace,
    app: args.app,
    since: args.since,
    tail: Number.parseInt(args.tail, 10),
    ok: false,
    dryRun: args.dryRun,
    pods: [],
    findings: [],
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
    ok: child.status === 0,
    status: child.status,
    stdout: child.stdout || "",
    stderr: child.stderr || "",
    command: `kubectl ${fullArgs.join(" ")}`,
  };
}

function normalize(value) {
  return String(value || "").toLowerCase();
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

function trimLine(line) {
  const text = line.trim();
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

function collectContainers(pod) {
  const containers = [];
  const add = (spec, status, type) => {
    containers.push({
      name: spec.name,
      type,
      ready: Boolean(status?.ready),
      restartCount: status?.restartCount || 0,
      state: status?.state || null,
      lastState: status?.lastState || null,
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

function scanLogStream(namespace, podName, containerName, since, tail, previous = false) {
  const args = [
    "-n",
    namespace,
    "logs",
    `pod/${podName}`,
    "-c",
    containerName,
    `--tail=${tail}`,
  ];

  if (since) {
    args.push(`--since=${since}`);
  }
  if (previous) {
    args.push("--previous");
  }

  return kubectl(args);
}

function appendFindings(result, podName, containerName, containerType, stream, signals) {
  for (const signal of signals) {
    result.findings.push({
      pod: podName,
      container: containerName,
      containerType,
      stream,
      signal: signal.id,
      count: signal.count,
      examples: signal.examples,
    });
  }
}

function scanPodLogs(result, pod, args) {
  const podName = pod.metadata?.name || "";
  const podResult = {
    name: podName,
    phase: pod.status?.phase || "",
    labels: pod.metadata?.labels || {},
    containers: [],
  };

  for (const container of collectContainers(pod)) {
    const containerResult = {
      ...container,
      statusSignals: statusSignals(container),
      streams: [],
    };
    appendFindings(result, podName, container.name, container.type, "status", containerResult.statusSignals);

    const current = scanLogStream(args.namespace, podName, container.name, args.since, args.tail, false);
    const currentSignals = current.ok ? scanText(current.stdout) : [];
    containerResult.streams.push({
      name: "current",
      ok: current.ok,
      lineCount: current.stdout ? current.stdout.split(/\r?\n/).filter(Boolean).length : 0,
      signals: currentSignals,
      error: current.ok ? null : trimLine(current.stderr || "kubectl logs failed"),
    });
    appendFindings(result, podName, container.name, container.type, "current", currentSignals);

    if (!current.ok) {
      result.errors.push({
        pod: podName,
        container: container.name,
        stream: "current",
        message: trimLine(current.stderr || "kubectl logs failed"),
      });
    }

    if (container.restartCount > 0) {
      const previous = scanLogStream(args.namespace, podName, container.name, args.since, args.tail, true);
      const previousSignals = previous.ok ? scanText(previous.stdout) : [];
      containerResult.streams.push({
        name: "previous",
        ok: previous.ok,
        lineCount: previous.stdout ? previous.stdout.split(/\r?\n/).filter(Boolean).length : 0,
        signals: previousSignals,
        error: previous.ok ? null : trimLine(previous.stderr || "kubectl logs --previous failed"),
      });
      appendFindings(result, podName, container.name, container.type, "previous", previousSignals);
    }

    podResult.containers.push(containerResult);
  }

  result.pods.push(podResult);
}

function main() {
  let args;
  try {
    args = parseArgs(process.argv.slice(2));
  } catch (error) {
    const result = baseResult({ namespace: "", app: "", since: "10m", tail: "300", dryRun: false });
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

  if (!args.namespace || !args.app) {
    result.errors.push({ message: "--namespace and --app are required", usage: USAGE });
    printJson(result, 2);
    return;
  }

  if (!Number.isInteger(result.tail) || result.tail <= 0) {
    result.errors.push({ message: "--tail must be a positive integer" });
    printJson(result, 2);
    return;
  }

  if (args.dryRun) {
    result.ok = true;
    printJson(result);
    return;
  }

  const podList = kubectl(["-n", args.namespace, "get", "pods", "-o", "json"]);
  if (!podList.ok) {
    result.errors.push({ message: trimLine(podList.stderr || "kubectl get pods failed") });
    printJson(result, 1);
    return;
  }

  let pods;
  try {
    pods = JSON.parse(podList.stdout).items || [];
  } catch (error) {
    result.errors.push({ message: `Unable to parse kubectl pod JSON: ${error.message}` });
    printJson(result, 1);
    return;
  }

  const matchedPods = pods.filter((pod) => podMatchesApp(pod, args.app));
  if (matchedPods.length === 0) {
    result.findings.push({
      signal: "no_pods",
      count: 1,
      examples: [{ line: 0, text: `No pods matched app '${args.app}' in namespace '${args.namespace}'` }],
    });
  }

  for (const pod of matchedPods) {
    scanPodLogs(result, pod, args);
  }

  result.ok = result.errors.length === 0 && result.findings.length === 0;
  printJson(result, result.errors.length > 0 ? 1 : 0);
}

main();
