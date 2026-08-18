#!/usr/bin/env node
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";

const SCRIPT_DIR = dirname(fileURLToPath(import.meta.url));
const SCANNER = join(SCRIPT_DIR, "sealos-log-scan.mjs");
const KUBECTL_FIXTURE = join(SCRIPT_DIR, "fixtures", "kubectl-fixture.cjs");
const APP = "demo";
const NAMESPACE = "ns";

function pod({
  ready = true,
  restartCount = 0,
  readyTransitionTime = "2026-07-15T00:00:20Z",
  uid = "pod-uid",
} = {}) {
  return {
    metadata: { name: "demo-0", uid, labels: { app: APP } },
    spec: { containers: [{ name: APP }] },
    status: {
      phase: ready ? "Running" : "Pending",
      conditions: [{ type: "Ready", status: ready ? "True" : "False", lastTransitionTime: readyTransitionTime }],
      containerStatuses: [{ name: APP, ready, restartCount, state: { running: {} } }],
    },
  };
}

function warning({
  uid = "event-uid",
  reason = "Unhealthy",
  message = "Startup probe failed: HTTP probe failed with statuscode: 404",
  count = 1,
  lastTimestamp = "2026-07-15T00:00:10Z",
  podUid = "pod-uid",
} = {}) {
  return {
    metadata: { uid, creationTimestamp: "2026-07-15T00:00:05Z" },
    type: "Warning",
    reason,
    message,
    count,
    firstTimestamp: "2026-07-15T00:00:05Z",
    lastTimestamp,
    involvedObject: { kind: "Pod", name: "demo-0", uid: podUid },
  };
}

function fixture({ pods = [pod()], events = [], secrets = [], logs = {}, failures = {} } = {}) {
  return { pods, events, secrets, logs, failures };
}

function runScan(runtimeFixture, extraArgs = []) {
  const dir = mkdtempSync(join(tmpdir(), "sealos-log-scan-test-"));
  const kubectl = join(dir, "kubectl");
  writeFileSync(kubectl, readFileSync(KUBECTL_FIXTURE, "utf8"), { mode: 0o755 });
  try {
    return spawnSync(
      process.execPath,
      [SCANNER, "--namespace", NAMESPACE, "--app", APP, ...extraArgs],
      {
        env: {
          ...process.env,
          KUBECONFIG: "/dev/null",
          PATH: `${dir}:${process.env.PATH}`,
          SEALOS_KUBECTL_FIXTURE_JSON: JSON.stringify(runtimeFixture),
        },
        encoding: "utf8",
      },
    );
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
}

function reportFrom(result) {
  assert.ok(result.stdout, result.stderr);
  return JSON.parse(result.stdout);
}

function sample(runtimeFixture) {
  const result = runScan(runtimeFixture);
  assert.equal(result.status, 0, result.stderr || result.stdout);
  return reportFrom(result);
}

function agedBaseline(runtimeFixture, seconds = 120) {
  const baseline = sample(runtimeFixture);
  baseline.generatedAt = new Date(Date.now() - seconds * 1000).toISOString();
  return baseline;
}

function compare(runtimeFixture, baseline, extraArgs = []) {
  return runScan(runtimeFixture, ["--baseline", JSON.stringify(baseline), ...extraArgs]);
}

test("sampling records Warning Events without failing solely on the Event", () => {
  const event = warning({
    reason: "FailedMount",
    message: 'MountVolume.SetUp failed: secret "demo-s3" not found',
  });
  const result = runScan(fixture({ events: [event] }));
  assert.equal(result.status, 0, result.stderr || result.stdout);
  const report = reportFrom(result);
  assert.equal(report.ok, true);
  assert.equal(report.events[0].classification, "observed");
  assert.equal(report.events[0].secret.exists, false);
  assert.equal(report.eventSummary.observed, 1);
});

test("stable startup and resolved Secret warnings become historical-transient", () => {
  const startup = warning({ uid: "startup-event", count: 3 });
  const secret = warning({
    uid: "secret-event",
    reason: "FailedMount",
    message: 'MountVolume.SetUp failed: secret "demo-s3" not found',
  });
  const initial = fixture({ events: [startup, secret] });
  const baseline = agedBaseline(initial);
  const current = fixture({
    events: [startup, secret],
    secrets: [{ metadata: { name: "demo-s3" } }],
  });
  const result = compare(current, baseline);
  assert.equal(result.status, 0, result.stderr || result.stdout);
  const report = reportFrom(result);
  assert.equal(report.ok, true);
  assert.equal(report.eventSummary["historical-transient"], 2);
  assert.deepEqual(report.events.map((event) => event.classification), ["historical-transient", "historical-transient"]);
  assert.equal(report.events.find((event) => event.reason === "FailedMount").secret.exists, true);
  assert.equal(report.events.find((event) => event.reason === "Unhealthy").occurredBeforeReady, true);
});

test("advanced Event count or last seen is an active failure", () => {
  const initialEvent = warning({ count: 1, lastTimestamp: "2026-07-15T00:00:10Z" });
  const baseline = agedBaseline(fixture({ events: [initialEvent] }));
  const currentEvent = warning({ count: 2, lastTimestamp: "2026-07-15T00:01:30Z" });
  const result = compare(fixture({ events: [currentEvent] }), baseline);
  assert.equal(result.status, 1);
  const report = reportFrom(result);
  assert.equal(report.ok, false);
  assert.equal(report.events[0].classification, "active-failure");
  assert.equal(report.events[0].delta.count, 1);
  assert.equal(report.events[0].delta.lastSeenAdvanced, true);
  assert.ok(report.findings.some((finding) => finding.signal === "active_warning_event"));
});

test("a still-missing Secret remains an active failure after a stable Event count", () => {
  const event = warning({
    reason: "FailedMount",
    message: 'MountVolume.SetUp failed: secret "demo-db" not found',
  });
  const baseline = agedBaseline(fixture({ events: [event] }));
  const result = compare(fixture({ events: [event] }), baseline);
  assert.equal(result.status, 1);
  const report = reportFrom(result);
  assert.equal(report.events[0].classification, "active-failure");
  assert.deepEqual(report.events[0].secret, { name: "demo-db", exists: false });
});

test("restart and Ready transition deltas fail convergence", () => {
  const event = warning();
  const baseline = agedBaseline(fixture({ pods: [pod()], events: [event] }));
  const currentPod = pod({ restartCount: 1, readyTransitionTime: "2026-07-15T00:02:00Z" });
  const result = compare(fixture({ pods: [currentPod], events: [event] }), baseline);
  assert.equal(result.status, 1);
  const report = reportFrom(result);
  assert.equal(report.pods[0].restartDelta, 1);
  assert.equal(report.pods[0].readyTransitionChanged, true);
  assert.equal(report.events[0].classification, "active-failure");
  assert.ok(report.findings.some((finding) => finding.signal === "restart_delta"));
  assert.ok(report.findings.some((finding) => finding.signal === "ready_transition_changed"));
});

test("stable historical restarts do not rescan old previous logs", () => {
  const stablePod = pod({ restartCount: 1 });
  const baseline = agedBaseline(fixture({ pods: [stablePod] }));
  const current = fixture({
    pods: [stablePod],
    logs: { "demo-0/demo/previous": "ERROR from an old terminated container\n" },
  });
  const result = compare(current, baseline);
  assert.equal(result.status, 0, result.stderr || result.stdout);
  const report = reportFrom(result);
  assert.equal(report.ok, true);
  assert.equal(report.pods[0].restartDelta, 0);
  assert.deepEqual(report.pods[0].containers[0].streams.map((stream) => stream.name), ["current"]);
});

test("a post-recovery baseline absorbs fault-injection history after a full window", () => {
  const injected = warning({
    uid: "injected-event",
    reason: "Unhealthy",
    message: "Readiness probe failed during intentional fault injection",
    count: 5,
    lastTimestamp: "2026-07-15T00:03:00Z",
  });
  const recoveryBaseline = agedBaseline(fixture({ events: [injected] }), 180);
  const result = compare(fixture({ events: [injected] }), recoveryBaseline, ["--min-window-seconds", "120"]);
  assert.equal(result.status, 0, result.stderr || result.stdout);
  const report = reportFrom(result);
  assert.equal(report.events[0].classification, "historical-transient");
  assert.equal(report.baseline.complete, true);
});

test("a comparison shorter than 60 seconds remains an incomplete observation", () => {
  const event = warning();
  const baseline = agedBaseline(fixture({ events: [event] }), 5);
  const result = compare(fixture({ events: [event] }), baseline);
  assert.equal(result.status, 1);
  const report = reportFrom(result);
  assert.equal(report.events[0].classification, "observed");
  assert.ok(report.findings.some((finding) => finding.signal === "stability_window_too_short"));
});

test("unrelated Warning Events are excluded", () => {
  const unrelated = {
    ...warning({ podUid: "other-pod", uid: "other-event" }),
    involvedObject: { kind: "Pod", name: "other-0", uid: "other-pod" },
  };
  const result = runScan(fixture({ events: [unrelated] }));
  assert.equal(result.status, 0, result.stderr || result.stdout);
  assert.equal(reportFrom(result).events.length, 0);
});

test("log findings and kubectl errors exit 1 while parameter errors exit 2", () => {
  const logResult = runScan(fixture({ logs: { "demo-0/demo/current": "ERROR startup failed\n" } }));
  assert.equal(logResult.status, 1);
  assert.equal(reportFrom(logResult).ok, false);

  const kubectlResult = runScan(fixture({ failures: { events: "events unavailable" } }));
  assert.equal(kubectlResult.status, 1);
  assert.equal(reportFrom(kubectlResult).ok, false);

  const parameterResult = spawnSync(process.execPath, [SCANNER, "--namespace", NAMESPACE, "--app"], {
    encoding: "utf8",
  });
  assert.equal(parameterResult.status, 2);
  assert.equal(reportFrom(parameterResult).ok, false);

  const integerResult = runScan(fixture(), ["--min-window-seconds", "60x"]);
  assert.equal(integerResult.status, 2);
  assert.equal(reportFrom(integerResult).ok, false);
});

test("completed Job Pods are terminal success and unchanged init output is historical", () => {
  const completedInitPod = {
    metadata: {
      name: "demo-job-0",
      uid: "job-pod-uid",
      labels: { app: APP },
      ownerReferences: [{ kind: "Job", name: "demo-init" }],
    },
    spec: {
      initContainers: [{ name: "init" }],
      containers: [{ name: APP }],
    },
    status: {
      phase: "Succeeded",
      conditions: [{ type: "Ready", status: "False" }],
      initContainerStatuses: [{
        name: "init",
        restartCount: 0,
        state: { terminated: { exitCode: 0, finishedAt: "2026-07-15T00:00:10Z" } },
      }],
      containerStatuses: [{
        name: APP,
        restartCount: 0,
        state: { terminated: { exitCode: 0, finishedAt: "2026-07-15T00:00:11Z" } },
      }],
    },
  };
  const runtimeFixture = fixture({
    pods: [completedInitPod],
    events: [warning({ podUid: "job-pod-uid" })],
    logs: {
      "demo-job-0/init/current": "WARNING bootstrap completed\n",
      "demo-job-0/demo/current": "migration complete\n",
    },
  });
  const baseline = agedBaseline(runtimeFixture, 120);
  const result = compare(runtimeFixture, baseline);
  assert.equal(result.status, 0, result.stderr || result.stdout);
  const report = reportFrom(result);
  assert.equal(report.ok, true);
  assert.equal(report.pods[0].lifecycle, "completed");
  assert.equal(report.pods[0].containers.find((item) => item.name === "init").historicalCompletedInit, true);
  assert.ok(report.observations.some((item) => item.historicalCompletedInit === true));
  assert.equal(report.findings.some((item) => item.signal === "pod_not_ready"), false);
  assert.equal(report.events[0].classification, "historical-transient");
});

test("failed Job Pods remain blocking findings", () => {
  const failedPod = {
    metadata: {
      name: "demo-job-0",
      uid: "failed-job-pod-uid",
      labels: { app: APP },
      ownerReferences: [{ kind: "Job", name: "demo-init" }],
    },
    spec: { containers: [{ name: APP }] },
    status: {
      phase: "Failed",
      conditions: [{ type: "Ready", status: "False" }],
      containerStatuses: [{
        name: APP,
        restartCount: 0,
        state: { terminated: { exitCode: 1, reason: "Error" } },
      }],
    },
  };
  const result = runScan(fixture({ pods: [failedPod] }));
  assert.equal(result.status, 1);
  const report = reportFrom(result);
  assert.equal(report.ok, false);
  assert.ok(report.findings.some((item) => item.signal === "pod_failed"));
});
