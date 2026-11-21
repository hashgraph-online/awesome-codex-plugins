#!/usr/bin/env node
import {
  appendFileSync,
  existsSync,
  mkdirSync,
  readFileSync,
  writeFileSync,
} from "node:fs";
import path from "node:path";

const PREFERENCE_DIR = ".writers-loop";
const JOURNAL_FILE = "journal.jsonl";
const PREFS_FILE = "prefs.md";
const HALF_LIFE_DAYS = 45;

const EVENT_WEIGHTS = {
  question_answered: 1.25,
  question_skipped: 0.4,
  plan_approved: 1.4,
  plan_revision_requested: 1.4,
  draft_accepted: 1.1,
  proposal_applied: 1.35,
  proposal_rejected: 1.15,
  proposal_adjusted: 0.75,
  proposal_undone: 1.1,
  manual_rewrite: 1.15,
  preference_declared: 1.6,
};

const DERIVABLE_EVENT_TYPES = new Set([
  "plan_approved",
  "plan_revision_requested",
  "proposal_applied",
  "proposal_rejected",
  "proposal_adjusted",
  "proposal_undone",
  "manual_rewrite",
  "preference_declared",
]);

function usage() {
  console.error(`Usage:
  node scripts/journal.mjs init [project-dir]
  node scripts/journal.mjs append [project-dir] '<event-json>'
  node scripts/journal.mjs derive [project-dir]

Default project-dir is the current working directory.`);
}

function resolveProjectDir(arg) {
  return path.resolve(arg ?? process.cwd());
}

function journalPaths(projectDir) {
  const dir = path.join(projectDir, PREFERENCE_DIR);
  return {
    dir,
    journal: path.join(dir, JOURNAL_FILE),
    prefs: path.join(dir, PREFS_FILE),
  };
}

function emptyPrefs() {
  return [
    "# Learned Preferences",
    "",
    "_Derived from .writers-loop/journal.jsonl._",
    "",
  ].join("\n");
}

function init(projectDir) {
  const paths = journalPaths(projectDir);
  mkdirSync(paths.dir, { recursive: true });
  if (!existsSync(paths.journal)) {
    writeFileSync(paths.journal, "", "utf8");
  }
  if (!existsSync(paths.prefs)) {
    writeFileSync(paths.prefs, emptyPrefs(), "utf8");
  }
  console.log(`Initialized ${paths.dir}`);
}

function normalizeSignal(value) {
  if (value === "positive" || value === "negative" || value === "neutral") {
    return value;
  }
  return "neutral";
}

function signalValue(signal) {
  if (signal === "positive") return 1;
  if (signal === "negative") return -1;
  return 0;
}

function normalizeText(value) {
  return typeof value === "string" ? value.trim() : "";
}

function slug(value) {
  const normalized = normalizeText(value)
    .toLowerCase()
    .replace(/[^a-z0-9\u4e00-\u9fff]+/g, "-")
    .replace(/^-+|-+$/g, "");
  return normalized || "unspecified";
}

function normalizeScope(value) {
  return normalizeText(value.scope ?? value.appliesTo ?? value.applies_to);
}

function inferScope(event) {
  const scope = normalizeScope(event);
  if (scope) return scope;
  const artifact = normalizeText(event.artifact) || "generic";
  const stage = normalizeText(event.stage) || "general";
  return `${artifact}/${stage}`;
}

function descriptorFromEvent(event) {
  const payload = event && typeof event.payload === "object" && event.payload
    ? event.payload
    : {};
  const explicit = normalizeText(
    payload.preference ?? payload.rule ?? payload.instruction,
  );
  if (explicit) return explicit;

  const targetSection = normalizeText(payload.targetSection);
  if (targetSection) return `${event.type} in ${targetSection}`;

  const scope = normalizeScope(payload);
  if (scope) return `${event.type} for ${scope}`;

  const changeSize = normalizeText(payload.changeSize);
  if (changeSize) return `${changeSize} changes`;

  const summary = normalizeText(event.summary);
  if (summary) return summary;

  return event.type;
}

function parseEvent(input) {
  const event = JSON.parse(input);
  if (!event || typeof event !== "object") {
    throw new Error("Event JSON must be an object.");
  }
  const now = new Date().toISOString();
  const type = normalizeText(event.type) || "unspecified";
  const scope = normalizeScope(event);
  return {
    id: normalizeText(event.id) || `evt-${Date.now().toString(36)}`,
    createdAt: normalizeText(event.createdAt) || now,
    artifact: normalizeText(event.artifact) || "generic",
    stage: normalizeText(event.stage) || "general",
    type,
    signal: normalizeSignal(event.signal),
    scope,
    appliesTo: scope,
    summary: normalizeText(event.summary),
    payload:
      event.payload && typeof event.payload === "object" ? event.payload : {},
  };
}

function append(projectDir, eventJson) {
  if (!eventJson) {
    throw new Error("Missing event JSON.");
  }
  init(projectDir);
  const event = parseEvent(eventJson);
  const paths = journalPaths(projectDir);
  appendFileSync(paths.journal, `${JSON.stringify(event)}\n`, "utf8");
  console.log(`Appended ${event.id}`);
}

function readEvents(projectDir) {
  const paths = journalPaths(projectDir);
  if (!existsSync(paths.journal)) return [];
  return readFileSync(paths.journal, "utf8")
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line, index) => {
      try {
        return JSON.parse(line);
      } catch (error) {
        throw new Error(`Invalid JSONL at line ${index + 1}: ${error.message}`);
      }
    });
}

function confidenceLabel(score, evidenceCount, explicit) {
  if (explicit) return "high";
  if (score >= 0.75 && evidenceCount >= 3) return "high";
  if (score >= 0.45 && evidenceCount >= 2) return "medium";
  return "low";
}

function canDerivePreference(event) {
  return DERIVABLE_EVENT_TYPES.has(event.type);
}

function derive(projectDir) {
  init(projectDir);
  const events = readEvents(projectDir);
  const referenceTime = Date.now();
  const groups = new Map();

  for (const rawEvent of events) {
    const event = parseEvent(JSON.stringify(rawEvent));
    if (!canDerivePreference(event)) continue;
    const descriptor = descriptorFromEvent(event);
    const scope = inferScope(event);
    const key = `${scope}|${slug(descriptor)}`;
    const ageMs = referenceTime - Date.parse(event.createdAt);
    const ageDays = Number.isFinite(ageMs) ? Math.max(0, ageMs / 86400000) : 0;
    const recency = 0.5 ** (ageDays / HALF_LIFE_DAYS);
    const contribution =
      signalValue(event.signal) * (EVENT_WEIGHTS[event.type] ?? 1) * recency;
    const group = groups.get(key) ?? {
      scope,
      descriptor,
      positive: 0,
      negative: 0,
      evidence: 0,
      explicit: false,
    };
    if (contribution >= 0) {
      group.positive += contribution;
    } else {
      group.negative += Math.abs(contribution);
    }
    group.evidence += 1;
    group.explicit = group.explicit || event.type === "preference_declared";
    groups.set(key, group);
  }

  const byScope = new Map();
  for (const group of groups.values()) {
    const total = group.positive + group.negative;
    if (total <= 0) continue;
    const confidence = Math.abs(group.positive - group.negative) / total;
    const label = confidenceLabel(confidence, group.evidence, group.explicit);
    if (label === "low") continue;
    const direction = group.positive >= group.negative ? "Prefer" : "Avoid";
    const scoped = byScope.get(group.scope) ?? { Prefer: [], Avoid: [] };
    scoped[direction].push({
      text: group.descriptor,
      confidence: label,
      evidence: group.evidence,
      strength: confidence,
    });
    byScope.set(group.scope, scoped);
  }

  const lines = [
    "# Learned Preferences",
    "",
    `_Derived from .writers-loop/journal.jsonl on ${new Date().toISOString()}._`,
    "",
  ];

  for (const [scope, sections] of [...byScope.entries()].sort()) {
    lines.push(`## ${scope}`, "");
    for (const direction of ["Prefer", "Avoid"]) {
      const items = sections[direction].sort(
        (left, right) =>
          right.strength - left.strength || right.evidence - left.evidence,
      );
      if (items.length === 0) continue;
      lines.push(`### ${direction}`);
      for (const item of items) {
        lines.push(
          `- ${item.text}. [confidence: ${item.confidence}, evidence: ${item.evidence}]`,
        );
      }
      lines.push("");
    }
  }

  if (byScope.size === 0) {
    lines.push("_No medium or high confidence preferences yet._", "");
  }

  const paths = journalPaths(projectDir);
  writeFileSync(paths.prefs, lines.join("\n"), "utf8");
  console.log(`Derived preferences: ${paths.prefs}`);
}

const [command, projectDirArg, eventJson] = process.argv.slice(2);

try {
  if (command === "init") {
    init(resolveProjectDir(projectDirArg));
  } else if (command === "append") {
    append(resolveProjectDir(projectDirArg), eventJson);
  } else if (command === "derive") {
    derive(resolveProjectDir(projectDirArg));
  } else {
    usage();
    process.exit(1);
  }
} catch (error) {
  console.error(error.message);
  process.exit(1);
}
