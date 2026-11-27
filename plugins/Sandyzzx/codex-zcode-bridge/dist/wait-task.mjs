#!/usr/bin/env node
// Thin host waiter adapted from PR #49 of codex-zcode-bridge
// (head 13ab83626a7fa7f35319a21244215c2915ecb112), contributed by Bill
// <chen.pengyu1@student.zy.cdut.edu.cn>, licensed under Apache-2.0.
// The task-state observation is replaced by the shared SQLite Attention Core.
var __defProp = Object.defineProperty;
var __getOwnPropNames = Object.getOwnPropertyNames;
var __esm = (fn, res, err) => function __init() {
  if (err) throw err[0];
  try {
    return fn && (res = (0, fn[__getOwnPropNames(fn)[0]])(fn = 0)), res;
  } catch (e) {
    throw err = [e], e;
  }
};
var __export = (target, all) => {
  for (var name in all)
    __defProp(target, name, { get: all[name], enumerable: true });
};

// src/result-contract.mjs
function canonical(value) {
  if (value === null || typeof value === "string" || typeof value === "boolean") return JSON.stringify(value);
  if (typeof value === "number" && Number.isSafeInteger(value)) return JSON.stringify(value);
  if (Array.isArray(value)) return `[${value.map(canonical).join(",")}]`;
  if (value && Object.getPrototypeOf(value) === Object.prototype) return `{${Object.keys(value).sort().map((k) => `${JSON.stringify(k)}:${canonical(value[k])}`).join(",")}}`;
  throw new ResultContractError("invalid_json_value");
}
function isStringArray(value) {
  return Array.isArray(value) && value.every((x) => typeof x === "string");
}
function validateTestReport(value) {
  if (!value || Object.getPrototypeOf(value) !== Object.prototype) return { ok: false, error: "entry is not an object" };
  if (typeof value.command !== "string") return { ok: false, error: "command must be a string" };
  if (!["passed", "failed", "not_run"].includes(value.status)) return { ok: false, error: "status must be one of passed|failed|not_run" };
  if (value.details !== void 0 && typeof value.details !== "string") return { ok: false, error: "details must be a string when present" };
  return { ok: true, test: { command: value.command, status: value.status, ...value.details === void 0 ? {} : { details: value.details } } };
}
function validateReportFields(value, partial = false) {
  if (!value || Object.getPrototypeOf(value) !== Object.prototype) fail("invalid_result_payload", "report is not a JSON object");
  for (const key of ["summary", "files_changed", "tests", "issues", "needs_master_decision"]) {
    if (partial && !Object.hasOwn(value, key)) continue;
    const v = value[key];
    if (key === "tests") {
      if (!Array.isArray(v)) fail("invalid_result_payload", "report.tests must be an array");
      for (const entry of v) {
        const parsed = validateTestReport(entry);
        if (!parsed.ok) fail("invalid_result_payload", `report.tests entry invalid: ${parsed.error}`);
      }
    } else if (key === "summary" ? typeof v !== "string" : key === "needs_master_decision" ? typeof v !== "boolean" : !isStringArray(v)) {
      fail("invalid_result_payload", `report.${key} must be ${key === "summary" ? "a string" : key === "needs_master_decision" ? "a boolean" : "an array of strings"}`);
    }
  }
}
function validText(value, max) {
  return typeof value === "string" && value.length > 0 && value.length <= max && !/[\x00-\x1f]/u.test(value);
}
function isNullableText(value, max = 4096) {
  return value === null || typeof value === "string" && value.length <= max && !/[\x00-\x1f]/u.test(value);
}
function validateStringArray(value, maxItems = 256) {
  if (!Array.isArray(value) || value.length > maxItems || value.some((x) => typeof x !== "string" || x.length > 4096 || /[\x00-\x1f]/u.test(x))) fail("invalid_result_payload");
}
function validateResultObject(value, keys, required = []) {
  if (!value || Object.getPrototypeOf(value) !== Object.prototype) fail("invalid_result_payload");
  const own = Object.keys(value);
  if (own.some((k) => !keys.has(k)) || required.some((k) => !Object.hasOwn(value, k))) fail("invalid_result_payload");
}
function validateUsage(value) {
  validateResultObject(
    value,
    /* @__PURE__ */ new Set(["source", "scope", "observed_at", "finality", "input_tokens", "output_tokens", "total_tokens", "cached_input_tokens", "cached_write_input_tokens", "reasoning_tokens", "conflicts", "dropped_unknown_keys"]),
    ["source", "scope", "observed_at", "finality", "input_tokens", "output_tokens", "total_tokens", "cached_input_tokens", "reasoning_tokens", "conflicts", "dropped_unknown_keys"]
  );
  if (!isNullableText(value.source) || !isNullableText(value.scope) || !isNullableText(value.observed_at) || !["reported", "derived", "partial"].includes(value.finality) || ["input_tokens", "output_tokens", "total_tokens", "cached_input_tokens", "cached_write_input_tokens", "reasoning_tokens"].some((k) => Object.hasOwn(value, k) && value[k] !== null && (!Number.isSafeInteger(value[k]) || value[k] < 0)) || !Number.isSafeInteger(value.dropped_unknown_keys) || value.dropped_unknown_keys < 0) fail("invalid_result_payload");
  validateStringArray(value.conflicts, 64);
}
function validateModel(value) {
  validateResultObject(
    value,
    /* @__PURE__ */ new Set(["executor", "provider_id", "model_id", "requested_model", "requested_reasoning_level", "effective_reasoning_level", "effective_reasoning_level_source", "selection_source", "effective_at", "session_id", "turn_id"]),
    ["executor", "provider_id", "model_id", "requested_model", "requested_reasoning_level", "effective_reasoning_level", "effective_reasoning_level_source", "selection_source", "effective_at", "session_id", "turn_id"]
  );
  if (typeof value.executor !== "string" || !["runtime", "not_reported"].includes(value.effective_reasoning_level_source) || ["provider_id", "model_id", "requested_model", "requested_reasoning_level", "effective_reasoning_level", "selection_source", "effective_at", "session_id", "turn_id"].some((k) => !isNullableText(value[k]))) fail("invalid_result_payload");
}
function validateTiming(value) {
  validateResultObject(value, /* @__PURE__ */ new Set(["queued_ms", "execution_ms", "turn_ms", "finalize_ms", "wall_ms", "derived", "notes"]), ["queued_ms", "execution_ms", "turn_ms", "finalize_ms", "wall_ms", "derived", "notes"]);
  if (["queued_ms", "execution_ms", "turn_ms", "finalize_ms", "wall_ms"].some((k) => value[k] !== null && (!Number.isSafeInteger(value[k]) || value[k] < 0)) || typeof value.derived !== "boolean") fail("invalid_result_payload");
  validateStringArray(value.notes, 64);
}
function validateRpcDiagnostics(value, status) {
  if (status !== "failed" || !Array.isArray(value) || value.length < 1 || value.length > MAX_RPC_DIAGNOSTICS) fail("invalid_result_payload");
  const seen = /* @__PURE__ */ new Set();
  for (const entry of value) {
    validateResultObject(entry, /* @__PURE__ */ new Set(["method", "code", "message", "data_name", "data_code", "stack"]), ["method", "code", "message", "data_name", "data_code"]);
    const stack = Object.hasOwn(entry, "stack") ? entry.stack : "";
    const stackLines = typeof stack === "string" ? stack.split("\n") : [];
    const identity = `${String(entry.method)}|${String(entry.code)}|${String(entry.data_code)}`;
    if (typeof entry.method !== "string" || !RPC_METHOD.test(entry.method) || !(entry.code === null || typeof entry.code === "number" && Number.isSafeInteger(entry.code)) || typeof entry.message !== "string" || !CLEAN_DIAGNOSTIC_TEXT(entry.message) || /[\r\n\t]/u.test(entry.message) || [...entry.message].length > 500 || !(entry.data_name === null || typeof entry.data_name === "string" && CLEAN_DIAGNOSTIC_TEXT(entry.data_name) && entry.data_name.length <= 64 && RPC_DATA_NAME.test(entry.data_name)) || !(entry.data_code === null || typeof entry.data_code === "string" && CLEAN_DIAGNOSTIC_TEXT(entry.data_code) && entry.data_code.length <= 128 && RPC_DATA_CODE.test(entry.data_code)) || Object.hasOwn(entry, "stack") && (typeof entry.stack !== "string" || entry.stack.length > 1200 || stackLines.length > 12 || stackLines.some((line) => !CLEAN_DIAGNOSTIC_TEXT(line) || !RPC_STACK_LINE.test(line))) || seen.has(identity)) fail("invalid_result_payload");
    seen.add(identity);
  }
  if (Buffer.byteLength(canonical(value), "utf8") > MAX_RPC_DIAGNOSTICS_BYTES) fail("invalid_result_payload");
}
function canonicalTaskResult(result, input) {
  validateResultObject(result, RESULT_FIELDS, REQUIRED_RESULT_FIELDS);
  if (result.task_id !== input.task_id || result.attempt !== input.attempt || result.status !== input.result_status || !RESULT_STATUSES.has(result.status) || typeof result.summary !== "string" || typeof result.zcode_output !== "string" || typeof result.needs_master_decision !== "boolean" || result.exit_code !== null && !Number.isSafeInteger(result.exit_code) || !isNullableText(result.session_id) || !isNullableText(result.started_at, 64) || !isNullableText(result.finished_at, 64)) fail("invalid_result_payload");
  validateReportFields(result);
  if (Object.hasOwn(result, "error_code") && !validText(result.error_code, 128)) fail("invalid_result_payload");
  if (Object.hasOwn(result, "report_candidate")) {
    validateResultObject(result.report_candidate, /* @__PURE__ */ new Set(["summary", "files_changed", "tests", "issues", "needs_master_decision"]));
    validateReportFields(result.report_candidate, true);
  }
  if (Object.hasOwn(result, "usage") && result.usage !== null) validateUsage(result.usage);
  if (Object.hasOwn(result, "model") && result.model !== null) validateModel(result.model);
  if (Object.hasOwn(result, "timing") && result.timing !== null) validateTiming(result.timing);
  if (Object.hasOwn(result, "rpc_diagnostics")) validateRpcDiagnostics(result.rpc_diagnostics, result.status);
  const json = canonical(result);
  const bytes = Buffer.byteLength(json, "utf8");
  if (bytes > MAX_TASK_RESULT_BYTES) throw new ResultContractError("result_too_large", `canonical TaskResult ${bytes} bytes exceeds ${MAX_TASK_RESULT_BYTES}; original report not committed`);
  return json;
}
var MAX_TASK_RESULT_BYTES, MAX_RESULT_ENVELOPE_BYTES, MAX_WORKER_RESULT_FRAME_BYTES, ResultContractError, fail, RESULT_STATUSES, RESULT_FIELDS, REQUIRED_RESULT_FIELDS, MAX_RPC_DIAGNOSTICS, MAX_RPC_DIAGNOSTICS_BYTES, RPC_METHOD, RPC_STACK_LINE, RPC_DATA_NAME, RPC_DATA_CODE, CLEAN_DIAGNOSTIC_TEXT;
var init_result_contract = __esm({
  "src/result-contract.mjs"() {
    "use strict";
    MAX_TASK_RESULT_BYTES = 32 * 1024 * 1024;
    MAX_RESULT_ENVELOPE_BYTES = 256 * 1024;
    MAX_WORKER_RESULT_FRAME_BYTES = MAX_TASK_RESULT_BYTES + MAX_RESULT_ENVELOPE_BYTES;
    ResultContractError = class extends Error {
      constructor(code, message = code) {
        super(message);
        this.code = code;
      }
    };
    fail = (code, message = code) => {
      throw new ResultContractError(code, message);
    };
    RESULT_STATUSES = /* @__PURE__ */ new Set(["completed", "failed", "cancelled", "waiting_for_master"]);
    RESULT_FIELDS = /* @__PURE__ */ new Set(["task_id", "attempt", "status", "summary", "files_changed", "tests", "issues", "needs_master_decision", "zcode_output", "exit_code", "session_id", "started_at", "finished_at", "error_code", "report_candidate", "usage", "model", "timing", "rpc_diagnostics"]);
    REQUIRED_RESULT_FIELDS = ["task_id", "attempt", "status", "summary", "files_changed", "tests", "issues", "needs_master_decision", "zcode_output", "exit_code", "session_id", "started_at", "finished_at"];
    MAX_RPC_DIAGNOSTICS = 4;
    MAX_RPC_DIAGNOSTICS_BYTES = 8192;
    RPC_METHOD = /^[a-z]+(?:\/[A-Za-z0-9_]+){1,2}$/u;
    RPC_STACK_LINE = /^at (?:(?:[^\s()\\/:]+)? ?(?:\((?:node:[^\s()\\]*|[^\s()\\/]*)\)|node:[^\s()\\]*|[^\s()\\/]*))$/u;
    RPC_DATA_NAME = /^[A-Za-z][A-Za-z0-9_]*$/u;
    RPC_DATA_CODE = /^[A-Za-z0-9][A-Za-z0-9_.:-]*$/u;
    CLEAN_DIAGNOSTIC_TEXT = (text) => typeof text === "string" && !/[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]/u.test(text);
  }
});

// src/sqlite-candidate/wp6b2b1/interaction-channel.mjs
function isCandidateInteractionPreparedAcknowledgement(value) {
  return !!value && PREPARED_ACKNOWLEDGEMENTS.has(value);
}
function isCandidateInteractionAcknowledgement(value) {
  return !!value && ACKNOWLEDGEMENTS.has(value);
}
var ACKNOWLEDGEMENTS, PREPARED_ACKNOWLEDGEMENTS, MAX_REQUEST_BYTES, MAX_FRAME_BYTES;
var init_interaction_channel = __esm({
  "src/sqlite-candidate/wp6b2b1/interaction-channel.mjs"() {
    "use strict";
    ACKNOWLEDGEMENTS = /* @__PURE__ */ new WeakSet();
    PREPARED_ACKNOWLEDGEMENTS = /* @__PURE__ */ new WeakSet();
    MAX_REQUEST_BYTES = 1048576;
    MAX_FRAME_BYTES = MAX_REQUEST_BYTES + 8192;
  }
});

// src/store/json-history-result-exceptions.mjs
import { createHash } from "node:crypto";
function freeze(value) {
  if (value && typeof value === "object" && !Object.isFrozen(value)) {
    for (const child of Object.values(value)) freeze(child);
    Object.freeze(value);
  }
  return value;
}
function canonical2(value) {
  if (value === null || typeof value !== "object") return JSON.stringify(value);
  if (Array.isArray(value)) return `[${value.map(canonical2).join(",")}]`;
  return `{${Object.keys(value).sort().map((key) => `${JSON.stringify(key)}:${canonical2(value[key])}`).join(",")}}`;
}
function historicalResultExceptionArtifactId(relativePath) {
  const digest2 = createHash("sha256").update(relativePath).digest("hex");
  return `artifact-${digest2.slice(0, 40)}`;
}
function annotateHistoricalResultException(entry) {
  return Object.freeze({
    exception_id: entry.exception_id,
    task_id: entry.task_id,
    stored_attempt: entry.stored_attempt,
    internal_attempt: entry.internal_attempt,
    relative_path: entry.relative_path,
    artifact_id: historicalResultExceptionArtifactId(entry.relative_path),
    sha256: entry.sha256,
    byte_length: entry.byte_length,
    archive_anomaly: Object.freeze({ ...entry.archive_anomaly })
  });
}
function historicalResultExceptionSetDigest(entries) {
  return createHash("sha256").update(canonical2(entries)).digest("hex");
}
function isCanonicalHistoricalResultExceptionSet(entries) {
  if (!Array.isArray(entries) || entries.length !== HISTORICAL_RESULT_EXCEPTIONS.length) return false;
  return HISTORICAL_RESULT_EXCEPTIONS.every((expected, index) => {
    const actual = entries[index];
    const annotated = annotateHistoricalResultException(expected);
    return canonical2(actual) === canonical2(annotated);
  });
}
function historicalResultExceptionTaskIds(entries) {
  return [...new Set(entries.map((entry) => entry.task_id))].sort((left, right) => left.localeCompare(right, "en"));
}
var HISTORICAL_RESULT_EXCEPTIONS;
var init_json_history_result_exceptions = __esm({
  "src/store/json-history-result-exceptions.mjs"() {
    "use strict";
    HISTORICAL_RESULT_EXCEPTIONS = freeze([
      {
        exception_id: "cad2bim_rm02_attempt_2_result_stored_at_3",
        task_id: "CAD2BIM_FULL_AUDIT_RM02_001",
        stored_attempt: 3,
        internal_attempt: 2,
        relative_path: "CAD2BIM_FULL_AUDIT_RM02_001/attempts/3/result.json",
        sha256: "539c76d236155688feb906a8dfb9764f92a2f76ff8e16b97e6177c2e7bd95530",
        byte_length: 13981,
        archive_anomaly: {
          code: "conflicting_projection",
          path: "CAD2BIM_FULL_AUDIT_RM02_001/attempts/3/result.json",
          record_type: "attempt",
          detail: "result_attempt_does_not_match_storage_generation"
        }
      },
      {
        exception_id: "cad2bim_rm02_attempt_3_result_stored_at_4",
        task_id: "CAD2BIM_FULL_AUDIT_RM02_001",
        stored_attempt: 4,
        internal_attempt: 3,
        relative_path: "CAD2BIM_FULL_AUDIT_RM02_001/attempts/4/result.json",
        sha256: "ec6faea33c6b3b7c299b2c4a6094c431b670d807e00398ed03364ec5a1c61cd3",
        byte_length: 12989,
        archive_anomaly: {
          code: "conflicting_projection",
          path: "CAD2BIM_FULL_AUDIT_RM02_001/attempts/4/result.json",
          record_type: "attempt",
          detail: "result_attempt_does_not_match_storage_generation"
        }
      },
      {
        exception_id: "project_alignment_current_attempt_2_root_result_binds_1",
        task_id: "PROJECT-ALIGNMENT-DOC-HYGIENE-CLOSE-1-COMMIT-20260930",
        stored_attempt: 2,
        internal_attempt: 1,
        relative_path: "PROJECT-ALIGNMENT-DOC-HYGIENE-CLOSE-1-COMMIT-20260930/result.json",
        sha256: "494235a230178fe2aeb0128210bba0cf8fec5029202b07b0a1b3648476d3e12e",
        byte_length: 6247,
        archive_anomaly: {
          code: "conflicting_projection",
          path: "PROJECT-ALIGNMENT-DOC-HYGIENE-CLOSE-1-COMMIT-20260930/result.json",
          record_type: "result",
          detail: "result_attempt_does_not_match_storage_generation"
        }
      }
    ]);
  }
});

// src/feedback/task-feedback-projection.mjs
function record(value) {
  return typeof value === "object" && value !== null && !Array.isArray(value) ? value : null;
}
function safeRuntimeText(value) {
  if (typeof value !== "string") return null;
  const text = value.replace(/[\u0000-\u001f\u007f]/gu, " ").trim();
  return text ? text.slice(0, 160) : null;
}
function safeToolName(value) {
  if (typeof value !== "string") return "tool";
  const name = value.replace(/[^A-Za-z0-9_.-]/gu, "").slice(0, 80);
  return name || "tool";
}
function durationMs(startedAt, finishedAt) {
  if (!startedAt || !finishedAt) return null;
  const start = Date.parse(startedAt);
  const finish = Date.parse(finishedAt);
  if (!Number.isFinite(start) || !Number.isFinite(finish) || finish < start) return null;
  return finish - start;
}
function buildTaskFeedbackSnapshotV01(input) {
  let model = null;
  let activity = null;
  let agentReportReady = false;
  for (const event of input.events) {
    const details = record(event.details);
    if (event.type === "model_selected" && details) {
      const providerId = safeRuntimeText(details.provider_id);
      const modelId = safeRuntimeText(details.model_id);
      if (providerId && modelId) {
        model = {
          provider_id: providerId,
          model_id: modelId,
          reasoning_level: details.reasoning_level_source === "runtime" ? safeRuntimeText(details.reasoning_level) : null,
          source: "runtime"
        };
      }
    } else if (event.type === "model_tool_call" && details) {
      activity = {
        kind: "tool_call",
        summary: `Tool request \xB7 ${safeToolName(details.tool_name)}`,
        observed_at: event.at,
        currentness: "last_observed"
      };
    } else if (event.type === "tool_status" && details) {
      activity = {
        kind: "tool_update",
        summary: `Tool update \xB7 ${safeToolName(details.tool_name)}`,
        observed_at: event.at,
        currentness: "last_observed"
      };
    } else if (event.type === "report_ready") {
      agentReportReady = true;
    }
  }
  const finalResult = input.result;
  const result = agentReportReady && finalResult && finalResult.attempt === input.status.attempt && finalResult.status === input.status.status && (finalResult.status === "completed" || finalResult.status === "waiting_for_master") ? {
    source: "agent_report",
    summary: finalResult.summary,
    issues: [...finalResult.issues],
    files_changed: [...finalResult.files_changed],
    tests: finalResult.tests.map((test) => ({ ...test })),
    started_at: input.status.started_at,
    finished_at: input.status.finished_at,
    duration_ms: durationMs(input.status.started_at, input.status.finished_at)
  } : null;
  return {
    schema_version: "0.1",
    task_id: input.status.task_id,
    attempt: input.status.attempt,
    status: input.status.status,
    model,
    phase: null,
    progress: null,
    activity,
    interaction: { ...EMPTY_INTERACTION },
    result
  };
}
var EMPTY_INTERACTION;
var init_task_feedback_projection = __esm({
  "src/feedback/task-feedback-projection.mjs"() {
    "use strict";
    EMPTY_INTERACTION = Object.freeze({ state: "not_observed", kind: null });
  }
});

// src/sqlite-candidate/wp6b2b1/store.mjs
var store_exports = {};
__export(store_exports, {
  AdmissionError: () => AdmissionError,
  IsolatedAdmissionStore: () => IsolatedAdmissionStore,
  canonical: () => canonical3,
  createWriterIntentIdentity: () => createWriterIntentIdentity,
  digest: () => digest,
  validateWorkspace: () => validateWorkspace
});
import { DatabaseSync } from "node:sqlite";
import { createHash as createHash2, randomUUID } from "node:crypto";
import { spawnSync } from "node:child_process";
import { existsSync, lstatSync, realpathSync, readFileSync, writeFileSync, openSync, closeSync, fsyncSync, unlinkSync, renameSync, statSync, readSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
function canonical3(value) {
  try {
    return canonical(value);
  } catch (error) {
    throw new AdmissionError(error.code ?? "invalid_json_value", error.message);
  }
}
function schemaObjects(db) {
  return db.prepare(SCHEMA_OBJECT_QUERY).all().map((row) => [
    row.type,
    row.name,
    row.tbl_name,
    row.sql === null ? null : row.sql.trim().replace(/\r\n?/gu, "\n")
  ]);
}
function normalizedTriggerSql(sql) {
  return String(sql).trim().replace(/\r\n?/gu, "\n").replace(/\s+/gu, " ");
}
function recoveryBindingTriggerSql() {
  if (expectedRecoveryBindingTriggerSql === void 0) {
    const db = new DatabaseSync(":memory:");
    try {
      db.exec(SCHEMA);
      expectedRecoveryBindingTriggerSql = db.prepare(
        "SELECT sql FROM sqlite_schema WHERE type='trigger' AND name='cleanup_reverified_binding_guard'"
      ).get()?.sql;
    } finally {
      db.close();
    }
    if (typeof expectedRecoveryBindingTriggerSql !== "string") throw new Error("Recovery binding trigger schema is missing");
  }
  return expectedRecoveryBindingTriggerSql;
}
function legacyRecoveryBindingTriggerSql() {
  const current = recoveryBindingTriggerSql();
  const start = current.indexOf("    AND (\n      (\n        json_type(NEW.evidence_json,'$.resolved_recovery_event_digests')='array'");
  const end = start < 0 ? -1 : current.indexOf("    AND NOT EXISTS (\n      SELECT 1 FROM manager_operation_events x", start);
  if (start < 0 || end < 0) throw new Error("Recovery binding trigger compatibility marker is missing");
  const legacyBlock = `    AND json_type(NEW.evidence_json,'$.resolved_recovery_event_digests')='array'
    AND json_array_length(NEW.evidence_json,'$.resolved_recovery_event_digests')<=8
    AND json_array_length(NEW.evidence_json,'$.resolved_recovery_event_digests')=(
      SELECT COUNT(*) FROM manager_operation_events h
      WHERE h.operation_id=NEW.operation_id AND h.event_type='observation_recorded'
        AND h.sequence<NEW.sequence AND json_extract(h.evidence_json,'$.reason')='recovery_hold'
        AND json_extract(h.evidence_json,'$.classification')='hold'
        AND json_extract(h.evidence_json,'$.reason_code') IN ('cleanup_identity_unknown','cleanup_incomplete'))
    AND NOT EXISTS (
      SELECT 1 FROM manager_operation_events h
      WHERE h.operation_id=NEW.operation_id AND h.event_type='observation_recorded'
        AND h.sequence<NEW.sequence AND json_extract(h.evidence_json,'$.reason') IN ('recovery_hold','recovery_quarantine')
        AND (json_extract(h.evidence_json,'$.reason')<>'recovery_hold'
          OR json_extract(h.evidence_json,'$.classification')<>'hold'
          OR json_extract(h.evidence_json,'$.reason_code') NOT IN ('cleanup_identity_unknown','cleanup_incomplete')))
    AND NOT EXISTS (
      SELECT 1 FROM json_each(NEW.evidence_json,'$.resolved_recovery_event_digests') j
      WHERE NOT EXISTS (
        SELECT 1 FROM manager_operation_events h
        WHERE h.operation_id=NEW.operation_id AND h.event_type='observation_recorded'
          AND h.evidence_digest=j.value AND h.sequence<NEW.sequence
          AND json_extract(h.evidence_json,'$.reason')='recovery_hold'
          AND json_extract(h.evidence_json,'$.classification')='hold'
          AND json_extract(h.evidence_json,'$.reason_code') IN ('cleanup_identity_unknown','cleanup_incomplete')))
`;
  return current.slice(0, start) + legacyBlock + current.slice(end);
}
function upgradeRecoveryBindingTrigger(db) {
  const current = recoveryBindingTriggerSql();
  const legacy = legacyRecoveryBindingTriggerSql();
  const read = () => db.prepare("SELECT sql FROM sqlite_schema WHERE type='trigger' AND name='cleanup_reverified_binding_guard'").get()?.sql;
  const actual = read();
  if (typeof actual !== "string") fail2("candidate_schema_mismatch");
  if (normalizedTriggerSql(actual) === normalizedTriggerSql(current)) return false;
  if (normalizedTriggerSql(actual) !== normalizedTriggerSql(legacy)) fail2("candidate_schema_mismatch");
  let began = false;
  try {
    db.exec("BEGIN IMMEDIATE");
    began = true;
    const locked = read();
    if (normalizedTriggerSql(locked) === normalizedTriggerSql(current)) {
      db.exec("COMMIT");
      began = false;
      return false;
    }
    if (normalizedTriggerSql(locked) !== normalizedTriggerSql(legacy)) fail2("candidate_schema_mismatch");
    db.exec("DROP TRIGGER cleanup_reverified_binding_guard");
    db.exec(current + ";");
    db.exec("COMMIT");
    began = false;
    return true;
  } catch (error) {
    if (began) try {
      db.exec("ROLLBACK");
    } catch {
    }
    throw error;
  }
}
function adminAbandonmentTableStatement(schema) {
  const start = schema.indexOf("CREATE TABLE manager_admin_abandonments");
  const end = schema.indexOf(";", start);
  if (start < 0 || end < 0) throw new Error("administrative abandonment table statement is missing");
  return schema.slice(start, end + 1).trim().replace(/\r\n?/gu, "\n");
}
function normalizeAdminAbandonmentTableSql(sql) {
  const normalized = String(sql).trim().replace(/\r\n?/gu, "\n");
  return normalized.endsWith(";") ? normalized.slice(0, -1) : normalized;
}
function adminAbandonmentRowsDigest(rows) {
  return createHash2("sha256").update(rows.map(upgradeRowJson).join("\n")).digest("hex");
}
function withoutSchemaObjects(objects, names) {
  return objects.filter((row) => !names.has(row[1]));
}
function assertCandidateSchema(db, {
  allowRuntimeEventExtensionAbsent = false,
  allowOwnerBindingExtensionAbsent = false,
  allowLegacyRecoveryBindingTrigger = false
} = {}) {
  const key = allowRuntimeEventExtensionAbsent ? "recovery" : "strict";
  if (!expectedSchemas.has(key)) {
    const base = new DatabaseSync(":memory:"), admin = new DatabaseSync(":memory:"), legacyAdmin = new DatabaseSync(":memory:");
    try {
      base.exec(SCHEMA);
      admin.exec(SCHEMA + "\n" + ADMIN_ABANDONMENT_SCHEMA);
      legacyAdmin.exec(SCHEMA + "\n" + LEGACY_ADMIN_ABANDONMENT_SCHEMA);
      const baseObjects = schemaObjects(base);
      const adminObjects = schemaObjects(admin);
      const legacyAdminObjects = schemaObjects(legacyAdmin);
      const variants = [JSON.stringify(baseObjects), JSON.stringify(adminObjects), JSON.stringify(legacyAdminObjects)];
      for (const [objects2] of [[baseObjects], [adminObjects], [legacyAdminObjects]]) {
        if (allowRuntimeEventExtensionAbsent) {
          variants.push(JSON.stringify(withoutSchemaObjects(objects2, RUNTIME_EVENT_SCHEMA_OBJECTS)));
        }
        if (allowOwnerBindingExtensionAbsent) {
          variants.push(JSON.stringify(withoutSchemaObjects(objects2, OWNER_BINDING_SCHEMA_OBJECTS)));
        }
        if (allowRuntimeEventExtensionAbsent && allowOwnerBindingExtensionAbsent) {
          const withoutBoth = withoutSchemaObjects(
            withoutSchemaObjects(objects2, RUNTIME_EVENT_SCHEMA_OBJECTS),
            OWNER_BINDING_SCHEMA_OBJECTS
          );
          variants.push(JSON.stringify(withoutBoth));
        }
      }
      expectedSchemas.set(key, variants);
    } finally {
      base.close();
      admin.close();
      legacyAdmin.close();
    }
  }
  const objects = schemaObjects(db);
  if (allowLegacyRecoveryBindingTrigger) {
    const trigger = objects.find((row) => row[0] === "trigger" && row[1] === "cleanup_reverified_binding_guard");
    if (trigger && normalizedTriggerSql(trigger[3]) === normalizedTriggerSql(legacyRecoveryBindingTriggerSql())) {
      trigger[3] = recoveryBindingTriggerSql().trim().replace(/\r\n?/gu, "\n");
    }
  }
  if (!expectedSchemas.get(key).includes(JSON.stringify(objects))) fail2("candidate_schema_mismatch");
}
function upgradeLegacyAdminAbandonmentSchema(db) {
  const table = db.prepare("SELECT sql FROM sqlite_schema WHERE type='table' AND name='manager_admin_abandonments'").get();
  if (!table) return false;
  const tableSql = normalizeAdminAbandonmentTableSql(table.sql);
  if (tableSql === NORMALIZED_ADMIN_ABANDONMENT_TABLE_SQL) return false;
  if (tableSql !== NORMALIZED_LEGACY_ADMIN_ABANDONMENT_TABLE_SQL) fail2("candidate_schema_mismatch");
  const legacyTable = "manager_admin_abandonments_v14_legacy";
  if (db.prepare("SELECT 1 FROM sqlite_schema WHERE name=?").get(legacyTable)) fail2("admin_abandonment_schema_migration_collision");
  const columns = db.prepare("PRAGMA table_info('manager_admin_abandonments')").all().map((row) => row.name);
  const names = columns.map((column) => '"' + column.replaceAll('"', '""') + '"');
  const beforeRows = db.prepare("SELECT * FROM manager_admin_abandonments ORDER BY operation_id").all();
  const beforeDigest = adminAbandonmentRowsDigest(beforeRows);
  db.exec("DROP TRIGGER manager_admin_abandonments_no_update");
  db.exec("DROP TRIGGER manager_admin_abandonments_no_delete");
  db.exec("ALTER TABLE manager_admin_abandonments RENAME TO " + legacyTable);
  db.exec(ADMIN_ABANDONMENT_TABLE_SQL);
  db.prepare(`INSERT INTO manager_admin_abandonments(${names.join(",")}) SELECT ${names.join(",")} FROM ${legacyTable}`).run();
  const afterRows = db.prepare("SELECT * FROM manager_admin_abandonments ORDER BY operation_id").all();
  if (beforeRows.length !== afterRows.length || adminAbandonmentRowsDigest(afterRows) !== beforeDigest) fail2("admin_abandonment_schema_migration_mismatch");
  db.exec("DROP TABLE " + legacyTable);
  db.exec(ADMIN_ABANDONMENT_SCHEMA.slice(ADMIN_ABANDONMENT_SCHEMA.indexOf("CREATE TRIGGER")).trim());
  assertCandidateSchema(db);
  return true;
}
function rejectV13UpgradeMarker(databasePath) {
  if (existsSync(v13UpgradeMarker(databasePath))) fail2("unsupported_sqlite_schema", V13_UPGRADE_MARKER_MESSAGE);
}
function walChecksum(buffer, start, length, s0, s1, littleEndian) {
  for (let offset = start; offset < start + length; offset += 8) {
    const first = littleEndian ? buffer.readUInt32LE(offset) : buffer.readUInt32BE(offset);
    const second = littleEndian ? buffer.readUInt32LE(offset + 4) : buffer.readUInt32BE(offset + 4);
    s0 = s0 + first + s1 >>> 0;
    s1 = s1 + second + s0 >>> 0;
  }
  return [s0, s1];
}
function walPageOneVersion(walPath, mainVersion) {
  if (!existsSync(walPath)) return mainVersion;
  const fd = openSync(walPath, "r");
  try {
    const header = Buffer.alloc(32);
    if (readSync(fd, header, 0, header.length, 0) !== header.length) return mainVersion;
    const magic = header.readUInt32BE(0);
    if (magic !== 931071618 && magic !== 931071619) return mainVersion;
    if (header.readUInt32BE(4) !== 3007e3) return mainVersion;
    const pageSize = header.readUInt32BE(8);
    if (pageSize < 512 || pageSize > 65536 || (pageSize & pageSize - 1) !== 0) return mainVersion;
    const salt1 = header.readUInt32BE(16), salt2 = header.readUInt32BE(20);
    const littleEndian = magic === 931071618;
    let checksum = walChecksum(header, 0, 24, 0, 0, littleEndian);
    if (checksum[0] !== header.readUInt32BE(24) || checksum[1] !== header.readUInt32BE(28)) return mainVersion;
    const frameHeader = Buffer.alloc(24), page = Buffer.alloc(pageSize);
    let offset = 32, currentPageOneVersion = mainVersion, lastCommittedPageOneVersion = mainVersion;
    while (true) {
      if (readSync(fd, frameHeader, 0, frameHeader.length, offset) !== frameHeader.length) break;
      if (frameHeader.readUInt32BE(8) !== salt1 || frameHeader.readUInt32BE(12) !== salt2) break;
      const pageNumber = frameHeader.readUInt32BE(0), databasePagesAfterCommit = frameHeader.readUInt32BE(4);
      if (readSync(fd, page, 0, page.length, offset + 24) !== page.length) break;
      checksum = walChecksum(frameHeader, 0, 8, checksum[0], checksum[1], littleEndian);
      checksum = walChecksum(page, 0, page.length, checksum[0], checksum[1], littleEndian);
      if (checksum[0] !== frameHeader.readUInt32BE(16) || checksum[1] !== frameHeader.readUInt32BE(20)) break;
      if (pageNumber === 1) {
        if (page.length < 100 || page.subarray(0, 16).toString("latin1") !== "SQLite format 3\0") break;
        currentPageOneVersion = page.readUInt32BE(60);
      }
      if (databasePagesAfterCommit !== 0) lastCommittedPageOneVersion = currentPageOneVersion;
      offset += 24 + pageSize;
    }
    return lastCommittedPageOneVersion;
  } catch {
    return mainVersion;
  } finally {
    closeSync(fd);
  }
}
function preflightSchemaVersion(databasePath) {
  let version;
  try {
    const fd = openSync(databasePath, "r");
    const header = Buffer.alloc(100);
    try {
      if (readSync(fd, header, 0, header.length, 0) !== header.length) return;
      if (header.subarray(0, 16).toString("latin1") !== "SQLite format 3\0") return;
      version = walPageOneVersion(databasePath + "-wal", header.readUInt32BE(60));
    } finally {
      closeSync(fd);
    }
  } catch {
    return;
  }
  if (version === 13) fail2("unsupported_sqlite_schema", SQLITE_V14_ONLY_MESSAGE);
}
function assertSchemaVersion(db) {
  const version = db.prepare("PRAGMA user_version").get().user_version;
  if (version === 13) fail2("unsupported_sqlite_schema", SQLITE_V14_ONLY_MESSAGE);
  if (version !== SCHEMA_VERSION) fail2("schema_version_unknown");
}
function ensureRuntimeEventsSchema(db) {
  if (db.prepare("SELECT 1 FROM sqlite_schema WHERE type='table' AND name='runtime_task_events'").get()) return;
  let began = false;
  try {
    db.exec("BEGIN IMMEDIATE");
    began = true;
    if (db.prepare("SELECT 1 FROM sqlite_schema WHERE type='table' AND name='runtime_task_events'").get()) {
      db.exec("COMMIT");
      began = false;
      return;
    }
    db.exec(RUNTIME_EVENTS_SCHEMA);
    db.exec("COMMIT");
    began = false;
  } catch (error) {
    if (began) try {
      db.exec("ROLLBACK");
    } catch {
    }
    throw error;
  }
}
function ownerBindingsSchema() {
  const start = SCHEMA.indexOf("CREATE TABLE task_owner_bindings");
  const end = SCHEMA.indexOf("CREATE TABLE attempts", start);
  if (start < 0 || end < 0) throw new Error("owner binding schema is missing");
  return SCHEMA.slice(start, end).trim();
}
function ensureOwnerBindingsSchema(db) {
  if (db.prepare("SELECT 1 FROM sqlite_schema WHERE type='table' AND name='task_owner_bindings'").get() && !db.prepare(`SELECT 1 FROM tasks
      WHERE task_id NOT IN (SELECT task_id FROM task_owner_bindings) LIMIT 1`).get()) return;
  let began = false;
  try {
    db.exec("BEGIN IMMEDIATE");
    began = true;
    if (!db.prepare("SELECT 1 FROM sqlite_schema WHERE type='table' AND name='task_owner_bindings'").get()) {
      db.exec(ownerBindingsSchema());
    }
    db.prepare(`INSERT INTO task_owner_bindings(task_id,binding_state,owner_thread_id,binding_source,bound_at)
      SELECT task_id,'unavailable',NULL,'legacy_unavailable',?
      FROM tasks
      WHERE task_id NOT IN (SELECT task_id FROM task_owner_bindings)`).run((/* @__PURE__ */ new Date()).toISOString());
    db.exec("COMMIT");
    began = false;
  } catch (error) {
    if (began) try {
      db.exec("ROLLBACK");
    } catch {
    }
    throw error;
  }
}
function resolvedRecoveryCommitment(digests) {
  const ordered = sortedDigests(digests);
  return {
    resolved_recovery_event_count: ordered.length,
    resolved_recovery_event_root: digest({ contract: RESOLVED_RECOVERY_SET_CONTRACT, event_digests: ordered })
  };
}
function validateResolvedRecoverySet(value, { minimum = 0, failureCode = "invalid_resolved_recovery_set" } = {}) {
  const hasArray = Object.hasOwn(value, "resolved_recovery_event_digests");
  const hasCount = Object.hasOwn(value, "resolved_recovery_event_count");
  const hasRoot = Object.hasOwn(value, "resolved_recovery_event_root");
  if (hasArray === (hasCount || hasRoot) || hasCount !== hasRoot) fail2(failureCode);
  if (hasArray) {
    const digests = value.resolved_recovery_event_digests;
    if (!Array.isArray(digests) || digests.length < minimum || digests.some((item) => typeof item !== "string" || !/^[0-9a-f]{64}$/u.test(item)) || new Set(digests).size !== digests.length || digests.join("|") !== sortedDigests(digests).join("|")) fail2(failureCode);
    return { kind: "digests", digests: [...digests] };
  }
  if (!Number.isSafeInteger(value.resolved_recovery_event_count) || value.resolved_recovery_event_count < minimum || typeof value.resolved_recovery_event_root !== "string" || !/^[0-9a-f]{64}$/u.test(value.resolved_recovery_event_root)) fail2(failureCode);
  return { kind: "commitment", count: value.resolved_recovery_event_count, root: value.resolved_recovery_event_root };
}
function resolvedRecoverySetMatches(value, eligible, failureCode) {
  const set = validateResolvedRecoverySet(value, { minimum: 0, failureCode });
  const ordered = sortedDigests(eligible);
  if (set.kind === "digests") {
    if (set.digests.join("|") !== ordered.join("|")) fail2(failureCode);
    return ordered;
  }
  const commitment = resolvedRecoveryCommitment(ordered);
  if (set.count !== commitment.resolved_recovery_event_count || set.root !== commitment.resolved_recovery_event_root) fail2(failureCode);
  return ordered;
}
function recoveryMaterialFacts(operationId, evidence, phase) {
  if (!evidence || Object.getPrototypeOf(evidence) !== Object.prototype) return null;
  const facts = { contract: RECOVERY_MATERIAL_CONTRACT, operation_id: operationId };
  for (const key of RECOVERY_MATERIAL_BINDING_KEYS) if (evidence[key] !== void 0) facts[key] = evidence[key];
  if (evidence.phase !== void 0) facts.phase = evidence.phase;
  else if (phase !== void 0) facts.phase = phase;
  for (const key of RECOVERY_MATERIAL_DETAIL_KEYS) if (evidence[key] !== void 0) facts[key] = evidence[key];
  return facts;
}
function recoveryMaterialDigest(operationId, evidence, phase) {
  const facts = recoveryMaterialFacts(operationId, evidence, phase);
  return facts ? digest(facts) : null;
}
function validateEvidence(eventType, value) {
  const keys = EVIDENCE_KEYS[eventType];
  if (!value || Object.getPrototypeOf(value) !== Object.prototype) fail2("invalid_evidence");
  if (eventType === "observation_recorded") validateObservationEventEvidence(value);
  else if (eventType.startsWith("interaction_")) validateInteractionEvidence(eventType, value);
  else if (eventType === "result_committed") {
    const base = ["claim_id", "outcome", "result_commit_ref", "result_digest", "worker_identity_digest"];
    const expected = value.outcome === "cancelled" ? [...base, "cancel_verification_digest"] : base;
    if (Object.keys(value).sort().join("|") !== expected.sort().join("|")) fail2("invalid_evidence");
  } else if (eventType === "reserved") {
    const fields = Object.keys(value).sort().join("|");
    if (fields !== ["capacity_slot", "reservation_id"].join("|") && fields !== ["authorization_source", "capacity_slot", "execution_profile_id", "policy_digest", "policy_revision", "reservation_id"].join("|")) fail2("invalid_evidence");
  } else if (keys) {
    let expectedKeys = (["cleanup_verified", "cleanup_reverified"].includes(eventType) && value.adapter_cleanup === void 0 ? keys.filter((key) => key !== "adapter_cleanup") : [...keys]).sort();
    if (eventType === "cleanup_reverified") {
      const resolvedSet = validateResolvedRecoverySet(value, { minimum: 0, failureCode: "invalid_cleanup_reverification" });
      expectedKeys = [...expectedKeys, ...resolvedSet.kind === "digests" ? ["resolved_recovery_event_digests"] : ["resolved_recovery_event_count", "resolved_recovery_event_root"]].sort();
    }
    if (Object.keys(value).sort().join("|") !== expectedKeys.join("|")) fail2("invalid_evidence");
  }
  if (["cleanup_verified", "cleanup_reverified"].includes(eventType) && value.adapter_cleanup !== void 0 && !validAdapterCleanupEvidence(value.adapter_cleanup)) fail2("invalid_adapter_cleanup_evidence");
  if (FUTURE_EVENT_TYPES.has(eventType)) {
    const ownKeys = Object.keys(value);
    if (!ownKeys.length || ownKeys.some((k) => !FUTURE_EVIDENCE_KEYS.has(k))) fail2("invalid_evidence");
    for (const [k, v] of Object.entries(value)) {
      if (k === "adapter_cleanup") {
        continue;
      }
      if (k.endsWith("_digest") || k === "token_digest") {
        if (typeof v !== "string" || !/^[0-9a-f]{64}$/u.test(v)) fail2("invalid_evidence");
      } else if (k === "launch_epoch") {
        if (!Number.isInteger(v) || v < 1) fail2("invalid_evidence");
      } else if (k === "root_process_id") {
        if (!Number.isSafeInteger(v) || v < 1) fail2("invalid_evidence");
      } else if (k === "resolved_recovery_event_count") {
        if (!Number.isSafeInteger(v) || v < 0) fail2("invalid_evidence");
      } else if (["operation_resources_complete", "worker_tree_complete", "workspace_touched"].includes(k)) {
        if (typeof v !== "boolean") fail2("invalid_evidence");
      } else if (typeof v !== "string" || !validText2(v, 256)) fail2("invalid_evidence");
    }
  } else if (!keys) fail2("invalid_evidence");
  if (eventType === "capacity_policy_committed" && (!Number.isInteger(value.capacity_limit) || value.capacity_limit < 1 || value.capacity_limit > 8 || !Number.isInteger(value.generation) || value.generation < 1)) fail2("invalid_evidence");
  if (eventType === "reserved" && (!validText2(value.reservation_id, 128) || !Number.isInteger(value.capacity_slot) || value.capacity_slot < 1 || value.capacity_slot > 8)) fail2("invalid_evidence");
  if (eventType === "reserved" && "authorization_source" in value && (value.authorization_source !== "trusted_local_policy" || !validText2(value.policy_revision, 64) || !validText2(value.execution_profile_id, 64) || typeof value.policy_digest !== "string" || !/^[0-9a-f]{64}$/u.test(value.policy_digest))) fail2("invalid_evidence");
  if (eventType === "observation_recorded" && (!validText2(value.reason, 256) || typeof value.evidence_digest !== "string" || !/^[0-9a-f]{64}$/u.test(value.evidence_digest))) fail2("invalid_evidence");
  if (eventType === "cleanup_reverified" && (!/^([0-9a-f]{64})$/u.test(value.prior_cleanup_event_digest) || !validId(value.operation_id) || !validId(value.task_id) || !Number.isSafeInteger(value.attempt) || value.attempt < 1 || !Number.isSafeInteger(value.generation) || value.generation < 1)) fail2("invalid_cleanup_reverification");
  for (const key of ["launch_id", "claim_id"]) if (key in value && !validText2(value[key], 128)) fail2("invalid_evidence");
  if ("launch_epoch" in value && (!Number.isInteger(value.launch_epoch) || value.launch_epoch < 1)) fail2("invalid_evidence");
  const recoveryObservation = eventType === "observation_recorded" && (value.reason === "recovery_hold" || value.reason === "recovery_quarantine");
  const executorWake = eventType === "observation_recorded" && value.reason === "executor_wake";
  const json = canonical3(value);
  const maxBytes = ["cleanup_verified", "cleanup_reverified"].includes(eventType) || recoveryObservation || executorWake ? 2048 : 1024;
  if (Buffer.byteLength(json, "utf8") > maxBytes) fail2("invalid_evidence");
  return value;
}
function validateInteractionEvidence(eventType, value) {
  const keys = EVIDENCE_KEYS[eventType];
  if (!keys || Object.keys(value).sort().join("|") !== keys.join("|") || !validId(value.request_id) || value.request_id.length > 512 || !validId(value.claim_id) || typeof value.worker_identity_digest !== "string" || !/^[0-9a-f]{64}$/u.test(value.worker_identity_digest))
    fail2("invalid_interaction_evidence");
  if (eventType === "interaction_requested") {
    if (!["interaction/requestPermission", "interaction/requestUserInput"].includes(value.request_method) || typeof value.request_digest !== "string" || !/^[0-9a-f]{64}$/u.test(value.request_digest)) fail2("invalid_interaction_evidence");
  } else if (!validId(value.reply_id) || typeof value.answer_digest !== "string" || !/^[0-9a-f]{64}$/u.test(value.answer_digest) || eventType === "interaction_reply_prepared" && (typeof value.prepared_digest !== "string" || !/^[0-9a-f]{64}$/u.test(value.prepared_digest)) || eventType === "interaction_reply_committed" && [value.prepared_digest, value.commit_digest].some((v) => typeof v !== "string" || !/^[0-9a-f]{64}$/u.test(v)) || eventType === "interaction_reply_accepted" && [value.ack_digest, value.commit_digest].some((v) => typeof v !== "string" || !/^[0-9a-f]{64}$/u.test(v))) fail2("invalid_interaction_evidence");
  if (Buffer.byteLength(canonical3(value), "utf8") > 1024) fail2("invalid_interaction_evidence");
}
function validateObservationEventEvidence(value) {
  const own = Object.keys(value).sort().join("|");
  if (own === EXECUTOR_WAKE_BASE_EVIDENCE_KEYS.join("|") || own === EXECUTOR_WAKE_EVIDENCE_KEYS.join("|")) {
    const { evidence_digest, ...unsigned } = value;
    const executorWake = value.reason === "executor_wake";
    const lateWake = value.reason === LATE_WAKE_REASON;
    if (!executorWake && !lateWake || !(executorWake ? EXECUTOR_WAKE_STATES : LATE_WAKE_STATES).has(value.state) || !validId(value.task_id) || !validId(value.operation_id) || !Number.isSafeInteger(value.attempt) || value.attempt < 1 || !Number.isSafeInteger(value.generation) || value.generation < 1 || ![value.result_digest, value.policy_digest, value.authorization_digest, value.delivery_id].every((item) => typeof item === "string" && /^[0-9a-f]{64}$/u.test(item)) || !validId(value.result_commit_ref) || !validText2(value.reason_code, 128) || value.thread_id !== null && !validId(value.thread_id) || executorWake && value.state !== "web_notify" && value.thread_id === null || lateWake && value.thread_id === null || "queue_message_id" in value && (!validId(value.queue_message_id) || value.state !== "queued") || evidence_digest !== digest(unsigned) || [value.task_id, value.operation_id, value.result_commit_ref].some((item) => item !== item.normalize("NFC"))) fail2("invalid_executor_wake_evidence");
    return;
  }
  if (own === "cancel_id|evidence_digest|launch_id|reason|request_digest|token_digest") {
    const { evidence_digest, ...unsigned } = value;
    if (value.reason !== "cancelled_before_claim" || ![value.cancel_id, value.launch_id].every(validId) || ![value.request_digest, value.token_digest].every((v) => typeof v === "string" && /^[0-9a-f]{64}$/u.test(v)) || evidence_digest !== digest(unsigned)) fail2("invalid_queued_cancel");
    return;
  }
  const cancelResolutionBase = ["cancel_id", "cancellation_verification_digest", "evidence_digest", "proof_digest", "reason"];
  const cancelResolutionVariants = [
    [...cancelResolutionBase, "resolved_recovery_event_digests"].sort().join("|"),
    [...cancelResolutionBase, "resolved_recovery_event_count", "resolved_recovery_event_root"].sort().join("|")
  ];
  if (cancelResolutionVariants.includes(own)) {
    const { evidence_digest, ...unsigned } = value;
    if (value.reason !== "cancel_recovery_resolved" || !validId(value.cancel_id) || ![value.cancellation_verification_digest, value.proof_digest].every((v) => typeof v === "string" && /^[0-9a-f]{64}$/u.test(v)) || evidence_digest !== digest(unsigned)) fail2("invalid_cancellation_resolution");
    validateResolvedRecoverySet(value, { minimum: 1, failureCode: "invalid_cancellation_resolution" });
    return;
  }
  if (own === "evidence_digest|reason") return;
  if (own === "claim_id|evidence_digest|reason|recovery_evidence_digest|result_commit_ref|result_digest|worker_identity_digest") {
    const { evidence_digest, ...unsigned } = value;
    if (value.reason !== "user_authorized_release_unverified" || ![value.recovery_evidence_digest, value.result_digest, value.worker_identity_digest].every((item) => typeof item === "string" && /^[0-9a-f]{64}$/u.test(item)) || !validId(value.claim_id) || typeof value.result_commit_ref !== "string" || !/^(?:result-)?[0-9a-f]{64}$/u.test(value.result_commit_ref) || evidence_digest !== digest(unsigned)) fail2("invalid_user_authorized_release_evidence");
    return;
  }
  if (own === "cancel_id|evidence_digest|reason" || own === "cancel_id|evidence_digest|launch_receipt_digest|reason|worker_risk_accepted" || own === "cancel_id|cancellation_verification_digest|evidence_digest|reason|recovery_evidence_digest") {
    const { evidence_digest, ...unsigned } = value;
    if (value.reason !== "user_authorized_release_unverified" || !validId(value.cancel_id) || own.includes("cancellation_verification_digest") && ![value.cancellation_verification_digest, value.recovery_evidence_digest].every((item) => typeof item === "string" && /^[0-9a-f]{64}$/u.test(item)) || evidence_digest !== digest(unsigned)) fail2("invalid_user_authorized_release_evidence");
    return;
  }
  if (own === "cancel_id|claim_id|evidence_digest|identity_evidence_digest|identity_state|reason|worker_identity_digest") {
    if (value.reason !== "cancel_requested" || !validId(value.cancel_id) || !validId(value.claim_id) || !["alive", "exited"].includes(value.identity_state) || ![value.evidence_digest, value.identity_evidence_digest, value.worker_identity_digest].every((v) => typeof v === "string" && /^[0-9a-f]{64}$/u.test(v)))
      fail2("invalid_cancellation_intent");
    return;
  }
  if (own === "cancel_id|claim_id|evidence_digest|intent_event_digest|process_tree_digest|proof_digest|reason|root_process_id|root_start_fingerprint|worker_identity_digest|worker_tree_complete") {
    if (value.reason !== "cancel_tree_verified" || !validId(value.cancel_id) || !validId(value.claim_id) || ![value.evidence_digest, value.intent_event_digest, value.process_tree_digest, value.proof_digest, value.worker_identity_digest].every((v) => typeof v === "string" && /^[0-9a-f]{64}$/u.test(v)) || !Number.isSafeInteger(value.root_process_id) || value.root_process_id < 1 || !validText2(value.root_start_fingerprint, 256) || value.worker_tree_complete !== true)
      fail2("invalid_cancellation_verification");
    return;
  }
  const recoveryRequired = new Set(RECOVERY_EVIDENCE_KEYS);
  const recoveryReleaseKeys = ["process_tree_root_observed", "process_tree_scan_clean", "process_tree_scan_digest", "recovery_disposition"];
  const recoveryAllowed = /* @__PURE__ */ new Set([...RECOVERY_EVIDENCE_KEYS, ...recoveryReleaseKeys, ...RECOVERY_MATERIAL_DETAIL_KEYS, "material_digest"]);
  const recoveryOwnKeys = Object.keys(value);
  if ([...recoveryRequired].some((key) => !Object.hasOwn(value, key)) || recoveryOwnKeys.some((key) => !recoveryAllowed.has(key))) fail2("invalid_evidence");
  if (!Number.isSafeInteger(value.attempt) || value.attempt < 1 || !Number.isSafeInteger(value.expected_revision) || value.expected_revision < 1 || !validId(value.task_id) || !validId(value.claim_id) || !["hold", "quarantine"].includes(value.classification) || !["recovery_hold", "recovery_quarantine"].includes(value.reason) || value.reason !== `recovery_${value.classification}` || !RECOVERY_REASON_CODES.has(value.reason_code) || !RECOVERY_SOURCES.has(value.evidence_source) || RECOVERY_QUARANTINE_CODES.has(value.reason_code) !== (value.classification === "quarantine") || ![value.envelope_digest, value.evidence_digest, value.worker_identity_digest].every((v) => typeof v === "string" && /^[0-9a-f]{64}$/u.test(v)) || [value.task_id, value.claim_id, value.reason_code].some((v) => v !== v.normalize("NFC"))) {
    fail2("invalid_recovery_observation");
  }
  const releaseMarker = Object.hasOwn(value, "process_tree_root_observed") || Object.hasOwn(value, "process_tree_scan_digest");
  const releaseFieldsPresent = recoveryReleaseKeys.filter((key) => Object.hasOwn(value, key));
  if (releaseMarker && (releaseFieldsPresent.length !== recoveryReleaseKeys.length || value.classification !== "hold" || value.reason_code !== "cleanup_incomplete" || value.recovery_disposition !== "complete_cleanup_closure_unavailable" || value.process_tree_scan_clean !== true || value.process_tree_root_observed !== true || typeof value.process_tree_scan_digest !== "string" || !/^[0-9a-f]{64}$/u.test(value.process_tree_scan_digest)))
    fail2("invalid_recovery_release_evidence");
  if (value.material_digest !== void 0 && (typeof value.material_digest !== "string" || !/^[0-9a-f]{64}$/u.test(value.material_digest)))
    fail2("invalid_recovery_observation");
  if (value.phase !== void 0 && !RECOVERY_PHASES.has(value.phase)) fail2("invalid_recovery_observation");
  for (const key of ["identity_state", "probe_reason", "process_tree_scan_scope", "recovery_disposition"])
    if (value[key] !== void 0 && !validText2(value[key], 128)) fail2("invalid_recovery_observation");
  if (value.process_id !== void 0 && (!Number.isSafeInteger(value.process_id) || value.process_id < 1)) fail2("invalid_recovery_observation");
  if (value.start_fingerprint !== void 0 && !validText2(value.start_fingerprint, 256)) fail2("invalid_recovery_observation");
  for (const key of ["complete_cleanup_closure", "process_tree_root_observed", "process_tree_scan_clean"])
    if (value[key] !== void 0 && typeof value[key] !== "boolean") fail2("invalid_recovery_observation");
  if (value.process_tree_scan_digest !== void 0 && (typeof value.process_tree_scan_digest !== "string" || !/^[0-9a-f]{64}$/u.test(value.process_tree_scan_digest)))
    fail2("invalid_recovery_observation");
}
function recoveryEnvelope(input) {
  const inputKeys = input && Object.getPrototypeOf(input) === Object.prototype ? Object.keys(input).sort().join("|") : "";
  const releaseInput = inputKeys === [...RECOVERY_RELEASE_INPUT_KEYS].sort().join("|");
  if (!input || Object.getPrototypeOf(input) !== Object.prototype || !releaseInput && inputKeys !== [...RECOVERY_INPUT_KEYS].sort().join("|") || ![input.operation_id, input.task_id, input.claim_id].every(validId) || ![input.attempt, input.generation, input.expected_revision].every((v) => Number.isSafeInteger(v) && v >= 1) || !["hold", "quarantine"].includes(input.classification) || !RECOVERY_REASON_CODES.has(input.reason_code) || RECOVERY_QUARANTINE_CODES.has(input.reason_code) !== (input.classification === "quarantine") || !RECOVERY_SOURCES.has(input.evidence_source) || ![input.worker_identity_digest, input.evidence_digest].every((v) => typeof v === "string" && /^[0-9a-f]{64}$/u.test(v)) || [input.operation_id, input.task_id, input.claim_id, input.reason_code].some((v) => v !== v.normalize("NFC"))) {
    fail2("invalid_recovery_observation");
  }
  if (releaseInput && (input.classification !== "hold" || input.reason_code !== "cleanup_incomplete" || input.recovery_disposition !== "complete_cleanup_closure_unavailable" || input.process_tree_scan_clean !== true || input.process_tree_root_observed !== true || typeof input.process_tree_scan_digest !== "string" || !/^[0-9a-f]{64}$/u.test(input.process_tree_scan_digest)))
    fail2("invalid_recovery_release_evidence");
  return {
    contract: "wp6c-c3b-recovery-observation-v1",
    operation_id: input.operation_id,
    task_id: input.task_id,
    attempt: input.attempt,
    generation: input.generation,
    expected_revision: input.expected_revision,
    claim_id: input.claim_id,
    worker_identity_digest: input.worker_identity_digest,
    classification: input.classification,
    reason_code: input.reason_code,
    evidence_source: input.evidence_source,
    evidence_digest: input.evidence_digest,
    ...releaseInput ? {
      process_tree_root_observed: true,
      process_tree_scan_clean: true,
      process_tree_scan_digest: input.process_tree_scan_digest,
      recovery_disposition: input.recovery_disposition
    } : {}
  };
}
function recoveryEventEvidence(input, envelopeDigest, evidence, phase) {
  const stable = {};
  for (const key of RECOVERY_MATERIAL_DETAIL_KEYS) {
    if (evidence[key] === void 0 || evidence[key] === null) continue;
    stable[key] = evidence[key];
  }
  const event = {
    attempt: input.attempt,
    claim_id: input.claim_id,
    classification: input.classification,
    envelope_digest: envelopeDigest,
    evidence_digest: input.evidence_digest,
    evidence_source: input.evidence_source,
    expected_revision: input.expected_revision,
    reason: `recovery_${input.classification}`,
    reason_code: input.reason_code,
    task_id: input.task_id,
    worker_identity_digest: input.worker_identity_digest,
    ...stable,
    ...input.recovery_disposition !== void 0 ? {
      process_tree_root_observed: input.process_tree_root_observed,
      process_tree_scan_clean: input.process_tree_scan_clean,
      process_tree_scan_digest: input.process_tree_scan_digest,
      recovery_disposition: input.recovery_disposition
    } : {}
  };
  return { ...event, material_digest: recoveryMaterialDigest(input.operation_id, event, phase) };
}
function recoveryEventsFor(events, operationId) {
  const operation = typeof operationId === "object" ? operationId : null;
  const id = operation?.operation_id ?? operationId;
  const operationEvents = events.filter((e) => e.operation_id === id);
  const claimSequence = operationEvents.find((e) => e.event_type === "claim_committed")?.sequence;
  const recovery = [];
  for (const event of operationEvents) {
    if (event.event_type !== "observation_recorded") continue;
    let evidence;
    try {
      evidence = event.evidence ?? JSON.parse(event.evidence_json);
    } catch {
      fail2("invalid_evidence");
    }
    const recoveryMarker = typeof evidence?.reason === "string" && (evidence.reason.startsWith("recovery_") || Object.hasOwn(evidence, "classification"));
    if (!recoveryMarker) continue;
    validateObservationEventEvidence(evidence);
    if (!operation) fail2("recovery_operation_binding_required");
    validateRecoveryEventBinding(operation, event, evidence, claimSequence);
    recovery.push({ event, evidence });
  }
  const resolved = /* @__PURE__ */ new Set();
  for (const event of operationEvents) {
    if (event.event_type !== "observation_recorded") continue;
    const evidence = event.evidence ?? JSON.parse(event.evidence_json);
    if (evidence.reason !== "cancel_recovery_resolved") continue;
    validateObservationEventEvidence(evidence);
    const verification = operationEvents.find((e) => e.evidence_digest === evidence.cancellation_verification_digest);
    const verified = verification && (verification.evidence ?? JSON.parse(verification.evidence_json));
    if (!operation || event.from_phase !== "running" || event.to_phase !== "running" || event.generation !== operation.generation || !verification || verification.sequence >= event.sequence || verified.reason !== "cancel_tree_verified" || verified.cancel_id !== evidence.cancel_id || verified.claim_id !== operation.claim_id || verified.worker_identity_digest !== operation.claim_worker_identity_digest || verified.proof_digest !== evidence.proof_digest)
      fail2("cancellation_resolution_binding_mismatch");
    const eligible = recovery.filter((item) => item.event.sequence < event.sequence && !resolved.has(item.event.evidence_digest));
    if (eligible.some((item) => item.evidence.classification !== "hold" || !["cleanup_identity_unknown", "cleanup_incomplete"].includes(item.evidence.reason_code) || item.event.sequence >= verification.sequence)) fail2("cancellation_resolution_hold_mismatch");
    const committed = resolvedRecoverySetMatches(
      evidence,
      eligible.map((item) => item.event.evidence_digest),
      "cancellation_resolution_hold_mismatch"
    );
    for (const hash of committed) resolved.add(hash);
  }
  for (const event of operationEvents) {
    if (event.event_type !== "cleanup_reverified") continue;
    let evidence;
    try {
      evidence = event.evidence ?? JSON.parse(event.evidence_json);
    } catch {
      fail2("cleanup_reverification_history_invalid");
    }
    validateEvidence("cleanup_reverified", evidence);
    const prior = operationEvents.find((candidate) => candidate.event_type === "cleanup_unverified");
    const priorEvidence = prior && JSON.parse(prior.evidence_json);
    if (!operation || !prior || prior.evidence_digest !== evidence.prior_cleanup_event_digest || prior.sequence >= event.sequence || event.from_phase !== "cleanup_unverified" || event.to_phase !== "cleanup_reverified" || event.generation !== operation.generation || evidence.operation_id !== operation.operation_id || evidence.task_id !== operation.task_id || evidence.attempt !== operation.attempt || evidence.generation !== operation.generation || evidence.claim_id !== operation.claim_id || evidence.worker_identity_digest !== operation.claim_worker_identity_digest || evidence.launch_receipt_digest !== operation.launch_receipt_digest || evidence.result_commit_ref !== operation.result_commit_ref || !priorEvidence || priorEvidence.claim_id !== evidence.claim_id || priorEvidence.worker_identity_digest !== evidence.worker_identity_digest)
      fail2("cleanup_reverification_history_mismatch");
    const between = operationEvents.filter((candidate) => candidate.sequence > prior.sequence && candidate.sequence < event.sequence);
    const betweenRecovery = recovery.filter((item) => item.event.sequence > prior.sequence && item.event.sequence < event.sequence);
    const eligible = betweenRecovery.filter((item) => !resolved.has(item.event.evidence_digest));
    if (between.some((candidate) => candidate.event_type !== "observation_recorded") || betweenRecovery.length !== between.length || betweenRecovery.some((item) => item.evidence.classification !== "hold" || !["cleanup_identity_unknown", "cleanup_incomplete"].includes(item.evidence.reason_code)))
      fail2("cleanup_reverification_intervening_event_mismatch");
    const committed = resolvedRecoverySetMatches(
      evidence,
      eligible.map((item) => item.event.evidence_digest),
      "cleanup_reverification_hold_binding_mismatch"
    );
    for (const eventDigest of committed) resolved.add(eventDigest);
  }
  return recovery.map((item) => ({ ...item, active: !resolved.has(item.event.evidence_digest) }));
}
function foldedRecoveryClassification(operation, events) {
  let level = operation.phase === "quarantined" ? 2 : 0;
  for (const { evidence, active } of recoveryEventsFor(events, operation)) if (active) level = Math.max(level, evidence.classification === "quarantine" ? 2 : 1);
  return level === 2 ? "quarantine" : level === 1 ? "hold" : "normal";
}
function cancellableRecoveryHolds(operation, events) {
  const active = recoveryEventsFor(events, operation).filter((item) => item.active);
  if (operation.phase === "quarantined" || active.some((item) => item.evidence.classification !== "hold" || !["cleanup_identity_unknown", "cleanup_incomplete"].includes(item.evidence.reason_code))) fail2("operation_recovery_latched");
  return active;
}
function validText2(value, max) {
  return typeof value === "string" && value.length > 0 && value.length <= max && !/[\x00-\x1f]/u.test(value);
}
function canonicalTaskResult2(result, input) {
  try {
    return canonicalTaskResult(result, input);
  } catch (error) {
    fail2(error.code ?? "invalid_result_payload", error.message);
  }
}
function fixtureLaunchIdentity(value) {
  if (value?.source === "manager_os_spawn_observation") {
    const { evidence_digest, ...evidence } = value;
    if (Object.getPrototypeOf(value) !== Object.prototype || value.fixture !== false || !validId(value.launch_id) || !Number.isSafeInteger(value.generation) || value.generation < 1 || !Number.isSafeInteger(value.process_id) || value.process_id < 1 || !validText2(value.start_fingerprint, 256) || value.fingerprint_precision !== "exact" || !Number.isSafeInteger(value.identity_version) || value.identity_version < 1 || value.platform !== "win32" || !validText2(value.captured_at, 64) || typeof evidence_digest !== "string" || !/^[0-9a-f]{64}$/u.test(evidence_digest) || digest(evidence) !== evidence_digest || Object.keys(value).sort().join("|") !== "captured_at|evidence_digest|fingerprint_precision|fixture|generation|identity_version|launch_id|platform|process_id|source|start_fingerprint") fail2("invalid_trusted_launch_identity");
    return value;
  }
  if (!value || Object.getPrototypeOf(value) !== Object.prototype || value.source !== "synthetic_fixture" || value.fixture !== true || !Number.isSafeInteger(value.process_id) || value.process_id < 1 || !validText2(value.start_fingerprint, 256) || Object.keys(value).sort().join("|") !== "fixture|process_id|source|start_fingerprint") fail2("invalid_synthetic_launch_identity");
  return value;
}
function fixtureWorkerIdentity(value) {
  if (value?.source === "manager_verified_process_probe") {
    const { evidence_digest, ...evidence } = value;
    if (Object.getPrototypeOf(value) !== Object.prototype || value.fixture !== false || !validId(value.worker_id) || !Number.isSafeInteger(value.process_id) || value.process_id < 1 || !validText2(value.start_fingerprint, 256) || value.fingerprint_precision !== "exact" || !Number.isSafeInteger(value.identity_version) || value.identity_version < 1 || value.platform !== "win32" || !validText2(value.captured_at, 64) || typeof evidence_digest !== "string" || !/^[0-9a-f]{64}$/u.test(evidence_digest) || digest(evidence) !== evidence_digest || Object.keys(value).sort().join("|") !== "captured_at|evidence_digest|fingerprint_precision|fixture|identity_version|platform|process_id|source|start_fingerprint|worker_id") fail2("invalid_trusted_worker_identity");
    return value;
  }
  if (!value || Object.getPrototypeOf(value) !== Object.prototype || value.source !== "synthetic_fixture" || value.fixture !== true || !validText2(value.worker_id, 128) || !validText2(value.incarnation, 128) || !Number.isSafeInteger(value.process_id) || value.process_id < 1 || !validText2(value.start_fingerprint, 256) || Object.keys(value).sort().join("|") !== "fixture|incarnation|process_id|source|start_fingerprint|worker_id") fail2("invalid_synthetic_worker_identity");
  return value;
}
function validLaunchRequest(x) {
  return validId(x?.operation_id) && validId(x?.task_id) && Number.isInteger(x?.attempt) && x.attempt > 0 && Number.isInteger(x?.generation) && x.generation > 0 && Number.isInteger(x?.revision) && x.revision > 0 && validId(x?.launch_id) && Number.isInteger(x?.launch_epoch) && x.launch_epoch > 0 && typeof x?.launch_token === "string" && Buffer.byteLength(x.launch_token, "utf8") >= 16 && Buffer.byteLength(x.launch_token, "utf8") <= 4096;
}
function validCleanupRequest(x) {
  return validId(x?.operation_id) && validId(x?.task_id) && Number.isSafeInteger(x?.attempt) && x.attempt > 0 && Number.isSafeInteger(x?.generation) && x.generation > 0 && Number.isSafeInteger(x?.revision) && x.revision > 0 && validId(x?.claim_id) && typeof x?.claim_worker_identity_digest === "string" && /^[0-9a-f]{64}$/u.test(x.claim_worker_identity_digest);
}
function validCancellationFence(x) {
  return !!x && Object.getPrototypeOf(x) === Object.prototype && Object.keys(x).sort().join("|") === "attempt|claim_id|claim_worker_identity_digest|generation|operation_id|revision|task_id|worker_identity" && validId(x.operation_id) && validId(x.task_id) && Number.isSafeInteger(x.attempt) && x.attempt > 0 && Number.isSafeInteger(x.generation) && x.generation > 0 && Number.isSafeInteger(x.revision) && x.revision > 0 && validId(x.claim_id) && typeof x.claim_worker_identity_digest === "string" && /^[0-9a-f]{64}$/u.test(x.claim_worker_identity_digest);
}
function validAdapterCleanupEvidence(value) {
  const scanStatuses = /* @__PURE__ */ new Set(["verified", "live", "incomplete", "not_applicable"]);
  const stages = /* @__PURE__ */ new Set(["not_started", "direct_close", "official_manager_dispose", "official_manager_dispose_all", "official_manager_workspace_dispose"]);
  if (!value || Object.getPrototypeOf(value) !== Object.prototype) return false;
  const close = value.close;
  if (!close || Object.getPrototypeOf(close) !== Object.prototype) return false;
  const evidenceKeys = ["close", "contract", "treeScanStatus"];
  const closeKeys = ["stage", "status", "treeScanStatus"];
  if (close.errorCode !== void 0) closeKeys.push("errorCode");
  if (close.errorName !== void 0) closeKeys.push("errorName");
  if (close.managerProcessCountAfter !== void 0) closeKeys.push("managerProcessCountAfter");
  return Object.keys(value).sort().join("|") === evidenceKeys.sort().join("|") && Object.keys(close).sort().join("|") === closeKeys.sort().join("|") && value.contract === "adapter-cleanup-v1" && ["resolved", "rejected"].includes(close.status) && typeof close.stage === "string" && stages.has(close.stage) && scanStatuses.has(close.treeScanStatus) && scanStatuses.has(value.treeScanStatus) && (close.errorName === void 0 || /^[A-Za-z][A-Za-z0-9_.:-]{0,119}$/u.test(close.errorName)) && (close.errorCode === void 0 || /^[A-Za-z][A-Za-z0-9_.:-]{0,119}$/u.test(close.errorCode)) && (close.managerProcessCountAfter === void 0 || Number.isSafeInteger(close.managerProcessCountAfter) && close.managerProcessCountAfter >= 0) && (!close.stage.startsWith("official_") || Number.isSafeInteger(close.managerProcessCountAfter));
}
function validVerifiedAdapterCleanupEvidence(value) {
  return validAdapterCleanupEvidence(value) && value.close.status === "resolved" && value.close.treeScanStatus === "verified" && value.treeScanStatus === "verified";
}
function normalizeCleanupEvidence(value, input) {
  const keys = ["attempt", "claim_id", "fixture", "generation", "launch_receipt_digest", "operation_id", "operation_resources_complete", "process_tree_digest", "resources_digest", "result_commit_ref", "root_process_id", "root_start_fingerprint", "source", "task_id", "worker_identity_digest", "worker_tree_complete", "workspace_touched"];
  const expectedKeys = value?.adapter_cleanup === void 0 ? keys : [...keys, "adapter_cleanup"].sort();
  if (!value || Object.getPrototypeOf(value) !== Object.prototype || Object.keys(value).sort().join("|") !== expectedKeys.join("|")) fail2("invalid_cleanup_evidence");
  if (value.adapter_cleanup !== void 0 && !validAdapterCleanupEvidence(value.adapter_cleanup)) fail2("invalid_adapter_cleanup_evidence");
  if (!["manager_os_cleanup_verification", "synthetic_fixture"].includes(value.source) || typeof value.fixture !== "boolean" || value.source === "synthetic_fixture" !== value.fixture || value.operation_id !== input.operation_id || value.task_id !== input.task_id || value.attempt !== input.attempt || value.generation !== input.generation || value.claim_id !== input.claim_id || value.worker_identity_digest !== input.claim_worker_identity_digest || !/^([0-9a-f]{64})$/u.test(value.launch_receipt_digest) || !/^([0-9a-f]{64})$/u.test(value.process_tree_digest) || !/^([0-9a-f]{64})$/u.test(value.resources_digest) || !validId(value.result_commit_ref) || !Number.isSafeInteger(value.root_process_id) || value.root_process_id < 1 || !validText2(value.root_start_fingerprint, 256) || value.worker_tree_complete !== true || value.operation_resources_complete !== true || value.workspace_touched !== false) fail2("invalid_cleanup_evidence");
  if (Buffer.byteLength(canonical3(value), "utf8") > 4096) fail2("cleanup_evidence_too_large");
  return value;
}
function presentOperation(row, adminAbandonment) {
  return {
    ...row,
    ...adminAbandonment ? {
      physical_phase: row.phase,
      phase: "admin_abandoned",
      admin_abandoned: true,
      result_absent: true,
      cleanup_verified: false,
      administrative_release_reason: "cleanup_incomplete",
      admin_abandonment_audit_digest: adminAbandonment.audit_digest,
      admin_abandoned_at: adminAbandonment.abandoned_at
    } : {},
    launch_outcome: row.launch_id === null ? "not_requested" : row.launch_receipt_digest === null ? "unknown_receipt_missing" : "receipt_recorded_process_unverified",
    claim_status: row.claim_id === null ? "not_claimed" : "permanent_claim_recorded"
  };
}
function validIsoInstant(value) {
  return typeof value === "string" && Number.isFinite(Date.parse(value));
}
function validateExecutorWakeInput(input) {
  const inputKeys = input && Object.getPrototypeOf(input) === Object.prototype ? Object.keys(input).sort().join("|") : "";
  if (!input || inputKeys !== EXECUTOR_WAKE_BASE_INPUT_KEYS && inputKeys !== EXECUTOR_WAKE_INPUT_KEYS || !validId(input.operation_id) || !validId(input.task_id) || !Number.isSafeInteger(input.attempt) || input.attempt < 1 || !Number.isSafeInteger(input.generation) || input.generation < 1 || !EXECUTOR_WAKE_STATES.has(input.state) || !validText2(input.reason_code, 128) || ![input.policy_digest, input.authorization_digest, input.delivery_id].every((item) => typeof item === "string" && /^[0-9a-f]{64}$/u.test(item)) || input.thread_id !== null && !validId(input.thread_id) || input.state !== "web_notify" && input.thread_id === null || "queue_message_id" in input && (!validId(input.queue_message_id) || input.state !== "queued") || [input.operation_id, input.task_id, input.reason_code].some((item) => item !== item.normalize("NFC")))
    fail2("invalid_executor_wake_request");
  return input;
}
function validateLateWakeInput(input) {
  const inputKeys = input && Object.getPrototypeOf(input) === Object.prototype ? Object.keys(input).sort().join("|") : "";
  if (!input || inputKeys !== EXECUTOR_WAKE_BASE_INPUT_KEYS && inputKeys !== EXECUTOR_WAKE_INPUT_KEYS || !validId(input.operation_id) || !validId(input.task_id) || !Number.isSafeInteger(input.attempt) || input.attempt < 1 || !Number.isSafeInteger(input.generation) || input.generation < 1 || !LATE_WAKE_STATES.has(input.state) || !validText2(input.reason_code, 128) || ![input.policy_digest, input.authorization_digest, input.delivery_id].every((item) => typeof item === "string" && /^[0-9a-f]{64}$/u.test(item)) || !validId(input.thread_id) || "queue_message_id" in input && (!validId(input.queue_message_id) || input.state !== "queued") || [input.operation_id, input.task_id, input.reason_code].some((item) => item !== item.normalize("NFC")))
    fail2("invalid_late_wake_request");
  return input;
}
function validateAdminAbandonmentInput(input) {
  if (!input || Object.getPrototypeOf(input) !== Object.prototype || Object.keys(input).sort().join("|") !== ADMIN_ABANDONMENT_INPUT_KEYS || !validId(input.operation_id) || !validId(input.task_id) || !Number.isSafeInteger(input.attempt) || input.attempt < 1 || !Number.isSafeInteger(input.generation) || input.generation < 1 || !Number.isSafeInteger(input.revision) || input.revision < 1 || !validId(input.claim_id) || typeof input.claim_worker_identity_digest !== "string" || !/^[0-9a-f]{64}$/u.test(input.claim_worker_identity_digest))
    fail2("invalid_admin_abandonment_request");
  const evidence = input.evidence;
  if (!evidence || Object.getPrototypeOf(evidence) !== Object.prototype || Object.keys(evidence).sort().join("|") !== ADMIN_ABANDONMENT_EVIDENCE_KEYS || !validIsoInstant(evidence.boot_time) || !validIsoInstant(evidence.failed_at) || !validIsoInstant(evidence.observed_at) || !Number.isSafeInteger(evidence.worker_process_id) || evidence.worker_process_id < 1 || !validText2(evidence.worker_start_fingerprint, 256) || typeof evidence.process_inventory_digest !== "string" || !/^[0-9a-f]{64}$/u.test(evidence.process_inventory_digest) || typeof evidence.platform_probe_digest !== "string" || !/^[0-9a-f]{64}$/u.test(evidence.platform_probe_digest) || typeof evidence.claimant_scan_digest !== "string" || !/^[0-9a-f]{64}$/u.test(evidence.claimant_scan_digest) || evidence.hosts_closed !== true || evidence.writer_closed !== true || evidence.worker_exited !== true || evidence.claimant_scan_clean !== true)
    fail2("invalid_admin_abandonment_evidence");
  if (Date.parse(evidence.boot_time) <= Date.parse(evidence.failed_at) || Date.parse(evidence.observed_at) < Date.parse(evidence.boot_time))
    fail2("admin_abandonment_generation_boundary_unverified");
  return input;
}
function validateUserAuthorizedReleaseInput(input) {
  const fields = input && Object.getPrototypeOf(input) === Object.prototype ? Object.keys(input).sort().join("|") : "";
  const validShape = fields === USER_AUTHORIZED_RELEASE_INPUT_KEYS || fields === USER_AUTHORIZED_FORCED_RELEASE_INPUT_KEYS || fields === USER_AUTHORIZED_CLEANUP_RELEASE_INPUT_KEYS || fields === USER_AUTHORIZED_TERMINAL_RELEASE_INPUT_KEYS;
  const commonValid = input && validShape && validId(input.operation_id) && validId(input.task_id) && input.release_reason === "user_authorized_release_unverified" && [input.attempt, input.generation, input.revision].every((value) => Number.isSafeInteger(value) && value >= 1) && (fields !== USER_AUTHORIZED_TERMINAL_RELEASE_INPUT_KEYS || validId(input.cancel_id) === false);
  if (!commonValid) fail2("invalid_user_authorized_release");
  if (fields === USER_AUTHORIZED_RELEASE_INPUT_KEYS && !validId(input.cancel_id))
    fail2("invalid_user_authorized_release");
  if (fields === USER_AUTHORIZED_FORCED_RELEASE_INPUT_KEYS && (input.accept_worker_risk !== true || !validId(input.cancel_id) || !/^[0-9a-f]{64}$/u.test(input.launch_receipt_digest)))
    fail2("invalid_user_authorized_release");
  if (fields === USER_AUTHORIZED_CLEANUP_RELEASE_INPUT_KEYS && (!validId(input.cancel_id) || ![input.cancellation_verification_digest, input.recovery_evidence_digest].every((value) => typeof value === "string" && /^[0-9a-f]{64}$/u.test(value))))
    fail2("invalid_user_authorized_release");
  if (fields === USER_AUTHORIZED_TERMINAL_RELEASE_INPUT_KEYS && (![input.recovery_evidence_digest, input.result_digest, input.worker_identity_digest].every((value) => typeof value === "string" && /^[0-9a-f]{64}$/u.test(value)) || !validId(input.claim_id) || typeof input.result_commit_ref !== "string" || !/^(?:result-)?[0-9a-f]{64}$/u.test(input.result_commit_ref)))
    fail2("invalid_user_authorized_release");
  return input;
}
function isBusy(error) {
  return [5, 6].includes(error?.errcode) || /SQLITE_(BUSY|LOCKED)/u.test(String(error?.code ?? "")) || /database is (busy|locked)/iu.test(String(error?.message ?? ""));
}
function containsNonNfcString(value, depth = 0) {
  if (depth > 32) return true;
  if (typeof value === "string") return value !== value.normalize("NFC");
  if (Array.isArray(value)) return value.length > 256 || value.some((v) => containsNonNfcString(v, depth + 1));
  if (value && Object.getPrototypeOf(value) === Object.prototype) {
    const keys = Object.keys(value);
    return keys.length > 256 || keys.some((k) => k !== k.normalize("NFC") || containsNonNfcString(value[k], depth + 1));
  }
  return false;
}
function validateRecoveryEventBinding(operation, event, evidence, claimSequence) {
  if (!RECOVERY_REASON_CODES.has(evidence.reason_code) || !RECOVERY_SOURCES.has(evidence.evidence_source) || event.event_type !== "observation_recorded" || event.operation_id !== operation.operation_id || event.from_phase !== event.to_phase || !RECOVERY_PHASES.has(event.to_phase) || event.sequence !== evidence.expected_revision + 1 || event.generation !== operation.generation || event.sequence > operation.revision || event.evidence_digest !== digest(event.evidence_json ?? canonical3(evidence)) || evidence.task_id !== operation.task_id || evidence.attempt !== operation.attempt || evidence.claim_id !== operation.claim_id || evidence.worker_identity_digest !== operation.claim_worker_identity_digest || !operation.claim_id || operation.claim_generation !== operation.generation || claimSequence === void 0 || event.sequence <= claimSequence) {
    fail2("recovery_event_binding_mismatch");
  }
  if (event.to_phase === "quarantined" && evidence.classification !== "quarantine") fail2("recovery_classification_downgrade");
  const input = {
    operation_id: operation.operation_id,
    task_id: evidence.task_id,
    attempt: evidence.attempt,
    generation: event.generation,
    expected_revision: evidence.expected_revision,
    claim_id: evidence.claim_id,
    worker_identity_digest: evidence.worker_identity_digest,
    classification: evidence.classification,
    reason_code: evidence.reason_code,
    evidence_source: evidence.evidence_source,
    evidence_digest: evidence.evidence_digest,
    ...Object.hasOwn(evidence, "process_tree_root_observed") || Object.hasOwn(evidence, "process_tree_scan_digest") ? {
      process_tree_root_observed: evidence.process_tree_root_observed,
      process_tree_scan_clean: evidence.process_tree_scan_clean,
      process_tree_scan_digest: evidence.process_tree_scan_digest,
      recovery_disposition: evidence.recovery_disposition
    } : {}
  };
  if (digest(recoveryEnvelope(input)) !== evidence.envelope_digest) fail2("recovery_envelope_digest_mismatch");
  if (evidence.material_digest !== void 0 && recoveryMaterialDigest(operation.operation_id, evidence, event.to_phase) !== evidence.material_digest)
    fail2("recovery_material_digest_mismatch");
}
function parseHistoricalExceptionManifest(sourceManifestJson, sourceManifestDigest) {
  let manifest;
  try {
    manifest = JSON.parse(sourceManifestJson);
  } catch {
    fail2("invalid_source_manifest");
  }
  if (!manifest || Object.getPrototypeOf(manifest) !== Object.prototype || typeof sourceManifestDigest !== "string" || digest(sourceManifestJson) !== sourceManifestDigest || !Array.isArray(manifest.files)) fail2("invalid_source_manifest");
  const exceptions = manifest.historical_exceptions;
  if (!Array.isArray(exceptions) || exceptions.length !== 0 && !isCanonicalHistoricalResultExceptionSet(exceptions) || manifest.historical_exception_count !== exceptions.length || manifest.historical_exception_digest !== historicalResultExceptionSetDigest(exceptions)) fail2("invalid_historical_exception_policy");
  return { manifest, exceptions, exceptionTaskIds: historicalResultExceptionTaskIds(exceptions) };
}
function parseAuthoritySourceManifest(sourceManifestJson, sourceManifestDigest) {
  const parsed = parseHistoricalExceptionManifest(sourceManifestJson, sourceManifestDigest);
  const { manifest } = parsed;
  if (manifest.kind === void 0) return { ...parsed, kind: "historical_projection" };
  if (manifest.kind !== "raw_json_archive_cutover" || typeof manifest.source_tasks_root !== "string" || !path.isAbsolute(manifest.source_tasks_root) || typeof manifest.archive_manifest_digest !== "string" || !/^[0-9a-f]{64}$/u.test(manifest.archive_manifest_digest) || typeof manifest.source_files_digest !== "string" || !/^[0-9a-f]{64}$/u.test(manifest.source_files_digest) || manifest.task_count !== 0 || manifest.result_count !== 0 || manifest.event_count !== 0 || !Number.isSafeInteger(manifest.artifact_count) || manifest.artifact_count < 0 || !Number.isSafeInteger(manifest.artifact_bytes) || manifest.artifact_bytes < 0 || !Number.isSafeInteger(manifest.archive_file_count) || manifest.archive_file_count !== manifest.artifact_count || !Number.isSafeInteger(manifest.archive_byte_count) || manifest.archive_byte_count !== manifest.artifact_bytes || parsed.exceptions.length !== 0 || !Array.isArray(manifest.files) || manifest.files.length !== 0)
    fail2("invalid_raw_json_archive_cutover_manifest");
  return { ...parsed, kind: "raw_json_archive_cutover" };
}
function pathsFor(root, { databaseFileName = "operations.sqlite3", managedDataDirectory = false, allowCutoverPending = false, allowUnpublishedCutover = false, allowFreshBootstrapPending = false } = {}) {
  if (typeof root !== "string" || !path.isAbsolute(root) || !existsSync(root) || !lstatSync(root).isDirectory() || lstatSync(root).isSymbolicLink()) fail2("invalid_data_root");
  if (typeof databaseFileName !== "string" || !/^[A-Za-z0-9][A-Za-z0-9._-]{0,95}$/u.test(databaseFileName) || databaseFileName === "." || databaseFileName === "..") fail2("invalid_database_file_name");
  const resolved = realpathSync.native(root);
  if (!managedDataDirectory) {
    const relative = path.relative(HERE, resolved);
    if (!relative || relative.startsWith("..") || path.isAbsolute(relative)) fail2("data_root_outside_candidate");
  }
  const db = path.join(resolved, databaseFileName);
  const files = {
    root: resolved,
    db,
    bootstrapPending: `${db}.bootstrap-pending.json`,
    cutoverPending: `${db}.cutover-pending.json`,
    cutoverPublished: `${db}.cutover-published.json`,
    poison: path.join(resolved, "ROOT_POISONED.json"),
    intent: path.join(resolved, "WRITER_INTENT.json")
  };
  for (const file of [files.db, `${files.db}-wal`, `${files.db}-shm`, files.bootstrapPending, files.cutoverPending, files.cutoverPublished, files.poison, files.intent]) {
    try {
      const st = lstatSync(file);
      if (st.isSymbolicLink() || !st.isFile()) fail2("unsafe_root_entry");
    } catch (e) {
      if (e instanceof AdmissionError) throw e;
      if (e?.code !== "ENOENT") fail2("unsafe_root_entry");
    }
  }
  return { ...files, allowBootstrapPending: allowFreshBootstrapPending, allowCutoverPending, allowUnpublishedCutover };
}
function readPublishedCutoverReceipt(file) {
  let value;
  try {
    value = JSON.parse(readFileSync(file, "utf8"));
  } catch {
    fail2("cutover_publication_receipt_unreadable");
  }
  const keys = ["archive", "created_at", "cutover_id", "database_file", "migration_id", "schema_version", "source_manifest_digest", "source_root_digest", "state"];
  const archiveKeys = ["archive_directory", "byte_count", "file_count", "manifest_digest", "source_tasks_root"];
  if (!value || Object.getPrototypeOf(value) !== Object.prototype || Object.keys(value).sort().join("|") !== keys.join("|") || value.schema_version !== 1 || value.state !== "authority_switch_receipt" || !validText2(value.migration_id, 128) || !validText2(value.cutover_id, 128) || typeof value.source_root_digest !== "string" || !/^[0-9a-f]{64}$/u.test(value.source_root_digest) || typeof value.source_manifest_digest !== "string" || !/^[0-9a-f]{64}$/u.test(value.source_manifest_digest) || !validText2(value.database_file, 96) || !validText2(value.created_at, 64) || Number.isNaN(Date.parse(value.created_at)) || !value.archive || Object.getPrototypeOf(value.archive) !== Object.prototype || Object.keys(value.archive).sort().join("|") !== archiveKeys.join("|") || !validText2(value.archive.archive_directory, 32767) || !path.isAbsolute(value.archive.archive_directory) || !validText2(value.archive.source_tasks_root, 32767) || !path.isAbsolute(value.archive.source_tasks_root) || typeof value.archive.manifest_digest !== "string" || !/^[0-9a-f]{64}$/u.test(value.archive.manifest_digest) || !Number.isSafeInteger(value.archive.file_count) || value.archive.file_count < 0 || !Number.isSafeInteger(value.archive.byte_count) || value.archive.byte_count < 0) fail2("cutover_publication_receipt_invalid");
  return value;
}
function assertCutoverPublicationGate(db, paths) {
  const switched = db.prepare("SELECT * FROM authority_switch").all();
  if (switched.length === 0) return;
  if (switched.length !== 1) fail2("authority_receipt_missing_or_ambiguous");
  const pending = existsSync(paths.cutoverPending);
  const published = existsSync(paths.cutoverPublished);
  if (pending && published) fail2("cutover_publication_receipt_ambiguous");
  if (pending) {
    if (!paths.allowCutoverPending) fail2("cutover_publish_pending");
    return;
  }
  if (!published) {
    if (paths.allowUnpublishedCutover) return;
    fail2("cutover_publication_receipt_missing");
  }
  const receipt = switched[0];
  const publication = readPublishedCutoverReceipt(paths.cutoverPublished);
  if (publication.database_file !== path.basename(paths.db) || publication.migration_id !== receipt.migration_id || publication.cutover_id !== receipt.cutover_id || publication.source_root_digest !== receipt.source_root_digest || publication.source_manifest_digest !== receipt.source_manifest_digest || publication.archive.archive_directory !== receipt.archive_directory || publication.archive.manifest_digest !== receipt.archive_manifest_digest || publication.archive.source_tasks_root !== receipt.archive_source_tasks_root || publication.archive.file_count !== receipt.archive_file_count || publication.archive.byte_count !== receipt.archive_byte_count) fail2("cutover_publication_receipt_mismatch");
}
function processStartEvidence(pid) {
  try {
    if (process.platform === "linux") {
      try {
        const stat = readFileSync(`/proc/${pid}/stat`, "utf8");
        const fingerprint = stat.slice(stat.lastIndexOf(")") + 2).split(" ")[19]?.trim();
        return fingerprint ? { state: "live", fingerprint } : { state: "unknown" };
      } catch (e) {
        return e?.code === "ENOENT" ? { state: "absent" } : { state: "unknown" };
      }
    }
    if (process.platform === "darwin") {
      const timeout = pid === process.pid ? 15e3 : 5e3;
      const query = spawnSync("ps", ["-o", "pid=,lstart=", "-p", String(pid)], { encoding: "utf8", timeout, windowsHide: true, shell: false });
      if (query.status !== 0) return { state: "unknown" };
      const row = query.stdout.split(/\r?\n/u).find((line) => line.trim());
      return row ? { state: "live", fingerprint: row.trim().split(/\s+/u).slice(1).join(" ") } : { state: "absent" };
    }
    if (process.platform === "win32") {
      const systemRoot = Object.entries(process.env).find(([key]) => key.toLowerCase() === "systemroot")?.[1];
      const executable = systemRoot ? `${systemRoot}\\System32\\WindowsPowerShell\\v1.0\\powershell.exe` : "powershell.exe";
      const timeout = pid === process.pid ? 15e3 : 5e3;
      const query = spawnSync(executable, [
        "-NoProfile",
        "-NonInteractive",
        "-ExecutionPolicy",
        "Bypass",
        "-Command",
        `$p=$null; try { $p=[System.Diagnostics.Process]::GetProcessById(${pid}); [Console]::Out.Write($p.StartTime.Ticks) } catch [System.ArgumentException] { [Console]::Out.Write('bridge_pid_absent_v1') }`
      ], {
        encoding: "utf8",
        timeout,
        windowsHide: true,
        shell: false
      });
      const output = query.status === 0 ? query.stdout.trim() : "";
      return output === "bridge_pid_absent_v1" ? { state: "absent" } : /^[0-9]+$/u.test(output) ? { state: "live", fingerprint: output } : { state: "unknown" };
    }
  } catch {
    return { state: "unknown" };
  }
  return { state: "unknown" };
}
function createWriterIntentIdentity(probe = processStartEvidence, {
  attempts = SELF_IDENTITY_PROBE_ATTEMPTS,
  retryDelayMs = SELF_IDENTITY_RETRY_MS
} = {}) {
  let cached;
  return function writerIntentIdentity2() {
    if (cached !== void 0) return cached;
    for (let attempt = 0; attempt < attempts; attempt += 1) {
      const evidence = probe(process.pid);
      if (evidence.state === "live") {
        cached = evidence.fingerprint;
        return cached;
      }
      if (attempt + 1 < attempts && retryDelayMs > 0) {
        Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, retryDelayMs);
      }
    }
    return null;
  };
}
function readWriterIntent(file) {
  try {
    const stat = lstatSync(file);
    if (stat.isFile() && !stat.isSymbolicLink() && stat.size <= 65536) return JSON.parse(readFileSync(file, "utf8"));
  } catch {
  }
  return null;
}
function validWriterIntentIdentity(intent) {
  return intent && intent.version === 2 && typeof intent.token === "string" && intent.token.length > 0 && intent.token.length <= 128 && Number.isSafeInteger(intent.process_id) && intent.process_id > 0 && typeof intent.start_fingerprint === "string" && intent.start_fingerprint.length > 0 && intent.start_fingerprint.length <= 256 && intent.identity_version === 1 && intent.platform === process.platform;
}
function retireWriterIntent(paths) {
  const intent = readWriterIntent(paths.intent);
  if (!validWriterIntentIdentity(intent)) return false;
  const evidence = processStartEvidence(intent.process_id);
  if (evidence.state !== "absent") return false;
  const retired = `${paths.intent}.cleared-${intent.token}-${randomUUID()}.json`;
  try {
    renameSync(paths.intent, retired);
    return true;
  } catch {
    return false;
  }
}
function writePoison(file, value) {
  const tmp = `${file}.${randomUUID()}.tmp`;
  const fd = openSync(tmp, "wx", 384);
  try {
    writeFileSync(fd, JSON.stringify(value));
    fsyncSync(fd);
  } finally {
    closeSync(fd);
  }
  try {
    renameSync(tmp, file);
  } catch (error) {
    if (!existsSync(file)) throw error;
    try {
      unlinkSync(tmp);
    } catch {
    }
  }
}
function workspacePathsOverlap(left, right) {
  const a = path.win32.resolve(left).toLowerCase();
  const b = path.win32.resolve(right).toLowerCase();
  const contains = (parent, child) => child === parent || child.startsWith(parent.endsWith("\\") ? parent : `${parent}\\`);
  return contains(a, b) || contains(b, a);
}
function validateInteractionHistory(db, operation, events) {
  const payloads = db.prepare("SELECT * FROM manager_interaction_payloads WHERE operation_id=? ORDER BY request_id").all(operation.operation_id);
  const interactionEvents = events.filter((event) => event.event_type.startsWith("interaction_"));
  if (payloads.length > 128) fail2("interaction_request_limit");
  const grouped = /* @__PURE__ */ new Map();
  for (const event of interactionEvents) {
    let evidence;
    try {
      evidence = JSON.parse(event.evidence_json);
    } catch {
      fail2("interaction_history_mismatch");
    }
    const requestId = evidence.request_id;
    if (!validId(requestId) || event.evidence_digest !== digest(event.evidence_json)) fail2("interaction_history_mismatch");
    const list = grouped.get(requestId) ?? [];
    list.push({ event, evidence });
    grouped.set(requestId, list);
  }
  const seen = /* @__PURE__ */ new Set();
  for (const payload of payloads) {
    if (!validId(payload.request_id) || seen.has(payload.request_id) || payload.task_id !== operation.task_id || payload.attempt !== operation.attempt || payload.generation !== operation.generation || payload.claim_id !== operation.claim_id || payload.worker_identity_digest !== operation.claim_worker_identity_digest || !operation.claim_id || operation.claim_generation !== operation.generation) fail2("interaction_payload_identity_mismatch");
    seen.add(payload.request_id);
    let request;
    try {
      request = JSON.parse(payload.request_json);
    } catch {
      fail2("interaction_history_mismatch");
    }
    if (!validateInteractionRequest(request) || request.request_id !== payload.request_id || request.method !== payload.request_method || interactionCanonical(request) !== payload.request_json || Buffer.byteLength(payload.request_json, "utf8") > 1048576 || payload.request_digest !== interactionDigest({
      interaction_contract_version: 1,
      operation_id: payload.operation_id,
      task_id: payload.task_id,
      attempt: payload.attempt,
      generation: payload.generation,
      claim_id: payload.claim_id,
      worker_identity_digest: payload.worker_identity_digest,
      request
    }))
      fail2("interaction_history_mismatch");
    const rows = grouped.get(payload.request_id) ?? [];
    const requested = rows.filter((row) => row.event.event_type === "interaction_requested");
    const intents = rows.filter((row) => row.event.event_type === "interaction_reply_intent");
    const prepared = rows.filter((row) => row.event.event_type === "interaction_reply_prepared");
    const committed = rows.filter((row) => row.event.event_type === "interaction_reply_committed");
    const accepted = rows.filter((row) => row.event.event_type === "interaction_reply_accepted");
    if (requested.length !== 1 || intents.length > 1 || prepared.length > 1 || committed.length > 1 || accepted.length > 1 || accepted.length && !committed.length || committed.length && !prepared.length || prepared.length && !intents.length || rows.length !== requested.length + intents.length + prepared.length + committed.length + accepted.length) fail2("interaction_history_unbounded");
    const req = requested[0];
    if (req.event.sequence > operation.revision || req.evidence.claim_id !== payload.claim_id || req.evidence.request_digest !== payload.request_digest || req.evidence.request_method !== payload.request_method || req.evidence.worker_identity_digest !== payload.worker_identity_digest || req.event.from_phase !== "running" || req.event.to_phase !== "running" || req.event.generation !== payload.generation) fail2("interaction_request_event_mismatch");
    if (intents.length) {
      const intent = intents[0];
      let answer;
      try {
        answer = JSON.parse(payload.answer_json);
      } catch {
        fail2("interaction_history_mismatch");
      }
      const answerDigest = interactionDigest({
        interaction_reply_contract_version: 1,
        operation_id: payload.operation_id,
        task_id: payload.task_id,
        attempt: payload.attempt,
        generation: payload.generation,
        claim_id: payload.claim_id,
        worker_identity_digest: payload.worker_identity_digest,
        request_id: payload.request_id,
        answer
      });
      if (intent.event.sequence <= req.event.sequence || intent.evidence.claim_id !== payload.claim_id || intent.evidence.worker_identity_digest !== payload.worker_identity_digest || intent.evidence.reply_id !== payload.reply_id || intent.evidence.answer_digest !== payload.answer_digest || payload.answer_digest !== answerDigest || interactionCanonical(answer) !== payload.answer_json || !validPersistedInteractionAnswer(request, answer)) fail2("interaction_reply_intent_mismatch");
      if (prepared.length) {
        const prep = prepared[0];
        if (prep.event.sequence !== intent.event.sequence + 1 || prep.evidence.claim_id !== payload.claim_id || prep.evidence.worker_identity_digest !== payload.worker_identity_digest || prep.evidence.reply_id !== payload.reply_id || prep.evidence.answer_digest !== payload.answer_digest || !/^[0-9a-f]{64}$/u.test(prep.evidence.prepared_digest)) fail2("interaction_reply_prepared_mismatch");
      }
      if (committed.length) {
        const commit = committed[0], prep = prepared[0];
        if (!prep || commit.event.sequence !== prep.event.sequence + 1 || commit.evidence.claim_id !== payload.claim_id || commit.evidence.worker_identity_digest !== payload.worker_identity_digest || commit.evidence.reply_id !== payload.reply_id || commit.evidence.answer_digest !== payload.answer_digest || commit.evidence.prepared_digest !== prep.evidence.prepared_digest || commit.evidence.commit_digest !== interactionCommitDigest(
          {
            operation_id: operation.operation_id,
            task_id: operation.task_id,
            attempt: operation.attempt,
            generation: operation.generation,
            claim_id: payload.claim_id,
            worker_identity_digest: payload.worker_identity_digest
          },
          {
            request_id: payload.request_id,
            reply_id: payload.reply_id,
            revision: commit.event.sequence,
            answer_digest: payload.answer_digest,
            prepared_digest: prep.evidence.prepared_digest
          }
        )) fail2("interaction_reply_commit_mismatch");
      }
      if (accepted.length) {
        const ack = accepted[0];
        if (!committed.length || ack.event.sequence !== committed[0].event.sequence + 1 || ack.evidence.claim_id !== payload.claim_id || ack.evidence.worker_identity_digest !== payload.worker_identity_digest || ack.evidence.reply_id !== payload.reply_id || ack.evidence.answer_digest !== payload.answer_digest || ack.evidence.commit_digest !== committed[0].evidence.commit_digest || !/^([0-9a-f]{64})$/u.test(ack.evidence.ack_digest)) fail2("interaction_reply_acceptance_mismatch");
      } else if (!["running", "quarantined"].includes(operation.phase)) fail2("interaction_reply_outcome_unknown");
    } else if (payload.answer_json !== null || payload.answer_digest !== null || payload.reply_id !== null) fail2("interaction_payload_reply_without_intent");
  }
  for (const requestId of grouped.keys()) if (!seen.has(requestId)) fail2("interaction_event_without_payload");
  if (hasUnresolvedInteraction(events) && !["running", "quarantined"].includes(operation.phase)) fail2("interaction_reply_outcome_unknown");
}
function hasUnresolvedInteraction(events) {
  const pending = /* @__PURE__ */ new Set();
  for (const event of events) {
    if (event.event_type !== "interaction_reply_intent" && event.event_type !== "interaction_reply_accepted") continue;
    let evidence;
    try {
      evidence = JSON.parse(event.evidence_json);
    } catch {
      return true;
    }
    if (event.event_type === "interaction_reply_intent") pending.add(evidence.request_id);
    else pending.delete(evidence.request_id);
  }
  return pending.size > 0;
}
function validateInteractionRequest(value) {
  return !!value && Object.getPrototypeOf(value) === Object.prototype && Object.keys(value).sort().join("|") === "method|params|request_id" && validId(value.request_id) && value.request_id.length <= 512 && ["interaction/requestPermission", "interaction/requestUserInput"].includes(value.method) && !!value.params && Object.getPrototypeOf(value.params) === Object.prototype && validInteractionJson(value);
}
function validInteractionJson(value) {
  try {
    interactionCanonical(value);
    return true;
  } catch {
    return false;
  }
}
function interactionCanonical(value, depth = 0) {
  if (depth > 32) fail2("interaction_json_too_deep");
  if (value === null || typeof value === "string" || typeof value === "boolean") return JSON.stringify(value);
  if (typeof value === "number" && Number.isFinite(value)) return JSON.stringify(value);
  if (Array.isArray(value)) {
    if (value.length > 256) fail2("interaction_json_too_large");
    return `[${value.map((item) => interactionCanonical(item, depth + 1)).join(",")}]`;
  }
  if (value && Object.getPrototypeOf(value) === Object.prototype) {
    const keys = Object.keys(value);
    if (keys.length > 256 || keys.some((key) => key !== key.normalize("NFC"))) fail2("interaction_json_invalid");
    return `{${keys.sort().map((key) => `${JSON.stringify(key)}:${interactionCanonical(value[key], depth + 1)}`).join(",")}}`;
  }
  fail2("interaction_json_invalid");
}
function interactionDigest(value) {
  return digest(interactionCanonical(value));
}
function interactionCommitDigest(binding, commit) {
  return interactionDigest({
    interaction_commit_contract_version: 1,
    operation_id: binding.operation_id,
    task_id: binding.task_id,
    attempt: binding.attempt,
    generation: binding.generation,
    claim_id: binding.claim_id,
    worker_identity_digest: binding.worker_identity_digest,
    request_id: commit.request_id,
    reply_id: commit.reply_id,
    revision: commit.revision,
    answer_digest: commit.answer_digest,
    prepared_digest: commit.prepared_digest
  });
}
function validInteractionFence(value) {
  return !!value && Object.getPrototypeOf(value) === Object.prototype && Object.keys(value).sort().join("|") === "attempt|claim_id|expected_revision|generation|operation_id|request|task_id|worker_identity_digest" && validId(value.operation_id) && validId(value.task_id) && Number.isSafeInteger(value.attempt) && value.attempt > 0 && Number.isSafeInteger(value.generation) && value.generation > 0 && Number.isSafeInteger(value.expected_revision) && value.expected_revision > 0 && validId(value.claim_id) && typeof value.worker_identity_digest === "string" && /^[0-9a-f]{64}$/u.test(value.worker_identity_digest);
}
function validInteractionReplyInput(value) {
  if (!value || Object.getPrototypeOf(value) !== Object.prototype || !["answers", "decision", "reason", "request_id", "task_id"].every((key) => Object.hasOwn(value, key) ? true : ["answers", "reason"].includes(key)) || Object.keys(value).some((key) => !["task_id", "request_id", "decision", "answers", "reason"].includes(key)) || !validId(value.task_id) || !validId(value.request_id) || value.request_id.length > 512 || !["allow", "deny", "accept", "decline"].includes(value.decision) || "reason" in value && typeof value.reason !== "string" || "answers" in value && (!value.answers || Object.getPrototypeOf(value.answers) !== Object.prototype || Object.values(value.answers).some((answer) => typeof answer !== "string"))) return false;
  return true;
}
function buildInteractionAnswer(request, input) {
  const params = request.params;
  if (request.method === "interaction/requestPermission") {
    if (!["allow", "deny"].includes(input.decision)) fail2("invalid_interaction_decision");
    if (input.decision === "allow" && !(Array.isArray(params.options) && params.options.some((option) => option && Object.getPrototypeOf(option) === Object.prototype && typeof option.kind === "string" && option.kind.startsWith("allow")))) fail2("interaction_allow_not_offered");
    return input.decision === "allow" ? { decision: "allow" } : { decision: "deny", reason: (input.reason?.trim() || "the calling host declined this request").slice(0, 2e3) };
  }
  if (!["accept", "decline"].includes(input.decision)) fail2("invalid_interaction_decision");
  if (input.decision === "decline") return { action: "decline" };
  if (params.schema && Object.getPrototypeOf(params.schema) === Object.prototype && params.schema.interaction === "plan_approval") return { action: "accept", content: { answer_0: "approve" } };
  const nested = params.input && Object.getPrototypeOf(params.input) === Object.prototype ? params.input : {};
  const raw = Array.isArray(params.questions) ? params.questions : Array.isArray(nested.questions) ? nested.questions : [];
  const questions = raw.filter((question) => question && Object.getPrototypeOf(question) === Object.prototype && typeof question.question === "string").map((question) => question.question);
  if (!questions.length) fail2("interaction_questions_missing");
  const answers = input.answers ?? {};
  const keys = Object.keys(answers);
  if (!keys.length || keys.some((key) => !questions.includes(key))) fail2("interaction_answer_question_mismatch");
  for (const [question, answer] of Object.entries(answers)) if (!answer.trim() || answer.length > 4e3) fail2("invalid_interaction_answer");
  if (Buffer.byteLength(JSON.stringify(answers), "utf8") > 16e3) fail2("interaction_answers_too_large");
  return { action: "accept", content: { answers } };
}
function validPersistedInteractionAnswer(request, answer) {
  if (!answer || Object.getPrototypeOf(answer) !== Object.prototype) return false;
  if (request.method === "interaction/requestPermission") {
    const keys = Object.keys(answer).sort().join("|");
    if (answer.decision === "allow") return keys === "decision" && Array.isArray(request.params.options) && request.params.options.some((option) => option && Object.getPrototypeOf(option) === Object.prototype && typeof option.kind === "string" && option.kind.startsWith("allow"));
    return answer.decision === "deny" && keys === "decision|reason" && typeof answer.reason === "string" && answer.reason.length <= 2e3;
  }
  if (answer.action === "decline") return Object.keys(answer).join("|") === "action";
  if (answer.action !== "accept" || Object.keys(answer).sort().join("|") !== "action|content" || !answer.content || Object.getPrototypeOf(answer.content) !== Object.prototype) return false;
  if (request.params.schema && Object.getPrototypeOf(request.params.schema) === Object.prototype && request.params.schema.interaction === "plan_approval")
    return Object.keys(answer.content).join("|") === "answer_0" && answer.content.answer_0 === "approve";
  if (Object.keys(answer.content).join("|") !== "answers" || !answer.content.answers || Object.getPrototypeOf(answer.content.answers) !== Object.prototype) return false;
  const nested = request.params.input && Object.getPrototypeOf(request.params.input) === Object.prototype ? request.params.input : {};
  const raw = Array.isArray(request.params.questions) ? request.params.questions : Array.isArray(nested.questions) ? nested.questions : [];
  const questions = raw.filter((question) => question && Object.getPrototypeOf(question) === Object.prototype && typeof question.question === "string").map((question) => question.question);
  const entries = Object.entries(answer.content.answers);
  return entries.length > 0 && entries.every(([key, value]) => questions.includes(key) && typeof value === "string" && !!value.trim() && value.length <= 4e3) && Buffer.byteLength(JSON.stringify(answer.content.answers), "utf8") <= 16e3;
}
function validInteractionAcknowledgement(value) {
  const keys = ["ack_digest", "answer_digest", "attempt", "claim_id", "commit_digest", "generation", "operation_id", "process_id", "reply_id", "request_id", "revision", "start_fingerprint", "task_id", "worker_identity_digest"];
  return Object.getPrototypeOf(value) === Object.prototype && Object.keys(value).sort().join("|") === keys.sort().join("|") && validId(value.operation_id) && validId(value.task_id) && validId(value.claim_id) && validId(value.request_id) && validId(value.reply_id) && Number.isSafeInteger(value.attempt) && value.attempt > 0 && Number.isSafeInteger(value.generation) && value.generation > 0 && Number.isSafeInteger(value.revision) && value.revision > 0 && Number.isSafeInteger(value.process_id) && value.process_id > 0 && validText2(value.start_fingerprint, 256) && [value.worker_identity_digest, value.answer_digest, value.commit_digest, value.ack_digest].every((item) => typeof item === "string" && /^[0-9a-f]{64}$/u.test(item));
}
function validInteractionPreparedAcknowledgement(value) {
  const keys = ["ack_digest", "answer_digest", "attempt", "claim_id", "generation", "operation_id", "process_id", "reply_id", "request_id", "revision", "start_fingerprint", "task_id", "worker_identity_digest"];
  return Object.getPrototypeOf(value) === Object.prototype && Object.keys(value).sort().join("|") === keys.sort().join("|") && validId(value.operation_id) && validId(value.task_id) && validId(value.claim_id) && validId(value.request_id) && validId(value.reply_id) && Number.isSafeInteger(value.attempt) && value.attempt > 0 && Number.isSafeInteger(value.generation) && value.generation > 0 && Number.isSafeInteger(value.revision) && value.revision > 0 && Number.isSafeInteger(value.process_id) && value.process_id > 0 && validText2(value.start_fingerprint, 256) && [value.worker_identity_digest, value.answer_digest, value.ack_digest].every((item) => typeof item === "string" && /^[0-9a-f]{64}$/u.test(item));
}
function validId(v) {
  return typeof v === "string" && v.length > 0 && v.length <= 128 && !/[\x00-\x1f]/u.test(v);
}
function normalizeTaskAdmission(value) {
  if (value === void 0 || value === null) {
    return { owner_thread_id: null, binding_source: "non_host_admission" };
  }
  if (!value || Object.getPrototypeOf(value) !== Object.prototype) return { owner_thread_id: null, binding_source: "mcp_meta_invalid" };
  const ownerThreadId = value.owner_thread_id ?? null;
  if (ownerThreadId === null) {
    const source = value.source === "mcp_meta_missing" || value.source === "mcp_meta_invalid" ? value.source : "non_host_admission";
    return { owner_thread_id: null, binding_source: source };
  }
  if (!validId(ownerThreadId) || ownerThreadId !== ownerThreadId.trim() || ownerThreadId !== ownerThreadId.normalize("NFC")) return { owner_thread_id: null, binding_source: "mcp_meta_invalid" };
  if (value.source !== "mcp_meta") return { owner_thread_id: null, binding_source: "mcp_meta_invalid" };
  return { owner_thread_id: ownerThreadId, binding_source: "mcp_meta" };
}
function ownerBindingProjection(taskId, admission, boundAt) {
  return {
    task_id: taskId,
    state: admission.owner_thread_id === null ? "unavailable" : "bound",
    owner_thread_id: admission.owner_thread_id,
    source: admission.binding_source,
    bound_at: boundAt,
    reason_code: admission.owner_thread_id === null ? "owner_thread_unavailable" : null
  };
}
function validateTaskPackage(task) {
  if (!task || Object.getPrototypeOf(task) !== Object.prototype || !validId(task.task_id) || typeof task.workspace !== "string" || !task.workspace || typeof task.objective !== "string" || !["requirements", "allowed_paths", "forbidden_paths", "acceptance_criteria", "test_commands"].every((k) => Array.isArray(task[k]) && task[k].every((v) => typeof v === "string")) || task.worktree_path !== void 0 && typeof task.worktree_path !== "string" || task.context !== void 0 && typeof task.context !== "string" || task.timeout_ms !== void 0 && (!Number.isSafeInteger(task.timeout_ms) || task.timeout_ms < 6e4 || task.timeout_ms > 144e5) || task.model !== void 0 && (!task.model || Object.getPrototypeOf(task.model) !== Object.prototype || typeof task.model.provider_id !== "string" || !task.model.provider_id || typeof task.model.model_id !== "string" || !task.model.model_id))
    fail2("invalid_task_package");
  const json = canonical3(task);
  if (Buffer.byteLength(json, "utf8") > 1048576) fail2("task_package_too_large");
  return task;
}
function validateWorkspace(input, validator) {
  if (typeof input !== "string" || !input.trim()) fail2("workspace_missing");
  if (!path.isAbsolute(input)) fail2("workspace_not_absolute");
  if (input.replace(/\//g, "\\").startsWith("\\\\")) fail2("workspace_unsupported_path_form");
  let st, canonicalPath;
  try {
    st = statSync(input);
    canonicalPath = realpathSync(input);
  } catch {
    fail2("workspace_unavailable");
  }
  if (!st.isDirectory()) fail2("workspace_not_directory");
  if (!validator) fail2("workspace_validator_missing");
  let result;
  try {
    result = validator({ requestedPath: input, canonicalPath });
  } catch {
    fail2("workspace_validation_unknown");
  }
  if (result === "deny" || result?.state === "deny") fail2("workspace_validation_denied");
  if (result !== "allow" && result?.state !== "allow") fail2("workspace_validation_unknown");
  return canonicalPath;
}
function callDecision(fn, workspace, input) {
  if (typeof fn !== "function") fail2("execution_permission_unknown");
  try {
    const r = fn({ workspace, task: input });
    const state = r === "allow" || r?.state === "allow" ? "allow" : r === "deny" || r?.state === "deny" ? "deny" : "unknown";
    if (state !== "allow") return { state };
    if (r?.source === "trusted_local_policy") return { state, audit: { authorization_source: r.source, policy_revision: r.policy_revision, execution_profile_id: r.execution_profile_id, policy_digest: r.policy_digest } };
    return { state };
  } catch {
    return { state: "unknown" };
  }
}
var HERE, SCHEMA, RUNTIME_EVENTS_SCHEMA, ADMIN_ABANDONMENT_SCHEMA, NORMALIZED_ADMIN_ABANDONMENT_SCHEMA, LEGACY_ADMIN_ABANDONMENT_SCHEMA, CONSTRUCT, SCHEMA_VERSION, SCHEMA_OBJECT_QUERY, RUNTIME_EVENT_SCHEMA_OBJECTS, OWNER_BINDING_SCHEMA_OBJECTS, expectedSchemas, expectedRecoveryBindingTriggerSql, ADMIN_ABANDONMENT_TABLE_SQL, LEGACY_ADMIN_ABANDONMENT_TABLE_SQL, NORMALIZED_ADMIN_ABANDONMENT_TABLE_SQL, NORMALIZED_LEGACY_ADMIN_ABANDONMENT_TABLE_SQL, SQLITE_V14_ONLY_MESSAGE, V13_UPGRADE_MARKER_MESSAGE, v13UpgradeMarker, RESULT_CONTRACT_VERSION, RESULT_STATUSES2, RECOVERY_PHASES, RECOVERY_SOURCES, RECOVERY_REASON_CODES, RECOVERY_QUARANTINE_CODES, RECOVERY_EVIDENCE_KEYS, RECOVERY_RELEASE_EVIDENCE_KEYS, EXECUTOR_WAKE_BASE_EVIDENCE_KEYS, EXECUTOR_WAKE_EVIDENCE_KEYS, EXECUTOR_WAKE_STATES, EXECUTOR_WAKE_LIMIT, LATE_WAKE_REASON, LATE_WAKE_STATES, LATE_WAKE_LIMIT, RECOVERY_MATERIAL_BINDING_KEYS, RECOVERY_MATERIAL_DETAIL_KEYS, RESOLVED_RECOVERY_SET_CONTRACT, RECOVERY_MATERIAL_CONTRACT, digest, rawDigest, sortedDigests, upgradeRowJson, EVIDENCE_KEYS, FUTURE_EVENT_TYPES, FUTURE_EVIDENCE_KEYS, EVENT_PHASE, RECOVERY_INPUT_KEYS, RECOVERY_RELEASE_INPUT_KEYS, ADMIN_ABANDONMENT_INPUT_KEYS, ADMIN_ABANDONMENT_EVIDENCE_KEYS, USER_AUTHORIZED_RELEASE_INPUT_KEYS, USER_AUTHORIZED_FORCED_RELEASE_INPUT_KEYS, USER_AUTHORIZED_CLEANUP_RELEASE_INPUT_KEYS, EXECUTOR_WAKE_BASE_INPUT_KEYS, EXECUTOR_WAKE_INPUT_KEYS, USER_AUTHORIZED_TERMINAL_RELEASE_INPUT_KEYS, AdmissionError, fail2, SELF_IDENTITY_PROBE_ATTEMPTS, SELF_IDENTITY_RETRY_MS, writerIntentIdentity, IsolatedAdmissionStore;
var init_store = __esm({
  "src/sqlite-candidate/wp6b2b1/store.mjs"() {
    "use strict";
    init_result_contract();
    init_interaction_channel();
    init_json_history_result_exceptions();
    init_task_feedback_projection();
    HERE = path.dirname(fileURLToPath(import.meta.url));
    SCHEMA = readFileSync(new URL("./schema.sql", import.meta.url), "utf8");
    RUNTIME_EVENTS_SCHEMA = readFileSync(new URL("./runtime-events.sql", import.meta.url), "utf8");
    ADMIN_ABANDONMENT_SCHEMA = readFileSync(new URL("./admin-abandonment.sql", import.meta.url), "utf8");
    NORMALIZED_ADMIN_ABANDONMENT_SCHEMA = ADMIN_ABANDONMENT_SCHEMA.replace(/\r\n?/gu, "\n");
    LEGACY_ADMIN_ABANDONMENT_SCHEMA = NORMALIZED_ADMIN_ABANDONMENT_SCHEMA.replace(
      "event_sequence INTEGER NOT NULL CHECK(event_sequence=original_revision+1)",
      "event_sequence INTEGER NOT NULL UNIQUE CHECK(event_sequence=original_revision+1)"
    );
    if (LEGACY_ADMIN_ABANDONMENT_SCHEMA === NORMALIZED_ADMIN_ABANDONMENT_SCHEMA) {
      throw new Error("administrative abandonment schema compatibility marker is missing");
    }
    CONSTRUCT = /* @__PURE__ */ Symbol("construct");
    SCHEMA_VERSION = 14;
    SCHEMA_OBJECT_QUERY = "SELECT type,name,tbl_name,sql FROM sqlite_schema WHERE type IN ('table','view','index','trigger') AND substr(lower(name),1,7)<>'sqlite_' ORDER BY type COLLATE BINARY,name COLLATE BINARY";
    RUNTIME_EVENT_SCHEMA_OBJECTS = /* @__PURE__ */ new Set([
      "runtime_task_events",
      "runtime_task_events_task_cursor",
      "runtime_task_events_no_update",
      "runtime_task_events_no_delete",
      "runtime_task_events_identity_guard"
    ]);
    OWNER_BINDING_SCHEMA_OBJECTS = /* @__PURE__ */ new Set([
      "task_owner_bindings",
      "task_owner_bindings_thread",
      "task_owner_bindings_no_update",
      "task_owner_bindings_no_delete"
    ]);
    expectedSchemas = /* @__PURE__ */ new Map();
    ADMIN_ABANDONMENT_TABLE_SQL = adminAbandonmentTableStatement(ADMIN_ABANDONMENT_SCHEMA);
    LEGACY_ADMIN_ABANDONMENT_TABLE_SQL = adminAbandonmentTableStatement(LEGACY_ADMIN_ABANDONMENT_SCHEMA);
    NORMALIZED_ADMIN_ABANDONMENT_TABLE_SQL = normalizeAdminAbandonmentTableSql(ADMIN_ABANDONMENT_TABLE_SQL);
    NORMALIZED_LEGACY_ADMIN_ABANDONMENT_TABLE_SQL = normalizeAdminAbandonmentTableSql(LEGACY_ADMIN_ABANDONMENT_TABLE_SQL);
    SQLITE_V14_ONLY_MESSAGE = "SQLite v14 ONLY: schema version 13 is not supported; the database was not modified";
    V13_UPGRADE_MARKER_MESSAGE = "SQLite v14 ONLY: an interrupted v13 upgrade marker is present; preserve the root for diagnosis";
    v13UpgradeMarker = (databasePath) => `${databasePath}.v13-v14-pending.json`;
    RESULT_CONTRACT_VERSION = 1;
    RESULT_STATUSES2 = /* @__PURE__ */ new Set(["completed", "failed", "cancelled", "waiting_for_master"]);
    RECOVERY_PHASES = /* @__PURE__ */ new Set(["running", "result_committed", "cleanup_pending", "cleanup_verified", "cleanup_unverified", "cleanup_reverified", "quarantined"]);
    RECOVERY_SOURCES = /* @__PURE__ */ new Set(["manager_process_probe", "manager_launch_probe", "manager_cleanup_probe", "manager_projection_validator"]);
    RECOVERY_REASON_CODES = /* @__PURE__ */ new Set(["worker_identity_unknown", "launch_outcome_unknown", "cleanup_identity_unknown", "cleanup_incomplete", "claim_identity_conflict", "operation_projection_conflict"]);
    RECOVERY_QUARANTINE_CODES = /* @__PURE__ */ new Set(["claim_identity_conflict", "operation_projection_conflict"]);
    RECOVERY_EVIDENCE_KEYS = Object.freeze(["attempt", "claim_id", "classification", "envelope_digest", "evidence_digest", "evidence_source", "expected_revision", "reason", "reason_code", "task_id", "worker_identity_digest"]);
    RECOVERY_RELEASE_EVIDENCE_KEYS = Object.freeze([...RECOVERY_EVIDENCE_KEYS, "process_tree_root_observed", "process_tree_scan_clean", "process_tree_scan_digest", "recovery_disposition"]);
    EXECUTOR_WAKE_BASE_EVIDENCE_KEYS = Object.freeze([
      "attempt",
      "authorization_digest",
      "delivery_id",
      "evidence_digest",
      "generation",
      "operation_id",
      "policy_digest",
      "reason",
      "reason_code",
      "result_commit_ref",
      "result_digest",
      "state",
      "task_id",
      "thread_id"
    ]);
    EXECUTOR_WAKE_EVIDENCE_KEYS = Object.freeze([...EXECUTOR_WAKE_BASE_EVIDENCE_KEYS, "queue_message_id"].sort());
    EXECUTOR_WAKE_STATES = /* @__PURE__ */ new Set(["intent", "queued", "submission_unknown", "turn_started", "web_notify"]);
    EXECUTOR_WAKE_LIMIT = 5;
    LATE_WAKE_REASON = "executor_late_wake_compensation";
    LATE_WAKE_STATES = /* @__PURE__ */ new Set(["intent", "queued", "submission_unknown", "turn_started", "web_notify"]);
    LATE_WAKE_LIMIT = 5;
    RECOVERY_MATERIAL_BINDING_KEYS = Object.freeze(["attempt", "claim_id", "classification", "evidence_source", "reason_code", "task_id", "worker_identity_digest"]);
    RECOVERY_MATERIAL_DETAIL_KEYS = Object.freeze([
      "complete_cleanup_closure",
      "identity_state",
      "phase",
      "probe_reason",
      "process_id",
      "process_tree_root_observed",
      "process_tree_scan_clean",
      "process_tree_scan_digest",
      "process_tree_scan_scope",
      "recovery_disposition",
      "start_fingerprint"
    ]);
    RESOLVED_RECOVERY_SET_CONTRACT = "wp6c-resolved-recovery-set-v2";
    RECOVERY_MATERIAL_CONTRACT = "wp6c-recovery-material-v1";
    digest = (value) => createHash2("sha256").update(typeof value === "string" ? value : canonical3(value)).digest("hex");
    rawDigest = (value) => createHash2("sha256").update(Buffer.from(value)).digest("hex");
    sortedDigests = (values) => [...values].sort();
    upgradeRowJson = (row) => canonical3(Object.fromEntries(Object.entries(row).map(([key, value]) => [
      key,
      value instanceof Uint8Array ? { sqlite_type: "blob", bytes: value.byteLength, sha256: createHash2("sha256").update(value).digest("hex") } : value
    ])));
    EVIDENCE_KEYS = Object.freeze({
      capacity_policy_committed: ["capacity_limit", "generation"],
      reserved: ["capacity_slot", "reservation_id"],
      cancelled_before_launch: ["cancel_id", "request_digest"],
      observation_recorded: ["evidence_digest", "reason"],
      launch_intent: ["launch_epoch", "launch_id", "token_digest"],
      launch_receipt: ["launch_epoch", "launch_id", "receipt_digest", "token_digest"],
      claim_committed: ["claim_id", "launch_epoch", "launch_id", "token_digest", "worker_identity_digest"],
      result_committed: ["claim_id", "outcome", "result_commit_ref", "result_digest", "worker_identity_digest"],
      cleanup_pending: ["claim_id", "result_commit_ref", "worker_identity_digest"],
      cleanup_verified: ["adapter_cleanup", "claim_id", "cleanup_digest", "evidence_source", "launch_receipt_digest", "operation_resources_complete", "process_tree_digest", "resources_digest", "result_commit_ref", "root_process_id", "root_start_fingerprint", "worker_identity_digest", "worker_tree_complete", "workspace_touched"],
      cleanup_unverified: ["claim_id", "probe_state", "reason", "worker_identity_digest"],
      cleanup_reverified: ["adapter_cleanup", "attempt", "claim_id", "cleanup_digest", "evidence_source", "generation", "launch_receipt_digest", "operation_id", "operation_resources_complete", "prior_cleanup_event_digest", "process_tree_digest", "resources_digest", "result_commit_ref", "root_process_id", "root_start_fingerprint", "task_id", "worker_identity_digest", "worker_tree_complete", "workspace_touched"],
      released: ["claim_id", "cleanup_digest", "result_commit_ref", "worker_identity_digest"],
      interaction_requested: ["claim_id", "request_digest", "request_id", "request_method", "worker_identity_digest"],
      interaction_reply_intent: ["answer_digest", "claim_id", "reply_id", "request_id", "worker_identity_digest"],
      interaction_reply_prepared: ["answer_digest", "claim_id", "prepared_digest", "reply_id", "request_id", "worker_identity_digest"],
      interaction_reply_committed: ["answer_digest", "claim_id", "commit_digest", "prepared_digest", "reply_id", "request_id", "worker_identity_digest"],
      interaction_reply_accepted: ["ack_digest", "answer_digest", "claim_id", "commit_digest", "reply_id", "request_id", "worker_identity_digest"]
    });
    FUTURE_EVENT_TYPES = /* @__PURE__ */ new Set(["launch_intent", "launch_receipt", "launch_unknown", "claim_committed", "result_committed", "cleanup_pending", "cleanup_verified", "cleanup_unverified", "quarantined", "released", "launch_failed"]);
    FUTURE_EVIDENCE_KEYS = /* @__PURE__ */ new Set(["adapter_cleanup", "cancel_verification_digest", "claim_id", "cleanup_digest", "evidence_digest", "evidence_source", "launch_epoch", "launch_id", "launch_receipt_digest", "operation_resources_complete", "outcome", "probe_state", "process_tree_digest", "reason", "resolved_recovery_event_count", "resolved_recovery_event_digests", "resolved_recovery_event_root", "resources_digest", "result_commit_ref", "root_process_id", "root_start_fingerprint", "receipt_digest", "result_digest", "token_digest", "worker_identity_digest", "worker_tree_complete", "workspace_touched"]);
    EVENT_PHASE = Object.freeze({
      capacity_policy_committed: "policy_change_committed",
      reserved: "reserved",
      cancelled_before_launch: "cancelled_before_launch",
      launch_intent: "launch_intent",
      launch_unknown: "launch_unknown",
      claim_committed: "running",
      result_committed: "result_committed",
      cleanup_pending: "cleanup_pending",
      cleanup_verified: "cleanup_verified",
      cleanup_unverified: "cleanup_unverified",
      cleanup_reverified: "cleanup_reverified",
      quarantined: "quarantined",
      released: "released",
      launch_failed: "launch_failed"
    });
    RECOVERY_INPUT_KEYS = Object.freeze(["operation_id", "task_id", "attempt", "generation", "expected_revision", "claim_id", "worker_identity_digest", "classification", "reason_code", "evidence_source", "evidence_digest"]);
    RECOVERY_RELEASE_INPUT_KEYS = Object.freeze([...RECOVERY_INPUT_KEYS, "process_tree_root_observed", "process_tree_scan_clean", "process_tree_scan_digest", "recovery_disposition"]);
    ADMIN_ABANDONMENT_INPUT_KEYS = "attempt|claim_id|claim_worker_identity_digest|evidence|generation|operation_id|revision|task_id";
    ADMIN_ABANDONMENT_EVIDENCE_KEYS = "boot_time|claimant_scan_clean|claimant_scan_digest|failed_at|hosts_closed|observed_at|platform_probe_digest|process_inventory_digest|worker_exited|worker_process_id|worker_start_fingerprint|writer_closed";
    USER_AUTHORIZED_RELEASE_INPUT_KEYS = "attempt|cancel_id|generation|operation_id|release_reason|revision|task_id";
    USER_AUTHORIZED_FORCED_RELEASE_INPUT_KEYS = "accept_worker_risk|attempt|cancel_id|generation|launch_receipt_digest|operation_id|release_reason|revision|task_id";
    USER_AUTHORIZED_CLEANUP_RELEASE_INPUT_KEYS = "attempt|cancel_id|cancellation_verification_digest|generation|operation_id|recovery_evidence_digest|release_reason|revision|task_id";
    EXECUTOR_WAKE_BASE_INPUT_KEYS = "attempt|authorization_digest|delivery_id|generation|operation_id|policy_digest|reason_code|state|task_id|thread_id";
    EXECUTOR_WAKE_INPUT_KEYS = "attempt|authorization_digest|delivery_id|generation|operation_id|policy_digest|queue_message_id|reason_code|state|task_id|thread_id";
    USER_AUTHORIZED_TERMINAL_RELEASE_INPUT_KEYS = "attempt|claim_id|generation|operation_id|recovery_evidence_digest|release_reason|result_commit_ref|result_digest|revision|task_id|worker_identity_digest";
    AdmissionError = class extends Error {
      constructor(code, message = code) {
        super(message);
        this.code = code;
      }
    };
    fail2 = (code, message) => {
      throw new AdmissionError(code, message);
    };
    SELF_IDENTITY_PROBE_ATTEMPTS = 2;
    SELF_IDENTITY_RETRY_MS = 50;
    writerIntentIdentity = createWriterIntentIdentity();
    IsolatedAdmissionStore = class _IsolatedAdmissionStore {
      #db;
      #paths;
      #closed = false;
      #poisoned = false;
      #fault;
      #recoveryOnly = false;
      #validatedSnapshot = null;
      constructor(key, db, paths, fault, recoveryOnly = false) {
        if (key !== CONSTRUCT) fail2("private_constructor");
        this.#db = db;
        this.#paths = paths;
        this.#fault = fault;
        this.#recoveryOnly = recoveryOnly;
      }
      static initialize(root, options = {}) {
        const p = pathsFor(root, options);
        rejectV13UpgradeMarker(p.db);
        if (existsSync(p.db) || existsSync(p.cutoverPending) || existsSync(p.cutoverPublished) || existsSync(p.poison) || existsSync(p.intent)) fail2("root_not_empty");
        if (options.onFreshBootstrapStage !== void 0 && typeof options.onFreshBootstrapStage !== "function") fail2("invalid_fresh_bootstrap_stage_hook");
        const freshBootstrapStage = options.onFreshBootstrapStage;
        const db = new DatabaseSync(p.db, { timeout: 5e3 });
        try {
          db.exec("PRAGMA journal_mode=WAL; PRAGMA synchronous=FULL; PRAGMA foreign_keys=ON; BEGIN IMMEDIATE");
          db.exec(SCHEMA);
          db.prepare("INSERT INTO authority_metadata(singleton,schema_version,next_generation) VALUES(1,?,0)").run(SCHEMA_VERSION);
          if (options.freshInstallReceiptId !== void 0) freshBootstrapStage?.("schema_initialized");
          if (options.freshInstallReceiptId !== void 0) {
            if (!validText2(options.freshInstallReceiptId, 128) || !validText2(options.verifierVersion, 128) || !Number.isInteger(options.freshInstallCapacityLimit) || options.freshInstallCapacityLimit < 1 || options.freshInstallCapacityLimit > 8) fail2("invalid_fresh_install_receipt");
            freshBootstrapStage?.("before_ready_receipt");
            db.prepare("INSERT INTO fresh_install_receipt(singleton,receipt_id,verifier_version,created_at) VALUES(1,?,?,?)").run(options.freshInstallReceiptId, options.verifierVersion, (/* @__PURE__ */ new Date()).toISOString());
            freshBootstrapStage?.("ready_receipt_written");
            const operationId = "fresh-install-capacity-v1";
            const capacityLimit = options.freshInstallCapacityLimit;
            const requestDigest = digest({ operation_id: operationId, capacity_limit: capacityLimit, expected_generation: 0 });
            const at = (/* @__PURE__ */ new Date()).toISOString();
            db.prepare("INSERT INTO manager_operations(operation_id,operation_kind,request_digest,revision,phase,policy_generation,capacity_limit,created_at) VALUES(?,'capacity_policy_change',?,1,'policy_change_committed',1,?,?)").run(operationId, requestDigest, capacityLimit, at);
            const evidenceJson = canonical3({ generation: 1, capacity_limit: capacityLimit });
            const evidenceDigest = digest(evidenceJson);
            db.prepare("INSERT INTO manager_operation_events(event_cursor,operation_id,sequence,event_type,from_phase,to_phase,generation,evidence_json,evidence_digest,at) VALUES(1,?,1,'capacity_policy_committed',NULL,'policy_change_committed',NULL,?,?,?)").run(operationId, evidenceJson, evidenceDigest, at);
            db.prepare("UPDATE authority_metadata SET next_event_cursor=1,policy_version=1,policy_generation=1,capacity_limit=?,policy_operation_id=? WHERE singleton=1").run(capacityLimit, operationId);
          }
          db.exec(`PRAGMA user_version=${SCHEMA_VERSION}; COMMIT`);
          if (options.freshInstallReceiptId !== void 0) freshBootstrapStage?.("capacity_provisioned");
        } catch (e) {
          try {
            db.exec("ROLLBACK");
          } catch {
          }
          db.close();
          throw e;
        }
        return new _IsolatedAdmissionStore(CONSTRUCT, db, p);
      }
      static open(root, { fault, ...pathOptions } = {}) {
        const p = pathsFor(root, pathOptions);
        if (existsSync(p.bootstrapPending) && !p.allowBootstrapPending) fail2("sqlite_bootstrap_pending");
        if (existsSync(p.cutoverPending)) fail2("cutover_publish_pending");
        if (existsSync(p.poison)) fail2("root_poisoned");
        if (existsSync(p.intent) && !retireWriterIntent(p)) fail2("root_writer_busy");
        rejectV13UpgradeMarker(p.db);
        if (!existsSync(p.db)) fail2("database_missing");
        preflightSchemaVersion(p.db);
        const db = new DatabaseSync(p.db, { timeout: 5e3 });
        db.exec("PRAGMA foreign_keys=ON");
        const s = new _IsolatedAdmissionStore(CONSTRUCT, db, p, fault);
        try {
          assertSchemaVersion(db);
          upgradeRecoveryBindingTrigger(db);
          assertCandidateSchema(db, {
            allowRuntimeEventExtensionAbsent: true,
            allowOwnerBindingExtensionAbsent: true
          });
          ensureRuntimeEventsSchema(db);
          ensureOwnerBindingsSchema(db);
          assertCandidateSchema(db);
          const columns = new Set(db.prepare("PRAGMA table_info(manager_operations)").all().map((x) => x.name));
          if (!["result_status", "result_generation", "result_digest", "result_json", "result_commit_ref"].every((x) => columns.has(x))) fail2("candidate_schema_mismatch");
          if (!db.prepare("SELECT 1 FROM pragma_table_info('manager_operation_events') WHERE name='event_cursor'").get()) fail2("candidate_schema_mismatch");
          s.#validate();
          assertCutoverPublicationGate(db, p);
        } catch (e) {
          db.close();
          if (e instanceof AdmissionError) throw e;
          fail2("database_unreadable", String(e));
        }
        return s;
      }
      /** Open only the current candidate schema read-only for conservative recovery inspection. */
      static openForRecovery(root, options = {}) {
        const p = pathsFor(root, options);
        if (existsSync(p.bootstrapPending)) fail2("sqlite_bootstrap_pending");
        if (existsSync(p.cutoverPending) && !p.allowCutoverPending) fail2("cutover_publish_pending");
        rejectV13UpgradeMarker(p.db);
        if (!existsSync(p.db)) fail2("database_missing");
        preflightSchemaVersion(p.db);
        const db = new DatabaseSync(p.db, { timeout: 5e3, readOnly: true });
        try {
          db.exec("PRAGMA foreign_keys=ON");
          db.exec("PRAGMA query_only=ON");
          assertSchemaVersion(db);
          const columns = new Set(db.prepare("PRAGMA table_info(manager_operations)").all().map((x) => x.name));
          if (!["result_status", "result_generation", "result_digest", "result_json", "result_commit_ref"].every((x) => columns.has(x))) fail2("candidate_schema_mismatch");
          if (!db.prepare("SELECT 1 FROM pragma_table_info('manager_operation_events') WHERE name='event_cursor'").get()) fail2("candidate_schema_mismatch");
          assertCutoverPublicationGate(db, p);
          return new _IsolatedAdmissionStore(CONSTRUCT, db, p, void 0, true);
        } catch (e) {
          db.close();
          if (e instanceof AdmissionError) throw e;
          fail2("database_unreadable", String(e));
        }
      }
      close() {
        if (!this.#closed) {
          this.#closed = true;
          this.#db.close();
        }
      }
      checkpoint() {
        this.#assertOpen();
        this.#db.exec("PRAGMA wal_checkpoint(TRUNCATE)");
      }
      get poisoned() {
        return this.#poisoned || existsSync(this.#paths.poison);
      }
      get foreignKeysEnabled() {
        this.#assertOpen();
        return this.#db.prepare("PRAGMA foreign_keys").get().foreign_keys === 1;
      }
      get queryOnlyEnabled() {
        this.#assertOpen();
        return this.#db.prepare("PRAGMA query_only").get().query_only === 1;
      }
      #adminAbandonments() {
        const table = this.#db.prepare("SELECT 1 FROM sqlite_schema WHERE type='table' AND name='manager_admin_abandonments'").get();
        if (!table) return /* @__PURE__ */ new Map();
        return new Map(this.#db.prepare("SELECT * FROM manager_admin_abandonments ORDER BY operation_id").all().map((row) => [row.operation_id, row]));
      }
      /** Production startup requires exactly one durable reason for this root. */
      assertAuthorityReady(expectedRuntimeRosterDigest) {
        return this.#readConsistent(() => this.#assertAuthorityReadyContents(expectedRuntimeRosterDigest));
      }
      #assertAuthorityReadyContents(expectedRuntimeRosterDigest) {
        const integrity = this.#db.prepare("PRAGMA integrity_check").all();
        if (integrity.length !== 1 || integrity[0].integrity_check !== "ok") fail2("database_corrupt");
        const fresh = this.#db.prepare("SELECT * FROM fresh_install_receipt").all();
        const switched = this.#db.prepare("SELECT * FROM authority_switch").all();
        if (fresh.length + switched.length !== 1) fail2("authority_receipt_missing_or_ambiguous");
        const metadata = this.#db.prepare("SELECT policy_generation,capacity_limit,policy_operation_id FROM authority_metadata WHERE singleton=1").get();
        if (!metadata || metadata.policy_generation < 1 || metadata.capacity_limit < 1 || metadata.capacity_limit > 8 || !validId(metadata.policy_operation_id)) fail2("capacity_policy_missing");
        if (fresh.length) {
          if (this.#db.prepare("SELECT COUNT(*) AS n FROM migration_runs").get().n !== 0 || this.#db.prepare("SELECT COUNT(*) AS n FROM json_artifacts").get().n !== 0 || this.#db.prepare("SELECT COUNT(*) AS n FROM migrated_task_results").get().n !== 0 || this.#db.prepare("SELECT COUNT(*) AS n FROM migrated_task_events").get().n !== 0) fail2("fresh_install_contains_legacy_data");
          return { kind: "fresh_install", receipt_id: fresh[0].receipt_id, verifier_version: fresh[0].verifier_version };
        }
        const receipt = switched[0];
        const migration = this.#db.prepare("SELECT source_manifest_json,source_manifest_digest FROM migration_runs WHERE migration_id=?").get(receipt.migration_id);
        if (!migration) fail2("migration_receipt_missing");
        const policy = parseAuthoritySourceManifest(migration.source_manifest_json, migration.source_manifest_digest);
        if (typeof expectedRuntimeRosterDigest !== "string" || !/^[0-9a-f]{64}$/u.test(expectedRuntimeRosterDigest) || receipt.runtime_roster_digest !== expectedRuntimeRosterDigest) fail2("authority_runtime_roster_mismatch");
        assertCutoverPublicationGate(this.#db, this.#paths);
        return {
          kind: "authority_switch",
          authority_generation: receipt.authority_generation,
          cutover_id: receipt.cutover_id,
          migration_id: receipt.migration_id,
          source_root_digest: receipt.source_root_digest,
          source_manifest_digest: receipt.source_manifest_digest,
          archive_directory: receipt.archive_directory,
          archive_manifest_digest: receipt.archive_manifest_digest,
          archive_source_tasks_root: receipt.archive_source_tasks_root,
          archive_file_count: receipt.archive_file_count,
          archive_byte_count: receipt.archive_byte_count,
          historical_exception_count: policy.exceptions.length,
          historical_exception_digest: policy.manifest.historical_exception_digest,
          source_kind: policy.kind,
          verifier_version: receipt.verifier_version
        };
      }
      /**
      /** Persist a TaskPackage, its initial queued Attempt, and its trusted Owner
       * Binding in one transaction. The binding is never read from task_json. */
      createTask(task, admissionOrCreatedAt = {}, legacyCreatedAt) {
        this.#assertWritable();
        validateTaskPackage(task);
        const createdAt = typeof admissionOrCreatedAt === "string" ? admissionOrCreatedAt : legacyCreatedAt ?? (/* @__PURE__ */ new Date()).toISOString();
        const admission = normalizeTaskAdmission(
          typeof admissionOrCreatedAt === "string" ? void 0 : admissionOrCreatedAt
        );
        if (!validText2(createdAt, 64) || Number.isNaN(Date.parse(createdAt))) fail2("invalid_task_created_at");
        const taskJson = canonical3(task);
        return this.#transaction(() => {
          if (this.#db.prepare("SELECT task_id FROM tasks WHERE task_id=?").get(task.task_id)) fail2("task_already_exists");
          this.#db.prepare("INSERT INTO tasks(task_id,task_json,status,current_attempt,created_at) VALUES(?,?,'queued',1,?)").run(task.task_id, taskJson, createdAt);
          this.#db.prepare("INSERT INTO attempts(task_id,attempt,generation,status,created_at) VALUES(?,1,NULL,'queued',?)").run(task.task_id, createdAt);
          this.#db.prepare(`INSERT INTO task_owner_bindings(
        task_id,binding_state,owner_thread_id,binding_source,bound_at
      ) VALUES(?,?,?,?,?)`).run(
            task.task_id,
            admission.owner_thread_id === null ? "unavailable" : "bound",
            admission.owner_thread_id,
            admission.binding_source,
            createdAt
          );
          this.#faultPoint("after_projection");
          return {
            task_id: task.task_id,
            current_attempt: 1,
            status: "queued",
            created_at: createdAt,
            owner_binding: ownerBindingProjection(task.task_id, admission, createdAt)
          };
        });
      }
      #ownerBinding(taskId) {
        if (!this.#db.prepare("SELECT 1 FROM sqlite_schema WHERE type='table' AND name='task_owner_bindings'").get()) {
          return {
            task_id: taskId,
            state: "unavailable",
            owner_thread_id: null,
            source: "legacy_unavailable",
            bound_at: null,
            reason_code: "owner_thread_unavailable"
          };
        }
        const row = this.#db.prepare(`SELECT task_id,binding_state,owner_thread_id,binding_source,bound_at
      FROM task_owner_bindings WHERE task_id=?`).get(taskId);
        if (!row) return {
          task_id: taskId,
          state: "unavailable",
          owner_thread_id: null,
          source: "legacy_unavailable",
          bound_at: null,
          reason_code: "owner_thread_unavailable"
        };
        return {
          task_id: row.task_id,
          state: row.binding_state,
          owner_thread_id: row.owner_thread_id,
          source: row.binding_source,
          bound_at: row.bound_at,
          reason_code: row.binding_state === "unavailable" ? "owner_thread_unavailable" : null
        };
      }
      readTask(taskId) {
        return this.#readConsistent(() => {
          const row = this.#db.prepare("SELECT task_json FROM tasks WHERE task_id=?").get(taskId);
          if (!row) return null;
          let task;
          try {
            task = JSON.parse(row.task_json);
          } catch {
            fail2("task_projection_invalid");
          }
          validateTaskPackage(task);
          if (task.task_id !== taskId) fail2("task_projection_identity_mismatch");
          return task;
        });
      }
      readTaskProjection(taskId) {
        return this.#readConsistent(() => this.#db.prepare("SELECT task_id,status,current_attempt,created_at FROM tasks WHERE task_id=?").get(taskId) ?? null);
      }
      /** Stable, bounded, read-only task enumeration for the Executor Control API. */
      readTaskProjections({ afterTaskId = null, limit = 50, status = null } = {}) {
        if (afterTaskId !== null && !validId(afterTaskId) || !Number.isSafeInteger(limit) || limit < 1 || limit > 100 || status !== null && !["queued", "running", "completed", "failed", "cancelled", "waiting_for_master"].includes(status)) {
          fail2("invalid_task_list_query");
        }
        return this.#readConsistent(() => {
          const rows = this.#db.prepare(`SELECT t.task_id,t.status,t.current_attempt,t.created_at,t.task_json,
          (SELECT e.evidence_json
             FROM manager_operation_events e
             JOIN manager_operations o ON o.operation_id=e.operation_id
            WHERE o.task_id=t.task_id
              AND o.attempt=t.current_attempt
              AND e.event_type='observation_recorded'
              AND json_extract(e.evidence_json,'$.reason')='executor_wake'
            ORDER BY e.sequence DESC LIMIT 1) AS wake_evidence_json,
          (SELECT e.at
             FROM manager_operation_events e
             JOIN manager_operations o ON o.operation_id=e.operation_id
            WHERE o.task_id=t.task_id
              AND o.attempt=t.current_attempt
              AND e.event_type='observation_recorded'
              AND json_extract(e.evidence_json,'$.reason')='executor_wake'
            ORDER BY e.sequence DESC LIMIT 1) AS wake_at
        FROM tasks t
        WHERE t.task_id>? AND (? IS NULL OR t.status=?)
        ORDER BY t.task_id
        LIMIT ?`).all(afterTaskId ?? "", status, status, limit + 1);
          const hasMore = rows.length > limit;
          const visible = rows.slice(0, limit).map((row) => {
            let task;
            try {
              task = JSON.parse(row.task_json);
            } catch {
              fail2("task_projection_invalid");
            }
            validateTaskPackage(task);
            if (task.task_id !== row.task_id) fail2("task_projection_identity_mismatch");
            return {
              task_id: row.task_id,
              status: row.status,
              attempt: row.current_attempt,
              created_at: row.created_at,
              workspace: task.workspace,
              objective: task.objective,
              owner_binding: this.#ownerBinding(row.task_id),
              wake_evidence_json: row.wake_evidence_json,
              wake_at: row.wake_at
            };
          });
          return {
            tasks: visible,
            next_task_id: hasMore ? visible.at(-1)?.task_id ?? null : null,
            has_more: hasMore
          };
        });
      }
      /** Return only the current queued Attempt for each queued Task, with an explicit safe-to-dispatch classification. */
      readRecoverableQueuedAttempts() {
        return this.#readConsistent(() => {
          const rows = this.#db.prepare(`SELECT t.task_id,t.status AS task_status,t.current_attempt,t.created_at,t.task_json,
          a.attempt,a.generation,a.status AS attempt_status,
          o.operation_id,o.task_id AS operation_task_id,o.attempt AS operation_attempt,o.generation AS operation_generation,
          o.revision AS operation_revision,o.phase,o.reservation_id,o.capacity_slot,
          o.launch_id,o.launch_epoch,o.launch_token_digest,o.launch_intent_digest,
          o.launch_receipt_id,o.launch_receipt_digest,o.launch_identity_json,
          o.claim_id,o.claim_request_digest,o.claim_worker_identity_json,o.claim_worker_identity_digest,
          o.claim_launch_id,o.claim_generation,o.claim_token_digest,
          o.result_status,o.result_generation,o.result_digest,o.result_json,o.result_commit_ref
        FROM tasks t JOIN attempts a ON a.task_id=t.task_id AND a.attempt=t.current_attempt
        LEFT JOIN manager_operations o ON o.operation_kind='attempt_lifecycle' AND o.task_id=t.task_id AND o.attempt=a.attempt
        WHERE t.status='queued' AND a.status='queued' ORDER BY t.created_at,t.task_id`).all();
          return rows.map((row) => {
            let task;
            try {
              task = JSON.parse(row.task_json);
            } catch {
              fail2("task_projection_invalid");
            }
            validateTaskPackage(task);
            if (task.task_id !== row.task_id || row.attempt !== row.current_attempt) fail2("task_attempt_projection_mismatch");
            const hasOperation = row.operation_id !== null;
            if (!hasOperation && row.generation !== null) fail2("queued_attempt_generation_without_operation");
            if (hasOperation && (row.operation_task_id !== row.task_id || row.operation_attempt !== row.attempt || row.operation_generation !== row.generation || row.generation === null)) fail2("queued_operation_identity_mismatch");
            let dispatchable = !hasOperation;
            let reason = hasOperation ? "operation_requires_recovery" : null;
            if (hasOperation && row.phase === "reserved" && row.operation_revision === 1 && row.launch_id === null && row.launch_epoch === null && row.launch_token_digest === null && row.launch_intent_digest === null && row.launch_receipt_id === null && row.launch_receipt_digest === null && row.launch_identity_json === null && row.claim_id === null && row.claim_request_digest === null && row.claim_worker_identity_json === null && row.claim_worker_identity_digest === null && row.claim_launch_id === null && row.claim_generation === null && row.claim_token_digest === null && row.result_status === null && row.result_generation === null && row.result_digest === null && row.result_json === null && row.result_commit_ref === null) {
              const events = this.#db.prepare("SELECT operation_id,event_cursor,sequence,event_type,from_phase,to_phase,generation,evidence_json FROM manager_operation_events WHERE operation_id=? ORDER BY sequence").all(row.operation_id);
              if (events.length !== 1 || events[0].sequence !== 1 || events[0].event_type !== "reserved" || events[0].from_phase !== null || events[0].operation_id !== row.operation_id || !Number.isSafeInteger(events[0].event_cursor) || events[0].event_cursor < 1 || events[0].to_phase !== "reserved" || events[0].generation !== row.generation) fail2("reserved_operation_history_invalid");
              let evidence;
              try {
                evidence = JSON.parse(events[0].evidence_json);
              } catch {
                fail2("reserved_operation_history_invalid");
              }
              if (evidence.reservation_id !== row.reservation_id || evidence.capacity_slot !== row.capacity_slot) fail2("reserved_operation_history_invalid");
              dispatchable = true;
              reason = null;
            }
            return {
              task,
              task_id: row.task_id,
              attempt: row.attempt,
              generation: row.generation,
              operation_id: row.operation_id,
              phase: row.phase ?? null,
              dispatchable,
              reason
            };
          });
        });
      }
      readAttempt(taskId, attempt) {
        if (!validId(taskId) || !Number.isSafeInteger(attempt) || attempt < 1) fail2("invalid_attempt_identity");
        return this.#readConsistent(() => this.#db.prepare("SELECT task_id,attempt,generation,status,created_at FROM attempts WHERE task_id=? AND attempt=?").get(taskId, attempt) ?? null);
      }
      /** Read the Task, current Attempt, bound Operation and verified Result in one snapshot. */
      readTaskLifecycle(taskId) {
        if (!validId(taskId)) fail2("invalid_task_id");
        return this.#readConsistent(() => {
          const taskRow = this.#db.prepare("SELECT task_id,status,current_attempt,created_at,task_json FROM tasks WHERE task_id=?").get(taskId);
          if (!taskRow || this.#isRetiredHistoricalTask(taskId)) return null;
          let task;
          try {
            task = JSON.parse(taskRow.task_json);
          } catch {
            fail2("task_projection_invalid");
          }
          validateTaskPackage(task);
          if (task.task_id !== taskId) fail2("task_projection_identity_mismatch");
          const attemptRow = this.#db.prepare("SELECT task_id,attempt,generation,status,created_at,queued_cancel_id,continuation_operation_id,continuation_json,continuation_digest,queued_cancel_result_json FROM attempts WHERE task_id=? AND attempt=?").get(taskId, taskRow.current_attempt);
          const attempt = attemptRow ? {
            task_id: attemptRow.task_id,
            attempt: attemptRow.attempt,
            generation: attemptRow.generation,
            status: attemptRow.status,
            created_at: attemptRow.created_at,
            ...attemptRow.queued_cancel_id !== null ? { queued_cancel_id: attemptRow.queued_cancel_id } : {}
          } : null;
          if (!attempt) fail2("task_attempt_projection_mismatch");
          const operationRow = this.#db.prepare("SELECT * FROM manager_operations WHERE operation_kind='attempt_lifecycle' AND task_id=? AND attempt=?").get(taskId, taskRow.current_attempt);
          const adminAbandonment = operationRow ? this.#adminAbandonments().get(operationRow.operation_id) : void 0;
          const operation = operationRow ? presentOperation(operationRow, adminAbandonment) : null;
          let result = null;
          if (operationRow?.result_json !== null && operationRow?.result_json !== void 0) {
            try {
              result = JSON.parse(operationRow.result_json);
            } catch {
              fail2("result_projection_invalid");
            }
          } else if (attemptRow.queued_cancel_result_json !== null) {
            try {
              result = JSON.parse(attemptRow.queued_cancel_result_json);
            } catch {
              fail2("result_projection_invalid");
            }
          }
          const continuation = attemptRow.continuation_json === null ? null : JSON.parse(attemptRow.continuation_json);
          const rejected = operationRow ? this.#db.prepare("SELECT evidence_json FROM manager_operation_events WHERE operation_id=? AND event_type='observation_recorded' AND json_extract(evidence_json,'$.reason') LIKE 'result_submission_failed:%' ORDER BY sequence DESC LIMIT 1").get(operationRow.operation_id) : null;
          const result_submission_error = rejected ? JSON.parse(rejected.evidence_json).reason.slice("result_submission_failed:".length) : null;
          return {
            task,
            projection: { task_id: taskRow.task_id, status: taskRow.status, current_attempt: taskRow.current_attempt, created_at: taskRow.created_at },
            owner_binding: this.#ownerBinding(taskId),
            attempt,
            operation,
            result,
            continuation,
            ...result_submission_error ? { result_submission_error } : {}
          };
        });
      }
      /** Read-only Console projection. All relational facts and Result summaries
       * come from one SQLite snapshot; callers must not infer Plan, Usage or
       * Release from Workspace, Task name, or model naming conventions. */
      readTaskConsoleProjection(taskId, { includeAttempts = false } = {}) {
        if (!validId(taskId) || typeof includeAttempts !== "boolean") fail2("invalid_console_projection_query");
        return this.#readConsistent(() => {
          const taskRow = this.#db.prepare("SELECT task_id,status,current_attempt,created_at,task_json FROM tasks WHERE task_id=?").get(taskId);
          if (!taskRow || this.#isRetiredHistoricalTask(taskId)) return null;
          let task;
          try {
            task = JSON.parse(taskRow.task_json);
          } catch {
            fail2("task_projection_invalid");
          }
          validateTaskPackage(task);
          if (task.task_id !== taskId) fail2("task_projection_identity_mismatch");
          const attemptRows = this.#db.prepare(`SELECT task_id,attempt,generation,status,created_at,
          queued_cancel_id,queued_cancel_event_cursor,queued_cancelled_at,queued_cancel_operation_id,queued_cancel_result_json
        FROM attempts WHERE task_id=? ORDER BY attempt`).all(taskId);
          if (!attemptRows.length || !attemptRows.some((row) => row.attempt === taskRow.current_attempt)) fail2("task_attempt_projection_mismatch");
          const operationRows = this.#db.prepare(`SELECT * FROM manager_operations
        WHERE operation_kind='attempt_lifecycle' AND task_id=? ORDER BY attempt`).all(taskId);
          const operations = new Map(operationRows.map((row) => [row.attempt, row]));
          const runtimeEvents = this.#db.prepare("SELECT 1 FROM sqlite_schema WHERE type='table' AND name='runtime_task_events'").get();
          const attempts = attemptRows.map((attemptRow) => {
            const operationRow = operations.get(attemptRow.attempt) ?? null;
            const adminAbandonment = operationRow ? this.#adminAbandonments().get(operationRow.operation_id) : void 0;
            const operation = operationRow ? presentOperation(operationRow, adminAbandonment) : null;
            let result = null;
            if (operationRow?.result_json !== null && operationRow?.result_json !== void 0) {
              try {
                result = JSON.parse(operationRow.result_json);
              } catch {
                fail2("result_projection_invalid");
              }
            } else if (attemptRow.queued_cancel_result_json !== null) {
              try {
                result = JSON.parse(attemptRow.queued_cancel_result_json);
              } catch {
                fail2("result_projection_invalid");
              }
            }
            const events = operationRow ? this.#db.prepare(`SELECT *
          FROM manager_operation_events WHERE operation_id=? ORDER BY sequence`).all(operationRow.operation_id) : [];
            let wake = null, hold = null, resultSubmissionError = null, administrativeRelease = false, cleanupVerified = false;
            for (const event of events) {
              let evidence;
              try {
                evidence = JSON.parse(event.evidence_json);
              } catch {
                fail2("operation_event_evidence_invalid");
              }
              if (event.event_type === "cleanup_verified" || event.event_type === "cleanup_reverified") cleanupVerified = true;
              if (event.event_type === "observation_recorded" && evidence.reason === "executor_wake" && typeof evidence.state === "string" && typeof evidence.reason_code === "string") {
                wake = { state: evidence.state, reason_code: evidence.reason_code, at: event.at };
              }
              if (event.event_type === "observation_recorded" && evidence.reason === "user_authorized_release_unverified") {
                administrativeRelease = true;
              }
              if (event.event_type === "observation_recorded" && typeof evidence.reason === "string" && evidence.reason.startsWith("result_submission_failed:")) {
                resultSubmissionError = evidence.reason.slice("result_submission_failed:".length);
              }
            }
            if (operationRow && foldedRecoveryClassification(operationRow, events) !== "normal") {
              const active = recoveryEventsFor(events, operationRow).filter((event) => event.active).at(-1);
              hold = {
                reason_code: typeof active?.evidence.reason_code === "string" ? active.evidence.reason_code : operationRow.phase === "quarantined" ? "recovery_quarantine" : "recovery_hold",
                at: active?.event.at ?? null
              };
            }
            const pendingRequests = [];
            const replyOutcomeUnknownRequests = [];
            if (operationRow) {
              const payloads = this.#db.prepare(`SELECT p.request_id,
              EXISTS(SELECT 1 FROM manager_operation_events e WHERE e.operation_id=p.operation_id
                AND json_extract(e.evidence_json,'$.request_id')=p.request_id
                AND e.event_type='interaction_reply_accepted') AS answered,
              EXISTS(SELECT 1 FROM manager_operation_events e WHERE e.operation_id=p.operation_id
                AND json_extract(e.evidence_json,'$.request_id')=p.request_id
                AND e.event_type='interaction_reply_intent') AS reply_intent
            FROM manager_interaction_payloads p WHERE p.operation_id=? ORDER BY p.rowid`).all(operationRow.operation_id);
              for (const payload of payloads) {
                if (payload.answered) continue;
                if (payload.reply_intent) replyOutcomeUnknownRequests.push(payload.request_id);
                else pendingRequests.push(payload.request_id);
              }
            }
            const latestOperationAt = events.at(-1)?.at ?? null;
            const latestRuntimeAt = runtimeEvents ? this.#db.prepare(`SELECT MAX(at) AS at FROM runtime_task_events
          WHERE task_id=? AND attempt=?`).get(taskId, attemptRow.attempt).at : null;
            const cancelledAt = attemptRow.queued_cancelled_at ?? null;
            const attemptUpdatedAt = [latestOperationAt, latestRuntimeAt, cancelledAt, attemptRow.created_at].filter((value) => typeof value === "string" && Number.isFinite(Date.parse(value))).sort().at(-1) ?? attemptRow.created_at;
            return {
              attempt: attemptRow.attempt,
              generation: attemptRow.generation,
              status: attemptRow.status,
              created_at: attemptRow.created_at,
              updated_at: attemptUpdatedAt,
              current: attemptRow.attempt === taskRow.current_attempt,
              operation: operation ? {
                operation_id: operation.operation_id,
                phase: operation.phase,
                revision: operation.revision,
                result_status: operation.result_status,
                result_digest: operation.result_digest,
                cleanup_verified: cleanupVerified,
                administrative_release: administrativeRelease
              } : null,
              result,
              wake,
              hold,
              pending_requests: pendingRequests,
              reply_outcome_unknown_requests: replyOutcomeUnknownRequests,
              ...resultSubmissionError ? { result_submission_error: resultSubmissionError } : {}
            };
          });
          const current = attempts.find((attempt) => attempt.current);
          if (!current) fail2("task_attempt_projection_mismatch");
          const updatedAt = [current.updated_at, taskRow.created_at].filter((value) => typeof value === "string" && Number.isFinite(Date.parse(value))).sort().at(-1) ?? taskRow.created_at;
          return {
            task,
            projection: {
              task_id: taskRow.task_id,
              status: taskRow.status,
              current_attempt: taskRow.current_attempt,
              created_at: taskRow.created_at
            },
            owner_binding: this.#ownerBinding(taskId),
            updated_at: updatedAt,
            current,
            ...includeAttempts ? { attempts } : {}
          };
        });
      }
      /** P1 §3.4: read one bounded page of the exact stored canonical Result
       * JSON. Byte offsets always land on UTF-8 codepoint boundaries via the
       * returned next_offset; callers must page with it instead of computing
       * their own offsets. Concatenating every page's data reproduces the stored
       * bytes whose SHA-256 is operation.result_digest. */
      readTaskResultPage(taskId, offsetBytes, maxBytes) {
        if (!validId(taskId) || !Number.isSafeInteger(offsetBytes) || offsetBytes < 0 || !Number.isSafeInteger(maxBytes) || maxBytes < 1 || maxBytes > 4194304) fail2("invalid_result_page_read");
        return this.#readConsistent(() => {
          const taskRow = this.#db.prepare("SELECT task_id,current_attempt FROM tasks WHERE task_id=?").get(taskId);
          if (!taskRow || this.#isRetiredHistoricalTask(taskId)) fail2("task_not_found");
          const operationRow = this.#db.prepare("SELECT operation_id,result_json,result_digest,result_commit_ref,result_status FROM manager_operations WHERE operation_kind='attempt_lifecycle' AND task_id=? AND attempt=?").get(taskId, taskRow.current_attempt);
          if (!operationRow || operationRow.result_json === null) fail2("result_not_committed");
          const bytes = Buffer.from(operationRow.result_json, "utf8");
          if (offsetBytes > bytes.length) fail2("invalid_result_page_offset");
          let end = Math.min(offsetBytes + maxBytes, bytes.length);
          while (end < bytes.length && (bytes[end] & 192) === 128) end += 1;
          if (end >= bytes.length) end = bytes.length;
          const nextOffset = end < bytes.length ? end : null;
          return {
            operation_id: operationRow.operation_id,
            result_digest: operationRow.result_digest,
            result_content_digest: createHash2("sha256").update(bytes).digest("hex"),
            result_commit_ref: operationRow.result_commit_ref,
            result_status: operationRow.result_status,
            offset_bytes: offsetBytes,
            next_offset: nextOffset,
            total_bytes: bytes.length,
            data: bytes.subarray(offsetBytes, end).toString("utf8")
          };
        });
      }
      /** P2 §4.5: latest persisted event time for a Task. Reads one row per event
       * source (operation events, queued cancels, runtime events), so the cost
       * never scales with the full history the way a cursor-0 page read did. */
      readTaskLatestEventAt(taskId) {
        if (!validId(taskId)) fail2("invalid_task_id");
        return this.#readConsistent(() => {
          if (!this.#db.prepare("SELECT task_id FROM tasks WHERE task_id=?").get(taskId) || this.#isRetiredHistoricalTask(taskId)) fail2("task_not_found");
          const candidates = [];
          const operationRow = this.#db.prepare(`SELECT e.at AS at FROM manager_operation_events e
          JOIN manager_operations o ON o.operation_id=e.operation_id
          WHERE o.operation_kind='attempt_lifecycle' AND o.task_id=?
          ORDER BY e.event_cursor DESC LIMIT 1`).get(taskId);
          if (operationRow) candidates.push(operationRow.at);
          const cancelRow = this.#db.prepare(`SELECT queued_cancelled_at AS at FROM attempts
          WHERE task_id=? AND queued_cancel_event_cursor IS NOT NULL
          ORDER BY queued_cancel_event_cursor DESC LIMIT 1`).get(taskId);
          if (cancelRow) candidates.push(cancelRow.at);
          if (this.#db.prepare("SELECT 1 FROM sqlite_schema WHERE type='table' AND name='runtime_task_events'").get()) {
            const runtimeRow = this.#db.prepare(`SELECT at FROM runtime_task_events WHERE task_id=?
          ORDER BY event_cursor DESC LIMIT 1`).get(taskId);
            if (runtimeRow) candidates.push(runtimeRow.at);
          }
          if (candidates.length === 0) return null;
          candidates.sort();
          return { at: candidates[candidates.length - 1] };
        });
      }
      /** Project Feedback only from this Attempt's persisted runtime observations
       * and a committed Result. */
      readTaskFeedback(taskId) {
        const snapshot = this.readTaskLifecycle(taskId);
        if (!snapshot) return null;
        if (snapshot.projection.status !== snapshot.attempt.status) fail2("task_attempt_projection_mismatch");
        const runtimeTable = this.#db.prepare("SELECT 1 FROM sqlite_schema WHERE type='table' AND name='runtime_task_events'").get();
        const runtimeRows = runtimeTable ? this.#db.prepare(`SELECT event_cursor,event_type,at,summary,details_json
      FROM runtime_task_events WHERE task_id=? AND attempt=? ORDER BY event_cursor`).all(taskId, snapshot.attempt.attempt) : [];
        let workerPid = null;
        if (snapshot.operation?.claim_worker_identity_json) {
          try {
            const identity = JSON.parse(snapshot.operation.claim_worker_identity_json);
            if (Number.isSafeInteger(identity.process_id)) workerPid = identity.process_id;
          } catch {
            fail2("feedback_worker_identity_invalid");
          }
        }
        const result = snapshot.result;
        const events = runtimeRows.map((row) => {
          let details;
          if (row.details_json !== null) {
            try {
              details = JSON.parse(row.details_json);
            } catch {
              fail2("feedback_event_projection_invalid");
            }
          }
          return {
            seq: row.event_cursor,
            at: row.at,
            type: row.event_type,
            summary: row.summary,
            ...details === void 0 ? {} : { details }
          };
        });
        return buildTaskFeedbackSnapshotV01({
          status: {
            task_id: snapshot.projection.task_id,
            status: snapshot.projection.status,
            attempt: snapshot.attempt.attempt,
            created_at: snapshot.projection.created_at,
            updated_at: events.at(-1)?.at ?? result?.finished_at ?? snapshot.projection.created_at,
            started_at: result?.started_at ?? (snapshot.projection.status === "running" ? snapshot.operation?.created_at ?? null : null),
            finished_at: result?.finished_at ?? null,
            worker_pid: snapshot.projection.status === "running" ? workerPid : null,
            zcode_session_id: typeof result?.session_id === "string" ? result.session_id : null,
            exit_code: Number.isSafeInteger(result?.exit_code) ? result.exit_code : null
          },
          events,
          result: result ?? null
        });
      }
      /** Persist a request received from the currently claimed Worker channel. */
      recordInteractionRequest(input) {
        this.#assertWritable();
        const request = input?.request;
        if (!validateInteractionRequest(request)) fail2("invalid_interaction_request");
        if (!validInteractionFence(input) || typeof input.worker_identity_digest !== "string" || !/^[0-9a-f]{64}$/u.test(input.worker_identity_digest)) fail2("invalid_interaction_fence");
        const requestJson = interactionCanonical(request);
        if (Buffer.byteLength(requestJson, "utf8") > 1048576) fail2("interaction_request_too_large");
        const requestDigest = interactionDigest({
          interaction_contract_version: 1,
          operation_id: input.operation_id,
          task_id: input.task_id,
          attempt: input.attempt,
          generation: input.generation,
          claim_id: input.claim_id,
          worker_identity_digest: input.worker_identity_digest,
          request
        });
        return this.#transaction(() => {
          const existing = this.#db.prepare("SELECT * FROM manager_interaction_payloads WHERE operation_id=? AND request_id=?").get(input.operation_id, request.request_id);
          if (existing) {
            if (existing.request_digest !== requestDigest || existing.task_id !== input.task_id || existing.attempt !== input.attempt || existing.generation !== input.generation || existing.claim_id !== input.claim_id || existing.worker_identity_digest !== input.worker_identity_digest)
              fail2("interaction_request_conflict");
            const event = this.#db.prepare("SELECT sequence FROM manager_operation_events WHERE operation_id=? AND event_type='interaction_requested' AND json_extract(evidence_json,'$.request_id')=?").get(input.operation_id, request.request_id);
            if (!event) fail2("interaction_history_mismatch");
            return {
              duplicate: true,
              operation_id: input.operation_id,
              task_id: input.task_id,
              attempt: input.attempt,
              generation: input.generation,
              request_id: request.request_id,
              revision: this.#db.prepare("SELECT revision FROM manager_operations WHERE operation_id=?").get(input.operation_id).revision,
              event_sequence: event.sequence,
              request_digest: requestDigest
            };
          }
          const o = this.#attemptOperation(input);
          this.#assertRecoveryNotLatched(o.operation_id);
          this.#assertInteractionRunning(o, input);
          if (o.revision !== input.expected_revision) fail2("stale_interaction_cas");
          const priorCount = this.#db.prepare("SELECT COUNT(*) AS n FROM manager_interaction_payloads WHERE operation_id=?").get(o.operation_id).n;
          if (priorCount >= 128) fail2("interaction_request_limit");
          const changed = this.#db.prepare("UPDATE manager_operations SET revision=revision+1 WHERE operation_id=? AND task_id=? AND attempt=? AND generation=? AND phase='running' AND revision=? AND claim_id=? AND claim_generation=? AND claim_worker_identity_digest=?").run(o.operation_id, o.task_id, o.attempt, o.generation, o.revision, o.claim_id, o.generation, o.claim_worker_identity_digest);
          if (changed.changes !== 1) fail2("stale_interaction_cas");
          this.#faultPoint("after_projection");
          this.#db.prepare("INSERT INTO manager_interaction_payloads(operation_id,request_id,task_id,attempt,generation,claim_id,worker_identity_digest,request_method,request_json,request_digest) VALUES(?,?,?,?,?,?,?,?,?,?)").run(o.operation_id, request.request_id, o.task_id, o.attempt, o.generation, o.claim_id, o.claim_worker_identity_digest, request.method, requestJson, requestDigest);
          this.#faultPoint("after_interaction_payload");
          const at = (/* @__PURE__ */ new Date()).toISOString();
          this.#event(
            o.operation_id,
            o.revision + 1,
            "interaction_requested",
            "running",
            "running",
            o.generation,
            { claim_id: o.claim_id, request_digest: requestDigest, request_id: request.request_id, request_method: request.method, worker_identity_digest: o.claim_worker_identity_digest },
            at
          );
          return {
            duplicate: false,
            operation_id: o.operation_id,
            task_id: o.task_id,
            attempt: o.attempt,
            generation: o.generation,
            claim_id: o.claim_id,
            worker_identity_digest: o.claim_worker_identity_digest,
            request_id: request.request_id,
            request_digest: requestDigest,
            revision: o.revision + 1,
            event_sequence: o.revision + 1
          };
        });
      }
      /** Read the current Attempt's request and derive state only from immutable events. */
      readInteractionRequest(taskId, requestId) {
        if (!validId(taskId) || typeof requestId !== "string" || !validId(requestId) || requestId.length > 512) fail2("invalid_interaction_request_id");
        return this.#readConsistent(() => {
          const task = this.#db.prepare("SELECT task_id,current_attempt FROM tasks WHERE task_id=?").get(taskId);
          if (!task) fail2("task_not_found");
          return this.#readInteractionRequestInSnapshot(task, requestId);
        });
      }
      /** Read current Attention facts in one SQLite snapshot without mutating state. */
      readTaskAttention(taskId) {
        if (!validId(taskId)) fail2("invalid_task_id");
        return this.#readConsistent(() => {
          const task = this.#db.prepare("SELECT task_id,status,current_attempt FROM tasks WHERE task_id=?").get(taskId);
          if (!task) return null;
          const attempt = this.#db.prepare("SELECT attempt,generation,status FROM attempts WHERE task_id=? AND attempt=?").get(taskId, task.current_attempt);
          if (!attempt || attempt.attempt !== task.current_attempt || attempt.status !== task.status) fail2("task_attempt_projection_mismatch");
          const pending = [];
          if (task.status === "completed" || task.status === "failed" || task.status === "cancelled" || task.status === "waiting_for_master") {
            return { task_id: task.task_id, attempt: task.current_attempt, status: task.status, pending_requests: [] };
          }
          if (task.status === "queued") return { task_id: task.task_id, attempt: task.current_attempt, status: task.status, pending_requests: [] };
          if (task.status !== "running") fail2("task_attempt_projection_mismatch");
          const operation = this.#db.prepare("SELECT * FROM manager_operations WHERE operation_kind='attempt_lifecycle' AND task_id=? AND attempt=?").get(taskId, task.current_attempt);
          if (!operation || attempt.status !== "running" || operation.phase !== "running" || operation.generation !== attempt.generation || operation.claim_generation !== operation.generation || !operation.claim_id || !operation.claim_worker_identity_digest)
            fail2("interaction_task_projection_mismatch");
          const candidates = this.#db.prepare(`SELECT p.request_id,e.sequence
        FROM manager_interaction_payloads p
        LEFT JOIN manager_operation_events e ON e.operation_id=p.operation_id
          AND e.event_type='interaction_requested'
          AND json_extract(e.evidence_json,'$.request_id')=p.request_id
        WHERE p.operation_id=? AND p.task_id=? AND p.attempt=?
        ORDER BY e.sequence,p.rowid`).all(operation.operation_id, taskId, task.current_attempt);
          for (const candidate of candidates) {
            const request = this.#readInteractionRequestInSnapshot(task, candidate.request_id);
            if (!request) fail2("interaction_history_mismatch");
            if (request.state === "unknown") fail2("interaction_reply_outcome_unknown");
            if (request.state === "pending") pending.push(candidate.request_id);
          }
          return { task_id: task.task_id, attempt: task.current_attempt, status: task.status, pending_requests: pending };
        });
      }
      #readInteractionRequestInSnapshot(task, requestId) {
        const requestIdValue = String(requestId);
        const payload = this.#db.prepare("SELECT * FROM manager_interaction_payloads WHERE task_id=? AND attempt=? AND request_id=?").get(task.task_id, task.current_attempt, requestIdValue);
        if (!payload) return null;
        const events = this.#db.prepare("SELECT sequence,event_type,evidence_json,evidence_digest FROM manager_operation_events WHERE operation_id=? AND json_extract(evidence_json,'$.request_id')=? AND event_type IN ('interaction_requested','interaction_reply_intent','interaction_reply_prepared','interaction_reply_committed','interaction_reply_accepted') ORDER BY sequence").all(payload.operation_id, requestIdValue).map((e) => ({ ...e, evidence: JSON.parse(e.evidence_json) }));
        const requestEvent = events.find((e) => e.event_type === "interaction_requested");
        const intent = events.find((e) => e.event_type === "interaction_reply_intent");
        const prepared = events.find((e) => e.event_type === "interaction_reply_prepared");
        const committed = events.find((e) => e.event_type === "interaction_reply_committed");
        const accepted = events.find((e) => e.event_type === "interaction_reply_accepted");
        if (!requestEvent || events.filter((e) => e.event_type === "interaction_requested").length !== 1 || events.filter((e) => e.event_type === "interaction_reply_intent").length > 1 || events.filter((e) => e.event_type === "interaction_reply_prepared").length > 1 || events.filter((e) => e.event_type === "interaction_reply_committed").length > 1 || events.filter((e) => e.event_type === "interaction_reply_accepted").length > 1 || accepted && !committed || events.some((e) => e.evidence_digest !== digest(e.evidence_json)) || requestEvent.evidence.request_digest !== payload.request_digest || requestEvent.evidence.request_method !== payload.request_method || intent && (intent.sequence <= requestEvent.sequence || intent.evidence.reply_id !== payload.reply_id || intent.evidence.answer_digest !== payload.answer_digest) || prepared && (!intent || prepared.sequence !== intent.sequence + 1 || prepared.evidence.reply_id !== payload.reply_id || prepared.evidence.answer_digest !== payload.answer_digest) || committed && (!prepared || committed.sequence !== prepared.sequence + 1 || committed.evidence.reply_id !== payload.reply_id || committed.evidence.answer_digest !== payload.answer_digest || committed.evidence.prepared_digest !== prepared.evidence.prepared_digest) || accepted && (!committed || accepted.sequence !== committed.sequence + 1 || accepted.evidence.reply_id !== payload.reply_id || accepted.evidence.answer_digest !== payload.answer_digest || accepted.evidence.commit_digest !== committed.evidence.commit_digest)) fail2("interaction_history_mismatch");
        const request = JSON.parse(payload.request_json);
        if (!validateInteractionRequest(request) || interactionCanonical(request) !== payload.request_json || request.request_id !== requestIdValue || request.method !== payload.request_method || payload.request_digest !== interactionDigest({
          interaction_contract_version: 1,
          operation_id: payload.operation_id,
          task_id: payload.task_id,
          attempt: payload.attempt,
          generation: payload.generation,
          claim_id: payload.claim_id,
          worker_identity_digest: payload.worker_identity_digest,
          request
        }))
          fail2("interaction_history_mismatch");
        if (intent) {
          const answer = JSON.parse(payload.answer_json);
          if (interactionCanonical(answer) !== payload.answer_json || !validPersistedInteractionAnswer(request, answer) || payload.answer_digest !== interactionDigest({
            interaction_reply_contract_version: 1,
            operation_id: payload.operation_id,
            task_id: payload.task_id,
            attempt: payload.attempt,
            generation: payload.generation,
            claim_id: payload.claim_id,
            worker_identity_digest: payload.worker_identity_digest,
            request_id: requestIdValue,
            answer
          }))
            fail2("interaction_history_mismatch");
        }
        return {
          operation_id: payload.operation_id,
          task_id: payload.task_id,
          attempt: payload.attempt,
          generation: payload.generation,
          claim_id: payload.claim_id,
          worker_identity_digest: payload.worker_identity_digest,
          request,
          request_digest: payload.request_digest,
          state: accepted ? "answered" : intent ? "unknown" : "pending",
          ...intent ? { reply_id: intent.evidence.reply_id, answer_digest: intent.evidence.answer_digest } : {},
          ...accepted ? { answer: JSON.parse(payload.answer_json), ack_digest: accepted.evidence.ack_digest } : {}
        };
      }
      /** Persist reply intent before any channel write. An intent without accepted ack is never replayed. */
      beginInteractionReply(input) {
        this.#assertWritable();
        if (!validInteractionReplyInput(input)) fail2("invalid_interaction_reply");
        return this.#transaction(() => {
          const task = this.#db.prepare("SELECT status,current_attempt FROM tasks WHERE task_id=?").get(input.task_id);
          if (!task) fail2("task_not_found");
          const o = this.#db.prepare("SELECT * FROM manager_operations WHERE operation_kind='attempt_lifecycle' AND task_id=? AND attempt=?").get(input.task_id, task.current_attempt);
          if (!o) fail2("interaction_operation_missing");
          const p = this.#db.prepare("SELECT * FROM manager_interaction_payloads WHERE operation_id=? AND request_id=?").get(o.operation_id, input.request_id);
          if (!p) fail2("interaction_request_not_found");
          const ev = this.#db.prepare("SELECT * FROM manager_operation_events WHERE operation_id=? AND event_type='interaction_requested' AND json_extract(evidence_json,'$.request_id')=?").get(o.operation_id, input.request_id);
          if (!ev || ev.evidence_digest !== digest(ev.evidence_json) || JSON.parse(ev.evidence_json).request_digest !== p.request_digest) fail2("interaction_history_mismatch");
          const previous = this.#db.prepare("SELECT event_type,evidence_json FROM manager_operation_events WHERE operation_id=? AND json_extract(evidence_json,'$.request_id')=? AND event_type IN ('interaction_reply_intent','interaction_reply_accepted') ORDER BY sequence").all(o.operation_id, input.request_id);
          if (previous.some((e) => e.event_type === "interaction_reply_accepted")) fail2("interaction_already_answered");
          if (previous.some((e) => e.event_type === "interaction_reply_intent")) fail2("interaction_reply_outcome_unknown");
          if (task.status !== "running" || o.phase !== "running" || o.task_id !== p.task_id || o.attempt !== p.attempt || o.generation !== p.generation || o.claim_id !== p.claim_id || o.claim_worker_identity_digest !== p.worker_identity_digest) fail2("stale_interaction_identity");
          this.#assertRecoveryNotLatched(o.operation_id);
          this.#assertNoCancellationIntent(o.operation_id);
          this.#assertInteractionRunning(o, {
            task_id: p.task_id,
            attempt: p.attempt,
            generation: p.generation,
            claim_id: p.claim_id,
            claim_worker_identity_digest: p.worker_identity_digest,
            worker_identity_digest: p.worker_identity_digest
          });
          const request = JSON.parse(p.request_json);
          const answer = buildInteractionAnswer(request, input);
          const answerJson = interactionCanonical(answer);
          if (Buffer.byteLength(answerJson, "utf8") > 2e4) fail2("interaction_answer_too_large");
          const answerDigest = interactionDigest({
            interaction_reply_contract_version: 1,
            operation_id: o.operation_id,
            task_id: o.task_id,
            attempt: o.attempt,
            generation: o.generation,
            claim_id: o.claim_id,
            worker_identity_digest: o.claim_worker_identity_digest,
            request_id: input.request_id,
            answer
          });
          const replyId = randomUUID();
          const changed = this.#db.prepare("UPDATE manager_operations SET revision=revision+1 WHERE operation_id=? AND task_id=? AND attempt=? AND generation=? AND phase='running' AND revision=? AND claim_id=? AND claim_generation=? AND claim_worker_identity_digest=?").run(o.operation_id, o.task_id, o.attempt, o.generation, o.revision, o.claim_id, o.generation, o.claim_worker_identity_digest);
          if (changed.changes !== 1) fail2("stale_interaction_cas");
          const saved = this.#db.prepare("UPDATE manager_interaction_payloads SET answer_json=?,answer_digest=?,reply_id=? WHERE operation_id=? AND request_id=? AND answer_json IS NULL").run(answerJson, answerDigest, replyId, o.operation_id, input.request_id);
          if (saved.changes !== 1) fail2("interaction_reply_conflict");
          this.#faultPoint("after_projection");
          this.#event(
            o.operation_id,
            o.revision + 1,
            "interaction_reply_intent",
            "running",
            "running",
            o.generation,
            { answer_digest: answerDigest, claim_id: o.claim_id, reply_id: replyId, request_id: input.request_id, worker_identity_digest: o.claim_worker_identity_digest },
            (/* @__PURE__ */ new Date()).toISOString()
          );
          return {
            operation_id: o.operation_id,
            task_id: o.task_id,
            attempt: o.attempt,
            generation: o.generation,
            claim_id: o.claim_id,
            worker_identity_digest: o.claim_worker_identity_digest,
            request_id: input.request_id,
            reply_id: replyId,
            answer,
            answer_digest: answerDigest,
            process_id: JSON.parse(o.claim_worker_identity_json).process_id,
            start_fingerprint: JSON.parse(o.claim_worker_identity_json).start_fingerprint,
            revision: o.revision + 1,
            event_sequence: o.revision + 1
          };
        });
      }
      /** Persist the Worker prepared acknowledgement and the one-way commit fact
       * before allowing the caller to send the commit frame. */
      commitInteractionReply(preparedAck) {
        this.#assertWritable();
        if (!isCandidateInteractionPreparedAcknowledgement(preparedAck) || !validInteractionPreparedAcknowledgement(preparedAck)) fail2("invalid_interaction_prepared_ack");
        return this.#transaction(() => {
          const o = this.#attemptOperation({ ...preparedAck, expected_revision: preparedAck.revision });
          const p = this.#db.prepare("SELECT * FROM manager_interaction_payloads WHERE operation_id=? AND request_id=?").get(o.operation_id, preparedAck.request_id);
          const intent = this.#db.prepare("SELECT * FROM manager_operation_events WHERE operation_id=? AND event_type='interaction_reply_intent' AND json_extract(evidence_json,'$.request_id')=?").get(o.operation_id, preparedAck.request_id);
          if (!p || !intent) fail2("interaction_reply_intent_missing");
          const ie = JSON.parse(intent.evidence_json);
          if (p.reply_id !== preparedAck.reply_id || p.answer_digest !== preparedAck.answer_digest || ie.reply_id !== preparedAck.reply_id || ie.answer_digest !== preparedAck.answer_digest || o.claim_id !== preparedAck.claim_id || o.claim_worker_identity_digest !== preparedAck.worker_identity_digest || o.claim_generation !== o.generation || o.phase !== "running" || o.revision !== intent.sequence || preparedAck.revision !== intent.sequence || preparedAck.process_id !== JSON.parse(o.claim_worker_identity_json).process_id || preparedAck.start_fingerprint !== JSON.parse(o.claim_worker_identity_json).start_fingerprint) fail2("interaction_prepared_ack_identity_mismatch");
          const events = this.#db.prepare("SELECT event_type FROM manager_operation_events WHERE operation_id=? AND json_extract(evidence_json,'$.request_id')=? AND event_type IN ('interaction_reply_prepared','interaction_reply_committed','interaction_reply_accepted')").all(o.operation_id, preparedAck.request_id);
          if (events.length) fail2("interaction_reply_outcome_unknown");
          this.#assertRecoveryNotLatched(o.operation_id);
          this.#assertNoCancellationIntent(o.operation_id);
          for (const [offset, eventType, evidence] of [
            [1, "interaction_reply_prepared", {
              answer_digest: p.answer_digest,
              claim_id: o.claim_id,
              prepared_digest: preparedAck.ack_digest,
              reply_id: p.reply_id,
              request_id: p.request_id,
              worker_identity_digest: o.claim_worker_identity_digest
            }],
            [2, "interaction_reply_committed", {
              answer_digest: p.answer_digest,
              claim_id: o.claim_id,
              commit_digest: "",
              prepared_digest: preparedAck.ack_digest,
              reply_id: p.reply_id,
              request_id: p.request_id,
              worker_identity_digest: o.claim_worker_identity_digest
            }]
          ]) {
            const changed = this.#db.prepare("UPDATE manager_operations SET revision=revision+1 WHERE operation_id=? AND task_id=? AND attempt=? AND generation=? AND phase='running' AND revision=? AND claim_id=? AND claim_generation=? AND claim_worker_identity_digest=?").run(o.operation_id, o.task_id, o.attempt, o.generation, o.revision + offset - 1, o.claim_id, o.generation, o.claim_worker_identity_digest);
            if (changed.changes !== 1) fail2("stale_interaction_prepared_ack");
            if (eventType === "interaction_reply_committed") evidence.commit_digest = interactionCommitDigest(
              {
                operation_id: o.operation_id,
                task_id: o.task_id,
                attempt: o.attempt,
                generation: o.generation,
                claim_id: o.claim_id,
                worker_identity_digest: o.claim_worker_identity_digest
              },
              { request_id: p.request_id, reply_id: p.reply_id, revision: o.revision + offset, answer_digest: p.answer_digest, prepared_digest: preparedAck.ack_digest }
            );
            this.#event(o.operation_id, o.revision + offset, eventType, "running", "running", o.generation, evidence, (/* @__PURE__ */ new Date()).toISOString());
          }
          return {
            state: "committed",
            operation_id: o.operation_id,
            task_id: o.task_id,
            attempt: o.attempt,
            generation: o.generation,
            claim_id: o.claim_id,
            worker_identity_digest: o.claim_worker_identity_digest,
            process_id: preparedAck.process_id,
            start_fingerprint: preparedAck.start_fingerprint,
            request_id: p.request_id,
            reply_id: p.reply_id,
            answer_digest: p.answer_digest,
            prepared_digest: preparedAck.ack_digest,
            commit_digest: JSON.parse(this.#db.prepare("SELECT evidence_json FROM manager_operation_events WHERE operation_id=? AND event_type='interaction_reply_committed' AND json_extract(evidence_json,'$.request_id')=?").get(o.operation_id, p.request_id).evidence_json).commit_digest,
            revision: o.revision + 2
          };
        });
      }
      /** Confirm only an ack already validated by the bound private Worker channel. */
      completeInteractionReply(input) {
        this.#assertWritable();
        if (!isCandidateInteractionAcknowledgement(input) || !validInteractionAcknowledgement(input)) fail2("invalid_interaction_ack");
        return this.#transaction(() => {
          const o = this.#attemptOperation({ ...input, expected_revision: input.revision });
          this.#assertRecoveryNotLatched(o.operation_id);
          this.#assertNoCancellationIntent(o.operation_id);
          const p = this.#db.prepare("SELECT * FROM manager_interaction_payloads WHERE operation_id=? AND request_id=?").get(o.operation_id, input.request_id);
          const intent = this.#db.prepare("SELECT * FROM manager_operation_events WHERE operation_id=? AND event_type='interaction_reply_intent' AND json_extract(evidence_json,'$.request_id')=?").get(o.operation_id, input.request_id);
          const committed = this.#db.prepare("SELECT * FROM manager_operation_events WHERE operation_id=? AND event_type='interaction_reply_committed' AND json_extract(evidence_json,'$.request_id')=?").get(o.operation_id, input.request_id);
          if (!p || !intent) fail2("interaction_reply_intent_missing");
          const evidence = JSON.parse(intent.evidence_json);
          if (evidence.reply_id !== input.reply_id || evidence.answer_digest !== input.answer_digest || evidence.claim_id !== input.claim_id || evidence.worker_identity_digest !== input.worker_identity_digest || p.reply_id !== input.reply_id || p.answer_digest !== input.answer_digest || o.claim_id !== input.claim_id || o.claim_worker_identity_digest !== input.worker_identity_digest || !committed || JSON.parse(committed.evidence_json).commit_digest !== input.commit_digest) fail2("interaction_ack_identity_mismatch");
          const priorAccepted = this.#db.prepare("SELECT * FROM manager_operation_events WHERE operation_id=? AND event_type='interaction_reply_accepted' AND json_extract(evidence_json,'$.request_id')=?").get(o.operation_id, input.request_id);
          if (priorAccepted) {
            const priorEvidence = JSON.parse(priorAccepted.evidence_json);
            if (priorEvidence.ack_digest !== input.ack_digest || priorAccepted.evidence_digest !== digest(priorAccepted.evidence_json)) fail2("interaction_ack_conflict");
            return {
              duplicate: true,
              task_id: o.task_id,
              request_id: input.request_id,
              reply_id: p.reply_id,
              answer_digest: p.answer_digest,
              state: "answered",
              operation_id: o.operation_id,
              generation: o.generation,
              revision: priorAccepted.sequence
            };
          }
          if (o.phase !== "running" || o.revision !== input.revision) fail2("stale_interaction_ack");
          const changed = this.#db.prepare("UPDATE manager_operations SET revision=revision+1 WHERE operation_id=? AND task_id=? AND attempt=? AND generation=? AND phase='running' AND revision=? AND claim_id=? AND claim_generation=? AND claim_worker_identity_digest=?").run(o.operation_id, o.task_id, o.attempt, o.generation, o.revision, o.claim_id, o.generation, o.claim_worker_identity_digest);
          if (changed.changes !== 1) fail2("stale_interaction_ack");
          this.#faultPoint("after_projection");
          this.#event(
            o.operation_id,
            o.revision + 1,
            "interaction_reply_accepted",
            "running",
            "running",
            o.generation,
            {
              ack_digest: input.ack_digest,
              answer_digest: p.answer_digest,
              claim_id: o.claim_id,
              commit_digest: input.commit_digest,
              reply_id: input.reply_id,
              request_id: input.request_id,
              worker_identity_digest: o.claim_worker_identity_digest
            },
            (/* @__PURE__ */ new Date()).toISOString()
          );
          return {
            duplicate: false,
            task_id: o.task_id,
            request_id: input.request_id,
            reply_id: p.reply_id,
            answer_digest: p.answer_digest,
            state: "answered",
            operation_id: o.operation_id,
            generation: o.generation,
            revision: o.revision + 1
          };
        });
      }
      /** Atomically persist a queued continuation Attempt without reserving lifecycle Capacity. */
      createNextAttempt(input, { workspaceValidator, executionPermissionCheck } = {}) {
        this.#assertWritable();
        const operationId = input?.operation_id === void 0 ? randomUUID() : input.operation_id;
        if (!validId(operationId) || operationId !== operationId.trim() || !validId(input?.task_id) || typeof input?.feedback !== "string" || !input.feedback.trim() || input.additional_requirements !== void 0 && (!Array.isArray(input.additional_requirements) || input.additional_requirements.some((value) => typeof value !== "string"))) fail2("invalid_continue_request");
        const additionalRequirements = input.additional_requirements ?? [];
        const publicRequest = { task_id: input.task_id, feedback: input.feedback, additional_requirements: additionalRequirements };
        const publicRequestJson = canonical3(publicRequest);
        if (Buffer.byteLength(publicRequestJson, "utf8") > 1048576) fail2("continue_request_too_large");
        const duplicateReceipt = (priorAttempt) => {
          if (priorAttempt.task_id !== input.task_id) fail2("continue_operation_conflict");
          let stored;
          try {
            stored = JSON.parse(priorAttempt.continuation_json);
          } catch {
            fail2("continue_history_mismatch");
          }
          if (!stored || Object.getPrototypeOf(stored) !== Object.prototype || priorAttempt.continuation_operation_id !== operationId || priorAttempt.continuation_digest !== digest(priorAttempt.continuation_json) || stored.contract !== "wp6b2b-continue-v1" || stored.operation_id !== operationId || stored.task_id !== priorAttempt.task_id) fail2("continue_history_mismatch");
          if (canonical3({ task_id: stored.task_id, feedback: stored.feedback, additional_requirements: stored.additional_requirements }) !== publicRequestJson)
            fail2("continue_operation_conflict");
          return {
            duplicate: true,
            operation_id: operationId,
            task_id: input.task_id,
            attempt: priorAttempt.attempt,
            status: "queued",
            created_at: priorAttempt.created_at,
            owner_binding: this.#ownerBinding(input.task_id)
          };
        };
        const existing = this.#readConsistent(() => {
          const priorAttempt = this.#db.prepare("SELECT task_id,attempt,continuation_operation_id,continuation_json,continuation_digest,created_at FROM attempts WHERE continuation_operation_id=?").get(operationId);
          return priorAttempt ? duplicateReceipt(priorAttempt) : null;
        });
        if (existing) return existing;
        if (!Number.isSafeInteger(input.previous_attempt) || input.previous_attempt < 1 || !validId(input.previous_operation_id) || !Number.isSafeInteger(input.expected_generation) || input.expected_generation < 1 || !Number.isSafeInteger(input.expected_revision) || input.expected_revision < 1 || !validId(input.claim_id) || typeof input.claim_worker_identity_digest !== "string" || !/^[0-9a-f]{64}$/u.test(input.claim_worker_identity_digest))
          fail2("continue_cas_required");
        const continuation = {
          contract: "wp6b2b-continue-v1",
          operation_id: operationId,
          task_id: input.task_id,
          feedback: input.feedback,
          additional_requirements: additionalRequirements,
          previous_attempt: input.previous_attempt,
          previous_operation_id: input.previous_operation_id,
          previous_generation: input.expected_generation,
          previous_revision: input.expected_revision,
          previous_claim_id: input.claim_id,
          previous_worker_identity_digest: input.claim_worker_identity_digest
        };
        const continuationJson = canonical3(continuation);
        if (Buffer.byteLength(continuationJson, "utf8") > 1048576) fail2("continue_request_too_large");
        const continuationDigest = digest(continuationJson);
        const prior = this.readOperation(input.previous_operation_id);
        if (!prior) fail2("continue_prior_operation_missing");
        const task = this.readTask(input.task_id);
        if (!task) fail2("task_not_found");
        const workspace = validateWorkspace(prior.workspace_ref, workspaceValidator);
        if (workspace !== prior.workspace_ref) fail2("continue_workspace_mismatch");
        const permission = callDecision(executionPermissionCheck, workspace, { operation_id: operationId, task_id: input.task_id, attempt: input.previous_attempt + 1, task });
        if (permission.state !== "allow") fail2(permission.state === "deny" ? "execution_permission_denied" : "execution_permission_unknown");
        const createdAt = (/* @__PURE__ */ new Date()).toISOString();
        return this.#transaction(() => {
          const raced = this.#db.prepare("SELECT task_id,attempt,continuation_operation_id,continuation_json,continuation_digest,created_at FROM attempts WHERE continuation_operation_id=?").get(operationId);
          if (raced) return duplicateReceipt(raced);
          const taskRow = this.#db.prepare("SELECT task_id,status,current_attempt FROM tasks WHERE task_id=?").get(input.task_id);
          const previousAttempt = this.#db.prepare("SELECT task_id,attempt,generation,status FROM attempts WHERE task_id=? AND attempt=?").get(input.task_id, input.previous_attempt);
          const previous = this.#db.prepare("SELECT * FROM manager_operations WHERE operation_id=? AND operation_kind='attempt_lifecycle'").get(input.previous_operation_id);
          if (!taskRow || !previousAttempt || !previous || previous.task_id !== input.task_id || previous.attempt !== input.previous_attempt || taskRow.current_attempt !== input.previous_attempt || previousAttempt.generation !== input.expected_generation || previous.revision < input.expected_revision || previous.claim_id !== input.claim_id || previous.revision > input.expected_revision && !this.#db.prepare("SELECT 1 FROM manager_operation_events WHERE operation_id=? AND event_type='released' AND sequence=?").get(previous.operation_id, input.expected_revision) || previous.claim_generation !== input.expected_generation || previous.claim_worker_identity_digest !== input.claim_worker_identity_digest)
            fail2("stale_continue_cas");
          const eligible = /* @__PURE__ */ new Set(["completed", "failed", "waiting_for_master"]);
          if (!eligible.has(taskRow.status) || taskRow.status !== previousAttempt.status || taskRow.status !== previous.result_status)
            fail2(taskRow.status === "cancelled" ? "continue_cancelled_not_supported" : "continue_status_not_eligible");
          if (previous.phase !== "released" || !previous.result_digest || !previous.result_commit_ref || !previous.claim_id || !this.#db.prepare("SELECT 1 FROM manager_operation_events WHERE operation_id=? AND event_type='released' AND sequence<=?").get(previous.operation_id, input.expected_revision))
            fail2("continue_prior_not_released");
          this.#assertRecoveryNotLatched(previous.operation_id);
          const nextAttempt = input.previous_attempt + 1;
          const changedTask = this.#db.prepare("UPDATE tasks SET status='queued',current_attempt=? WHERE task_id=? AND current_attempt=? AND status=?").run(nextAttempt, input.task_id, input.previous_attempt, taskRow.status);
          if (changedTask.changes !== 1) fail2("stale_continue_cas");
          const insertedAttempt = this.#db.prepare("INSERT INTO attempts(task_id,attempt,generation,status,created_at,continuation_operation_id,continuation_json,continuation_digest) VALUES(?,?,NULL,'queued',?,?,?,?)").run(input.task_id, nextAttempt, createdAt, operationId, continuationJson, continuationDigest);
          if (insertedAttempt.changes !== 1) fail2("continue_attempt_conflict");
          this.#faultPoint("after_projection");
          return {
            duplicate: false,
            operation_id: operationId,
            task_id: input.task_id,
            attempt: nextAttempt,
            status: "queued",
            created_at: createdAt,
            owner_binding: this.#ownerBinding(input.task_id)
          };
        });
      }
      /**
       * Atomically turn a claimed, Result-less Attempt into preserved interruption
       * history, release its occupancy after externally verified Worker cleanup,
       * and create exactly one queued next Attempt. The caller supplies process
       * tree/resource digests only after exact identity exit and claimant closure.
       */
      interruptAndRequeue(input, { workspaceValidator, executionPermissionCheck } = {}) {
        this.#assertWritable();
        const keys = [
          "adapter_cleanup",
          "attempt",
          "claim_id",
          "claim_worker_identity_digest",
          "continuation_operation_id",
          "generation",
          "interruption_evidence",
          "operation_id",
          "process_tree_digest",
          "reason",
          "resources_digest",
          "revision",
          "task_id"
        ];
        const interruptions = /* @__PURE__ */ new Set(["interrupted_by_upgrade", "worker_exited_without_result", "worker_terminated_without_result"]);
        if (!input || Object.getPrototypeOf(input) !== Object.prototype || Object.keys(input).some((key) => !keys.includes(key)) || !validId(input.operation_id) || !validId(input.task_id) || !Number.isSafeInteger(input.attempt) || input.attempt < 1 || !Number.isSafeInteger(input.generation) || input.generation < 1 || !Number.isSafeInteger(input.revision) || input.revision < 1 || !validId(input.claim_id) || typeof input.claim_worker_identity_digest !== "string" || !/^[0-9a-f]{64}$/u.test(input.claim_worker_identity_digest) || !validId(input.continuation_operation_id) || !interruptions.has(input.reason) || !input.interruption_evidence || Object.getPrototypeOf(input.interruption_evidence) !== Object.prototype || input.interruption_evidence.reason !== input.reason || !validVerifiedAdapterCleanupEvidence(input.adapter_cleanup) || typeof input.process_tree_digest !== "string" || !/^[0-9a-f]{64}$/u.test(input.process_tree_digest) || typeof input.resources_digest !== "string" || !/^[0-9a-f]{64}$/u.test(input.resources_digest)) fail2("invalid_interruption_request");
        const interruptionJson = canonical3(input.interruption_evidence);
        if (Buffer.byteLength(interruptionJson, "utf8") > 4096) fail2("invalid_interruption_evidence");
        const interruptionDigest = digest(interruptionJson);
        const nextAttemptNumber = input.attempt + 1;
        const createdAt = (/* @__PURE__ */ new Date()).toISOString();
        const result = {
          task_id: input.task_id,
          attempt: input.attempt,
          status: "failed",
          summary: `Worker execution was interrupted (${input.reason}); the previous Attempt is retained and a new Attempt is queued.`,
          files_changed: [],
          tests: [],
          issues: [`interruption_evidence:${interruptionDigest}`],
          needs_master_decision: false,
          zcode_output: "",
          exit_code: null,
          session_id: null,
          started_at: null,
          finished_at: createdAt,
          error_code: input.reason
        };
        const resultJson = canonicalTaskResult2(result, { task_id: input.task_id, attempt: input.attempt, result_status: "failed" });
        const resultDigest = digest({ result_contract_version: RESULT_CONTRACT_VERSION, result_status: "failed", result });
        const resultCommitRef = `result-${resultDigest}`;
        const previousReleasedRevision = input.revision + 5;
        const continuation = {
          contract: "wp6b2b-continue-v1",
          operation_id: input.continuation_operation_id,
          task_id: input.task_id,
          feedback: `Automatic recovery after ${input.reason}.`,
          additional_requirements: [],
          previous_attempt: input.attempt,
          previous_operation_id: input.operation_id,
          previous_generation: input.generation,
          previous_revision: previousReleasedRevision,
          previous_claim_id: input.claim_id,
          previous_worker_identity_digest: input.claim_worker_identity_digest
        };
        const continuationJson = canonical3(continuation);
        const continuationDigest = digest(continuationJson);
        const priorOperation = this.readOperation(input.operation_id);
        if (!priorOperation) fail2("operation_not_found");
        if (priorOperation.task_id !== input.task_id || priorOperation.attempt !== input.attempt || priorOperation.generation !== input.generation || priorOperation.claim_id !== input.claim_id || priorOperation.claim_worker_identity_digest !== input.claim_worker_identity_digest) fail2("interruption_identity_mismatch");
        const workspace = validateWorkspace(priorOperation.workspace_ref, workspaceValidator);
        if (workspace !== priorOperation.workspace_ref) fail2("interruption_workspace_mismatch");
        const task = this.readTask(input.task_id);
        if (!task) fail2("task_not_found");
        const permission = callDecision(executionPermissionCheck, workspace, {
          operation_id: input.continuation_operation_id,
          task_id: input.task_id,
          attempt: nextAttemptNumber,
          task
        });
        if (permission.state !== "allow") fail2(permission.state === "deny" ? "execution_permission_denied" : "execution_permission_unknown");
        return this.#transaction(() => {
          const existing = this.#db.prepare("SELECT * FROM attempts WHERE continuation_operation_id=?").get(input.continuation_operation_id);
          if (existing) {
            let stored;
            try {
              stored = JSON.parse(existing.continuation_json);
            } catch {
              fail2("continue_history_mismatch");
            }
            const prior = this.#db.prepare("SELECT * FROM manager_operations WHERE operation_id=? AND operation_kind='attempt_lifecycle'").get(input.operation_id);
            let priorResult;
            try {
              priorResult = prior?.result_json === null ? null : JSON.parse(prior?.result_json);
            } catch {
              fail2("interruption_requeue_conflict");
            }
            const issue = Array.isArray(priorResult?.issues) ? priorResult.issues.find((value) => typeof value === "string" && value.startsWith("interruption_evidence:")) : null;
            const storedEvidenceDigest = issue?.slice("interruption_evidence:".length);
            if (existing.task_id !== input.task_id || existing.attempt !== nextAttemptNumber || existing.continuation_digest !== digest(existing.continuation_json) || stored?.operation_id !== input.continuation_operation_id || stored?.previous_operation_id !== input.operation_id || stored?.previous_attempt !== input.attempt || stored?.previous_generation !== input.generation || stored?.previous_claim_id !== input.claim_id || stored?.previous_worker_identity_digest !== input.claim_worker_identity_digest || !prior || prior.phase !== "released" || prior.result_status !== "failed" || prior.result_digest === null || prior.result_json === null || priorResult?.error_code !== input.reason || typeof storedEvidenceDigest !== "string" || !/^[0-9a-f]{64}$/u.test(storedEvidenceDigest) || !this.#db.prepare("SELECT 1 FROM manager_operation_events WHERE operation_id=? AND event_type='observation_recorded' AND json_extract(evidence_json,'$.reason')=? AND json_extract(evidence_json,'$.evidence_digest')=?").get(input.operation_id, input.reason, storedEvidenceDigest) || !Number.isSafeInteger(stored?.previous_revision) || prior.revision < stored.previous_revision || !this.#db.prepare("SELECT 1 FROM manager_operation_events WHERE operation_id=? AND event_type='released' AND sequence=?").get(input.operation_id, stored.previous_revision))
              fail2("interruption_requeue_conflict");
            const cleanupEvent = this.#db.prepare("SELECT evidence_json FROM manager_operation_events WHERE operation_id=? AND event_type='cleanup_verified'").get(input.operation_id);
            let cleanupEvidence2;
            try {
              cleanupEvidence2 = JSON.parse(cleanupEvent?.evidence_json);
            } catch {
              fail2("interruption_requeue_conflict");
            }
            if (cleanupEvidence2?.claim_id !== input.claim_id || cleanupEvidence2?.worker_identity_digest !== input.claim_worker_identity_digest || !validVerifiedAdapterCleanupEvidence(cleanupEvidence2?.adapter_cleanup) || canonical3(cleanupEvidence2.adapter_cleanup) !== canonical3(input.adapter_cleanup) || typeof cleanupEvidence2?.cleanup_digest !== "string" || !/^[0-9a-f]{64}$/u.test(cleanupEvidence2.cleanup_digest))
              fail2("interruption_requeue_conflict");
            return {
              duplicate: true,
              operation_id: input.operation_id,
              task_id: input.task_id,
              previous_attempt: input.attempt,
              attempt: existing.attempt,
              next_operation_id: input.continuation_operation_id,
              status: "queued",
              created_at: existing.created_at,
              result_digest: prior.result_digest,
              cleanup_digest: cleanupEvidence2.cleanup_digest,
              interruption_reason: input.reason,
              evidence_digest: storedEvidenceDigest
            };
          }
          const previous = this.#db.prepare("SELECT * FROM manager_operations WHERE operation_id=? AND operation_kind='attempt_lifecycle'").get(input.operation_id);
          const taskRow = this.#db.prepare("SELECT task_id,status,current_attempt FROM tasks WHERE task_id=?").get(input.task_id);
          const previousAttempt = this.#db.prepare("SELECT task_id,attempt,generation,status FROM attempts WHERE task_id=? AND attempt=?").get(input.task_id, input.attempt);
          if (!previous || !taskRow || !previousAttempt || previous.task_id !== input.task_id || previous.attempt !== input.attempt || previous.generation !== input.generation || previous.revision !== input.revision || previous.claim_id !== input.claim_id || previous.claim_generation !== input.generation || previous.claim_worker_identity_digest !== input.claim_worker_identity_digest || previous.phase !== "running" || previous.result_digest !== null || previous.result_json !== null || previous.result_status !== null || previousAttempt.generation !== input.generation || previousAttempt.status !== "running" || taskRow.current_attempt !== input.attempt || taskRow.status !== "running") fail2("stale_interruption_cas");
          this.#assertNoUnansweredInteraction(input.operation_id);
          this.#assertNoCancellationIntent(input.operation_id);
          let worker, launch;
          try {
            worker = JSON.parse(previous.claim_worker_identity_json);
            launch = JSON.parse(previous.launch_identity_json);
          } catch {
            fail2("interruption_worker_identity_invalid");
          }
          fixtureWorkerIdentity(worker);
          fixtureLaunchIdentity(launch);
          if (worker.source !== "manager_verified_process_probe" || worker.fixture !== false || launch.source !== "manager_os_spawn_observation" || launch.fixture !== false || worker.platform !== "win32" || launch.platform !== "win32" || worker.fingerprint_precision !== "exact" || launch.fingerprint_precision !== "exact" || worker.process_id !== launch.process_id || worker.start_fingerprint !== launch.start_fingerprint || digest(canonical3(worker)) !== input.claim_worker_identity_digest) fail2("interruption_worker_identity_mismatch");
          if (previous.launch_receipt_digest === null) fail2("interruption_launch_receipt_missing");
          const cleanupEvidence = {
            source: "manager_os_cleanup_verification",
            fixture: false,
            operation_id: input.operation_id,
            task_id: input.task_id,
            attempt: input.attempt,
            generation: input.generation,
            claim_id: input.claim_id,
            worker_identity_digest: input.claim_worker_identity_digest,
            launch_receipt_digest: previous.launch_receipt_digest,
            result_commit_ref: resultCommitRef,
            process_tree_digest: input.process_tree_digest,
            resources_digest: input.resources_digest,
            root_process_id: worker.process_id,
            root_start_fingerprint: worker.start_fingerprint,
            worker_tree_complete: true,
            operation_resources_complete: true,
            workspace_touched: false,
            adapter_cleanup: input.adapter_cleanup
          };
          const normalized = normalizeCleanupEvidence(cleanupEvidence, {
            operation_id: input.operation_id,
            task_id: input.task_id,
            attempt: input.attempt,
            generation: input.generation,
            claim_id: input.claim_id,
            claim_worker_identity_digest: input.claim_worker_identity_digest
          });
          const cleanupDigest = digest({ cleanup_contract_version: 1, evidence: normalized });
          const at = createdAt;
          const observation = { reason: input.reason, evidence_digest: interruptionDigest };
          let revision = input.revision;
          let changed = this.#db.prepare("UPDATE manager_operations SET revision=revision+1 WHERE operation_id=? AND task_id=? AND attempt=? AND generation=? AND phase='running' AND revision=? AND claim_id=? AND claim_generation=? AND claim_worker_identity_digest=? AND result_digest IS NULL").run(input.operation_id, input.task_id, input.attempt, input.generation, revision, input.claim_id, input.generation, input.claim_worker_identity_digest);
          if (changed.changes !== 1) fail2("stale_interruption_cas");
          this.#faultPoint("after_projection");
          this.#event(input.operation_id, revision + 1, "observation_recorded", "running", "running", input.generation, observation, at);
          revision += 1;
          changed = this.#db.prepare("UPDATE manager_operations SET phase='result_committed',revision=revision+1,result_status='failed',result_generation=?,result_digest=?,result_json=?,result_commit_ref=? WHERE operation_id=? AND task_id=? AND attempt=? AND generation=? AND phase='running' AND revision=? AND claim_id=? AND claim_generation=? AND claim_worker_identity_digest=? AND result_digest IS NULL").run(input.generation, resultDigest, resultJson, resultCommitRef, input.operation_id, input.task_id, input.attempt, input.generation, revision, input.claim_id, input.generation, input.claim_worker_identity_digest);
          if (changed.changes !== 1) fail2("stale_interruption_cas");
          const attemptChanged = this.#db.prepare("UPDATE attempts SET status='failed' WHERE task_id=? AND attempt=? AND generation=? AND status='running'").run(input.task_id, input.attempt, input.generation);
          const taskChanged = this.#db.prepare("UPDATE tasks SET status='failed' WHERE task_id=? AND current_attempt=? AND status='running'").run(input.task_id, input.attempt);
          if (attemptChanged.changes !== 1 || taskChanged.changes !== 1) fail2("interruption_projection_cas");
          this.#event(
            input.operation_id,
            revision + 1,
            "result_committed",
            "running",
            "result_committed",
            input.generation,
            {
              claim_id: input.claim_id,
              outcome: "failed",
              result_commit_ref: resultCommitRef,
              result_digest: resultDigest,
              worker_identity_digest: input.claim_worker_identity_digest
            },
            at
          );
          revision += 1;
          changed = this.#db.prepare("UPDATE manager_operations SET phase='cleanup_pending',revision=revision+1 WHERE operation_id=? AND phase='result_committed' AND revision=? AND result_commit_ref=?").run(input.operation_id, revision, resultCommitRef);
          if (changed.changes !== 1) fail2("stale_interruption_cas");
          this.#event(
            input.operation_id,
            revision + 1,
            "cleanup_pending",
            "result_committed",
            "cleanup_pending",
            input.generation,
            { claim_id: input.claim_id, result_commit_ref: resultCommitRef, worker_identity_digest: input.claim_worker_identity_digest },
            at
          );
          revision += 1;
          changed = this.#db.prepare("UPDATE manager_operations SET phase='cleanup_verified',revision=revision+1 WHERE operation_id=? AND phase='cleanup_pending' AND revision=? AND result_commit_ref=?").run(input.operation_id, revision, resultCommitRef);
          if (changed.changes !== 1) fail2("stale_interruption_cas");
          const cleanupEventEvidence = {
            claim_id: input.claim_id,
            cleanup_digest: cleanupDigest,
            evidence_source: normalized.source,
            launch_receipt_digest: normalized.launch_receipt_digest,
            operation_resources_complete: true,
            process_tree_digest: normalized.process_tree_digest,
            resources_digest: normalized.resources_digest,
            result_commit_ref: resultCommitRef,
            root_process_id: normalized.root_process_id,
            root_start_fingerprint: normalized.root_start_fingerprint,
            worker_identity_digest: input.claim_worker_identity_digest,
            worker_tree_complete: true,
            workspace_touched: false,
            adapter_cleanup: normalized.adapter_cleanup
          };
          this.#event(
            input.operation_id,
            revision + 1,
            "cleanup_verified",
            "cleanup_pending",
            "cleanup_verified",
            input.generation,
            cleanupEventEvidence,
            at
          );
          revision += 1;
          changed = this.#db.prepare("UPDATE manager_operations SET phase='released',revision=revision+1 WHERE operation_id=? AND phase='cleanup_verified' AND revision=? AND result_commit_ref=?").run(input.operation_id, revision, resultCommitRef);
          if (changed.changes !== 1) fail2("stale_interruption_cas");
          this.#event(
            input.operation_id,
            revision + 1,
            "released",
            "cleanup_verified",
            "released",
            input.generation,
            {
              claim_id: input.claim_id,
              cleanup_digest: cleanupDigest,
              result_commit_ref: resultCommitRef,
              worker_identity_digest: input.claim_worker_identity_digest
            },
            at
          );
          revision += 1;
          const queued = this.#db.prepare("UPDATE tasks SET status='queued',current_attempt=? WHERE task_id=? AND current_attempt=? AND status='failed'").run(nextAttemptNumber, input.task_id, input.attempt);
          if (queued.changes !== 1) fail2("interruption_requeue_cas");
          const inserted = this.#db.prepare("INSERT INTO attempts(task_id,attempt,generation,status,created_at,continuation_operation_id,continuation_json,continuation_digest) VALUES(?,?,NULL,'queued',?,?,?,?)").run(input.task_id, nextAttemptNumber, createdAt, input.continuation_operation_id, continuationJson, continuationDigest);
          if (inserted.changes !== 1) fail2("interruption_requeue_conflict");
          return {
            duplicate: false,
            operation_id: input.operation_id,
            task_id: input.task_id,
            previous_attempt: input.attempt,
            attempt: nextAttemptNumber,
            next_operation_id: input.continuation_operation_id,
            status: "queued",
            created_at: createdAt,
            result_digest: resultDigest,
            cleanup_digest: cleanupDigest,
            interruption_reason: input.reason,
            evidence_digest: interruptionDigest
          };
        });
      }
      provisionCapacity({ operation_id, capacity_limit, expected_generation = 0, maintenance }) {
        this.#assertWritable();
        if (!validId(operation_id) || !Number.isInteger(capacity_limit) || capacity_limit < 1 || capacity_limit > 8 || maintenance?.dispatch_blocked !== true || maintenance?.writers_drained !== true) fail2("invalid_maintenance_request");
        return this.#transaction(() => {
          const req = { operation_id, capacity_limit, expected_generation };
          const d = digest(req);
          const old = this.#db.prepare("SELECT * FROM manager_operations WHERE operation_id=?").get(operation_id);
          if (old) {
            if (old.request_digest !== d) fail2("operation_id_conflict");
            return { duplicate: true, operation_id };
          }
          const meta = this.#db.prepare("SELECT * FROM authority_metadata WHERE singleton=1").get();
          if (meta.policy_generation !== expected_generation) fail2("stale_policy_generation");
          const n = this.#db.prepare("SELECT COUNT(*) AS n FROM manager_operations WHERE operation_kind='attempt_lifecycle' AND phase NOT IN ('released','cancelled_before_launch')").get().n;
          if (n !== 0) fail2("active_occupancy");
          const generation = expected_generation + 1;
          const at = (/* @__PURE__ */ new Date()).toISOString();
          this.#db.prepare("INSERT INTO manager_operations(operation_id,operation_kind,request_digest,revision,phase,policy_generation,capacity_limit,created_at) VALUES(?,'capacity_policy_change',?,1,'policy_change_committed',?,?,?)").run(operation_id, d, generation, capacity_limit, at);
          this.#faultPoint("after_projection");
          this.#event(operation_id, 1, "capacity_policy_committed", null, "policy_change_committed", null, { generation, capacity_limit }, at);
          this.#db.prepare("UPDATE authority_metadata SET policy_version=1,policy_generation=?,capacity_limit=?,policy_operation_id=? WHERE singleton=1").run(generation, capacity_limit, operation_id);
          return { duplicate: false, operation_id, generation, capacity_limit };
        });
      }
      assertCapacityPolicy(expected) {
        this.#assertWritable();
        const m = this.#db.prepare("SELECT * FROM authority_metadata WHERE singleton=1").get();
        if (!m || m.policy_version !== 1 || m.policy_generation < 1 || m.capacity_limit !== expected) fail2("capacity_policy_mismatch");
        return { capacity_limit: m.capacity_limit, policy_generation: m.policy_generation };
      }
      admitOperation(input, gates) {
        if (input && Object.hasOwn(input, "generation")) fail2("caller_generation_forbidden");
        return this.#admitOperation(input, gates, false);
      }
      /** Explicitly synthetic compatibility path for inherited fixture-only regressions. */
      admitSyntheticFixtureOperation(input, gates) {
        if (!Number.isSafeInteger(input?.generation) || input.generation < 1) fail2("invalid_fixture_generation");
        return this.#admitOperation(input, gates, true);
      }
      #admitOperation(input, { workspaceValidator, executionPermissionCheck }, fixtureGenerationAuthority) {
        this.#assertWritable();
        const w = validateWorkspace(input?.workspace_ref, workspaceValidator);
        const permission = callDecision(executionPermissionCheck, w, input);
        if (permission.state !== "allow") fail2(permission.state === "deny" ? "execution_permission_denied" : "execution_permission_unknown");
        const requested = { operation_id: input.operation_id, task_id: input.task_id, attempt: input.attempt, workspace_ref: w };
        const fixtureGeneration = fixtureGenerationAuthority ? input.generation : void 0;
        if (!validId(requested.operation_id) || !validId(requested.task_id) || !Number.isInteger(requested.attempt) || requested.attempt < 1 || fixtureGeneration !== void 0 && (!Number.isInteger(fixtureGeneration) || fixtureGeneration < 1)) fail2("invalid_request");
        const d = digest(fixtureGeneration === void 0 ? requested : { ...requested, generation: fixtureGeneration });
        const at = (/* @__PURE__ */ new Date()).toISOString();
        return this.#transaction(() => {
          const prior = this.#db.prepare("SELECT * FROM manager_operations WHERE operation_id=?").get(requested.operation_id);
          if (prior) {
            if (prior.request_digest !== d) fail2("operation_id_conflict");
            return { duplicate: true, operation_id: prior.operation_id, generation: prior.generation, revision: prior.revision, phase: prior.phase };
          }
          const same = this.#db.prepare("SELECT operation_id FROM manager_operations WHERE operation_kind='attempt_lifecycle' AND task_id=? AND attempt=?").get(requested.task_id, requested.attempt);
          if (same) fail2("attempt_already_admitted");
          const occupiedWorkspaces = this.#db.prepare("SELECT workspace_ref FROM manager_operations WHERE operation_kind='attempt_lifecycle' AND phase NOT IN ('released','cancelled_before_launch')").all();
          if (occupiedWorkspaces.some((row2) => typeof row2.workspace_ref === "string" && workspacePathsOverlap(w, row2.workspace_ref))) fail2("workspace_already_occupied");
          const meta = this.#db.prepare("SELECT * FROM authority_metadata WHERE singleton=1").get();
          if (!meta || meta.policy_version !== 1 || meta.policy_generation < 1) fail2("capacity_policy_missing");
          const active = this.#db.prepare("SELECT COUNT(*) AS n FROM manager_operations WHERE operation_kind='attempt_lifecycle' AND phase NOT IN ('released','cancelled_before_launch')").get().n;
          if (active >= meta.capacity_limit) fail2("capacity_exhausted");
          const row = this.#db.prepare("SELECT a.status,a.generation,t.current_attempt FROM attempts a JOIN tasks t ON t.task_id=a.task_id WHERE a.task_id=? AND a.attempt=?").get(requested.task_id, requested.attempt);
          if (!row || row.current_attempt !== requested.attempt || row.status !== "queued") fail2("task_attempt_not_admissible");
          let generation = fixtureGeneration;
          if (generation === void 0) {
            if (row.generation !== null) fail2("attempt_generation_already_assigned");
            const highest = this.#db.prepare("SELECT MAX(generation) AS n FROM attempts WHERE generation IS NOT NULL").get().n ?? 0;
            generation = Math.max(meta.next_generation, highest) + 1;
            const assigned = this.#db.prepare("UPDATE attempts SET generation=? WHERE task_id=? AND attempt=? AND generation IS NULL AND status='queued'").run(generation, requested.task_id, requested.attempt);
            if (assigned.changes !== 1) fail2("attempt_generation_cas_conflict");
            const generationChanged = this.#db.prepare("UPDATE authority_metadata SET next_generation=? WHERE singleton=1 AND next_generation=?").run(generation, meta.next_generation);
            if (generationChanged.changes !== 1) fail2("generation_authority_cas_conflict");
          } else if (row.generation !== generation) fail2("attempt_generation_mismatch");
          const normalized = { ...requested, generation };
          const slot = this.#db.prepare("SELECT n FROM (SELECT 1 AS n UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4 UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8) WHERE n<=? AND n NOT IN (SELECT capacity_slot FROM manager_operations WHERE operation_kind='attempt_lifecycle' AND phase NOT IN ('released','cancelled_before_launch')) ORDER BY n LIMIT 1").get(meta.capacity_limit);
          if (!slot) fail2("capacity_exhausted");
          const reservation_id = randomUUID();
          this.#db.prepare("INSERT INTO manager_operations(operation_id,operation_kind,request_digest,task_id,attempt,generation,reservation_id,revision,phase,capacity_slot,workspace_ref,workspace_identity_json,created_at) VALUES(?,'attempt_lifecycle',?,?,?,?,?,1,'reserved',?,?,NULL,?)").run(normalized.operation_id, d, normalized.task_id, normalized.attempt, normalized.generation, reservation_id, slot.n, w, at);
          this.#faultPoint("after_projection");
          this.#event(normalized.operation_id, 1, "reserved", null, "reserved", normalized.generation, {
            reservation_id,
            capacity_slot: slot.n,
            ...permission.audit ?? {}
          }, at);
          return { duplicate: false, operation_id: normalized.operation_id, reservation_id, revision: 1, event_sequence: 1, capacity_slot: slot.n, phase: "reserved", generation: normalized.generation };
        });
      }
      readOperation(operationId) {
        return this.#readConsistent(() => {
          const row = this.#db.prepare("SELECT * FROM manager_operations WHERE operation_id=?").get(operationId);
          return row ? presentOperation(row, this.#adminAbandonments().get(operationId)) : null;
        });
      }
      readLifecycleEvents(operationId, { afterSequence = 0, limit = 100 } = {}) {
        this.#assertOpen();
        if (!validId(operationId) || !Number.isSafeInteger(afterSequence) || afterSequence < 0 || !Number.isInteger(limit) || limit < 1 || limit > 200) fail2("invalid_event_read");
        return this.#readConsistent(() => {
          if (!this.#db.prepare("SELECT operation_id FROM manager_operations WHERE operation_id=?").get(operationId)) fail2("operation_not_found");
          return this.#db.prepare("SELECT event_cursor,operation_id,sequence,event_type,from_phase,to_phase,generation,evidence_json,evidence_digest,at FROM manager_operation_events WHERE operation_id=? AND sequence>? ORDER BY sequence LIMIT ?").all(operationId, afterSequence, limit);
        });
      }
      /** Read persisted lifecycle facts for one Task across all its Operations and Attempts. */
      readTaskEvents(taskId, { afterCursor = 0, limit = 100 } = {}) {
        this.#assertOpen();
        if (!validId(taskId) || !Number.isSafeInteger(afterCursor) || afterCursor < 0 || !Number.isInteger(limit) || limit < 1 || limit > 200) fail2("invalid_event_read");
        return this.#readConsistent(() => {
          if (!this.#db.prepare("SELECT task_id FROM tasks WHERE task_id=?").get(taskId) || this.#isRetiredHistoricalTask(taskId)) fail2("task_not_found");
          const operationRows = this.#db.prepare(`SELECT e.event_cursor AS cursor,e.event_cursor AS sequence,e.sequence AS operation_sequence,
          e.operation_id,e.event_type,e.from_phase,e.to_phase,e.generation,
          e.evidence_json,e.evidence_digest,e.at,o.task_id,o.attempt AS operation_attempt
        FROM manager_operation_events e JOIN manager_operations o ON o.operation_id=e.operation_id
        WHERE o.operation_kind='attempt_lifecycle' AND o.task_id=? AND e.event_cursor>? ORDER BY e.event_cursor LIMIT ?`).all(taskId, afterCursor, limit + 1);
          const taskCancelRows = this.#db.prepare(`SELECT queued_cancel_event_cursor AS cursor,queued_cancel_event_cursor AS sequence,
          NULL AS operation_sequence,queued_cancel_operation_id AS operation_id,'cancelled' AS event_type,
          NULL AS from_phase,'cancelled' AS to_phase,generation,
          queued_cancel_id,queued_cancel_request_digest,queued_cancelled_at AS at,task_id,attempt AS operation_attempt
        FROM attempts WHERE task_id=? AND queued_cancel_event_cursor>? AND queued_cancel_operation_id IS NULL ORDER BY queued_cancel_event_cursor LIMIT ?`).all(taskId, afterCursor, limit + 1).map((row) => {
            const evidence_json = canonical3({ cancel_id: row.queued_cancel_id, request_digest: row.queued_cancel_request_digest });
            const { queued_cancel_id, queued_cancel_request_digest, ...event } = row;
            return { ...event, evidence_json, evidence_digest: digest(evidence_json) };
          });
          const hasRuntimeEvents = Boolean(this.#db.prepare("SELECT 1 FROM sqlite_schema WHERE type='table' AND name='runtime_task_events'").get());
          const runtimeRows = hasRuntimeEvents ? this.#db.prepare(`SELECT event_cursor AS cursor,event_cursor AS sequence,NULL AS operation_sequence,
          operation_id,event_type,NULL AS from_phase,NULL AS to_phase,generation,
          COALESCE(details_json,'{}') AS evidence_json,COALESCE(details_digest,?) AS evidence_digest,at,task_id,
          attempt AS operation_attempt,summary
        FROM runtime_task_events WHERE task_id=? AND event_cursor>? ORDER BY event_cursor LIMIT ?`).all(digest("{}"), taskId, afterCursor, limit + 1) : [];
          const rows = [...operationRows.map((row) => row.event_type === "cancelled_before_launch" || row.event_type === "observation_recorded" && JSON.parse(row.evidence_json).reason === "cancelled_before_claim" ? { ...row, event_type: "cancelled", from_phase: null, to_phase: "cancelled" } : row), ...taskCancelRows, ...runtimeRows].sort((a, b) => a.cursor - b.cursor).slice(0, limit + 1);
          const hasMore = rows.length > limit;
          const events = hasMore ? rows.slice(0, limit) : rows;
          return { events, nextCursor: events.at(-1)?.cursor ?? afterCursor, hasMore };
        });
      }
      /** Persist one already-sanitized Adapter observation under the Manager's
       * permanent Claim binding. Worker sequence is idempotent within an Operation. */
      appendRuntimeTaskEvent(input) {
        this.#assertWritable();
        const eventTypes = /* @__PURE__ */ new Set(["session_ready", "model_selected", "turn_started", "model_tool_call", "tool_status", "model_output", "turn_completed", "turn_failed", "report_ready"]);
        if (!input || Object.getPrototypeOf(input) !== Object.prototype || !validId(input.operation_id) || !validId(input.task_id) || !Number.isSafeInteger(input.attempt) || input.attempt < 1 || !Number.isSafeInteger(input.generation) || input.generation < 1 || typeof input.claim_id !== "string" || !validId(input.claim_id) || !Number.isSafeInteger(input.worker_sequence) || input.worker_sequence < 1 || !eventTypes.has(input.event_type) || typeof input.at !== "string" || input.at.length > 64 || Number.isNaN(Date.parse(input.at)) || typeof input.summary !== "string" || !input.summary.length || Buffer.byteLength(input.summary, "utf8") > 8192 || input.summary.includes("\0") || input.details !== void 0 && (input.details === null || Object.getPrototypeOf(input.details) !== Object.prototype)) fail2("invalid_runtime_task_event");
        const detailsJson = input.details === void 0 ? null : canonical3(input.details);
        if (detailsJson !== null && Buffer.byteLength(detailsJson, "utf8") > 8192) fail2("runtime_task_event_too_large");
        return this.#transaction(() => {
          const o = this.#attemptOperation(input);
          this.#assertRecoveryNotLatched(o.operation_id);
          if (o.phase !== "running" || o.claim_id !== input.claim_id || o.claim_generation !== o.generation) fail2("runtime_task_event_stale_claim");
          const projection = this.#db.prepare("SELECT t.current_attempt,t.status AS task_status,a.status AS attempt_status,a.generation FROM tasks t JOIN attempts a ON a.task_id=t.task_id AND a.attempt=? WHERE t.task_id=?").get(o.attempt, o.task_id);
          if (!projection || projection.current_attempt !== o.attempt || projection.task_status !== "running" || projection.attempt_status !== "running" || projection.generation !== o.generation) fail2("runtime_task_event_stale_attempt");
          const eventDigest = digest({
            contract: "runtime-task-event-v1",
            operation_id: input.operation_id,
            task_id: input.task_id,
            attempt: input.attempt,
            generation: input.generation,
            claim_id: input.claim_id,
            worker_sequence: input.worker_sequence,
            event_type: input.event_type,
            at: input.at,
            summary: input.summary,
            details: input.details ?? null
          });
          const existing = this.#db.prepare("SELECT * FROM runtime_task_events WHERE operation_id=? AND worker_sequence=?").get(input.operation_id, input.worker_sequence);
          if (existing) {
            const existingDigest = digest({
              contract: "runtime-task-event-v1",
              operation_id: existing.operation_id,
              task_id: existing.task_id,
              attempt: existing.attempt,
              generation: existing.generation,
              claim_id: existing.claim_id,
              worker_sequence: existing.worker_sequence,
              event_type: existing.event_type,
              at: existing.at,
              summary: existing.summary,
              details: existing.details_json === null ? null : JSON.parse(existing.details_json)
            });
            if (existingDigest !== eventDigest) fail2("runtime_task_event_conflict");
            return {
              duplicate: true,
              event_cursor: existing.event_cursor,
              worker_sequence: existing.worker_sequence,
              event_type: existing.event_type
            };
          }
          const count = this.#db.prepare("SELECT COUNT(*) AS n FROM runtime_task_events WHERE operation_id=?").get(o.operation_id).n;
          if (count >= 2e4) fail2("runtime_task_event_limit");
          const eventCursor = this.#nextEventCursor();
          this.#db.prepare(`INSERT INTO runtime_task_events(event_cursor,operation_id,task_id,attempt,generation,claim_id,
        worker_sequence,event_type,at,summary,details_json,details_digest) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)`).run(
            eventCursor,
            o.operation_id,
            o.task_id,
            o.attempt,
            o.generation,
            o.claim_id,
            input.worker_sequence,
            input.event_type,
            input.at,
            input.summary,
            detailsJson,
            detailsJson === null ? null : digest(detailsJson)
          );
          this.#faultPoint("after_runtime_event_insert");
          return { duplicate: false, event_cursor: eventCursor, worker_sequence: input.worker_sequence, event_type: input.event_type };
        });
      }
      /** Read only the imported historical Event rows for one Task. */
      /** Persist cancellation of the current queued Attempt without inventing an Operation or Worker. */
      cancelQueuedAttempt({ task_id, expected_attempt } = {}) {
        this.#assertWritable();
        if (!validId(task_id) || !Number.isSafeInteger(expected_attempt) || expected_attempt < 1) fail2("invalid_queued_cancel");
        const requestDigest = digest({ contract: "wp6a-queued-cancel-v1", task_id, attempt: expected_attempt });
        return this.#transaction(() => {
          const task = this.#db.prepare("SELECT task_id,status,current_attempt FROM tasks WHERE task_id=?").get(task_id);
          if (!task) fail2("task_not_found");
          const attempt = this.#db.prepare("SELECT * FROM attempts WHERE task_id=? AND attempt=?").get(task_id, expected_attempt);
          if (!attempt) fail2("task_attempt_not_found");
          if (attempt.queued_cancel_id !== null) {
            if (attempt.queued_cancel_request_digest !== requestDigest || attempt.status !== "cancelled" || task.status !== "cancelled" || task.current_attempt !== expected_attempt) fail2("queued_cancel_history_mismatch");
            return {
              duplicate: true,
              task_id,
              attempt: expected_attempt,
              status: "cancelled",
              cancel_id: attempt.queued_cancel_id,
              event_cursor: attempt.queued_cancel_event_cursor,
              operation_id: attempt.queued_cancel_operation_id
            };
          }
          if (task.current_attempt !== expected_attempt || task.status !== "queued" || attempt.status !== "queued") fail2("queued_cancel_not_admissible");
          const operation = this.#db.prepare("SELECT * FROM manager_operations WHERE operation_kind='attempt_lifecycle' AND task_id=? AND attempt=?").get(task_id, expected_attempt);
          if (operation && !["reserved", "launch_intent"].includes(operation.phase)) fail2("queued_cancel_operation_not_cancellable");
          if (operation && (operation.generation !== attempt.generation || operation.claim_id !== null || operation.result_digest !== null))
            fail2("queued_cancel_operation_mismatch");
          if (!operation && attempt.generation !== null) fail2("queued_cancel_generation_without_operation");
          const cancelId = randomUUID(), at = (/* @__PURE__ */ new Date()).toISOString(), next = this.#nextEventCursor();
          const result = {
            task_id,
            attempt: expected_attempt,
            status: "cancelled",
            summary: "cancelled by request before the task started",
            files_changed: [],
            tests: [],
            issues: [],
            needs_master_decision: false,
            zcode_output: "",
            exit_code: null,
            session_id: null,
            started_at: null,
            finished_at: at
          };
          canonicalTaskResult2(result, { task_id, attempt: expected_attempt, result_status: "cancelled" });
          const resultJson = canonical3(result), resultDigest = digest(resultJson);
          const changedAttempt = this.#db.prepare("UPDATE attempts SET status='cancelled',queued_cancel_id=?,queued_cancel_request_digest=?,queued_cancel_event_cursor=?,queued_cancelled_at=?,queued_cancel_operation_id=?,queued_cancel_result_digest=?,queued_cancel_result_json=? WHERE task_id=? AND attempt=? AND generation IS ? AND status='queued' AND queued_cancel_id IS NULL").run(cancelId, requestDigest, next, at, operation?.operation_id ?? null, resultDigest, resultJson, task_id, expected_attempt, attempt.generation);
          const changedTask = this.#db.prepare("UPDATE tasks SET status='cancelled' WHERE task_id=? AND current_attempt=? AND status='queued'").run(task_id, expected_attempt);
          if (changedAttempt.changes !== 1 || changedTask.changes !== 1) fail2("queued_cancel_cas_conflict");
          if (operation) {
            if (operation.phase === "launch_intent") {
              const changed = this.#db.prepare("UPDATE manager_operations SET revision=revision+1 WHERE operation_id=? AND task_id=? AND attempt=? AND generation=? AND phase='launch_intent' AND revision=? AND claim_id IS NULL AND result_digest IS NULL").run(operation.operation_id, task_id, expected_attempt, attempt.generation, operation.revision);
              if (changed.changes !== 1) fail2("queued_cancel_operation_cas_conflict");
              const evidence = { reason: "cancelled_before_claim", cancel_id: cancelId, request_digest: requestDigest, launch_id: operation.launch_id, token_digest: operation.launch_token_digest };
              this.#event(
                operation.operation_id,
                operation.revision + 1,
                "observation_recorded",
                "launch_intent",
                "launch_intent",
                operation.generation,
                { ...evidence, evidence_digest: digest(evidence) },
                at,
                next
              );
            } else {
              const changedOperation = this.#db.prepare("UPDATE manager_operations SET phase='cancelled_before_launch',revision=revision+1 WHERE operation_id=? AND task_id=? AND attempt=? AND generation=? AND phase='reserved' AND revision=? AND launch_id IS NULL AND claim_id IS NULL AND result_digest IS NULL").run(operation.operation_id, task_id, expected_attempt, attempt.generation, operation.revision);
              if (changedOperation.changes !== 1) fail2("queued_cancel_operation_cas_conflict");
              this.#event(
                operation.operation_id,
                operation.revision + 1,
                "cancelled_before_launch",
                "reserved",
                "cancelled_before_launch",
                operation.generation,
                { cancel_id: cancelId, request_digest: requestDigest },
                at,
                next
              );
            }
          }
          this.#faultPoint("after_projection");
          return {
            duplicate: false,
            task_id,
            attempt: expected_attempt,
            status: "cancelled",
            cancel_id: cancelId,
            event_cursor: next,
            operation_id: operation?.operation_id ?? null
          };
        });
      }
      readCommittedResult(operationId) {
        this.#assertOpen();
        if (!validId(operationId)) fail2("invalid_operation_id");
        return this.#readConsistent(() => {
          const o = this.#db.prepare("SELECT * FROM manager_operations WHERE operation_id=? AND operation_kind='attempt_lifecycle'").get(operationId);
          if (!o) fail2("operation_not_found");
          if (o.result_json === null) return null;
          let result;
          try {
            result = JSON.parse(o.result_json);
          } catch {
            fail2("result_projection_invalid");
          }
          return {
            operation_id: o.operation_id,
            task_id: o.task_id,
            attempt: o.attempt,
            generation: o.generation,
            revision: o.revision,
            phase: o.phase,
            claim_id: o.claim_id,
            claim_worker_identity_digest: o.claim_worker_identity_digest,
            result_status: o.result_status,
            result_generation: o.result_generation,
            result_digest: o.result_digest,
            result_commit_ref: o.result_commit_ref,
            result
          };
        });
      }
      /** Explicit user cancellation may administratively release a historical
       * pre-Claim or terminal-cleanup Hold. This is not Cleanup verification and
       * never overwrites an existing Result or event. */
      userAuthorizedReleaseUnverifiedOperation(input) {
        validateUserAuthorizedReleaseInput(input);
        this.#assertWritable();
        return this.#transaction(() => {
          const o = this.#attemptOperation(input);
          const task = this.#db.prepare("SELECT task_id,status,current_attempt FROM tasks WHERE task_id=?").get(input.task_id);
          const attempt = this.#db.prepare("SELECT task_id,attempt,generation,status,queued_cancel_id,queued_cancel_operation_id,queued_cancel_result_json FROM attempts WHERE task_id=? AND attempt=?").get(input.task_id, input.attempt);
          const expectedStatus = o.phase === "launch_intent" ? "cancelled" : o.phase === "released" ? attempt?.status : o.result_status;
          if (!task || !attempt || task.current_attempt !== input.attempt || task.status !== expectedStatus || attempt.status !== expectedStatus || attempt.generation !== input.generation)
            fail2("user_authorized_release_projection_mismatch");
          const cleanupBinding = input.cancellation_verification_digest !== void 0;
          const terminalBinding = input.result_digest !== void 0;
          const forcedPreclaim = input.accept_worker_risk === true;
          const unsignedEvidence = {
            reason: "user_authorized_release_unverified",
            ...terminalBinding ? {} : { cancel_id: input.cancel_id },
            ...forcedPreclaim ? {
              launch_receipt_digest: input.launch_receipt_digest,
              worker_risk_accepted: true
            } : {},
            ...cleanupBinding ? {
              cancellation_verification_digest: input.cancellation_verification_digest,
              recovery_evidence_digest: input.recovery_evidence_digest
            } : {},
            ...terminalBinding ? {
              claim_id: input.claim_id,
              result_commit_ref: input.result_commit_ref,
              result_digest: input.result_digest,
              recovery_evidence_digest: input.recovery_evidence_digest,
              worker_identity_digest: input.worker_identity_digest
            } : {}
          };
          const evidence = { ...unsignedEvidence, evidence_digest: digest(unsignedEvidence) };
          if (o.phase === "released") {
            const released = this.#db.prepare("SELECT * FROM manager_operation_events WHERE operation_id=? AND event_type='observation_recorded' AND json_extract(evidence_json,'$.reason')='user_authorized_release_unverified' ORDER BY sequence DESC LIMIT 1").get(input.operation_id);
            let parsed;
            try {
              parsed = JSON.parse(released?.evidence_json);
            } catch {
              parsed = null;
            }
            if (released && parsed?.reason === "user_authorized_release_unverified" && parsed?.cancel_id === input.cancel_id && parsed?.launch_receipt_digest === input.launch_receipt_digest && parsed?.worker_risk_accepted === input.accept_worker_risk && parsed?.cancellation_verification_digest === input.cancellation_verification_digest && parsed?.recovery_evidence_digest === input.recovery_evidence_digest && parsed?.claim_id === input.claim_id && parsed?.result_commit_ref === input.result_commit_ref && parsed?.result_digest === input.result_digest && parsed?.worker_identity_digest === input.worker_identity_digest && parsed?.evidence_digest === evidence.evidence_digest)
              return {
                duplicate: true,
                operation_id: o.operation_id,
                task_id: o.task_id,
                attempt: o.attempt,
                generation: o.generation,
                revision: o.revision,
                phase: "released",
                cleanup_verified: false,
                release_reason: "user_authorized_release_unverified"
              };
            fail2("user_authorized_release_conflict");
          }
          const preClaim = o.phase === "launch_intent" && o.claim_id === null && o.result_digest === null;
          const historicalCleanup = o.phase === "cleanup_unverified" && o.result_digest !== null && ["completed", "failed", "waiting_for_master", "cancelled"].includes(o.result_status);
          if (!preClaim && !historicalCleanup) fail2("user_authorized_release_phase_not_allowed");
          if (historicalCleanup ? cleanupBinding === terminalBinding : cleanupBinding || terminalBinding)
            fail2("user_authorized_release_phase_mismatch");
          if (preClaim) {
            if ((o.launch_receipt_id !== null || o.launch_receipt_digest !== null || o.launch_identity_json !== null) && !input.accept_worker_risk)
              fail2("user_authorized_release_spawn_evidence_present");
            if (input.accept_worker_risk && o.launch_receipt_digest !== input.launch_receipt_digest)
              fail2("user_authorized_release_spawn_evidence_mismatch");
            if (attempt.queued_cancel_operation_id !== input.operation_id || attempt.queued_cancel_id !== input.cancel_id || attempt.queued_cancel_result_json === null)
              fail2("user_authorized_release_projection_mismatch");
            let queuedResult;
            try {
              queuedResult = JSON.parse(attempt.queued_cancel_result_json);
            } catch {
              queuedResult = null;
            }
            if (!queuedResult || queuedResult.task_id !== input.task_id || queuedResult.attempt !== input.attempt || queuedResult.status !== "cancelled" || queuedResult.started_at !== null)
              fail2("user_authorized_release_projection_mismatch");
          } else if (cleanupBinding) {
            const resultEvent = this.#db.prepare("SELECT * FROM manager_operation_events WHERE operation_id=? AND event_type='result_committed' ORDER BY sequence DESC LIMIT 1").get(input.operation_id);
            let resultEvidence;
            try {
              resultEvidence = resultEvent ? JSON.parse(resultEvent.evidence_json) : null;
            } catch {
              resultEvidence = null;
            }
            if (!resultEvent || !resultEvidence || resultEvidence.outcome !== "cancelled" || resultEvidence.cancel_verification_digest !== input.cancellation_verification_digest)
              fail2("user_authorized_release_cancel_identity_mismatch");
            const cancelEvent = this.#db.prepare("SELECT * FROM manager_operation_events WHERE operation_id=? AND evidence_digest=?").get(input.operation_id, input.cancellation_verification_digest);
            let parsed;
            try {
              parsed = cancelEvent ? JSON.parse(cancelEvent.evidence_json) : null;
            } catch {
              parsed = null;
            }
            if (!cancelEvent || cancelEvent.event_type !== "observation_recorded" || cancelEvent.sequence >= resultEvent.sequence || !parsed || parsed.reason !== "cancel_tree_verified" || parsed.cancel_id !== input.cancel_id || parsed.claim_id !== o.claim_id || parsed.worker_identity_digest !== o.claim_worker_identity_digest)
              fail2("user_authorized_release_cancel_identity_mismatch");
            const lifecycle = this.#db.prepare("SELECT * FROM manager_operation_events WHERE operation_id=? ORDER BY sequence").all(input.operation_id).map((event) => {
              try {
                return { ...event, evidence: JSON.parse(event.evidence_json) };
              } catch {
                fail2("user_authorized_release_recovery_evidence_mismatch");
              }
            });
            const latestActiveRecovery = recoveryEventsFor(lifecycle, o).filter((event) => event.active).at(-1);
            const recoveryEvent = latestActiveRecovery?.event;
            const recoveryEvidence = latestActiveRecovery?.evidence;
            if (!recoveryEvent || recoveryEvent.sequence > o.revision || recoveryEvent.generation !== o.generation || ![recoveryEvent.evidence_digest, recoveryEvidence?.evidence_digest].includes(input.recovery_evidence_digest) || !recoveryEvidence || recoveryEvidence.reason !== "recovery_hold" || recoveryEvidence.task_id !== o.task_id || recoveryEvidence.attempt !== o.attempt || recoveryEvent.sequence !== recoveryEvidence.expected_revision + 1 || recoveryEvidence.claim_id !== o.claim_id || recoveryEvidence.worker_identity_digest !== o.claim_worker_identity_digest || recoveryEvidence.reason_code !== "cleanup_incomplete" || recoveryEvidence.recovery_disposition !== "complete_cleanup_closure_unavailable" || recoveryEvidence.process_tree_scan_clean !== true || recoveryEvidence.process_tree_root_observed !== true || typeof recoveryEvidence.process_tree_scan_digest !== "string" || !/^[0-9a-f]{64}$/u.test(recoveryEvidence.process_tree_scan_digest))
              fail2("user_authorized_release_recovery_evidence_mismatch");
          } else {
            const resultEvent = this.#db.prepare("SELECT * FROM manager_operation_events WHERE operation_id=? AND event_type='result_committed' ORDER BY sequence DESC LIMIT 1").get(input.operation_id);
            let resultEvidence;
            try {
              resultEvidence = resultEvent ? JSON.parse(resultEvent.evidence_json) : null;
            } catch {
              resultEvidence = null;
            }
            if (!resultEvent || !resultEvidence || resultEvidence.outcome !== o.result_status || resultEvidence.result_commit_ref !== input.result_commit_ref || resultEvidence.result_digest !== input.result_digest || resultEvidence.claim_id !== input.claim_id || resultEvidence.worker_identity_digest !== input.worker_identity_digest)
              fail2("user_authorized_release_result_identity_mismatch");
            const lifecycle = this.#db.prepare("SELECT * FROM manager_operation_events WHERE operation_id=? ORDER BY sequence").all(input.operation_id).map((event) => {
              try {
                return { ...event, evidence: JSON.parse(event.evidence_json) };
              } catch {
                fail2("user_authorized_release_recovery_evidence_mismatch");
              }
            });
            const latestActiveRecovery = recoveryEventsFor(lifecycle, o).filter((event) => event.active).at(-1);
            const recoveryEvent = latestActiveRecovery?.event;
            const recoveryEvidence = latestActiveRecovery?.evidence;
            if (!recoveryEvent || recoveryEvent.sequence > o.revision || recoveryEvent.generation !== o.generation || ![recoveryEvent.evidence_digest, recoveryEvidence?.evidence_digest].includes(input.recovery_evidence_digest) || !recoveryEvidence || recoveryEvidence.reason !== "recovery_hold" || recoveryEvidence.task_id !== o.task_id || recoveryEvidence.attempt !== o.attempt || recoveryEvent.sequence !== recoveryEvidence.expected_revision + 1 || recoveryEvidence.claim_id !== o.claim_id || recoveryEvidence.worker_identity_digest !== o.claim_worker_identity_digest || recoveryEvidence.reason_code !== "cleanup_incomplete" || recoveryEvidence.recovery_disposition !== "complete_cleanup_closure_unavailable" || recoveryEvidence.process_tree_scan_clean !== true || recoveryEvidence.process_tree_root_observed !== true || typeof recoveryEvidence.process_tree_scan_digest !== "string" || !/^[0-9a-f]{64}$/u.test(recoveryEvidence.process_tree_scan_digest))
              fail2("user_authorized_release_recovery_evidence_mismatch");
          }
          if (o.revision !== input.revision) fail2("stale_user_authorized_release_cas");
          const changed = this.#db.prepare("UPDATE manager_operations SET phase='released',revision=revision+1 WHERE operation_id=? AND task_id=? AND attempt=? AND generation=? AND revision=? AND phase=? AND claim_id IS ? AND result_digest IS ?").run(input.operation_id, input.task_id, input.attempt, input.generation, input.revision, o.phase, o.claim_id, o.result_digest);
          if (changed.changes !== 1) fail2("stale_user_authorized_release_cas");
          this.#faultPoint("after_projection");
          this.#event(
            input.operation_id,
            input.revision + 1,
            "observation_recorded",
            o.phase,
            "released",
            input.generation,
            evidence,
            (/* @__PURE__ */ new Date()).toISOString()
          );
          return {
            duplicate: false,
            operation_id: o.operation_id,
            task_id: o.task_id,
            attempt: o.attempt,
            generation: o.generation,
            revision: input.revision + 1,
            phase: "released",
            cleanup_verified: false,
            release_reason: "user_authorized_release_unverified"
          };
        });
      }
      /** Persist one cancellation intent for a claimed running Operation after exact identity verification. */
      requestCancellation(input, identityEvidence, identityVerifier) {
        this.#assertWritable();
        if (!validCancellationFence(input)) fail2("invalid_cancellation_request");
        const snapshot = this.#readConsistent(() => {
          const operation = this.#db.prepare("SELECT * FROM manager_operations WHERE operation_id=? AND operation_kind='attempt_lifecycle'").get(input.operation_id);
          if (!operation) fail2("operation_not_found");
          this.#assertNoUnknownInteraction(input.operation_id);
          const observations = this.#db.prepare("SELECT * FROM manager_operation_events WHERE operation_id=? AND event_type='observation_recorded'").all(input.operation_id).map((event) => ({ ...event, evidence: JSON.parse(event.evidence_json) }));
          return { operation, observations };
        });
        if (snapshot.operation.task_id !== input.task_id || snapshot.operation.attempt !== input.attempt || snapshot.operation.generation !== input.generation)
          fail2("operation_identity_mismatch");
        const worker = this.#cancellationWorker(input, snapshot.operation);
        const existing = snapshot.observations.find((event) => event.evidence.reason === "cancel_requested");
        if (snapshot.operation.result_digest !== null || ["result_committed", "cleanup_pending", "cleanup_verified", "cleanup_unverified", "released", "quarantined"].includes(snapshot.operation.phase))
          return {
            duplicate: !!existing && snapshot.operation.result_status === "cancelled",
            result_won: snapshot.operation.result_status !== "cancelled",
            operation_id: input.operation_id,
            task_id: input.task_id,
            attempt: input.attempt,
            generation: input.generation,
            revision: snapshot.operation.revision,
            phase: snapshot.operation.phase,
            result_status: snapshot.operation.result_status,
            ...existing ? { cancel_id: existing.evidence.cancel_id } : {}
          };
        if (existing) return {
          duplicate: true,
          result_won: false,
          operation_id: input.operation_id,
          task_id: input.task_id,
          attempt: input.attempt,
          generation: input.generation,
          revision: snapshot.operation.revision,
          phase: snapshot.operation.phase,
          cancel_id: existing.evidence.cancel_id
        };
        if (snapshot.operation.phase !== "running" || snapshot.operation.revision !== input.revision) fail2("stale_cancellation_cas");
        if (typeof identityVerifier !== "function") fail2("cancellation_identity_verifier_required");
        let identityVerdict;
        try {
          identityVerdict = identityVerifier({ operation: presentOperation(snapshot.operation), worker_identity: worker, evidence: identityEvidence });
        } catch (error) {
          fail2("cancellation_identity_unknown", String(error));
        }
        if (!identityVerdict || !["alive", "exited"].includes(identityVerdict.state) || identityVerdict.worker_identity_digest !== snapshot.operation.claim_worker_identity_digest || typeof identityVerdict.evidence_digest !== "string" || !/^[0-9a-f]{64}$/u.test(identityVerdict.evidence_digest)) fail2("cancellation_identity_unknown");
        if (identityVerdict.evidence_digest !== digest(identityEvidence)) fail2("cancellation_identity_evidence_mismatch");
        const cancelId = randomUUID();
        return this.#transaction(() => {
          const current = this.#attemptOperation(input);
          if (current.result_digest !== null || ["result_committed", "cleanup_pending", "cleanup_verified", "cleanup_unverified", "released", "quarantined"].includes(current.phase))
            return {
              duplicate: false,
              result_won: current.result_status !== "cancelled",
              operation_id: input.operation_id,
              generation: input.generation,
              revision: current.revision,
              phase: current.phase,
              result_status: current.result_status
            };
          this.#cancellationWorker(input, current);
          const raced = this.#db.prepare("SELECT * FROM manager_operation_events WHERE operation_id=? AND event_type='observation_recorded'").all(input.operation_id).map((event) => ({ ...event, evidence: JSON.parse(event.evidence_json) })).find((event) => event.evidence.reason === "cancel_requested");
          if (raced) return {
            duplicate: true,
            result_won: false,
            operation_id: input.operation_id,
            task_id: input.task_id,
            attempt: input.attempt,
            generation: input.generation,
            revision: current.revision,
            phase: current.phase,
            cancel_id: raced.evidence.cancel_id
          };
          if (current.phase !== "running" || current.revision !== input.revision) fail2("stale_cancellation_cas");
          cancellableRecoveryHolds(current, this.#db.prepare("SELECT * FROM manager_operation_events WHERE operation_id=? ORDER BY sequence").all(input.operation_id));
          this.#assertNoUnknownInteraction(input.operation_id);
          const intent = {
            contract: "wp6c-cancel-intent-v1",
            cancel_id: cancelId,
            operation_id: current.operation_id,
            task_id: current.task_id,
            attempt: current.attempt,
            generation: current.generation,
            claim_id: current.claim_id,
            worker_identity_digest: current.claim_worker_identity_digest,
            identity_state: identityVerdict.state,
            identity_evidence_digest: identityVerdict.evidence_digest
          };
          const evidence = {
            reason: "cancel_requested",
            cancel_id: cancelId,
            claim_id: current.claim_id,
            worker_identity_digest: current.claim_worker_identity_digest,
            identity_state: identityVerdict.state,
            identity_evidence_digest: identityVerdict.evidence_digest,
            evidence_digest: digest(intent)
          };
          const changed = this.#db.prepare("UPDATE manager_operations SET revision=revision+1 WHERE operation_id=? AND task_id=? AND attempt=? AND generation=? AND phase='running' AND revision=? AND claim_id=? AND claim_generation=? AND claim_worker_identity_digest=?").run(input.operation_id, input.task_id, input.attempt, input.generation, input.revision, input.claim_id, input.generation, input.claim_worker_identity_digest);
          if (changed.changes !== 1) fail2("stale_cancellation_cas");
          this.#faultPoint("after_projection");
          const at = (/* @__PURE__ */ new Date()).toISOString();
          this.#event(input.operation_id, input.revision + 1, "observation_recorded", "running", "running", input.generation, evidence, at);
          return {
            duplicate: false,
            result_won: false,
            operation_id: input.operation_id,
            task_id: input.task_id,
            attempt: input.attempt,
            generation: input.generation,
            revision: input.revision + 1,
            phase: "running",
            cancel_id: cancelId,
            identity_state: identityVerdict.state
          };
        });
      }
      /** Persist verified Worker-tree exit evidence without marking Result, Cleanup, or Release complete. */
      recordCancellationVerification(input, treeEvidence, cancellationVerifier) {
        this.#assertWritable();
        if (!validCancellationFence(input)) fail2("invalid_cancellation_verification");
        const snapshot = this.#readConsistent(() => {
          const operation = this.#db.prepare("SELECT * FROM manager_operations WHERE operation_id=? AND operation_kind='attempt_lifecycle'").get(input.operation_id);
          if (!operation) fail2("operation_not_found");
          this.#assertNoUnknownInteraction(input.operation_id);
          const observations = this.#db.prepare("SELECT * FROM manager_operation_events WHERE operation_id=? AND event_type='observation_recorded'").all(input.operation_id).map((event) => ({ ...event, evidence: JSON.parse(event.evidence_json) }));
          const events = this.#db.prepare("SELECT * FROM manager_operation_events WHERE operation_id=? ORDER BY sequence").all(input.operation_id);
          return { operation, observations, holds: cancellableRecoveryHolds(operation, events) };
        });
        if (snapshot.operation.task_id !== input.task_id || snapshot.operation.attempt !== input.attempt || snapshot.operation.generation !== input.generation)
          fail2("operation_identity_mismatch");
        const worker = this.#cancellationWorker(input, snapshot.operation);
        const intent = snapshot.observations.find((event) => event.evidence.reason === "cancel_requested");
        if (!intent) fail2("cancel_intent_required");
        const prior = [...snapshot.observations].reverse().find((event) => event.evidence.reason === "cancel_tree_verified");
        if (snapshot.operation.result_digest !== null || snapshot.operation.phase !== "running") {
          if (prior && prior.evidence.proof_digest === digest(treeEvidence) && snapshot.operation.result_status === "cancelled") return {
            duplicate: true,
            result_won: false,
            operation_id: input.operation_id,
            generation: input.generation,
            revision: snapshot.operation.revision,
            phase: snapshot.operation.phase,
            cancellation_verification_digest: prior.evidence_digest
          };
          return {
            duplicate: false,
            result_won: snapshot.operation.result_status !== "cancelled",
            operation_id: input.operation_id,
            generation: input.generation,
            revision: snapshot.operation.revision,
            phase: snapshot.operation.phase,
            result_status: snapshot.operation.result_status
          };
        }
        if (prior && snapshot.holds.length === 0 && prior.evidence.proof_digest === digest(treeEvidence)) return {
          duplicate: true,
          result_won: false,
          operation_id: input.operation_id,
          generation: input.generation,
          revision: snapshot.operation.revision,
          phase: snapshot.operation.phase,
          cancellation_verification_digest: prior.evidence_digest
        };
        if (snapshot.operation.revision !== input.revision) fail2("stale_cancellation_cas");
        if (typeof cancellationVerifier !== "function") fail2("cancellation_verifier_required");
        let verdict;
        try {
          verdict = cancellationVerifier({ operation: presentOperation(snapshot.operation), cancel_intent: intent.evidence, worker_identity: worker, evidence: treeEvidence });
        } catch (error) {
          fail2("cancellation_verification_unknown", String(error));
        }
        const launchIdentity = JSON.parse(snapshot.operation.launch_identity_json);
        if (!verdict || verdict.state !== "verified" || verdict.worker_identity_digest !== snapshot.operation.claim_worker_identity_digest || typeof verdict.process_tree_digest !== "string" || !/^[0-9a-f]{64}$/u.test(verdict.process_tree_digest) || verdict.root_process_id !== worker.process_id || verdict.root_process_id !== launchIdentity.process_id || verdict.root_start_fingerprint !== worker.start_fingerprint || verdict.root_start_fingerprint !== launchIdentity.start_fingerprint || verdict.worker_tree_complete !== true || typeof verdict.evidence_digest !== "string" || !/^[0-9a-f]{64}$/u.test(verdict.evidence_digest) || verdict.evidence_digest !== digest(treeEvidence)) fail2("cancellation_verification_unverified");
        return this.#transaction(() => {
          const current = this.#attemptOperation(input);
          if (current.result_digest !== null || current.phase !== "running") return {
            duplicate: false,
            result_won: current.result_status !== "cancelled",
            operation_id: input.operation_id,
            generation: input.generation,
            revision: current.revision,
            phase: current.phase,
            result_status: current.result_status
          };
          if (current.revision !== input.revision) fail2("stale_cancellation_cas");
          this.#cancellationWorker(input, current);
          const persistedIntent = this.#db.prepare("SELECT * FROM manager_operation_events WHERE operation_id=? AND event_type='observation_recorded'").all(input.operation_id).map((event2) => ({ ...event2, evidence: JSON.parse(event2.evidence_json) })).find((event2) => event2.evidence.reason === "cancel_requested");
          if (!persistedIntent || persistedIntent.evidence.cancel_id !== intent.evidence.cancel_id) fail2("cancel_intent_mismatch");
          const existingRows = this.#db.prepare("SELECT * FROM manager_operation_events WHERE operation_id=? AND event_type='observation_recorded' ORDER BY sequence").all(input.operation_id).map((event2) => ({ ...event2, evidence: JSON.parse(event2.evidence_json) })).filter((event2) => event2.evidence.reason === "cancel_tree_verified");
          const existing = existingRows.at(-1);
          const holds = cancellableRecoveryHolds(current, this.#db.prepare("SELECT * FROM manager_operation_events WHERE operation_id=? ORDER BY sequence").all(input.operation_id));
          if (existing && holds.length === 0) {
            if (existing.evidence.proof_digest === verdict.evidence_digest) return {
              duplicate: true,
              result_won: false,
              operation_id: input.operation_id,
              generation: input.generation,
              revision: current.revision,
              phase: current.phase,
              cancellation_verification_digest: existing.evidence_digest
            };
            fail2("cancellation_verification_conflict");
          }
          this.#assertNoUnknownInteraction(input.operation_id);
          const unsigned = {
            reason: "cancel_tree_verified",
            cancel_id: intent.evidence.cancel_id,
            claim_id: current.claim_id,
            worker_identity_digest: current.claim_worker_identity_digest,
            intent_event_digest: persistedIntent.evidence_digest,
            process_tree_digest: verdict.process_tree_digest,
            proof_digest: verdict.evidence_digest,
            root_process_id: verdict.root_process_id,
            root_start_fingerprint: verdict.root_start_fingerprint,
            worker_tree_complete: true
          };
          const evidence = { ...unsigned, evidence_digest: digest({ cancel_verification_contract_version: 1, ...unsigned }) };
          const count = 1 + (holds.length ? 1 : 0);
          const changed = this.#db.prepare("UPDATE manager_operations SET revision=revision+1 WHERE operation_id=? AND task_id=? AND attempt=? AND generation=? AND phase='running' AND revision=? AND claim_id=? AND claim_generation=? AND claim_worker_identity_digest=?").run(input.operation_id, input.task_id, input.attempt, input.generation, input.revision, input.claim_id, input.generation, input.claim_worker_identity_digest);
          if (changed.changes !== 1) fail2("stale_cancellation_cas");
          this.#faultPoint("after_projection");
          const at = (/* @__PURE__ */ new Date()).toISOString();
          this.#event(input.operation_id, input.revision + 1, "observation_recorded", "running", "running", input.generation, evidence, at);
          const event = this.#db.prepare("SELECT evidence_digest FROM manager_operation_events WHERE operation_id=? AND sequence=?").get(input.operation_id, input.revision + 1);
          if (holds.length) {
            const next = this.#db.prepare("UPDATE manager_operations SET revision=revision+1 WHERE operation_id=? AND revision=?").run(input.operation_id, input.revision + 1);
            if (next.changes !== 1) fail2("stale_cancellation_cas");
            const resolution = {
              reason: "cancel_recovery_resolved",
              cancel_id: intent.evidence.cancel_id,
              cancellation_verification_digest: event.evidence_digest,
              proof_digest: verdict.evidence_digest,
              ...resolvedRecoveryCommitment(holds.map((item) => item.event.evidence_digest))
            };
            this.#event(
              input.operation_id,
              input.revision + count,
              "observation_recorded",
              "running",
              "running",
              input.generation,
              { ...resolution, evidence_digest: digest(resolution) },
              at
            );
          }
          return {
            duplicate: false,
            result_won: false,
            operation_id: input.operation_id,
            generation: input.generation,
            revision: input.revision + count,
            phase: "running",
            cancel_id: intent.evidence.cancel_id,
            cancellation_verification_digest: event.evidence_digest
          };
        });
      }
      /**
       * Narrow operator-only recovery for one durable cleanup_incomplete Hold whose
       * Worker generation ended before the current Windows boot. This is not a
       * generic admin API and never records a Result, cleanup_verified, or released
       * lifecycle event.
       */
      adminAbandonHeldOperation(input) {
        this.#assertWritable();
        validateAdminAbandonmentInput(input);
        return this.#transaction(() => {
          const hasAdminTable = Boolean(this.#db.prepare("SELECT 1 FROM sqlite_schema WHERE type='table' AND name='manager_admin_abandonments'").get());
          const operation = this.#db.prepare("SELECT * FROM manager_operations WHERE operation_id=? AND operation_kind='attempt_lifecycle'").get(input.operation_id);
          if (!operation) fail2("operation_not_found");
          const existing = hasAdminTable ? this.#db.prepare("SELECT * FROM manager_admin_abandonments WHERE operation_id=?").get(input.operation_id) : void 0;
          if (operation.task_id !== input.task_id || operation.attempt !== input.attempt || operation.generation !== input.generation || operation.claim_id !== input.claim_id || operation.claim_worker_identity_digest !== input.claim_worker_identity_digest)
            fail2("admin_abandonment_identity_mismatch");
          let worker, launch;
          try {
            worker = JSON.parse(operation.claim_worker_identity_json);
            launch = JSON.parse(operation.launch_identity_json);
          } catch {
            fail2("admin_abandonment_identity_invalid");
          }
          if (!worker || worker.source !== "manager_verified_process_probe" || worker.fixture !== false || worker.platform !== "win32" || worker.fingerprint_precision !== "exact" || digest(canonical3(worker)) !== input.claim_worker_identity_digest || !launch || launch.source !== "manager_os_spawn_observation" || launch.fixture !== false || launch.platform !== "win32" || launch.fingerprint_precision !== "exact" || launch.process_id !== worker.process_id || launch.start_fingerprint !== worker.start_fingerprint || input.evidence.worker_process_id !== worker.process_id || input.evidence.worker_start_fingerprint !== worker.start_fingerprint) fail2("admin_abandonment_worker_identity_mismatch");
          const audit = {
            boot_time: input.evidence.boot_time,
            claimant_scan_clean: true,
            claimant_scan_digest: input.evidence.claimant_scan_digest,
            cleanup_verified: false,
            failed_at: input.evidence.failed_at,
            hosts_closed: true,
            observed_at: input.evidence.observed_at,
            platform_probe_digest: input.evidence.platform_probe_digest,
            process_inventory_digest: input.evidence.process_inventory_digest,
            result_absent: true,
            worker_exited: true,
            writer_closed: true
          };
          const auditJson = canonical3(audit), auditDigest = digest(auditJson);
          const requestDigest = digest({
            operation_id: input.operation_id,
            task_id: input.task_id,
            attempt: input.attempt,
            generation: input.generation,
            original_revision: input.revision,
            claim_id: input.claim_id,
            worker_identity_digest: input.claim_worker_identity_digest,
            worker_process_id: input.evidence.worker_process_id,
            worker_start_fingerprint: input.evidence.worker_start_fingerprint,
            audit_digest: auditDigest
          });
          if (existing) {
            if (existing.task_id === input.task_id && existing.attempt === input.attempt && existing.generation === input.generation && existing.claim_id === input.claim_id && existing.worker_identity_digest === input.claim_worker_identity_digest && existing.original_revision === input.revision && existing.audit_digest === auditDigest && existing.request_digest === requestDigest)
              return {
                duplicate: true,
                operation_id: input.operation_id,
                task_id: input.task_id,
                attempt: input.attempt,
                generation: input.generation,
                phase: "admin_abandoned",
                result_absent: true,
                cleanup_verified: false,
                revision: operation.revision,
                event_sequence: existing.event_sequence,
                audit_digest: existing.audit_digest
              };
            fail2("admin_abandonment_evidence_conflict");
          }
          if (operation.revision !== input.revision) fail2("admin_abandonment_identity_mismatch");
          if (operation.phase !== "running" || operation.result_digest !== null || operation.result_json !== null || operation.result_commit_ref !== null || operation.result_status !== null || operation.result_generation !== null) fail2("admin_abandonment_result_or_phase_invalid");
          const projection = this.#db.prepare(`SELECT t.current_attempt,t.status AS task_status,a.status AS attempt_status,a.generation
        FROM tasks t JOIN attempts a ON a.task_id=t.task_id AND a.attempt=t.current_attempt
        WHERE t.task_id=? AND a.attempt=?`).get(input.task_id, input.attempt);
          if (!projection || projection.current_attempt !== input.attempt || projection.task_status !== "running" || projection.attempt_status !== "running" || projection.generation !== input.generation) fail2("admin_abandonment_projection_invalid");
          const events = this.#db.prepare("SELECT * FROM manager_operation_events WHERE operation_id=? ORDER BY sequence").all(input.operation_id);
          const holds = [];
          for (const event of events) {
            if (event.event_type !== "observation_recorded") continue;
            let evidence;
            try {
              evidence = JSON.parse(event.evidence_json);
            } catch {
              fail2("database_unreadable");
            }
            if (evidence.reason === "recovery_hold" && evidence.reason_code === "cleanup_incomplete" && evidence.claim_id === input.claim_id && evidence.worker_identity_digest === input.claim_worker_identity_digest) holds.push({ event, evidence });
          }
          if (holds.length === 0) fail2("admin_abandonment_cleanup_hold_required");
          const latestHold = holds.at(-1);
          if (input.evidence.failed_at !== latestHold.event.at) fail2("admin_abandonment_failure_time_mismatch");
          this.#assertNoUnknownInteraction(input.operation_id);
          this.#assertNoCancellationIntent(input.operation_id);
          if (hasAdminTable) {
            upgradeLegacyAdminAbandonmentSchema(this.#db);
          } else {
            this.#db.exec(ADMIN_ABANDONMENT_SCHEMA);
            assertCandidateSchema(this.#db);
          }
          const changedOperation = this.#db.prepare(`UPDATE manager_operations
        SET phase='released',revision=revision+1
        WHERE operation_id=? AND task_id=? AND attempt=? AND generation=? AND phase='running' AND revision=?
          AND claim_id=? AND claim_generation=? AND claim_worker_identity_digest=?
          AND result_digest IS NULL AND result_json IS NULL AND result_commit_ref IS NULL`).run(input.operation_id, input.task_id, input.attempt, input.generation, input.revision, input.claim_id, input.generation, input.claim_worker_identity_digest);
          if (changedOperation.changes !== 1) fail2("stale_admin_abandonment_cas");
          const changedAttempt = this.#db.prepare(`UPDATE attempts SET status='failed'
        WHERE task_id=? AND attempt=? AND generation=? AND status='running'`).run(input.task_id, input.attempt, input.generation);
          const changedTask = this.#db.prepare(`UPDATE tasks SET status='failed'
        WHERE task_id=? AND current_attempt=? AND status='running'`).run(input.task_id, input.attempt);
          if (changedAttempt.changes !== 1 || changedTask.changes !== 1) fail2("admin_abandonment_projection_cas");
          const eventSequence = input.revision + 1;
          this.#event(
            input.operation_id,
            eventSequence,
            "observation_recorded",
            "running",
            "released",
            input.generation,
            { reason: "admin_abandoned", evidence_digest: auditDigest },
            input.evidence.observed_at
          );
          const inserted = this.#db.prepare(`INSERT INTO manager_admin_abandonments(
        operation_id,operation_kind,task_id,attempt,generation,claim_id,worker_identity_digest,original_revision,event_sequence,
        outcome,result_absent,cleanup_verified,release_reason,request_digest,audit_json,audit_digest,abandoned_at)
        VALUES(?,'attempt_lifecycle',?,?,?,?,?,?,?, 'admin_abandoned',1,0,'cleanup_incomplete',?,?,?,?)`).run(
            input.operation_id,
            input.task_id,
            input.attempt,
            input.generation,
            input.claim_id,
            input.claim_worker_identity_digest,
            input.revision,
            eventSequence,
            requestDigest,
            auditJson,
            auditDigest,
            input.evidence.observed_at
          );
          if (inserted.changes !== 1) fail2("admin_abandonment_insert_failed");
          return {
            duplicate: false,
            operation_id: input.operation_id,
            task_id: input.task_id,
            attempt: input.attempt,
            generation: input.generation,
            phase: "admin_abandoned",
            result_absent: true,
            cleanup_verified: false,
            revision: eventSequence,
            event_sequence: eventSequence,
            audit_digest: auditDigest
          };
        });
      }
      readSnapshot() {
        const snapshot = this.#readConsistent(() => {
          const admins = this.#adminAbandonments();
          return {
            capacity: this.#db.prepare("SELECT * FROM authority_metadata").get(),
            operations: this.#db.prepare("SELECT * FROM manager_operations ORDER BY operation_id").all().map((row) => presentOperation(row, admins.get(row.operation_id))),
            events: this.#db.prepare("SELECT * FROM manager_operation_events ORDER BY operation_id,sequence").all()
          };
        });
        return { ...snapshot, root_poisoned: this.poisoned || existsSync(this.#paths.intent) };
      }
      /** Read-only recovery entry point. Writable Stores cannot be used as Recovery authority. */
      readRecoverySnapshot() {
        this.#assertOpen();
        if (!this.#recoveryOnly) fail2("recovery_read_only");
        return this.rebuildRecoveryState();
      }
      /** Reconstruct only from persisted facts. Any inconsistency blocks the whole root; no repair or release occurs. */
      rebuildRecoveryState() {
        this.#assertOpen();
        if (!this.#recoveryOnly) fail2("recovery_read_only");
        let transaction = false;
        try {
          this.#db.exec("BEGIN");
          transaction = true;
          const userVersion = this.#db.prepare("PRAGMA user_version").get().user_version;
          if (userVersion !== SCHEMA_VERSION) fail2("schema_version_unknown");
          const columns = new Set(this.#db.prepare("PRAGMA table_info(manager_operations)").all().map((x) => x.name));
          if (!["result_status", "result_generation", "result_digest", "result_json", "result_commit_ref"].every((x) => columns.has(x))) fail2("candidate_schema_mismatch");
          const meta = this.#db.prepare("SELECT * FROM authority_metadata").all();
          const operations = this.#db.prepare("SELECT * FROM manager_operations ORDER BY operation_id").all();
          const events = this.#db.prepare("SELECT * FROM manager_operation_events ORDER BY operation_id,sequence").all();
          const taskProjections = this.#db.prepare(`SELECT task_id,current_attempt,status,created_at,
          json_extract(task_json,'$.workspace') AS workspace,
          COALESCE(json_extract(task_json,'$.worktree_path'),json_extract(task_json,'$.workspace')) AS execution_workspace
        FROM tasks ORDER BY task_id`).all().map((row) => ({ ...row, owner_binding: this.#ownerBinding(row.task_id) }));
          const adminAbandonments = this.#adminAbandonments();
          let integrityError = null;
          try {
            this.#validateContents();
          } catch (e) {
            integrityError = e?.code ?? "projection_event_mismatch";
          }
          this.#db.exec("COMMIT");
          transaction = false;
          const poisoned = this.poisoned, writerIntent = existsSync(this.#paths.intent);
          const rootBlocked = Boolean(integrityError || meta.length !== 1 || poisoned || writerIntent);
          const operationsWithRecovery = operations.map((row) => {
            const adminAbandonment = adminAbandonments.get(row.operation_id);
            const active = row.operation_kind === "attempt_lifecycle" && !adminAbandonment && !["released", "cancelled_before_launch"].includes(row.phase);
            const operationEvents = events.filter((e) => e.operation_id === row.operation_id);
            const recoveryEvents = recoveryEventsFor(operationEvents, row);
            const recoveryClassification = foldedRecoveryClassification(row, operationEvents);
            const preclaimCancelled = row.phase === "launch_intent" && row.claim_id === null && operationEvents.some((event) => event.event_type === "observation_recorded" && JSON.parse(event.evidence_json).reason === "cancelled_before_claim");
            const userAuthorizedRelease = row.phase === "released" && operationEvents.some((event) => event.event_type === "observation_recorded" && JSON.parse(event.evidence_json).reason === "user_authorized_release_unverified");
            const cleanupState = preclaimCancelled ? "unverified" : adminAbandonment ? "not_applicable" : row.phase === "cleanup_verified" || row.phase === "released" && !userAuthorizedRelease ? "verified" : row.phase === "cleanup_unverified" ? "unverified" : row.phase === "result_committed" || row.phase === "cleanup_pending" || row.phase === "quarantined" || active && row.claim_id !== null ? "unknown" : userAuthorizedRelease ? "unverified_admin_release" : "not_applicable";
            const blockers = [];
            if (preclaimCancelled) blockers.push("cancelled_before_claim_cleanup_unverified");
            if (integrityError) blockers.push(integrityError);
            if (row.operation_kind === "attempt_lifecycle" && !adminAbandonment) {
              if (row.launch_id !== null && row.launch_receipt_digest === null) blockers.push("launch_outcome_unknown_receipt_missing");
              if (row.claim_id !== null && active && cleanupState !== "verified") blockers.push("manager_os_identity_probe_required");
              if (row.result_digest === null && row.claim_id !== null && active) blockers.push("execution_result_unknown");
              if (row.phase === "result_committed" || row.phase === "cleanup_pending" || row.phase === "cleanup_unverified") blockers.push("operation_cleanup_unverified");
              if (row.phase === "cleanup_verified") blockers.push("operation_release_pending");
              if (row.phase === "quarantined") blockers.push("result_conflict_quarantined");
              if (hasUnresolvedInteraction(operationEvents)) blockers.push("interaction_reply_outcome_unknown");
              if (recoveryClassification === "hold") blockers.push("recovery_hold");
              if (recoveryClassification === "quarantine") blockers.push("recovery_quarantine");
              if (active) blockers.push("capacity_and_workspace_occupancy_retained");
            }
            if (poisoned) blockers.push("root_poisoned");
            if (writerIntent) blockers.push("writer_intent_present_outcome_unknown");
            const recoveryDecision = integrityError ? "quarantine_read_only" : poisoned || writerIntent || meta.length !== 1 ? "blocked_read_only" : adminAbandonment ? "complete" : userAuthorizedRelease || row.operation_kind === "attempt_lifecycle" && ["released", "cancelled_before_launch"].includes(row.phase) ? "complete" : recoveryClassification === "quarantine" ? "quarantine_read_only" : "hold";
            return {
              ...presentOperation(row, adminAbandonment),
              recovery_decision: recoveryDecision,
              recovery_blockers: [...new Set(blockers)],
              recovery_classification: recoveryClassification,
              recovery_observation_count: recoveryEvents.length,
              claim_permanent: row.claim_id !== null,
              capacity_occupied: active,
              cleanup_state: cleanupState
            };
          });
          return {
            schema_version: 3,
            root_status: integrityError ? "quarantined_read_only" : rootBlocked ? "blocked_read_only" : "consistent_read_only",
            root_blockers: [.../* @__PURE__ */ new Set([...integrityError ? [integrityError] : [], ...poisoned ? ["root_poisoned"] : [], ...writerIntent ? ["writer_intent_present_outcome_unknown"] : [], ...meta.length !== 1 ? ["authority_metadata_invalid"] : []])],
            capacity: meta.length === 1 ? meta[0] : null,
            operations: operationsWithRecovery,
            events,
            task_projections: taskProjections,
            verified_event_projection_consistency: !integrityError,
            writes_allowed: false,
            cleanup_performed: false,
            claim_release_performed: false,
            operation_release_performed: false
          };
        } catch (e) {
          if (transaction) {
            try {
              this.#db.exec("ROLLBACK");
            } catch {
            }
          }
          return {
            schema_version: 3,
            root_status: "unavailable_read_only",
            root_blockers: [e?.code ?? "recovery_read_failed"],
            capacity: null,
            operations: [],
            events: [],
            verified_event_projection_consistency: false,
            writes_allowed: false,
            cleanup_performed: false,
            claim_release_performed: false,
            operation_release_performed: false
          };
        }
      }
      compareAndSwapObservation({ operation_id, generation, revision, evidence }) {
        if (!Number.isInteger(generation) || !Number.isInteger(revision)) fail2("invalid_cas");
        validateEvidence("observation_recorded", evidence);
        return this.#transaction(() => {
          if (evidence.reason === "recovery_hold" || evidence.reason === "recovery_quarantine") fail2("reserved_recovery_reason");
          if (["cancel_requested", "cancel_tree_verified", "cancelled_before_claim", "cancel_recovery_resolved"].includes(evidence.reason)) fail2("reserved_cancellation_reason");
          const o = this.#db.prepare("SELECT * FROM manager_operations WHERE operation_id=? AND operation_kind='attempt_lifecycle'").get(operation_id);
          if (!o || o.generation !== generation || o.revision !== revision || o.phase !== "reserved") fail2("stale_operation_cas");
          const at = (/* @__PURE__ */ new Date()).toISOString();
          const changed = this.#db.prepare("UPDATE manager_operations SET revision=revision+1 WHERE operation_id=? AND generation=? AND revision=?").run(operation_id, generation, revision);
          if (changed.changes !== 1) fail2("stale_operation_cas");
          this.#faultPoint("after_projection");
          const evidenceJson = canonical3(evidence);
          this.#event(operation_id, revision + 1, "observation_recorded", "reserved", "reserved", generation, evidence, at);
          return { revision: revision + 1, phase: "reserved" };
        });
      }
      /**
       * Append a bounded, release-bound Wake fact to the existing SQLite Authority.
       * A deterministic delivery id may advance only through one terminal Queue
       * acknowledgement and one observed Turn start. Wake facts never change Task,
       * Result, Cleanup, Release, capacity, or Recovery state.
       */
      recordExecutorWakeObservation(input) {
        validateExecutorWakeInput(input);
        this.#assertWritable();
        return this.#transaction(() => {
          const o = this.#attemptOperation(input);
          if (o.phase !== "released" || o.result_digest === null || o.result_commit_ref === null)
            fail2("executor_wake_operation_not_released");
          const releaseEvent = this.#db.prepare("SELECT * FROM manager_operation_events WHERE operation_id=? AND event_type='released'").get(input.operation_id);
          if (!releaseEvent) fail2("executor_wake_cleanup_release_required");
          const wake = [];
          for (const row of this.#db.prepare("SELECT * FROM manager_operation_events WHERE operation_id=? AND event_type='observation_recorded' ORDER BY sequence").all(input.operation_id)) {
            let evidence2;
            try {
              evidence2 = JSON.parse(row.evidence_json);
            } catch {
              fail2("invalid_executor_wake_evidence");
            }
            if (evidence2.reason !== "executor_wake") continue;
            validateObservationEventEvidence(evidence2);
            wake.push({ row, evidence: evidence2 });
          }
          const unsigned = {
            reason: "executor_wake",
            state: input.state,
            task_id: input.task_id,
            attempt: input.attempt,
            operation_id: input.operation_id,
            generation: input.generation,
            result_digest: o.result_digest,
            result_commit_ref: o.result_commit_ref,
            thread_id: input.thread_id,
            delivery_id: input.delivery_id,
            policy_digest: input.policy_digest,
            authorization_digest: input.authorization_digest,
            reason_code: input.reason_code,
            ..."queue_message_id" in input ? { queue_message_id: input.queue_message_id } : {}
          };
          const evidence = { ...unsigned, evidence_digest: digest(unsigned) };
          validateObservationEventEvidence(evidence);
          const same = wake.find((item) => item.evidence.delivery_id === input.delivery_id && item.evidence.state === input.state);
          if (same) {
            if (same.evidence.evidence_digest === evidence.evidence_digest && canonical3(same.evidence) === canonical3(evidence))
              return {
                duplicate: true,
                operation_id: o.operation_id,
                task_id: o.task_id,
                attempt: o.attempt,
                generation: o.generation,
                revision: o.revision,
                event_sequence: same.row.sequence,
                state: input.state,
                delivery_id: input.delivery_id,
                desktop_visible: "UNKNOWN"
              };
            fail2("executor_wake_observation_conflict");
          }
          if (wake.length >= EXECUTOR_WAKE_LIMIT) fail2("executor_wake_observation_limit");
          if (wake.some((item) => item.evidence.delivery_id !== input.delivery_id))
            fail2("executor_wake_delivery_conflict");
          if (wake.some((item) => item.evidence.result_digest !== o.result_digest || item.evidence.result_commit_ref !== o.result_commit_ref || item.evidence.task_id !== o.task_id || item.evidence.attempt !== o.attempt || item.evidence.generation !== o.generation))
            fail2("executor_wake_operation_binding_conflict");
          const states = new Set(wake.map((item) => item.evidence.state));
          if (input.state === "intent" && wake.length !== 0) fail2("executor_wake_intent_not_first");
          if (["queued", "submission_unknown"].includes(input.state) && (!states.has("intent") || states.has("queued") || states.has("submission_unknown") || states.has("web_notify")))
            fail2("executor_wake_ack_transition_invalid");
          if (input.state === "turn_started" && (!states.has("intent") || !states.has("queued") && !states.has("submission_unknown") || states.has("turn_started") || states.has("web_notify")))
            fail2("executor_wake_turn_transition_invalid");
          if (input.state === "web_notify" && states.has("turn_started")) fail2("executor_wake_turn_transition_invalid");
          if (wake.length) {
            const binding = wake[0].evidence;
            if (binding.thread_id !== input.thread_id || binding.policy_digest !== input.policy_digest || binding.authorization_digest !== input.authorization_digest)
              fail2("executor_wake_binding_conflict");
          }
          const changed = this.#db.prepare("UPDATE manager_operations SET revision=revision+1 WHERE operation_id=? AND task_id=? AND attempt=? AND generation=? AND phase='released' AND revision=? AND result_digest=? AND result_commit_ref=?").run(o.operation_id, o.task_id, o.attempt, o.generation, o.revision, o.result_digest, o.result_commit_ref);
          if (changed.changes !== 1) fail2("stale_executor_wake_cas");
          this.#faultPoint("after_projection");
          this.#event(o.operation_id, o.revision + 1, "observation_recorded", "released", "released", o.generation, evidence, (/* @__PURE__ */ new Date()).toISOString());
          return {
            duplicate: false,
            operation_id: o.operation_id,
            task_id: o.task_id,
            attempt: o.attempt,
            generation: o.generation,
            revision: o.revision + 1,
            event_sequence: o.revision + 1,
            state: input.state,
            delivery_id: input.delivery_id,
            desktop_visible: "UNKNOWN"
          };
        });
      }
      /**
       * Append an explicit, per-Operation Late Wake Compensation fact. This is
       * deliberately separate from executor_wake: it is eligible only after a
       * terminal web_notify and never for a Queue submission whose outcome is
       * queued, unknown, or already observed as started. It never changes Task,
       * Result, Cleanup, Release, capacity, or Worker execution.
       */
      recordLateWakeCompensation(input) {
        validateLateWakeInput(input);
        this.#assertWritable();
        return this.#transaction(() => {
          const o = this.#attemptOperation(input);
          if (o.phase !== "released" || o.result_digest === null || o.result_commit_ref === null)
            fail2("executor_wake_operation_not_released");
          const binding = this.#ownerBinding(input.task_id);
          if (binding.state !== "bound" || binding.owner_thread_id !== input.thread_id)
            fail2("late_wake_owner_binding_required");
          const wake = [];
          const compensation = [];
          for (const row of this.#db.prepare("SELECT * FROM manager_operation_events WHERE operation_id=? AND event_type='observation_recorded' ORDER BY sequence").all(input.operation_id)) {
            let evidence2;
            try {
              evidence2 = JSON.parse(row.evidence_json);
            } catch {
              fail2("invalid_executor_wake_evidence");
            }
            if (evidence2.reason === "executor_wake") {
              validateObservationEventEvidence(evidence2);
              wake.push({ row, evidence: evidence2 });
            } else if (evidence2.reason === LATE_WAKE_REASON) {
              validateObservationEventEvidence(evidence2);
              compensation.push({ row, evidence: evidence2 });
            }
          }
          if (!wake.some((item) => item.evidence.state === "web_notify") || wake.some((item) => ["queued", "submission_unknown", "turn_started"].includes(item.evidence.state)))
            fail2("late_wake_not_eligible");
          if (input.state === "intent" && compensation.length !== 0) fail2("late_wake_intent_not_first");
          if (wake.some((item) => item.evidence.delivery_id === input.delivery_id))
            fail2("late_wake_delivery_conflict");
          if (compensation.length >= LATE_WAKE_LIMIT) fail2("late_wake_observation_limit");
          if (compensation.some((item) => item.evidence.delivery_id !== input.delivery_id))
            fail2("late_wake_delivery_conflict");
          if (compensation.some((item) => item.evidence.result_digest !== o.result_digest || item.evidence.result_commit_ref !== o.result_commit_ref || item.evidence.task_id !== o.task_id || item.evidence.attempt !== o.attempt || item.evidence.generation !== o.generation))
            fail2("late_wake_operation_binding_conflict");
          const unsigned = {
            reason: LATE_WAKE_REASON,
            state: input.state,
            task_id: input.task_id,
            attempt: input.attempt,
            operation_id: input.operation_id,
            generation: input.generation,
            result_digest: o.result_digest,
            result_commit_ref: o.result_commit_ref,
            thread_id: input.thread_id,
            delivery_id: input.delivery_id,
            policy_digest: input.policy_digest,
            authorization_digest: input.authorization_digest,
            reason_code: input.reason_code,
            ..."queue_message_id" in input ? { queue_message_id: input.queue_message_id } : {}
          };
          const evidence = { ...unsigned, evidence_digest: digest(unsigned) };
          validateObservationEventEvidence(evidence);
          const same = compensation.find((item) => item.evidence.delivery_id === input.delivery_id && item.evidence.state === input.state);
          if (same) {
            if (same.evidence.evidence_digest === evidence.evidence_digest && canonical3(same.evidence) === canonical3(evidence))
              return {
                duplicate: true,
                operation_id: o.operation_id,
                task_id: o.task_id,
                attempt: o.attempt,
                generation: o.generation,
                revision: o.revision,
                event_sequence: same.row.sequence,
                state: input.state,
                delivery_id: input.delivery_id,
                desktop_visible: "UNKNOWN"
              };
            fail2("late_wake_observation_conflict");
          }
          const states = new Set(compensation.map((item) => item.evidence.state));
          if (["queued", "submission_unknown"].includes(input.state) && (!states.has("intent") || states.has("queued") || states.has("submission_unknown") || states.has("web_notify")))
            fail2("late_wake_ack_transition_invalid");
          if (input.state === "turn_started" && (!states.has("intent") || !states.has("queued") && !states.has("submission_unknown") || states.has("turn_started") || states.has("web_notify")))
            fail2("late_wake_turn_transition_invalid");
          if (input.state === "web_notify" && states.has("turn_started")) fail2("late_wake_turn_transition_invalid");
          if (compensation.length) {
            const prior = compensation[0].evidence;
            if (prior.thread_id !== input.thread_id || prior.policy_digest !== input.policy_digest || prior.authorization_digest !== input.authorization_digest)
              fail2("late_wake_binding_conflict");
          }
          const changed = this.#db.prepare("UPDATE manager_operations SET revision=revision+1 WHERE operation_id=? AND task_id=? AND attempt=? AND generation=? AND phase='released' AND revision=? AND result_digest=? AND result_commit_ref=?").run(o.operation_id, o.task_id, o.attempt, o.generation, o.revision, o.result_digest, o.result_commit_ref);
          if (changed.changes !== 1) fail2("stale_late_wake_cas");
          this.#faultPoint("after_projection");
          this.#event(o.operation_id, o.revision + 1, "observation_recorded", "released", "released", o.generation, evidence, (/* @__PURE__ */ new Date()).toISOString());
          return {
            duplicate: false,
            operation_id: o.operation_id,
            task_id: o.task_id,
            attempt: o.attempt,
            generation: o.generation,
            revision: o.revision + 1,
            event_sequence: o.revision + 1,
            state: input.state,
            delivery_id: input.delivery_id,
            desktop_visible: "UNKNOWN"
          };
        });
      }
      /** Diagnostic only: no Result, phase transition, cleanup proof or Release. */
      recordResultSubmissionFailure(input, reason) {
        if (!validText2(reason, 128)) fail2("invalid_result_failure_reason");
        return this.#transaction(() => {
          const o = this.#db.prepare("SELECT * FROM manager_operations WHERE operation_id=?").get(input.operation_id);
          if (!o || o.phase !== "running" || o.generation !== input.generation || o.revision !== input.revision || o.claim_id !== input.claim_id || o.claim_worker_identity_digest !== input.claim_worker_identity_digest) fail2("stale_operation_cas");
          const evidence = { reason: `result_submission_failed:${reason}`, evidence_digest: digest({ operation_id: o.operation_id, claim_id: o.claim_id, reason }) };
          this.#db.prepare("UPDATE manager_operations SET revision=revision+1 WHERE operation_id=?").run(o.operation_id);
          this.#event(o.operation_id, o.revision + 1, "observation_recorded", "running", "running", o.generation, evidence, (/* @__PURE__ */ new Date()).toISOString());
          return { revision: o.revision + 1, phase: "running" };
        });
      }
      /** Persist only a verified, operation-scoped Recovery classification; no external action is performed. */
      compareAndSwapRecoveryObservation(input, evidence, verifyEvidence) {
        this.#assertWritable();
        if (typeof verifyEvidence !== "function") fail2("recovery_evidence_verifier_required");
        const envelope = recoveryEnvelope(input), envelopeDigest = digest(envelope);
        let evidenceJson;
        try {
          evidenceJson = canonical3(evidence);
        } catch {
          fail2("recovery_evidence_invalid");
        }
        if (Buffer.byteLength(evidenceJson, "utf8") > 4096 || !evidence || Object.getPrototypeOf(evidence) !== Object.prototype || containsNonNfcString(evidence) || digest(evidenceJson) !== input.evidence_digest) fail2("recovery_evidence_invalid");
        return this.#transaction(() => {
          const o = this.#db.prepare("SELECT * FROM manager_operations WHERE operation_id=? AND operation_kind='attempt_lifecycle'").get(input.operation_id);
          if (!o) fail2("operation_not_found");
          if (o.task_id !== input.task_id || o.attempt !== input.attempt || o.generation !== input.generation) fail2("operation_identity_mismatch");
          if (o.claim_id === null || o.claim_generation !== input.generation || !o.claim_worker_identity_digest) fail2("recovery_claim_missing");
          if (o.claim_id !== input.claim_id || o.claim_worker_identity_digest !== input.worker_identity_digest) fail2("recovery_claim_identity_mismatch");
          if (!RECOVERY_PHASES.has(o.phase)) fail2("recovery_phase_not_allowed");
          let verified = null;
          try {
            verified = verifyEvidence({ operation: {
              operation_id: o.operation_id,
              task_id: o.task_id,
              attempt: o.attempt,
              generation: o.generation,
              phase: o.phase,
              revision: o.revision,
              claim_id: o.claim_id,
              worker_identity_digest: o.claim_worker_identity_digest
            }, observation: input, evidence });
          } catch {
            verified = null;
          }
          if (!verified || Object.getPrototypeOf(verified) !== Object.prototype || Object.keys(verified).sort().join("|") !== "classification|evidence_digest|evidence_source|reason_code" || verified.classification !== input.classification || verified.evidence_digest !== input.evidence_digest || verified.evidence_source !== input.evidence_source || verified.reason_code !== input.reason_code) fail2("recovery_evidence_unverified");
          const eventEvidence = recoveryEventEvidence(input, envelopeDigest, evidence, o.phase);
          validateEvidence("observation_recorded", eventEvidence);
          const history = this.#db.prepare("SELECT * FROM manager_operation_events WHERE operation_id=? ORDER BY sequence").all(input.operation_id).map((e) => ({ ...e, evidence: JSON.parse(e.evidence_json) }));
          const existing = history.filter((e) => e.event_type === "observation_recorded");
          const currentClass = foldedRecoveryClassification(o, history);
          if (currentClass === "quarantine" && input.classification !== "quarantine") fail2("recovery_classification_downgrade");
          const recoveryExisting = recoveryEventsFor(history, o).filter((e) => e.active);
          const same = recoveryExisting.find((e) => e.evidence?.envelope_digest === envelopeDigest)?.event;
          const sameMaterial = recoveryExisting.find((e) => e.evidence.material_digest !== void 0 ? e.evidence.material_digest === eventEvidence.material_digest : recoveryMaterialDigest(e.event.operation_id, e.evidence, e.event.to_phase) === recoveryMaterialDigest(o.operation_id, eventEvidence, o.phase));
          const duplicate = same ?? sameMaterial?.event;
          if (duplicate) return {
            duplicate: true,
            operation_id: o.operation_id,
            task_id: o.task_id,
            attempt: o.attempt,
            generation: o.generation,
            revision: o.revision,
            event_sequence: duplicate.sequence,
            expected_revision: input.expected_revision,
            phase: o.phase,
            evidence_digest: duplicate.evidence?.evidence_digest ?? duplicate.evidence_digest,
            classification: input.classification,
            claim_id: o.claim_id,
            worker_identity_digest: o.claim_worker_identity_digest
          };
          const sameRevision = recoveryExisting.find((e) => e.evidence?.reason?.startsWith("recovery_") && e.evidence.expected_revision === input.expected_revision);
          if (sameRevision) fail2("recovery_observation_conflict");
          if (o.revision !== input.expected_revision) fail2("stale_recovery_cas");
          if (o.phase === "quarantined" && input.classification !== "quarantine") fail2("recovery_classification_downgrade");
          const at = (/* @__PURE__ */ new Date()).toISOString();
          const changed = this.#db.prepare("UPDATE manager_operations SET revision=revision+1 WHERE operation_id=? AND task_id=? AND attempt=? AND generation=? AND phase=? AND revision=? AND claim_id=? AND claim_generation=? AND claim_worker_identity_digest=?").run(o.operation_id, o.task_id, o.attempt, o.generation, o.phase, input.expected_revision, input.claim_id, input.generation, input.worker_identity_digest);
          if (changed.changes !== 1) fail2("stale_recovery_cas");
          this.#faultPoint("after_projection");
          this.#event(o.operation_id, input.expected_revision + 1, "observation_recorded", o.phase, o.phase, o.generation, eventEvidence, at);
          return {
            duplicate: false,
            operation_id: o.operation_id,
            task_id: o.task_id,
            attempt: o.attempt,
            generation: o.generation,
            revision: input.expected_revision + 1,
            event_sequence: input.expected_revision + 1,
            expected_revision: input.expected_revision,
            phase: o.phase,
            classification: input.classification,
            claim_id: o.claim_id,
            worker_identity_digest: o.claim_worker_identity_digest,
            evidence_digest: eventEvidence.evidence_digest
          };
        });
      }
      createLaunchIntent(input) {
        this.#assertWritable();
        if (!validLaunchRequest(input)) fail2("invalid_launch_intent");
        const tokenDigest = digest(input.launch_token);
        const intentDigest = digest({
          operation_id: input.operation_id,
          task_id: input.task_id,
          attempt: input.attempt,
          generation: input.generation,
          launch_id: input.launch_id,
          launch_epoch: input.launch_epoch,
          token_digest: tokenDigest
        });
        return this.#transaction(() => {
          const o = this.#attemptOperation(input);
          if (o.launch_id !== null) {
            if (o.launch_id !== input.launch_id || o.launch_epoch !== input.launch_epoch || o.launch_token_digest !== tokenDigest || o.launch_intent_digest !== intentDigest) fail2("launch_intent_conflict");
            return { duplicate: true, operation_id: o.operation_id, launch_id: o.launch_id, launch_epoch: o.launch_epoch, revision: o.revision, phase: o.phase, process_started: "unknown" };
          }
          if (this.#db.prepare("SELECT operation_id FROM manager_operations WHERE launch_id=?").get(input.launch_id)) fail2("launch_id_already_used");
          if (o.phase !== "reserved" || o.revision !== input.revision) fail2("stale_launch_cas");
          const current = this.#db.prepare("SELECT t.current_attempt,t.status AS task_status,a.status AS attempt_status,a.generation FROM tasks t JOIN attempts a ON a.task_id=t.task_id AND a.attempt=? WHERE t.task_id=?").get(input.attempt, input.task_id);
          if (!current || current.current_attempt !== input.attempt || current.task_status !== "queued" || current.attempt_status !== "queued" || current.generation !== input.generation)
            fail2("launch_task_attempt_not_queued");
          const at = (/* @__PURE__ */ new Date()).toISOString();
          const changed = this.#db.prepare("UPDATE manager_operations SET phase='launch_intent',revision=revision+1,launch_id=?,launch_epoch=?,launch_token_digest=?,launch_intent_digest=? WHERE operation_id=? AND task_id=? AND attempt=? AND generation=? AND phase='reserved' AND revision=?").run(input.launch_id, input.launch_epoch, tokenDigest, intentDigest, input.operation_id, input.task_id, input.attempt, input.generation, input.revision);
          if (changed.changes !== 1) fail2("stale_launch_cas");
          this.#faultPoint("after_projection");
          this.#event(
            input.operation_id,
            input.revision + 1,
            "launch_intent",
            "reserved",
            "launch_intent",
            input.generation,
            { launch_id: input.launch_id, launch_epoch: input.launch_epoch, token_digest: tokenDigest },
            at
          );
          return {
            duplicate: false,
            operation_id: input.operation_id,
            launch_id: input.launch_id,
            launch_epoch: input.launch_epoch,
            generation: input.generation,
            revision: input.revision + 1,
            event_sequence: input.revision + 1,
            phase: "launch_intent",
            intent_digest: intentDigest,
            process_started: "unknown"
          };
        });
      }
      recordLaunchReceipt(input) {
        this.#assertWritable();
        if (!validLaunchRequest(input) || !validId(input.receipt_id)) fail2("invalid_launch_receipt");
        fixtureLaunchIdentity(input.launch_identity);
        if (input.launch_identity.source === "manager_os_spawn_observation" && (input.launch_identity.launch_id !== input.launch_id || input.launch_identity.generation !== input.generation))
          fail2("trusted_launch_identity_binding_mismatch");
        const tokenDigest = digest(input.launch_token), identityJson = canonical3(input.launch_identity);
        const receiptDigest = digest({
          receipt_id: input.receipt_id,
          operation_id: input.operation_id,
          task_id: input.task_id,
          attempt: input.attempt,
          generation: input.generation,
          launch_id: input.launch_id,
          launch_epoch: input.launch_epoch,
          token_digest: tokenDigest,
          launch_identity: input.launch_identity
        });
        return this.#transaction(() => {
          const o = this.#attemptOperation(input);
          if (!o.launch_id) fail2("launch_intent_missing");
          const cancelled = this.#db.prepare("SELECT queued_cancel_id FROM attempts WHERE task_id=? AND attempt=?").get(o.task_id, o.attempt);
          if (cancelled?.queued_cancel_id !== null) fail2("launch_cancelled_before_claim");
          if (o.launch_id !== input.launch_id || o.launch_epoch !== input.launch_epoch || o.launch_token_digest !== tokenDigest) fail2("launch_receipt_intent_mismatch");
          if (o.launch_receipt_digest !== null) {
            if (o.launch_receipt_digest !== receiptDigest || o.launch_identity_json !== identityJson) fail2("launch_receipt_conflict");
            return { duplicate: true, operation_id: o.operation_id, launch_id: o.launch_id, revision: o.revision, phase: o.phase, process_started: "not_independently_verified", synthetic: input.launch_identity.source === "synthetic_fixture" };
          }
          if (this.#db.prepare("SELECT operation_id FROM manager_operations WHERE launch_receipt_id=?").get(input.receipt_id)) fail2("launch_receipt_id_already_used");
          if (o.phase !== "launch_intent" || o.revision !== input.revision) fail2("stale_launch_cas");
          const at = (/* @__PURE__ */ new Date()).toISOString();
          const changed = this.#db.prepare("UPDATE manager_operations SET revision=revision+1,launch_receipt_id=?,launch_receipt_digest=?,launch_identity_json=? WHERE operation_id=? AND task_id=? AND attempt=? AND generation=? AND phase='launch_intent' AND revision=? AND launch_id=? AND launch_epoch=? AND launch_token_digest=?").run(input.receipt_id, receiptDigest, identityJson, input.operation_id, input.task_id, input.attempt, input.generation, input.revision, input.launch_id, input.launch_epoch, tokenDigest);
          if (changed.changes !== 1) fail2("stale_launch_cas");
          this.#faultPoint("after_projection");
          this.#event(
            input.operation_id,
            input.revision + 1,
            "launch_receipt",
            "launch_intent",
            "launch_intent",
            input.generation,
            { launch_id: input.launch_id, launch_epoch: input.launch_epoch, token_digest: tokenDigest, receipt_digest: receiptDigest },
            at
          );
          return {
            duplicate: false,
            operation_id: input.operation_id,
            launch_id: input.launch_id,
            launch_epoch: input.launch_epoch,
            generation: input.generation,
            revision: input.revision + 1,
            event_sequence: input.revision + 1,
            phase: "launch_intent",
            receipt_digest: receiptDigest,
            process_started: "not_independently_verified",
            synthetic: input.launch_identity.source === "synthetic_fixture"
          };
        });
      }
      commitPermanentClaim(input) {
        this.#assertWritable();
        if (!validLaunchRequest(input) || !validId(input.claim_id)) fail2("invalid_claim");
        fixtureWorkerIdentity(input.worker_identity);
        const tokenDigest = digest(input.launch_token), workerJson = canonical3(input.worker_identity), workerDigest = digest(workerJson);
        const claimDigest = digest({
          claim_id: input.claim_id,
          operation_id: input.operation_id,
          task_id: input.task_id,
          attempt: input.attempt,
          generation: input.generation,
          launch_id: input.launch_id,
          launch_epoch: input.launch_epoch,
          token_digest: tokenDigest,
          worker_identity: input.worker_identity
        });
        return this.#transaction(() => {
          const o = this.#attemptOperation(input);
          if (o.claim_id !== null) {
            if (o.claim_id !== input.claim_id || o.claim_request_digest !== claimDigest || o.claim_worker_identity_json !== workerJson) fail2("claim_conflict");
            return { duplicate: true, operation_id: o.operation_id, claim_id: o.claim_id, revision: o.revision, phase: o.phase, claim_permanent: true, synthetic: input.worker_identity.source === "synthetic_fixture" };
          }
          if (this.#db.prepare("SELECT operation_id FROM manager_operations WHERE claim_id=?").get(input.claim_id)) fail2("claim_id_already_used");
          if (o.phase !== "launch_intent" || o.launch_receipt_digest === null) fail2("launch_receipt_required");
          if (o.launch_id !== input.launch_id || o.launch_epoch !== input.launch_epoch || o.launch_token_digest !== tokenDigest) fail2("claim_launch_mismatch");
          const launchIdentity = JSON.parse(o.launch_identity_json);
          if (input.worker_identity.process_id !== launchIdentity.process_id || input.worker_identity.start_fingerprint !== launchIdentity.start_fingerprint) fail2("claim_worker_launch_identity_mismatch");
          if (o.revision !== input.revision) fail2("stale_claim_cas");
          const current = this.#db.prepare("SELECT t.current_attempt,t.status AS task_status,a.status AS attempt_status FROM tasks t JOIN attempts a ON a.task_id=t.task_id WHERE t.task_id=? AND a.attempt=? AND a.generation=?").get(input.task_id, input.attempt, input.generation);
          if (!current || current.current_attempt !== input.attempt || current.task_status !== "queued" || current.attempt_status !== "queued") fail2("claim_attempt_not_current");
          const at = (/* @__PURE__ */ new Date()).toISOString();
          const changed = this.#db.prepare("UPDATE manager_operations SET phase='running',revision=revision+1,claim_id=?,claim_request_digest=?,claim_worker_identity_json=?,claim_worker_identity_digest=?,claim_launch_id=?,claim_generation=?,claim_token_digest=? WHERE operation_id=? AND task_id=? AND attempt=? AND generation=? AND phase='launch_intent' AND revision=? AND launch_id=? AND launch_epoch=? AND launch_token_digest=? AND launch_receipt_digest IS NOT NULL AND claim_id IS NULL").run(input.claim_id, claimDigest, workerJson, workerDigest, input.launch_id, input.generation, tokenDigest, input.operation_id, input.task_id, input.attempt, input.generation, input.revision, input.launch_id, input.launch_epoch, tokenDigest);
          if (changed.changes !== 1) fail2("stale_claim_cas");
          const attemptChanged = this.#db.prepare("UPDATE attempts SET status='running' WHERE task_id=? AND attempt=? AND generation=? AND status='queued'").run(input.task_id, input.attempt, input.generation);
          if (attemptChanged.changes !== 1) fail2("claim_attempt_status_conflict");
          const taskChanged = this.#db.prepare("UPDATE tasks SET status='running' WHERE task_id=? AND current_attempt=? AND status='queued'").run(input.task_id, input.attempt);
          if (taskChanged.changes !== 1) fail2("claim_task_status_conflict");
          this.#faultPoint("after_projection");
          this.#event(
            input.operation_id,
            input.revision + 1,
            "claim_committed",
            "launch_intent",
            "running",
            input.generation,
            { claim_id: input.claim_id, launch_id: input.launch_id, launch_epoch: input.launch_epoch, token_digest: tokenDigest, worker_identity_digest: workerDigest },
            at
          );
          return {
            duplicate: false,
            operation_id: input.operation_id,
            claim_id: input.claim_id,
            launch_id: input.launch_id,
            generation: input.generation,
            revision: input.revision + 1,
            event_sequence: input.revision + 1,
            phase: "running",
            claim_permanent: true,
            synthetic: input.worker_identity.source === "synthetic_fixture"
          };
        });
      }
      commitResult(input) {
        this.#assertWritable();
        if (!validId(input?.operation_id) || !validId(input?.task_id) || !Number.isSafeInteger(input?.attempt) || input.attempt < 1 || !Number.isSafeInteger(input?.generation) || input.generation < 1 || !Number.isSafeInteger(input?.revision) || input.revision < 1 || !validId(input?.claim_id) || !RESULT_STATUSES2.has(input?.result_status) || typeof input?.claim_worker_identity_digest !== "string" || !/^[0-9a-f]{64}$/u.test(input.claim_worker_identity_digest)) fail2("invalid_result_commit");
        if (input.result_status === "cancelled" ? typeof input.cancel_verification_digest !== "string" || !/^[0-9a-f]{64}$/u.test(input.cancel_verification_digest) : Object.hasOwn(input, "cancel_verification_digest")) fail2("invalid_result_commit");
        const resultJson = canonicalTaskResult2(input.result, input);
        const resultDigest = digest({ result_contract_version: RESULT_CONTRACT_VERSION, result_status: input.result_status, result: JSON.parse(resultJson) });
        const commitRef = `result-${resultDigest}`;
        return this.#transaction(() => {
          const o = this.#attemptOperation(input);
          this.#assertRecoveryNotLatched(o.operation_id);
          this.#assertNoUnknownInteraction(o.operation_id);
          if (o.claim_id !== input.claim_id || o.claim_generation !== input.generation || o.claim_worker_identity_digest !== input.claim_worker_identity_digest) fail2("result_claim_mismatch");
          if (o.result_digest !== null) {
            if (o.result_generation !== input.generation) fail2("result_generation_mismatch");
            const resultEvent = this.#db.prepare("SELECT sequence FROM manager_operation_events WHERE operation_id=? AND event_type='result_committed'").get(input.operation_id);
            if (!resultEvent || input.revision !== resultEvent.sequence - 1) fail2("stale_result_cas");
            if (o.result_digest === resultDigest && o.result_status === input.result_status && o.result_json === resultJson && o.result_commit_ref === commitRef) {
              if (input.result_status === "cancelled") {
                const persisted = this.#db.prepare("SELECT evidence_json FROM manager_operation_events WHERE operation_id=? AND sequence=?").get(input.operation_id, resultEvent.sequence);
                if (!persisted || JSON.parse(persisted.evidence_json).cancel_verification_digest !== input.cancel_verification_digest) fail2("result_cancellation_evidence_mismatch");
              }
              return {
                duplicate: true,
                conflict: false,
                operation_id: o.operation_id,
                task_id: o.task_id,
                attempt: o.attempt,
                generation: o.generation,
                claim_id: o.claim_id,
                revision: o.revision,
                phase: o.phase,
                result_status: o.result_status,
                result_digest: o.result_digest,
                result_commit_ref: o.result_commit_ref
              };
            }
            if (input.result_status === "cancelled" && o.result_status !== "cancelled") {
              const cancelIntent = this.#db.prepare("SELECT evidence_json FROM manager_operation_events WHERE operation_id=? AND event_type='observation_recorded'").all(input.operation_id).some((row) => JSON.parse(row.evidence_json).reason === "cancel_requested");
              if (cancelIntent) return {
                duplicate: false,
                conflict: false,
                cancellation_lost_to_result: true,
                operation_id: o.operation_id,
                task_id: o.task_id,
                attempt: o.attempt,
                generation: o.generation,
                revision: o.revision,
                phase: o.phase,
                result_status: o.result_status,
                result_digest: o.result_digest,
                result_commit_ref: o.result_commit_ref
              };
            }
            const quarantineEvent = this.#db.prepare("SELECT sequence,evidence_json FROM manager_operation_events WHERE operation_id=? AND event_type='quarantined' ORDER BY sequence").all(input.operation_id).map((row) => ({ ...row, evidence: JSON.parse(row.evidence_json) })).find((row) => row.evidence.reason === "result_conflict");
            if (o.phase === "quarantined") {
              if (quarantineEvent?.evidence.result_digest === resultDigest) return {
                duplicate: true,
                conflict: true,
                quarantined: true,
                operation_id: o.operation_id,
                generation: o.generation,
                revision: o.revision,
                result_digest: o.result_digest,
                conflict_evidence_digest: quarantineEvent.evidence.evidence_digest
              };
              fail2("result_quarantine_exists");
            }
            if (o.phase === "released") {
              this.#poison("result_conflict_after_release", digest({ operation_id: o.operation_id, claim_id: o.claim_id, generation: o.generation, existing_result_digest: o.result_digest, conflicting_result_digest: resultDigest }));
              fail2("result_conflict_after_release");
            }
            const quarantineDigest = digest({
              result_contract_version: RESULT_CONTRACT_VERSION,
              reason: "result_conflict",
              operation_id: o.operation_id,
              claim_id: o.claim_id,
              generation: o.generation,
              existing_result_digest: o.result_digest,
              conflicting_result_digest: resultDigest
            });
            const at2 = (/* @__PURE__ */ new Date()).toISOString();
            const changed2 = this.#db.prepare("UPDATE manager_operations SET phase='quarantined',revision=revision+1 WHERE operation_id=? AND task_id=? AND attempt=? AND generation=? AND phase=? AND revision=? AND claim_id=? AND claim_generation=? AND claim_worker_identity_digest=? AND result_digest=?").run(o.operation_id, o.task_id, o.attempt, o.generation, o.phase, o.revision, input.claim_id, input.generation, input.claim_worker_identity_digest, o.result_digest);
            if (changed2.changes !== 1) fail2("stale_result_cas");
            this.#faultPoint("after_projection");
            this.#event(
              o.operation_id,
              o.revision + 1,
              "quarantined",
              o.phase,
              "quarantined",
              o.generation,
              { claim_id: o.claim_id, reason: "result_conflict", result_digest: resultDigest, result_commit_ref: commitRef, evidence_digest: quarantineDigest },
              at2
            );
            return {
              duplicate: false,
              conflict: true,
              quarantined: true,
              operation_id: o.operation_id,
              generation: o.generation,
              revision: o.revision + 1,
              result_digest: o.result_digest,
              conflict_evidence_digest: quarantineDigest
            };
          }
          if (o.phase !== "running" || o.revision !== input.revision) fail2("stale_result_cas");
          if (input.result_status === "cancelled") {
            const observations = this.#db.prepare("SELECT * FROM manager_operation_events WHERE operation_id=? AND event_type='observation_recorded' ORDER BY sequence").all(input.operation_id).map((event) => ({ ...event, evidence: JSON.parse(event.evidence_json) }));
            const intent = observations.find((event) => event.evidence.reason === "cancel_requested");
            const verification = observations.find((event) => event.evidence.reason === "cancel_tree_verified" && event.evidence_digest === input.cancel_verification_digest);
            if (!intent || !verification || verification.sequence <= intent.sequence || verification.evidence.cancel_id !== intent.evidence.cancel_id || verification.evidence.claim_id !== input.claim_id || verification.evidence.worker_identity_digest !== input.claim_worker_identity_digest || verification.evidence_digest !== input.cancel_verification_digest) fail2("cancel_verification_required");
            const resolutions = observations.filter((event) => event.evidence.reason === "cancel_recovery_resolved");
            if (resolutions.length && resolutions.at(-1).evidence.cancellation_verification_digest !== input.cancel_verification_digest)
              fail2("cancel_verification_required");
          }
          const current = this.#db.prepare("SELECT t.status AS task_status,t.current_attempt,a.status AS attempt_status FROM tasks t JOIN attempts a ON a.task_id=t.task_id WHERE t.task_id=? AND a.attempt=? AND a.generation=?").get(input.task_id, input.attempt, input.generation);
          if (!current || current.current_attempt !== input.attempt || current.task_status !== "running" || current.attempt_status !== "running") fail2("result_attempt_not_running");
          const at = (/* @__PURE__ */ new Date()).toISOString();
          const changed = this.#db.prepare("UPDATE manager_operations SET phase='result_committed',revision=revision+1,result_status=?,result_generation=?,result_digest=?,result_json=?,result_commit_ref=? WHERE operation_id=? AND task_id=? AND attempt=? AND generation=? AND phase='running' AND revision=? AND claim_id=? AND claim_generation=? AND claim_worker_identity_digest=? AND result_digest IS NULL").run(input.result_status, input.generation, resultDigest, resultJson, commitRef, input.operation_id, input.task_id, input.attempt, input.generation, input.revision, input.claim_id, input.generation, input.claim_worker_identity_digest);
          if (changed.changes !== 1) fail2("stale_result_cas");
          const attempt = this.#db.prepare("UPDATE attempts SET status=? WHERE task_id=? AND attempt=? AND generation=? AND status='running'").run(input.result_status, input.task_id, input.attempt, input.generation);
          if (attempt.changes !== 1) fail2("result_attempt_status_conflict");
          const task = this.#db.prepare("UPDATE tasks SET status=? WHERE task_id=? AND current_attempt=? AND status='running'").run(input.result_status, input.task_id, input.attempt);
          if (task.changes !== 1) fail2("result_task_status_conflict");
          this.#faultPoint("after_projection");
          this.#event(
            input.operation_id,
            input.revision + 1,
            "result_committed",
            "running",
            "result_committed",
            input.generation,
            {
              claim_id: input.claim_id,
              outcome: input.result_status,
              result_commit_ref: commitRef,
              result_digest: resultDigest,
              worker_identity_digest: input.claim_worker_identity_digest,
              ...input.result_status === "cancelled" ? { cancel_verification_digest: input.cancel_verification_digest } : {}
            },
            at
          );
          return {
            duplicate: false,
            conflict: false,
            operation_id: o.operation_id,
            task_id: o.task_id,
            attempt: o.attempt,
            generation: o.generation,
            claim_id: o.claim_id,
            revision: input.revision + 1,
            event_sequence: input.revision + 1,
            phase: "result_committed",
            result_status: input.result_status,
            result_digest: resultDigest,
            result_commit_ref: commitRef
          };
        });
      }
      /** Persist an operation-scoped cleanup intent before any external OS cleanup is attempted. */
      beginCleanup(input) {
        this.#assertWritable();
        if (!validCleanupRequest(input)) fail2("invalid_cleanup_request");
        return this.#transaction(() => {
          const o = this.#attemptOperation(input);
          this.#assertRecoveryNotLatched(o.operation_id);
          this.#assertNoUnknownInteraction(o.operation_id);
          if (o.claim_id !== input.claim_id || o.claim_generation !== input.generation || o.claim_worker_identity_digest !== input.claim_worker_identity_digest) fail2("cleanup_claim_mismatch");
          if (o.phase === "cleanup_pending") {
            const prior = this.#db.prepare("SELECT * FROM manager_operation_events WHERE operation_id=? AND event_type='cleanup_pending'").get(input.operation_id);
            const evidence = prior && JSON.parse(prior.evidence_json);
            if (prior && prior.sequence === input.revision + 1 && evidence.claim_id === input.claim_id && evidence.result_commit_ref === o.result_commit_ref && evidence.worker_identity_digest === input.claim_worker_identity_digest) return { duplicate: true, operation_id: o.operation_id, generation: o.generation, revision: o.revision, phase: o.phase };
            fail2("cleanup_pending_conflict");
          }
          if (o.phase !== "result_committed" || o.revision !== input.revision || o.result_digest === null || o.result_commit_ref === null) fail2("cleanup_result_not_committed");
          const changed = this.#db.prepare("UPDATE manager_operations SET phase='cleanup_pending',revision=revision+1 WHERE operation_id=? AND task_id=? AND attempt=? AND generation=? AND phase='result_committed' AND revision=? AND claim_id=? AND claim_generation=? AND claim_worker_identity_digest=? AND result_digest IS NOT NULL").run(input.operation_id, input.task_id, input.attempt, input.generation, input.revision, input.claim_id, input.generation, input.claim_worker_identity_digest);
          if (changed.changes !== 1) fail2("stale_cleanup_cas");
          const at = (/* @__PURE__ */ new Date()).toISOString();
          this.#faultPoint("after_projection");
          this.#event(
            input.operation_id,
            input.revision + 1,
            "cleanup_pending",
            "result_committed",
            "cleanup_pending",
            input.generation,
            { claim_id: input.claim_id, result_commit_ref: o.result_commit_ref, worker_identity_digest: input.claim_worker_identity_digest },
            at
          );
          return { duplicate: false, operation_id: o.operation_id, generation: o.generation, revision: input.revision + 1, event_sequence: input.revision + 1, phase: "cleanup_pending" };
        });
      }
      /** Persist only evidence supplied after an external, operation-scoped cleanup attempt. */
      recordCleanupEvidence(input) {
        this.#assertWritable();
        if (!validCleanupRequest(input) || !["verified", "unverified"].includes(input?.outcome)) fail2("invalid_cleanup_request");
        let normalized = null, cleanupDigest = null;
        if (input.outcome === "verified") {
          normalized = normalizeCleanupEvidence(input.cleanup_evidence, input);
          cleanupDigest = digest({ cleanup_contract_version: 1, evidence: normalized });
        } else if (!["alive", "unknown", "identity_mismatch", "incomplete"].includes(input?.probe_state) || !validText2(input?.reason, 128)) fail2("invalid_cleanup_outcome");
        return this.#transaction(() => {
          const o = this.#attemptOperation(input);
          this.#assertRecoveryNotLatched(o.operation_id);
          this.#assertNoUnknownInteraction(o.operation_id);
          if (o.claim_id !== input.claim_id || o.claim_generation !== input.generation || o.claim_worker_identity_digest !== input.claim_worker_identity_digest) fail2("cleanup_claim_mismatch");
          if (o.launch_receipt_digest === null || o.result_commit_ref === null || o.result_digest === null) fail2("cleanup_prerequisite_missing");
          if (input.outcome === "verified" && (normalized.launch_receipt_digest !== o.launch_receipt_digest || normalized.result_commit_ref !== o.result_commit_ref)) fail2("cleanup_evidence_identity_mismatch");
          if (input.outcome === "verified") {
            const worker = JSON.parse(o.claim_worker_identity_json), launchIdentity = JSON.parse(o.launch_identity_json);
            if (normalized.root_process_id !== worker.process_id || normalized.root_start_fingerprint !== worker.start_fingerprint || normalized.root_process_id !== launchIdentity.process_id || normalized.root_start_fingerprint !== launchIdentity.start_fingerprint) fail2("cleanup_worker_identity_mismatch");
          }
          const finalType = input.outcome === "verified" ? "cleanup_verified" : "cleanup_unverified";
          const final = this.#db.prepare("SELECT * FROM manager_operation_events WHERE operation_id=? AND event_type IN ('cleanup_verified','cleanup_unverified')").get(input.operation_id);
          if (final) {
            const evidence = JSON.parse(final.evidence_json);
            const same = input.outcome === "verified" ? final.event_type === "cleanup_verified" && evidence.cleanup_digest === cleanupDigest : final.event_type === "cleanup_unverified" && evidence.probe_state === input.probe_state && evidence.reason === input.reason;
            if (same && final.sequence === input.revision + 1 && (o.phase === finalType || o.phase === "released")) return {
              duplicate: true,
              operation_id: o.operation_id,
              generation: o.generation,
              revision: final.sequence,
              phase: o.phase,
              cleanup_verified: input.outcome === "verified",
              cleanup_digest: input.outcome === "verified" ? evidence.cleanup_digest : void 0
            };
            if (o.phase === "released") {
              this.#poison("cleanup_evidence_conflict_after_release", digest({ operation_id: o.operation_id, generation: o.generation, cleanup_digest: cleanupDigest ?? null }));
              fail2("cleanup_result_conflict_after_release");
            }
            fail2("cleanup_evidence_conflict");
          }
          if (o.phase !== "cleanup_pending" || o.revision !== input.revision) fail2("stale_cleanup_cas");
          const at = (/* @__PURE__ */ new Date()).toISOString();
          const next = input.outcome === "verified" ? "cleanup_verified" : "cleanup_unverified";
          const changed = this.#db.prepare("UPDATE manager_operations SET phase=?,revision=revision+1 WHERE operation_id=? AND task_id=? AND attempt=? AND generation=? AND phase='cleanup_pending' AND revision=? AND claim_id=? AND claim_generation=? AND claim_worker_identity_digest=? AND result_commit_ref=?").run(next, input.operation_id, input.task_id, input.attempt, input.generation, input.revision, input.claim_id, input.generation, input.claim_worker_identity_digest, o.result_commit_ref);
          if (changed.changes !== 1) fail2("stale_cleanup_cas");
          this.#faultPoint("after_projection");
          if (input.outcome === "verified") {
            const eventEvidence = {
              claim_id: input.claim_id,
              cleanup_digest: cleanupDigest,
              evidence_source: normalized.source,
              launch_receipt_digest: normalized.launch_receipt_digest,
              operation_resources_complete: normalized.operation_resources_complete,
              process_tree_digest: normalized.process_tree_digest,
              resources_digest: normalized.resources_digest,
              result_commit_ref: normalized.result_commit_ref,
              root_process_id: normalized.root_process_id,
              root_start_fingerprint: normalized.root_start_fingerprint,
              worker_identity_digest: input.claim_worker_identity_digest,
              worker_tree_complete: normalized.worker_tree_complete,
              workspace_touched: normalized.workspace_touched,
              ...normalized.adapter_cleanup !== void 0 ? { adapter_cleanup: normalized.adapter_cleanup } : {}
            };
            this.#event(input.operation_id, input.revision + 1, "cleanup_verified", "cleanup_pending", "cleanup_verified", input.generation, eventEvidence, at);
          } else {
            this.#event(
              input.operation_id,
              input.revision + 1,
              "cleanup_unverified",
              "cleanup_pending",
              "cleanup_unverified",
              input.generation,
              { claim_id: input.claim_id, probe_state: input.probe_state, reason: input.reason, worker_identity_digest: input.claim_worker_identity_digest },
              at
            );
          }
          return {
            duplicate: false,
            operation_id: o.operation_id,
            generation: o.generation,
            revision: input.revision + 1,
            event_sequence: input.revision + 1,
            phase: next,
            cleanup_verified: input.outcome === "verified",
            cleanup_digest: cleanupDigest
          };
        });
      }
      /** Replace a prior cleanup-unknown outcome only with fresh, complete, operation-bound evidence.
       * The re-verification event, exact cleanup-Hold resolution, and normal verified projection are atomic.
       */
      reverifyCleanup(input) {
        this.#assertWritable();
        if (!validCleanupRequest(input) || !input.cleanup_evidence) fail2("invalid_cleanup_reverification");
        const normalized = normalizeCleanupEvidence(input.cleanup_evidence, input);
        const cleanupDigest = digest({ cleanup_contract_version: 1, evidence: normalized });
        return this.#transaction(() => {
          const o = this.#attemptOperation(input);
          this.#assertNoUnknownInteraction(o.operation_id);
          if (o.claim_id !== input.claim_id || o.claim_generation !== input.generation || o.claim_worker_identity_digest !== input.claim_worker_identity_digest || o.launch_receipt_digest !== normalized.launch_receipt_digest || o.result_commit_ref !== normalized.result_commit_ref || o.result_digest === null) fail2("cleanup_reverification_identity_mismatch");
          const history = this.#db.prepare("SELECT * FROM manager_operation_events WHERE operation_id=? ORDER BY sequence").all(o.operation_id).map((event) => ({ ...event, evidence: JSON.parse(event.evidence_json) }));
          const unverified = history.filter((event) => event.event_type === "cleanup_unverified");
          if (unverified.length !== 1 || unverified[0].evidence.claim_id !== o.claim_id || unverified[0].evidence.worker_identity_digest !== o.claim_worker_identity_digest) fail2("cleanup_unverified_event_missing_or_conflicting");
          const priorReverification = history.find((event) => event.event_type === "cleanup_reverified");
          if (priorReverification && (o.phase === "cleanup_verified" || o.phase === "released") && o.revision >= input.revision + 2 && priorReverification.from_phase === "cleanup_unverified" && priorReverification.to_phase === "cleanup_reverified" && priorReverification.evidence.prior_cleanup_event_digest === unverified[0].evidence_digest && priorReverification.evidence.cleanup_digest === cleanupDigest && history.some((event) => event.event_type === "cleanup_verified" && event.evidence.cleanup_digest === cleanupDigest && event.sequence === priorReverification.sequence + 1)) {
            const verified = history.find((event) => event.event_type === "cleanup_verified" && event.evidence.cleanup_digest === cleanupDigest);
            const resolved = recoveryEventsFor(history, o).filter((event) => event.event.sequence < priorReverification.sequence).map((event) => event.event.evidence_digest).sort();
            return {
              duplicate: true,
              operation_id: o.operation_id,
              task_id: o.task_id,
              attempt: o.attempt,
              generation: o.generation,
              claim_id: o.claim_id,
              revision: o.revision,
              event_sequence: verified.sequence,
              phase: o.phase,
              cleanup_verified: true,
              cleanup_digest: cleanupDigest,
              resolved_recovery_event_digests: resolved
            };
          }
          if (o.phase !== "cleanup_unverified" || o.revision !== input.revision) fail2("stale_cleanup_reverification_cas");
          if (priorReverification) fail2("cleanup_reverification_already_committed");
          const recovery = recoveryEventsFor(history, o);
          const active = recovery.filter((event) => event.active);
          if (active.some((event) => event.evidence.classification !== "hold" || !["cleanup_identity_unknown", "cleanup_incomplete"].includes(event.evidence.reason_code))) fail2("cleanup_reverification_blocked_by_unrelated_hold");
          const resolvedDigests = active.map((event) => event.event.evidence_digest).sort();
          const changed = this.#db.prepare("UPDATE manager_operations SET phase='cleanup_reverified',revision=revision+1 WHERE operation_id=? AND task_id=? AND attempt=? AND generation=? AND phase='cleanup_unverified' AND revision=? AND claim_id=? AND claim_generation=? AND claim_worker_identity_digest=? AND result_commit_ref=?").run(o.operation_id, o.task_id, o.attempt, o.generation, input.revision, o.claim_id, o.generation, o.claim_worker_identity_digest, o.result_commit_ref);
          if (changed.changes !== 1) fail2("stale_cleanup_reverification_cas");
          const baseEvidence = {
            claim_id: o.claim_id,
            cleanup_digest: cleanupDigest,
            evidence_source: normalized.source,
            launch_receipt_digest: normalized.launch_receipt_digest,
            operation_resources_complete: true,
            process_tree_digest: normalized.process_tree_digest,
            resources_digest: normalized.resources_digest,
            result_commit_ref: o.result_commit_ref,
            root_process_id: normalized.root_process_id,
            root_start_fingerprint: normalized.root_start_fingerprint,
            worker_identity_digest: o.claim_worker_identity_digest,
            worker_tree_complete: true,
            workspace_touched: false,
            ...normalized.adapter_cleanup !== void 0 ? { adapter_cleanup: normalized.adapter_cleanup } : {}
          };
          const reverifiedEvidence = {
            ...baseEvidence,
            operation_id: o.operation_id,
            task_id: o.task_id,
            attempt: o.attempt,
            generation: o.generation,
            prior_cleanup_event_digest: unverified[0].evidence_digest,
            ...resolvedRecoveryCommitment(resolvedDigests)
          };
          validateEvidence("cleanup_reverified", reverifiedEvidence);
          const at = (/* @__PURE__ */ new Date()).toISOString();
          this.#event(o.operation_id, input.revision + 1, "cleanup_reverified", "cleanup_unverified", "cleanup_reverified", o.generation, reverifiedEvidence, at);
          this.#faultPoint("after_cleanup_reverification_event");
          const finalized = this.#db.prepare("UPDATE manager_operations SET phase='cleanup_verified',revision=revision+1 WHERE operation_id=? AND task_id=? AND attempt=? AND generation=? AND phase='cleanup_reverified' AND revision=? AND claim_id=? AND claim_generation=? AND claim_worker_identity_digest=?").run(o.operation_id, o.task_id, o.attempt, o.generation, input.revision + 1, o.claim_id, o.generation, o.claim_worker_identity_digest);
          if (finalized.changes !== 1) fail2("stale_cleanup_reverification_finalize");
          this.#event(o.operation_id, input.revision + 2, "cleanup_verified", "cleanup_reverified", "cleanup_verified", o.generation, baseEvidence, at);
          return {
            duplicate: false,
            operation_id: o.operation_id,
            task_id: o.task_id,
            attempt: o.attempt,
            generation: o.generation,
            claim_id: o.claim_id,
            revision: input.revision + 2,
            event_sequence: input.revision + 2,
            phase: "cleanup_verified",
            cleanup_verified: true,
            cleanup_digest: cleanupDigest,
            resolved_recovery_event_digests: resolvedDigests
          };
        });
      }
      /** Release only this operation's capacity slot after persisted verified cleanup evidence. */
      releaseCapacity(input) {
        this.#assertWritable();
        if (!validCleanupRequest(input) || typeof input.cleanup_digest !== "string" || !/^[0-9a-f]{64}$/u.test(input.cleanup_digest)) fail2("invalid_release_request");
        return this.#transaction(() => {
          const o = this.#attemptOperation(input);
          this.#assertRecoveryNotLatched(o.operation_id);
          this.#assertNoUnknownInteraction(o.operation_id);
          if (o.claim_id !== input.claim_id || o.claim_generation !== input.generation || o.claim_worker_identity_digest !== input.claim_worker_identity_digest) fail2("release_claim_mismatch");
          const verified = this.#db.prepare("SELECT * FROM manager_operation_events WHERE operation_id=? AND event_type='cleanup_verified'").get(input.operation_id);
          const release = this.#db.prepare("SELECT * FROM manager_operation_events WHERE operation_id=? AND event_type='released'").get(input.operation_id);
          if (o.phase === "released") {
            const e = release && JSON.parse(release.evidence_json);
            if (release && (release.sequence === input.revision + 1 || input.revision === o.revision) && e.claim_id === input.claim_id && e.cleanup_digest === input.cleanup_digest && e.worker_identity_digest === input.claim_worker_identity_digest) return {
              duplicate: true,
              operation_id: o.operation_id,
              generation: o.generation,
              revision: release.sequence,
              phase: "released",
              capacity_released: true
            };
            this.#poison("release_conflict_after_release", digest({ operation_id: o.operation_id, generation: o.generation, cleanup_digest: input.cleanup_digest }));
            fail2("release_conflict_after_release");
          }
          if (o.phase !== "cleanup_verified" || o.revision !== input.revision || !verified) fail2("cleanup_not_verified");
          const evidence = JSON.parse(verified.evidence_json);
          if (evidence.cleanup_digest !== input.cleanup_digest || evidence.claim_id !== input.claim_id || evidence.worker_identity_digest !== input.claim_worker_identity_digest || evidence.launch_receipt_digest !== o.launch_receipt_digest || evidence.result_commit_ref !== o.result_commit_ref) fail2("release_cleanup_evidence_mismatch");
          const projection = this.#db.prepare("SELECT t.status AS task_status,t.current_attempt,a.status AS attempt_status FROM tasks t JOIN attempts a ON a.task_id=t.task_id WHERE t.task_id=? AND a.attempt=? AND a.generation=?").get(o.task_id, o.attempt, o.generation);
          if (!projection || projection.current_attempt !== o.attempt || projection.task_status !== o.result_status || projection.attempt_status !== o.result_status || o.result_generation !== o.generation || o.result_digest === null) fail2("release_result_projection_mismatch");
          const changed = this.#db.prepare("UPDATE manager_operations SET phase='released',revision=revision+1 WHERE operation_id=? AND task_id=? AND attempt=? AND generation=? AND phase='cleanup_verified' AND revision=? AND claim_id=? AND claim_generation=? AND claim_worker_identity_digest=? AND result_digest IS NOT NULL").run(input.operation_id, input.task_id, input.attempt, input.generation, input.revision, input.claim_id, input.generation, input.claim_worker_identity_digest);
          if (changed.changes !== 1) fail2("stale_release_cas");
          this.#faultPoint("after_projection");
          this.#event(
            input.operation_id,
            input.revision + 1,
            "released",
            "cleanup_verified",
            "released",
            input.generation,
            { claim_id: input.claim_id, cleanup_digest: input.cleanup_digest, result_commit_ref: o.result_commit_ref, worker_identity_digest: input.claim_worker_identity_digest },
            (/* @__PURE__ */ new Date()).toISOString()
          );
          return { duplicate: false, operation_id: o.operation_id, generation: o.generation, revision: input.revision + 1, event_sequence: input.revision + 1, phase: "released", capacity_released: true };
        });
      }
      #cancellationWorker(input, o) {
        if (!o.claim_id || o.claim_id !== input.claim_id || o.claim_generation !== input.generation || o.claim_worker_identity_digest !== input.claim_worker_identity_digest || !o.claim_worker_identity_json || !o.launch_identity_json)
          fail2("cancellation_claim_mismatch");
        fixtureWorkerIdentity(input.worker_identity);
        const workerJson = canonical3(input.worker_identity);
        if (workerJson !== o.claim_worker_identity_json || digest(workerJson) !== o.claim_worker_identity_digest) fail2("cancellation_worker_identity_mismatch");
        let launchIdentity;
        try {
          launchIdentity = JSON.parse(o.launch_identity_json);
        } catch {
          fail2("launch_identity_invalid");
        }
        if (input.worker_identity.process_id !== launchIdentity.process_id || input.worker_identity.start_fingerprint !== launchIdentity.start_fingerprint)
          fail2("cancellation_worker_identity_mismatch");
        return input.worker_identity;
      }
      #attemptOperation(input) {
        const o = this.#db.prepare("SELECT * FROM manager_operations WHERE operation_id=? AND operation_kind='attempt_lifecycle'").get(input.operation_id);
        if (!o) fail2("operation_not_found");
        if (o.task_id !== input.task_id || o.attempt !== input.attempt || o.generation !== input.generation) fail2("operation_identity_mismatch");
        return o;
      }
      #assertRecoveryNotLatched(operationId) {
        const operation = this.#db.prepare("SELECT * FROM manager_operations WHERE operation_id=?").get(operationId);
        if (!operation) fail2("operation_not_found");
        const events = this.#db.prepare("SELECT * FROM manager_operation_events WHERE operation_id=? ORDER BY sequence").all(operationId);
        if (recoveryEventsFor(events, operation).some((event) => event.active)) fail2("operation_recovery_latched");
      }
      #assertInteractionRunning(o, input) {
        if (o.operation_kind !== "attempt_lifecycle" || o.phase !== "running" || o.task_id !== input.task_id || o.attempt !== input.attempt || o.generation !== input.generation || o.claim_id !== input.claim_id || o.claim_generation !== o.generation || o.claim_worker_identity_digest !== input.worker_identity_digest) fail2("interaction_identity_mismatch");
        const projection = this.#db.prepare("SELECT t.current_attempt,t.status AS task_status,a.status AS attempt_status,a.generation FROM tasks t JOIN attempts a ON a.task_id=t.task_id AND a.attempt=? WHERE t.task_id=?").get(o.attempt, o.task_id);
        if (!projection || projection.current_attempt !== o.attempt || projection.task_status !== "running" || projection.attempt_status !== "running" || projection.generation !== o.generation) fail2("interaction_task_projection_mismatch");
      }
      #assertNoUnknownInteraction(operationId) {
        const rows = this.#db.prepare("SELECT event_type,evidence_json FROM manager_operation_events WHERE operation_id=? AND event_type IN ('interaction_reply_intent','interaction_reply_accepted') ORDER BY sequence").all(operationId);
        const pending = /* @__PURE__ */ new Set();
        for (const row of rows) {
          const requestId = JSON.parse(row.evidence_json).request_id;
          if (row.event_type === "interaction_reply_intent") pending.add(requestId);
          else pending.delete(requestId);
        }
        if (pending.size) fail2("interaction_reply_outcome_unknown");
      }
      #assertNoUnansweredInteraction(operationId) {
        const rows = this.#db.prepare("SELECT event_type,evidence_json FROM manager_operation_events WHERE operation_id=? AND event_type IN ('interaction_requested','interaction_reply_accepted') ORDER BY sequence").all(operationId);
        const pending = /* @__PURE__ */ new Set();
        for (const row of rows) {
          const requestId = JSON.parse(row.evidence_json).request_id;
          if (row.event_type === "interaction_requested") pending.add(requestId);
          else pending.delete(requestId);
        }
        if (pending.size) fail2("interaction_reply_outcome_unknown");
      }
      #assertNoCancellationIntent(operationId) {
        const rows = this.#db.prepare("SELECT evidence_json FROM manager_operation_events WHERE operation_id=? AND event_type='observation_recorded'").all(operationId);
        if (rows.some((row) => {
          try {
            return JSON.parse(row.evidence_json).reason === "cancel_requested";
          } catch {
            fail2("database_unreadable");
          }
        }))
          fail2("interaction_cancel_intent_present");
      }
      #readConsistent(read) {
        this.#assertOpen();
        this.#db.exec("BEGIN");
        try {
          this.#db.prepare("SELECT name FROM sqlite_schema LIMIT 1").get();
          const external = this.#db.prepare("PRAGMA data_version").get().data_version;
          const local = this.#db.prepare("SELECT total_changes() AS n").get().n;
          const snapshot = `${external}:${local}`;
          if (this.#validatedSnapshot !== snapshot) {
            this.#validateContents();
            this.#validatedSnapshot = snapshot;
          }
          const result = read();
          this.#db.exec("COMMIT");
          return result;
        } catch (e) {
          try {
            this.#db.exec("ROLLBACK");
          } catch {
          }
          throw e;
        }
      }
      #nextEventCursor() {
        const row = this.#db.prepare("UPDATE authority_metadata SET next_event_cursor=next_event_cursor+1 WHERE singleton=1 AND next_event_cursor<9007199254740991 RETURNING next_event_cursor").get();
        if (!row || !Number.isSafeInteger(row.next_event_cursor) || row.next_event_cursor < 1) fail2("event_cursor_exhausted");
        const sequence = this.#db.prepare("SELECT seq FROM sqlite_sequence WHERE name='manager_operation_events'").get();
        if (sequence && (!Number.isSafeInteger(sequence.seq) || sequence.seq < 0 || sequence.seq > row.next_event_cursor)) fail2("event_cursor_invalid");
        const changed = this.#db.prepare("UPDATE sqlite_sequence SET seq=? WHERE name='manager_operation_events'").run(row.next_event_cursor);
        if (changed.changes === 0) this.#db.prepare("INSERT INTO sqlite_sequence(name,seq) VALUES('manager_operation_events',?)").run(row.next_event_cursor);
        else if (changed.changes !== 1) fail2("event_cursor_invalid");
        return row.next_event_cursor;
      }
      // Historical JSON projections remain immutable and validated, but they are
      // no longer public business objects. Task-scoped import artifacts are the
      // stable provenance marker for a migrated-only Task; native Tasks created
      // after the authority switch never gain this marker.
      #isRetiredHistoricalTask(taskId) {
        return Boolean(this.#db.prepare(`SELECT 1 WHERE
      EXISTS(SELECT 1 FROM migrated_task_results WHERE task_id=?)
      OR EXISTS(SELECT 1 FROM migrated_task_events WHERE task_id=?)
      OR EXISTS(SELECT 1 FROM json_artifacts WHERE task_id=?)`).get(taskId, taskId, taskId));
      }
      #event(id, seq, type, from, to, generation, evidence, at, cursor) {
        const eventCursor = cursor ?? this.#nextEventCursor(), j = canonical3(validateEvidence(type, evidence));
        this.#db.prepare("INSERT INTO manager_operation_events(event_cursor,operation_id,sequence,event_type,from_phase,to_phase,generation,evidence_json,evidence_digest,at) VALUES(?,?,?,?,?,?,?,?,?,?)").run(eventCursor, id, seq, type, from, to, generation, j, digest(j), at);
        this.#faultPoint("after_event_insert");
        return eventCursor;
      }
      #assertOpen() {
        if (this.#closed) fail2("store_closed");
      }
      #assertWritable() {
        this.#assertOpen();
        if (this.#recoveryOnly) fail2("recovery_read_only");
        if (this.poisoned) fail2("root_poisoned");
        this.#validate();
      }
      #faultPoint(name) {
        if (this.#fault === name || this.#fault === "rollback_unknown" && name === "after_projection") fail2("injected_failure", `injected ${name}`);
      }
      #transaction(fn) {
        this.#assertWritable();
        let began = false, commitStarted = false, settled = false;
        const token = randomUUID();
        const identity = writerIntentIdentity();
        if (identity === null) fail2("writer_intent_identity_unavailable");
        try {
          const fd = openSync(this.#paths.intent, "wx", 384);
          try {
            writeFileSync(fd, JSON.stringify({ version: 2, token, started_at: (/* @__PURE__ */ new Date()).toISOString(), process_id: process.pid, platform: process.platform, identity_version: 1, start_fingerprint: identity }));
            fsyncSync(fd);
          } finally {
            closeSync(fd);
          }
        } catch (e) {
          if (e?.code === "EEXIST") fail2("root_writer_busy");
          throw e;
        }
        try {
          this.#db.exec("BEGIN IMMEDIATE");
          began = true;
          assertCandidateSchema(this.#db);
          const v = fn();
          this.#validate(false);
          commitStarted = true;
          this.#db.exec("COMMIT");
          settled = true;
          if (this.#fault === "commit_ack_lost") throw new Error("injected lost commit acknowledgment");
          return v;
        } catch (e) {
          if (commitStarted && isBusy(e)) {
            try {
              this.#db.exec("ROLLBACK");
              settled = true;
              fail2("root_writer_busy");
            } catch (re) {
              if (re instanceof AdmissionError && re.code === "root_writer_busy") throw re;
              this.#poison("commit_busy_rollback_unknown", String(re));
              fail2("transaction_outcome_unknown", String(re));
            }
          }
          if (commitStarted) {
            this.#poison("commit_outcome_unknown", String(e));
            fail2("transaction_outcome_unknown", String(e));
          }
          if (began) {
            try {
              if (this.#fault === "rollback_unknown") throw new Error("injected rollback outcome unknown");
              this.#db.exec("ROLLBACK");
              settled = true;
            } catch (re) {
              this.#poison("rollback_outcome_unknown", String(re));
              fail2("transaction_outcome_unknown", String(re));
            }
          } else {
            settled = true;
            if (isBusy(e)) fail2("root_writer_busy");
          }
          throw e;
        } finally {
          if (settled && !this.#poisoned && !existsSync(this.#paths.poison)) {
            try {
              const intent = JSON.parse(readFileSync(this.#paths.intent, "utf8"));
              if (intent.token !== token) fail2("writer_intent_identity_mismatch");
              unlinkSync(this.#paths.intent);
            } catch (e) {
              this.#poison("writer_intent_release_unknown", String(e));
              fail2("transaction_outcome_unknown", String(e));
            }
          }
        }
      }
      #poison(reason, detail) {
        this.#poisoned = true;
        try {
          writePoison(this.#paths.poison, { version: 1, reason, detail, at: (/* @__PURE__ */ new Date()).toISOString() });
        } catch (error) {
          process.stderr.write(`SQLITE_POISON_RECORD_FAILED ${JSON.stringify({ reason, error: error.code ?? "io_error" })}
`);
        }
      }
      #validate(integrity = true) {
        if (!integrity) {
          if (this.#db.prepare("PRAGMA foreign_keys").get().foreign_keys !== 1) fail2("foreign_keys_disabled");
          if (this.#db.prepare("PRAGMA user_version").get().user_version !== SCHEMA_VERSION) fail2("schema_version_unknown");
          return;
        }
        this.#readConsistent(() => void 0);
      }
      #validateContents() {
        try {
          if (this.#db.prepare("PRAGMA foreign_keys").get().foreign_keys !== 1) fail2("foreign_keys_disabled");
          if (this.#db.prepare("PRAGMA user_version").get().user_version !== SCHEMA_VERSION) fail2("schema_version_unknown");
          assertCandidateSchema(this.#db, {
            allowRuntimeEventExtensionAbsent: this.#recoveryOnly,
            allowOwnerBindingExtensionAbsent: this.#recoveryOnly,
            allowLegacyRecoveryBindingTrigger: this.#recoveryOnly
          });
          if (this.#db.prepare("PRAGMA quick_check").get().quick_check !== "ok") fail2("database_corrupt");
          if (this.#db.prepare("PRAGMA foreign_key_check").all().length) fail2("database_inconsistent");
          const m = this.#db.prepare("SELECT * FROM authority_metadata").all();
          if (m.length !== 1 || m[0].schema_version !== SCHEMA_VERSION) fail2("policy_or_schema_mismatch");
          const hasOwnerBindings = Boolean(this.#db.prepare(
            "SELECT 1 FROM sqlite_schema WHERE type='table' AND name='task_owner_bindings'"
          ).get());
          if (hasOwnerBindings) {
            const bindings = this.#db.prepare("SELECT * FROM task_owner_bindings ORDER BY task_id").all();
            const taskCount = this.#db.prepare("SELECT COUNT(*) AS n FROM tasks").get().n;
            if (bindings.length !== taskCount) fail2("task_owner_binding_missing");
            const validSources = /* @__PURE__ */ new Set(["mcp_meta", "mcp_meta_missing", "mcp_meta_invalid", "non_host_admission", "legacy_unavailable"]);
            for (const binding of bindings) {
              if (!this.#db.prepare("SELECT 1 FROM tasks WHERE task_id=?").get(binding.task_id) || !validText2(binding.bound_at, 64) || Number.isNaN(Date.parse(binding.bound_at)) || !validSources.has(binding.binding_source)) fail2("task_owner_binding_invalid");
              if (binding.binding_state === "bound") {
                if (binding.owner_thread_id === null || !validId(binding.owner_thread_id) || binding.binding_source !== "mcp_meta") fail2("task_owner_binding_invalid");
              } else if (binding.binding_state === "unavailable") {
                if (binding.owner_thread_id !== null || binding.binding_source === "mcp_meta")
                  fail2("task_owner_binding_invalid");
              } else fail2("task_owner_binding_invalid");
            }
          }
          const freshReceipts = this.#db.prepare("SELECT * FROM fresh_install_receipt").all();
          const authoritySwitches = this.#db.prepare("SELECT * FROM authority_switch").all();
          const migrationRuns = this.#db.prepare("SELECT * FROM migration_runs").all();
          const migratedResultsCount = this.#db.prepare("SELECT COUNT(*) AS n FROM migrated_task_results").get().n;
          const migratedEventsCount = this.#db.prepare("SELECT COUNT(*) AS n FROM migrated_task_events").get().n;
          if (freshReceipts.length > 1 || authoritySwitches.length > 1 || migrationRuns.length > 1 || freshReceipts.length && authoritySwitches.length) fail2("authority_receipt_missing_or_ambiguous");
          if (freshReceipts.length) {
            if (migrationRuns.length || migratedResultsCount || migratedEventsCount || this.#db.prepare("SELECT COUNT(*) AS n FROM json_artifacts").get().n) fail2("fresh_install_contains_legacy_data");
          } else if (authoritySwitches.length) {
            const receipt = authoritySwitches[0], migration = migrationRuns[0];
            if (!migration || migration.state !== "verified" || migration.migration_id !== receipt.migration_id || migration.source_root_digest !== receipt.source_root_digest || migration.source_manifest_digest !== receipt.source_manifest_digest || digest(migration.source_manifest_json) !== migration.source_manifest_digest || !validText2(migration.archive_directory, 32767) || !path.isAbsolute(migration.archive_directory) || !validText2(receipt.archive_directory, 32767) || !path.isAbsolute(receipt.archive_directory) || migration.archive_directory !== receipt.archive_directory || typeof migration.archive_manifest_digest !== "string" || !/^[0-9a-f]{64}$/u.test(migration.archive_manifest_digest) || migration.archive_manifest_digest !== receipt.archive_manifest_digest || !validText2(migration.archive_source_tasks_root, 32767) || !path.isAbsolute(migration.archive_source_tasks_root) || migration.archive_source_tasks_root !== receipt.archive_source_tasks_root || !Number.isSafeInteger(migration.archive_file_count) || migration.archive_file_count < 0 || migration.archive_file_count !== migration.source_artifact_count || migration.archive_file_count !== receipt.archive_file_count || !Number.isSafeInteger(migration.archive_byte_count) || migration.archive_byte_count < 0 || migration.archive_byte_count !== migration.source_artifact_bytes || migration.archive_byte_count !== receipt.archive_byte_count || receipt.schema_version !== SCHEMA_VERSION || !validText2(receipt.protocol_version, 128) || typeof receipt.runtime_roster_digest !== "string" || !/^[0-9a-f]{64}$/u.test(receipt.runtime_roster_digest) || !validText2(receipt.verifier_version, 128) || !validText2(migration.verifier_version, 128) || receipt.verifier_version !== migration.verifier_version || !validText2(receipt.cutover_id, 128) || !validText2(receipt.created_at, 64) || Number.isNaN(Date.parse(receipt.created_at)) || !validText2(migration.created_at, 64) || !validText2(migration.verified_at, 64) || Number.isNaN(Date.parse(migration.created_at)) || Number.isNaN(Date.parse(migration.verified_at))) fail2("authority_switch_invalid");
            const policy = parseAuthoritySourceManifest(migration.source_manifest_json, migration.source_manifest_digest);
            if (policy.manifest.task_count !== migration.source_task_count || policy.manifest.artifact_count !== migration.source_artifact_count || policy.manifest.artifact_bytes !== migration.source_artifact_bytes || policy.manifest.result_count !== migration.source_result_count || policy.manifest.event_count !== migration.source_event_count) fail2("authority_switch_invalid");
          } else if (migrationRuns.length || migratedResultsCount || migratedEventsCount || this.#db.prepare("SELECT COUNT(*) AS n FROM json_artifacts").get().n) {
            fail2("migration_receipt_missing");
          }
          const artifacts = this.#db.prepare("SELECT * FROM json_artifacts ORDER BY artifact_id").all();
          const artifactById = /* @__PURE__ */ new Map(), artifactPathById = /* @__PURE__ */ new Map();
          let artifactBytes = 0;
          for (const artifact of artifacts) {
            const content = Buffer.from(artifact.content);
            if (!validText2(artifact.relative_path, 1024) || artifact.relative_path.includes("\\") || artifact.relative_path.startsWith("/") || artifact.relative_path.split("/").some((part) => !part || part === "." || part === "..") || !validText2(artifact.kind, 64) || !Number.isSafeInteger(artifact.byte_length) || artifact.byte_length < 0 || content.length !== artifact.byte_length || rawDigest(content) !== artifact.sha256 || artifactPathById.has(artifact.relative_path)) fail2("migrated_artifact_invalid");
            if (artifact.task_id !== null && !this.#db.prepare("SELECT 1 FROM tasks WHERE task_id=?").get(artifact.task_id))
              fail2("migrated_artifact_task_mismatch");
            if (artifact.attempt !== null && (artifact.task_id === null || !this.#db.prepare("SELECT 1 FROM attempts WHERE task_id=? AND attempt=?").get(artifact.task_id, artifact.attempt)))
              fail2("migrated_artifact_attempt_mismatch");
            artifactById.set(artifact.artifact_id, artifact);
            artifactPathById.set(artifact.relative_path, artifact);
            artifactBytes += artifact.byte_length;
          }
          if (authoritySwitches.length) {
            const migration = migrationRuns[0];
            const policy = parseAuthoritySourceManifest(migration.source_manifest_json, migration.source_manifest_digest);
            if (policy.kind === "raw_json_archive_cutover") {
              if (artifacts.length !== 0 || migratedResultsCount !== 0 || migratedEventsCount !== 0 || migration.source_task_count !== 0 || migration.source_result_count !== 0 || migration.source_event_count !== 0 || migration.source_artifact_count !== migration.archive_file_count || migration.source_artifact_bytes !== migration.archive_byte_count)
                fail2("raw_cutover_contains_legacy_projection", JSON.stringify({
                  artifact_count: artifacts.length,
                  migrated_result_count: migratedResultsCount,
                  migrated_event_count: migratedEventsCount,
                  source_task_count: migration.source_task_count,
                  source_result_count: migration.source_result_count,
                  source_event_count: migration.source_event_count,
                  source_artifact_count: migration.source_artifact_count,
                  archive_file_count: migration.archive_file_count,
                  source_artifact_bytes: migration.source_artifact_bytes,
                  archive_byte_count: migration.archive_byte_count
                }));
            } else {
              const migratedOnlineTaskIds = new Set(artifacts.map((artifact) => artifact.task_id).filter((taskId) => taskId !== null));
              if (!Number.isSafeInteger(migration.source_task_count) || migration.source_task_count < 0 || !Number.isSafeInteger(migration.source_artifact_count) || migration.source_artifact_count < 0 || !Number.isSafeInteger(migration.source_artifact_bytes) || migration.source_artifact_bytes < 0 || !Number.isSafeInteger(migration.source_result_count) || migration.source_result_count < 0 || !Number.isSafeInteger(migration.source_event_count) || migration.source_event_count < 0 || migration.source_task_count !== migratedOnlineTaskIds.size + policy.exceptionTaskIds.length || migration.source_artifact_count !== artifacts.length || migration.source_artifact_bytes !== artifactBytes || migration.source_result_count !== migratedResultsCount || migration.source_event_count !== migratedEventsCount || migration.archive_file_count !== artifacts.length || migration.archive_byte_count !== artifactBytes)
                fail2("migration_counts_mismatch");
            }
            for (const taskId of policy.exceptionTaskIds) {
              if (this.#db.prepare("SELECT 1 FROM tasks WHERE task_id=?").get(taskId) || this.#db.prepare("SELECT 1 FROM migrated_task_results WHERE task_id=?").get(taskId) || this.#db.prepare("SELECT 1 FROM migrated_task_events WHERE task_id=?").get(taskId) || artifacts.some((artifact) => artifact.relative_path.startsWith(`${taskId}/`) && (artifact.task_id !== null || artifact.attempt !== null))) fail2("historical_exception_promoted_to_online_authority");
            }
            for (const exception of policy.exceptions) {
              const artifact = artifactById.get(exception.artifact_id);
              if (!artifact || artifact.relative_path !== exception.relative_path || artifact.sha256 !== exception.sha256 || artifact.byte_length !== exception.byte_length || artifact.task_id !== null || artifact.attempt !== null || this.#db.prepare("SELECT 1 FROM migrated_task_results WHERE artifact_id=?").get(exception.artifact_id))
                fail2("invalid_historical_exception_artifact");
            }
          }
          const migratedResults = this.#db.prepare("SELECT * FROM migrated_task_results ORDER BY task_id,attempt").all();
          for (const resultRow of migratedResults) {
            const task = this.#db.prepare("SELECT current_attempt FROM tasks WHERE task_id=?").get(resultRow.task_id);
            const artifact = artifactById.get(resultRow.artifact_id);
            const expectedPath = resultRow.attempt === task?.current_attempt ? `${resultRow.task_id}/result.json` : `${resultRow.task_id}/attempts/${resultRow.attempt}/result.json`;
            const currentResultArtifact = artifact?.attempt === null && artifact?.kind === "task_result" && expectedPath === `${resultRow.task_id}/result.json`;
            let result;
            try {
              result = JSON.parse(resultRow.result_json);
              canonicalTaskResult2(result, { task_id: resultRow.task_id, attempt: resultRow.attempt, result_status: result.status });
            } catch {
              fail2("migrated_result_invalid");
            }
            if (!task || !artifact || artifact.task_id !== resultRow.task_id || artifact.attempt !== resultRow.attempt && !currentResultArtifact || artifact.relative_path !== expectedPath || canonical3(result) !== resultRow.result_json || digest(resultRow.result_json) !== resultRow.result_digest) fail2("migrated_result_artifact_mismatch");
          }
          const migratedEvents = this.#db.prepare("SELECT * FROM migrated_task_events ORDER BY event_cursor").all();
          const seenSourceEvents = /* @__PURE__ */ new Set();
          const seenEventCursors = /* @__PURE__ */ new Set();
          for (const event of migratedEvents) {
            const artifact = artifactById.get(event.artifact_id);
            const sourceKey = `${event.task_id}\0${event.source_sequence}`;
            const expectedDetails = event.details_json === null ? null : digest(event.details_json);
            if (!Number.isSafeInteger(event.event_cursor) || event.event_cursor < 1 || seenEventCursors.has(event.event_cursor) || !Number.isSafeInteger(event.source_sequence) || event.source_sequence < 1 || seenSourceEvents.has(sourceKey) || !validText2(event.event_type, 128) || !validText2(event.at, 64) || Number.isNaN(Date.parse(event.at)) || !validText2(event.summary, 4096) || !artifact || artifact.task_id !== event.task_id || artifact.attempt !== null || artifact.relative_path !== `${event.task_id}/events.jsonl` || expectedDetails !== event.details_digest)
              fail2("migrated_event_invalid");
            seenEventCursors.add(event.event_cursor);
            seenSourceEvents.add(sourceKey);
          }
          const maxAssigned = this.#db.prepare("SELECT MAX(generation) AS n FROM attempts WHERE generation IS NOT NULL").get().n ?? 0;
          if (m[0].next_generation < maxAssigned) fail2("generation_authority_regressed");
          const eventCursorState = this.#db.prepare("SELECT COUNT(*) AS n,MIN(event_cursor) AS min_cursor,MAX(event_cursor) AS max_cursor FROM manager_operation_events").get();
          if (eventCursorState.max_cursor !== null && (!Number.isSafeInteger(eventCursorState.max_cursor) || eventCursorState.max_cursor < 1) || eventCursorState.n > 0 && (!Number.isSafeInteger(eventCursorState.min_cursor) || eventCursorState.min_cursor < 1)) fail2("event_cursor_invalid");
          const invalidCursor = this.#db.prepare("SELECT event_cursor FROM manager_operation_events WHERE event_cursor<=0 LIMIT 1").get();
          if (invalidCursor) fail2("event_cursor_invalid");
          const eventSchema = this.#db.prepare("SELECT sql FROM sqlite_schema WHERE type='table' AND name='manager_operation_events'").get()?.sql;
          if (typeof eventSchema !== "string" || !/event_cursor\s+INTEGER\s+PRIMARY\s+KEY\s+AUTOINCREMENT/iu.test(eventSchema)) fail2("event_cursor_schema_mismatch");
          const sequenceRows = this.#db.prepare("SELECT name,seq FROM sqlite_sequence").all();
          const unlinkedCancelCursorState = this.#db.prepare("SELECT COUNT(*) AS n,MIN(queued_cancel_event_cursor) AS min_cursor,MAX(queued_cancel_event_cursor) AS max_cursor FROM attempts WHERE queued_cancel_id IS NOT NULL AND queued_cancel_operation_id IS NULL").get();
          const hasRuntimeEvents = Boolean(this.#db.prepare("SELECT 1 FROM sqlite_schema WHERE type='table' AND name='runtime_task_events'").get());
          const logicalCursorState = this.#db.prepare(`SELECT COUNT(*) AS n,MIN(cursor) AS min_cursor,MAX(cursor) AS max_cursor FROM (
        SELECT event_cursor AS cursor FROM manager_operation_events
        UNION ALL SELECT queued_cancel_event_cursor AS cursor FROM attempts WHERE queued_cancel_id IS NOT NULL AND queued_cancel_operation_id IS NULL
        UNION ALL SELECT event_cursor AS cursor FROM migrated_task_events
        ${hasRuntimeEvents ? "UNION ALL SELECT event_cursor AS cursor FROM runtime_task_events" : ""})`).get();
          if (unlinkedCancelCursorState.n && (!Number.isSafeInteger(unlinkedCancelCursorState.min_cursor) || unlinkedCancelCursorState.min_cursor < 1 || !Number.isSafeInteger(unlinkedCancelCursorState.max_cursor) || unlinkedCancelCursorState.max_cursor < 1) || logicalCursorState.n !== m[0].next_event_cursor || m[0].next_event_cursor === 0 && (logicalCursorState.min_cursor !== null || logicalCursorState.max_cursor !== null) || m[0].next_event_cursor > 0 && (logicalCursorState.min_cursor !== 1 || logicalCursorState.max_cursor !== m[0].next_event_cursor)) fail2("event_cursor_invalid");
          if (sequenceRows.some((row) => row.name !== "manager_operation_events") || logicalCursorState.n === 0 && sequenceRows.length !== 0 || logicalCursorState.n > 0 && (sequenceRows.length !== 1 || sequenceRows[0].seq !== logicalCursorState.max_cursor || !Number.isSafeInteger(sequenceRows[0].seq) || sequenceRows[0].seq < 1)) fail2("event_cursor_invalid");
          if (this.#db.prepare(`SELECT a.task_id FROM attempts a JOIN manager_operation_events e ON e.event_cursor=a.queued_cancel_event_cursor
        WHERE a.queued_cancel_id IS NOT NULL AND (a.queued_cancel_operation_id IS NULL OR e.operation_id<>a.queued_cancel_operation_id
          OR NOT (e.event_type='cancelled_before_launch' OR e.event_type='observation_recorded'
            AND json_extract(e.evidence_json,'$.reason')='cancelled_before_claim')) LIMIT 1`).get()) fail2("queued_cancel_event_mismatch");
          const queuedCancels = this.#db.prepare("SELECT * FROM attempts WHERE queued_cancel_id IS NOT NULL ORDER BY task_id,attempt").all();
          for (const a of queuedCancels) {
            const task = this.#db.prepare("SELECT current_attempt,status FROM tasks WHERE task_id=?").get(a.task_id);
            let result;
            try {
              result = JSON.parse(a.queued_cancel_result_json);
            } catch {
              fail2("queued_cancel_result_invalid");
            }
            const requestDigest = digest({ contract: "wp6a-queued-cancel-v1", task_id: a.task_id, attempt: a.attempt });
            canonicalTaskResult2(result, { task_id: a.task_id, attempt: a.attempt, result_status: "cancelled" });
            if (a.status !== "cancelled" || task?.status !== "cancelled" || task.current_attempt !== a.attempt || !validId(a.queued_cancel_id) || a.queued_cancel_request_digest !== requestDigest || !Number.isSafeInteger(a.queued_cancel_event_cursor) || a.queued_cancel_event_cursor < 1 || !validText2(a.queued_cancelled_at, 64) || Number.isNaN(Date.parse(a.queued_cancelled_at)) || canonical3(result) !== a.queued_cancel_result_json || a.queued_cancel_result_digest !== digest(a.queued_cancel_result_json) || result.task_id !== a.task_id || result.attempt !== a.attempt || result.status !== "cancelled" || result.finished_at !== a.queued_cancelled_at || result.started_at !== null || result.needs_master_decision !== false) fail2("queued_cancel_projection_mismatch");
            if (a.queued_cancel_operation_id === null) {
              if (this.#db.prepare("SELECT operation_id FROM manager_operations WHERE operation_kind='attempt_lifecycle' AND task_id=? AND attempt=?").get(a.task_id, a.attempt)) fail2("queued_cancel_operation_missing");
            } else {
              const e = this.#db.prepare("SELECT * FROM manager_operation_events WHERE event_cursor=? AND operation_id=?").get(a.queued_cancel_event_cursor, a.queued_cancel_operation_id);
              let evidence;
              try {
                evidence = e ? JSON.parse(e.evidence_json) : null;
              } catch {
                fail2("queued_cancel_event_mismatch");
              }
              const preclaim = e?.event_type === "observation_recorded" && evidence?.reason === "cancelled_before_claim";
              const o = this.#db.prepare("SELECT * FROM manager_operations WHERE operation_id=? AND operation_kind='attempt_lifecycle'").get(a.queued_cancel_operation_id);
              const operationEvents = this.#db.prepare("SELECT * FROM manager_operation_events WHERE operation_id=? ORDER BY sequence").all(a.queued_cancel_operation_id);
              const administrativeRelease = o?.phase === "released" && operationEvents.some((row) => {
                if (row.event_type !== "observation_recorded") return false;
                try {
                  return JSON.parse(row.evidence_json).reason === "user_authorized_release_unverified";
                } catch {
                  return false;
                }
              });
              if (!o || o.task_id !== a.task_id || o.attempt !== a.attempt || o.generation !== a.generation || (preclaim ? o.phase !== "launch_intent" && o.phase !== "released" || e.from_phase !== "launch_intent" || e.to_phase !== "launch_intent" || evidence.launch_id !== o.launch_id || evidence.token_digest !== o.launch_token_digest : !(o.phase === "cancelled_before_launch" && o.launch_id === null && e?.event_type === "cancelled_before_launch" || o.phase === "released" && administrativeRelease && e?.event_type === "observation_recorded" && evidence?.reason === "cancelled_before_claim")) || o.claim_id !== null || o.result_digest !== null || !e || evidence.cancel_id !== a.queued_cancel_id || evidence.request_digest !== requestDigest) fail2("queued_cancel_operation_mismatch");
            }
          }
          if (this.#db.prepare("SELECT t.task_id FROM tasks t LEFT JOIN attempts a ON a.task_id=t.task_id AND a.attempt=t.current_attempt WHERE a.task_id IS NULL").all().length) fail2("task_attempt_projection_mismatch");
          const malformedContinuations = this.#db.prepare("SELECT task_id,attempt FROM attempts WHERE NOT ((continuation_operation_id IS NULL AND continuation_json IS NULL AND continuation_digest IS NULL) OR (attempt>1 AND continuation_operation_id IS NOT NULL AND continuation_json IS NOT NULL AND continuation_digest IS NOT NULL))").all();
          if (malformedContinuations.length) fail2("continue_history_mismatch");
          const continuationRows = this.#db.prepare("SELECT * FROM attempts WHERE continuation_operation_id IS NOT NULL ORDER BY task_id,attempt").all();
          for (const a of continuationRows) {
            let c;
            try {
              c = JSON.parse(a.continuation_json);
            } catch {
              fail2("continue_history_mismatch");
            }
            const continuationKeys = [
              "additional_requirements",
              "contract",
              "feedback",
              "operation_id",
              "previous_attempt",
              "previous_claim_id",
              "previous_generation",
              "previous_operation_id",
              "previous_revision",
              "previous_worker_identity_digest",
              "task_id"
            ];
            if (!c || Object.getPrototypeOf(c) !== Object.prototype || Object.keys(c).sort().join("|") !== continuationKeys.join("|") || c.contract !== "wp6b2b-continue-v1" || canonical3(c) !== a.continuation_json || a.continuation_digest !== digest(a.continuation_json) || c.operation_id !== a.continuation_operation_id || c.task_id !== a.task_id || c.previous_attempt !== a.attempt - 1 || !validId(c.operation_id) || c.operation_id !== c.operation_id.trim() || !validId(c.previous_operation_id) || typeof c.feedback !== "string" || !c.feedback.trim() || c.feedback.includes("\0") || !Array.isArray(c.additional_requirements) || c.additional_requirements.some((value) => typeof value !== "string") || !Number.isSafeInteger(c.previous_generation) || c.previous_generation < 1 || !Number.isSafeInteger(c.previous_revision) || c.previous_revision < 1 || !validId(c.previous_claim_id) || typeof c.previous_worker_identity_digest !== "string" || !/^[0-9a-f]{64}$/u.test(c.previous_worker_identity_digest)) fail2("continue_history_mismatch");
            const prior = this.#db.prepare("SELECT * FROM manager_operations WHERE operation_id=? AND operation_kind='attempt_lifecycle'").get(c.previous_operation_id);
            const op = this.#db.prepare("SELECT * FROM manager_operations WHERE operation_kind='attempt_lifecycle' AND task_id=? AND attempt=?").get(a.task_id, a.attempt);
            const priorAttempt = this.#db.prepare("SELECT status,generation FROM attempts WHERE task_id=? AND attempt=?").get(a.task_id, c.previous_attempt);
            if (!prior || prior.task_id !== a.task_id || prior.attempt !== c.previous_attempt || prior.generation !== c.previous_generation || prior.revision < c.previous_revision || prior.claim_id !== c.previous_claim_id || prior.claim_worker_identity_digest !== c.previous_worker_identity_digest || prior.phase !== "released" || !["completed", "failed", "waiting_for_master"].includes(prior.result_status) || !this.#db.prepare("SELECT 1 FROM manager_operation_events WHERE operation_id=? AND event_type='released' AND sequence<=?").get(prior.operation_id, c.previous_revision) || priorAttempt?.status !== prior.result_status) fail2("continue_history_mismatch");
            const current = this.#db.prepare("SELECT current_attempt,status FROM tasks WHERE task_id=?").get(a.task_id);
            const cancelledCurrent = current?.status === "cancelled" && a.status === "cancelled" && a.queued_cancel_id !== null;
            if (op ? op.generation !== a.generation || a.generation === null : a.generation !== null || current?.current_attempt !== a.attempt || !(current.status === "queued" && a.status === "queued") && !cancelledCurrent) fail2("continue_history_mismatch");
          }
          if (m[0].policy_generation === 0) {
            if (m[0].policy_version !== null || m[0].capacity_limit !== null || m[0].policy_operation_id !== null) fail2("policy_or_schema_mismatch");
          } else {
            const ps = this.#db.prepare("SELECT * FROM manager_operations WHERE operation_kind='capacity_policy_change' ORDER BY policy_generation").all();
            if (m[0].policy_version !== 1 || ps.length !== m[0].policy_generation) fail2("policy_or_schema_mismatch");
            for (let i = 0; i < ps.length; i++) {
              const p = ps[i], ev = this.#db.prepare("SELECT * FROM manager_operation_events WHERE operation_id=? ORDER BY sequence").all(p.operation_id);
              if (p.policy_generation !== i + 1 || !p.capacity_limit || p.capacity_limit > 8 || p.request_digest !== digest({ operation_id: p.operation_id, capacity_limit: p.capacity_limit, expected_generation: i }) || ev.length !== 1 || ev[0].event_type !== "capacity_policy_committed" || ev[0].generation !== null || ev[0].evidence_digest !== digest(ev[0].evidence_json)) fail2("policy_or_schema_mismatch");
              const e = JSON.parse(ev[0].evidence_json);
              if (e.generation !== i + 1 || e.capacity_limit !== p.capacity_limit) fail2("policy_or_schema_mismatch");
            }
            const current = ps.at(-1);
            if (!current || current.operation_id !== m[0].policy_operation_id || current.capacity_limit !== m[0].capacity_limit) fail2("policy_or_schema_mismatch");
          }
          const slots = this.#db.prepare("SELECT capacity_slot,COUNT(*) n FROM manager_operations WHERE operation_kind='attempt_lifecycle' AND phase NOT IN ('released','cancelled_before_launch') GROUP BY capacity_slot HAVING COUNT(*)>1").all();
          const active = this.#db.prepare("SELECT COUNT(*) n,MAX(capacity_slot) max_slot FROM manager_operations WHERE operation_kind='attempt_lifecycle' AND phase NOT IN ('released','cancelled_before_launch')").get();
          if (slots.length || active.n > m[0].capacity_limit || active.max_slot > m[0].capacity_limit) fail2("active_capacity_invariant");
          const adminAbandonments = this.#adminAbandonments();
          const os2 = this.#db.prepare("SELECT * FROM manager_operations").all();
          for (const o of os2) {
            if (o.operation_kind === "attempt_lifecycle" && o.phase === "running") {
              const running = this.#db.prepare("SELECT t.status AS task_status,t.current_attempt,a.status AS attempt_status FROM tasks t JOIN attempts a ON a.task_id=t.task_id AND a.attempt=t.current_attempt WHERE t.task_id=? AND a.attempt=? AND a.generation=?").get(o.task_id, o.attempt, o.generation);
              if (!running || running.task_status !== "running" || running.attempt_status !== "running") fail2("claim_task_projection_mismatch");
            }
            const es = this.#db.prepare("SELECT * FROM manager_operation_events WHERE operation_id=? ORDER BY sequence").all(o.operation_id);
            if (es.length !== o.revision || es.at(-1)?.to_phase !== o.phase) fail2("projection_event_mismatch");
            if (o.operation_kind === "attempt_lifecycle" && o.phase === "cancelled_before_launch") {
              const a = this.#db.prepare("SELECT status,queued_cancel_id,queued_cancel_operation_id FROM attempts WHERE task_id=? AND attempt=? AND generation=?").get(o.task_id, o.attempt, o.generation);
              const task = this.#db.prepare("SELECT current_attempt,status FROM tasks WHERE task_id=?").get(o.task_id);
              const evidence = es.at(-1)?.event_type === "cancelled_before_launch" ? JSON.parse(es.at(-1).evidence_json) : null;
              if (!a || a.status !== "cancelled" || !a.queued_cancel_id || a.queued_cancel_operation_id !== o.operation_id || task?.current_attempt !== o.attempt || task.status !== "cancelled" || o.launch_id !== null || o.claim_id !== null || o.result_digest !== null || es.length !== 2 || es.at(-1)?.from_phase !== "reserved" || evidence?.cancel_id !== a.queued_cancel_id) fail2("queued_cancel_operation_mismatch");
            }
            const launchEvents = { launch_intent: [], launch_receipt: [], claim_committed: [] };
            const cleanupEvents = { cleanup_pending: [], cleanup_verified: [], cleanup_unverified: [], cleanup_reverified: [], released: [] };
            const resultEvents = [];
            const recoveryEvents = [], cancellationIntents = [], cancellationVerifications = [], executorWakeEvents = [], lateWakeEvents = [];
            for (let i = 0; i < es.length; i++) {
              const e = es[i];
              if (e.sequence !== i + 1 || e.evidence_digest !== digest(e.evidence_json) || (i === 0 ? e.from_phase !== null : e.from_phase !== es[i - 1].to_phase)) fail2("projection_event_mismatch");
              let parsed;
              try {
                parsed = JSON.parse(e.evidence_json);
              } catch {
                fail2("invalid_evidence");
              }
              validateEvidence(e.event_type, parsed);
              if (e.event_type in launchEvents) launchEvents[e.event_type].push({ event: e, evidence: parsed });
              if (e.event_type in cleanupEvents) cleanupEvents[e.event_type].push({ event: e, evidence: parsed });
              if (e.event_type === "result_committed") resultEvents.push({ event: e, evidence: parsed });
              if (e.event_type === "observation_recorded" && (parsed.reason === "recovery_hold" || parsed.reason === "recovery_quarantine")) recoveryEvents.push({ event: e, evidence: parsed });
              if (e.event_type === "observation_recorded" && parsed.reason === "cancel_requested") cancellationIntents.push({ event: e, evidence: parsed });
              if (e.event_type === "observation_recorded" && parsed.reason === "cancel_tree_verified") cancellationVerifications.push({ event: e, evidence: parsed });
              if (e.event_type === "observation_recorded" && parsed.reason === "executor_wake") executorWakeEvents.push({ event: e, evidence: parsed });
              if (e.event_type === "observation_recorded" && parsed.reason === LATE_WAKE_REASON) lateWakeEvents.push({ event: e, evidence: parsed });
              if (i > 0 && e.from_phase !== es[i - 1].to_phase) fail2("projection_event_mismatch");
              if (e.event_type === "launch_receipt" && (e.from_phase !== "launch_intent" || e.to_phase !== "launch_intent")) fail2("invalid_event_phase");
              if (e.event_type === "claim_committed" && (e.from_phase !== "launch_intent" || e.to_phase !== "running")) fail2("invalid_event_phase");
              if (e.event_type === "result_committed" && (e.from_phase !== "running" || e.to_phase !== "result_committed")) fail2("invalid_event_phase");
              if (e.event_type === "cleanup_pending" && (e.from_phase !== "result_committed" || e.to_phase !== "cleanup_pending")) fail2("invalid_event_phase");
              if (e.event_type === "cleanup_verified" && (!(e.from_phase === "cleanup_pending" || e.from_phase === "cleanup_reverified") || e.to_phase !== "cleanup_verified")) fail2("invalid_event_phase");
              if (e.event_type === "cleanup_unverified" && (e.from_phase !== "cleanup_pending" || e.to_phase !== "cleanup_unverified")) fail2("invalid_event_phase");
              if (e.event_type === "cleanup_reverified" && (e.from_phase !== "cleanup_unverified" || e.to_phase !== "cleanup_reverified")) fail2("invalid_event_phase");
              if (e.event_type === "released" && (e.from_phase !== "cleanup_verified" || e.to_phase !== "released")) fail2("invalid_event_phase");
              if (e.event_type === "launch_intent" && (e.from_phase !== "reserved" || e.to_phase !== "launch_intent")) fail2("invalid_event_phase");
              if (e.event_type === "observation_recorded" && e.from_phase !== e.to_phase && !(parsed.reason === "admin_abandoned" && e.from_phase === "running" && e.to_phase === "released") && !(parsed.reason === "user_authorized_release_unverified" && (e.from_phase === "launch_intent" && o.claim_id === null && o.result_digest === null || e.from_phase === "cleanup_unverified" && o.result_digest !== null && ["completed", "failed", "waiting_for_master", "cancelled"].includes(o.result_status)) && e.to_phase === "released")) fail2("invalid_event_phase");
              if (parsed.reason === "executor_wake" && (e.from_phase !== "released" || e.to_phase !== "released"))
                fail2("invalid_executor_wake_phase");
              if (e.event_type !== "launch_receipt" && e.event_type !== "claim_committed" && e.event_type !== "launch_intent" && e.event_type !== "observation_recorded" && !e.event_type.startsWith("interaction_") && EVENT_PHASE[e.event_type] !== e.to_phase) fail2("invalid_event_phase");
              if (e.event_type.startsWith("interaction_") && (e.from_phase !== "running" || e.to_phase !== "running")) fail2("invalid_event_phase");
              if (o.operation_kind === "attempt_lifecycle" && e.generation !== o.generation) fail2("invalid_event_phase");
              if (o.operation_kind === "capacity_policy_change" && (e.generation !== null || e.event_type !== "capacity_policy_committed" || e.to_phase !== "policy_change_committed")) fail2("invalid_event_phase");
            }
            if (executorWakeEvents.length) {
              if (o.phase !== "released" || o.result_digest === null || o.result_commit_ref === null)
                fail2("executor_wake_operation_not_released");
              const releaseEvent = es.find((event) => event.event_type === "released");
              if (!releaseEvent || executorWakeEvents[0].event.sequence <= releaseEvent.sequence || executorWakeEvents.length > EXECUTOR_WAKE_LIMIT)
                fail2("executor_wake_history_invalid");
              const releaseSequence = releaseEvent.sequence;
              if (es.some((event) => event.sequence > releaseSequence && (event.event_type !== "observation_recorded" || !["executor_wake", LATE_WAKE_REASON].includes(JSON.parse(event.evidence_json).reason))))
                fail2("executor_wake_terminal_history_invalid");
              const deliveryId = executorWakeEvents[0].evidence.delivery_id;
              const binding = executorWakeEvents[0].evidence;
              let stage = "start";
              for (const { event, evidence } of executorWakeEvents) {
                if (evidence.delivery_id !== deliveryId || evidence.operation_id !== o.operation_id || evidence.task_id !== o.task_id || evidence.attempt !== o.attempt || evidence.generation !== o.generation || evidence.result_digest !== o.result_digest || evidence.result_commit_ref !== o.result_commit_ref || evidence.thread_id !== binding.thread_id || evidence.policy_digest !== binding.policy_digest || evidence.authorization_digest !== binding.authorization_digest || event.generation !== o.generation || event.sequence <= releaseSequence)
                  fail2("executor_wake_history_binding_mismatch");
                if (stage === "start") {
                  if (evidence.state === "intent") stage = "intent";
                  else if (evidence.state === "web_notify") stage = "web_notify";
                  else fail2("executor_wake_history_transition_invalid");
                } else if (stage === "intent") {
                  if (evidence.state === "queued" || evidence.state === "submission_unknown") stage = "ack";
                  else if (evidence.state === "web_notify") stage = "web_notify";
                  else fail2("executor_wake_history_transition_invalid");
                } else if (stage === "ack") {
                  if (evidence.state === "turn_started") stage = "turn_started";
                  else if (evidence.state === "web_notify") stage = "web_notify";
                  else fail2("executor_wake_history_transition_invalid");
                } else fail2("executor_wake_history_transition_invalid");
              }
            }
            if (lateWakeEvents.length) {
              if (o.phase !== "released" || o.result_digest === null || o.result_commit_ref === null)
                fail2("late_wake_operation_not_released");
              const releaseEvent = es.find((event) => event.event_type === "released");
              if (!releaseEvent || lateWakeEvents[0].event.sequence <= releaseEvent.sequence || lateWakeEvents.length > LATE_WAKE_LIMIT)
                fail2("late_wake_history_invalid");
              if (!executorWakeEvents.length || !executorWakeEvents.some((item) => item.evidence.state === "web_notify") || executorWakeEvents.some((item) => ["queued", "submission_unknown", "turn_started"].includes(item.evidence.state)))
                fail2("late_wake_not_eligible");
              if (lateWakeEvents[0].event.sequence <= executorWakeEvents[executorWakeEvents.length - 1].event.sequence)
                fail2("late_wake_history_invalid");
              if (es.some((event) => event.sequence > lateWakeEvents[0].event.sequence && event.event_type === "observation_recorded" && JSON.parse(event.evidence_json).reason === "executor_wake"))
                fail2("late_wake_history_invalid");
              const owner = this.#db.prepare("SELECT binding_state,owner_thread_id FROM task_owner_bindings WHERE task_id=?").get(o.task_id);
              if (!owner || owner.binding_state !== "bound" || owner.owner_thread_id !== lateWakeEvents[0].evidence.thread_id)
                fail2("late_wake_owner_binding_required");
              const deliveryId = lateWakeEvents[0].evidence.delivery_id;
              const binding = lateWakeEvents[0].evidence;
              let stage = "start";
              for (const { event, evidence } of lateWakeEvents) {
                if (evidence.delivery_id !== deliveryId || evidence.operation_id !== o.operation_id || evidence.task_id !== o.task_id || evidence.attempt !== o.attempt || evidence.generation !== o.generation || evidence.result_digest !== o.result_digest || evidence.result_commit_ref !== o.result_commit_ref || evidence.thread_id !== binding.thread_id || evidence.policy_digest !== binding.policy_digest || evidence.authorization_digest !== binding.authorization_digest || event.generation !== o.generation || event.sequence <= releaseEvent.sequence)
                  fail2("late_wake_history_binding_mismatch");
                if (stage === "start") {
                  if (evidence.state === "intent") stage = "intent";
                  else fail2("late_wake_history_transition_invalid");
                } else if (stage === "intent") {
                  if (evidence.state === "queued" || evidence.state === "submission_unknown") stage = "ack";
                  else if (evidence.state === "web_notify") stage = "web_notify";
                  else fail2("late_wake_history_transition_invalid");
                } else if (stage === "ack") {
                  if (evidence.state === "turn_started") stage = "turn_started";
                  else if (evidence.state === "web_notify") stage = "web_notify";
                  else fail2("late_wake_history_transition_invalid");
                } else fail2("late_wake_history_transition_invalid");
              }
            }
            if (o.operation_kind === "attempt_lifecycle") {
              const intents = launchEvents.launch_intent, receipts = launchEvents.launch_receipt, claims = launchEvents.claim_committed;
              if (cancellationIntents.length > 1 || cancellationVerifications.length > 0 && cancellationIntents.length !== 1)
                fail2("cancellation_history_mismatch");
              if (cancellationIntents.length || cancellationVerifications.length) {
                if (claims.length !== 1 || !o.claim_id || o.claim_generation !== o.generation || !o.claim_worker_identity_json || !o.launch_identity_json) fail2("cancellation_claim_missing");
                const worker = JSON.parse(o.claim_worker_identity_json), launchIdentity = JSON.parse(o.launch_identity_json);
                if (cancellationIntents.length) {
                  const { event, evidence } = cancellationIntents[0];
                  const intent = {
                    contract: "wp6c-cancel-intent-v1",
                    cancel_id: evidence.cancel_id,
                    operation_id: o.operation_id,
                    task_id: o.task_id,
                    attempt: o.attempt,
                    generation: o.generation,
                    claim_id: o.claim_id,
                    worker_identity_digest: o.claim_worker_identity_digest,
                    identity_state: evidence.identity_state,
                    identity_evidence_digest: evidence.identity_evidence_digest
                  };
                  if (event.sequence <= claims[0].event.sequence || event.from_phase !== "running" || event.to_phase !== "running" || evidence.claim_id !== o.claim_id || evidence.worker_identity_digest !== o.claim_worker_identity_digest || evidence.evidence_digest !== digest(intent)) fail2("cancellation_intent_history_mismatch");
                  const identityJson = canonical3(worker);
                  if (digest(identityJson) !== o.claim_worker_identity_digest || worker.process_id !== launchIdentity.process_id || worker.start_fingerprint !== launchIdentity.start_fingerprint) fail2("cancellation_identity_history_mismatch");
                }
                if (cancellationVerifications.length) {
                  const intent = cancellationIntents[0];
                  for (const { event, evidence } of cancellationVerifications) {
                    const unsigned = {
                      reason: "cancel_tree_verified",
                      cancel_id: intent.evidence.cancel_id,
                      claim_id: o.claim_id,
                      worker_identity_digest: o.claim_worker_identity_digest,
                      intent_event_digest: intent.event.evidence_digest,
                      process_tree_digest: evidence.process_tree_digest,
                      proof_digest: evidence.proof_digest,
                      root_process_id: evidence.root_process_id,
                      root_start_fingerprint: evidence.root_start_fingerprint,
                      worker_tree_complete: true
                    };
                    if (event.sequence <= intent.event.sequence || event.from_phase !== "running" || event.to_phase !== "running" || evidence.cancel_id !== intent.evidence.cancel_id || evidence.claim_id !== o.claim_id || evidence.worker_identity_digest !== o.claim_worker_identity_digest || evidence.intent_event_digest !== intent.event.evidence_digest || evidence.evidence_digest !== digest({ cancel_verification_contract_version: 1, ...unsigned }) || evidence.root_process_id !== worker.process_id || evidence.root_process_id !== launchIdentity.process_id || evidence.root_start_fingerprint !== worker.start_fingerprint || evidence.root_start_fingerprint !== launchIdentity.start_fingerprint)
                      fail2("cancellation_verification_history_mismatch");
                  }
                  const linkedProofs = /* @__PURE__ */ new Map();
                  for (const event of es) {
                    if (event.event_type !== "observation_recorded") continue;
                    const evidence = JSON.parse(event.evidence_json);
                    if (evidence.reason !== "cancel_recovery_resolved") continue;
                    const verificationDigest = evidence.cancellation_verification_digest;
                    linkedProofs.set(verificationDigest, (linkedProofs.get(verificationDigest) ?? 0) + 1);
                  }
                  for (let index = 0; index < cancellationVerifications.length; index++) {
                    const count = linkedProofs.get(cancellationVerifications[index].event.evidence_digest) ?? 0;
                    if (count > 1 || index > 0 && count !== 1) fail2("cancellation_verification_history_mismatch");
                  }
                }
              }
              const seenRecoveryEnvelopes = /* @__PURE__ */ new Set(), seenRecoveryRevisions = /* @__PURE__ */ new Set();
              let recoveryLevel = o.phase === "quarantined" ? 2 : 0;
              for (const { event, evidence } of recoveryEvents) {
                validateRecoveryEventBinding(o, event, evidence, claims[0]?.event.sequence);
                if (seenRecoveryEnvelopes.has(evidence.envelope_digest) || seenRecoveryRevisions.has(evidence.expected_revision)) fail2("recovery_event_duplicate");
                seenRecoveryEnvelopes.add(evidence.envelope_digest);
                seenRecoveryRevisions.add(evidence.expected_revision);
                const level = evidence.classification === "quarantine" ? 2 : 1;
                if (level < recoveryLevel) fail2("recovery_classification_downgrade");
                recoveryLevel = level;
              }
              recoveryEventsFor(es, o);
              if (intents.length > 1 || receipts.length > 1 || claims.length > 1) fail2("launch_claim_history_mismatch");
              if (intents.length === 0 !== (o.launch_id === null)) fail2("launch_claim_history_mismatch");
              if (intents.length) {
                const i = intents[0], v = i.evidence;
                if (i.event.sequence < 2 || v.launch_id !== o.launch_id || v.launch_epoch !== o.launch_epoch || v.token_digest !== o.launch_token_digest || o.launch_intent_digest !== digest({ operation_id: o.operation_id, task_id: o.task_id, attempt: o.attempt, generation: o.generation, launch_id: o.launch_id, launch_epoch: o.launch_epoch, token_digest: o.launch_token_digest })) fail2("launch_claim_history_mismatch");
              }
              if (receipts.length === 0 !== (o.launch_receipt_digest === null) || receipts.length !== (o.launch_identity_json === null ? 0 : 1) || receipts.length !== (o.launch_receipt_id === null ? 0 : 1)) fail2("launch_claim_history_mismatch");
              if (receipts.length) {
                const r = receipts[0], v = r.evidence, identity = JSON.parse(o.launch_identity_json);
                if (r.event.sequence <= intents[0].event.sequence || v.launch_id !== o.launch_id || v.launch_epoch !== o.launch_epoch || v.token_digest !== o.launch_token_digest || v.receipt_digest !== o.launch_receipt_digest || o.launch_receipt_digest !== digest({ receipt_id: o.launch_receipt_id, operation_id: o.operation_id, task_id: o.task_id, attempt: o.attempt, generation: o.generation, launch_id: o.launch_id, launch_epoch: o.launch_epoch, token_digest: o.launch_token_digest, launch_identity: identity })) fail2("launch_claim_history_mismatch");
                fixtureLaunchIdentity(identity);
              }
              if (claims.length === 0 !== (o.claim_id === null) || claims.length !== (o.claim_worker_identity_json === null ? 0 : 1)) fail2("launch_claim_history_mismatch");
              if (claims.length) {
                const c = claims[0], v = c.evidence, worker = JSON.parse(o.claim_worker_identity_json);
                if (!receipts.length || c.event.sequence <= receipts[0].event.sequence || v.claim_id !== o.claim_id || v.launch_id !== o.launch_id || v.launch_epoch !== o.launch_epoch || v.token_digest !== o.launch_token_digest || v.worker_identity_digest !== o.claim_worker_identity_digest || o.claim_launch_id !== o.launch_id || o.claim_generation !== o.generation || o.claim_token_digest !== o.launch_token_digest || o.claim_worker_identity_digest !== digest(o.claim_worker_identity_json) || o.claim_request_digest !== digest({ claim_id: o.claim_id, operation_id: o.operation_id, task_id: o.task_id, attempt: o.attempt, generation: o.generation, launch_id: o.launch_id, launch_epoch: o.launch_epoch, token_digest: o.launch_token_digest, worker_identity: worker })) fail2("launch_claim_history_mismatch");
                fixtureWorkerIdentity(worker);
                const task = this.#db.prepare("SELECT status FROM attempts WHERE task_id=? AND attempt=? AND generation=?").get(o.task_id, o.attempt, o.generation);
                const allowed = o.phase === "running" ? task?.status === "running" : ["running", "completed", "failed", "cancelled", "waiting_for_master"].includes(task?.status);
                if (!allowed) fail2("launch_claim_task_mismatch");
              }
              if (o.launch_id === null && (o.launch_receipt_id !== null || o.launch_receipt_digest !== null || o.launch_identity_json !== null || o.claim_id !== null)) fail2("launch_claim_history_mismatch");
              if (resultEvents.length === 0 !== (o.result_digest === null) || resultEvents.length !== (o.result_json === null ? 0 : 1) || resultEvents.length !== (o.result_commit_ref === null ? 0 : 1) || resultEvents.length !== (o.result_status === null ? 0 : 1)) fail2("result_event_projection_mismatch");
              const resultConflictEvents = es.filter((e) => e.event_type === "quarantined" && JSON.parse(e.evidence_json).reason === "result_conflict");
              if (resultConflictEvents.length > 1) fail2("result_conflict_quarantine_unbounded");
              if (resultEvents.length) {
                const r = resultEvents[0], v = r.evidence, result = JSON.parse(o.result_json);
                if (claims.length !== 1 || r.event.sequence <= claims[0].event.sequence || v.claim_id !== o.claim_id || v.outcome !== o.result_status || v.worker_identity_digest !== o.claim_worker_identity_digest || v.result_digest !== o.result_digest || v.result_commit_ref !== o.result_commit_ref || o.result_generation !== o.generation || result.task_id !== o.task_id || result.attempt !== o.attempt || result.status !== o.result_status || !RESULT_STATUSES2.has(o.result_status) || o.result_digest !== digest({ result_contract_version: RESULT_CONTRACT_VERSION, result_status: o.result_status, result }) || o.result_commit_ref !== `result-${o.result_digest}`) fail2("result_event_projection_mismatch");
                const projection = this.#db.prepare("SELECT t.status AS task_status,t.current_attempt,a.status AS attempt_status FROM tasks t JOIN attempts a ON a.task_id=t.task_id WHERE t.task_id=? AND a.attempt=? AND a.generation=?").get(o.task_id, o.attempt, o.generation);
                if (projection?.current_attempt < o.attempt || projection?.attempt_status !== o.result_status || projection.current_attempt === o.attempt && projection.task_status !== o.result_status) fail2("result_task_attempt_projection_mismatch");
              }
              if (resultConflictEvents.length) {
                const q = resultConflictEvents[0], e = JSON.parse(q.evidence_json);
                if (!resultEvents.length || q.to_phase !== "quarantined" || e.claim_id !== o.claim_id || !validText2(e.reason, 256) || !/^[0-9a-f]{64}$/u.test(e.result_digest) || !/^[0-9a-f]{64}$/u.test(e.evidence_digest) || !validText2(e.result_commit_ref, 128)) fail2("result_conflict_quarantine_mismatch");
              }
              const pending = cleanupEvents.cleanup_pending, verified = cleanupEvents.cleanup_verified, unverified = cleanupEvents.cleanup_unverified, reverified = cleanupEvents.cleanup_reverified, released = cleanupEvents.released;
              if (pending.length > 1 || verified.length > 1 || unverified.length > 1 || reverified.length > 1 || released.length > 1 || verified.length && unverified.length && !reverified.length || reverified.length && (verified.length !== reverified.length || unverified.length !== reverified.length)) fail2("cleanup_history_unbounded");
              if (pending.length === 0 && (verified.length !== 0 || unverified.length !== 0 || reverified.length !== 0 || released.length !== 0) || pending.length === 1 && resultEvents.length !== 1) fail2("cleanup_history_mismatch");
              if (pending.length) {
                const p = pending[0], pe = p.evidence, resultEvent = resultEvents[0];
                if (!resultEvent || p.event.sequence <= resultEvent.event.sequence || pe.claim_id !== o.claim_id || pe.result_commit_ref !== o.result_commit_ref || pe.worker_identity_digest !== o.claim_worker_identity_digest) fail2("cleanup_pending_mismatch");
                if (unverified.length) {
                  const u = unverified[0], ue = u.evidence;
                  if (u.event.sequence !== p.event.sequence + 1 || ue.claim_id !== o.claim_id || ue.worker_identity_digest !== o.claim_worker_identity_digest || !["alive", "unknown", "identity_mismatch", "incomplete"].includes(ue.probe_state) || !validText2(ue.reason, 128)) fail2("cleanup_unverified_mismatch");
                }
                if (reverified.length) {
                  const rv = reverified[0], rve = rv.evidence;
                  if (unverified.length !== 1 || rv.event.sequence <= unverified[0].event.sequence || rve.prior_cleanup_event_digest !== unverified[0].event.evidence_digest || rve.claim_id !== o.claim_id || rve.operation_id !== o.operation_id || rve.task_id !== o.task_id || rve.attempt !== o.attempt || rve.generation !== o.generation || rve.worker_identity_digest !== o.claim_worker_identity_digest) fail2("cleanup_reverification_history_mismatch");
                  const between = es.filter((event) => event.sequence > unverified[0].event.sequence && event.sequence < rv.event.sequence);
                  const betweenRecovery = recoveryEventsFor(es, o).filter((item) => item.event.sequence > unverified[0].event.sequence && item.event.sequence < rv.event.sequence);
                  if (between.some((event) => event.event_type !== "observation_recorded") || betweenRecovery.length !== between.length)
                    fail2("cleanup_reverification_intervening_event_mismatch");
                  if (betweenRecovery.some((item) => item.evidence.classification !== "hold" || !["cleanup_identity_unknown", "cleanup_incomplete"].includes(item.evidence.reason_code))) fail2("cleanup_reverification_unrelated_hold");
                  resolvedRecoverySetMatches(
                    rve,
                    betweenRecovery.map((item) => item.event.evidence_digest),
                    "cleanup_reverification_hold_set_mismatch"
                  );
                } else if (unverified.length && verified.length) fail2("cleanup_reverification_event_missing");
                if (verified.length) {
                  const v = verified[0], ve = v.evidence;
                  const expectedVerifiedSequence = reverified.length ? reverified[0].event.sequence + 1 : p.event.sequence + 1;
                  if (v.event.sequence !== expectedVerifiedSequence || ve.claim_id !== o.claim_id || ve.launch_receipt_digest !== o.launch_receipt_digest || ve.result_commit_ref !== o.result_commit_ref || ve.worker_identity_digest !== o.claim_worker_identity_digest || ve.workspace_touched !== false || ve.worker_tree_complete !== true || ve.operation_resources_complete !== true || !["synthetic_fixture", "manager_os_cleanup_verification"].includes(ve.evidence_source) || !/^[0-9a-f]{64}$/u.test(ve.process_tree_digest) || !/^[0-9a-f]{64}$/u.test(ve.resources_digest)) fail2("cleanup_verified_mismatch");
                  const worker = JSON.parse(o.claim_worker_identity_json), launchIdentity = JSON.parse(o.launch_identity_json);
                  if (ve.root_process_id !== worker.process_id || ve.root_start_fingerprint !== worker.start_fingerprint || ve.root_process_id !== launchIdentity.process_id || ve.root_start_fingerprint !== launchIdentity.start_fingerprint) fail2("cleanup_worker_identity_mismatch");
                  const normalized = {
                    operation_id: o.operation_id,
                    task_id: o.task_id,
                    attempt: o.attempt,
                    generation: o.generation,
                    claim_id: o.claim_id,
                    worker_identity_digest: o.claim_worker_identity_digest,
                    launch_receipt_digest: o.launch_receipt_digest,
                    result_commit_ref: o.result_commit_ref,
                    process_tree_digest: ve.process_tree_digest,
                    resources_digest: ve.resources_digest,
                    root_process_id: ve.root_process_id,
                    root_start_fingerprint: ve.root_start_fingerprint,
                    worker_tree_complete: ve.worker_tree_complete,
                    operation_resources_complete: ve.operation_resources_complete,
                    workspace_touched: ve.workspace_touched,
                    source: ve.evidence_source,
                    fixture: ve.evidence_source === "synthetic_fixture",
                    ...ve.adapter_cleanup !== void 0 ? { adapter_cleanup: ve.adapter_cleanup } : {}
                  };
                  if (ve.cleanup_digest !== digest({ cleanup_contract_version: 1, evidence: normalized })) fail2("cleanup_digest_mismatch");
                  if (reverified.length) {
                    const rve = reverified[0].evidence;
                    const paired = [
                      "adapter_cleanup",
                      "claim_id",
                      "cleanup_digest",
                      "evidence_source",
                      "launch_receipt_digest",
                      "operation_resources_complete",
                      "process_tree_digest",
                      "resources_digest",
                      "result_commit_ref",
                      "root_process_id",
                      "root_start_fingerprint",
                      "worker_identity_digest",
                      "worker_tree_complete",
                      "workspace_touched"
                    ];
                    if (paired.some((key) => rve[key] !== ve[key])) fail2("cleanup_reverification_evidence_mismatch");
                  }
                }
                if (released.length) {
                  const r = released[0], re = r.evidence, ve = verified[0]?.evidence;
                  if (!ve || r.event.sequence !== verified[0].event.sequence + 1 || re.claim_id !== o.claim_id || re.cleanup_digest !== ve.cleanup_digest || re.result_commit_ref !== o.result_commit_ref || re.worker_identity_digest !== o.claim_worker_identity_digest) fail2("release_history_mismatch");
                }
                const expected = o.phase === "quarantined" ? "quarantined" : released.length ? "released" : verified.length ? "cleanup_verified" : unverified.length ? "cleanup_unverified" : "cleanup_pending";
                let administrativeRelease = false;
                const terminal = [...es].reverse().find((event) => {
                  if (event.event_type !== "observation_recorded") return false;
                  try {
                    return JSON.parse(event.evidence_json).reason === "user_authorized_release_unverified";
                  } catch {
                    return false;
                  }
                });
                if (terminal?.event_type === "observation_recorded" && terminal.from_phase === "cleanup_unverified" && terminal.to_phase === "released") {
                  let terminalEvidence;
                  try {
                    terminalEvidence = JSON.parse(terminal.evidence_json);
                  } catch {
                    fail2("cleanup_projection_mismatch");
                  }
                  const parsedEvents = es.map((event) => {
                    try {
                      return { event, evidence: JSON.parse(event.evidence_json) };
                    } catch {
                      fail2("cleanup_projection_mismatch");
                    }
                  });
                  const recoveryEvent = parsedEvents.find((item) => item.event.event_type === "observation_recorded" && (item.evidence.evidence_digest === terminalEvidence.recovery_evidence_digest || item.event.evidence_digest === terminalEvidence.recovery_evidence_digest));
                  if (terminalEvidence.result_digest !== void 0) {
                    const resultEvent2 = parsedEvents.find((item) => item.event.event_type === "result_committed" && item.evidence.result_digest === terminalEvidence.result_digest && item.evidence.result_commit_ref === terminalEvidence.result_commit_ref);
                    administrativeRelease = released.length === 0 && unverified.length === 1 && terminalEvidence.reason === "user_authorized_release_unverified" && ["completed", "failed", "waiting_for_master", "cancelled"].includes(o.result_status) && resultEvent2 !== void 0 && recoveryEvent !== void 0 && resultEvent2.evidence.outcome === o.result_status && resultEvent2.evidence.claim_id === terminalEvidence.claim_id && resultEvent2.evidence.worker_identity_digest === terminalEvidence.worker_identity_digest && recoveryEvent.event.sequence === terminal.sequence - 1 && recoveryEvent.evidence.reason === "recovery_hold" && recoveryEvent.evidence.task_id === o.task_id && recoveryEvent.evidence.attempt === o.attempt && recoveryEvent.evidence.expected_revision === terminal.sequence - 2 && recoveryEvent.evidence.claim_id === o.claim_id && recoveryEvent.evidence.worker_identity_digest === o.claim_worker_identity_digest && recoveryEvent.evidence.reason_code === "cleanup_incomplete" && recoveryEvent.evidence.recovery_disposition === "complete_cleanup_closure_unavailable" && recoveryEvent.evidence.process_tree_scan_clean === true && recoveryEvent.evidence.process_tree_root_observed === true;
                  } else {
                    const verification = parsedEvents.find((item) => item.event.event_type === "observation_recorded" && item.event.evidence_digest === terminalEvidence.cancellation_verification_digest);
                    const resultEvent2 = parsedEvents.find((item) => item.event.event_type === "result_committed" && item.event.evidence_digest && item.evidence.cancel_verification_digest === terminalEvidence.cancellation_verification_digest);
                    administrativeRelease = released.length === 0 && unverified.length === 1 && terminalEvidence.reason === "user_authorized_release_unverified" && o.result_status === "cancelled" && verification !== void 0 && resultEvent2 !== void 0 && recoveryEvent !== void 0 && verification.evidence.reason === "cancel_tree_verified" && terminalEvidence.cancel_id === verification.evidence.cancel_id && verification.evidence.claim_id === o.claim_id && verification.evidence.worker_identity_digest === o.claim_worker_identity_digest && verification.event.sequence < resultEvent2.event.sequence && resultEvent2.evidence.outcome === "cancelled" && recoveryEvent.event.sequence === terminal.sequence - 1 && recoveryEvent.evidence.reason === "recovery_hold" && recoveryEvent.evidence.task_id === o.task_id && recoveryEvent.evidence.attempt === o.attempt && recoveryEvent.evidence.expected_revision === terminal.sequence - 2 && recoveryEvent.evidence.claim_id === o.claim_id && recoveryEvent.evidence.worker_identity_digest === o.claim_worker_identity_digest && recoveryEvent.evidence.reason_code === "cleanup_incomplete" && recoveryEvent.evidence.recovery_disposition === "complete_cleanup_closure_unavailable" && recoveryEvent.evidence.process_tree_scan_clean === true && recoveryEvent.evidence.process_tree_root_observed === true;
                  }
                }
                if (o.phase !== expected && !(o.phase === "released" && administrativeRelease)) fail2("cleanup_projection_mismatch");
              } else if (["cleanup_pending", "cleanup_verified", "cleanup_unverified", "cleanup_reverified", "released"].includes(o.phase) && !adminAbandonments.has(o.operation_id)) {
                const administrativeRelease = es.some((event) => {
                  if (event.event_type !== "observation_recorded") return false;
                  try {
                    return JSON.parse(event.evidence_json).reason === "user_authorized_release_unverified";
                  } catch {
                    return false;
                  }
                });
                if (!administrativeRelease) fail2("cleanup_projection_mismatch");
              }
              const adminAbandonment = adminAbandonments.get(o.operation_id);
              if (adminAbandonment) {
                let adminWorker;
                try {
                  adminWorker = JSON.parse(o.claim_worker_identity_json);
                } catch {
                  fail2("admin_abandonment_projection_mismatch");
                }
                if (!adminWorker || typeof adminWorker !== "object") fail2("admin_abandonment_projection_mismatch");
                const expectedRouteDigest = digest({
                  operation_id: o.operation_id,
                  task_id: o.task_id,
                  attempt: o.attempt,
                  generation: o.generation,
                  original_revision: adminAbandonment.original_revision,
                  claim_id: o.claim_id,
                  worker_identity_digest: adminAbandonment.worker_identity_digest,
                  worker_process_id: adminWorker.process_id,
                  worker_start_fingerprint: adminWorker.start_fingerprint,
                  audit_digest: adminAbandonment.audit_digest
                });
                if (adminAbandonment.operation_kind !== "attempt_lifecycle" || adminAbandonment.task_id !== o.task_id || adminAbandonment.attempt !== o.attempt || adminAbandonment.generation !== o.generation || adminAbandonment.claim_id !== o.claim_id || adminAbandonment.worker_identity_digest !== o.claim_worker_identity_digest || adminAbandonment.original_revision + 1 !== o.revision || adminAbandonment.event_sequence !== o.revision || adminAbandonment.outcome !== "admin_abandoned" || adminAbandonment.result_absent !== 1 || adminAbandonment.cleanup_verified !== 0 || adminAbandonment.release_reason !== "cleanup_incomplete" || adminAbandonment.audit_digest !== digest(adminAbandonment.audit_json) || adminAbandonment.request_digest !== expectedRouteDigest || o.phase !== "released" || o.result_digest !== null || o.result_json !== null || o.result_commit_ref !== null || !Number.isFinite(Date.parse(adminAbandonment.abandoned_at))) fail2("admin_abandonment_projection_mismatch");
                const terminalEvent = es.find((event) => event.sequence === adminAbandonment.event_sequence);
                let terminalEvidence;
                try {
                  terminalEvidence = JSON.parse(terminalEvent.evidence_json);
                } catch {
                  fail2("admin_abandonment_projection_mismatch");
                }
                if (!terminalEvent || terminalEvent.sequence !== adminAbandonment.event_sequence || terminalEvent.event_type !== "observation_recorded" || terminalEvent.from_phase !== "running" || terminalEvent.to_phase !== "released" || terminalEvidence.reason !== "admin_abandoned" || terminalEvidence.evidence_digest !== adminAbandonment.audit_digest)
                  fail2("admin_abandonment_event_mismatch");
                let audit;
                try {
                  audit = JSON.parse(adminAbandonment.audit_json);
                } catch {
                  fail2("admin_abandonment_audit_invalid");
                }
                if (Object.keys(audit).sort().join("|") !== "boot_time|claimant_scan_clean|claimant_scan_digest|cleanup_verified|failed_at|hosts_closed|observed_at|platform_probe_digest|process_inventory_digest|result_absent|worker_exited|writer_closed" || audit.claimant_scan_clean !== true || audit.cleanup_verified !== false || audit.hosts_closed !== true || audit.result_absent !== true || audit.worker_exited !== true || audit.writer_closed !== true || !validIsoInstant(audit.boot_time) || typeof audit.claimant_scan_digest !== "string" || !/^[0-9a-f]{64}$/u.test(audit.claimant_scan_digest) || typeof audit.platform_probe_digest !== "string" || !/^[0-9a-f]{64}$/u.test(audit.platform_probe_digest) || typeof audit.process_inventory_digest !== "string" || !/^[0-9a-f]{64}$/u.test(audit.process_inventory_digest) || !validIsoInstant(audit.failed_at) || !validIsoInstant(audit.observed_at) || Date.parse(audit.boot_time) <= Date.parse(audit.failed_at) || Date.parse(audit.observed_at) < Date.parse(audit.boot_time) || adminAbandonment.abandoned_at !== audit.observed_at) fail2("admin_abandonment_audit_invalid");
                const projection = this.#db.prepare(`SELECT t.current_attempt,t.status AS task_status,a.status AS attempt_status
              FROM tasks t JOIN attempts a ON a.task_id=t.task_id AND a.attempt=t.current_attempt
              WHERE t.task_id=? AND a.attempt=? AND a.generation=?`).get(o.task_id, o.attempt, o.generation);
                if (!projection || projection.current_attempt !== o.attempt || projection.task_status !== "failed" || projection.attempt_status !== "failed") fail2("admin_abandonment_projection_mismatch");
              }
              validateInteractionHistory(this.#db, o, es);
            }
          }
        } catch (e) {
          if (e instanceof AdmissionError) throw e;
          fail2("database_unreadable", String(e));
        }
      }
    };
  }
});

// src/cli/wait-task.ts
import { realpathSync as realpathSync4 } from "node:fs";
import { homedir as homedir2 } from "node:os";
import path6 from "node:path";
import { fileURLToPath as fileURLToPath4 } from "node:url";

// src/attention/read-only.ts
import { lstatSync as lstatSync2, realpathSync as realpathSync2 } from "node:fs";
import path2 from "node:path";

// src/runtime/node-runtime.ts
var SUPPORTED_NODE_RANGE = ">=24.16.0 <25";
function isSupportedNodeVersion(version) {
  const match = /^(\d+)\.(\d+)\.(\d+)$/u.exec(version);
  if (!match) return false;
  const major = Number(match[1]);
  const minor = Number(match[2]);
  const patch = Number(match[3]);
  return major === 24 && minor >= 16 && patch >= 0;
}
function assertSupportedNodeRuntime(version = process.versions.node) {
  if (!isSupportedNodeVersion(version)) {
    throw new Error(`Unsupported Node.js runtime ${version}; SQLite Authority requires Node ${SUPPORTED_NODE_RANGE}.`);
  }
}

// src/task-errors.ts
var TaskManagerError = class extends Error {
  code;
  constructor(code, message) {
    super(message);
    this.name = "TaskManagerError";
    this.code = code;
  }
};

// src/attention/snapshot.ts
var TASK_STATUSES = /* @__PURE__ */ new Set([
  "queued",
  "running",
  "completed",
  "failed",
  "cancelled",
  "waiting_for_master"
]);
function parseTaskAttentionSnapshot(value, expectedTaskId) {
  if (!isRecord(value)) throw new TaskManagerError("TASK_STATE", "SQLite attention projection is invalid");
  const taskId = value.task_id;
  const attempt = value.attempt;
  const status = value.status;
  const pending = value.pending_requests;
  if (typeof taskId !== "string" || !taskId || expectedTaskId !== void 0 && taskId !== expectedTaskId || !Number.isSafeInteger(attempt) || Number(attempt) < 1 || typeof status !== "string" || !TASK_STATUSES.has(status) || !Array.isArray(pending) || pending.some((requestId) => typeof requestId !== "string" || requestId.length < 1 || requestId.length > 512)) {
    throw new TaskManagerError("TASK_STATE", "SQLite attention projection is invalid");
  }
  return {
    task_id: taskId,
    attempt: Number(attempt),
    status,
    pending_requests: [...pending]
  };
}
function isAttentionTerminalStatus(status) {
  return status === "completed" || status === "failed" || status === "cancelled" || status === "waiting_for_master";
}
function isRecord(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

// src/attention/read-only.ts
async function openReadOnlyAttention(options) {
  assertSupportedNodeRuntime();
  const root = requirePlainDirectory(options.dataRoot);
  const load = options.loadModule ?? (() => Promise.resolve().then(() => (init_store(), store_exports)));
  const module = await load();
  const databaseFileName = options.databaseFileName ?? "bridge.sqlite";
  const store = module.IsolatedAdmissionStore.openForRecovery(root, {
    databaseFileName,
    managedDataDirectory: true
  });
  if (!store) throw new Error("read-only SQLite Attention Store was not opened");
  let closed = false;
  return {
    read(taskId) {
      if (closed) throw new Error("read-only SQLite Attention Store is closed");
      const value = store.readTaskAttention(taskId);
      return value === null ? null : parseTaskAttentionSnapshot(value, taskId);
    },
    close() {
      if (closed) return;
      closed = true;
      store.close();
    }
  };
}
function requirePlainDirectory(value) {
  if (typeof value !== "string" || !path2.isAbsolute(value)) throw new Error("SQLite data directory must be an absolute path");
  const stat = lstatSync2(value);
  if (!stat.isDirectory() || stat.isSymbolicLink()) throw new Error("SQLite data directory must be a plain directory");
  const resolved = realpathSync2.native(value);
  if (!samePath(value, resolved)) throw new Error("SQLite data directory must not be redirected");
  return resolved;
}
function samePath(left, right) {
  const normalize = (value) => process.platform === "win32" ? path2.win32.normalize(value).replace(/[\\/]+$/u, "").toLocaleLowerCase("en-US") : path2.resolve(value);
  return normalize(left) === normalize(right);
}

// src/attention/wait.ts
async function waitForAttentionSnapshot(options) {
  const now = options.now ?? Date.now;
  const pollMs = options.pollMs ?? 250;
  const sleep = options.sleep ?? ((milliseconds) => new Promise((resolve) => setTimeout(resolve, milliseconds)));
  if (!Number.isFinite(options.timeoutMs) || options.timeoutMs < 0) throw new Error("timeoutMs must be non-negative");
  if (!Number.isInteger(pollMs) || pollMs < 1) throw new Error("pollMs must be a positive integer");
  const started = now();
  const deadline = started + options.timeoutMs;
  let snapshot = await options.read();
  const initialAttempt = snapshot.attempt;
  for (; ; ) {
    const reason = classify(snapshot, initialAttempt, now() >= deadline);
    if (reason) {
      return { snapshot, initial_attempt: initialAttempt, reason, elapsed_ms: Math.max(0, now() - started) };
    }
    await sleep(Math.min(pollMs, Math.max(1, deadline - now())));
    snapshot = await options.read();
  }
}
function classify(snapshot, initialAttempt, deadlineReached) {
  if (isAttentionTerminalStatus(snapshot.status)) return "terminal";
  if (snapshot.pending_requests.length > 0) return "interaction";
  if (snapshot.attempt !== initialAttempt) return "attempt_changed";
  return deadlineReached ? "timeout" : null;
}

// src/runtime/host-profile.ts
import { homedir } from "node:os";
import path3 from "node:path";
function codexHostProfile(homeDirectory = homedir()) {
  return {
    name: "codex-zcode-bridge",
    settingsDirectory: path3.join(homeDirectory, ".codex", "codex-zcode-bridge")
  };
}
function validateHostProfile(host) {
  if (!host || typeof host.name !== "string" || !host.name.trim() || typeof host.settingsDirectory !== "string" || !path3.isAbsolute(host.settingsDirectory)) {
    throw new Error("invalid Bridge host profile");
  }
  if (host.legacySettingsDirectories !== void 0 && (!Array.isArray(host.legacySettingsDirectories) || host.legacySettingsDirectories.some((directory) => typeof directory !== "string" || !path3.isAbsolute(directory)))) {
    throw new Error("host migration directories must be absolute");
  }
  if (host.workerEntryPath !== void 0 && (typeof host.workerEntryPath !== "string" || !path3.isAbsolute(host.workerEntryPath))) {
    throw new Error("host worker entry must be absolute");
  }
  if (host.instructions !== void 0 && typeof host.instructions !== "string") {
    throw new Error("host instructions must be text");
  }
  if (host.defaultDataRoot !== void 0 && (typeof host.defaultDataRoot !== "string" || !path3.isAbsolute(host.defaultDataRoot))) {
    throw new Error("host default data root must be absolute");
  }
  return host;
}

// src/runtime/sqlite-install-config.ts
import { existsSync as existsSync3, lstatSync as lstatSync3, mkdirSync, readFileSync as readFileSync3, realpathSync as realpathSync3 } from "node:fs";
import os from "node:os";
import path5 from "node:path";
import { fileURLToPath as fileURLToPath3 } from "node:url";

// src/runtime/resolver.ts
import { accessSync, existsSync as existsSync2, readFileSync as readFileSync2, statSync as statSync2 } from "node:fs";
import path4 from "node:path";
import { fileURLToPath as fileURLToPath2 } from "node:url";

// src/runtime/desktop-host-launch.ts
var MAX_ASAR_HEADER_BYTES = 32 * 1024 * 1024;
var MAX_METADATA_BYTES = 64 * 1024;

// src/runtime/official-builtin-registry.ts
var OFFICIAL_ENDPOINT_ENV_KEYS = Object.freeze([
  "ZCODE_ENV",
  "ZCODE_BASE_URL",
  "ZCODE_ENDPOINT_ORIGIN",
  "ZCODE_PRODUCTION_BASE_URL",
  "ZCODE_TEST_BASE_URL"
]);
var MAX_REGISTRY_BYTES = 8 * 1024 * 1024;

// src/runtime/resolver.ts
function findPackageRoot(startDir) {
  let current = startDir ?? path4.dirname(fileURLToPath2(import.meta.url));
  for (let depth = 0; depth < 10; depth++) {
    if (existsSync2(path4.join(current, "package.json")) || existsSync2(path4.join(current, "plugin.json")) && existsSync2(path4.join(current, "dist")) && existsSync2(path4.join(current, "worker"))) {
      return current;
    }
    const parent = path4.dirname(current);
    if (parent === current) break;
    current = parent;
  }
  throw new Error(
    `Cannot locate the Bridge package root (no package.json or installed plugin markers above ${startDir ?? "module directory"})`
  );
}

// src/runtime/sqlite-install-config.ts
var CONFIG_FILE = "authority.json";
var CONFIG_LIMIT = 8 * 1024;
var FRESH_SQLITE_DATABASE_FILE = "bridge.sqlite";
var SqliteInstallConfigurationError = class extends Error {
  constructor(code, message = code) {
    super(message);
    this.code = code;
    this.name = "SqliteInstallConfigurationError";
  }
  code;
};
function loadInstallAuthoritySelection(host) {
  validateHostProfile(host);
  const configPath = path5.join(host.settingsDirectory, CONFIG_FILE);
  try {
    const stat = lstatSync3(configPath);
    if (!stat.isFile() || stat.isSymbolicLink()) throw new SqliteInstallConfigurationError("authority_config_not_regular_file");
    if (stat.size > CONFIG_LIMIT) throw new SqliteInstallConfigurationError("authority_config_too_large");
    const parsed = JSON.parse(readFileSync3(configPath, "utf8"));
    if (!isRecord2(parsed)) throw new SqliteInstallConfigurationError("authority_config_invalid_shape");
    const keys = Object.keys(parsed).sort().join("|");
    if (parsed.schema_version !== 1) throw new SqliteInstallConfigurationError("authority_config_version_unsupported");
    if (parsed.authority === "json" && keys === "authority|schema_version") {
      throw new SqliteInstallConfigurationError("authority_config_json_unsupported");
    }
    if (parsed.authority !== "sqlite" || keys !== "authority|schema_version" && keys !== "authority|data_root|schema_version") {
      throw new SqliteInstallConfigurationError("authority_config_invalid_contract");
    }
    const configuredDataRoot = parsed.data_root === void 0 ? "" : parsed.data_root;
    if (typeof configuredDataRoot !== "string" || configuredDataRoot && !isLocalAbsolutePath(configuredDataRoot)) {
      throw new SqliteInstallConfigurationError("authority_config_data_root_invalid");
    }
    return { state: "sqlite", configPath, configuredDataRoot };
  } catch (error) {
    if (error.code === "ENOENT") return { state: "sqlite", configPath, configuredDataRoot: "" };
    if (error instanceof SqliteInstallConfigurationError) throw error;
    throw new SqliteInstallConfigurationError("authority_config_unreadable_or_invalid", error instanceof Error ? error.message : "authority config failed");
  }
}
function sqliteInstallationRoot(env) {
  const modulePath = fileURLToPath3(import.meta.url);
  const dist = path5.dirname(modulePath);
  const entry = path5.basename(modulePath);
  const pluginEntry = entry === "wait-task.mjs" || entry === "bridge.mjs" && env["ZCODE_BRIDGE_PLUGIN_MODE"] === "1";
  if (pluginEntry && path5.basename(dist) === "dist") {
    const pluginRoot = path5.dirname(dist);
    if (!existsSync3(path5.join(pluginRoot, ".codex-plugin", "plugin.json")) || !existsSync3(path5.join(pluginRoot, "launch-node24.mjs"))) {
      throw new SqliteInstallConfigurationError("sqlite_plugin_layout_invalid");
    }
    return pluginRoot;
  }
  return findPackageRoot();
}
function resolveSqliteStateDirectory(selection, env) {
  return resolveStateDirectory(selection, env, sqliteInstallationRoot(env), os.tmpdir());
}
function resolveStateDirectory(selection, env, packageRootValue, tempRootValue) {
  const appRoot = selection.configuredDataRoot || defaultDataRoot(env);
  if (!isLocalAbsolutePath(appRoot)) throw new SqliteInstallConfigurationError("sqlite_data_root_not_local_absolute");
  const normalizedRoot = path5.resolve(appRoot);
  const stateDirectory = path5.join(normalizedRoot, "state");
  const packageRoot = path5.resolve(packageRootValue);
  const tempRoot = path5.resolve(tempRootValue);
  if (within(packageRoot, normalizedRoot) || within(tempRoot, normalizedRoot) || within(packageRoot, stateDirectory) || within(tempRoot, stateDirectory)) {
    throw new SqliteInstallConfigurationError("sqlite_data_root_reserved_location");
  }
  return { dataRoot: stateDirectory, databaseFileName: FRESH_SQLITE_DATABASE_FILE };
}
function defaultDataRoot(env) {
  const localAppData = env["LOCALAPPDATA"]?.trim();
  if (!localAppData || !isLocalAbsolutePath(localAppData)) throw new SqliteInstallConfigurationError("local_app_data_unavailable");
  return path5.join(localAppData, "CodexZCodeBridge");
}
function isLocalAbsolutePath(value) {
  if (process.platform === "win32") return /^[A-Za-z]:\\/u.test(value) && path5.win32.isAbsolute(value) && !value.startsWith("\\\\");
  return path5.isAbsolute(value) && !value.startsWith("/proc/") && !value.startsWith("/sys/") && !value.startsWith("/dev/");
}
function within(root, candidate) {
  const relative = path5.relative(root, candidate);
  return relative === "" || relative !== ".." && !relative.startsWith(`..${path5.sep}`) && !path5.isAbsolute(relative);
}
function isRecord2(value) {
  return typeof value === "object" && value !== null && !Array.isArray(value) && (Object.getPrototypeOf(value) === Object.prototype || Object.getPrototypeOf(value) === null);
}

// src/cli/wait-task.ts
var TASK_ID = /^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$/u;
var THIN_WAITER_SCHEMA = "zcode-bridge/wait-task-v2";
var PENDING_OUTPUT_LIMIT = 4096;
var UsageError = class extends Error {
};
function parseWaitTaskArgs(argv) {
  const options = {
    task: null,
    timeoutS: 1500,
    pollMs: 2e3,
    dataDir: null
  };
  for (let index = 0; index < argv.length; index += 1) {
    const flag = argv[index];
    const value = argv[index + 1];
    if (flag === "--help" || flag === "-h") throw new UsageError("");
    if (value === void 0) throw new UsageError(`missing value for ${flag}`);
    index += 1;
    if (flag === "--task") options.task = value;
    else if (flag === "--timeout-s") options.timeoutS = integer(flag, value, 1, 86400);
    else if (flag === "--poll-ms") options.pollMs = integer(flag, value, 250, 6e4);
    else if (flag === "--data-dir") options.dataDir = value;
    else throw new UsageError(`unknown option ${flag}`);
  }
  if (!options.task || !TASK_ID.test(options.task)) {
    throw new UsageError("--task must match ^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$");
  }
  if (options.dataDir !== null) options.dataDir = requireAbsolute(options.dataDir, "--data-dir");
  return options;
}
function resolveWaitDataRoot(dataDir, env = process.env, home = homedir2()) {
  if (dataDir) {
    return { dataRoot: requireAbsolute(dataDir, "--data-dir"), databaseFileName: FRESH_SQLITE_DATABASE_FILE };
  }
  const selection = loadInstallAuthoritySelection(codexHostProfile(home));
  if (selection.state !== "sqlite") {
    throw new Error("SQLite authority is not selected; thin waiter never falls back to legacy JSON");
  }
  return resolveSqliteStateDirectory(selection, env);
}
async function runThinWaitTask(options) {
  const dataSource = resolveWaitDataRoot(options.dataDir);
  const source = await openReadOnlyAttention(dataSource);
  try {
    const result = await waitForAttentionSnapshot({
      read: async () => {
        const value = source.read(options.task);
        if (value === null) throw new TaskManagerError("TASK_NOT_FOUND", `unknown SQLite task: ${options.task}`);
        return value;
      },
      timeoutMs: options.timeoutS * 1e3,
      pollMs: options.pollMs
    });
    const pending = boundedPending(result.snapshot.pending_requests);
    return {
      schema: THIN_WAITER_SCHEMA,
      task_id: options.task,
      reason: result.reason,
      status: result.snapshot.status,
      attempt: result.snapshot.attempt,
      initial_attempt: result.initial_attempt,
      elapsed_ms: result.elapsed_ms,
      pending_count: result.snapshot.pending_requests.length,
      pending_requests: pending.requests,
      pending_truncated: pending.truncated,
      note: "Read-only observation from the SQLite Attention Core. Read request details and make decisions through zcode_events and zcode_interaction_reply; completed is not acceptance."
    };
  } finally {
    source.close();
  }
}
async function main() {
  let options;
  try {
    options = parseWaitTaskArgs(process.argv.slice(2));
  } catch (error) {
    if (!(error instanceof UsageError)) throw error;
    if (error.message) console.error(`wait-task: ${error.message}`);
    console.error("usage: node wait-task.mjs --task <task_id> [--timeout-s S] [--poll-ms MS] [--data-dir ABS_SQLITE_STATE_DIR]");
    process.exitCode = 2;
    return;
  }
  try {
    const result = await runThinWaitTask(options);
    process.stdout.write(`${JSON.stringify(result, null, 2)}
`);
    process.exitCode = result.reason === "timeout" ? 3 : 0;
  } catch (error) {
    const code = typeof error.code === "string" ? `${error.code}: ` : "";
    console.error(`wait-task: ${code}${error instanceof Error ? error.message : String(error)}`);
    process.exitCode = 2;
  }
}
function boundedPending(values) {
  const requests = [];
  let bytes = 2;
  for (const value of values) {
    const size = Buffer.byteLength(JSON.stringify(value), "utf8") + (requests.length ? 1 : 0);
    if (requests.length > 0 && bytes + size > PENDING_OUTPUT_LIMIT) return { requests, truncated: true };
    requests.push(value);
    bytes += size;
  }
  return { requests, truncated: false };
}
function integer(flag, value, min, max) {
  if (!/^\d+$/u.test(value)) throw new UsageError(`${flag} must be an integer`);
  const parsed = Number(value);
  if (!Number.isSafeInteger(parsed) || parsed < min || parsed > max) {
    throw new UsageError(`${flag} must be within ${min}..${max}`);
  }
  return parsed;
}
function requireAbsolute(value, label) {
  if (!path6.isAbsolute(value)) throw new UsageError(`${label} must be an absolute path: ${value}`);
  return path6.normalize(value);
}
function isEntry() {
  if (process.argv[1] === void 0) return false;
  try {
    const self = realpathSync4(fileURLToPath4(import.meta.url));
    const entry = realpathSync4(path6.resolve(process.argv[1]));
    return process.platform === "win32" ? self.toLocaleLowerCase("en-US") === entry.toLocaleLowerCase("en-US") : self === entry;
  } catch {
    return false;
  }
}
if (isEntry()) await main();
export {
  THIN_WAITER_SCHEMA,
  UsageError,
  parseWaitTaskArgs,
  resolveWaitDataRoot,
  runThinWaitTask
};
