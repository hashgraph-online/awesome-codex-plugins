// 춘식이 정비소 AQ 점검 실행 파일. src/를 묶은 빌드 결과라 직접 고치지 않는다.

// src/cli.ts
import { homedir, tmpdir as tmpdir2 } from "node:os";

// src/commands/badge.ts
import { mkdir as mkdir2, rename, rm, writeFile } from "node:fs/promises";
import { join as join2 } from "node:path";

// src/core/score.ts
function settleScore(value) {
  return Math.round(value * 1e12) / 1e12;
}
function ruleScore(value, zeroAt, fullAt) {
  const position = (value - zeroAt) / (fullAt - zeroAt);
  return position <= 0 ? 0 : position >= 1 ? 1 : position;
}
function roundHalfUp(value) {
  return Math.floor(Math.round(value * 1e9) / 1e9 + 0.5);
}
function gradeOf(aq) {
  if (aq >= 90) return { grade: "S", tier: 5 };
  if (aq >= 80) return { grade: "A", tier: 4 };
  if (aq >= 65) return { grade: "B", tier: 3 };
  if (aq >= 50) return { grade: "C", tier: 2 };
  return { grade: "D", tier: 1 };
}

// src/core/copy/format.ts
var UNCOUNTED = "\u2014";
function groupDigits(value) {
  return String(value).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}
function decimalText(value, places) {
  const scale = 10 ** places;
  const scaled = roundHalfUp(value * scale);
  const whole = groupDigits(Math.floor(scaled / scale));
  const rest = places === 0 ? "" : String(scaled % scale).padStart(places, "0").replace(/0+$/, "");
  return rest === "" ? whole : `${whole}.${rest}`;
}
function oneDecimal(value) {
  return decimalText(value, 1);
}
function placesOf(value) {
  for (let places = 0; places < 6; places++) {
    const scaled = value * 10 ** places;
    if (Math.abs(scaled - Math.round(scaled)) < 1e-9) return places;
  }
  return 6;
}
function rulePlaces(spec) {
  const scale = spec.kind === "share" ? 100 : 1;
  return Math.max(1, placesOf(spec.zeroAt * scale), placesOf(spec.fullAt * scale));
}
function formatValue(kind, value, places = 1) {
  if (kind === "share") return decimalText(value * 100, places);
  if (kind === "rate") return decimalText(value, places);
  return groupDigits(roundHalfUp(value));
}
var SLOT = /\{([A-Za-z]+)(?::([^|{}]*)\|([^|{}]*))?\}/g;
function slots(template) {
  return [...new Set([...template.matchAll(SLOT)].map((match) => match[1]))];
}
function fill(template, values) {
  return template.replace(SLOT, (_match, name, one, other) => {
    if (!(name in values)) throw new Error(`no value for {${name}} in "${template}"`);
    const value = values[name];
    if (one !== void 0 && other !== void 0) return value === 1 ? one : other;
    if (value === null) return UNCOUNTED;
    return typeof value === "number" ? groupDigits(value) : value;
  });
}

// src/report/badge.ts
var BADGE_COLORS = { S: "#1f883d", A: "#4d7c0f", B: "#8a6d00", C: "#c2410c", D: "#b91c1c" };
var LABEL_COLOR = "#555";
var PAD = 6;
var charWidth = (char) => /[0-9]/.test(char) ? 7 : /[A-Z]/.test(char) ? 8 : char === " " || char === "\xB7" ? 4 : 7;
var textWidth = (text) => [...text].reduce((sum2, char) => sum2 + charWidth(char), 0);
function badgeSvg(score) {
  const label = "AQ";
  const message = `${score.aq} \xB7 ${score.grade}`;
  const name = `${label} ${message}`;
  const left = textWidth(label) + PAD * 2;
  const right = textWidth(message) + PAD * 2;
  const width = left + right;
  const color = BADGE_COLORS[score.grade];
  return `${[
    `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="20" viewBox="0 0 ${width} 20" role="img" aria-label="${name}">`,
    `<title>${name}</title>`,
    `<rect width="${width}" height="20" rx="3" fill="${LABEL_COLOR}"/>`,
    `<rect x="${left}" width="${right}" height="20" rx="3" fill="${color}"/>`,
    // 오른쪽 칸의 왼쪽 모서리는 각지게 덮는다
    `<rect x="${left}" width="4" height="20" fill="${color}"/>`,
    `<g fill="#fff" text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" font-size="11">`,
    `<text x="${left / 2}" y="14">${label}</text>`,
    `<text x="${left + right / 2}" y="14">${message}</text>`,
    "</g>",
    "</svg>"
  ].join("")}
`;
}

// src/state/history.ts
import { appendFile, mkdir, open, readFile } from "node:fs/promises";
import { join } from "node:path";

// src/core/reasons.ts
var REASONS = ["unsupported", "unreadable", "not_applicable", "incomplete", "no_data", "too_little", "watching"];
var RESOLVABLE = /* @__PURE__ */ new Set(["unreadable", "incomplete", "no_data", "too_little", "watching"]);
var rank = (reason) => REASONS.indexOf(reason);
function ruleReason(toolReasons) {
  if (toolReasons.length === 0) return "no_data";
  const resolvable = toolReasons.filter((reason) => RESOLVABLE.has(reason));
  const pool = resolvable.length > 0 ? resolvable : toolReasons;
  return pool.reduce((last, reason) => rank(reason) > rank(last) ? reason : last);
}

// src/core/rules.ts
var RULES_VERSION = "1.0.0";
var rule = (id, axis, kind, zeroAt, fullAt, weight, unit, tunable = false) => ({ id, axis, kind, zeroAt, fullAt, weight, unit, tunable });
var RULES = [
  rule("S1", "setup", "share", 0, 1, 3, "merged"),
  rule("S2", "setup", "share", 0, 1, 3, "merged"),
  rule("S3", "setup", "count", 3, 0, 2, "merged"),
  rule("S4", "setup", "share", 0.1, 0.01, 2, "perTool"),
  rule("S5", "setup", "share", 0.3, 0.02, 2, "perTool"),
  rule("E1", "efficiency", "share", 0.5, 0.9, 3, "perTool"),
  rule("E2", "efficiency", "share", 0.12, 0.02, 3, "perTool"),
  rule("E3", "efficiency", "rate", 3, 0.2, 3, "perTool"),
  rule("E4", "efficiency", "amount", 16e3, 4e3, 2, "perTool"),
  rule("E5", "efficiency", "share", 0.8, 0.2, 2, "perTool", true),
  rule("E6", "efficiency", "share", 0.7, 0.1, 2, "perTool", true),
  rule("E7", "efficiency", "rate", 0.15, 0.02, 1, "perTool"),
  rule("F1", "fit", "share", 0.95, 0.6, 1, "perTool"),
  rule("F2", "fit", "share", 0.1, 0.6, 1, "perTool"),
  rule("F3", "fit", "share", 0.2, 0.8, 3, "merged"),
  rule("F4", "fit", "share", 0.25, 0.02, 2, "merged"),
  rule("F5", "fit", "rate", 0.4, 0, 2, "perTool"),
  rule("F6", "fit", "count", 3, 0, 2, "merged"),
  rule("I1", "intensity", "count", 2, 20, 3, "merged"),
  rule("I2", "intensity", "rate", 3, 40, 3, "merged"),
  rule("I3", "intensity", "rate", 1, 8, 2, "merged"),
  rule("I4", "intensity", "count", 1, 4, 1, "merged")
];
function ruleSpec(id) {
  const found = RULES.find((spec) => spec.id === id);
  if (found === void 0) throw new Error(`unknown rule: ${id}`);
  return found;
}

// src/core/scoreboard.ts
var isMerged = (id) => RULES.some((spec) => spec.id === id && spec.unit === "merged");
var MERGED_RULES = RULES.map((spec) => spec.id).filter(isMerged);
var TOOL_RULES = RULES.map((spec) => spec.id).filter((id) => !isMerged(id));
var AXES = ["setup", "efficiency", "fit", "intensity"];
var CATEGORY_ORDER = ["strength", "average", "repair", "unmeasured"];
var SEVERITY_ORDER = ["critical", "caution", "info"];
var byText = (a, b) => a < b ? -1 : a > b ? 1 : 0;
function rateMerged(spec, measurement) {
  if (measurement.status === "unmeasured") return { status: "unmeasured", reason: measurement.reason, value: null, score: null, evidence: measurement.evidence, tools: [] };
  return { status: "scored", reason: null, value: measurement.value, score: ruleScore(measurement.value, spec.zeroAt, spec.fullAt), evidence: measurement.evidence, tools: [] };
}
function rateTools(spec, id, tools2) {
  const responses = new Map(tools2.map((tool) => [tool.tool, tool.responses]));
  const values = tools2.map((tool) => {
    const measurement = tool.rules[id];
    const candidates = tool.candidates.filter((candidate) => candidate.rule === id).map((candidate) => candidate.id);
    if (measurement.status === "unmeasured") return { tool: tool.tool, status: "unmeasured", reason: measurement.reason, value: null, score: null, evidence: measurement.evidence, candidates };
    return { tool: tool.tool, status: "scored", reason: null, value: measurement.value, score: ruleScore(measurement.value, spec.zeroAt, spec.fullAt), evidence: measurement.evidence, candidates };
  });
  const measured2 = values.filter((value) => value.status === "scored");
  if (measured2.length === 0) return { status: "unmeasured", reason: ruleReason(values.map((value) => value.reason)), value: null, score: null, evidence: {}, tools: values };
  const weight = measured2.reduce((sum2, value) => sum2 + responses.get(value.tool), 0);
  const mean = (pick) => measured2.reduce((sum2, value) => sum2 + pick(value) * responses.get(value.tool), 0) / weight;
  return { status: "scored", reason: null, value: mean((value) => value.value), score: mean((value) => value.score), evidence: {}, tools: values };
}
var settled = (score) => score === null ? null : settleScore(score);
function categoryOf(spec, rated, candidates) {
  const score = settled(rated.score);
  const fromUnmeasuredTool = rated.tools.some((tool) => tool.status === "unmeasured" && tool.candidates.length > 0);
  if (spec.tunable && (fromUnmeasuredTool || score !== null && score < 1 && candidates.length > 0)) return "repair";
  if (score === null) return "unmeasured";
  return score >= 0.8 ? "strength" : score >= 0.6 ? "average" : "repair";
}
function severityOf(category, rawScore, weight) {
  const score = settled(rawScore);
  if (category !== "repair") return null;
  if (score === null) return "info";
  if (score < 0.3 && weight === 3) return "critical";
  return score < 0.6 && weight >= 2 ? "caution" : "info";
}
function axisScore(rules) {
  const measured2 = rules.filter((rule2) => rule2.score !== null);
  if (measured2.length === 0) return null;
  const weight = measured2.reduce((sum2, rule2) => sum2 + rule2.weight, 0);
  return roundHalfUp(measured2.reduce((sum2, rule2) => sum2 + rule2.weight * rule2.score, 0) / weight * 100);
}
function compareFindings(a, b, order) {
  const byTable = order.get(a.ruleId) - order.get(b.ruleId);
  const byCategory = CATEGORY_ORDER.indexOf(a.category) - CATEGORY_ORDER.indexOf(b.category);
  if (byCategory !== 0) return byCategory;
  if (a.category === "strength") return settleScore(b.weight * b.score) - settleScore(a.weight * a.score) || byTable;
  if (a.category === "repair") {
    if (a.gain === null || b.gain === null) return (a.gain === null ? 1 : 0) - (b.gain === null ? 1 : 0) || byTable;
    return b.gain - a.gain || SEVERITY_ORDER.indexOf(a.severity) - SEVERITY_ORDER.indexOf(b.severity) || byTable;
  }
  return byTable;
}
function scoreboard(measured2) {
  const tools2 = [...measured2.tools].sort((a, b) => byText(a.tool, b.tool));
  const rated = new Map(RULES.map((spec) => [spec.id, isMerged(spec.id) ? rateMerged(spec, measured2.merged[spec.id]) : rateTools(spec, spec.id, tools2)]));
  const scores = new Map(AXES.map((axis) => [axis, axisScore(RULES.filter((spec) => spec.axis === axis).map((spec) => ({ weight: spec.weight, score: rated.get(spec.id).score })))]));
  const findings = RULES.map((spec) => {
    const rule2 = rated.get(spec.id);
    const candidates = rule2.tools.flatMap((tool) => tool.candidates);
    const category = categoryOf(spec, rule2, candidates);
    const raised = RULES.filter((other) => other.axis === spec.axis).map((other) => ({ weight: other.weight, score: other.id === spec.id ? 1 : rated.get(other.id).score }));
    const gain = rule2.score !== null && settleScore(rule2.score) < 1 ? axisScore(raised) - scores.get(spec.axis) : null;
    return { ruleId: spec.id, axis: spec.axis, kind: spec.kind, weight: spec.weight, status: rule2.status, reason: rule2.reason, value: rule2.value, score: rule2.score, category, severity: severityOf(category, rule2.score, spec.weight), gain, evidence: rule2.evidence, tools: rule2.tools, candidates };
  });
  const axes = AXES.map((axis) => {
    const own = findings.filter((finding) => finding.axis === axis);
    return { axis, score: scores.get(axis), strengths: own.filter((finding) => finding.category === "strength").length, repairs: own.filter((finding) => finding.category === "repair").length };
  });
  const order = new Map(RULES.map((spec, index) => [spec.id, index]));
  return { axes, findings: findings.sort((a, b) => compareFindings(a, b, order)) };
}
var MIN_REQUESTS_FOR_AQ = 20;
var MIN_DAYS_FOR_AQ = 3;
function aqOfAxes(scores) {
  return roundHalfUp(scores.reduce((sum2, score) => sum2 + score, 0) / scores.length);
}
function overall(axes, humanRequests, activeDays2, webOnly = false) {
  const measured2 = axes.flatMap((axis) => axis.score === null ? [] : [axis.score]);
  const missingAxes = axes.filter((axis) => axis.score === null).map((axis) => axis.axis);
  const withheld = [];
  if (humanRequests < MIN_REQUESTS_FOR_AQ) withheld.push("too_few_requests");
  if (activeDays2 < MIN_DAYS_FOR_AQ) withheld.push("too_few_days");
  if (measured2.length === 0) withheld.push("no_axes");
  if (webOnly) withheld.push("no_setup_tools");
  if (withheld.length > 0) return { aq: null, grade: null, tier: null, withheld, missingAxes };
  const aq = aqOfAxes(measured2);
  return { aq, ...gradeOf(aq), withheld, missingAxes };
}

// src/state/history.ts
var HISTORY_FILE = "history.jsonl";
function historyEntry(evaluation, nowMs) {
  const byAxis = new Map(evaluation.axes.map((axis) => [axis.axis, axis.score]));
  const axes = Object.fromEntries(AXES.map((axis) => [axis, byAxis.get(axis) ?? null]));
  return { at: new Date(nowMs).toISOString(), aq: evaluation.score.aq, axes, missingAxes: [...evaluation.score.missingAxes], rulesVersion: evaluation.rulesVersion };
}
async function endsMidLine(path) {
  let handle;
  try {
    handle = await open(path, "r");
  } catch (error) {
    if (error.code === "ENOENT") return false;
    throw error;
  }
  try {
    const { size } = await handle.stat();
    if (size === 0) return false;
    const last = Buffer.alloc(1);
    await handle.read(last, 0, 1, size - 1);
    return last[0] !== 10;
  } finally {
    await handle.close();
  }
}
async function appendHistory(stateDir2, entry) {
  await mkdir(stateDir2, { recursive: true });
  const path = join(stateDir2, HISTORY_FILE);
  const prefix = await endsMidLine(path) ? "\n" : "";
  await appendFile(path, `${prefix}${JSON.stringify(entry)}
`);
}
async function historyCount(stateDir2) {
  let text;
  try {
    text = await readFile(join(stateDir2, HISTORY_FILE), "utf8");
  } catch (error) {
    if (error.code === "ENOENT") return 0;
    throw error;
  }
  return text.split("\n").filter((line) => line.trim() !== "").length;
}
async function recentAq(stateDir2, limit = 12) {
  let text;
  try {
    text = await readFile(join(stateDir2, HISTORY_FILE), "utf8");
  } catch {
    return [];
  }
  const entries = [];
  for (const line of text.split("\n")) {
    if (line.trim() === "") continue;
    try {
      const value = JSON.parse(line);
      if (typeof value.at === "string" && (value.aq === null || typeof value.aq === "number")) entries.push({ at: value.at, aq: value.aq });
    } catch {
    }
  }
  return entries.slice(-limit);
}

// src/commands/badge.ts
var BADGE_FILE = "badge.svg";
var BADGE_LINK = "https://github.com/yeunlee1/chunsik-garage";
var COPY = {
  en: { made: "Made the AQ {aq} \xB7 {grade} badge from the checkup of {date}. The file is at {path}.", howTo: "Put this file next to your README and add the line below to the README." },
  ko: { made: "{date} \uC810\uAC80\uC758 AQ {aq} \xB7 {grade}\uB85C \uBC30\uC9C0\uB97C \uB9CC\uB4E4\uC5C8\uC2B5\uB2C8\uB2E4. \uD30C\uC77C\uC740 {path}\uC5D0 \uC788\uC2B5\uB2C8\uB2E4.", howTo: "\uC774 \uD30C\uC77C\uC744 README\uC640 \uAC19\uC740 \uD3F4\uB354\uC5D0 \uB450\uACE0 \uC544\uB798 \uC904\uC744 README\uC5D0 \uBD99\uC774\uC138\uC694." }
};
var failure = (code, message) => Object.assign(new Error(message), { code });
var localDate = (iso, timeZone) => new Intl.DateTimeFormat("en-CA", { timeZone, year: "numeric", month: "2-digit", day: "2-digit" }).format(new Date(iso));
async function runBadge(options) {
  const scored2 = (await recentAq(options.stateDir, Number.MAX_SAFE_INTEGER)).filter((entry) => entry.aq !== null && Number.isInteger(entry.aq) && entry.aq >= 0 && entry.aq <= 100 && !Number.isNaN(Date.parse(entry.at)));
  const latest = scored2.at(-1);
  if (latest === void 0) throw failure("no-score", "no saved checkup has an AQ");
  const { grade } = gradeOf(latest.aq);
  const path = join2(options.stateDir, BADGE_FILE);
  const temp = `${path}.${process.pid}.tmp`;
  try {
    await mkdir2(options.stateDir, { recursive: true });
    await writeFile(temp, badgeSvg({ aq: latest.aq, grade }));
    await rename(temp, path);
  } catch (error) {
    await rm(temp, { force: true }).catch(() => void 0);
    throw failure("badge-unwritten", `could not write the badge (${error.code ?? "unknown"})`);
  }
  const copy2 = COPY[options.lang];
  return {
    badge: { path, aq: latest.aq, grade, at: latest.at, markdown: `[![AQ ${latest.aq} \xB7 ${grade}](${BADGE_FILE})](${BADGE_LINK})` },
    run: { text: { made: fill(copy2.made, { aq: latest.aq, grade, date: localDate(latest.at, options.timeZone), path }), howTo: copy2.howTo } }
  };
}

// src/commands/checkup.ts
import { join as join31 } from "node:path";

// src/adapters/common/dates.ts
var SCORE_WINDOW_DAYS = 30;
var COLLECT_WINDOW_DAYS = 35;
var QUARTER_MS = 15 * 60 * 1e3;
var MAX_UTC_OFFSET_MS = 14 * 60 * 60 * 1e3;
var formatters = /* @__PURE__ */ new Map();
var quarterDates = /* @__PURE__ */ new Map();
function formatterFor(timeZone) {
  let formatter = formatters.get(timeZone);
  if (formatter === void 0) {
    formatter = new Intl.DateTimeFormat("en-US", { timeZone, year: "numeric", month: "2-digit", day: "2-digit" });
    formatters.set(timeZone, formatter);
  }
  return formatter;
}
function localDateOf(epochMs, timeZone) {
  const quarter = Math.floor(epochMs / QUARTER_MS);
  const key = `${timeZone}|${quarter}`;
  const cached = quarterDates.get(key);
  if (cached !== void 0) return cached;
  const parts = formatterFor(timeZone).formatToParts(new Date(quarter * QUARTER_MS));
  const part = (type) => parts.find((p) => p.type === type)?.value ?? "";
  const date = `${part("year")}-${part("month")}-${part("day")}`;
  quarterDates.set(key, date);
  return date;
}
function localDateOfIso(iso, timeZone) {
  if (typeof iso !== "string") return null;
  const epochMs = Date.parse(iso);
  return Number.isFinite(epochMs) ? localDateOf(epochMs, timeZone) : null;
}
function shiftDate(date, days) {
  const [y, m, d] = date.split("-").map(Number);
  return new Date(Date.UTC(y, m - 1, d + days)).toISOString().slice(0, 10);
}
function makeWindows(nowMs, timeZone) {
  const today = localDateOf(nowMs, timeZone);
  const span2 = (count) => Array.from({ length: count }, (_, i) => shiftDate(today, i - (count - 1)));
  const collectDates = span2(COLLECT_WINDOW_DAYS);
  const [y, m, d] = collectDates[0].split("-").map(Number);
  return {
    today,
    scoreDates: span2(SCORE_WINDOW_DAYS),
    collectDates,
    collectStartLowerBoundMs: Date.UTC(y, m - 1, d) - MAX_UTC_OFFSET_MS
  };
}

// src/core/installs/age.ts
var ESTABLISHED_DAYS = 14;
var RECENT_USE_DAYS = 30;
var DAY_MS = 24 * 60 * 60 * 1e3;
var epochDay = (date) => {
  const [y, m, d] = date.split("-").map(Number);
  return Date.UTC(y, m - 1, d) / DAY_MS;
};
function daysBefore(today, date) {
  return epochDay(today) - epochDay(date);
}
function daysAfter(date, days) {
  return new Date((epochDay(date) + days) * DAY_MS).toISOString().slice(0, 10);
}
function olderThan(today, date, days) {
  return daysBefore(today, date) > days;
}
function msOlderThan(day, epochMs, days) {
  return olderThan(day.today, localDateOf(epochMs, day.timeZone), days);
}

// src/core/installs/candidates.ts
var byText2 = (a, b) => a < b ? -1 : a > b ? 1 : 0;
var make = (tool, unit, rule2, targets) => [...targets].sort(byText2).map((target) => ({ id: `${unit}:${tool.tool}:${target}`, unit, rule: rule2, tool: tool.tool, target }));
function codexCandidates(tool, servers) {
  const a4 = /* @__PURE__ */ new Set();
  for (const judged of servers.servers) {
    const { server } = judged;
    if (server.scope !== "user" || !server.enabled || server.managedFixed || judged.verdict !== "unused" || judged.excluded !== null) continue;
    const sameName = servers.servers.filter((other) => other !== judged && other.server.scope === "project" && other.server.enabled && other.server.name === server.name);
    if (sameName.every((other) => other.verdict === "unused" && other.excluded === null)) a4.add(server.name);
  }
  return make(tool, "A4", "E6", a4);
}
function candidatesOf(tool, skills, servers, day, self) {
  if (tool.tool === "codex") return codexCandidates(tool, servers);
  if (tool.tool === "gemini") return [];
  const { setup } = tool;
  const enabledPlugins = setup.plugins.filter((plugin) => plugin.enabled);
  const unknownPlugin = enabledPlugins.some((plugin) => !plugin.compositionKnown) || setup.pluginsWithoutInstall.length > 0;
  const hooksUnseen = unknownPlugin || enabledPlugins.some((plugin) => plugin.hooksUnreadable);
  const selfPaths = new Set(self.skillRealPaths);
  const selfPlugins = new Set(setup.plugins.filter((plugin) => self.pluginNames.includes(plugin.entryName) || self.pluginNames.includes(plugin.name)).map((plugin) => plugin.id));
  const isSelfBundle = (bundle) => bundle.positions.some(
    (skill) => skill.realPath !== null && selfPaths.has(skill.realPath) || skill.recordNames.some((name) => self.skillNames.includes(name)) || skill.pluginId !== null && selfPlugins.has(skill.pluginId)
  );
  const turnedOffBy = (target) => skills.bundles.filter((bundle) => bundle.positions.some((position) => position.recordNames.includes(target)));
  const confirmed = (bundle) => bundle.verdict === "unused" && bundle.excluded === null;
  const namesUnknown = setup.skills.some((skill) => skill.nameUnreadable || !skill.readable);
  const a1 = /* @__PURE__ */ new Set();
  const a2 = /* @__PURE__ */ new Set();
  const a3 = /* @__PURE__ */ new Set();
  if (!hooksUnseen) {
    if (!namesUnknown) {
      for (const bundle of skills.bundles) {
        if (!bundle.enabled || !confirmed(bundle)) continue;
        for (const skill of bundle.positions) {
          if (skill.scope !== "user" || !skill.enabled || skill.managedFixed) continue;
          const affected = turnedOffBy(skill.name);
          if (affected.every(confirmed) && !affected.some(isSelfBundle)) a1.add(skill.name);
        }
      }
    }
    const uncounted = new Set(setup.unreadableSkillPlaces.plugins);
    const usageStale2 = (plugin) => setup.claudeJson === "ok" && !plugin.usageUndated && (plugin.usageLastUsedMs === null || msOlderThan(day, plugin.usageLastUsedMs, RECENT_USE_DAYS));
    for (const plugin of enabledPlugins) {
      const sameId = setup.plugins.filter((other) => other.id === plugin.id);
      if (sameId.length !== 1 || plugin.scopes.length !== 1 || plugin.scopes[0] !== "user") continue;
      if (!plugin.exists || !plugin.compositionKnown || plugin.managedFixed || plugin.mcpUnreadable || uncounted.has(plugin.id)) continue;
      if (self.pluginNames.includes(plugin.entryName) || self.pluginNames.includes(plugin.name)) continue;
      if (plugin.components.some((component) => component !== "skills") || plugin.unknownEntries.length > 0 || !usageStale2(plugin)) continue;
      if (enabledPlugins.some((other) => other.id !== plugin.id && (other.dependencies === null || other.dependencies.includes(plugin.entryName)))) continue;
      const own = skills.bundles.filter((bundle) => bundle.positions.some((skill) => skill.pluginId === plugin.id));
      if (own.length === 0 || !own.every(confirmed) || own.some(isSelfBundle)) continue;
      a2.add(plugin.id);
    }
  }
  for (const judged of servers.servers) {
    const { server } = judged;
    if (server.scope !== "user" || !server.enabled || server.managedFixed || judged.verdict !== "unused" || judged.excluded !== null) continue;
    const sameName = servers.servers.filter((other) => other !== judged && other.server.scope !== "plugin" && other.server.enabled && other.server.name === server.name);
    if (sameName.every((other) => other.verdict === "unused" && other.excluded === null)) a3.add(server.name);
  }
  return [...make(tool, "A1", "E5", a1), ...make(tool, "A2", "E5", a2), ...make(tool, "A3", "E6", a3)];
}

// src/core/measure.ts
var scored = (value, evidence) => ({ status: "scored", value, evidence });
var unmeasured = (reason, evidence) => ({ status: "unmeasured", reason, evidence });
var blank = (evidence) => Object.fromEntries(Object.keys(evidence).map((key) => [key, null]));
function countGate(sees2, denominator, minimum, evidence) {
  if (!sees2) return unmeasured("unsupported", blank(evidence));
  if (denominator <= 0) return unmeasured("no_data", evidence);
  if (denominator < minimum) return unmeasured("too_little", evidence);
  return null;
}

// src/core/installs/gate.ts
var BLANK_INSTALL_EVIDENCE = { enabled: null, judgeable: null, judged: null, structural: null, unused: null, used: null };
function measureInstalls(enabled, complete, minimum) {
  const structural = enabled.filter((item2) => item2.structural).length;
  const judgeable = enabled.length - structural;
  const used = enabled.filter((item2) => !item2.structural && item2.verdict === "used").length;
  const unused = enabled.filter((item2) => !item2.structural && item2.verdict === "unused").length;
  const judged = used + unused;
  const evidence = { enabled: enabled.length, judgeable, judged, structural, unused, used };
  if (enabled.length === 0) return unmeasured("not_applicable", evidence);
  if (judgeable === 0) return unmeasured("unsupported", evidence);
  if (!complete) return unmeasured("incomplete", evidence);
  if (judgeable < minimum) return unmeasured("too_little", evidence);
  if (judged * 2 < judgeable || judged < minimum) return unmeasured("watching", evidence);
  return scored(unused / judged, evidence);
}

// src/core/installs/signals.ts
function collectNames(summaries, windows, namesOf) {
  const score = new Set(windows.scoreDates);
  const collect = new Set(windows.collectDates);
  const inScore = /* @__PURE__ */ new Set();
  const inCollect = /* @__PURE__ */ new Set();
  for (const summary of summaries) {
    for (const [date, cell] of Object.entries(summary.days)) {
      if (!collect.has(date)) continue;
      for (const name of namesOf(cell)) {
        inCollect.add(name);
        if (score.has(date)) inScore.add(name);
      }
    }
  }
  return { inScore, inCollect };
}
var positive = (record) => Object.keys(record).filter((name) => record[name] > 0);
function usedSkillNames(summaries, windows) {
  return collectNames(
    summaries,
    windows,
    (cell) => Object.keys(cell.skillSignals).filter((name) => {
      const counts = cell.skillSignals[name];
      return counts.tool + counts.attribution + counts.slash + counts.injected > 0;
    })
  );
}
function calledMcpNames(summaries, windows) {
  return collectNames(summaries, windows, (cell) => [...positive(cell.mcpCalls), ...positive(cell.mcpAttributions)]);
}
function anyIn(recordNames, names2) {
  return recordNames.some((name) => names2.has(name));
}

// src/core/installs/listing.ts
function sessionListings(summaries, kind, normalizedCwds, lookup) {
  const normalized2 = new Map(Object.entries(normalizedCwds));
  const out = [];
  for (const summary of summaries) {
    if (summary.kind !== "main") continue;
    const initialNames = kind === "skill" ? summary.initialSkills : summary.initialMcpServers;
    const everLoaded = new Set(initialNames ?? []);
    const days = [];
    for (const date of Object.keys(summary.days).sort()) {
      const cell = summary.days[date];
      const loaded = new Set(kind === "skill" ? cell.loadedSkills : cell.loadedMcpServers);
      for (const name of loaded) everLoaded.add(name);
      days.push({ date, responses: cell.responses, loaded, reloaded: new Set(kind === "skill" ? cell.reloadedSkills : cell.reloadedMcpServers) });
    }
    out.push({
      cwdKey: summary.cwd === null ? null : normalized2.get(summary.cwd) ?? summary.cwd,
      projectRoot: lookup(summary.cwd)?.normRoot ?? null,
      firstDate: summary.firstDate,
      initial: initialNames === null ? null : new Set(initialNames),
      days,
      everLoaded
    });
  }
  return out;
}
function loadedSince(listings, recordNames, projectRoot, windows) {
  const collect = new Set(windows.collectDates);
  const loadedOn = /* @__PURE__ */ new Map();
  for (const listing of listings) {
    if (listing.initial === null || projectRoot !== null && listing.projectRoot !== projectRoot) continue;
    for (const day of listing.days) {
      if (!collect.has(day.date) || day.responses <= 0) continue;
      loadedOn.set(day.date, (loadedOn.get(day.date) ?? true) && anyIn(recordNames, day.loaded));
    }
  }
  let lastMissing = "";
  for (const [date, loaded] of loadedOn) if (!loaded && date > lastMissing) lastMissing = date;
  for (const [date, loaded] of loadedOn) if (loaded && date > lastMissing && olderThan(windows.today, date, ESTABLISHED_DAYS)) return true;
  return false;
}
function restartedRecently(listings, recordNames, today) {
  const recent = (date) => date === null || !olderThan(today, date, ESTABLISHED_DAYS);
  const loadedIn = /* @__PURE__ */ new Set();
  for (const listing of listings) {
    if (listing.days.some((day) => recent(day.date) && anyIn(recordNames, day.reloaded))) return true;
    if (listing.cwdKey !== null && anyIn(recordNames, listing.everLoaded)) loadedIn.add(listing.cwdKey);
  }
  return listings.some((listing) => listing.cwdKey !== null && loadedIn.has(listing.cwdKey) && listing.initial !== null && recent(listing.firstDate) && !anyIn(recordNames, listing.initial));
}
function restartDates(listings, recordNames, today) {
  const recent = (date) => !olderThan(today, date, ESTABLISHED_DAYS);
  const dates = [];
  const loadedIn = /* @__PURE__ */ new Set();
  for (const listing of listings) {
    for (const day of listing.days) if (recent(day.date) && anyIn(recordNames, day.reloaded)) dates.push(day.date);
    if (listing.cwdKey !== null && anyIn(recordNames, listing.everLoaded)) loadedIn.add(listing.cwdKey);
  }
  for (const listing of listings) {
    if (listing.cwdKey === null || !loadedIn.has(listing.cwdKey) || listing.initial === null || anyIn(recordNames, listing.initial)) continue;
    if (listing.firstDate === null) return null;
    if (recent(listing.firstDate)) dates.push(listing.firstDate);
  }
  return dates;
}

// src/core/order.ts
function byContent(a, b) {
  const left = JSON.stringify(a);
  const right = JSON.stringify(b);
  return left < right ? -1 : left > right ? 1 : 0;
}

// src/core/readability.ts
var unread = (status) => status === "unparsable" || status === "unreadable";
function codexSettingsUnread(facts) {
  return unread(facts.config) || facts.projects.some((project) => project.trust === "trusted" && unread(project.configStatus));
}
function geminiSettingsUnread(facts) {
  return unread(facts.settings) || facts.managedParts.some((part) => unread(part.status)) || facts.folderTrust && unread(facts.trustedFolders) || facts.projects.some((project) => project.scanned && project.trusted && unread(project.settingsStatus));
}
function globalSettingsUnread(facts) {
  return unread(facts.settings.user) || facts.settings.managedParts.some((part) => unread(part.status));
}
function projectSettingsUnread(facts) {
  return facts.projects.some((project) => unread(project.settingsStatus) || unread(project.localSettingsStatus));
}
function enablementUnread(facts) {
  return globalSettingsUnread(facts) || projectSettingsUnread(facts);
}
function mcpPlacesUnread(facts) {
  return unread(facts.claudeJson) || unread(facts.pluginsFile) || facts.projects.some((project) => unread(project.mcpJsonStatus)) || facts.plugins.some((plugin) => plugin.enabled && (!plugin.compositionKnown || plugin.mcpUnreadable)) || facts.pluginsWithoutInstall.length > 0 || facts.unreadableSkillPlaces.user || facts.unreadableSkillPlaces.projects.length > 0;
}

// src/core/installs/same.ts
function sameInstall(items, keyOf2) {
  const byKey = /* @__PURE__ */ new Map();
  const groups = [];
  for (const item2 of items) {
    const key = keyOf2(item2);
    const group = key === null ? void 0 : byKey.get(key);
    if (group !== void 0) {
      group.push(item2);
      continue;
    }
    const fresh = [item2];
    groups.push(fresh);
    if (key !== null) byKey.set(key, fresh);
  }
  return groups;
}

// src/core/installs/verdict.ts
function recordMap(installs) {
  return installs === null ? null : new Map(installs.map((record) => [record.key, record]));
}
function observed(key, context) {
  const record = key === null ? void 0 : context.records?.get(key);
  const long = record !== void 0 && olderThan(context.day.today, record.firstSeen, ESTABLISHED_DAYS);
  return {
    // ㉯ 같은 정체의 설치를 계속 봐 온 첫날이 14일 넘게 앞선다
    seenLong: long,
    // ㉲ 지난 점검에는 없다가 14일 안의 점검에 새로 나타났다
    appearedRecently: record !== void 0 && record.appeared && !long,
    // ㉳ 관측 기록은 있는데 이 정체의 기록이 없다. 지난 점검과 정체가 다르다
    changed: context.records !== null && record === void 0
  };
}
function skillEstablished(skill, context) {
  const created = skill.isLink ? [skill.createdMs, skill.targetCreatedMs] : [skill.createdMs];
  const recent = (ms) => ms !== null && !msOlderThan(context.day, ms, ESTABLISHED_DAYS);
  const state = observed(skill.installKey, context);
  const createdLongAgo = created.every((ms) => ms !== null && !recent(ms));
  const loaded = createdLongAgo && loadedSince(context.listings, skill.recordNames, skill.scope === "project" ? skill.projectRoot : null, context.windows);
  if (!loaded && !state.seenLong) return false;
  return !(created.some(recent) || restartedRecently(context.listings, skill.recordNames, context.day.today) || state.appearedRecently || state.changed);
}
function serverEstablished(server, context) {
  if (server.installKey === null) return false;
  const state = observed(server.installKey, context);
  return state.seenLong && !(restartedRecently(context.listings, server.recordNames, context.day.today) || state.appearedRecently || state.changed);
}
function serverJudgeableFrom(server, context) {
  if (server.installKey === null) return null;
  const first = context.records?.get(server.installKey)?.firstSeen ?? context.day.today;
  const restarts = restartDates(context.listings, server.recordNames, context.day.today);
  if (restarts === null) return null;
  return [first, ...restarts].map((date) => daysAfter(date, ESTABLISHED_DAYS + 1)).reduce((a, b) => a > b ? a : b);
}
function usageStale(skill, claudeJson, day) {
  if (claudeJson !== "ok" || skill.usageUndated) return false;
  return skill.usageLastUsedMs === null || msOlderThan(day, skill.usageLastUsedMs, RECENT_USE_DAYS);
}
function skillVerdict(skill, claudeJson, context) {
  if (skill.hookProvided) return "unknown";
  if (anyIn(skill.recordNames, context.used.inScore)) return "used";
  if (skill.nameUnreadable || !skill.readable) return "unknown";
  const unused = !anyIn(skill.recordNames, context.used.inCollect) && // ①
  usageStale(skill, claudeJson, context.day) && // ②
  context.complete && // ③
  skillEstablished(skill, context);
  return unused ? "unused" : "unknown";
}
function serverVerdict(server, context) {
  if (server.installKey === null) return "unknown";
  if (anyIn(server.recordNames, context.used.inScore)) return "used";
  return !anyIn(server.recordNames, context.used.inCollect) && context.complete && serverEstablished(server, context) ? "unused" : "unknown";
}

// src/core/installs/servers.ts
var MIN_JUDGED_SERVERS = 2;
var SCOPE_ORDER = { user: 0, local: 1, project: 2, plugin: 3, "claude-ai": 4 };
var byText3 = (a, b) => a < b ? -1 : a > b ? 1 : 0;
var byServer = (a, b) => byText3(a.name, b.name) || SCOPE_ORDER[a.scope] - SCOPE_ORDER[b.scope] || byText3(a.projectRoot ?? "", b.projectRoot ?? "") || byText3(a.pluginId ?? "", b.pluginId ?? "") || byText3(a.definitionHash ?? "", b.definitionHash ?? "") || // 같은 플러그인을 두 길로 찾으면 켜짐만 다른 서버 사실 둘이 온다. 내용까지 견줘 차례를 끝까지 정한다
byContent(a, b);
function serversUnread(tool) {
  if (tool.tool === "codex") return codexSettingsUnread(tool.setup);
  if (tool.tool === "gemini") return geminiSettingsUnread(tool.setup);
  const { setup } = tool;
  const places = setup.unreadableSkillPlaces;
  return unread(setup.claudeJson) || places.user || places.projects.length > 0 || setup.projects.some((project) => unread(project.mcpJsonStatus)) || unread(setup.pluginsFile) || enablementUnread(setup);
}
function judgeServers(tool, context) {
  if (tool.tool === "gemini") return { measurement: unmeasured("unsupported", blank(BLANK_INSTALL_EVIDENCE)), servers: [] };
  const { setup } = tool;
  if (tool.coverage.mcpCalls === "unsupported") return { measurement: unmeasured("unsupported", blank(BLANK_INSTALL_EVIDENCE)), servers: [] };
  if (serversUnread(tool)) return { measurement: unmeasured("unreadable", blank(BLANK_INSTALL_EVIDENCE)), servers: [] };
  const unreadPlugins = new Set(setup.plugins.filter((plugin) => !plugin.compositionKnown || plugin.mcpUnreadable).map((plugin) => plugin.id));
  const servers = [...setup.mcpServers].sort(byServer).map((server) => {
    if (server.installKey === null) return { server, verdict: "unknown", excluded: "no_definition", judgeFrom: null };
    if (server.pluginId !== null && unreadPlugins.has(server.pluginId)) return { server, verdict: "unknown", excluded: "plugin_unread", judgeFrom: null };
    const verdict = serverVerdict(server, context);
    return { server, verdict, excluded: null, judgeFrom: verdict === "unknown" ? serverJudgeableFrom(server, context) : null };
  });
  const installs = sameInstall(servers.filter((judged) => judged.server.enabled), (judged) => judged.server.installKey);
  const counted = installs.map((facts) => ({
    verdict: facts.some((judged) => judged.verdict === "used") ? "used" : facts.every((judged) => judged.verdict === "unused") ? "unused" : "unknown",
    structural: facts.some((judged) => judged.excluded !== null)
  }));
  return { measurement: measureInstalls(counted, context.complete, MIN_JUDGED_SERVERS), servers };
}

// src/core/installs/skills.ts
var MIN_JUDGED_SKILLS = 5;
var SCOPE_ORDER2 = { user: 0, project: 1, plugin: 2 };
var byText4 = (a, b) => a < b ? -1 : a > b ? 1 : 0;
var byPosition = (a, b) => byText4(a.name, b.name) || SCOPE_ORDER2[a.scope] - SCOPE_ORDER2[b.scope] || byText4(a.realPath ?? a.path, b.realPath ?? b.path) || byText4(a.installKey, b.installKey) || byText4(a.pluginId ?? "", b.pluginId ?? "") || byText4(a.path, b.path) || byContent(a, b);
function skillsUnread(tool) {
  const { setup } = tool;
  const places = setup.unreadableSkillPlaces;
  return setup.claudeJson !== "ok" || places.user || places.projects.length > 0 || unread(setup.pluginsFile) || enablementUnread(setup);
}
function judgeSkills(tool, context) {
  if (tool.coverage.skillUsage === "unsupported" || tool.tool === "codex" || tool.tool === "gemini") return { measurement: unmeasured("unsupported", blank(BLANK_INSTALL_EVIDENCE)), bundles: [] };
  const { setup } = tool;
  if (skillsUnread(tool)) return { measurement: unmeasured("unreadable", blank(BLANK_INSTALL_EVIDENCE)), bundles: [] };
  const uncounted = new Set(setup.unreadableSkillPlaces.plugins);
  const grouped = /* @__PURE__ */ new Map();
  for (const skill of [...setup.skills].sort(byPosition)) {
    const key = skill.realPath ?? `\0${skill.installKey}`;
    const positions = grouped.get(key);
    if (positions === void 0) grouped.set(key, [skill]);
    else positions.push(skill);
  }
  const bundles = [];
  for (const positions of grouped.values()) {
    const fromUnreadPlugin = positions.some((skill) => skill.pluginId !== null && uncounted.has(skill.pluginId));
    const excluded = fromUnreadPlugin ? "plugin_unread" : positions.some((skill) => skill.hookProvided) ? "hook_provided" : null;
    const verdicts = positions.map((skill) => skillVerdict(skill, setup.claudeJson, context));
    const verdict = excluded !== null ? "unknown" : verdicts.includes("used") ? "used" : verdicts.every((v) => v === "unused") ? "unused" : "unknown";
    bundles.push({ positions, enabled: positions.some((skill) => skill.enabled), verdict, excluded });
  }
  const counted = bundles.filter((bundle) => bundle.enabled).map((bundle) => ({ verdict: bundle.verdict, structural: bundle.excluded !== null }));
  return { measurement: measureInstalls(counted, context.complete, MIN_JUDGED_SKILLS), bundles };
}

// src/core/metrics/fit.ts
var FREQUENT_SESSIONS = 3;
var byText5 = (a, b) => a < b ? -1 : a > b ? 1 : 0;
var scanned = (project) => project.exists && !project.excluded;
function toolProjects(tool) {
  const projects = tool.tool === "codex" ? tool.setup.projects.filter((project) => project.scanned).map((project) => ({ normRoot: project.normRoot, name: null, instructions: project.instructions, treated: hasInstructionFiles(project.instructions) || project.configStatus !== null && project.configStatus !== "missing" })) : tool.tool === "gemini" ? tool.setup.projects.filter((project) => project.scanned).map((project) => ({ normRoot: project.normRoot, name: null, instructions: project.instructions, treated: hasInstructionFiles(project.instructions) || project.settingsStatus !== null && project.settingsStatus !== "missing" })) : tool.setup.projects.filter(scanned).map((project) => ({ normRoot: project.normRoot, name: project.name, instructions: project.instructions, treated: hasInstructionFiles(project.instructions) || project.hasSettings || project.hasLocalSettings }));
  return projects.sort((a, b) => byText5(a.normRoot, b.normRoot));
}
function hasInstructionFiles(set) {
  return set.files.length > 0 || set.unreadable.length > 0 || set.unreadableDirs.length > 0;
}
var treatedAsProject = (project) => hasInstructionFiles(project.instructions) || project.hasSettings || project.hasLocalSettings;
var hasInstructions = (project) => project?.instructions.files.some((file) => file.hasContent) ?? false;
function mainTools(use) {
  const most = Math.max(...Object.values(use.sessions));
  return Object.keys(use.sessions).filter((tool) => use.sessions[tool] >= FREQUENT_SESSIONS || use.sessions[tool] === most);
}
function f3(tools2, usage2) {
  const byId = new Map(tools2.map((tool) => [tool.tool, new Map(toolProjects(tool).map((project) => [project.normRoot, project]))]));
  const missing = [];
  let targets = 0;
  for (const use of usage2.projects) {
    const { project } = use;
    if (use.total < FREQUENT_SESSIONS || !scanned(project)) continue;
    if (project.kind !== "git" && !treatedAsProject(project) && ![...byId.values()].some((projects) => projects.get(project.normRoot)?.treated === true)) continue;
    targets++;
    const without = mainTools(use).filter((tool) => !hasInstructions(byId.get(tool)?.get(project.normRoot)));
    if (without.length > 0) missing.push({ normRoot: project.normRoot, name: project.name, tools: without });
  }
  const withInstructions = targets - missing.length;
  const evidence = { targets, withInstructions };
  return { measurement: targets === 0 ? unmeasured("not_applicable", evidence) : scored(withInstructions / targets, evidence), missing };
}
var instructionsUnread = (set) => set.unreadable.length > 0 || set.unreadableDirs.length > 0;
function f4(tools2, names2) {
  let unreadable = false;
  let globalLines = 0;
  let comparedProjects = 0;
  let worst = null;
  for (const tool of [...tools2].sort((a, b) => byText5(a.tool, b.tool))) {
    const global = tool.setup.globalInstructions;
    const projects = toolProjects(tool);
    if (instructionsUnread(global) || projects.some((project) => instructionsUnread(project.instructions))) unreadable = true;
    const lines = new Set(global.lineHashes);
    globalLines += lines.size;
    if (global.files.length === 0 || lines.size === 0) continue;
    for (const project of projects) {
      if (!project.instructions.files.some((file) => !file.sameAsGlobal)) continue;
      comparedProjects++;
      const overlapping = new Set(project.instructions.lineHashes.filter((hash) => lines.has(hash))).size;
      const name = project.name ?? names2.get(project.normRoot) ?? project.normRoot;
      if (worst === null || overlapping * worst.globalLines > worst.overlapping * lines.size) worst = { tool: tool.tool, normRoot: project.normRoot, name, overlapping, globalLines: lines.size };
    }
  }
  if (unreadable) return { measurement: unmeasured("unreadable", { comparedProjects: null, globalLines: null, overlappingLines: null }), worst: null };
  if (worst === null) return { measurement: unmeasured("not_applicable", { comparedProjects: 0, globalLines, overlappingLines: 0 }), worst: null };
  const evidence = { comparedProjects, globalLines: worst.globalLines, overlappingLines: worst.overlapping };
  return { measurement: scored(worst.overlapping / worst.globalLines, evidence), worst: { tool: worst.tool, normRoot: worst.normRoot, name: worst.name } };
}
function f5(tool) {
  if (tool.tool === "gemini") return unmeasured("unsupported", { differingCopies: null, identicalCopies: null, skillKinds: null });
  const places = tool.setup.unreadableSkillPlaces;
  if (places.user || places.projects.length > 0) return unmeasured("unreadable", { differingCopies: null, identicalCopies: null, skillKinds: null });
  const hashesByName = /* @__PURE__ */ new Map();
  for (const skill of tool.setup.skills) {
    if (skill.scope === "plugin") continue;
    let copies = hashesByName.get(skill.name);
    if (copies === void 0) hashesByName.set(skill.name, copies = /* @__PURE__ */ new Map());
    if (!skill.isLink) copies.set(skill.realPath ?? skill.path, skill.contentHash);
  }
  let identicalCopies = 0;
  let differingCopies = 0;
  for (const copies of hashesByName.values()) {
    const spare = copies.size - 1;
    if (spare <= 0) continue;
    const hashes = [...copies.values()];
    if (hashes.every((hash) => hash !== null && hash === hashes[0])) identicalCopies += spare;
    else differingCopies += spare;
  }
  const evidence = { differingCopies, identicalCopies, skillKinds: hashesByName.size };
  if (hashesByName.size === 0) return unmeasured("not_applicable", evidence);
  return scored((identicalCopies + 2 * differingCopies) / hashesByName.size, evidence);
}
function f6(tools2) {
  let unreadable = false;
  let conflicts = 0;
  let projectsWithSettings = 0;
  for (const tool of tools2) {
    if (tool.tool !== "claude-code") continue;
    if (unread(tool.setup.settings.user) || projectSettingsUnread(tool.setup)) unreadable = true;
    for (const project of tool.setup.projects.filter(scanned)) {
      if (!project.hasSettings && !project.hasLocalSettings) continue;
      projectsWithSettings++;
      conflicts += project.permissionConflicts;
    }
  }
  if (unreadable) return unmeasured("unreadable", { conflicts: null, projectsWithSettings: null });
  const evidence = { conflicts, projectsWithSettings };
  return projectsWithSettings === 0 ? unmeasured("not_applicable", evidence) : scored(conflicts, evidence);
}
function mergedFitRules(tools2, usage2, projects) {
  const guides = f3(tools2, usage2);
  const overlap = f4(tools2, new Map(projects.map((project) => [project.normRoot, project.name])));
  return { F3: guides.measurement, F4: overlap.measurement, F6: f6(tools2), missingInstructions: guides.missing, worstOverlap: overlap.worst };
}
function fitToolRules(tool) {
  return { F5: f5(tool) };
}

// src/core/metrics/usage.ts
var EFFORT_LEVELS = ["minimal", "low", "medium", "high", "xhigh", "max"];
var HIGH_EFFORT = /* @__PURE__ */ new Set(["xhigh", "max"]);
var MIN_HOOK_RUNS = 100;
var MIN_TOOL_RESULTS = 50;
var MIN_MAIN_SESSIONS = 3;
var MIN_HUMAN_REQUESTS = 20;
var MIN_KNOWN_EFFORT = 50;
var MIN_COMPACTED_SESSIONS = 3;
var sees = (coverage, ...keys) => keys.every((key) => coverage[key] !== "unsupported");
function median(values) {
  const sorted = [...values].sort((a, b) => a - b);
  const middle = Math.floor(sorted.length / 2);
  return sorted.length % 2 === 1 ? sorted[middle] : (sorted[middle - 1] + sorted[middle]) / 2;
}
function s4(totals2, coverage) {
  const evidence = { failures: totals2.hookFailures, runs: totals2.hookRuns, unclassifiedBlocks: totals2.hookUnclassified };
  return countGate(sees(coverage, "mcpFailuresAndHooks"), totals2.hookRuns, MIN_HOOK_RUNS, evidence) ?? scored(totals2.hookFailures / totals2.hookRuns, evidence);
}
function e1(totals2, coverage, tool) {
  const { input, cacheRead, cacheWrite } = totals2.tokens;
  const all = tool === "codex" || tool === "gemini" ? input : input + cacheRead + cacheWrite;
  const evidence = { cacheRead, cacheWrite, input };
  return countGate(sees(coverage, "responsesAndTokens"), all, 1, evidence) ?? scored(cacheRead / all, evidence);
}
function e2(totals2, coverage) {
  const evidence = { errors: totals2.nonShellErrors, results: totals2.nonShellResults };
  return countGate(sees(coverage, "toolErrors"), totals2.nonShellResults, MIN_TOOL_RESULTS, evidence) ?? scored(totals2.nonShellErrors / totals2.nonShellResults, evidence);
}
function e3(totals2, coverage) {
  const autoCompactions = totals2.mainSessions.reduce((sum2, session) => sum2 + session.autoCompactions, 0);
  const evidence = { autoCompactions, mainSessions: totals2.mainSessions.length };
  return countGate(sees(coverage, "autoCompaction"), totals2.mainSessions.length, MIN_MAIN_SESSIONS, evidence) ?? scored(autoCompactions / totals2.mainSessions.length, evidence);
}
function e4(totals2, coverage) {
  const sample = totals2.mainSessions.flatMap((session) => session.instructionTokens === null ? [] : [session.instructionTokens]);
  const evidence = { sampledSessions: sample.length, skippedSessions: totals2.mainSessions.length - sample.length };
  return countGate(sees(coverage, "instructionSize"), sample.length, 1, evidence) ?? scored(median(sample), evidence);
}
function e7(totals2, coverage) {
  const evidence = { denied: totals2.denied, humanRequests: totals2.humanRequests, interruptedTurns: totals2.interruptedTurns, lengthStops: totals2.lengthStops };
  const stopped = totals2.denied + totals2.interruptedTurns + totals2.lengthStops;
  return countGate(sees(coverage, "deniedAndLengthStops", "interruptedTurns"), totals2.humanRequests, MIN_HUMAN_REQUESTS, evidence) ?? scored(stopped / totals2.humanRequests, evidence);
}
function f1(totals2, coverage) {
  let knownEffort = 0;
  let highEffort = 0;
  let unknownLevel = 0;
  const levels = new Set(EFFORT_LEVELS);
  for (const [level, count] of Object.entries(totals2.efforts)) {
    if (!levels.has(level)) unknownLevel += count;
    else {
      knownEffort += count;
      if (HIGH_EFFORT.has(level)) highEffort += count;
    }
  }
  const evidence = { highEffort, knownEffort, unknownEffort: totals2.unknownEffort, unknownLevel };
  return countGate(sees(coverage, "effort"), knownEffort, MIN_KNOWN_EFFORT, evidence) ?? scored(highEffort / knownEffort, evidence);
}
function f2(totals2, coverage) {
  const compacted = totals2.mainSessions.filter((session) => session.autoCompactions > 0);
  const delegatedSessions = compacted.filter((session) => session.subagentCalls > 0).length;
  const evidence = { compactedSessions: compacted.length, delegatedSessions };
  return countGate(sees(coverage, "subagents", "autoCompaction"), compacted.length, MIN_COMPACTED_SESSIONS, evidence) ?? scored(delegatedSessions / compacted.length, evidence);
}
function usageRules(totals2, coverage, tool) {
  return {
    S4: s4(totals2, coverage),
    E1: e1(totals2, coverage, tool),
    E2: e2(totals2, coverage),
    E3: e3(totals2, coverage),
    E4: e4(totals2, coverage),
    E7: e7(totals2, coverage),
    F1: f1(totals2, coverage),
    F2: f2(totals2, coverage)
  };
}

// src/core/metrics/intensity.ts
var seeing = (tools2, ...keys) => tools2.filter((tool) => keys.every((key) => tool.coverage[key] !== "unsupported"));
var anySees = (all, seen) => seen.length > 0 || all.length === 0;
var activeDays = (tools2) => new Set(tools2.flatMap((tool) => tool.totals.activeDates)).size;
var sum = (tools2, pick) => tools2.reduce((total, tool) => total + pick(tool), 0);
function i1(tools2) {
  const days = activeDays(tools2);
  return scored(days, { activeDays: days });
}
function i2(tools2) {
  const seen = seeing(tools2, "humanRequests");
  const days = activeDays(seen);
  const humanRequests = sum(seen, (tool) => tool.totals.humanRequests);
  const evidence = { activeDays: days, humanRequests };
  return countGate(anySees(tools2, seen), days, 1, evidence) ?? scored(humanRequests / days, evidence);
}
function i3(tools2) {
  const seen = seeing(tools2, "humanRequests", "toolCalls");
  const humanRequests = sum(seen, (tool) => tool.totals.humanRequests);
  const toolCalls = sum(seen, (tool) => tool.totals.toolCalls);
  const evidence = { humanRequests, toolCalls };
  return countGate(anySees(tools2, seen), humanRequests, MIN_HUMAN_REQUESTS, evidence) ?? scored(toolCalls / humanRequests, evidence);
}
function i4(usage2) {
  const excludedFolders = usage2.projects.filter((use) => use.project.excluded).length;
  const projects = usage2.projects.length - excludedFolders;
  const evidence = { excludedFolders, projects, unlinkedSessions: usage2.unlinkedSessions };
  return countGate(true, projects, 1, evidence) ?? scored(projects, evidence);
}
function intensityRules(tools2, usage2) {
  return { I1: i1(tools2), I2: i2(tools2), I3: i3(tools2), I4: i4(usage2) };
}

// src/adapters/common/version.ts
function parseVersion(text) {
  if (typeof text !== "string") return null;
  const match = /^(\d+)\.(\d+)\.(\d+)$/.exec(text.trim());
  if (match === null) return null;
  return [Number(match[1]), Number(match[2]), Number(match[3])];
}
function compareVersions(a, b) {
  for (let i = 0; i < 3; i++) {
    const diff = a[i] - b[i];
    if (diff !== 0) return diff;
  }
  return 0;
}
function formatVersion(version) {
  return `${version[0]}.${version[1]}.${version[2]}`;
}
function maxVersion(values) {
  let best = null;
  for (const value of values) {
    const version = parseVersion(value);
    if (version !== null && (best === null || compareVersions(version, best) > 0)) best = version;
  }
  return best === null ? null : formatVersion(best);
}

// src/core/metrics/setup.ts
var MIN_GLOBAL_INSTRUCTION_BYTES = 200;
var PROJECT_BYPASS_IGNORED_FROM = [2, 1, 257];
function highestMainVersion(summaries) {
  return maxVersion(summaries.filter((summary) => summary.kind === "main").map((summary) => summary.version));
}
function guardRuns(guard, hooks) {
  if (hooks.managedDisableAll) return false;
  const fromManaged = guard.source === "managed" || guard.source === "managed-plugin";
  return fromManaged || !(hooks.userDisableAll || hooks.managedAllowManagedOnly);
}
function seesProjectBypass(highestVersion) {
  const version = parseVersion(highestVersion);
  return version === null || compareVersions(version, PROJECT_BYPASS_IGNORED_FROM) < 0;
}
function codexSafeguard(setup) {
  if (codexSettingsUnread(setup)) return { tool: "codex", guardHook: null, permissionChecks: null };
  const contexts = [setup.safety, ...setup.projects.flatMap((project) => project.trust === "trusted" && project.safety !== null ? [project.safety] : [])];
  const unsafe = contexts.some((context) => context.approval === "never" && context.fullAccess);
  return { tool: "codex", guardHook: false, permissionChecks: !unsafe };
}
function geminiSafeguard(setup) {
  if (geminiSettingsUnread(setup) || setup.safety.shellAutoApproved === null) return { tool: "gemini", guardHook: null, permissionChecks: null };
  const contexts = [setup.safety, ...setup.projects.flatMap((project) => project.scanned && project.trusted && project.safety !== null ? [project.safety] : [])];
  const open9 = contexts.filter((context) => context.shellAutoApproved === true);
  if (open9.some((context) => context.sandbox === false)) return { tool: "gemini", guardHook: false, permissionChecks: false };
  if (open9.some((context) => context.sandbox === null)) return { tool: "gemini", guardHook: null, permissionChecks: null };
  return { tool: "gemini", guardHook: false, permissionChecks: true };
}
function safeguardOf(tool) {
  if (tool.tool === "codex") return codexSafeguard(tool.setup);
  if (tool.tool === "gemini") return geminiSafeguard(tool.setup);
  const { setup } = tool;
  const old = seesProjectBypass(tool.highestVersion);
  if (globalSettingsUnread(setup) || old && projectSettingsUnread(setup)) return { tool: tool.tool, guardHook: null, permissionChecks: null };
  const guardHook = setup.hooks.guards.some((guard) => guard.coversShell && guard.canBlock && guardRuns(guard, setup.hooks));
  const mode = setup.settings.defaultMode.managed ?? setup.settings.defaultMode.user;
  const bypass = mode === "bypass" || old && setup.projects.some((project) => project.bypassInProject || project.bypassInLocal);
  return { tool: tool.tool, guardHook, permissionChecks: !bypass };
}
function s1(tools2) {
  const withInstructions = tools2.filter((tool) => tool.setup.globalInstructions.bytes >= MIN_GLOBAL_INSTRUCTION_BYTES).length;
  const evidence = { tools: tools2.length, withInstructions };
  return countGate(true, tools2.length, 1, evidence) ?? scored(withInstructions / tools2.length, evidence);
}
function s2(safeguards) {
  const readable = safeguards.filter((safeguard) => safeguard.permissionChecks !== null);
  const unreadTools = safeguards.length - readable.length;
  if (readable.length === 0 && unreadTools > 0) return unmeasured("unreadable", { guarded: null, tools: 0, unreadTools });
  const guarded = readable.filter((safeguard) => safeguard.guardHook === true || safeguard.permissionChecks === true).length;
  const evidence = { guarded, tools: readable.length, unreadTools };
  return countGate(true, readable.length, 1, evidence) ?? scored(guarded / readable.length, evidence);
}
var PROBLEM_COUNTERS = { danglingLink: "danglingLinks", noFrontmatter: "noFrontmatter", unparsable: "unparsable" };
function countedProblems(tools2) {
  const counted = [];
  const seen = /* @__PURE__ */ new Set();
  for (const tool of tools2) {
    for (const problem of tool.setup.problems) {
      if (problem.owner !== "user") continue;
      const at = problem.realPath ?? problem.path;
      if (seen.has(at)) continue;
      seen.add(at);
      counted.push({ tool: tool.tool, kind: problem.kind, place: problem.place });
    }
  }
  return counted;
}
function s3(problems) {
  const counts = { danglingLinks: 0, noFrontmatter: 0, unparsable: 0 };
  for (const problem of problems) counts[PROBLEM_COUNTERS[problem.kind]]++;
  return scored(problems.length, { danglingLinks: counts.danglingLinks, noFrontmatter: counts.noFrontmatter, problems: problems.length, unparsable: counts.unparsable });
}
function s5(tool) {
  const { totals: totals2 } = tool;
  const enabledServers = sameInstall(tool.setup.mcpServers.filter((server) => server.enabled), (server) => server.installKey).length;
  const failedSessions = totals2.mainSessions.filter((session) => session.mcpConnectionFailure).length;
  const evidence = { enabledServers, failedSessions, mainSessions: totals2.mainSessions.length };
  if (tool.coverage.mcpFailuresAndHooks === "unsupported") return unmeasured("unsupported", blank(evidence));
  const enablementUnknown = tool.tool === "codex" ? codexSettingsUnread(tool.setup) : tool.tool === "gemini" ? geminiSettingsUnread(tool.setup) : enablementUnread(tool.setup);
  const placesUnknown = tool.tool === "codex" ? codexSettingsUnread(tool.setup) : tool.tool === "gemini" ? geminiSettingsUnread(tool.setup) : mcpPlacesUnread(tool.setup);
  if (enablementUnknown) return unmeasured("unreadable", { ...evidence, enabledServers: null });
  if (enabledServers === 0) return placesUnknown ? unmeasured("unreadable", { ...evidence, enabledServers: null }) : unmeasured("not_applicable", evidence);
  return countGate(true, totals2.mainSessions.length, 1, evidence) ?? scored(failedSessions / totals2.mainSessions.length, evidence);
}
function mergedSetupRules(tools2) {
  const safeguards = tools2.map(safeguardOf);
  const setupProblems = countedProblems(tools2);
  const S3 = tools2.length === 0 ? unmeasured("no_data", { danglingLinks: 0, noFrontmatter: 0, problems: 0, unparsable: 0 }) : s3(setupProblems);
  return { S1: s1(tools2), S2: s2(safeguards), S3, safeguards, setupProblems };
}
function setupToolRules(tool) {
  return { S5: s5(tool) };
}

// src/core/projects.ts
function projectLookup(projects, normalizedCwds) {
  const byNormCwd = /* @__PURE__ */ new Map();
  for (const project of projects) for (const cwd of project.cwds) byNormCwd.set(cwd, project);
  const byRawCwd = /* @__PURE__ */ new Map();
  for (const [raw, normalized2] of Object.entries(normalizedCwds)) {
    const project = byNormCwd.get(normalized2);
    if (project !== void 0) byRawCwd.set(raw, project);
  }
  return (cwd) => cwd === null ? null : byRawCwd.get(cwd) ?? null;
}
var byText6 = (a, b) => a < b ? -1 : a > b ? 1 : 0;
function projectUsage(tools2, lookup) {
  const counts = /* @__PURE__ */ new Map();
  let unlinkedSessions = 0;
  for (const { tool, totals: totals2 } of tools2) {
    for (const session of totals2.mainSessions) {
      const project = lookup(session.cwd);
      if (project === null) {
        unlinkedSessions++;
        continue;
      }
      let entry = counts.get(project.normRoot);
      if (entry === void 0) counts.set(project.normRoot, entry = { project, byTool: /* @__PURE__ */ new Map() });
      entry.byTool.set(tool, (entry.byTool.get(tool) ?? 0) + 1);
    }
  }
  const projects = [...counts.keys()].sort(byText6).map((normRoot) => {
    const { project, byTool } = counts.get(normRoot);
    const sessions = {};
    let total = 0;
    for (const tool of [...byTool.keys()].sort(byText6)) {
      sessions[tool] = byTool.get(tool);
      total += byTool.get(tool);
    }
    return { project, sessions, total };
  });
  return { projects, unlinkedSessions };
}

// src/core/totals.ts
function instructionTokens(chars) {
  if (chars === null || chars.ascii + chars.other <= 0) return null;
  return chars.ascii / 4 + chars.other;
}
function toolTotals(summaries, windows, shellTools) {
  const score = new Set(windows.scoreDates);
  const collect = new Set(windows.collectDates);
  const shell = new Set(shellTools);
  const totals2 = {
    responses: 0,
    collectResponses: 0,
    tokens: { input: 0, cacheRead: 0, cacheWrite: 0, output: 0, thinking: 0 },
    humanRequests: 0,
    toolCalls: 0,
    nonShellResults: 0,
    nonShellErrors: 0,
    denied: 0,
    interruptedTurns: 0,
    lengthStops: 0,
    efforts: {},
    unknownEffort: 0,
    hookRuns: 0,
    hookFailures: 0,
    hookUnclassified: 0,
    activeDates: [],
    mainSessions: []
  };
  const efforts = /* @__PURE__ */ new Map();
  const active = /* @__PURE__ */ new Set();
  for (const summary of summaries) {
    const session = {
      sessionId: summary.sessionId,
      cwd: summary.cwd,
      autoCompactions: 0,
      subagentCalls: 0,
      mcpConnectionFailure: false,
      mcpFailedServers: [],
      instructionTokens: instructionTokens(summary.instructionChars)
    };
    const failedServers = /* @__PURE__ */ new Set();
    let sessionResponses = 0;
    for (const [date, cell] of Object.entries(summary.days)) {
      if (collect.has(date)) totals2.collectResponses += cell.responses;
      if (!score.has(date)) continue;
      totals2.responses += cell.responses;
      sessionResponses += cell.responses;
      if (cell.responses > 0) active.add(date);
      totals2.tokens.input += cell.tokens.input;
      totals2.tokens.cacheRead += cell.tokens.cacheRead;
      totals2.tokens.cacheWrite += cell.tokens.cacheWrite;
      totals2.tokens.output += cell.tokens.output;
      totals2.tokens.thinking += cell.tokens.thinking;
      if (summary.kind === "main") totals2.humanRequests += cell.humanRequests;
      for (const [name, counts] of Object.entries(cell.tools)) {
        totals2.toolCalls += counts.calls;
        totals2.denied += counts.deniedByUser + counts.deniedByHook + counts.deniedByPermission;
        if (shell.has(name)) continue;
        totals2.nonShellResults += counts.results;
        totals2.nonShellErrors += counts.errors;
      }
      totals2.interruptedTurns += cell.interruptedTurns;
      totals2.lengthStops += cell.lengthStops;
      for (const [name, count] of Object.entries(cell.efforts)) efforts.set(name, (efforts.get(name) ?? 0) + count);
      totals2.unknownEffort += cell.unknownEffort;
      for (const counts of Object.values(cell.hooks)) {
        totals2.hookRuns += counts.runs;
        totals2.hookFailures += counts.failures;
        totals2.hookUnclassified += counts.unclassifiedBlocks;
      }
      session.autoCompactions += cell.autoCompactions;
      session.subagentCalls += cell.subagentCalls;
      if (cell.mcpConnectionFailure) session.mcpConnectionFailure = true;
      for (const name of Object.keys(cell.mcpFailedServers)) failedServers.add(name);
    }
    session.mcpFailedServers = [...failedServers].sort();
    if (summary.kind === "main" && sessionResponses > 0) totals2.mainSessions.push(session);
  }
  for (const name of [...efforts.keys()].sort()) totals2.efforts[name] = efforts.get(name);
  totals2.activeDates = [...active].sort();
  totals2.mainSessions.sort((a, b) => (a.sessionId < b.sessionId ? -1 : a.sessionId > b.sessionId ? 1 : 0) || byContent(a, b));
  return totals2;
}

// src/core/evaluate.ts
var setupTools = (tools2) => tools2.filter((tool) => tool.setup !== null);
var byText7 = (a, b) => a < b ? -1 : a > b ? 1 : 0;
function webToolRules(tool) {
  const install = unmeasured("unsupported", blank(BLANK_INSTALL_EVIDENCE));
  return {
    ...usageRules(tool.totals, tool.coverage, tool.tool),
    S5: unmeasured("unsupported", { enabledServers: null, failedSessions: null, mainSessions: null }),
    F5: unmeasured("unsupported", { differingCopies: null, identicalCopies: null, skillKinds: null }),
    E5: install,
    E6: install
  };
}
var span = (dates) => ({ from: dates[0], to: dates[dates.length - 1] });
function evaluate(input) {
  const windows = makeWindows(input.clock.nowMs, input.clock.timeZone);
  const day = { today: windows.today, timeZone: input.clock.timeZone };
  const lookup = projectLookup(input.projects, input.normalizedCwds);
  const records = recordMap(input.installs);
  const all = [...input.tools].sort((a, b) => byText7(a.tool, b.tool)).map((tool) => ({ input: tool, totals: toolTotals(tool.summaries, windows, tool.shellTools) }));
  const scored2 = all.filter((tool) => tool.totals.responses > 0);
  const withSetup = scored2.filter((tool) => tool.input.setup !== null);
  const setups = withSetup.map(({ input: tool, totals: totals2 }) => {
    const common = { totals: totals2, coverage: tool.coverage, highestVersion: highestMainVersion(tool.summaries) };
    if (tool.tool === "codex") return { ...common, tool: "codex", setup: tool.setup };
    if (tool.tool === "gemini") return { ...common, tool: "gemini", setup: tool.setup };
    return { ...common, tool: "claude-code", setup: tool.setup };
  });
  const usage2 = projectUsage(setups, lookup);
  const judged = withSetup.map((tool, index) => {
    const setup = setups[index];
    const { summaries } = tool.input;
    const base = { day, windows, records };
    const skills = judgeSkills(setup, { ...base, used: usedSkillNames(summaries, windows), listings: sessionListings(summaries, "skill", input.normalizedCwds, lookup), complete: tool.input.complete.skills });
    const servers = judgeServers(setup, { ...base, used: calledMcpNames(summaries, windows), listings: sessionListings(summaries, "mcp", input.normalizedCwds, lookup), complete: tool.input.complete.mcp });
    const candidates = candidatesOf(setup, skills, servers, day, input.self);
    const measured2 = {
      tool: setup.tool,
      responses: setup.totals.responses,
      rules: { ...usageRules(setup.totals, setup.coverage, setup.tool), ...setupToolRules(setup), ...fitToolRules(setup), E5: skills.measurement, E6: servers.measurement },
      candidates
    };
    return { tool: setup.tool, skills: skills.bundles, servers: servers.servers, candidates, measured: measured2 };
  });
  const web = scored2.filter((tool) => tool.input.setup === null).map(({ input: tool, totals: totals2 }) => ({ tool: tool.tool, responses: totals2.responses, rules: webToolRules({ tool: tool.tool, totals: totals2, coverage: tool.coverage }), candidates: [] }));
  const usages = scored2.map(({ input: tool, totals: totals2 }) => ({ tool: tool.tool, totals: totals2, coverage: tool.coverage }));
  const { S1, S2, S3, safeguards, setupProblems } = mergedSetupRules(setups);
  const { F3, F4, F6, missingInstructions, worstOverlap } = mergedFitRules(setups, usage2, input.projects);
  const measuredTools = [...judged.map((tool) => tool.measured), ...web].sort((a, b) => byText7(a.tool, b.tool));
  const board = scoreboard({ merged: { S1, S2, S3, F3, F4, F6, ...intensityRules(usages, usage2) }, tools: measuredTools });
  const humanRequests = scored2.reduce((sum2, tool) => sum2 + tool.totals.humanRequests, 0);
  const activeDays2 = new Set(scored2.flatMap((tool) => tool.totals.activeDates)).size;
  const judgedByTool = new Map(judged.map((tool) => [tool.tool, tool]));
  return {
    rulesVersion: RULES_VERSION,
    windows: { today: windows.today, score: span(windows.scoreDates), collect: span(windows.collectDates) },
    tools: all.map((tool) => {
      const own = judgedByTool.get(tool.input.tool);
      return { tool: tool.input.tool, scored: tool.totals.responses > 0, inCalendar: tool.totals.collectResponses > 0, totals: tool.totals, skills: own?.skills ?? [], servers: own?.servers ?? [] };
    }),
    score: overall(board.axes, humanRequests, activeDays2, scored2.length > 0 && withSetup.length === 0),
    axes: board.axes,
    findings: board.findings,
    candidates: judged.flatMap((tool) => tool.candidates),
    safeguards,
    missingInstructions,
    worstOverlap,
    setupProblems,
    projects: usage2
  };
}

// src/core/copy/common.ts
var TOOL_NAMES = {
  "claude-code": { en: "Claude Code", ko: "Claude Code" },
  codex: { en: "Codex", ko: "Codex" },
  gemini: { en: "Gemini CLI", ko: "Gemini CLI" },
  "web-chatgpt": { en: "ChatGPT", ko: "ChatGPT" },
  "web-claude": { en: "Claude.ai", ko: "Claude.ai" }
};
var AXIS_NAMES = {
  setup: { en: "Setup", ko: "\uC14B\uD305" },
  efficiency: { en: "Efficiency", ko: "\uD6A8\uC728" },
  fit: { en: "Fit", ko: "\uC0C1\uD669 \uC801\uD569" },
  intensity: { en: "Intensity", ko: "\uAC15\uB3C4" }
};
var SUMMARY_COPY = {
  en: { credentials: "{count} {count:place in your settings has|places in your settings have} an API key or token written as it is. See where in the report page and move {count:it|them} into environment variables.", best: "{name} {value}", gain: "{axis} up to +{gain}", gainBelow: "{axis} up to +{gain} \xB7 now {now}, rises only below {start}", gainAbove: "{axis} up to +{gain} \xB7 now {now}, rises only above {start}", gainBelowTools: "{axis} up to +{gain} \xB7 now {now}, each rises only below {start}", gainAboveTools: "{axis} up to +{gain} \xB7 now {now}, each rises only above {start}", toolJoin: " and ", unmeasured: "{candidates} to clean up \xB7 share not measured", otherTools: "{candidates} to clean up \xB7 share for {tools} not measured", candidates: "{candidates} to clean up" },
  ko: { credentials: "\uC124\uC815 {count}\uACF3\uC5D0 API \uD0A4\uB098 \uD1A0\uD070\uC774 \uADF8\uB300\uB85C \uC801\uD600 \uC788\uC2B5\uB2C8\uB2E4. \uACB0\uACFC \uD654\uBA74\uC5D0\uC11C \uC704\uCE58\uB97C \uBCF4\uACE0 \uD658\uACBD \uBCC0\uC218\uB85C \uC62E\uAE30\uC138\uC694.", best: "{name} {value}", gain: "{axis} \uCD5C\uB300 +{gain}", gainBelow: "{axis} \uCD5C\uB300 +{gain} \xB7 \uC9C0\uAE08 {now}, {start} \uC544\uB798\uB85C \uC904\uC5EC\uC57C \uC624\uB974\uAE30 \uC2DC\uC791", gainAbove: "{axis} \uCD5C\uB300 +{gain} \xB7 \uC9C0\uAE08 {now}, {start} \uC704\uB85C \uC62C\uB824\uC57C \uC624\uB974\uAE30 \uC2DC\uC791", gainBelowTools: "{axis} \uCD5C\uB300 +{gain} \xB7 \uC9C0\uAE08 {now}, \uB3C4\uAD6C\uB9C8\uB2E4 {start} \uC544\uB798\uB85C \uC904\uC5EC\uC57C \uC624\uB974\uAE30 \uC2DC\uC791", gainAboveTools: "{axis} \uCD5C\uB300 +{gain} \xB7 \uC9C0\uAE08 {now}, \uB3C4\uAD6C\uB9C8\uB2E4 {start} \uC704\uB85C \uC62C\uB824\uC57C \uC624\uB974\uAE30 \uC2DC\uC791", toolJoin: "\xB7", unmeasured: "\uC815\uB9AC\uD560 \uAC83 {candidates}\uAC1C \xB7 \uBE44\uC728\uC740 \uC7B4 \uC218 \uC5C6\uC74C", otherTools: "\uC815\uB9AC\uD560 \uAC83 {candidates}\uAC1C \xB7 {tools}\uC758 \uBE44\uC728\uC740 \uC7B4 \uC218 \uC5C6\uC74C", candidates: "\uC815\uB9AC\uD560 \uAC83 {candidates}\uAC1C" }
};
var REASON_COPY = {
  unsupported: {
    en: { word: "Not recorded", text: "This tool or record format does not record what this rule needs." },
    ko: { word: "\uAE30\uB85D\uB418\uC9C0 \uC54A\uC74C", text: "\uC774 \uB3C4\uAD6C\uB098 \uAE30\uB85D \uD615\uC2DD\uC740 \uC774 \uADDC\uCE59\uC774 \uBCF4\uB294 \uAC83\uC744 \uB0A8\uAE30\uC9C0 \uC54A\uC2B5\uB2C8\uB2E4." }
  },
  unreadable: {
    en: { word: "Could not read", text: "A file this rule needs could not be read. See the notices as well." },
    ko: { word: "\uC77D\uC9C0 \uBABB\uD568", text: "\uC774 \uADDC\uCE59\uC5D0 \uD544\uC694\uD55C \uD30C\uC77C\uC744 \uC77D\uC9C0 \uBABB\uD588\uC2B5\uB2C8\uB2E4. \uC54C\uB9BC\uB3C4 \uD568\uAED8 \uBCF4\uC138\uC694." }
  },
  not_applicable: {
    en: { word: "Not applicable", text: "There is nothing for this rule to look at." },
    ko: { word: "\uD574\uB2F9 \uC5C6\uC74C", text: "\uC774 \uADDC\uCE59\uC774 \uBCFC \uAC83\uC774 \uC5C6\uC2B5\uB2C8\uB2E4." }
  },
  incomplete: {
    en: { word: "Incomplete records", text: "The records could not all be read, so this was not measured." },
    ko: { word: "\uAE30\uB85D\uC774 \uBE60\uC9D0", text: "\uAE30\uB85D\uC744 \uBE60\uC9D0\uC5C6\uC774 \uC77D\uC9C0 \uBABB\uD574 \uC7AC\uC9C0 \uC54A\uC558\uC2B5\uB2C8\uB2E4." }
  },
  no_data: {
    en: { word: "No records", text: "There is nothing in the records to measure yet." },
    ko: { word: "\uAE30\uB85D \uC5C6\uC74C", text: "\uC7B4 \uAE30\uB85D\uC774 \uC544\uC9C1 \uC5C6\uC2B5\uB2C8\uB2E4." }
  },
  too_little: {
    en: { word: "Too few records", text: "Not enough records have built up to measure this." },
    ko: { word: "\uAE30\uB85D\uC774 \uC801\uC74C", text: "\uC7B4 \uB9CC\uD07C \uAE30\uB85D\uC774 \uC313\uC774\uC9C0 \uC54A\uC558\uC2B5\uB2C8\uB2E4." }
  },
  watching: {
    en: { word: "Still watching", text: "Still watching before judging." },
    ko: { word: "\uC9C0\uCF1C\uBCF4\uB294 \uC911", text: "\uC544\uC9C1 \uC9C0\uCF1C\uBCF4\uB294 \uC911\uC785\uB2C8\uB2E4." }
  }
};
var TOOL_LINE = {
  en: { measured: "{tool}: {value} \xB7 {evidence}", unmeasured: "{tool}: not measured ({reason}) \xB7 {evidence}" },
  ko: { measured: "{tool}: {value} \xB7 {evidence}", unmeasured: "{tool}: \uC7B4 \uC218 \uC5C6\uC74C({reason}) \xB7 {evidence}" }
};
var OTHER_TOOL_COPY = {
  too_little: {
    en: "Only {judgeable} {judgeable:installation|installations} in {tool} can be assessed for use, so its share was not calculated, but {candidates} can be cleaned up.",
    ko: "{tool}\uB294 \uC4F0\uB294\uC9C0 \uAC00\uB9B4 \uC218 \uC788\uB294 \uAC83\uC774 {judgeable}\uAC1C\uBFD0\uC774\uC5B4\uC11C \uBE44\uC728\uC744 \uB0B4\uC9C0 \uC54A\uC558\uC9C0\uB9CC \uC815\uB9AC\uD560 \uC218 \uC788\uB294 \uAC83\uC774 {candidates}\uAC1C \uC788\uC2B5\uB2C8\uB2E4."
  },
  watching: {
    en: "Some installations in {tool} are still being observed, so its share was not calculated, but {candidates} of those confirmed unused can be cleaned up now.",
    ko: "{tool}\uB294 \uC544\uC9C1 \uC9C0\uCF1C\uBCF4\uB294 \uC911\uC778 \uAC83\uC774 \uC788\uC5B4 \uBE44\uC728\uC744 \uB0B4\uC9C0 \uC54A\uC558\uC9C0\uB9CC \uC548 \uC4F0\uB294 \uAC83\uC73C\uB85C \uD655\uC778\uB41C \uAC83 \uAC00\uC6B4\uB370 {candidates}\uAC1C\uB294 \uC9C0\uAE08 \uC815\uB9AC\uD560 \uC218 \uC788\uC2B5\uB2C8\uB2E4."
  }
};
var SAFEGUARD_COPY = {
  en: {
    line: "{tool}: {condition}",
    hook: "a PreToolUse hook that can block covers shell commands",
    permissions: "the default mode does not bypass permissions",
    both: "the default mode does not bypass permissions, and a confirming hook covers shell commands too",
    none: "no safeguard (permissions are bypassed and no confirming hook covers shell commands)",
    codexGuarded: "no place combines no approval with full sandbox access",
    codexNone: "no safeguard (a place combines no approval with full sandbox access)",
    geminiGuarded: "no place lets shell commands run without asking while the sandbox is off",
    geminiNone: "no safeguard (a place lets shell commands run without asking while the sandbox is off)",
    unknown: "left out, because a settings file that decides the safeguard could not be read"
  },
  ko: {
    line: "{tool}: {condition}",
    hook: "\uC178 \uBA85\uB839\uC744 \uB36E\uB294 \uB3C4\uAD6C \uC2E4\uD589 \uC804 \uD655\uC778 \uD6C5\uC774 \uC788\uC74C",
    permissions: "\uAE30\uBCF8 \uBAA8\uB4DC\uAC00 \uAD8C\uD55C \uC6B0\uD68C\uAC00 \uC544\uB2D8",
    both: "\uAE30\uBCF8 \uBAA8\uB4DC\uAC00 \uAD8C\uD55C \uC6B0\uD68C\uAC00 \uC544\uB2C8\uACE0 \uC178 \uBA85\uB839\uC744 \uB36E\uB294 \uD655\uC778 \uD6C5\uB3C4 \uC788\uC74C",
    none: "\uC548\uC804\uC7A5\uCE58 \uC5C6\uC74C(\uAD8C\uD55C \uC6B0\uD68C \uBAA8\uB4DC\uC774\uACE0 \uC178 \uBA85\uB839\uC744 \uB36E\uB294 \uD655\uC778 \uD6C5\uC774 \uC5C6\uC74C)",
    codexGuarded: "\uC2B9\uC778 \uC5C6\uC74C\uACFC \uC0CC\uB4DC\uBC15\uC2A4 \uC804\uBA74 \uD574\uC81C\uB97C \uD568\uAED8 \uC4F0\uB294 \uACF3\uC774 \uC5C6\uC74C",
    codexNone: "\uC548\uC804\uC7A5\uCE58 \uC5C6\uC74C(\uC2B9\uC778 \uC5C6\uC74C\uACFC \uC0CC\uB4DC\uBC15\uC2A4 \uC804\uBA74 \uD574\uC81C\uB97C \uD568\uAED8 \uC4F0\uB294 \uACF3\uC774 \uC788\uC74C)",
    geminiGuarded: "\uC178 \uBA85\uB839\uC744 \uBB3B\uC9C0 \uC54A\uACE0 \uC2E4\uD589\uD558\uAC8C \uB450\uBA74\uC11C \uC0CC\uB4DC\uBC15\uC2A4\uB97C \uB048 \uACF3\uC774 \uC5C6\uC74C",
    geminiNone: "\uC548\uC804\uC7A5\uCE58 \uC5C6\uC74C(\uC178 \uBA85\uB839\uC744 \uBB3B\uC9C0 \uC54A\uACE0 \uC2E4\uD589\uD558\uAC8C \uB450\uBA74\uC11C \uC0CC\uB4DC\uBC15\uC2A4\uB97C \uB048 \uACF3\uC774 \uC788\uC74C)",
    unknown: "\uC548\uC804\uC7A5\uCE58\uB97C \uC815\uD558\uB294 \uC124\uC815 \uD30C\uC77C\uC744 \uC77D\uC9C0 \uBABB\uD574 \uBE7C\uACE0 \uC7C0\uC74C"
  }
};
var PROXY_LINE = {
  en: "{tool}: the records do not show this directly, so the value is approximate.",
  ko: "{tool}: \uAE30\uB85D\uC774 \uADF8\uB300\uB85C \uB0A8\uAE30\uC9C0 \uC54A\uB294 \uAC12\uC774\uB77C \uAC00\uAE4C\uC6B4 \uAC12\uC73C\uB85C \uC7C0\uC2B5\uB2C8\uB2E4."
};
var TOOL_CALL_GRAIN = {
  en: "Tool calls are counted at a different grain in each tool. In {models} one call the model makes is one, and in Codex one action that actually ran is one.",
  ko: "\uB3C4\uAD6C \uD638\uCD9C\uC744 \uC138\uB294 \uAD75\uAE30\uAC00 \uB3C4\uAD6C\uB9C8\uB2E4 \uB2E4\uB985\uB2C8\uB2E4. {models}\uB294 \uBAA8\uB378\uC774 \uB0B8 \uD638\uCD9C \uD558\uB098\uAC00, Codex\uB294 \uC2E4\uC81C\uB85C \uC2E4\uD589\uB41C \uC791\uC5C5 \uD558\uB098\uAC00 \uD558\uB098\uC785\uB2C8\uB2E4."
};
var TOOL_CALL_GRAIN_JOIN = { en: " and ", ko: "\uC640 " };
var UNJUDGED_COPY = {
  en: {
    intro: "Servers left out of the judgment that have no record of being called. They are not suggested for turning off.",
    line: "{tool}: {why} ({count})",
    why: {
      no_definition: "definition not on this PC or not fully read",
      plugin_unread: "plugin configuration or MCP definitions could not be read",
      not_established: "still being watched",
      observation_incomplete: "records could not all be read"
    },
    deny: 'To block a claude.ai connector that Claude Code loads itself, add { "serverName": "<name>" } to the deniedMcpServers list in your user settings (~/.claude/settings.json). Connectors that the desktop app passes in directly are not blocked this way. Disconnect those at claude.ai/customize/connectors.'
  },
  ko: {
    intro: "\uD310\uC815\uC5D0\uC11C \uBE80 \uC11C\uBC84 \uAC00\uC6B4\uB370 \uBD80\uB978 \uAE30\uB85D\uC774 \uC5C6\uB294 \uAC83\uC785\uB2C8\uB2E4. \uB044\uC790\uACE0 \uD558\uC9C0 \uC54A\uC2B5\uB2C8\uB2E4.",
    line: "{tool}: {why} {count}\uAC1C",
    why: {
      no_definition: "\uC815\uC758\uAC00 \uC774 PC\uC5D0 \uC5C6\uAC70\uB098 \uB2E4 \uC77D\uD788\uC9C0 \uC54A\uC74C",
      plugin_unread: "\uD50C\uB7EC\uADF8\uC778 \uAD6C\uC131\uC774\uB098 MCP \uC815\uC758\uB97C \uC77D\uC9C0 \uBABB\uD568",
      not_established: "\uC544\uC9C1 \uC9C0\uCF1C\uBCF4\uB294 \uC911",
      observation_incomplete: "\uAE30\uB85D\uC744 \uBE60\uC9D0\uC5C6\uC774 \uC77D\uC9C0 \uBABB\uD568"
    },
    deny: 'Claude Code\uAC00 \uC9C1\uC811 \uAC00\uC838\uC624\uB294 claude.ai \uC5F0\uACB0\uC744 \uB9C9\uC73C\uB824\uBA74 \uC0AC\uC6A9\uC790 \uC124\uC815(~/.claude/settings.json)\uC758 deniedMcpServers \uBAA9\uB85D\uC5D0 { "serverName": "<\uC774\uB984>" }\uC744 \uB354\uD558\uC138\uC694. \uB370\uC2A4\uD06C\uD1B1 \uC571\uC774 \uC9C1\uC811 \uB118\uAE30\uB294 \uC5F0\uACB0\uC740 \uC774\uB807\uAC8C \uB9C9\uD788\uC9C0 \uC54A\uC2B5\uB2C8\uB2E4. \uADF8\uB7F0 \uC5F0\uACB0\uC740 claude.ai/customize/connectors\uC5D0\uC11C \uB04A\uC73C\uC138\uC694.'
  }
};

// src/core/copy/rules-efficiency.ts
var WATCHING = {
  en: { word: "Still watching", text: "Some are still being watched, so the unused share was not given." },
  ko: { word: "\uC9C0\uCF1C\uBCF4\uB294 \uC911", text: "\uC544\uC9C1 \uC9C0\uCF1C\uBCF4\uB294 \uC911\uC778 \uAC83\uC774 \uC788\uC5B4 \uC548 \uC4F0\uB294 \uBE44\uC728\uC740 \uB0B4\uC9C0 \uC54A\uC558\uC2B5\uB2C8\uB2E4." }
};
var WATCHING_REPAIR = {
  en: "Some are still being watched, so the unused share was not given. {candidates} of the ones confirmed unused can be cleaned up now.",
  ko: "\uC544\uC9C1 \uC9C0\uCF1C\uBCF4\uB294 \uC911\uC778 \uAC83\uC774 \uC788\uC5B4 \uC548 \uC4F0\uB294 \uBE44\uC728\uC740 \uB0B4\uC9C0 \uC54A\uC558\uC2B5\uB2C8\uB2E4. \uC548 \uC4F0\uB294 \uAC83\uC73C\uB85C \uD655\uC778\uB41C \uAC83 \uAC00\uC6B4\uB370 {candidates}\uAC1C\uB294 \uC9C0\uAE08 \uC815\uB9AC\uD560 \uC218 \uC788\uC2B5\uB2C8\uB2E4."
};
var FEW = { en: "Few eligible for assessment", ko: "\uAC00\uB9B4 \uC218 \uC788\uB294 \uAC83\uC774 \uC801\uC74C" };
var EFFICIENCY_COPY = {
  E1: {
    en: {
      name: "Cache hits",
      good: "Reuses cached context instead of recomputing it",
      why: "Cached conversation prefixes are reused rather than processed again. This rule measures the share of input read from that cache.",
      fix: "Keep the start of sessions stable",
      problem: "{value} of input was read from the cache.",
      prescription: "Keep one task in one session, and avoid turning MCP servers on and off in the middle of a session. After a long pause the cache expires and is built again.",
      method: "Share of input read from the cache. For Claude Code, the whole input is plain input plus cache reads plus cache writes.",
      evidence: "Cache reads {cacheRead} \xB7 input {input} \xB7 cache writes {cacheWrite} (tokens)",
      unit: "%",
      reasons: { no_data: { text: "No input tokens were recorded in the scoring window." } }
    },
    ko: {
      name: "\uCE90\uC2DC \uC801\uC911",
      good: "\uAC19\uC740 \uB0B4\uC6A9\uC744 \uB2E4\uC2DC \uACC4\uC0B0\uC2DC\uD0A4\uC9C0 \uC54A\uC74C",
      why: "\uCE90\uC2DC\uC5D0\uC11C \uC77D\uC740 \uB300\uD654 \uC55E\uBD80\uBD84\uC740 \uB2E4\uC2DC \uACC4\uC0B0\uD558\uC9C0 \uC54A\uACE0 \uC7AC\uC0AC\uC6A9\uD569\uB2C8\uB2E4. \uC774 \uD56D\uBAA9\uC740 \uC785\uB825 \uAC00\uC6B4\uB370 \uADF8\uB807\uAC8C \uCE90\uC2DC\uC5D0\uC11C \uC77D\uC740 \uBAAB\uC744 \uBD05\uB2C8\uB2E4.",
      fix: "\uC138\uC158\uC758 \uC55E\uBD80\uBD84\uC744 \uC790\uC8FC \uBC14\uAFB8\uC9C0 \uC54A\uAE30",
      problem: "\uC785\uB825 \uAC00\uC6B4\uB370 \uCE90\uC2DC\uC5D0\uC11C \uC77D\uC740 \uBAAB\uC774 {value}\uC785\uB2C8\uB2E4.",
      prescription: "\uD55C \uAC00\uC9C0 \uC77C\uC740 \uD55C \uC138\uC158\uC5D0\uC11C \uC774\uC5B4 \uD558\uACE0, \uC138\uC158 \uB3C4\uC911\uC5D0 MCP \uC11C\uBC84\uB97C \uCF1C\uACE0 \uB044\uB294 \uC77C\uC744 \uC904\uC774\uC138\uC694. \uC624\uB798 \uC26C\uBA74 \uCE90\uC2DC\uAC00 \uB9CC\uB8CC\uB418\uC5B4 \uB2E4\uC2DC \uB9CC\uB4E4\uC5B4\uC9D1\uB2C8\uB2E4.",
      method: "\uC785\uB825 \uAC00\uC6B4\uB370 \uCE90\uC2DC\uC5D0\uC11C \uC77D\uC740 \uBAAB\uC785\uB2C8\uB2E4. Claude Code\uB294 \uC785\uB825, \uCE90\uC2DC \uC77D\uAE30, \uCE90\uC2DC \uC4F0\uAE30\uB97C \uB354\uD55C \uAC83\uC774 \uC804\uCCB4 \uC785\uB825\uC785\uB2C8\uB2E4.",
      evidence: "\uCE90\uC2DC \uC77D\uAE30 {cacheRead} \xB7 \uC785\uB825 {input} \xB7 \uCE90\uC2DC \uC4F0\uAE30 {cacheWrite} (\uD1A0\uD070)",
      unit: "%",
      reasons: { no_data: { text: "\uC810\uC218 \uAD6C\uAC04\uC5D0 \uC785\uB825 \uD1A0\uD070\uC774 \uAE30\uB85D\uB418\uC9C0 \uC54A\uC558\uC2B5\uB2C8\uB2E4." } }
    }
  },
  E2: {
    en: {
      name: "Tool errors",
      good: "Tools rarely end in errors",
      why: "A tool call that ends in an error has to be retried or worked around, which spends turns and tokens. Shell commands are left out, because a non-zero exit is usually the result of the work, such as a failing test.",
      fix: "Reduce tool errors",
      problem: "{value} of tool results ended in an error.",
      prescription: "Look at which tools fail most often. Reading a file that has moved, editing text that has already changed, and an MCP server that does not answer are examples. If the same cause keeps coming back, such as an old path in your instructions, fix that cause.",
      method: "Share of tool results that ended in an error. Shell commands, and results that were denied or interrupted, are left out of both counts.",
      evidence: "Errors {errors} \xB7 tool results {results}",
      unit: "%",
      reasons: {
        no_data: { text: "There were no tool results to count in the scoring window." },
        too_little: { text: "Fewer than 50 tool results, so this was not measured." }
      }
    },
    ko: {
      name: "\uB3C4\uAD6C \uC624\uB958",
      good: "\uB3C4\uAD6C\uAC00 \uC624\uB958\uB85C \uB05D\uB098\uB294 \uC77C\uC774 \uB4DC\uBB3E",
      why: "\uC624\uB958\uB85C \uB05D\uB09C \uB3C4\uAD6C \uD638\uCD9C\uC740 \uB2E4\uC2DC \uD558\uAC70\uB098 \uB3CC\uC544\uAC00\uC57C \uD574\uC11C \uD134\uACFC \uD1A0\uD070\uC774 \uB4ED\uB2C8\uB2E4. \uC178 \uBA85\uB839\uC740 \uBE8D\uB2C8\uB2E4. 0\uC774 \uC544\uB2CC \uAC12\uC73C\uB85C \uB05D\uB098\uB294 \uAC83\uC740 \uC2E4\uD328\uD55C \uC2DC\uD5D8\uCC98\uB7FC \uB300\uAC1C \uC77C\uC758 \uACB0\uACFC\uC774\uAE30 \uB54C\uBB38\uC785\uB2C8\uB2E4.",
      fix: "\uB3C4\uAD6C \uC624\uB958 \uC904\uC774\uAE30",
      problem: "\uB3C4\uAD6C \uACB0\uACFC \uAC00\uC6B4\uB370 {value}\uAC00 \uC624\uB958\uB85C \uB05D\uB0AC\uC2B5\uB2C8\uB2E4.",
      prescription: "\uC5B4\uB290 \uB3C4\uAD6C\uAC00 \uC790\uC8FC \uC2E4\uD328\uD558\uB294\uC9C0 \uBCF4\uC138\uC694. \uC62E\uACA8\uC9C4 \uD30C\uC77C\uC744 \uC77D\uAC70\uB098, \uC774\uBBF8 \uBC14\uB010 \uAE00\uC744 \uACE0\uCE58\uB824 \uD558\uAC70\uB098, MCP \uC11C\uBC84\uAC00 \uC751\uB2F5\uD558\uC9C0 \uC54A\uB294 \uAC83\uC774 \uADF8\uB7F0 \uC608\uC785\uB2C8\uB2E4. \uC9C0\uCE68\uC5D0 \uB0A8\uC740 \uC61B \uACBD\uB85C\uCC98\uB7FC \uAC19\uC740 \uAE4C\uB2ED\uC774 \uB418\uD480\uC774\uB418\uBA74 \uADF8 \uAE4C\uB2ED\uC744 \uACE0\uCE58\uC138\uC694.",
      method: "\uB3C4\uAD6C \uACB0\uACFC \uAC00\uC6B4\uB370 \uC624\uB958\uB85C \uB05D\uB09C \uBAAB\uC785\uB2C8\uB2E4. \uC178 \uBA85\uB839\uACFC, \uAC70\uC808\uB418\uAC70\uB098 \uB04A\uACA8\uC11C \uB05D\uB09C \uACB0\uACFC\uB294 \uB450 \uC218\uC5D0\uC11C \uBAA8\uB450 \uBE8D\uB2C8\uB2E4.",
      evidence: "\uC624\uB958 {errors} \xB7 \uB3C4\uAD6C \uACB0\uACFC {results}",
      unit: "%",
      reasons: {
        no_data: { text: "\uC810\uC218 \uAD6C\uAC04\uC5D0 \uC140 \uB3C4\uAD6C \uACB0\uACFC\uAC00 \uC5C6\uC2B5\uB2C8\uB2E4." },
        too_little: { text: "\uB3C4\uAD6C \uACB0\uACFC\uAC00 50\uAC1C\uC5D0 \uBABB \uBBF8\uCCD0 \uC7AC\uC9C0 \uC54A\uC558\uC2B5\uB2C8\uB2E4." }
      }
    }
  },
  E3: {
    en: {
      name: "Context overflow",
      good: "Rarely needs automatic compaction",
      why: "When a conversation fills the context window, Claude Code compacts it automatically and earlier details are shortened.",
      fix: "Split long sessions",
      problem: "Automatic compaction averaged {value}.",
      prescription: "Run /compact yourself before the context fills, or start a new conversation with /clear when the task changes. Hand large file reads and long searches to a subagent, which works in its own context window.",
      method: "Automatic compactions in main sessions divided by main sessions with responses in the scoring window.",
      evidence: "Automatic compactions {autoCompactions} \xB7 main sessions {mainSessions}",
      unit: "{value:compaction|compactions} per session",
      reasons: {
        no_data: { text: "No main session had responses in the scoring window." },
        too_little: { text: "Fewer than 3 main sessions with responses, so this was not measured." }
      }
    },
    ko: {
      name: "\uB300\uD654 \uB118\uCE68",
      good: "\uC790\uB3D9 \uC555\uCD95\uC774 \uB4DC\uBB3E",
      why: "\uB300\uD654\uAC00 \uB300\uD654 \uCC3D\uC744 \uCC44\uC6B0\uBA74 Claude Code\uAC00 \uC790\uB3D9\uC73C\uB85C \uC555\uCD95\uD558\uACE0 \uC55E\uC758 \uC790\uC138\uD55C \uB0B4\uC6A9\uC774 \uC904\uC5B4\uB4ED\uB2C8\uB2E4.",
      fix: "\uAE34 \uC138\uC158 \uB098\uB204\uAE30",
      problem: "\uC8FC \uC138\uC158\uC758 \uC790\uB3D9 \uC555\uCD95\uC774 \uD3C9\uADE0 {value}\uC785\uB2C8\uB2E4.",
      prescription: "\uB300\uD654 \uCC3D\uC774 \uCC28\uAE30 \uC804\uC5D0 /compact\uB85C \uC9C1\uC811 \uC904\uC774\uAC70\uB098, \uC77C\uC774 \uBC14\uB00C\uBA74 /clear\uB85C \uC0C8 \uB300\uD654\uB97C \uC2DC\uC791\uD558\uC138\uC694. \uD070 \uD30C\uC77C \uC77D\uAE30\uB098 \uAE34 \uC870\uC0AC\uB294 \uC790\uAE30 \uB300\uD654 \uCC3D\uC5D0\uC11C \uC77C\uD558\uB294 \uD558\uC704 \uC5D0\uC774\uC804\uD2B8\uC5D0 \uB9E1\uAE30\uC138\uC694.",
      method: "\uC8FC \uC138\uC158\uC758 \uC790\uB3D9 \uC555\uCD95 \uD69F\uC218\uB97C \uC810\uC218 \uAD6C\uAC04\uC5D0 \uC751\uB2F5\uC774 \uC788\uB294 \uC8FC \uC138\uC158 \uC218\uB85C \uB098\uB208 \uAC12\uC785\uB2C8\uB2E4.",
      evidence: "\uC790\uB3D9 \uC555\uCD95 {autoCompactions} \xB7 \uC8FC \uC138\uC158 {mainSessions}",
      unit: "\uD68C/\uC138\uC158",
      reasons: {
        no_data: { text: "\uC810\uC218 \uAD6C\uAC04\uC5D0 \uC751\uB2F5\uC774 \uC788\uB294 \uC8FC \uC138\uC158\uC774 \uC5C6\uC2B5\uB2C8\uB2E4." },
        too_little: { text: "\uC751\uB2F5\uC774 \uC788\uB294 \uC8FC \uC138\uC158\uC774 3\uAC1C\uC5D0 \uBABB \uBBF8\uCCD0 \uC7AC\uC9C0 \uC54A\uC558\uC2B5\uB2C8\uB2E4." }
      }
    }
  },
  E4: {
    en: {
      name: "Always-loaded instructions",
      good: "Keeps always-loaded instructions light",
      why: "Instructions load at the start of every session and take room in the context window for the whole session. Lighter instructions leave that much more room for the work.",
      fix: "Trim always-loaded instructions",
      problem: "Instructions loaded in a main session come to {value} at the median.",
      prescription: "Move instructions you do not need every time into .claude/rules/ files with paths frontmatter, so they load when Claude works on matching files. Importing a file with @ from an always-loaded CLAUDE.md does not make it load on demand.",
      method: "Median size of the instructions loaded in main sessions. One token is estimated per 4 ASCII characters and per other character, such as Korean. Sessions whose instruction size was not left in the records are not in the sample.",
      evidence: "Sessions in the sample {sampledSessions} \xB7 sessions whose instruction size was not recorded {skippedSessions}",
      unit: "{value:token|tokens} (est.)",
      reasons: {
        no_data: {
          word: "Size not recorded",
          text: "The instruction size was not found in the records. Some ways of running Claude Code do not record the input sent at the start of a session, including instructions."
        }
      }
    },
    ko: {
      name: "\uB9E4\uBC88 \uC2E4\uB9AC\uB294 \uC9C0\uCE68",
      good: "\uB9E4\uBC88 \uC2E4\uB9AC\uB294 \uC9C0\uCE68\uC744 \uAC00\uBCCD\uAC8C \uB460",
      why: "\uC9C0\uCE68\uC740 \uC138\uC158\uB9C8\uB2E4 \uCC98\uC74C\uC5D0 \uC2E4\uB824 \uC138\uC158 \uB0B4\uB0B4 \uB300\uD654 \uCC3D\uC758 \uC790\uB9AC\uB97C \uCC28\uC9C0\uD569\uB2C8\uB2E4. \uC9C0\uCE68\uC774 \uAC00\uBCBC\uC6B0\uBA74 \uC77C\uC5D0 \uC4F8 \uC790\uB9AC\uAC00 \uADF8\uB9CC\uD07C \uB0A8\uC2B5\uB2C8\uB2E4.",
      fix: "\uB9E4\uBC88 \uC2E4\uB9AC\uB294 \uC9C0\uCE68 \uC904\uC774\uAE30",
      problem: "\uC8FC \uC138\uC158\uC5D0 \uC2E4\uB9B0 \uC9C0\uCE68\uC774 \uAC00\uC6B4\uB370 \uAC12\uC73C\uB85C {value}\uC785\uB2C8\uB2E4.",
      prescription: "\uB298 \uD544\uC694\uD558\uC9C0\uB294 \uC54A\uC740 \uC9C0\uCE68\uC740 .claude/rules/ \uC544\uB798\uC758 \uADDC\uCE59 \uD30C\uC77C\uB85C \uC62E\uAE30\uACE0 \uBA38\uB9AC\uB9D0\uC758 paths\uB85C \uD574\uB2F9 \uD30C\uC77C\uC744 \uB2E4\uB8F0 \uB54C \uC2E4\uB9AC\uAC8C \uD558\uC138\uC694. \uB9E4\uBC88 \uC2E4\uB9AC\uB294 CLAUDE.md\uC5D0\uC11C @\uB85C \uAC00\uC838\uC624\uB294 \uAC83\uB9CC\uC73C\uB85C\uB294 \uD544\uC694\uD560 \uB54C \uC2E4\uB9AC\uB294 \uADDC\uCE59\uC774 \uB418\uC9C0 \uC54A\uC2B5\uB2C8\uB2E4.",
      method: "\uC8FC \uC138\uC158\uC5D0 \uC2E4\uB9B0 \uC9C0\uCE68\uC758 \uC5B4\uB9BC \uD1A0\uD070 \uC218\uC758 \uAC00\uC6B4\uB370 \uAC12\uC785\uB2C8\uB2E4. ASCII \uAE00\uC790\uB294 4\uAE00\uC790\uB97C, \uD55C\uAE00 \uAC19\uC740 \uADF8 \uBC16\uC758 \uAE00\uC790\uB294 1\uAE00\uC790\uB97C 1\uD1A0\uD070\uC73C\uB85C \uC5B4\uB9BC\uD569\uB2C8\uB2E4. \uC9C0\uCE68 \uD06C\uAE30\uAC00 \uAE30\uB85D\uC5D0 \uB0A8\uC9C0 \uC54A\uC740 \uC138\uC158\uC740 \uD45C\uBCF8\uC5D0\uC11C \uBE8D\uB2C8\uB2E4.",
      evidence: "\uD45C\uBCF8\uC5D0 \uB123\uC740 \uC138\uC158 {sampledSessions} \xB7 \uC9C0\uCE68 \uD06C\uAE30\uAC00 \uAE30\uB85D\uC5D0 \uB0A8\uC9C0 \uC54A\uC740 \uC138\uC158 {skippedSessions}",
      unit: "\uD1A0\uD070(\uC5B4\uB9BC)",
      reasons: {
        no_data: {
          word: "\uD06C\uAE30\uAC00 \uAE30\uB85D\uB418\uC9C0 \uC54A\uC74C",
          text: "\uAE30\uB85D\uC5D0\uC11C \uC9C0\uCE68 \uD06C\uAE30\uB97C \uCC3E\uC9C0 \uBABB\uD588\uC2B5\uB2C8\uB2E4. \uC138\uC158\uC744 \uC2DC\uC791\uD560 \uB54C\uC758 \uC785\uB825 \uC815\uBCF4(\uC9C0\uCE68 \uD3EC\uD568)\uB97C \uAE30\uB85D\uC5D0 \uB0A8\uAE30\uC9C0 \uC54A\uB294 \uC2E4\uD589 \uBC29\uC2DD\uC774 \uC788\uC2B5\uB2C8\uB2E4."
        }
      }
    }
  },
  E5: {
    en: {
      name: "Unused skills",
      good: "Uses most of the skills whose use was judged",
      why: "Automatically invocable skills can add names and descriptions to the session skill list. Visibility settings and user-only invocation can change what is listed.",
      fix: "Turn off unused skills",
      problem: "{value} of the judged skills went unused.",
      prescription: 'Turn off a skill you do not use by setting its name to "off" under skillOverrides in your user settings (~/.claude/settings.json). Skills inside a plugin are managed with /plugin.',
      method: "Skills confirmed unused, divided by skills used plus skills confirmed unused. A skill is confirmed unused only when it has been installed for more than 14 days with no sign of use. Skills whose use cannot be told are left out.",
      evidence: "Turned on {enabled} \xB7 can be judged {judgeable} \xB7 judged {judged} (used {used}, unused {unused}) \xB7 cannot be judged by design {structural}",
      unit: "%",
      reasons: {
        too_little: { word: FEW.en, text: "Only {judgeable} {judgeable:skill is|skills are} eligible for use assessment, so the unused share was not calculated." },
        watching: WATCHING.en,
        unsupported: { text: "Whether these skills are used cannot be told from the records." },
        unreadable: { text: "A place where skills are found, a settings file, or the tool's usage counts could not be read." },
        not_applicable: { text: "No skill is turned on." },
        incomplete: { text: "The records of skill use could not all be read." }
      },
      repairUnmeasured: {
        too_little: "Only {judgeable} {judgeable:skill is|skills are} eligible for use assessment, so the unused share was not calculated. Found {candidates} that can be cleaned up.",
        watching: WATCHING_REPAIR.en
      }
    },
    ko: {
      name: "\uC548 \uC4F0\uB294 \uC2A4\uD0AC",
      good: "\uD310\uC815\uB41C \uC2A4\uD0AC \uAC00\uC6B4\uB370 \uB300\uBD80\uBD84\uC744 \uC4F0\uACE0 \uC788\uC74C",
      why: "\uC790\uB3D9\uC73C\uB85C \uBD80\uB97C \uC218 \uC788\uB294 \uC2A4\uD0AC\uC740 \uC138\uC158\uC758 \uC2A4\uD0AC \uBAA9\uB85D\uC5D0 \uC774\uB984\uACFC \uC124\uBA85\uC744 \uB354\uD560 \uC218 \uC788\uC2B5\uB2C8\uB2E4. \uD45C\uC2DC \uC124\uC815\uC774\uB098 \uC0AC\uC6A9\uC790\uB9CC \uBD80\uB974\uB294 \uC124\uC815\uC5D0 \uB530\uB77C \uBAA9\uB85D\uC5D0 \uC2E4\uB9AC\uB294 \uB0B4\uC6A9\uC740 \uB2EC\uB77C\uC9D1\uB2C8\uB2E4.",
      fix: "\uC548 \uC4F0\uB294 \uC2A4\uD0AC \uB044\uAE30",
      problem: "\uC4F0\uB294\uC9C0 \uD310\uC815\uB41C \uC2A4\uD0AC \uAC00\uC6B4\uB370 {value}\uB294 \uC4F0\uC9C0 \uC54A\uC740 \uAC83\uC73C\uB85C \uD655\uC778\uB410\uC2B5\uB2C8\uB2E4.",
      prescription: '\uC4F0\uC9C0 \uC54A\uB294 \uC2A4\uD0AC\uC740 \uC0AC\uC6A9\uC790 \uC124\uC815(~/.claude/settings.json)\uC758 skillOverrides\uC5D0\uC11C \uADF8 \uC774\uB984\uC744 "off"\uB85C \uC801\uC5B4 \uAEBC \uB450\uC138\uC694. \uD50C\uB7EC\uADF8\uC778\uC5D0 \uB4E0 \uC2A4\uD0AC\uC740 /plugin\uC5D0\uC11C \uAD00\uB9AC\uD569\uB2C8\uB2E4.',
      method: "\uC548 \uC4F4 \uAC83\uC774 \uD655\uC778\uB41C \uC2A4\uD0AC\uC744, \uC4F4 \uC2A4\uD0AC\uACFC \uC548 \uC4F4 \uAC83\uC774 \uD655\uC778\uB41C \uC2A4\uD0AC\uC758 \uD569\uC73C\uB85C \uB098\uB208 \uAC12\uC785\uB2C8\uB2E4. \uAE50 \uC9C0 14\uC77C\uC774 \uB118\uC5C8\uB294\uB370 \uC4F4 \uD754\uC801\uC774 \uC5C6\uC5B4\uC57C \uC548 \uC4F4 \uAC83\uC774 \uD655\uC778\uB418\uACE0, \uC4F0\uB294\uC9C0 \uAC00\uB9B4 \uC218 \uC5C6\uB294 \uC2A4\uD0AC\uC740 \uBE8D\uB2C8\uB2E4.",
      evidence: "\uCF1C\uC838 \uC788\uC74C {enabled} \xB7 \uD310\uC815\uD560 \uC218 \uC788\uC74C {judgeable} \xB7 \uD310\uC815\uB428 {judged}(\uC500 {used}, \uC548 \uC500 {unused}) \xB7 \uAD6C\uC870\uC0C1 \uD310\uC815\uD560 \uC218 \uC5C6\uC74C {structural}",
      unit: "%",
      reasons: {
        too_little: { word: FEW.ko, text: "\uC4F0\uB294\uC9C0 \uAC00\uB9B4 \uC218 \uC788\uB294 \uC2A4\uD0AC\uC774 {judgeable}\uAC1C\uBFD0\uC774\uC5B4\uC11C \uC548 \uC4F0\uB294 \uBE44\uC728\uC740 \uB0B4\uC9C0 \uC54A\uC558\uC2B5\uB2C8\uB2E4." },
        watching: WATCHING.ko,
        unsupported: { text: "\uAE30\uB85D\uC73C\uB85C\uB294 \uC774 \uC2A4\uD0AC\uB4E4\uC744 \uC4F0\uB294\uC9C0 \uAC00\uB9B4 \uC218 \uC5C6\uC2B5\uB2C8\uB2E4." },
        unreadable: { text: "\uC2A4\uD0AC\uC744 \uCC3E\uB294 \uACF3, \uC124\uC815 \uD30C\uC77C, \uB3C4\uAD6C\uC758 \uC0AC\uC6A9 \uC9D1\uACC4 \uAC00\uC6B4\uB370 \uC77D\uC9C0 \uBABB\uD55C \uAC83\uC774 \uC788\uC2B5\uB2C8\uB2E4." },
        not_applicable: { text: "\uCF1C\uC838 \uC788\uB294 \uC2A4\uD0AC\uC774 \uC5C6\uC2B5\uB2C8\uB2E4." },
        incomplete: { text: "\uC2A4\uD0AC \uC0AC\uC6A9 \uAE30\uB85D\uC744 \uBE60\uC9D0\uC5C6\uC774 \uC77D\uC9C0 \uBABB\uD588\uC2B5\uB2C8\uB2E4." }
      },
      repairUnmeasured: {
        too_little: "\uC4F0\uB294\uC9C0 \uAC00\uB9B4 \uC218 \uC788\uB294 \uC2A4\uD0AC\uC774 {judgeable}\uAC1C\uBFD0\uC774\uC5B4\uC11C \uC548 \uC4F0\uB294 \uBE44\uC728\uC740 \uB0B4\uC9C0 \uC54A\uC558\uC2B5\uB2C8\uB2E4. \uC815\uB9AC\uD560 \uC218 \uC788\uB294 \uAC83\uC740 {candidates}\uAC1C \uCC3E\uC558\uC2B5\uB2C8\uB2E4.",
        watching: WATCHING_REPAIR.ko
      }
    }
  },
  E6: {
    en: {
      name: "Unused MCP servers",
      good: "Calls most of the servers whose use was judged",
      why: "Enabled MCP servers can be connected to provide tools. Some connect at session start and others on first use.",
      fix: "Turn off unused MCP servers",
      problem: "{value} of the servers whose use was judged were confirmed uncalled.",
      prescription: "Turn off servers you do not call. In Claude Code, use /mcp or the deniedMcpServers list in your user settings; in Codex, set enabled = false in config.toml.",
      prescriptionByTool: {
        "claude-code": 'In Claude Code, turn off a server you do not call in /mcp, or block it by adding { "serverName": "<name>" } to the deniedMcpServers list in your user settings (~/.claude/settings.json).',
        codex: "In Codex, turn off a server you do not call by setting enabled = false in its [mcp_servers.<name>] table in your user config.toml. Restart Codex after the change."
      },
      method: "Servers confirmed uncalled, divided by the sum of servers called and servers confirmed uncalled. Confirming non-use requires this tool to have watched the same definition for more than 14 days; a call in the scoring window can establish use on the first checkup. Servers whose definition is not on this PC, such as those connected through claude.ai, are left out.",
      evidence: "Turned on {enabled} \xB7 can be judged {judgeable} \xB7 judged {judged} (called {used}, uncalled {unused}) \xB7 cannot be judged by design {structural}",
      unit: "%",
      reasons: {
        too_little: { word: FEW.en, text: "Only {judgeable} MCP {judgeable:server is|servers are} eligible for use assessment, so the unused share was not calculated." },
        watching: WATCHING.en,
        unsupported: { text: "Whether these servers are called cannot be told from the records." },
        unreadable: { text: "A place where servers are defined or a settings file could not be read." },
        not_applicable: { text: "No MCP server is turned on." },
        incomplete: { text: "The records of MCP calls could not all be read." }
      },
      repairUnmeasured: {
        too_little: "Only {judgeable} MCP {judgeable:server is|servers are} eligible for use assessment, so the unused share was not calculated. Found {candidates} that can be cleaned up.",
        watching: WATCHING_REPAIR.en
      }
    },
    ko: {
      name: "\uC548 \uC4F0\uB294 MCP \uC11C\uBC84",
      good: "\uD310\uC815\uB41C \uC11C\uBC84 \uAC00\uC6B4\uB370 \uB300\uBD80\uBD84\uC744 \uBD80\uB974\uACE0 \uC788\uC74C",
      why: "\uCF1C \uB454 MCP \uC11C\uBC84\uB294 \uB3C4\uAD6C\uB97C \uC81C\uACF5\uD558\uAE30 \uC704\uD574 \uC5F0\uACB0\uB420 \uC218 \uC788\uC2B5\uB2C8\uB2E4. \uC138\uC158\uC744 \uC2DC\uC791\uD560 \uB54C \uC5F0\uACB0\uB418\uB294 \uC11C\uBC84\uB3C4 \uC788\uACE0 \uCC98\uC74C \uBD80\uB97C \uB54C \uC5F0\uACB0\uB418\uB294 \uC11C\uBC84\uB3C4 \uC788\uC2B5\uB2C8\uB2E4.",
      fix: "\uC548 \uC4F0\uB294 MCP \uC11C\uBC84 \uB044\uAE30",
      problem: "\uBD80\uB974\uB294\uC9C0 \uD310\uC815\uB41C \uC11C\uBC84 \uAC00\uC6B4\uB370 {value}\uB294 \uBD80\uB974\uC9C0 \uC54A\uC740 \uAC83\uC73C\uB85C \uD655\uC778\uB410\uC2B5\uB2C8\uB2E4.",
      prescription: "\uBD80\uB974\uC9C0 \uC54A\uB294 \uC11C\uBC84\uB294 \uB044\uC138\uC694. Claude Code\uC5D0\uC11C\uB294 /mcp\uB098 \uC0AC\uC6A9\uC790 \uC124\uC815\uC758 deniedMcpServers \uBAA9\uB85D\uC73C\uB85C, Codex\uC5D0\uC11C\uB294 config.toml\uC5D0 enabled = false\uB97C \uC801\uC5B4 \uB055\uB2C8\uB2E4.",
      prescriptionByTool: {
        "claude-code": 'Claude Code\uC5D0\uC11C\uB294 \uBD80\uB974\uC9C0 \uC54A\uB294 \uC11C\uBC84\uB97C /mcp\uC5D0\uC11C \uB044\uAC70\uB098, \uC0AC\uC6A9\uC790 \uC124\uC815(~/.claude/settings.json)\uC758 deniedMcpServers \uBAA9\uB85D\uC5D0 { "serverName": "<\uC774\uB984>" }\uC744 \uB354\uD574 \uB9C9\uC73C\uC138\uC694.',
        codex: "Codex\uC5D0\uC11C\uB294 \uBD80\uB974\uC9C0 \uC54A\uB294 \uC11C\uBC84\uB97C \uC0AC\uC6A9\uC790 config.toml\uC758 [mcp_servers.<\uC774\uB984>]\uC5D0 enabled = false\uB97C \uC801\uC5B4 \uB044\uC138\uC694. \uBC14\uAFBC \uB4A4\uC5D0\uB294 Codex\uB97C \uB2E4\uC2DC \uC2DC\uC791\uD574\uC57C \uD569\uB2C8\uB2E4."
      },
      method: "\uC548 \uBD80\uB978 \uAC83\uC774 \uD655\uC778\uB41C \uC11C\uBC84\uB97C, \uBD80\uB978 \uC11C\uBC84\uC640 \uC548 \uBD80\uB978 \uAC83\uC774 \uD655\uC778\uB41C \uC11C\uBC84\uC758 \uD569\uC73C\uB85C \uB098\uB208 \uAC12\uC785\uB2C8\uB2E4. \uC548 \uBD80\uB978 \uAC83\uC744 \uD655\uC778\uD558\uB824\uBA74 \uC774 \uB3C4\uAD6C\uAC00 \uAC19\uC740 \uC815\uC758\uC758 \uC11C\uBC84\uB97C 14\uC77C \uB118\uAC8C \uC9C0\uCF1C\uBD10\uC57C \uD558\uC9C0\uB9CC, \uC810\uC218 \uAD6C\uAC04\uC5D0 \uBD80\uB978 \uAE30\uB85D\uC774 \uC788\uC73C\uBA74 \uCCAB \uC810\uAC80\uC5D0\uC11C\uB3C4 \uBD80\uB978 \uAC83\uC73C\uB85C \uD310\uC815\uD560 \uC218 \uC788\uC2B5\uB2C8\uB2E4. claude.ai\uC5D0 \uC5F0\uACB0\uD55C \uC11C\uBC84\uCC98\uB7FC \uC815\uC758\uAC00 \uC774 PC\uC5D0 \uC5C6\uB294 \uC11C\uBC84\uB294 \uBE8D\uB2C8\uB2E4.",
      evidence: "\uCF1C\uC838 \uC788\uC74C {enabled} \xB7 \uD310\uC815\uD560 \uC218 \uC788\uC74C {judgeable} \xB7 \uD310\uC815\uB428 {judged}(\uBD80\uB984 {used}, \uC548 \uBD80\uB984 {unused}) \xB7 \uAD6C\uC870\uC0C1 \uD310\uC815\uD560 \uC218 \uC5C6\uC74C {structural}",
      unit: "%",
      reasons: {
        too_little: { word: FEW.ko, text: "\uC4F0\uB294\uC9C0 \uAC00\uB9B4 \uC218 \uC788\uB294 MCP \uC11C\uBC84\uAC00 {judgeable}\uAC1C\uBFD0\uC774\uC5B4\uC11C \uC548 \uC4F0\uB294 \uBE44\uC728\uC740 \uB0B4\uC9C0 \uC54A\uC558\uC2B5\uB2C8\uB2E4." },
        watching: WATCHING.ko,
        unsupported: { text: "\uAE30\uB85D\uC73C\uB85C\uB294 \uC774 \uC11C\uBC84\uB4E4\uC744 \uBD80\uB974\uB294\uC9C0 \uAC00\uB9B4 \uC218 \uC5C6\uC2B5\uB2C8\uB2E4." },
        unreadable: { text: "\uC11C\uBC84\uB97C \uCC3E\uB294 \uACF3\uC774\uB098 \uC124\uC815 \uD30C\uC77C \uAC00\uC6B4\uB370 \uC77D\uC9C0 \uBABB\uD55C \uAC83\uC774 \uC788\uC2B5\uB2C8\uB2E4." },
        not_applicable: { text: "\uCF1C\uC838 \uC788\uB294 MCP \uC11C\uBC84\uAC00 \uC5C6\uC2B5\uB2C8\uB2E4." },
        incomplete: { text: "MCP \uD638\uCD9C \uAE30\uB85D\uC744 \uBE60\uC9D0\uC5C6\uC774 \uC77D\uC9C0 \uBABB\uD588\uC2B5\uB2C8\uB2E4." }
      },
      repairUnmeasured: {
        too_little: "\uC4F0\uB294\uC9C0 \uAC00\uB9B4 \uC218 \uC788\uB294 MCP \uC11C\uBC84\uAC00 {judgeable}\uAC1C\uBFD0\uC774\uC5B4\uC11C \uC548 \uC4F0\uB294 \uBE44\uC728\uC740 \uB0B4\uC9C0 \uC54A\uC558\uC2B5\uB2C8\uB2E4. \uC815\uB9AC\uD560 \uC218 \uC788\uB294 \uAC83\uC740 {candidates}\uAC1C \uCC3E\uC558\uC2B5\uB2C8\uB2E4.",
        watching: WATCHING_REPAIR.ko
      }
    }
  },
  E7: {
    en: {
      name: "Stopped work",
      good: "Work rarely stops midway",
      why: "A denied tool call, an interrupted turn, or a reply cut off by the length limit stops work that was underway, and it has to be picked up again.",
      fix: "Reduce stopped work",
      problem: "Recorded stops averaged {value}.",
      prescription: "If you often deny the same safe command, allow it with a rule in /permissions, such as Bash(npm run test *). If replies get cut off by the length limit, ask for smaller pieces of work.",
      method: "Denied tool calls, interrupted turns, and replies cut off by the length limit, divided by requests from you. Denials include those by you, by hooks, and by permission checks.",
      evidence: "Denied {denied} \xB7 interrupted turns {interruptedTurns} \xB7 cut off by length {lengthStops} \xB7 requests from you {humanRequests}",
      unit: "{value:stop|stops} per request",
      reasons: {
        no_data: { text: "There were no requests from you in the scoring window." },
        too_little: { text: "Fewer than 20 requests from you, so this was not measured." }
      }
    },
    ko: {
      name: "\uBA48\uCD98 \uC77C",
      good: "\uC77C\uC774 \uC911\uAC04\uC5D0 \uC798 \uBA48\uCD94\uC9C0 \uC54A\uC74C",
      why: "\uAC70\uC808\uD55C \uB3C4\uAD6C \uC2E4\uD589, \uB04A\uC740 \uD134, \uAE38\uC774 \uC81C\uD55C\uC73C\uB85C \uB04A\uAE34 \uC751\uB2F5\uC740 \uD558\uB358 \uC77C\uC744 \uBA48\uCD94\uAC8C \uD558\uACE0 \uB2E4\uC2DC \uC774\uC5B4 \uAC00\uC57C \uD569\uB2C8\uB2E4.",
      fix: "\uBA48\uCD94\uB294 \uC77C \uC904\uC774\uAE30",
      problem: "\uC77C\uC774 \uBA48\uCD98 \uD69F\uC218\uAC00 \uD3C9\uADE0 {value}\uC785\uB2C8\uB2E4.",
      prescription: "\uAC19\uC740 \uC548\uC804\uD55C \uBA85\uB839\uC744 \uC790\uC8FC \uAC70\uC808\uD55C\uB2E4\uBA74 /permissions\uC5D0\uC11C Bash(npm run test *) \uAC19\uC740 \uD5C8\uC6A9 \uADDC\uCE59\uC73C\uB85C \uB354\uD558\uC138\uC694. \uC751\uB2F5\uC774 \uAE38\uC774 \uC81C\uD55C\uC73C\uB85C \uB04A\uAE30\uBA74 \uC77C\uC744 \uC791\uAC8C \uB098\uB220 \uB9E1\uAE30\uC138\uC694.",
      method: "\uAC70\uC808\uD55C \uB3C4\uAD6C \uC2E4\uD589, \uB04A\uC740 \uD134, \uAE38\uC774 \uC81C\uD55C\uC73C\uB85C \uB04A\uAE34 \uC751\uB2F5\uC744 \uB354\uD574 \uC0AC\uB78C \uC694\uCCAD \uC218\uB85C \uB098\uB208 \uAC12\uC785\uB2C8\uB2E4. \uAC70\uC808\uC5D0\uB294 \uC0AC\uB78C\uC774 \uAC70\uC808\uD55C \uAC83, \uD6C5\uC774 \uB9C9\uC740 \uAC83, \uAD8C\uD55C \uAC80\uC0AC\uAC00 \uB9C9\uC740 \uAC83\uC774 \uBAA8\uB450 \uB4ED\uB2C8\uB2E4.",
      evidence: "\uAC70\uC808 {denied} \xB7 \uB04A\uC740 \uD134 {interruptedTurns} \xB7 \uAE38\uC774 \uC81C\uD55C\uC73C\uB85C \uB04A\uAE40 {lengthStops} \xB7 \uC0AC\uB78C \uC694\uCCAD {humanRequests}",
      unit: "\uD68C/\uC694\uCCAD",
      reasons: {
        no_data: { text: "\uC810\uC218 \uAD6C\uAC04\uC5D0 \uC0AC\uB78C \uC694\uCCAD\uC774 \uC5C6\uC2B5\uB2C8\uB2E4." },
        too_little: { text: "\uC0AC\uB78C \uC694\uCCAD\uC774 20\uAC1C\uC5D0 \uBABB \uBBF8\uCCD0 \uC7AC\uC9C0 \uC54A\uC558\uC2B5\uB2C8\uB2E4." }
      }
    }
  }
};

// src/core/copy/rules-fit.ts
var FIT_COPY = {
  F1: {
    en: {
      name: "Highest effort share",
      good: "Does not lean on the highest effort for everything",
      why: "This shows how often responses use xhigh or max. It does not judge task difficulty, so it carries a low weight.",
      fix: "Lower the everyday effort",
      problem: "{value} of responses with a known effort ran at the highest levels (xhigh, max).",
      prescription: "Set a lower everyday effort with /effort and raise it only for hard tasks.",
      method: "Share of responses with a known effort level that ran at xhigh or max. Responses with no effort recorded and unknown levels are left out.",
      evidence: "Highest effort {highEffort} \xB7 known effort {knownEffort} \xB7 effort not recorded {unknownEffort} \xB7 unknown level {unknownLevel}",
      unit: "%",
      reasons: {
        no_data: { text: "No response had a recognized effort level." },
        too_little: { text: "Fewer than 50 responses with a known effort, so this was not measured." }
      }
    },
    ko: {
      name: "\uAC00\uC7A5 \uB192\uC740 \uCD94\uB860 \uAC15\uB3C4\uC758 \uBAAB",
      good: "\uAC00\uC7A5 \uB192\uC740 \uCD94\uB860 \uAC15\uB3C4\uC5D0 \uC3E0\uB9AC\uC9C0 \uC54A\uC74C",
      why: "\uC751\uB2F5\uC5D0\uC11C xhigh\uB098 max\uB97C \uC5BC\uB9C8\uB098 \uC790\uC8FC \uC37C\uB294\uC9C0 \uBD05\uB2C8\uB2E4. \uC774 \uADDC\uCE59\uC740 \uC77C\uC774 \uC5BC\uB9C8\uB098 \uC5B4\uB824\uC6E0\uB294\uC9C0 \uBAA8\uB974\uBBC0\uB85C \uBB34\uAC8C\uB97C \uB0AE\uAC8C \uB461\uB2C8\uB2E4.",
      fix: "\uD3C9\uC18C \uCD94\uB860 \uAC15\uB3C4 \uB0AE\uCD94\uAE30",
      problem: "\uAC15\uB3C4\uB97C \uC544\uB294 \uC751\uB2F5 \uAC00\uC6B4\uB370 {value}\uAC00 \uAC00\uC7A5 \uB192\uC740 \uAC15\uB3C4(xhigh, max)\uB85C \uB3CC\uC558\uC2B5\uB2C8\uB2E4.",
      prescription: "/effort\uB85C \uD3C9\uC18C \uAC15\uB3C4\uB97C \uB0AE\uCD94\uACE0 \uC5B4\uB824\uC6B4 \uC77C\uC5D0\uC11C\uB9CC \uB192\uC774\uC138\uC694.",
      method: "\uAC15\uB3C4\uB97C \uC544\uB294 \uC751\uB2F5 \uAC00\uC6B4\uB370 xhigh\uB098 max\uB85C \uB3C8 \uBAAB\uC785\uB2C8\uB2E4. \uAC15\uB3C4\uAC00 \uAE30\uB85D\uB418\uC9C0 \uC54A\uC740 \uC751\uB2F5\uACFC \uBAA8\uB974\uB294 \uB2E8\uACC4\uB294 \uBE8D\uB2C8\uB2E4.",
      evidence: "\uAC00\uC7A5 \uB192\uC740 \uAC15\uB3C4 {highEffort} \xB7 \uAC15\uB3C4\uB97C \uC54E {knownEffort} \xB7 \uAC15\uB3C4\uAC00 \uAE30\uB85D\uB418\uC9C0 \uC54A\uC74C {unknownEffort} \xB7 \uBAA8\uB974\uB294 \uB2E8\uACC4 {unknownLevel}",
      unit: "%",
      reasons: {
        no_data: { text: "\uC54C\uC544\uBCFC \uC218 \uC788\uB294 \uCD94\uB860 \uAC15\uB3C4\uAC00 \uAE30\uB85D\uB41C \uC751\uB2F5\uC774 \uC5C6\uC2B5\uB2C8\uB2E4." },
        too_little: { text: "\uAC15\uB3C4\uB97C \uC544\uB294 \uC751\uB2F5\uC774 50\uAC1C\uC5D0 \uBABB \uBBF8\uCCD0 \uC7AC\uC9C0 \uC54A\uC558\uC2B5\uB2C8\uB2E4." }
      }
    }
  },
  F2: {
    en: {
      name: "Delegating long work",
      good: "Hands parts of long work to subagents",
      why: "A subagent works in a separate context window and returns its results. This rule checks whether main sessions with automatic compaction used subagents.",
      fix: "Hand parts of long work to subagents",
      problem: "Subagents were used in {value} of the sessions that were compacted automatically.",
      prescription: "In long sessions, ask Claude to give searches and large file reads to a subagent. You can also write your own subagents as Markdown files in .claude/agents/ or ~/.claude/agents/.",
      method: "Share of main sessions with an automatic compaction that also used a subagent.",
      evidence: "Sessions that used a subagent {delegatedSessions} \xB7 sessions with automatic compaction {compactedSessions}",
      unit: "%",
      reasons: {
        no_data: { text: "No main session was compacted automatically." },
        too_little: { text: "Fewer than 3 main sessions were compacted automatically, so this was not measured." }
      }
    },
    ko: {
      name: "\uAE34 \uC77C \uB098\uB220 \uB9E1\uAE30\uAE30",
      good: "\uAE34 \uC77C\uC744 \uD558\uC704 \uC5D0\uC774\uC804\uD2B8\uC5D0 \uB098\uB220 \uB9E1\uAE40",
      why: "\uD558\uC704 \uC5D0\uC774\uC804\uD2B8\uB294 \uBCC4\uB3C4 \uB300\uD654 \uCC3D\uC5D0\uC11C \uC77C\uD558\uACE0 \uACB0\uACFC\uB97C \uB3CC\uB824\uC90D\uB2C8\uB2E4. \uC774 \uD56D\uBAA9\uC740 \uC790\uB3D9 \uC555\uCD95\uC774 \uC788\uC5C8\uB358 \uC8FC \uC138\uC158\uC5D0\uC11C \uD558\uC704 \uC5D0\uC774\uC804\uD2B8\uB97C \uC37C\uB294\uC9C0 \uBD05\uB2C8\uB2E4.",
      fix: "\uAE34 \uC77C\uC744 \uD558\uC704 \uC5D0\uC774\uC804\uD2B8\uC5D0 \uB098\uB220 \uB9E1\uAE30\uAE30",
      problem: "\uC790\uB3D9 \uC555\uCD95\uC774 \uC788\uC5C8\uB358 \uC138\uC158 \uAC00\uC6B4\uB370 \uD558\uC704 \uC5D0\uC774\uC804\uD2B8\uB97C \uC4F4 \uC138\uC158\uC740 {value}\uC785\uB2C8\uB2E4.",
      prescription: "\uAE34 \uC138\uC158\uC5D0\uC11C\uB294 \uC870\uC0AC\uB098 \uD070 \uD30C\uC77C \uC77D\uAE30\uB97C \uD558\uC704 \uC5D0\uC774\uC804\uD2B8\uC5D0 \uB9E1\uACA8 \uB2EC\uB77C\uACE0 \uD558\uC138\uC694. \uD558\uC704 \uC5D0\uC774\uC804\uD2B8\uB294 .claude/agents/\uB098 ~/.claude/agents/\uC5D0 \uB9C8\uD06C\uB2E4\uC6B4 \uD30C\uC77C\uB85C \uC9C1\uC811 \uB9CC\uB4E4 \uC218\uB3C4 \uC788\uC2B5\uB2C8\uB2E4.",
      method: "\uC790\uB3D9 \uC555\uCD95\uC774 \uC788\uC5C8\uB358 \uC8FC \uC138\uC158 \uAC00\uC6B4\uB370 \uD558\uC704 \uC5D0\uC774\uC804\uD2B8\uB97C \uC4F4 \uC138\uC158\uC758 \uBAAB\uC785\uB2C8\uB2E4.",
      evidence: "\uD558\uC704 \uC5D0\uC774\uC804\uD2B8\uB97C \uC4F4 \uC138\uC158 {delegatedSessions} \xB7 \uC790\uB3D9 \uC555\uCD95\uC774 \uC788\uC5C8\uB358 \uC138\uC158 {compactedSessions}",
      unit: "%",
      reasons: {
        no_data: { text: "\uC790\uB3D9 \uC555\uCD95\uC774 \uC788\uC5C8\uB358 \uC8FC \uC138\uC158\uC774 \uC5C6\uC2B5\uB2C8\uB2E4." },
        too_little: { text: "\uC790\uB3D9 \uC555\uCD95\uC774 \uC788\uC5C8\uB358 \uC8FC \uC138\uC158\uC774 3\uAC1C\uC5D0 \uBABB \uBBF8\uCCD0 \uC7AC\uC9C0 \uC54A\uC558\uC2B5\uB2C8\uB2E4." }
      }
    }
  },
  F3: {
    en: {
      name: "Project instructions",
      good: "Projects you use often have their own instructions",
      why: "Project instructions give the tool a reference for how a project is built and run. This rule checks whether often-used projects have those instructions.",
      fix: "Add instructions to projects you use often",
      problem: "{value} of the projects you use often have project instructions.",
      prescription: "In a project you use often, run /init to create a CLAUDE.md, then keep only what that project needs.",
      method: "Among target projects with 3 or more main sessions in the scoring window, the share that have project instructions for each tool mainly used there. Targets are folders on this PC that are Git repositories or have project instructions or settings. Folders not treated as projects, such as the home folder, are left out.",
      evidence: "Projects with instructions {withInstructions} \xB7 projects used often {targets}",
      unit: "%",
      reasons: { not_applicable: { text: "No target project had 3 or more main sessions in the scoring window. Folders that are gone or not treated as projects are not targets." } }
    },
    ko: {
      name: "\uD504\uB85C\uC81D\uD2B8 \uC9C0\uCE68",
      good: "\uC790\uC8FC \uC4F0\uB294 \uD504\uB85C\uC81D\uD2B8\uC5D0 \uC9C0\uCE68\uC744 \uB460",
      why: "\uD504\uB85C\uC81D\uD2B8 \uC9C0\uCE68\uC740 \uD504\uB85C\uC81D\uD2B8\uB97C \uC5B4\uB5BB\uAC8C \uBE4C\uB4DC\uD558\uACE0 \uC2E4\uD589\uD558\uB294\uC9C0 \uCC38\uACE0\uD560 \uB0B4\uC6A9\uC744 \uC90D\uB2C8\uB2E4. \uC774 \uD56D\uBAA9\uC740 \uC790\uC8FC \uC4F0\uB294 \uD504\uB85C\uC81D\uD2B8\uC5D0 \uADF8\uB7F0 \uC9C0\uCE68\uC774 \uC788\uB294\uC9C0 \uBD05\uB2C8\uB2E4.",
      fix: "\uC790\uC8FC \uC4F0\uB294 \uD504\uB85C\uC81D\uD2B8\uC5D0 \uC9C0\uCE68 \uB450\uAE30",
      problem: "\uC790\uC8FC \uC4F0\uB294 \uD504\uB85C\uC81D\uD2B8 \uAC00\uC6B4\uB370 \uC9C0\uCE68\uC774 \uC788\uB294 \uD504\uB85C\uC81D\uD2B8\uB294 {value}\uC785\uB2C8\uB2E4.",
      prescription: "\uC790\uC8FC \uC4F0\uB294 \uD504\uB85C\uC81D\uD2B8\uC5D0\uC11C /init\uC73C\uB85C CLAUDE.md\uB97C \uB9CC\uB4E4\uACE0 \uADF8 \uD504\uB85C\uC81D\uD2B8\uC5D0 \uD544\uC694\uD55C \uAC83\uB9CC \uB0A8\uAE30\uC138\uC694.",
      method: "\uC810\uC218 \uAD6C\uAC04\uC5D0 \uC8FC \uC138\uC158\uC774 3\uAC1C \uC774\uC0C1\uC778 \uB300\uC0C1 \uD504\uB85C\uC81D\uD2B8 \uAC00\uC6B4\uB370, \uAC70\uAE30\uC11C \uC8FC\uB85C \uC4F4 \uB3C4\uAD6C\uB9C8\uB2E4 \uD504\uB85C\uC81D\uD2B8 \uC9C0\uCE68\uC774 \uC788\uB294 \uD504\uB85C\uC81D\uD2B8\uC758 \uBAAB\uC785\uB2C8\uB2E4. \uB300\uC0C1\uC740 \uC9C0\uAE08 \uC774 PC\uC5D0 \uC788\uACE0 \uAE43 \uC800\uC7A5\uC18C\uC774\uAC70\uB098 \uD504\uB85C\uC81D\uD2B8 \uC9C0\uCE68\xB7\uC124\uC815\uC774 \uC788\uB294 \uD3F4\uB354\uC785\uB2C8\uB2E4. \uD648 \uD3F4\uB354\uCC98\uB7FC \uD504\uB85C\uC81D\uD2B8\uB85C \uBCF4\uC9C0 \uC54A\uB294 \uD3F4\uB354\uB294 \uBE8D\uB2C8\uB2E4.",
      evidence: "\uC9C0\uCE68\uC774 \uC788\uB294 \uD504\uB85C\uC81D\uD2B8 {withInstructions} \xB7 \uC790\uC8FC \uC4F0\uB294 \uD504\uB85C\uC81D\uD2B8 {targets}",
      unit: "%",
      reasons: { not_applicable: { text: "\uC810\uC218 \uAD6C\uAC04\uC5D0 \uC8FC \uC138\uC158\uC774 3\uAC1C \uC774\uC0C1\uC778 \uB300\uC0C1 \uD504\uB85C\uC81D\uD2B8\uAC00 \uC5C6\uC2B5\uB2C8\uB2E4. \uC791\uC5C5 \uD3F4\uB354\uAC00 \uC9C0\uAE08 \uC5C6\uAC70\uB098 \uD504\uB85C\uC81D\uD2B8\uB85C \uBCF4\uC9C0 \uC54A\uB294 \uD3F4\uB354\uB294 \uB300\uC0C1\uC5D0\uC11C \uBE8D\uB2C8\uB2E4." } }
    }
  },
  F4: {
    en: {
      name: "Instruction overlap",
      good: "Keeps overlap between global and project instructions low",
      why: "A line that is in both global and project instructions loads twice in that project and has to be kept the same in two places.",
      fix: "Remove repeated instruction lines",
      problem: "In the project with the most overlap, {value} of global instruction lines appear again in its instructions.",
      prescription: "Keep each line in one place. Rules for everywhere go in global instructions, and rules only one project needs go in that project.",
      method: "Share of distinct global instruction lines, at least 20 characters after trimming, that appear word for word in a project's instructions. The project with the highest share is used.",
      evidence: "Repeated lines {overlappingLines} \xB7 global lines {globalLines} \xB7 projects compared {comparedProjects}",
      unit: "%",
      reasons: {
        not_applicable: { text: "There are no global instruction lines or separate project instructions to compare." },
        unreadable: { text: "An instruction file to compare could not be read." }
      }
    },
    ko: {
      name: "\uC9C0\uCE68 \uACB9\uCE68",
      good: "\uC804\uC5ED \uC9C0\uCE68\uACFC \uD504\uB85C\uC81D\uD2B8 \uC9C0\uCE68\uC758 \uACB9\uCE68\uC774 \uC801\uC74C",
      why: "\uC804\uC5ED \uC9C0\uCE68\uACFC \uD504\uB85C\uC81D\uD2B8 \uC9C0\uCE68\uC5D0 \uAC19\uC740 \uC904\uC774 \uC788\uC73C\uBA74 \uADF8 \uD504\uB85C\uC81D\uD2B8\uC5D0\uC11C \uB450 \uBC88 \uC2E4\uB9AC\uACE0, \uACE0\uCE60 \uB54C\uB3C4 \uB450 \uACF3\uC744 \uB9DE\uCDB0\uC57C \uD569\uB2C8\uB2E4.",
      fix: "\uACB9\uCE58\uB294 \uC9C0\uCE68 \uC904 \uC815\uB9AC\uD558\uAE30",
      problem: "\uAC00\uC7A5 \uB9CE\uC774 \uACB9\uCE58\uB294 \uD504\uB85C\uC81D\uD2B8\uC5D0\uC11C \uC804\uC5ED \uC9C0\uCE68 \uC904\uC758 {value}\uAC00 \uD504\uB85C\uC81D\uD2B8 \uC9C0\uCE68\uC5D0 \uB2E4\uC2DC \uB098\uC635\uB2C8\uB2E4.",
      prescription: "\uD55C \uC904\uC740 \uD55C \uACF3\uC5D0\uB9CC \uB450\uC138\uC694. \uC5B4\uB514\uC11C\uB098 \uD1B5\uD558\uB294 \uADDC\uCE59\uC740 \uC804\uC5ED \uC9C0\uCE68\uC5D0, \uADF8 \uD504\uB85C\uC81D\uD2B8\uC5D0\uB9CC \uD544\uC694\uD55C \uADDC\uCE59\uC740 \uD504\uB85C\uC81D\uD2B8 \uC9C0\uCE68\uC5D0 \uB461\uB2C8\uB2E4.",
      method: "\uC55E\uB4A4 \uACF5\uBC31\uC744 \uB5BC\uACE0 20\uC790 \uC774\uC0C1\uC778 \uC11C\uB85C \uB2E4\uB978 \uC804\uC5ED \uC9C0\uCE68 \uC904 \uAC00\uC6B4\uB370 \uD504\uB85C\uC81D\uD2B8 \uC9C0\uCE68\uC5D0 \uAE00\uC790 \uADF8\uB300\uB85C \uB2E4\uC2DC \uB098\uC624\uB294 \uBAAB\uC785\uB2C8\uB2E4. \uBAAB\uC774 \uAC00\uC7A5 \uD070 \uD504\uB85C\uC81D\uD2B8\uC758 \uAC12\uC744 \uC501\uB2C8\uB2E4.",
      evidence: "\uACB9\uCE58\uB294 \uC904 {overlappingLines} \xB7 \uC804\uC5ED \uC9C0\uCE68 \uC904 {globalLines} \xB7 \uACAC\uC900 \uD504\uB85C\uC81D\uD2B8 {comparedProjects}",
      unit: "%",
      reasons: {
        not_applicable: { text: "\uACAC\uC904 \uC804\uC5ED \uC9C0\uCE68 \uC904\uC774\uB098 \uBCC4\uB3C4\uC758 \uD504\uB85C\uC81D\uD2B8 \uC9C0\uCE68\uC774 \uC5C6\uC2B5\uB2C8\uB2E4." },
        unreadable: { text: "\uACAC\uC8FC\uB294 \uC9C0\uCE68 \uD30C\uC77C \uAC00\uC6B4\uB370 \uC77D\uC9C0 \uBABB\uD55C \uAC83\uC774 \uC788\uC2B5\uB2C8\uB2E4." }
      }
    }
  },
  F5: {
    en: {
      name: "Duplicate skills",
      good: "Limits extra copies of skills sharing a name",
      why: "Copies of a skill can drift apart across folders, making it harder to track which copy is loaded.",
      fix: "Keep one copy of each skill",
      problem: "Extra copies score {value} on average.",
      prescription: "Keep one original and remove the other copies or replace them with links to the original. Before removing a copy, check that no project sees only that copy. If you use both Claude Code and Codex, one original can be linked from both tools' folders.",
      method: "Within one tool, each extra copy of a skill name scores 1 point if all copies are identical and 2 points if any differ or cannot be compared, divided by the number of skill names. Links and copies placed by plugins are not counted.",
      evidence: "Extra identical copies {identicalCopies} \xB7 extra differing copies {differingCopies} \xB7 skill names {skillKinds}",
      unit: "{value:point|points} per skill",
      reasons: {
        not_applicable: { text: "There are no user or project skills to compare for copies. Skills inside plugins are not counted." },
        unreadable: { text: "A skill folder searched for copies could not be listed." }
      }
    },
    ko: {
      name: "\uAC19\uC740 \uC774\uB984\uC758 \uC2A4\uD0AC \uC0AC\uBCF8",
      good: "\uAC19\uC740 \uC774\uB984\uC758 \uC2A4\uD0AC \uC0AC\uBCF8\uC744 \uC801\uAC8C \uB460",
      why: "\uC2A4\uD0AC\uC744 \uC5EC\uB7EC \uD3F4\uB354\uC5D0 \uBCF5\uC0AC\uD574 \uB450\uBA74 \uB0B4\uC6A9\uC774 \uB2EC\uB77C\uC9C8 \uC218 \uC788\uACE0 \uC5B4\uB290 \uC0AC\uBCF8\uC774 \uC2E4\uB9AC\uB294\uC9C0 \uD30C\uC545\uD558\uAE30 \uC5B4\uB824\uC6B8 \uC218 \uC788\uC2B5\uB2C8\uB2E4.",
      fix: "\uC2A4\uD0AC \uC0AC\uBCF8\uC744 \uD558\uB098\uB85C \uC815\uB9AC\uD558\uAE30",
      problem: "\uB0A8\uB294 \uC0AC\uBCF8\uC758 \uC810\uC218\uAC00 \uD3C9\uADE0 {value}\uC785\uB2C8\uB2E4.",
      prescription: "\uC6D0\uBCF8 \uD558\uB098\uB9CC \uB0A8\uAE30\uACE0 \uB098\uBA38\uC9C0 \uC0AC\uBCF8\uC740 \uC9C0\uC6B0\uAC70\uB098 \uC6D0\uBCF8\uC744 \uAC00\uB9AC\uD0A4\uB294 \uB9C1\uD06C\uB85C \uBC14\uAFB8\uC138\uC694. \uC0AC\uBCF8\uC744 \uCE58\uC6B0\uAE30 \uC804\uC5D0 \uADF8 \uC0AC\uBCF8\uB9CC \uBCF4\uC774\uB294 \uD504\uB85C\uC81D\uD2B8\uAC00 \uC5C6\uB294\uC9C0 \uBCF4\uC138\uC694. Claude Code\uC640 Codex\uB97C \uD568\uAED8 \uC4F0\uBA74 \uC6D0\uBCF8 \uD558\uB098\uB97C \uB450 \uB3C4\uAD6C\uC758 \uD3F4\uB354\uC5D0\uC11C \uB9C1\uD06C\uB85C \uAC78 \uC218 \uC788\uC2B5\uB2C8\uB2E4.",
      method: "\uAC19\uC740 \uB3C4\uAD6C \uC548\uC5D0\uC11C \uD55C \uC774\uB984\uC758 \uB0A8\uB294 \uC0AC\uBCF8\uB9C8\uB2E4, \uC0AC\uBCF8\uC774 \uBAA8\uB450 \uAC19\uC73C\uBA74 1\uC810, \uD558\uB098\uB77C\uB3C4 \uB2E4\uB974\uAC70\uB098 \uB0B4\uC6A9\uC744 \uACAC\uC904 \uC218 \uC5C6\uC73C\uBA74 2\uC810\uC73C\uB85C \uCCD0\uC11C \uC2A4\uD0AC \uC885 \uC218\uB85C \uB098\uB208 \uAC12\uC785\uB2C8\uB2E4. \uB9C1\uD06C\uC640 \uD50C\uB7EC\uADF8\uC778\uC774 \uB123\uC740 \uC0AC\uBCF8\uC740 \uC138\uC9C0 \uC54A\uC2B5\uB2C8\uB2E4.",
      evidence: "\uAC19\uC740 \uC0AC\uBCF8 {identicalCopies} \xB7 \uB0B4\uC6A9\uC774 \uB2E4\uB978 \uC0AC\uBCF8 {differingCopies} \xB7 \uC2A4\uD0AC \uC885 \uC218 {skillKinds}",
      unit: "\uC810/\uC2A4\uD0AC",
      reasons: {
        not_applicable: { text: "\uC0AC\uBCF8\uC744 \uACAC\uC904 \uC0AC\uC6A9\uC790\xB7\uD504\uB85C\uC81D\uD2B8 \uC2A4\uD0AC\uC774 \uC5C6\uC2B5\uB2C8\uB2E4. \uD50C\uB7EC\uADF8\uC778\uC5D0 \uB4E0 \uC2A4\uD0AC\uC740 \uC138\uC9C0 \uC54A\uC2B5\uB2C8\uB2E4." },
        unreadable: { text: "\uC0AC\uBCF8\uC744 \uCC3E\uB294 \uC2A4\uD0AC \uD3F4\uB354 \uAC00\uC6B4\uB370 \uBAA9\uB85D\uC744 \uC77D\uC9C0 \uBABB\uD55C \uAC83\uC774 \uC788\uC2B5\uB2C8\uB2E4." }
      }
    }
  },
  F6: {
    en: {
      name: "Settings conflicts",
      good: "Global and project settings do not contradict each other",
      why: "When the same permission rule is allowed on one side and denied on the other, the deny wins. The allow then has no effect, which may not be what you meant.",
      fix: "Resolve conflicting permission rules",
      problem: "Found {value} of conflicting rules.",
      prescription: "Look at each rule that is allowed in one place and denied in another, and keep it on one side only. /permissions shows the rules by scope.",
      method: "Number of pairs where the same rule text is allowed on one side and denied on the other, between your user settings and each project's project and local settings. Managed policy is not compared.",
      evidence: "Conflicting pairs {conflicts} \xB7 projects with settings {projectsWithSettings}",
      unit: "{value:pair|pairs}",
      reasons: {
        not_applicable: { text: "No listed project has project or local settings." },
        unreadable: { text: "A settings file to compare could not be read." }
      }
    },
    ko: {
      name: "\uC124\uC815 \uCDA9\uB3CC",
      good: "\uC804\uC5ED \uC124\uC815\uACFC \uD504\uB85C\uC81D\uD2B8 \uC124\uC815\uC774 \uBD80\uB52A\uD788\uC9C0 \uC54A\uC74C",
      why: "\uAC19\uC740 \uAD8C\uD55C \uADDC\uCE59\uC774 \uD55C\uCABD\uC5D0\uC11C\uB294 \uD5C8\uC6A9, \uB2E4\uB978 \uCABD\uC5D0\uC11C\uB294 \uAE08\uC9C0\uB418\uC5B4 \uC788\uC73C\uBA74 \uAE08\uC9C0\uAC00 \uC774\uAE41\uB2C8\uB2E4. \uD5C8\uC6A9\uD574 \uB454 \uCABD\uC740 \uB4E3\uC9C0 \uC54A\uC73C\uBBC0\uB85C \uB73B\uACFC \uB2E4\uB974\uAC8C \uB3D9\uC791\uD560 \uC218 \uC788\uC2B5\uB2C8\uB2E4.",
      fix: "\uBD80\uB52A\uD788\uB294 \uAD8C\uD55C \uADDC\uCE59 \uC815\uB9AC\uD558\uAE30",
      problem: "\uBD80\uB52A\uD788\uB294 \uADDC\uCE59\uC774 {value} \uC788\uC2B5\uB2C8\uB2E4.",
      prescription: "\uD55C\uCABD\uC5D0\uC11C \uD5C8\uC6A9\uD558\uACE0 \uB2E4\uB978 \uCABD\uC5D0\uC11C \uAE08\uC9C0\uD55C \uADDC\uCE59\uC744 \uBCF4\uACE0 \uD55C\uCABD\uC5D0\uB9CC \uB0A8\uAE30\uC138\uC694. /permissions\uC5D0\uC11C \uBC94\uC704\uBCC4\uB85C \uADDC\uCE59\uC744 \uBCFC \uC218 \uC788\uC2B5\uB2C8\uB2E4.",
      method: "\uC0AC\uC6A9\uC790 \uC124\uC815\uACFC \uAC01 \uD504\uB85C\uC81D\uD2B8\uC758 \uD504\uB85C\uC81D\uD2B8 \uC124\uC815\xB7\uB85C\uCEEC \uC124\uC815 \uC0AC\uC774\uC5D0\uC11C, \uAC19\uC740 \uADDC\uCE59 \uBB38\uC790\uC5F4\uC744 \uD55C\uCABD\uC740 \uD5C8\uC6A9\uC5D0 \uB2E4\uB978 \uCABD\uC740 \uAE08\uC9C0\uC5D0 \uB454 \uC30D\uC758 \uC218\uC785\uB2C8\uB2E4. \uAD00\uB9AC \uC815\uCC45\uC740 \uACAC\uC8FC\uC9C0 \uC54A\uC2B5\uB2C8\uB2E4.",
      evidence: "\uBD80\uB52A\uD788\uB294 \uC30D {conflicts} \xB7 \uC124\uC815\uC774 \uC788\uB294 \uD504\uB85C\uC81D\uD2B8 {projectsWithSettings}",
      unit: "\uC30D",
      reasons: {
        not_applicable: { text: "\uBAA9\uB85D\uC758 \uD504\uB85C\uC81D\uD2B8 \uC5B4\uB514\uC5D0\uB3C4 \uD504\uB85C\uC81D\uD2B8 \uC124\uC815\uC774\uB098 \uB85C\uCEEC \uC124\uC815\uC774 \uC5C6\uC2B5\uB2C8\uB2E4." },
        unreadable: { text: "\uACAC\uC8FC\uB294 \uC124\uC815 \uD30C\uC77C \uAC00\uC6B4\uB370 \uC77D\uC9C0 \uBABB\uD55C \uAC83\uC774 \uC788\uC2B5\uB2C8\uB2E4." }
      }
    }
  }
};

// src/core/copy/rules-intensity.ts
var INTENSITY_COPY = {
  I1: {
    en: {
      name: "Days used",
      good: "Uses the tools regularly",
      why: "This counts days with a response from any tool in the 30-day scoring window. It gives context for reading the other measurements.",
      fix: "Use the tools on more days",
      problem: "Tools were used on {value} in the last 30 days.",
      prescription: "Try handing everyday tasks to the tools too, such as reading logs, drafting messages, or tidying files.",
      method: "Days in the 30-day scoring window on which any tool had a response.",
      evidence: "Days with responses {activeDays}",
      unit: "{value:day|days}"
    },
    ko: {
      name: "\uC0AC\uC6A9\uD55C \uB0A0",
      good: "\uAFB8\uC900\uD788 \uC500",
      why: "\uC810\uC218 \uAD6C\uAC04 30\uC77C \uAC00\uC6B4\uB370 \uC5B4\uB290 \uB3C4\uAD6C\uC5D0\uC11C\uB4E0 \uC751\uB2F5\uC774 \uC788\uC5C8\uB358 \uB0A0\uC744 \uC149\uB2C8\uB2E4. \uB2E4\uB978 \uCE21\uC815\uAC12\uC744 \uD574\uC11D\uD560 \uB54C \uD568\uAED8 \uBCFC \uC815\uBCF4\uC785\uB2C8\uB2E4.",
      fix: "\uC4F0\uB294 \uB0A0 \uB298\uB9AC\uAE30",
      problem: "\uCD5C\uADFC 30\uC77C \uAC00\uC6B4\uB370 \uC4F4 \uB0A0\uC774 {value}\uC785\uB2C8\uB2E4.",
      prescription: "\uAE30\uB85D \uC77D\uAE30, \uAE00 \uCD08\uC548, \uD30C\uC77C \uC815\uB9AC\uCC98\uB7FC \uB0A0\uB9C8\uB2E4 \uD558\uB294 \uC77C\uB3C4 \uB9E1\uACA8 \uBCF4\uC138\uC694.",
      method: "\uC810\uC218 \uAD6C\uAC04 30\uC77C \uAC00\uC6B4\uB370 \uC5B4\uB290 \uB3C4\uAD6C\uC5D0\uC11C\uB4E0 \uC751\uB2F5\uC774 \uC788\uC5C8\uB358 \uB0A0\uC758 \uC218\uC785\uB2C8\uB2E4.",
      evidence: "\uC751\uB2F5\uC774 \uC788\uC5C8\uB358 \uB0A0 {activeDays}",
      unit: "\uC77C"
    }
  },
  I2: {
    en: {
      name: "Requests per day",
      good: "Hands over plenty of work each day",
      why: "This is the average number of requests on days when you used the tools. It shows how often you handed work to them on those days.",
      fix: "Hand over more work on the days you use them",
      problem: "You sent {value} on average.",
      prescription: 'Break your work into pieces you can hand over, such as "write a test for this function" or "summarize this log".',
      method: "Requests from you across all tools, divided by days used.",
      evidence: "Requests from you {humanRequests} \xB7 days used {activeDays}",
      unit: "{value:request|requests} per day",
      reasons: { no_data: { text: "There were no days of use in the scoring window." } }
    },
    ko: {
      name: "\uD558\uB8E8\uC5D0 \uC2DC\uD0A4\uB294 \uC591",
      good: "\uD558\uB8E8\uC5D0 \uB9CE\uC740 \uC77C\uC744 \uB9E1\uAE40",
      why: "\uC4F4 \uB0A0 \uD558\uB8E8\uC5D0 \uBCF4\uB0B8 \uD3C9\uADE0 \uC694\uCCAD \uC218\uC785\uB2C8\uB2E4. \uB3C4\uAD6C\uB97C \uC4F4 \uB0A0\uC5D0 \uC5BC\uB9C8\uB098 \uC790\uC8FC \uC77C\uC744 \uB9E1\uACBC\uB294\uC9C0 \uBCF4\uC5EC \uC90D\uB2C8\uB2E4.",
      fix: "\uC4F0\uB294 \uB0A0 \uB354 \uB9CE\uC740 \uC77C \uB9E1\uAE30\uAE30",
      problem: "\uC4F4 \uB0A0 \uD558\uB8E8\uC5D0 \uBCF4\uB0B8 \uC694\uCCAD\uC774 \uD3C9\uADE0 {value}\uC785\uB2C8\uB2E4.",
      prescription: '"\uC774 \uD568\uC218\uC758 \uC2DC\uD5D8\uC744 \uC368 \uC918", "\uC774 \uAE30\uB85D\uC744 \uC694\uC57D\uD574 \uC918"\uCC98\uB7FC \uB9E1\uAE38 \uC218 \uC788\uB294 \uB2E8\uC704\uB85C \uC77C\uC744 \uB098\uB220 \uBCF4\uC138\uC694.',
      method: "\uBAA8\uB4E0 \uB3C4\uAD6C\uC758 \uC0AC\uB78C \uC694\uCCAD \uC218\uB97C \uC0AC\uC6A9\uD55C \uB0A0\uB85C \uB098\uB208 \uAC12\uC785\uB2C8\uB2E4.",
      evidence: "\uC0AC\uB78C \uC694\uCCAD {humanRequests} \xB7 \uC0AC\uC6A9\uD55C \uB0A0 {activeDays}",
      unit: "\uAC1C/\uC77C",
      reasons: { no_data: { text: "\uC810\uC218 \uAD6C\uAC04\uC5D0 \uC4F4 \uB0A0\uC774 \uC5C6\uC2B5\uB2C8\uB2E4." } }
    }
  },
  I3: {
    en: {
      name: "Depth per request",
      good: "Lets each request run several steps",
      why: "Tool calls per request show how much one request carries, such as reading, editing, and testing in one go.",
      fix: "Hand over whole tasks",
      problem: "Tool calls averaged {value}.",
      prescription: 'Instead of asking for one small step at a time, describe the whole task and how to check it, such as "fix this bug and run the tests".',
      method: "Tool calls across all tools, divided by requests from you.",
      evidence: "Tool calls {toolCalls} \xB7 requests from you {humanRequests}",
      unit: "{value:call|calls} per request",
      reasons: {
        no_data: { text: "There were no requests from you in the scoring window." },
        too_little: { text: "Fewer than 20 requests from you, so this was not measured." }
      }
    },
    ko: {
      name: "\uD55C \uBC88\uC5D0 \uB9E1\uAE30\uB294 \uAE4A\uC774",
      good: "\uD55C \uBC88\uC5D0 \uC5EC\uB7EC \uB2E8\uACC4\uB97C \uB9E1\uAE40",
      why: "\uC694\uCCAD \uD558\uB098\uC5D0 \uB3C4\uAD6C \uD638\uCD9C\uC774 \uBA87 \uBC88 \uC788\uC5C8\uB294\uC9C0\uB85C, \uC77D\uACE0 \uACE0\uCE58\uACE0 \uC2DC\uD5D8\uD558\uB294 \uC77C\uC744 \uD55C \uBC88\uC5D0 \uC5BC\uB9C8\uB098 \uB9E1\uAE30\uB294\uC9C0 \uBD05\uB2C8\uB2E4.",
      fix: "\uC77C\uC744 \uD1B5\uC9F8\uB85C \uB9E1\uAE30\uAE30",
      problem: "\uC694\uCCAD \uD558\uB098\uC5D0 \uB3C4\uAD6C \uD638\uCD9C\uC774 \uD3C9\uADE0 {value}\uC785\uB2C8\uB2E4.",
      prescription: '\uC791\uC740 \uB2E8\uACC4\uB97C \uD558\uB098\uC529 \uC2DC\uD0A4\uAE30\uBCF4\uB2E4 "\uC774 \uBC84\uADF8\uB97C \uACE0\uCE58\uACE0 \uC2DC\uD5D8\uC744 \uB3CC\uB824 \uC918"\uCC98\uB7FC \uD560 \uC77C\uACFC \uD655\uC778 \uBC29\uBC95\uC744 \uD55C \uBC88\uC5D0 \uC54C\uB824 \uC8FC\uC138\uC694.',
      method: "\uBAA8\uB4E0 \uB3C4\uAD6C\uC758 \uB3C4\uAD6C \uD638\uCD9C \uC218\uB97C \uC0AC\uB78C \uC694\uCCAD \uC218\uB85C \uB098\uB208 \uAC12\uC785\uB2C8\uB2E4.",
      evidence: "\uB3C4\uAD6C \uD638\uCD9C {toolCalls} \xB7 \uC0AC\uB78C \uC694\uCCAD {humanRequests}",
      unit: "\uD68C/\uC694\uCCAD",
      reasons: {
        no_data: { text: "\uC810\uC218 \uAD6C\uAC04\uC5D0 \uC0AC\uB78C \uC694\uCCAD\uC774 \uC5C6\uC2B5\uB2C8\uB2E4." },
        too_little: { text: "\uC0AC\uB78C \uC694\uCCAD\uC774 20\uAC1C\uC5D0 \uBABB \uBBF8\uCCD0 \uC7AC\uC9C0 \uC54A\uC558\uC2B5\uB2C8\uB2E4." }
      }
    }
  },
  I4: {
    en: {
      name: "Projects in use",
      good: "Uses the tools across several projects",
      why: "This counts the projects that had a main session in the scoring window. Using the tools in more places puts the setup you built to wider use.",
      fix: "Try the tools in more projects",
      problem: "Main sessions ran in {value}.",
      prescription: "Try the tools in another project or folder you work in, too.",
      method: "Number of projects with a main session in the scoring window, counted across tools. Folders not treated as projects, such as the home folder, are left out.",
      evidence: "Projects {projects} \xB7 folders left out {excludedFolders} \xB7 sessions not linked to a project {unlinkedSessions}",
      unit: "{value:project|projects}",
      reasons: { no_data: { text: "No project had a main session in the scoring window. Folders not treated as projects, such as the home folder, and sessions not linked to a project are not counted." } }
    },
    ko: {
      name: "\uC4F0\uB294 \uD3ED",
      good: "\uC5EC\uB7EC \uD504\uB85C\uC81D\uD2B8\uC5D0\uC11C \uC500",
      why: "\uC810\uC218 \uAD6C\uAC04\uC5D0 \uC8FC \uC138\uC158\uC774 \uC788\uC5C8\uB358 \uD504\uB85C\uC81D\uD2B8\uC758 \uC218\uC785\uB2C8\uB2E4. \uC5EC\uB7EC \uACF3\uC5D0\uC11C \uC4F0\uBA74 \uAC16\uCDB0 \uB454 \uC14B\uD305\uC744 \uADF8\uB9CC\uD07C \uB113\uAC8C \uC501\uB2C8\uB2E4.",
      fix: "\uB2E4\uB978 \uD504\uB85C\uC81D\uD2B8\uC5D0\uC11C\uB3C4 \uC368 \uBCF4\uAE30",
      problem: "\uC8FC \uC138\uC158\uC774 \uC788\uC5C8\uB358 \uD504\uB85C\uC81D\uD2B8\uAC00 {value}\uC785\uB2C8\uB2E4.",
      prescription: "\uC77C\uD558\uB294 \uB2E4\uB978 \uD504\uB85C\uC81D\uD2B8\uB098 \uD3F4\uB354\uC5D0\uC11C\uB3C4 \uC368 \uBCF4\uC138\uC694.",
      method: "\uC810\uC218 \uAD6C\uAC04\uC5D0 \uC8FC \uC138\uC158\uC774 \uC788\uC5C8\uB358 \uD504\uB85C\uC81D\uD2B8\uC758 \uC218\uC785\uB2C8\uB2E4. \uB3C4\uAD6C\uB97C \uD569\uCCD0 \uC138\uACE0, \uD648 \uD3F4\uB354\uCC98\uB7FC \uD504\uB85C\uC81D\uD2B8\uB85C \uBCF4\uC9C0 \uC54A\uB294 \uD3F4\uB354\uB294 \uBE8D\uB2C8\uB2E4.",
      evidence: "\uD504\uB85C\uC81D\uD2B8 {projects} \xB7 \uBE80 \uD3F4\uB354 {excludedFolders} \xB7 \uD504\uB85C\uC81D\uD2B8\uC5D0 \uC787\uC9C0 \uBABB\uD55C \uC138\uC158 {unlinkedSessions}",
      unit: "\uAC1C",
      reasons: { no_data: { text: "\uC810\uC218 \uAD6C\uAC04\uC5D0 \uC8FC \uC138\uC158\uC774 \uC788\uC5C8\uB358 \uD504\uB85C\uC81D\uD2B8\uAC00 \uC5C6\uC2B5\uB2C8\uB2E4. \uD648 \uD3F4\uB354\uCC98\uB7FC \uD504\uB85C\uC81D\uD2B8\uB85C \uBCF4\uC9C0 \uC54A\uB294 \uD3F4\uB354\uC640 \uD504\uB85C\uC81D\uD2B8\uC5D0 \uC787\uC9C0 \uBABB\uD55C \uC138\uC158\uC740 \uC138\uC9C0 \uC54A\uC2B5\uB2C8\uB2E4." } }
    }
  }
};

// src/core/copy/rules-setup.ts
var NO_TOOL = {
  en: { text: "No tool was used in the last 30 days, so this was not measured." },
  ko: { text: "\uCD5C\uADFC 30\uC77C \uC548\uC5D0 \uC4F4 \uB3C4\uAD6C\uAC00 \uC5C6\uC5B4 \uC7AC\uC9C0 \uC54A\uC558\uC2B5\uB2C8\uB2E4." }
};
var SETUP_COPY = {
  S1: {
    en: {
      name: "Global instructions",
      good: "Keeps instructions that load everywhere",
      why: "Global instructions load in every session, in every project. Writing your working style and rules there once means you do not repeat them in each project.",
      fix: "Write global instructions",
      problem: "{value} of the tools you use have global instructions.",
      prescription: "For Claude Code, write at least 200 bytes in CLAUDE.md in its config folder (~/.claude by default). A few lines on how you work and what to avoid are enough.",
      method: "Share of the tools you use that have global instructions (instruction files totaling 200 bytes or more).",
      evidence: "Tools with global instructions {withInstructions} \xB7 tools in use {tools}",
      unit: "%",
      reasons: { no_data: NO_TOOL.en }
    },
    ko: {
      name: "\uC804\uC5ED \uC9C0\uCE68",
      good: "\uC5B4\uB514\uC11C\uB098 \uC2E4\uB9AC\uB294 \uC804\uC5ED \uC9C0\uCE68\uC744 \uB460",
      why: "\uC804\uC5ED \uC9C0\uCE68\uC740 \uC5B4\uB290 \uD504\uB85C\uC81D\uD2B8\uC5D0\uC11C\uB4E0 \uC138\uC158\uB9C8\uB2E4 \uC2E4\uB9BD\uB2C8\uB2E4. \uC77C\uD558\uB294 \uBC29\uC2DD\uACFC \uC9C0\uD0AC \uADDC\uCE59\uC744 \uD55C\uACF3\uC5D0 \uC801\uC5B4 \uB450\uBA74 \uD504\uB85C\uC81D\uD2B8\uB9C8\uB2E4 \uB2E4\uC2DC \uC801\uC9C0 \uC54A\uC544\uB3C4 \uB429\uB2C8\uB2E4.",
      fix: "\uC804\uC5ED \uC9C0\uCE68 \uC4F0\uAE30",
      problem: "\uC4F0\uB294 \uB3C4\uAD6C \uAC00\uC6B4\uB370 \uC804\uC5ED \uC9C0\uCE68\uC774 \uC788\uB294 \uB3C4\uAD6C\uB294 {value}\uC785\uB2C8\uB2E4.",
      prescription: "Claude Code\uB294 \uC124\uC815 \uD3F4\uB354(\uAE30\uBCF8\uC740 ~/.claude)\uC758 CLAUDE.md\uC5D0 200\uBC14\uC774\uD2B8 \uC774\uC0C1 \uC801\uC2B5\uB2C8\uB2E4. \uC77C\uD558\uB294 \uBC29\uC2DD\uACFC \uD53C\uD560 \uAC83\uC744 \uBA87 \uC904 \uC801\uC73C\uBA74 \uB429\uB2C8\uB2E4.",
      method: "\uC4F0\uB294 \uB3C4\uAD6C \uAC00\uC6B4\uB370 \uC804\uC5ED \uC9C0\uCE68(\uC9C0\uCE68 \uD30C\uC77C\uC758 \uD06C\uAE30\uB97C \uD569\uCCD0 200\uBC14\uC774\uD2B8 \uC774\uC0C1)\uC774 \uC788\uB294 \uB3C4\uAD6C\uC758 \uBAAB\uC785\uB2C8\uB2E4.",
      evidence: "\uC804\uC5ED \uC9C0\uCE68\uC774 \uC788\uB294 \uB3C4\uAD6C {withInstructions} \xB7 \uC4F0\uB294 \uB3C4\uAD6C {tools}",
      unit: "%",
      reasons: { no_data: NO_TOOL.ko }
    }
  },
  S2: {
    en: {
      name: "Safeguard",
      good: "Has a safeguard on shell commands",
      why: "This looks at whether each tool has something that can stop a shell command you did not mean to run. In Claude Code that is permission checks in the default mode or a confirming hook that can block commands, in Codex it is asking for approval or a sandbox limit, and in Gemini CLI it is asking before each shell command or a sandbox. What a hook actually filters is not checked.",
      fix: "Add a safeguard on shell commands",
      problem: "{value} of the tools whose settings were read have a safeguard. A tool can run shell commands without asking first.",
      prescription: "Add a check before shell commands in each tool that has no safeguard.",
      prescriptionByTool: {
        "claude-code": "In Claude Code, add an enabled PreToolUse hook in your user settings that can block shell commands (Bash or PowerShell) before they run, or choose a default mode that does not bypass permissions. If you keep bypassing permissions, use the blocking hook.",
        codex: "In Codex, if you set the approval policy to never, do not give the sandbox full access (danger-full-access). If you need full access, set the approval policy to on-request. Both your user config.toml and the settings of trusted projects count.",
        gemini: "In Gemini CLI, take run_shell_command out of tools.allowed, or turn on the sandbox (tools.sandbox). Your user settings, the system settings, and the settings of trusted projects all count."
      },
      method: "Share of the tools whose settings were read that have a safeguard. Claude Code has one if its default mode does not bypass permissions, or if a PreToolUse hook that can block covers shell commands. Codex has one if no place (the user settings or a trusted project) combines no approval with full sandbox access. Gemini CLI has one if no place (the user and system settings or a trusted project) lets shell commands run without asking (run_shell_command in tools.allowed) while the sandbox is off. Approving everything (--yolo) is turned on only when Gemini CLI starts, so the settings cannot show it. A tool whose deciding settings could not be read is left out.",
      evidence: "Tools with a safeguard {guarded} \xB7 tools measured {tools} \xB7 tools left out with unreadable settings {unreadTools}",
      unit: "%",
      reasons: {
        no_data: NO_TOOL.en,
        unreadable: { text: "A settings file that decides the safeguard could not be read, so this was not measured." }
      }
    },
    ko: {
      name: "\uC548\uC804\uC7A5\uCE58",
      good: "\uC178 \uBA85\uB839\uC5D0 \uC548\uC804\uC7A5\uCE58\uB97C \uB460",
      why: "\uB3C4\uAD6C\uB9C8\uB2E4 \uB73B\uD558\uC9C0 \uC54A\uC740 \uC178 \uBA85\uB839\uC744 \uBA48\uCD9C \uC790\uB9AC\uAC00 \uC788\uB294\uC9C0 \uBD05\uB2C8\uB2E4. Claude Code\uB294 \uAE30\uBCF8 \uBAA8\uB4DC\uC758 \uAD8C\uD55C \uD655\uC778\uC774\uB098 \uC2E4\uD589\uC744 \uB9C9\uC744 \uC218 \uC788\uB294 \uD655\uC778 \uD6C5\uC774\uACE0, Codex\uB294 \uC2B9\uC778 \uC694\uCCAD\uC774\uB098 \uC0CC\uB4DC\uBC15\uC2A4 \uC81C\uD55C\uC774\uACE0, Gemini CLI\uB294 \uC178 \uBA85\uB839\uB9C8\uB2E4 \uBB3B\uB294 \uD655\uC778\uC774\uB098 \uC0CC\uB4DC\uBC15\uC2A4\uC785\uB2C8\uB2E4. \uD6C5\uC774 \uBB34\uC5C7\uC744 \uAC78\uB7EC \uB0B4\uB294\uC9C0\uB294 \uBCF4\uC9C0 \uC54A\uC2B5\uB2C8\uB2E4.",
      fix: "\uC178 \uBA85\uB839\uC5D0 \uC548\uC804\uC7A5\uCE58 \uB450\uAE30",
      problem: "\uC124\uC815\uC744 \uC77D\uC740 \uB3C4\uAD6C \uAC00\uC6B4\uB370 \uC548\uC804\uC7A5\uCE58\uAC00 \uC788\uB294 \uB3C4\uAD6C\uB294 {value}\uC785\uB2C8\uB2E4. \uBB3B\uC9C0 \uC54A\uACE0 \uC178 \uBA85\uB839\uC744 \uC2E4\uD589\uD560 \uC218 \uC788\uB294 \uB3C4\uAD6C\uAC00 \uC788\uC2B5\uB2C8\uB2E4.",
      prescription: "\uC548\uC804\uC7A5\uCE58\uAC00 \uC5C6\uB294 \uB3C4\uAD6C\uB9C8\uB2E4 \uC178 \uBA85\uB839 \uC55E\uC5D0 \uD655\uC778\uC744 \uB450\uC138\uC694.",
      prescriptionByTool: {
        "claude-code": "Claude Code\uC5D0\uC11C \uC178 \uBA85\uB839(Bash \uB610\uB294 PowerShell)\uC758 \uC2E4\uD589 \uC804\uC5D0 \uACB0\uACFC\uB97C \uAE30\uB2E4\uB9AC\uBA70 \uC2E4\uD589\uC744 \uB9C9\uC744 \uC218 \uC788\uB294 PreToolUse \uD6C5\uC744 \uC0AC\uC6A9\uC790 \uC124\uC815\uC5D0 \uB450\uACE0 \uCF1C\uAC70\uB098, \uAE30\uBCF8 \uBAA8\uB4DC\uB97C \uAD8C\uD55C \uC6B0\uD68C\uAC00 \uC544\uB2CC \uAC83\uC73C\uB85C \uBC14\uAFB8\uC138\uC694. \uAD8C\uD55C \uC6B0\uD68C \uBAA8\uB4DC\uB97C \uACC4\uC18D \uC4F0\uB824\uBA74 \uC2E4\uD589\uC744 \uB9C9\uC744 \uC218 \uC788\uB294 \uD655\uC778 \uD6C5\uC744 \uB450\uC138\uC694.",
        codex: "Codex\uC5D0\uC11C \uC2B9\uC778 \uC815\uCC45\uC744 never\uB85C \uB450\uB824\uBA74 \uC0CC\uB4DC\uBC15\uC2A4\uB97C \uC804\uBA74 \uD574\uC81C(danger-full-access)\uD558\uC9C0 \uB9C8\uC138\uC694. \uC804\uBA74 \uD574\uC81C\uAC00 \uD544\uC694\uD558\uBA74 \uC2B9\uC778 \uC815\uCC45\uC744 on-request\uB85C \uB450\uC138\uC694. \uC0AC\uC6A9\uC790 config.toml\uACFC \uC2E0\uB8B0\uD55C \uD504\uB85C\uC81D\uD2B8\uC758 \uC124\uC815\uC744 \uBAA8\uB450 \uBD05\uB2C8\uB2E4.",
        gemini: "Gemini CLI\uC5D0\uC11C tools.allowed\uC5D0\uC11C run_shell_command\uB97C \uBE7C\uAC70\uB098 \uC0CC\uB4DC\uBC15\uC2A4(tools.sandbox)\uB97C \uCF1C\uC138\uC694. \uC0AC\uC6A9\uC790 \uC124\uC815, \uC2DC\uC2A4\uD15C \uC124\uC815, \uC2E0\uB8B0\uD55C \uD504\uB85C\uC81D\uD2B8\uC758 \uC124\uC815\uC744 \uBAA8\uB450 \uBD05\uB2C8\uB2E4."
      },
      method: "\uC124\uC815\uC744 \uC77D\uC740 \uB3C4\uAD6C \uAC00\uC6B4\uB370 \uC548\uC804\uC7A5\uCE58\uAC00 \uC788\uB294 \uB3C4\uAD6C\uC758 \uBAAB\uC785\uB2C8\uB2E4. Claude Code\uB294 \uAE30\uBCF8 \uBAA8\uB4DC\uAC00 \uAD8C\uD55C \uC6B0\uD68C\uAC00 \uC544\uB2C8\uAC70\uB098, \uC178 \uBA85\uB839\uC5D0 \uAC78\uB9AC\uACE0 \uC2E4\uD589\uC744 \uB9C9\uC744 \uC218 \uC788\uB294 \uB3C4\uAD6C \uC2E4\uD589 \uC804 \uD655\uC778 \uD6C5\uC774 \uC788\uC73C\uBA74 \uC548\uC804\uC7A5\uCE58\uAC00 \uC788\uB294 \uAC83\uC73C\uB85C \uBD05\uB2C8\uB2E4. Codex\uB294 \uC0AC\uC6A9\uC790 \uC124\uC815\uACFC \uC2E0\uB8B0\uD55C \uD504\uB85C\uC81D\uD2B8 \uAC00\uC6B4\uB370 \uC2B9\uC778 \uC5C6\uC74C\uACFC \uC0CC\uB4DC\uBC15\uC2A4 \uC804\uBA74 \uD574\uC81C\uB97C \uD568\uAED8 \uC4F0\uB294 \uACF3\uC774 \uC5C6\uC73C\uBA74 \uC548\uC804\uC7A5\uCE58\uAC00 \uC788\uB294 \uAC83\uC73C\uB85C \uBD05\uB2C8\uB2E4. Gemini CLI\uB294 \uC0AC\uC6A9\uC790\xB7\uC2DC\uC2A4\uD15C \uC124\uC815\uACFC \uC2E0\uB8B0\uD55C \uD504\uB85C\uC81D\uD2B8 \uAC00\uC6B4\uB370 \uC178 \uBA85\uB839\uC744 \uBB3B\uC9C0 \uC54A\uACE0 \uC2E4\uD589\uD558\uAC8C \uB450\uBA74\uC11C(tools.allowed\uC758 run_shell_command) \uC0CC\uB4DC\uBC15\uC2A4\uB97C \uB048 \uACF3\uC774 \uC5C6\uC73C\uBA74 \uC548\uC804\uC7A5\uCE58\uAC00 \uC788\uB294 \uAC83\uC73C\uB85C \uBD05\uB2C8\uB2E4. \uBAA8\uB450 \uC790\uB3D9 \uC2B9\uC778(--yolo)\uC740 Gemini CLI\uB97C \uC2DC\uC791\uD560 \uB54C\uB9CC \uCF1C\uC838\uC11C \uC124\uC815\uC73C\uB85C\uB294 \uBCF4\uC9C0 \uBABB\uD569\uB2C8\uB2E4. \uC548\uC804\uC7A5\uCE58\uB97C \uC815\uD558\uB294 \uC124\uC815\uC744 \uC77D\uC9C0 \uBABB\uD55C \uB3C4\uAD6C\uB294 \uBE7C\uACE0 \uC7BD\uB2C8\uB2E4.",
      evidence: "\uC548\uC804\uC7A5\uCE58\uAC00 \uC788\uB294 \uB3C4\uAD6C {guarded} \xB7 \uC7B0 \uB3C4\uAD6C {tools} \xB7 \uC124\uC815\uC744 \uC77D\uC9C0 \uBABB\uD574 \uBE80 \uB3C4\uAD6C {unreadTools}",
      unit: "%",
      reasons: {
        no_data: NO_TOOL.ko,
        unreadable: { text: "\uC548\uC804\uC7A5\uCE58\uB97C \uC815\uD558\uB294 \uC124\uC815 \uD30C\uC77C \uAC00\uC6B4\uB370 \uC77D\uC9C0 \uBABB\uD55C \uAC83\uC774 \uC788\uC5B4 \uC7AC\uC9C0 \uC54A\uC558\uC2B5\uB2C8\uB2E4." }
      }
    }
  },
  S3: {
    en: {
      name: "Broken settings",
      good: "No broken user-editable settings found",
      why: "This checks settings-file syntax, skill headers, and link targets in the setup you edit yourself.",
      fix: "Fix broken settings",
      problem: "Found {value} in the settings checked.",
      prescription: "Fix the JSON in settings files that do not parse, add a header with name and description at the top of each SKILL.md, and remove links that point nowhere.",
      method: "Count of unparsable settings files, skills without a header, and links that point nowhere, in the setup you edit yourself. Files inside plugins and managed policy files are not counted.",
      evidence: "Unparsable settings files {unparsable} \xB7 skills without a header {noFrontmatter} \xB7 links that point nowhere {danglingLinks} \xB7 total {problems}",
      unit: "{value:problem|problems}"
    },
    ko: {
      name: "\uAE68\uC9C4 \uC124\uC815",
      good: "\uC9C1\uC811 \uACE0\uCE58\uB294 \uC124\uC815\uC5D0\uC11C \uBB38\uC81C\uB97C \uCC3E\uC9C0 \uBABB\uD568",
      why: "\uC9C1\uC811 \uACE0\uCE58\uB294 \uC124\uC815\uC5D0\uC11C \uC124\uC815 \uD30C\uC77C\uC758 \uD615\uC2DD, \uC2A4\uD0AC \uBA38\uB9AC\uB9D0, \uB9C1\uD06C \uB300\uC0C1\uC744 \uD655\uC778\uD569\uB2C8\uB2E4.",
      fix: "\uAE68\uC9C4 \uC124\uC815 \uACE0\uCE58\uAE30",
      problem: "\uC810\uAC80\uD55C \uC124\uC815\uC5D0\uC11C \uBB38\uC81C\uB97C {value} \uCC3E\uC558\uC2B5\uB2C8\uB2E4.",
      prescription: "\uD480\uB9AC\uC9C0 \uC54A\uB294 \uC124\uC815 \uD30C\uC77C\uC740 JSON \uAF34\uC744 \uBC14\uB85C\uC7A1\uACE0, \uC2A4\uD0AC\uC740 SKILL.md \uB9E8 \uC704\uC5D0 name\uACFC description\uC774 \uB4E0 \uBA38\uB9AC\uB9D0\uC744 \uB123\uACE0, \uAC00\uB9AC\uD0A4\uB294 \uACF3\uC774 \uC5C6\uB294 \uB9C1\uD06C\uB294 \uC9C0\uC6B0\uC138\uC694.",
      method: "\uC0AC\uC6A9\uC790\uAC00 \uC9C1\uC811 \uACE0\uCE58\uB294 \uC14B\uD305\uC5D0\uC11C \uD480\uB9AC\uC9C0 \uC54A\uB294 \uC124\uC815 \uD30C\uC77C, \uBA38\uB9AC\uB9D0\uC774 \uC5C6\uB294 \uC2A4\uD0AC, \uAC00\uB9AC\uD0A4\uB294 \uACF3\uC774 \uC5C6\uB294 \uB9C1\uD06C\uC758 \uC218\uC785\uB2C8\uB2E4. \uD50C\uB7EC\uADF8\uC778 \uC548\uC758 \uAC83\uACFC \uAD00\uB9AC \uC815\uCC45 \uD30C\uC77C\uC740 \uC138\uC9C0 \uC54A\uC2B5\uB2C8\uB2E4.",
      evidence: "\uD480\uB9AC\uC9C0 \uC54A\uB294 \uC124\uC815 \uD30C\uC77C {unparsable} \xB7 \uBA38\uB9AC\uB9D0\uC774 \uC5C6\uB294 \uC2A4\uD0AC {noFrontmatter} \xB7 \uAC00\uB9AC\uD0A4\uB294 \uACF3\uC774 \uC5C6\uB294 \uB9C1\uD06C {danglingLinks} \xB7 \uD569\uACC4 {problems}",
      unit: "\uAC1C"
    }
  },
  S4: {
    en: {
      name: "Hook failures",
      good: "Hooks rarely fail",
      why: "When a hook fails, the check or automation you gave it may not complete. This rule tracks the share of hook runs that failed.",
      fix: "Fix failing hooks",
      problem: "{value} of hook runs failed.",
      prescription: "Open /hooks to see the registered hooks, run the command of a failing hook in a terminal to find why it fails, and remove hooks you no longer use.",
      method: "Share of hook runs in the scoring window that failed. Blocks that could be on purpose or a failure are counted as neither a run nor a failure.",
      evidence: "Failures {failures} \xB7 runs {runs} \xB7 blocks not classified {unclassifiedBlocks}",
      unit: "%",
      reasons: {
        no_data: { text: "There were no hook runs to include in the failure rate. Blocks that may have been on purpose are not included." },
        too_little: { text: "Fewer than 100 hook runs to include in the failure rate, so this was not measured." }
      }
    },
    ko: {
      name: "\uD6C5 \uC2E4\uD328",
      good: "\uD6C5 \uC2E4\uD328\uAC00 \uB4DC\uBB3E",
      why: "\uD6C5\uC774 \uC2E4\uD328\uD558\uBA74 \uADF8 \uD6C5\uC5D0 \uB9E1\uAE34 \uD655\uC778\uC774\uB098 \uC790\uB3D9 \uC791\uC5C5\uC774 \uC81C\uB300\uB85C \uB418\uC9C0 \uC54A\uC744 \uC218 \uC788\uC2B5\uB2C8\uB2E4. \uC774 \uD56D\uBAA9\uC740 \uD6C5 \uC2E4\uD589 \uAC00\uC6B4\uB370 \uC2E4\uD328\uD55C \uBAAB\uC744 \uBD05\uB2C8\uB2E4.",
      fix: "\uC2E4\uD328\uD558\uB294 \uD6C5 \uACE0\uCE58\uAE30",
      problem: "\uD6C5 \uC2E4\uD589 \uAC00\uC6B4\uB370 {value}\uAC00 \uC2E4\uD328\uD588\uC2B5\uB2C8\uB2E4.",
      prescription: "/hooks\uC5D0\uC11C \uB4F1\uB85D\uB41C \uD6C5\uC744 \uBCF4\uACE0, \uC2E4\uD328\uD558\uB294 \uD6C5\uC758 \uBA85\uB839\uC744 \uD130\uBBF8\uB110\uC5D0\uC11C \uC9C1\uC811 \uB3CC\uB824 \uAE4C\uB2ED\uC744 \uCC3E\uC73C\uC138\uC694. \uB354 \uC4F0\uC9C0 \uC54A\uB294 \uD6C5\uC740 \uC9C0\uC6B0\uC138\uC694.",
      method: "\uC810\uC218 \uAD6C\uAC04\uC758 \uD6C5 \uC2E4\uD589 \uAC00\uC6B4\uB370 \uC2E4\uD328\uD55C \uBAAB\uC785\uB2C8\uB2E4. \uC77C\uBD80\uB7EC \uB9C9\uC740 \uAC83\uC778\uC9C0 \uC2E4\uD328\uD574\uC11C \uB9C9\uD78C \uAC83\uC778\uC9C0 \uAC00\uB9B4 \uC218 \uC5C6\uB294 \uB9C9\uC74C\uC740 \uC2E4\uD589\uC5D0\uB3C4 \uC2E4\uD328\uC5D0\uB3C4 \uB123\uC9C0 \uC54A\uC2B5\uB2C8\uB2E4.",
      evidence: "\uC2E4\uD328 {failures} \xB7 \uC2E4\uD589 {runs} \xB7 \uAC00\uB9AC\uC9C0 \uBABB\uD55C \uB9C9\uC74C {unclassifiedBlocks}",
      unit: "%",
      reasons: {
        no_data: { text: "\uC2E4\uD328\uC728\uC5D0 \uB123\uC744 \uD6C5 \uC2E4\uD589\uC774 \uC5C6\uC2B5\uB2C8\uB2E4. \uC77C\uBD80\uB7EC \uB9C9\uC740 \uAC83\uC778\uC9C0 \uAC00\uB9B4 \uC218 \uC5C6\uB294 \uB9C9\uC74C\uC740 \uB123\uC9C0 \uC54A\uC2B5\uB2C8\uB2E4." },
        too_little: { text: "\uC2E4\uD328\uC728\uC5D0 \uB123\uC744 \uD6C5 \uC2E4\uD589\uC774 100\uBC88\uC5D0 \uBABB \uBBF8\uCCD0 \uC7AC\uC9C0 \uC54A\uC558\uC2B5\uB2C8\uB2E4." }
      }
    }
  },
  S5: {
    en: {
      name: "MCP connection failures",
      good: "MCP connection failures are uncommon",
      why: "When a server connection fails, calls to its tools may fail until a connection succeeds.",
      fix: "Fix MCP servers that fail to connect",
      problem: "{value} of sessions had an MCP connection failure.",
      prescription: "Open /mcp to find the servers that fail to connect, then fix their settings or turn off the ones you do not use.",
      method: "Share of main sessions with responses in the scoring window that had a connection failure. Servers waiting for sign-in or still connecting are not failures.",
      evidence: "Sessions with a failure {failedSessions} \xB7 main sessions with responses {mainSessions} \xB7 servers turned on {enabledServers}",
      unit: "%",
      reasons: {
        not_applicable: { text: "No MCP server is turned on." },
        unreadable: { text: "A settings file that decides which servers are on, or a place where servers are defined, could not be read." },
        no_data: { text: "No main session had responses in the scoring window." }
      }
    },
    ko: {
      name: "MCP \uC5F0\uACB0 \uC2E4\uD328",
      good: "MCP \uC5F0\uACB0 \uC2E4\uD328\uAC00 \uB4DC\uBB3E",
      why: "\uC11C\uBC84 \uC5F0\uACB0\uC5D0 \uC2E4\uD328\uD558\uBA74 \uB2E4\uC2DC \uC5F0\uACB0\uB420 \uB54C\uAE4C\uC9C0 \uADF8 \uC11C\uBC84\uC758 \uB3C4\uAD6C \uD638\uCD9C\uB3C4 \uC2E4\uD328\uD560 \uC218 \uC788\uC2B5\uB2C8\uB2E4.",
      fix: "\uC5F0\uACB0\uC5D0 \uC2E4\uD328\uD558\uB294 MCP \uC11C\uBC84 \uACE0\uCE58\uAE30",
      problem: "\uC751\uB2F5\uC774 \uC788\uB294 \uC138\uC158 \uAC00\uC6B4\uB370 {value}\uC5D0\uC11C MCP \uC5F0\uACB0 \uC2E4\uD328\uAC00 \uC788\uC5C8\uC2B5\uB2C8\uB2E4.",
      prescription: "/mcp\uC5D0\uC11C \uC5F0\uACB0\uC5D0 \uC2E4\uD328\uD558\uB294 \uC11C\uBC84\uB97C \uCC3E\uC544 \uC124\uC815\uC744 \uACE0\uCE58\uAC70\uB098, \uC4F0\uC9C0 \uC54A\uB294 \uC11C\uBC84\uB294 \uAEBC \uB450\uC138\uC694.",
      method: "\uC810\uC218 \uAD6C\uAC04\uC5D0 \uC751\uB2F5\uC774 \uC788\uB294 \uC8FC \uC138\uC158 \uAC00\uC6B4\uB370 \uC5F0\uACB0 \uC2E4\uD328\uAC00 \uC788\uC5C8\uB358 \uC138\uC158\uC758 \uBAAB\uC785\uB2C8\uB2E4. \uC778\uC99D\uC744 \uAE30\uB2E4\uB9AC\uAC70\uB098 \uC5F0\uACB0\uD558\uB294 \uC911\uC778 \uC11C\uBC84\uB294 \uC2E4\uD328\uB85C \uC138\uC9C0 \uC54A\uC2B5\uB2C8\uB2E4.",
      evidence: "\uC2E4\uD328\uAC00 \uC788\uC5C8\uB358 \uC138\uC158 {failedSessions} \xB7 \uC751\uB2F5\uC774 \uC788\uB294 \uC8FC \uC138\uC158 {mainSessions} \xB7 \uCF1C\uC838 \uC788\uB294 \uC11C\uBC84 {enabledServers}",
      unit: "%",
      reasons: {
        not_applicable: { text: "\uCF1C\uC838 \uC788\uB294 MCP \uC11C\uBC84\uAC00 \uC5C6\uC2B5\uB2C8\uB2E4." },
        unreadable: { text: "\uC11C\uBC84\uC758 \uCF1C\uC9D0\uC744 \uC815\uD558\uB294 \uC124\uC815 \uD30C\uC77C\uC774\uB098 \uC11C\uBC84\uB97C \uCC3E\uB294 \uACF3 \uAC00\uC6B4\uB370 \uC77D\uC9C0 \uBABB\uD55C \uAC83\uC774 \uC788\uC2B5\uB2C8\uB2E4." },
        no_data: { text: "\uC810\uC218 \uAD6C\uAC04\uC5D0 \uC751\uB2F5\uC774 \uC788\uB294 \uC8FC \uC138\uC158\uC774 \uC5C6\uC2B5\uB2C8\uB2E4." }
      }
    }
  }
};

// src/core/copy/findings.ts
var RULE_COPY = { ...SETUP_COPY, ...EFFICIENCY_COPY, ...FIT_COPY, ...INTENSITY_COPY };
function joinValue(value, unit, lang) {
  return unit === "%" || lang === "ko" ? `${value}${unit}` : `${value} ${unit}`;
}
function fillEvidence(template, evidence, extra = {}) {
  return fill(template, { ...Object.fromEntries(slots(template).map((slot) => [slot, null])), ...evidence, ...extra });
}
function reasonOf(copy2, reason, lang) {
  const own = copy2.reasons?.[reason];
  const common = REASON_COPY[reason][lang];
  return { word: own?.word ?? common.word, text: own?.text ?? common.text };
}
function measured(kind, value, copy2, places) {
  const shown = formatValue(kind, value, places);
  return { value: shown, unit: fill(copy2.unit, { value: shown === "1" ? 1 : 0 }) };
}
function toolLine(kind, places, value, copy2, lang) {
  const tool = TOOL_NAMES[value.tool][lang];
  const evidence = fillEvidence(copy2.evidence, value.evidence);
  if (value.status === "scored") {
    const shown = measured(kind, value.value, copy2, places);
    return fill(TOOL_LINE[lang].measured, { tool, value: joinValue(shown.value, shown.unit, lang), evidence });
  }
  return fill(TOOL_LINE[lang].unmeasured, { tool, reason: reasonOf(copy2, value.reason, lang).word, evidence });
}
function reasonEvidence(finding) {
  if (finding.tools.length === 0) return finding.evidence;
  return finding.tools.find((value) => value.reason === finding.reason)?.evidence ?? {};
}
var candidateSources = (finding) => finding.tools.filter((value) => value.status === "unmeasured" && value.candidates.length > 0 && (value.reason === "too_little" || value.reason === "watching"));
function description(finding, copy2, lang, shown) {
  if (finding.category === "strength" || finding.category === "average") return copy2.why;
  if (finding.category === "unmeasured") return fillEvidence(reasonOf(copy2, finding.reason, lang).text, reasonEvidence(finding));
  const sources = candidateSources(finding);
  if (finding.status === "unmeasured") {
    const sentences = sources.map((value) => {
      const sentence = fillEvidence(copy2.repairUnmeasured?.[value.reason] ?? reasonOf(copy2, value.reason, lang).text, value.evidence, { candidates: value.candidates.length });
      return sources.length > 1 ? `${TOOL_NAMES[value.tool][lang]}: ${sentence}` : sentence;
    });
    return sentences.length > 0 ? sentences.join(" ") : fillEvidence(reasonOf(copy2, finding.reason, lang).text, reasonEvidence(finding));
  }
  const others = sources.map((value) => fillEvidence(OTHER_TOOL_COPY[value.reason][lang], value.evidence, { tool: TOOL_NAMES[value.tool][lang], candidates: value.candidates.length }));
  return [fill(copy2.problem, { value: joinValue(shown.value, shown.unit, lang) }), ...others].join(" ");
}
function safeguardCondition(safeguard, copy2) {
  const { guardHook, permissionChecks } = safeguard;
  if (guardHook === null || permissionChecks === null) return copy2.unknown;
  if (safeguard.tool === "codex") return permissionChecks ? copy2.codexGuarded : copy2.codexNone;
  if (safeguard.tool === "gemini") return permissionChecks ? copy2.geminiGuarded : copy2.geminiNone;
  return guardHook && permissionChecks ? copy2.both : guardHook ? copy2.hook : permissionChecks ? copy2.permissions : copy2.none;
}
function safeguardLine(safeguard, lang) {
  const copy2 = SAFEGUARD_COPY[lang];
  return fill(copy2.line, { tool: TOOL_NAMES[safeguard.tool][lang], condition: safeguardCondition(safeguard, copy2) });
}
function prescriptionOf(finding, copy2, details) {
  const byTool = copy2.prescriptionByTool;
  if (byTool === void 0) return copy2.prescription;
  const pointed = finding.ruleId === "S2" ? details.safeguards.filter((safeguard) => safeguard.guardHook === false && safeguard.permissionChecks === false).map((safeguard) => safeguard.tool) : finding.ruleId === "E6" ? finding.tools.filter((value) => value.candidates.length > 0).map((value) => value.tool) : [];
  const sentences = [...new Set(pointed)].sort().map((tool) => byTool[tool]).filter((sentence) => sentence !== void 0);
  return sentences.length > 0 ? sentences.join(" ") : copy2.prescription;
}
function measurementNotes(finding, details, lang) {
  if (finding.status !== "scored") return [];
  const used = ruleSpec(finding.ruleId).unit === "merged" ? details.mergedTools?.[finding.ruleId] ?? [] : finding.tools.filter((value) => value.status === "scored").map((value) => ({ tool: value.tool, observed: value.observed }));
  const lines = used.filter((item2) => item2.observed === "proxy").map((item2) => fill(PROXY_LINE[lang], { tool: TOOL_NAMES[item2.tool][lang] }));
  const usedTools = new Set(used.map((item2) => item2.tool));
  const modelGrain = ["claude-code", "gemini"].filter((tool) => usedTools.has(tool));
  if (finding.ruleId === "I3" && usedTools.has("codex") && modelGrain.length > 0) {
    lines.push(fill(TOOL_CALL_GRAIN[lang], { models: modelGrain.map((tool) => TOOL_NAMES[tool][lang]).join(TOOL_CALL_GRAIN_JOIN[lang]) }));
  }
  return lines;
}
var WHY_ORDER = ["no_definition", "plugin_unread", "not_established", "observation_incomplete"];
function unjudgedNotes(servers, lang) {
  if (servers.length === 0) return [];
  const copy2 = UNJUDGED_COPY[lang];
  const lines = [copy2.intro];
  for (const tool of [...new Set(servers.map((server) => server.tool))].sort()) {
    for (const why of WHY_ORDER) {
      const count = servers.filter((server) => server.tool === tool && server.why === why).length;
      if (count > 0) lines.push(fill(copy2.line, { tool: TOOL_NAMES[tool][lang], why: copy2.why[why], count }));
    }
  }
  if (servers.some((server) => server.scope === "claude-ai")) lines.push(copy2.deny);
  return lines;
}
function ruleValueText(ruleId, value, lang) {
  const spec = ruleSpec(ruleId);
  const shown = measured(spec.kind, value, RULE_COPY[ruleId][lang], rulePlaces(spec));
  return joinValue(shown.value, shown.unit, lang);
}
function findingText(finding, details, lang) {
  const copy2 = RULE_COPY[finding.ruleId][lang];
  const places = rulePlaces(ruleSpec(finding.ruleId));
  const shown = finding.status === "scored" ? measured(finding.kind, finding.value, copy2, places) : null;
  const method = [copy2.method];
  if (ruleSpec(finding.ruleId).unit === "merged") method.push(fillEvidence(copy2.evidence, finding.evidence));
  for (const value of finding.tools) method.push(toolLine(finding.kind, places, value, copy2, lang));
  if (finding.ruleId === "S2") for (const safeguard of details.safeguards) method.push(safeguardLine(safeguard, lang));
  method.push(...measurementNotes(finding, details, lang));
  return {
    name: copy2.name,
    title: finding.category === "strength" ? copy2.good : finding.category === "repair" ? copy2.fix : copy2.name,
    value: shown?.value ?? null,
    unit: shown?.unit ?? null,
    reason: finding.status === "unmeasured" ? reasonOf(copy2, finding.reason, lang).word : null,
    description: description(finding, copy2, lang, shown),
    prescription: finding.category === "average" || finding.category === "repair" ? prescriptionOf(finding, copy2, details) : null,
    method,
    notes: finding.ruleId === "E6" ? unjudgedNotes(details.unjudgedServers, lang) : []
  };
}

// src/core/copy/grades.ts
var GRADE_COPY = {
  5: {
    en: { name: "Graduation Day", diagnosis: "Your AQ is in the highest grade band. Check each item's result as well." },
    ko: { name: "\uBA85\uC138\uC11C \uC878\uC5C5\uC2DD", diagnosis: "AQ\uAC00 \uAC00\uC7A5 \uB192\uC740 \uB4F1\uAE09\uC785\uB2C8\uB2E4. \uD56D\uBAA9\uB9C8\uB2E4\uC758 \uACB0\uACFC\uB3C4 \uD568\uAED8 \uBCF4\uC138\uC694." }
  },
  4: {
    en: { name: "Stamp of Approval", diagnosis: "Your AQ is in a high grade band. Check each item's result as well." },
    ko: { name: "\uD569\uACA9 \uB3C4\uC7A5", diagnosis: "AQ\uAC00 \uB192\uC740 \uB4F1\uAE09\uC785\uB2C8\uB2E4. \uD56D\uBAA9\uB9C8\uB2E4\uC758 \uACB0\uACFC\uB3C4 \uD568\uAED8 \uBCF4\uC138\uC694." }
  },
  3: {
    en: { name: "Sleeves Up", diagnosis: "Let's go through the results item by item. If anything needs work, Chunsik will help fix it." },
    ko: { name: "\uD314 \uAC77\uACE0 \uC218\uB9AC", diagnosis: "\uC810\uAC80 \uACB0\uACFC\uB97C \uD56D\uBAA9\uB9C8\uB2E4 \uC0B4\uD3B4\uBD05\uC2DC\uB2E4. \uC190\uBCFC \uACF3\uC774 \uC788\uC73C\uBA74 \uCD98\uC2DD\uC774\uAC00 \uD568\uAED8 \uACE0\uCE69\uB2C8\uB2E4." }
  },
  2: {
    en: { name: "Who did this?", diagnosis: "Let's look at the checked items one by one. Chunsik will go through them with you." },
    ko: { name: "\uB204\uAC00 \uC774\uB7AC\uC5B4?", diagnosis: "\uC810\uAC80\uD55C \uD56D\uBAA9\uC744 \uD558\uB098\uC529 \uC0B4\uD3B4\uBD05\uC2DC\uB2E4. \uCD98\uC2DD\uC774\uAC00 \uD568\uAED8 \uD655\uC778\uD569\uB2C8\uB2E4." }
  },
  1: {
    en: { name: "Lightning Slash", diagnosis: "There is a lot to fix. Chunsik is starting right away." },
    ko: { name: "\uBC88\uAC1C \uBCA0\uAE30", diagnosis: "\uC190\uBCFC \uACF3\uC774 \uB9CE\uC2B5\uB2C8\uB2E4. \uCD98\uC2DD\uC774\uAC00 \uBC14\uB85C \uC2DC\uC791\uD569\uB2C8\uB2E4." }
  }
};
var WITHHELD_COPY = {
  en: { records: "There are not enough records for a score yet. Try another checkup after more use has been recorded.", noAxes: "No criterion could be measured, so there is no score.", webOnly: "Only web chats were used lately, so there is no score. Use Claude Code, Codex, or Gemini CLI and check again." },
  ko: { records: "\uC810\uC218\uB97C \uB0B4\uB294 \uB370 \uD544\uC694\uD55C \uAE30\uB85D\uC774 \uBD80\uC871\uD569\uB2C8\uB2E4. \uC0AC\uC6A9 \uAE30\uB85D\uC774 \uB354 \uC313\uC778 \uB4A4 \uB2E4\uC2DC \uC810\uAC80\uD574 \uBCF4\uC138\uC694.", noAxes: "\uC7B4 \uC218 \uC788\uB294 \uAE30\uC900\uC774 \uC5C6\uC5B4 \uC810\uC218\uB97C \uB0B4\uC9C0 \uBABB\uD588\uC2B5\uB2C8\uB2E4.", webOnly: "\uCD5C\uADFC\uC5D0\uB294 \uC6F9 \uCC44\uD305\uB9CC \uC368\uC11C \uC810\uC218\uB97C \uB0B4\uC9C0 \uC54A\uC558\uC2B5\uB2C8\uB2E4. Claude Code, Codex, Gemini CLI\uB97C \uC4F4 \uB4A4 \uB2E4\uC2DC \uC810\uAC80\uD574 \uBCF4\uC138\uC694." }
};
var EMPTY_COPY = {
  en: { strengths: "No clear strength was found yet. Let's start with the fixes, one at a time.", repairs: "Nothing needs fixing right now." },
  ko: { strengths: "\uC544\uC9C1 \uB69C\uB837\uD55C \uAC15\uC810\uC744 \uCC3E\uC9C0 \uBABB\uD588\uC2B5\uB2C8\uB2E4. \uACE0\uCE60 \uAC83\uBD80\uD130 \uD558\uB098\uC529 \uD574 \uBD05\uC2DC\uB2E4.", repairs: "\uC9C0\uAE08\uC740 \uACE0\uCE60 \uAC83\uC774 \uC5C6\uC2B5\uB2C8\uB2E4." }
};
function resultText(score, categories, lang) {
  const fewRecords = score.withheld.includes("too_few_requests") || score.withheld.includes("too_few_days");
  return {
    grade: score.tier === null ? null : GRADE_COPY[score.tier][lang].name,
    diagnosis: score.tier !== null ? GRADE_COPY[score.tier][lang].diagnosis : fewRecords ? WITHHELD_COPY[lang].records : score.withheld.includes("no_setup_tools") ? WITHHELD_COPY[lang].webOnly : WITHHELD_COPY[lang].noAxes,
    noStrengths: categories.includes("strength") ? null : EMPTY_COPY[lang].strengths,
    noRepairs: categories.includes("repair") ? null : EMPTY_COPY[lang].repairs
  };
}

// src/core/copy/next-grade.ts
var COPY2 = {
  en: {
    reaches: "{need} {need:point|points} to grade {grade}. Fix in this order: {steps}.",
    partial: "{need} {need:point|points} to grade {grade}. Fix in this order: {steps}. These alone reach {last}.",
    // 화살표와 숫자 사이는 보통 빈칸이다. 모델이 그대로 옮기기 쉽게 하고, 결과 화면이 둘을 묶어 떨어지지 않게 한다(0.3.0)
    step: "{name} (\u2192 {aq})",
    join: ", "
  },
  ko: {
    reaches: "{grade}\uB4F1\uAE09\uAE4C\uC9C0 {need}\uC810\uC785\uB2C8\uB2E4. \uACE0\uCE60 \uCC28\uB840: {steps}.",
    partial: "{grade}\uB4F1\uAE09\uAE4C\uC9C0 {need}\uC810\uC785\uB2C8\uB2E4. \uACE0\uCE60 \uCC28\uB840: {steps}. \uC774\uAC83\uB9CC\uC73C\uB85C\uB294 {last}\uC810\uC785\uB2C8\uB2E4.",
    step: "{name}(\u2192 {aq})",
    join: ", "
  }
};
function nextGradeText(next, nameOf, lang) {
  const copy2 = COPY2[lang];
  const steps = next.steps.map((step) => fill(copy2.step, { name: nameOf(step.ruleId), aq: step.aq })).join(copy2.join);
  return fill(next.reaches ? copy2.reaches : copy2.partial, { need: next.need, grade: next.grade, steps, last: next.steps.at(-1).aq });
}

// src/core/copy/notices.ts
var WITHHELD_COPY2 = {
  too_few_requests: { en: "There were fewer than 20 requests from you in the scoring window.", ko: "\uC810\uC218 \uAD6C\uAC04\uC758 \uC0AC\uB78C \uC694\uCCAD\uC774 20\uAC1C\uC5D0 \uBABB \uBBF8\uCE69\uB2C8\uB2E4." },
  too_few_days: { en: "The tools were used on fewer than 3 days in the scoring window.", ko: "\uC810\uC218 \uAD6C\uAC04\uC5D0 \uC4F4 \uB0A0\uC774 3\uC77C\uC5D0 \uBABB \uBBF8\uCE69\uB2C8\uB2E4." },
  no_axes: { en: "None of the four criteria could be measured.", ko: "\uC7B4 \uC218 \uC788\uB294 \uAE30\uC900\uC774 \uD558\uB098\uB3C4 \uC5C6\uC2B5\uB2C8\uB2E4." },
  no_setup_tools: { en: "Only web chats were used in the scoring window. The AQ needs use of Claude Code, Codex, or Gemini CLI, whose setup can be checked.", ko: "\uC810\uC218 \uAD6C\uAC04\uC5D0 \uC6F9 \uCC44\uD305\uB9CC \uC37C\uC2B5\uB2C8\uB2E4. AQ\uB294 \uC14B\uD305\uC744 \uBCFC \uC218 \uC788\uB294 Claude Code, Codex, Gemini CLI\uB97C \uC4F4 \uAE30\uB85D\uC774 \uC788\uC5B4\uC57C \uB0C5\uB2C8\uB2E4." }
};
var METRIC = {
  skills: { en: "skill use", ko: "\uC2A4\uD0AC \uC0AC\uC6A9" },
  mcp: { en: "MCP calls", ko: "MCP \uD638\uCD9C" }
};
var OBSERVATION_REASON = {
  "unreadable-files": { en: "unreadable files", ko: "\uC77D\uC9C0 \uBABB\uD55C \uD30C\uC77C" },
  "too-long-lines": { en: "lines too long", ko: "\uB108\uBB34 \uAE34 \uC904" },
  "unconfirmed-pieces": { en: "unconfirmed pieces", ko: "\uD655\uC778\uD558\uC9C0 \uBABB\uD55C \uC870\uAC01" },
  "not-recorded": { en: "not recorded by the tool", ko: "\uB3C4\uAD6C\uAC00 \uAE30\uB85D\uD558\uC9C0 \uC54A\uC74C" }
};
var UNREADABLE_SETUP = {
  claude_json: { en: ".claude.json", ko: ".claude.json" },
  user_settings: { en: "user settings", ko: "\uC0AC\uC6A9\uC790 \uC124\uC815" },
  managed_settings: { en: "managed policy", ko: "\uAD00\uB9AC \uC815\uCC45" },
  project_settings: { en: "project settings", ko: "\uD504\uB85C\uC81D\uD2B8 \uC124\uC815" },
  local_settings: { en: "local settings", ko: "\uB85C\uCEEC \uC124\uC815" },
  mcp_json: { en: "project .mcp.json", ko: "\uD504\uB85C\uC81D\uD2B8\uC758 .mcp.json" },
  plugins_file: { en: "plugin install records", ko: "\uD50C\uB7EC\uADF8\uC778 \uC124\uCE58 \uAE30\uB85D" },
  codex_config: { en: "config.toml", ko: "config.toml" },
  codex_project_config: { en: "project config.toml", ko: "\uD504\uB85C\uC81D\uD2B8\uC758 config.toml" },
  gemini_trusted_folders: { en: "trustedFolders.json", ko: "trustedFolders.json" },
  skill_dirs: { en: "skill folders", ko: "\uC2A4\uD0AC \uD3F4\uB354" },
  instructions: { en: "instruction files", ko: "\uC9C0\uCE68 \uD30C\uC77C" },
  hook_settings: { en: "settings with hooks", ko: "\uD6C5\uC744 \uC801\uC740 \uC124\uC815" },
  skill_files: { en: "SKILL.md files", ko: "SKILL.md" }
};
var UNCOUNTED2 = {
  composition_unknown: { en: "contents unknown", ko: "\uAD6C\uC131\uC744 \uBAA8\uB984" },
  not_installed: { en: "not in the install records", ko: "\uC124\uCE58 \uAE30\uB85D\uC5D0 \uC5C6\uC74C" },
  skills_unreadable: { en: "skill folder could not be read", ko: "\uC2A4\uD0AC \uD3F4\uB354\uB97C \uC77D\uC9C0 \uBABB\uD568" },
  mcp_unreadable: { en: "MCP definitions could not be read", ko: "MCP \uC815\uC758\uB97C \uC77D\uC9C0 \uBABB\uD568" },
  hooks_unreadable: { en: "hooks could not be read", ko: "\uD6C5\uC744 \uC77D\uC9C0 \uBABB\uD568" }
};
var UNCLASSIFIED_GROUPS = ["compaction", "denial", "hook", "thread_source", "item", "content"];
var UNCLASSIFIED = {
  compaction: { en: "{count} {count:compaction|compactions}", ko: "\uC555\uCD95 {count}\uAC1C" },
  denial: { en: "{count} {count:denial marker|denial markers}", ko: "\uAC70\uC808 \uD45C\uC2DC {count}\uAC1C" },
  hook: { en: "{count} {count:hook attachment|hook attachments}", ko: "\uD6C5 \uCCA8\uBD80 {count}\uAC1C" },
  thread_source: { en: "{count} {count:session|sessions} of unknown origin counted as main", ko: "\uC8FC \uC138\uC158\uC73C\uB85C \uC13C \uCD9C\uCC98 \uBAA8\uB97C \uC138\uC158 {count}\uAC1C" },
  item: { en: "{count} {count:work item|work items} of an unknown kind", ko: "\uC885\uB958\uB97C \uBAA8\uB974\uB294 \uC2E4\uD589 \uD56D\uBAA9 {count}\uAC1C" },
  // 웹 채팅 내보내기에서 꼴을 모르는 메시지(0.5.0). 꼴의 이름은 문장에 넣지 않는다
  content: { en: "{count} {count:message|messages} of an unknown shape", ko: "\uAF34\uC744 \uBAA8\uB974\uB294 \uBA54\uC2DC\uC9C0 {count}\uAC1C" }
};
var WEB_PROBLEM = {
  "not-file": { en: "not a file", ko: "\uD30C\uC77C\uC774 \uC544\uB2D8" },
  "no-conversations": { en: "no conversation file inside", ko: "\uC548\uC5D0 \uB300\uD654 \uD30C\uC77C\uC774 \uC5C6\uC74C" },
  "folder-too-large": { en: "the folder has too many items to look through", ko: "\uD3F4\uB354\uC758 \uD56D\uBAA9\uC774 \uB108\uBB34 \uB9CE\uC544 \uB2E4 \uBCF4\uC9C0 \uBABB\uD568" },
  "not-array": { en: "the conversation file is not a list", ko: "\uB300\uD654 \uD30C\uC77C\uC774 \uBAA9\uB85D\uC774 \uC544\uB2D8" },
  "unknown-service": { en: "not an export of this service", ko: "\uC774 \uC11C\uBE44\uC2A4\uC758 \uB0B4\uBCF4\uB0B4\uAE30\uAC00 \uC544\uB2D8" },
  zip: { en: "the zip could not be unpacked", ko: "zip\uC744 \uD480\uC9C0 \uBABB\uD568" },
  unreadable: { en: "the file could not be opened", ko: "\uD30C\uC77C\uC744 \uC5F4\uC9C0 \uBABB\uD568" }
};
var webProblem = (problem, lang) => (problem.startsWith("zip-") ? WEB_PROBLEM.zip : WEB_PROBLEM[problem] ?? WEB_PROBLEM.unreadable)[lang];
var TOP_ITEM_KINDS = 3;
var LINES = {
  en: {
    withheld: "No AQ was given. {reasons}",
    state_reset: "The state file was broken, so a new one was started. The record of watched installs builds up again from the start.",
    web_exports_reset: "The list of added web chat exports was broken, so web chats were left out. Add the export files again to count them.",
    web_export_missing: "{tool}: the export file you added is no longer there, so it was left out. Add the export file again to count it.",
    web_export_unreadable: "{tool}: the export file could not be read ({why}), so it was left out.",
    web_export_partial: "{tool}: {count} {count:conversation in the export was|conversations in the export were} left out (too large, broken, or of an unknown shape). Only what was read is counted.",
    webTruncated: "{tool}: the export could not be read to the end (the file ended early or the folder has too many items). Only what was read is counted.",
    web_export_until: "{tool}: the export has conversations up to {date}. Later days count as days without use. Export again and add the file to count them.",
    credentials_in_config: "{tool}: {count} {count:place in the settings has|places in the settings have} an API key or token written as it is. Move {count:it|them} into environment variables. The values were not shown or saved.",
    record_unreadable: "{tool}: {files} {files:file|files} and {dirs} {dirs:folder|folders} of records could not be read. Only what was read is counted.",
    record_skipped: "{tool}: {files} compressed record {files:file was|files were} skipped because this Node.js cannot unpack zstd. Node.js 22.15.0 or later on 22, 23.8.0 or later on 23, and any version from 24 read them.",
    record_partial: "{tool}: only the first part of {files} record {files:file|files} could be read. Only what was read is counted, so the unread share is at least what is shown.",
    observation_incomplete: "{tool}: the records of {metric} could not all be read ({reasons}), so unused ones were not judged.",
    setup_unreadable: "{tool}: some setup could not be read ({what}). Only what was read is counted.",
    setupCounted: "{tool}: some setup could not be read ({what}, {count} {count:place|places}). Only what was read is counted.",
    plugins_uncounted: "{tool}: {count} enabled {count:plugin has|plugins have} information that could not be fully inspected ({why}).",
    setup_problems_unscored: "{tool}: {count} {count:problem was|problems were} found in places that scores do not count (inside plugins, managed policy, files the tool writes).",
    projects_gone: "{count} {count:project|projects} whose folder is no longer on this PC {count:was|were} left out of the rules that look at instructions and settings.",
    version_unverified: "{tool}: the records include {count} {count:version|versions} outside the verified range ({from} to {to}). Only the fields that could be read are counted.",
    weak_human_requests: "{tool}: {weak} of {total} {total:request|requests} in the scoring window {weak:has|have} weak evidence of coming from a person.",
    overlapping_responses: "{tool}: {sessions} {sessions:session starts|sessions start} with responses that also appear in another session. The overlap was not removed from the counts.",
    unverified_inheritance: "{tool}: for {sessions} {sessions:session|sessions}, what was carried over from another record could not be confirmed, so the counts are approximate.",
    id_fallbacks: "{tool}: the session ID could not be taken from the first line of {count} {count:record|records}, so the file name stood in for it. A session may be split in two, or an earlier part counted again.",
    unclassified: "{tool}: some records could not be classified ({items}).",
    orphan_subsessions: "{tool}: {sessions} {sessions:subsession has|subsessions have} no known parent session.",
    parent_record_missing: "{tool}: the parent session's records were not found for {sessions} {sessions:subsession|subsessions}.",
    merged_sessions: "{tool}: {sessions} {sessions:session has|sessions have} more than one record file, counted as one session each.",
    unknown_mtime_sessions: "{tool}: {sessions} {sessions:session has|sessions have} a copy whose modification time could not be read. Copies with a known time were read first.",
    skipped_copies: "{tool}: {count} other {count:copy|copies} of the same records {count:was|were} not read. One copy of each record is read.",
    unnamed_files: "{tool}: {count} {count:file|files} in the records folder could not be recognized by name and {count:was|were} not read."
  },
  ko: {
    withheld: "AQ\uB97C \uB0B4\uC9C0 \uC54A\uC558\uC2B5\uB2C8\uB2E4. {reasons}",
    state_reset: "\uC0C1\uD0DC \uD30C\uC77C\uC774 \uAE68\uC838 \uC0C8\uB85C \uC2DC\uC791\uD588\uC2B5\uB2C8\uB2E4. \uC124\uCE58\uB97C \uC9C0\uCF1C\uBCF8 \uAE30\uB85D\uC774 \uCC98\uC74C\uBD80\uD130 \uB2E4\uC2DC \uC313\uC785\uB2C8\uB2E4.",
    web_exports_reset: "\uB123\uC740 \uC6F9 \uCC44\uD305 \uB0B4\uBCF4\uB0B4\uAE30\uC758 \uBAA9\uB85D\uC774 \uAE68\uC838 \uC6F9 \uCC44\uD305\uC744 \uBE7C\uACE0 \uC14C\uC2B5\uB2C8\uB2E4. \uB0B4\uBCF4\uB0B4\uAE30 \uD30C\uC77C\uC744 \uB2E4\uC2DC \uB123\uC73C\uBA74 \uC149\uB2C8\uB2E4.",
    web_export_missing: "{tool} \uB0B4\uBCF4\uB0B4\uAE30 \uD30C\uC77C\uC774 \uB123\uC740 \uC790\uB9AC\uC5D0 \uC5C6\uC5B4 \uC774\uBC88 \uC810\uAC80\uC5D0\uC11C \uBE90\uC2B5\uB2C8\uB2E4. \uB0B4\uBCF4\uB0B4\uAE30 \uD30C\uC77C\uC744 \uB2E4\uC2DC \uB123\uC73C\uBA74 \uC149\uB2C8\uB2E4.",
    web_export_unreadable: "{tool} \uB0B4\uBCF4\uB0B4\uAE30 \uD30C\uC77C\uC744 \uC77D\uC9C0 \uBABB\uD574({why}) \uC774\uBC88 \uC810\uAC80\uC5D0\uC11C \uBE90\uC2B5\uB2C8\uB2E4.",
    web_export_partial: "{tool} \uB0B4\uBCF4\uB0B4\uAE30\uC5D0\uC11C \uB300\uD654 {count}\uAC1C\uB97C \uBE7C\uACE0 \uC14C\uC2B5\uB2C8\uB2E4(\uB108\uBB34 \uD06C\uAC70\uB098 \uAE68\uC84C\uAC70\uB098 \uAF34\uC744 \uBAA8\uB984). \uC77D\uC740 \uAC83\uB9CC\uC73C\uB85C \uACC4\uC0B0\uD588\uC2B5\uB2C8\uB2E4.",
    webTruncated: "{tool} \uB0B4\uBCF4\uB0B4\uAE30\uB97C \uB05D\uAE4C\uC9C0 \uC77D\uC9C0 \uBABB\uD588\uC2B5\uB2C8\uB2E4(\uD30C\uC77C\uC774 \uC911\uAC04\uC5D0 \uB04A\uACBC\uAC70\uB098 \uD3F4\uB354\uC758 \uD56D\uBAA9\uC774 \uB108\uBB34 \uB9CE\uC74C). \uC77D\uC740 \uB300\uD654\uB9CC \uC14C\uC2B5\uB2C8\uB2E4.",
    web_export_until: "{tool} \uB0B4\uBCF4\uB0B4\uAE30\uC5D0\uB294 {date}\uAE4C\uC9C0\uC758 \uB300\uD654\uAC00 \uC788\uC2B5\uB2C8\uB2E4. \uADF8 \uB4A4\uC758 \uB0A0\uC740 \uC4F0\uC9C0 \uC54A\uC740 \uB0A0\uB85C \uC149\uB2C8\uB2E4. \uB2E4\uC2DC \uB0B4\uBCF4\uB0B4 \uB123\uC73C\uBA74 \uADF8 \uB4A4\uB3C4 \uC149\uB2C8\uB2E4.",
    credentials_in_config: "{tool} \uC124\uC815 {count}\uACF3\uC5D0 API \uD0A4\uB098 \uD1A0\uD070\uC774 \uADF8\uB300\uB85C \uC801\uD600 \uC788\uC2B5\uB2C8\uB2E4. \uD658\uACBD \uBCC0\uC218\uB85C \uC62E\uAE30\uC138\uC694. \uAC12\uC740 \uBCF4\uC5EC \uC8FC\uAC70\uB098 \uC800\uC7A5\uD558\uC9C0 \uC54A\uC558\uC2B5\uB2C8\uB2E4.",
    record_unreadable: "{tool} \uAE30\uB85D \uAC00\uC6B4\uB370 \uC77D\uC9C0 \uBABB\uD55C \uD30C\uC77C {files}\uAC1C\uC640 \uD3F4\uB354 {dirs}\uAC1C\uAC00 \uC788\uC2B5\uB2C8\uB2E4. \uC77D\uC740 \uAC83\uB9CC\uC73C\uB85C \uACC4\uC0B0\uD588\uC2B5\uB2C8\uB2E4.",
    record_skipped: "{tool} \uAE30\uB85D \uAC00\uC6B4\uB370 \uC774 Node.js\uAC00 zstd \uC555\uCD95\uC744 \uD480\uC9C0 \uBABB\uD574 \uAC74\uB108\uB6F4 \uD30C\uC77C\uC774 {files}\uAC1C \uC788\uC2B5\uB2C8\uB2E4. Node.js 22\uB294 22.15.0 \uC774\uC0C1, 23\uC740 23.8.0 \uC774\uC0C1, 24\uBD80\uD130\uB294 \uBAA8\uB4E0 \uBC84\uC804\uC5D0\uC11C \uC77D\uD799\uB2C8\uB2E4.",
    record_partial: "{tool} \uAE30\uB85D \uAC00\uC6B4\uB370 \uC55E\uBD80\uBD84\uB9CC \uC77D\uC740 \uD30C\uC77C\uC774 {files}\uAC1C \uC788\uC2B5\uB2C8\uB2E4. \uC77D\uC740 \uBD80\uBD84\uB9CC \uACC4\uC0B0\uD574\uC11C \uC77D\uC9C0 \uBABB\uD55C \uBE44\uC728\uC740 \uC801\uC5B4\uB3C4 \uBCF4\uC774\uB294 \uAC12\uC785\uB2C8\uB2E4.",
    observation_incomplete: "{tool}\uC758 {metric} \uAE30\uB85D\uC744 \uBE60\uC9D0\uC5C6\uC774 \uC77D\uC9C0 \uBABB\uD574({reasons}) \uC548 \uC4F0\uB294 \uAC83\uC744 \uD310\uC815\uD558\uC9C0 \uC54A\uC558\uC2B5\uB2C8\uB2E4.",
    setup_unreadable: "{tool}\uC5D0\uC11C \uC77D\uC9C0 \uBABB\uD55C \uC14B\uD305\uC774 \uC788\uC2B5\uB2C8\uB2E4({what}). \uC77D\uC740 \uAC83\uB9CC\uC73C\uB85C \uACC4\uC0B0\uD588\uC2B5\uB2C8\uB2E4.",
    setupCounted: "{tool}\uC5D0\uC11C \uC77D\uC9C0 \uBABB\uD55C \uC14B\uD305\uC774 \uC788\uC2B5\uB2C8\uB2E4({what} {count}\uACF3). \uC77D\uC740 \uAC83\uB9CC\uC73C\uB85C \uACC4\uC0B0\uD588\uC2B5\uB2C8\uB2E4.",
    plugins_uncounted: "{tool}\uC5D0\uC11C \uCF1C\uC838 \uC788\uB294 \uD50C\uB7EC\uADF8\uC778 {count}\uAC1C\uC5D0 \uD655\uC778\uD558\uC9C0 \uBABB\uD55C \uC815\uBCF4\uAC00 \uC788\uC2B5\uB2C8\uB2E4({why}).",
    setup_problems_unscored: "{tool}\uC5D0\uC11C \uC810\uC218\uC5D0 \uC138\uC9C0 \uC54A\uB294 \uACF3(\uD50C\uB7EC\uADF8\uC778 \uC548, \uAD00\uB9AC \uC815\uCC45, \uB3C4\uAD6C\uAC00 \uC4F0\uB294 \uD30C\uC77C)\uC5D0 \uBB38\uC81C\uAC00 {count}\uAC1C \uC788\uC2B5\uB2C8\uB2E4.",
    projects_gone: "\uC791\uC5C5 \uD3F4\uB354\uAC00 \uC9C0\uAE08 PC\uC5D0 \uC5C6\uB294 \uD504\uB85C\uC81D\uD2B8 {count}\uAC1C\uB294 \uC9C0\uCE68\uACFC \uC124\uC815\uC744 \uBCF4\uB294 \uADDC\uCE59\uC5D0\uC11C \uBE90\uC2B5\uB2C8\uB2E4.",
    version_unverified: "{tool} \uAE30\uB85D\uC5D0 \uD655\uC778\uD55C \uBC94\uC704({from}~{to}) \uBC16\uC758 \uBC84\uC804\uC774 {count}\uAC1C \uC788\uC2B5\uB2C8\uB2E4. \uC77D\uC744 \uC218 \uC788\uB294 \uD544\uB4DC\uB9CC\uC73C\uB85C \uACC4\uC0B0\uD588\uC2B5\uB2C8\uB2E4.",
    weak_human_requests: "{tool}\uC758 \uC810\uC218 \uAD6C\uAC04 \uC0AC\uB78C \uC694\uCCAD {total}\uAC1C \uAC00\uC6B4\uB370 {weak}\uAC1C\uB294 \uC0AC\uB78C\uC774 \uBCF4\uB0C8\uB2E4\uB294 \uADFC\uAC70\uAC00 \uC57D\uD569\uB2C8\uB2E4.",
    overlapping_responses: "{tool}\uC5D0\uC11C \uCC98\uC74C \uB098\uC628 \uC751\uB2F5\uC774 \uB2E4\uB978 \uC138\uC158\uACFC \uACB9\uCE58\uB294 \uC138\uC158\uC774 {sessions}\uAC1C \uC788\uC2B5\uB2C8\uB2E4. \uACB9\uCE5C \uC751\uB2F5\uC744 \uBE7C\uC9C0 \uC54A\uACE0 \uC14C\uC2B5\uB2C8\uB2E4.",
    unverified_inheritance: "{tool}\uC5D0\uC11C \uB2E4\uB978 \uAE30\uB85D\uC5D0\uC11C \uC774\uC5B4\uBC1B\uC740 \uC55E\uBD80\uBD84\uC744 \uD655\uC778\uD558\uC9C0 \uBABB\uD55C \uC138\uC158\uC774 {sessions}\uAC1C \uC788\uC2B5\uB2C8\uB2E4. \uADF8 \uC22B\uC790\uB294 \uAC00\uAE4C\uC6B4 \uAC12\uC785\uB2C8\uB2E4.",
    id_fallbacks: "{tool} \uAE30\uB85D \uAC00\uC6B4\uB370 \uCCAB \uC904\uC5D0\uC11C \uC138\uC158 ID\uB97C \uC5BB\uC9C0 \uBABB\uD574 \uD30C\uC77C \uC774\uB984\uC73C\uB85C \uC138\uC158\uC744 \uAC00\uB978 \uAC83\uC774 {count}\uAC1C \uC788\uC2B5\uB2C8\uB2E4. \uAC19\uC740 \uC138\uC158\uC774 \uB458\uB85C \uB098\uB258\uAC70\uB098 \uC55E\uBD80\uBD84\uC744 \uB2E4\uC2DC \uC14C\uC744 \uC218 \uC788\uC2B5\uB2C8\uB2E4.",
    unclassified: "{tool}\uC5D0 \uBD84\uB958\uD558\uC9C0 \uBABB\uD55C \uAE30\uB85D\uC774 \uC788\uC2B5\uB2C8\uB2E4({items}).",
    orphan_subsessions: "{tool}\uC5D0 \uBD80\uBAA8 \uC138\uC158\uC744 \uBAA8\uB974\uB294 \uD558\uC704 \uC138\uC158\uC774 {sessions}\uAC1C \uC788\uC2B5\uB2C8\uB2E4.",
    parent_record_missing: "{tool}\uC5D0 \uBD80\uBAA8 \uC138\uC158\uC758 \uAE30\uB85D\uC744 \uCC3E\uC9C0 \uBABB\uD55C \uD558\uC704 \uC138\uC158\uC774 {sessions}\uAC1C \uC788\uC2B5\uB2C8\uB2E4.",
    merged_sessions: "{tool}\uC5D0\uC11C \uAE30\uB85D \uD30C\uC77C\uC774 \uB458 \uC774\uC0C1\uC778 \uC138\uC158 {sessions}\uAC1C\uB294 \uC138\uC158 \uD558\uB098\uC529\uC73C\uB85C \uD569\uCCD0 \uC14C\uC2B5\uB2C8\uB2E4.",
    unknown_mtime_sessions: "{tool}\uC5D0\uC11C \uC218\uC815 \uC2DC\uAC01\uC744 \uBCF4\uC9C0 \uBABB\uD55C \uC0AC\uBCF8\uC774 \uC788\uB294 \uC138\uC158\uC774 {sessions}\uAC1C \uC788\uC2B5\uB2C8\uB2E4. \uC218\uC815 \uC2DC\uAC01\uC744 \uC544\uB294 \uC0AC\uBCF8\uC744 \uBA3C\uC800 \uC77D\uC5C8\uC2B5\uB2C8\uB2E4.",
    skipped_copies: "{tool}\uC5D0\uC11C \uAC19\uC740 \uAE30\uB85D\uC758 \uB2E4\uB978 \uC0AC\uBCF8 {count}\uAC1C\uB294 \uC77D\uC9C0 \uC54A\uC558\uC2B5\uB2C8\uB2E4. \uAE30\uB85D\uB9C8\uB2E4 \uC0AC\uBCF8 \uD558\uB098\uB9CC \uC77D\uC2B5\uB2C8\uB2E4.",
    unnamed_files: "{tool} \uAE30\uB85D \uD3F4\uB354\uC5D0\uC11C \uC774\uB984\uC73C\uB85C \uAE30\uB85D\uC744 \uC54C\uC544\uBCFC \uC218 \uC5C6\uB294 \uD30C\uC77C {count}\uAC1C\uB294 \uC77D\uC9C0 \uC54A\uC558\uC2B5\uB2C8\uB2E4."
  }
};
var LIST_JOIN = ", ";
function unclassifiedItems(counts, lang) {
  const groups = UNCLASSIFIED_GROUPS.map((group) => ({ group, count: counts.filter((item2) => item2.what.split(":")[0] === group).reduce((sum2, item2) => sum2 + item2.count, 0) }));
  return groups.filter((item2) => item2.count > 0).map((item2) => {
    const text = fill(UNCLASSIFIED[item2.group][lang], { count: item2.count });
    if (item2.group !== "item") return text;
    const kinds = counts.filter((entry) => entry.what.startsWith("item:")).map((entry) => ({ name: entry.what.slice("item:".length), count: entry.count })).sort((a, b) => b.count - a.count || (a.name < b.name ? -1 : a.name > b.name ? 1 : 0)).slice(0, TOP_ITEM_KINDS);
    return `${text} [${kinds.map((kind) => `${kind.name} ${fill("{count}", { count: kind.count })}`).join(" \xB7 ")}]`;
  }).join(LIST_JOIN);
}
function noticeText(notice, lang) {
  const lines = LINES[lang];
  const tool = "tool" in notice ? TOOL_NAMES[notice.tool][lang] : "";
  switch (notice.kind) {
    case "score_withheld":
      return fill(lines.withheld, { reasons: notice.reasons.map((reason) => WITHHELD_COPY2[reason][lang]).join(" ") });
    case "state_reset":
      return lines.state_reset;
    case "web_exports_reset":
      return lines.web_exports_reset;
    case "web_export_missing":
      return fill(lines.web_export_missing, { tool });
    case "web_export_unreadable":
      return fill(lines.web_export_unreadable, { tool, why: webProblem(notice.problem, lang) });
    case "web_export_partial": {
      const parts = [notice.skipped > 0 ? fill(lines.web_export_partial, { tool, count: notice.skipped }) : null, notice.truncated ? fill(lines.webTruncated, { tool }) : null];
      return parts.filter((part) => part !== null).join(" ");
    }
    case "web_export_until":
      return fill(lines.web_export_until, { tool, date: notice.lastDate });
    case "credentials_in_config":
      return fill(lines.credentials_in_config, { tool, count: notice.places.length });
    case "record_unreadable":
      return fill(lines.record_unreadable, { tool, files: notice.files.length, dirs: notice.dirs.length });
    case "record_skipped":
    case "record_partial":
      return fill(lines[notice.kind], { tool, files: notice.files.length });
    case "observation_incomplete":
      return fill(lines.observation_incomplete, { tool, metric: METRIC[notice.metric][lang], reasons: notice.reasons.map((reason) => OBSERVATION_REASON[reason][lang]).join(LIST_JOIN) });
    case "setup_unreadable": {
      const what = UNREADABLE_SETUP[notice.what][lang];
      return notice.targets.length > 0 ? fill(lines.setupCounted, { tool, what, count: notice.targets.length }) : fill(lines.setup_unreadable, { tool, what });
    }
    case "plugins_uncounted":
      return fill(lines.plugins_uncounted, { tool, count: notice.plugins.length, why: UNCOUNTED2[notice.why][lang] });
    case "setup_problems_unscored":
      return fill(lines.setup_problems_unscored, { tool, count: notice.problems.length });
    case "projects_gone":
      return fill(lines.projects_gone, { count: notice.projects.length });
    case "version_unverified":
      return fill(lines.version_unverified, { tool, count: notice.versions.length, from: notice.verified.from, to: notice.verified.to });
    case "weak_human_requests":
      return fill(lines.weak_human_requests, { tool, weak: notice.weak, total: notice.total });
    case "overlapping_responses":
    case "unverified_inheritance":
    case "parent_record_missing":
    case "merged_sessions":
    case "unknown_mtime_sessions":
      return fill(lines[notice.kind], { tool, sessions: notice.sessions });
    case "id_fallbacks":
      return fill(lines.id_fallbacks, { tool, count: notice.counts.reduce((sum2, item2) => sum2 + item2.count, 0) });
    case "unclassified":
      return fill(lines.unclassified, { tool, items: unclassifiedItems(notice.counts, lang) });
    case "orphan_subsessions":
      return fill(lines.orphan_subsessions, { tool, sessions: notice.sessions });
    case "skipped_copies":
    case "unnamed_files":
      return fill(lines[notice.kind], { tool, count: notice.count });
  }
}

// src/core/next-grade.ts
var NEXT_GRADE_STEPS = 5;
var NEXT = { D: { grade: "C", at: 50 }, C: { grade: "B", at: 65 }, B: { grade: "A", at: 80 }, A: { grade: "S", at: 90 } };
function totals(rules, fixed2) {
  const rounded = [];
  let raw = 0;
  for (const axis of AXES) {
    const own = rules.filter((rule2) => rule2.axis === axis).map((rule2) => ({ weight: rule2.weight, score: fixed2.has(rule2.ruleId) ? 1 : rule2.score }));
    const score = axisScore(own);
    if (score === null) continue;
    rounded.push(score);
    const measured2 = own.filter((rule2) => rule2.score !== null);
    raw += measured2.reduce((sum2, rule2) => sum2 + rule2.weight * rule2.score, 0) / measured2.reduce((sum2, rule2) => sum2 + rule2.weight, 0) * 100;
  }
  return { rounded, raw };
}
function nextGrade(rules, score, exclude = /* @__PURE__ */ new Set()) {
  if (score.aq === null || score.grade === null || score.grade === "S") return null;
  const target = NEXT[score.grade];
  const candidates = rules.filter((rule2) => rule2.score !== null && settleScore(rule2.score) < 1 && !exclude.has(rule2.ruleId));
  const fixed2 = /* @__PURE__ */ new Set();
  const steps = [];
  while (steps.length < NEXT_GRADE_STEPS && (steps.at(-1)?.aq ?? score.aq) < target.at) {
    let best = null;
    for (const rule2 of candidates) {
      if (fixed2.has(rule2.ruleId)) continue;
      const after = totals(rules, /* @__PURE__ */ new Set([...fixed2, rule2.ruleId]));
      const rounded = after.rounded.reduce((sum2, value) => sum2 + value, 0);
      const better = best === null || rounded > best.rounded || rounded === best.rounded && (after.raw > best.raw + 1e-9 || Math.abs(after.raw - best.raw) <= 1e-9 && (rule2.gain ?? -1) > (best.rule.gain ?? -1));
      if (better) best = { rule: rule2, rounded, raw: after.raw };
    }
    if (best === null) break;
    fixed2.add(best.rule.ruleId);
    const aq = aqOfAxes(totals(rules, fixed2).rounded);
    steps.push({ ruleId: best.rule.ruleId, axis: best.rule.axis, aq, grade: gradeOf(aq).grade });
  }
  if (steps.length === 0) return null;
  return { grade: target.grade, need: target.at - score.aq, steps, reaches: steps.at(-1).aq >= target.at };
}

// src/core/result/coverage.ts
var PARTIAL_READ_SHARE = 0.2;
function resultCoverage(input, collected) {
  const tools2 = [...input.tools].sort((a, b) => a.tool < b.tool ? -1 : a.tool > b.tool ? 1 : 0);
  return tools2.map((tool) => {
    const found = collected.find((item2) => item2.tool === tool.tool);
    if (found === void 0) throw new Error(`no collected result for ${tool.tool}`);
    const { read } = found;
    const sum2 = (pick) => tool.summaries.reduce((total, summary) => total + pick(summary.missing), 0);
    const skipped = found.codex?.skippedFiles.length ?? 0;
    const skippedBytes = found.codex?.skippedFileBytes ?? 0;
    const partialFiles = found.codex?.partialFiles.length ?? 0;
    const shares = [read.files > 0 ? (read.unreadableFiles.length + skipped) / read.files : null, read.listedBytes > 0 ? (read.unreadableFileBytes + skippedBytes) / read.listedBytes : null].filter(
      (share2) => share2 !== null
    );
    const unreadableShare = shares.length === 0 ? null : Math.max(...shares);
    const lowerBound = read.unreadableDirs.length > 0 || read.unknownSizeFiles > 0 || partialFiles > 0;
    return {
      tool: tool.tool,
      files: read.files,
      listedBytes: read.listedBytes,
      readBytes: read.bytes,
      olderThanWindow: read.olderThanWindow,
      inProgress: read.inProgress,
      unreadableFiles: read.unreadableFiles.length,
      unreadableDirs: read.unreadableDirs.length,
      unknownSizeFiles: read.unknownSizeFiles,
      partialFiles,
      skippedFiles: skipped,
      brokenLines: sum2((missing) => missing.brokenLines),
      tooLongLines: sum2((missing) => missing.tooLongLines),
      tailFragments: sum2((missing) => missing.tailFragments),
      unreadableShare,
      lowerBound,
      partial: lowerBound || unreadableShare !== null && unreadableShare > PARTIAL_READ_SHARE,
      observation: found.observation
    };
  });
}

// src/core/result/hints.ts
var MENTION_HINT_MIN = 3;
var REPEATED_LINES_HINT_MIN = 3;
var LARGE_GLOBAL_TOKENS = ruleSpec("E4").fullAt;
var byText8 = (a, b) => a < b ? -1 : a > b ? 1 : 0;
function hintSetup(tool, input) {
  if (tool.tool === "claude-code") {
    const { setup: setup2 } = tool;
    return {
      globalInstructions: setup2.globalInstructions,
      globalMentions: setup2.globalMentions,
      projects: setup2.projects.filter((item2) => item2.exists && !item2.excluded).map((project) => ({ root: project.root, instructions: project.instructions })),
      rootOf: new Map(setup2.projects.map((project) => [project.normRoot, project.root]))
    };
  }
  const rootOf = new Map(input.projects.map((project) => [project.normRoot, project.root]));
  const { setup } = tool;
  return {
    globalInstructions: setup.globalInstructions,
    globalMentions: setup.globalMentions,
    projects: setup.projects.filter((project) => project.scanned).map((project) => ({ root: rootOf.get(project.normRoot) ?? project.normRoot, instructions: project.instructions })),
    rootOf
  };
}
function toolHints(tool, setup) {
  const hints = [];
  const mentioned = Object.entries(setup.globalMentions).filter(([, count]) => count >= MENTION_HINT_MIN).map(([normRoot, count]) => ({ root: setup.rootOf.get(normRoot) ?? normRoot, mentions: count })).sort((a, b) => byText8(a.root, b.root));
  if (mentioned.length > 0) hints.push({ kind: "global_mentions_project", tool, projects: mentioned });
  const global = new Set(setup.globalInstructions.lineHashes);
  const seen = /* @__PURE__ */ new Map();
  for (const project of setup.projects) {
    for (const hash of new Set(project.instructions.lineHashes)) {
      if (global.has(hash)) continue;
      seen.set(hash, [...seen.get(hash) ?? [], project.root]);
    }
  }
  const repeated = [...seen.values()].filter((roots) => roots.length >= 2);
  if (repeated.length >= REPEATED_LINES_HINT_MIN) hints.push({ kind: "repeated_project_lines", tool, lines: repeated.length, projects: [...new Set(repeated.flat())].sort(byText8) });
  const { ascii, other } = setup.globalInstructions.chars;
  const tokens = ascii / 4 + other;
  if (tokens > LARGE_GLOBAL_TOKENS) hints.push({ kind: "large_global_instructions", tool, tokens });
  return hints;
}
function toolsDiffer(claude, codex) {
  if (claude.lineHashes.length === 0 || codex.lineHashes.length === 0) return null;
  const codexReal = new Set(codex.files.map((file) => file.realPath).filter((realPath) => realPath !== null));
  if (claude.files.some((file) => file.realPath !== null && codexReal.has(file.realPath))) return null;
  const codexLines = new Set(codex.lineHashes);
  const shared = claude.lineHashes.filter((hash) => codexLines.has(hash)).length;
  const fewer = Math.min(claude.lineHashes.length, codex.lineHashes.length);
  return shared * 2 < fewer ? { kind: "tools_instructions_differ", shared, lines: { "claude-code": claude.lineHashes.length, codex: codex.lineHashes.length } } : null;
}
function deepHints(input) {
  const tools2 = setupTools(input.tools).sort((a, b) => byText8(a.tool, b.tool));
  const hints = tools2.flatMap((tool) => toolHints(tool.tool, hintSetup(tool, input)));
  const claude = tools2.find((tool) => tool.tool === "claude-code");
  const codex = tools2.find((tool) => tool.tool === "codex");
  const differ = claude === void 0 || codex === void 0 ? null : toolsDiffer(claude.setup.globalInstructions, codex.setup.globalInstructions);
  if (differ !== null) hints.push(differ);
  return hints;
}
function deepFiles(input) {
  const files = [];
  const seen = /* @__PURE__ */ new Set();
  const add = (file, entry) => {
    const key = file.realPath ?? file.path;
    if (!file.hasContent || seen.has(key)) return;
    seen.add(key);
    files.push({ ...entry, path: file.path, bytes: file.bytes });
  };
  for (const tool of setupTools(input.tools).sort((a, b) => byText8(a.tool, b.tool))) {
    const setup = hintSetup(tool, input);
    for (const file of setup.globalInstructions.files) add(file, { tool: tool.tool, scope: "global", project: null, selected: true });
    for (const project of setup.projects) for (const file of project.instructions.files) if (!file.sameAsGlobal) add(file, { tool: tool.tool, scope: "project", project: project.root, selected: false });
  }
  return files;
}

// src/core/result/notices.ts
var VERIFIED_VERSIONS = {
  "claude-code": { from: "2.1.220", to: "2.1.322" },
  codex: { from: "0.140.0", to: "0.169.0" },
  // 제미나이 CLI는 세션 기록에 버전을 적지 않아 이 범위로 견줄 버전이 없다. 해석 규약은 공개 소스 v0.68.0으로 확인했다(설계 「0.4.0에서 정한 것」)
  gemini: { from: "0.68.0", to: "0.68.0" },
  "web-chatgpt": null,
  "web-claude": null
};
var WEAK_REQUEST_SHARE = 0.1;
var NOTICE_KINDS = [
  "score_withheld",
  "state_reset",
  "web_exports_reset",
  "credentials_in_config",
  "record_unreadable",
  "record_skipped",
  "record_partial",
  "web_export_missing",
  "web_export_unreadable",
  "web_export_partial",
  "observation_incomplete",
  "setup_unreadable",
  "plugins_uncounted",
  "setup_problems_unscored",
  "projects_gone",
  "web_export_until",
  "version_unverified",
  "weak_human_requests",
  "overlapping_responses",
  "unverified_inheritance",
  "id_fallbacks",
  "unclassified",
  "orphan_subsessions",
  "parent_record_missing",
  "merged_sessions",
  "unknown_mtime_sessions",
  "skipped_copies",
  "unnamed_files"
];
var byText9 = (a, b) => a < b ? -1 : a > b ? 1 : 0;
var inRange = (date, range) => date >= range.from && date <= range.to;
var toolOf = (notice) => "tool" in notice ? notice.tool : "";
function sortNotices(notices2) {
  return notices2.map((notice, index) => ({ notice, index })).sort((a, b) => NOTICE_KINDS.indexOf(a.notice.kind) - NOTICE_KINDS.indexOf(b.notice.kind) || byText9(toolOf(a.notice), toolOf(b.notice)) || a.index - b.index).map((item2) => item2.notice);
}
var unread2 = (status) => status === "unparsable" || status === "unreadable";
var sortedUnique = (values) => [...new Set(values)].sort(byText9);
function unscoredProblems(tool, problems) {
  const unscored = problems.filter((problem) => problem.owner === "plugin" || problem.owner === "managed").map((problem) => ({ kind: problem.kind, path: problem.path }));
  return unscored.length > 0 ? [{ kind: "setup_problems_unscored", tool, problems: unscored.sort((a, b) => byText9(a.path, b.path) || byText9(a.kind, b.kind)) }] : [];
}
function codexSetupNotices(setup, projects) {
  const notices2 = [];
  const rootOf = new Map(projects.map((project) => [project.normRoot, project.root]));
  const unreadable = [
    ["codex_config", unread2(setup.config), []],
    ["codex_project_config", false, setup.projects.filter((project) => project.trust === "trusted" && unread2(project.configStatus)).map((project) => rootOf.get(project.normRoot) ?? project.normRoot)],
    ["skill_dirs", false, setup.unreadableDirs],
    ["instructions", false, [setup.globalInstructions, ...setup.projects.map((project) => project.instructions)].flatMap((set) => [...set.unreadable, ...set.unreadableDirs])],
    ["skill_files", false, setup.skills.filter((skill) => !skill.readable).map((skill) => skill.path)]
  ];
  for (const [what, whole, targets] of unreadable) {
    if (whole || targets.length > 0) notices2.push({ kind: "setup_unreadable", tool: "codex", what, targets: sortedUnique(targets) });
  }
  const enabledIds = new Set(setup.plugins.filter((plugin) => plugin.enabled).map((plugin) => plugin.id));
  const uncounted = [
    // 설정으로 켰는데 놓인 곳이나 매니페스트를 읽지 못했거나 Agent Plugins 형식이라 구성을 모르는 것(설계 「5단계 2부 계획 전 결정」 8번)
    ["composition_unknown", setup.plugins.filter((plugin) => plugin.configured && !plugin.compositionKnown).map((plugin) => plugin.id)],
    ["skills_unreadable", setup.unreadableSkillPlaces.plugins.filter((id) => enabledIds.has(id))],
    ["mcp_unreadable", setup.plugins.filter((plugin) => plugin.enabled && plugin.mcpUnreadable).map((plugin) => plugin.id)]
  ];
  for (const [why, plugins] of uncounted) {
    if (plugins.length > 0) notices2.push({ kind: "plugins_uncounted", tool: "codex", why, plugins: sortedUnique(plugins) });
  }
  notices2.push(...unscoredProblems("codex", setup.problems));
  return notices2;
}
function geminiSetupNotices(setup, projects) {
  const notices2 = [];
  const rootOf = new Map(projects.map((project) => [project.normRoot, project.root]));
  const unreadable = [
    ["user_settings", unread2(setup.settings), []],
    ["managed_settings", false, setup.managedParts.filter((part) => unread2(part.status)).map((part) => part.path)],
    ["project_settings", false, setup.projects.filter((project) => project.trusted && unread2(project.settingsStatus)).map((project) => rootOf.get(project.normRoot) ?? project.normRoot)],
    ["gemini_trusted_folders", setup.folderTrust && unread2(setup.trustedFolders), []],
    ["instructions", false, [setup.globalInstructions, ...setup.projects.map((project) => project.instructions)].flatMap((set) => [...set.unreadable, ...set.unreadableDirs])]
  ];
  for (const [what, whole, targets] of unreadable) {
    if (whole || targets.length > 0) notices2.push({ kind: "setup_unreadable", tool: "gemini", what, targets: sortedUnique(targets) });
  }
  notices2.push(...unscoredProblems("gemini", setup.problems));
  return notices2;
}
function setupNotices(input, evaluation, run2) {
  const notices2 = [];
  if (evaluation.score.withheld.length > 0) notices2.push({ kind: "score_withheld", reasons: [...evaluation.score.withheld] });
  if (run2.stateBroken) notices2.push({ kind: "state_reset" });
  if (run2.webExportsBroken === true) notices2.push({ kind: "web_exports_reset" });
  for (const tool of setupTools(input.tools)) {
    if (tool.setup.secrets.length > 0) notices2.push({ kind: "credentials_in_config", tool: tool.tool, places: [...tool.setup.secrets] });
    if (tool.tool === "codex") {
      notices2.push(...codexSetupNotices(tool.setup, input.projects));
      continue;
    }
    if (tool.tool === "gemini") {
      notices2.push(...geminiSetupNotices(tool.setup, input.projects));
      continue;
    }
    const id = tool.tool;
    const setup = tool.setup;
    const unreadable = [
      ["claude_json", unread2(setup.claudeJson), []],
      ["user_settings", unread2(setup.settings.user), []],
      ["managed_settings", false, setup.settings.managedParts.filter((part) => unread2(part.status)).map((part) => part.path)],
      ["project_settings", false, setup.projects.filter((project) => unread2(project.settingsStatus)).map((project) => project.root)],
      ["local_settings", false, setup.projects.filter((project) => unread2(project.localSettingsStatus)).map((project) => project.root)],
      ["mcp_json", false, setup.projects.filter((project) => unread2(project.mcpJsonStatus)).map((project) => project.root)],
      ["plugins_file", unread2(setup.pluginsFile), []],
      ["skill_dirs", false, setup.unreadableDirs],
      ["instructions", false, [setup.globalInstructions, ...setup.projects.map((project) => project.instructions)].flatMap((set) => [...set.unreadable, ...set.unreadableDirs])],
      ["hook_settings", false, setup.hooks.unreadableSettings],
      ["skill_files", false, setup.skills.filter((skill) => !skill.readable).map((skill) => skill.path)]
    ];
    for (const [what, whole, targets] of unreadable) {
      if (whole || targets.length > 0) notices2.push({ kind: "setup_unreadable", tool: id, what, targets: sortedUnique(targets) });
    }
    const enabled = setup.plugins.filter((plugin) => plugin.enabled);
    const enabledIds = new Set(enabled.map((plugin) => plugin.id));
    const uncounted = [
      // 놓인 곳이 지금 없는 플러그인도 구성을 모른다. 2부는 이런 플러그인이 켜져 있으면 스킬 끄기와 서버 막기 후보를 막는다
      ["composition_unknown", enabled.filter((plugin) => !plugin.compositionKnown).map((plugin) => plugin.id)],
      ["not_installed", setup.pluginsWithoutInstall],
      ["skills_unreadable", setup.unreadableSkillPlaces.plugins.filter((id2) => enabledIds.has(id2))],
      ["mcp_unreadable", enabled.filter((plugin) => plugin.compositionKnown && plugin.mcpUnreadable).map((plugin) => plugin.id)],
      ["hooks_unreadable", enabled.filter((plugin) => plugin.compositionKnown && plugin.hooksUnreadable).map((plugin) => plugin.id)]
    ];
    for (const [why, plugins] of uncounted) {
      if (plugins.length > 0) notices2.push({ kind: "plugins_uncounted", tool: id, why, plugins: sortedUnique(plugins) });
    }
    notices2.push(...unscoredProblems(id, setup.problems));
  }
  const gone = input.projects.filter((project) => !project.exists).map((project) => project.root);
  if (gone.length > 0) notices2.push({ kind: "projects_gone", projects: sortedUnique(gone) });
  return sortNotices(notices2);
}
function webRecordNotices(tool, state, today) {
  if (state.path === null) return [];
  if (state.missing) return [{ kind: "web_export_missing", tool, path: state.path }];
  if (state.problem !== null) return [{ kind: "web_export_unreadable", tool, path: state.path, problem: state.problem }];
  const notices2 = [];
  if (state.skipped > 0 || state.truncated) notices2.push({ kind: "web_export_partial", tool, skipped: state.skipped, truncated: state.truncated });
  if (state.lastDate !== null && state.lastDate < today) notices2.push({ kind: "web_export_until", tool, lastDate: state.lastDate });
  return notices2;
}
function codexRecordNotices(tool, codex) {
  const notices2 = [];
  if (codex.skippedFiles.length > 0) notices2.push({ kind: "record_skipped", tool, files: [...codex.skippedFiles].sort(byText9) });
  if (codex.partialFiles.length > 0) notices2.push({ kind: "record_partial", tool, files: [...codex.partialFiles].sort(byText9) });
  if (codex.unverifiedInheritance > 0) notices2.push({ kind: "unverified_inheritance", tool, sessions: codex.unverifiedInheritance });
  const fallbacks = Object.entries(codex.idFallbacks).filter(([, count]) => count > 0).sort((a, b) => byText9(a[0], b[0])).map(([why, count]) => ({ why, count }));
  if (fallbacks.length > 0) notices2.push({ kind: "id_fallbacks", tool, counts: fallbacks });
  if (codex.parentRecordMissing > 0) notices2.push({ kind: "parent_record_missing", tool, sessions: codex.parentRecordMissing });
  if (codex.mergedSessions > 0) notices2.push({ kind: "merged_sessions", tool, sessions: codex.mergedSessions });
  if (codex.unknownMtimeSessions > 0) notices2.push({ kind: "unknown_mtime_sessions", tool, sessions: codex.unknownMtimeSessions });
  if (codex.skippedCopies > 0) notices2.push({ kind: "skipped_copies", tool, count: codex.skippedCopies });
  if (codex.unnamedFiles > 0) notices2.push({ kind: "unnamed_files", tool, count: codex.unnamedFiles });
  return notices2;
}
function recordNotices(input, evaluation, collected) {
  const notices2 = [];
  for (const tool of input.tools) {
    const id = tool.tool;
    const found = collected.find((item2) => item2.tool === id);
    if (found !== void 0) {
      const { unreadableFiles, unreadableDirs } = found.read;
      if (unreadableFiles.length > 0 || unreadableDirs.length > 0) notices2.push({ kind: "record_unreadable", tool: id, files: [...unreadableFiles].sort(byText9), dirs: [...unreadableDirs].sort(byText9) });
      for (const metric of ["skills", "mcp"]) {
        const observation = found.observation[metric];
        if (!observation.complete && !observation.reasons.includes("not-recorded")) notices2.push({ kind: "observation_incomplete", tool: id, metric, reasons: [...observation.reasons] });
      }
      if (found.overlappingSessions > 0) notices2.push({ kind: "overlapping_responses", tool: id, sessions: found.overlappingSessions });
      if (found.codex !== void 0) notices2.push(...codexRecordNotices(id, found.codex));
      if (found.web !== void 0) notices2.push(...webRecordNotices(id, found.web, evaluation.windows.today));
    }
    const verified = VERIFIED_VERSIONS[id];
    if (verified !== null) {
      const [from, to] = [parseVersion(verified.from), parseVersion(verified.to)];
      const outside2 = /* @__PURE__ */ new Map();
      for (const summary of tool.summaries) {
        const version = parseVersion(summary.version);
        if (version !== null && (compareVersions(version, from) < 0 || compareVersions(version, to) > 0)) outside2.set(summary.version, version);
      }
      if (outside2.size > 0) notices2.push({ kind: "version_unverified", tool: id, versions: [...outside2].sort((a, b) => compareVersions(a[1], b[1])).map(([text]) => text), verified: { ...verified } });
    }
    let total = 0;
    let weak = 0;
    for (const summary of tool.summaries) {
      if (summary.kind !== "main") continue;
      for (const [date, day] of Object.entries(summary.days)) {
        if (!inRange(date, evaluation.windows.score)) continue;
        total += day.humanRequests;
        weak += day.weakHumanRequests;
      }
    }
    if (total > 0 && weak / total > WEAK_REQUEST_SHARE) notices2.push({ kind: "weak_human_requests", tool: id, weak, total });
    const counts = /* @__PURE__ */ new Map();
    const add = (what, count) => {
      if (count > 0) counts.set(what, (counts.get(what) ?? 0) + count);
    };
    for (const summary of tool.summaries) {
      if (summary.codex?.unknownThreadSource != null) add(`thread_source:${summary.codex.unknownThreadSource}`, 1);
      for (const [kind, count] of Object.entries(summary.codex?.unknownItemTypes ?? {})) add(`item:${kind}`, count);
      for (const [kind, count] of Object.entries(summary.notes.unknownHookKinds)) add(`hook:${kind}`, count);
      if (tool.setup === null) for (const [kind, count] of Object.entries(summary.missing.unconfirmedTypes)) add(`content:${kind}`, count);
      for (const day of Object.values(summary.days)) {
        for (const [kind, count] of Object.entries(day.unknownDenialKinds)) add(`denial:${kind}`, count);
        add("compaction", day.unknownCompactions);
      }
    }
    if (counts.size > 0) notices2.push({ kind: "unclassified", tool: id, counts: [...counts].sort((a, b) => byText9(a[0], b[0])).map(([what, count]) => ({ what, count })) });
    const orphans = tool.summaries.filter((summary) => summary.kind === "sub" && summary.parentSessionId === null).length;
    if (orphans > 0) notices2.push({ kind: "orphan_subsessions", tool: id, sessions: orphans });
  }
  return sortNotices(notices2);
}

// src/core/result/observed.ts
var RULE_METRICS = {
  S4: ["mcpFailuresAndHooks"],
  S5: ["mcpFailuresAndHooks"],
  E1: ["responsesAndTokens"],
  E2: ["toolErrors"],
  E3: ["autoCompaction"],
  E4: ["instructionSize"],
  E5: ["skillUsage"],
  E6: ["mcpCalls"],
  E7: ["deniedAndLengthStops", "interruptedTurns"],
  F1: ["effort"],
  F2: ["subagents", "autoCompaction"],
  F5: []
};
var STRENGTH = { unsupported: 0, proxy: 1, measured: 2 };
var weakestOf = (keys, coverage) => keys.reduce((weakest, key) => STRENGTH[coverage[key]] < STRENGTH[weakest] ? coverage[key] : weakest, "measured");
function observedOf(rule2, coverage) {
  return weakestOf(RULE_METRICS[rule2], coverage);
}
var MERGED_RULE_METRICS = { I2: ["humanRequests"], I3: ["humanRequests", "toolCalls"] };
function mergedObserved(rule2, tools2) {
  const metrics = MERGED_RULE_METRICS[rule2] ?? [];
  if (metrics.length === 0) return [];
  return tools2.filter((tool) => metrics.every((key) => tool.coverage[key] !== "unsupported")).map((tool) => ({ tool: tool.tool, observed: weakestOf(metrics, tool.coverage) }));
}

// src/core/result/tools.ts
var FORMATS = { "claude-code": ["claude-code-jsonl"], codex: ["codex-jsonl"], gemini: ["gemini-jsonl", "gemini-json"], "web-chatgpt": ["chatgpt-export"], "web-claude": ["claude-export"] };
var inRange2 = (date, range) => date >= range.from && date <= range.to;
function resultTools(input, evaluation, collected) {
  return evaluation.tools.map((tool) => {
    const found = collected.find((item2) => item2.tool === tool.tool) ?? null;
    const summaries = input.tools.find((item2) => item2.tool === tool.tool)?.summaries ?? [];
    const subSessions = summaries.filter((summary) => summary.kind === "sub" && Object.entries(summary.days).some(([date, day]) => inRange2(date, evaluation.windows.score) && day.responses > 0)).length;
    const visibleFrom2 = found?.visibleFrom ?? null;
    const lastDate = found?.web?.lastDate ?? null;
    const visibleTo = lastDate !== null && lastDate < evaluation.windows.today ? lastDate : evaluation.windows.today;
    return {
      tool: tool.tool,
      detected: found?.detected ?? false,
      scored: tool.scored,
      inCalendar: tool.inCalendar,
      formats: [...FORMATS[tool.tool]],
      mainSessions: tool.totals.mainSessions.length,
      subSessions,
      humanRequests: tool.totals.humanRequests,
      responses: tool.totals.responses,
      // 내보내기가 모두 수집 구간보다 오래되면 볼 수 있는 날이 없다(짝 검토 5 필수 8)
      visible: visibleFrom2 === null || visibleTo < visibleFrom2 ? null : { from: visibleFrom2, to: visibleTo }
    };
  });
}

// src/core/result/usage.ts
var inRange3 = (date, range) => date >= range.from && date <= range.to;
function shellCounts(tool, score) {
  if (tool.coverage.shellExitCodes === "unsupported") return null;
  const shell = new Set(tool.shellTools);
  let results = 0;
  let errors = 0;
  for (const summary of tool.summaries) {
    for (const [date, day] of Object.entries(summary.days)) {
      if (!inRange3(date, score)) continue;
      for (const [name, counts] of Object.entries(day.tools)) {
        if (!shell.has(name)) continue;
        results += counts.results;
        errors += counts.errors;
      }
    }
  }
  return { results, errors };
}
var share = (counts) => counts === null || counts.results === 0 ? null : counts.errors / counts.results;
function resultUsage(input, evaluation, collected) {
  const score = evaluation.windows.score;
  const e12 = evaluation.findings.find((finding) => finding.ruleId === "E1") ?? null;
  const scored2 = evaluation.tools.filter((tool) => tool.scored);
  const inputs = new Map(input.tools.map((tool) => [tool.tool, tool]));
  const byTool = scored2.map((tool) => ({
    tool: tool.tool,
    mainSessions: tool.totals.mainSessions.length,
    activeDays: tool.totals.activeDates.length,
    outputTokens: inputs.get(tool.tool).coverage.responsesAndTokens === "unsupported" ? null : tool.totals.tokens.output,
    cacheHit: e12?.tools.find((value) => value.tool === tool.tool)?.value ?? null,
    shellNonZero: share(shellCounts(inputs.get(tool.tool), score))
  }));
  const shells = scored2.map((tool) => shellCounts(inputs.get(tool.tool), score)).filter((counts) => counts !== null);
  const responsesByDate = /* @__PURE__ */ new Map();
  for (const tool of input.tools) {
    for (const summary of tool.summaries) {
      for (const [date, day] of Object.entries(summary.days)) responsesByDate.set(date, (responsesByDate.get(date) ?? 0) + day.responses);
    }
  }
  const today = evaluation.windows.today;
  const ranges = collected.flatMap((tool) => {
    if (tool.visibleFrom === null) return [];
    const last = tool.web?.lastDate ?? null;
    return [{ from: tool.visibleFrom, to: last !== null && last < today ? last : today }];
  });
  const calendar2 = makeWindows(input.clock.nowMs, input.clock.timeZone).collectDates.map((date) => {
    const responses = responsesByDate.get(date) ?? 0;
    const state = responses > 0 ? "used" : ranges.some((range) => range.from <= date && date <= range.to) ? "unused" : "unseen";
    return { date, responses, state };
  });
  return {
    mainSessions: byTool.reduce((sum2, tool) => sum2 + tool.mainSessions, 0),
    activeDays: new Set(scored2.flatMap((tool) => tool.totals.activeDates)).size,
    outputTokens: byTool.length > 0 && byTool.every((tool) => tool.outputTokens === null) ? null : byTool.reduce((sum2, tool) => sum2 + (tool.outputTokens ?? 0), 0),
    cacheHit: e12?.value ?? null,
    shellNonZero: shells.length === 0 ? null : share({ results: shells.reduce((sum2, counts) => sum2 + counts.results, 0), errors: shells.reduce((sum2, counts) => sum2 + counts.errors, 0) }),
    calendar: calendar2,
    byTool
  };
}

// src/core/result/assemble.ts
var RESULT_SCHEMA = 1;
var byText10 = (a, b) => a < b ? -1 : a > b ? 1 : 0;
var textsOf = (make2) => ({ en: make2("en"), ko: make2("ko") });
var SCOPE_ORDER3 = ["user", "local", "project", "plugin", "claude-ai"];
function unjudgedServers(input, evaluation) {
  const windows = makeWindows(input.clock.nowMs, input.clock.timeZone);
  const names2 = new Map(input.projects.map((project) => [project.normRoot, project.name]));
  const servers = [];
  for (const tool of evaluation.tools) {
    const source = input.tools.find((item2) => item2.tool === tool.tool);
    const called = calledMcpNames(source.summaries, windows);
    for (const judged of tool.servers) {
      const { server } = judged;
      if (!server.enabled || judged.verdict !== "unknown" || anyIn(server.recordNames, called.inCollect)) continue;
      const why = judged.excluded ?? (source.complete.mcp ? "not_established" : "observation_incomplete");
      const projectName = server.projectRoot === null ? null : names2.get(server.projectRoot) ?? null;
      servers.push({ tool: tool.tool, name: server.name, scope: server.scope, projectRoot: server.projectRoot, projectName, pluginId: server.pluginId, why, judgeFrom: why === "not_established" ? judged.judgeFrom : null });
    }
  }
  return servers.sort((a, b) => byText10(a.name, b.name) || SCOPE_ORDER3.indexOf(a.scope) - SCOPE_ORDER3.indexOf(b.scope) || byText10(a.projectRoot ?? "", b.projectRoot ?? "") || byText10(a.pluginId ?? "", b.pluginId ?? "") || byText10(a.tool, b.tool));
}
function failedMcpServers(evaluation) {
  return evaluation.tools.filter((tool) => tool.scored).flatMap((tool) => {
    const sessions = /* @__PURE__ */ new Map();
    for (const session of tool.totals.mainSessions) for (const name of session.mcpFailedServers) sessions.set(name, (sessions.get(name) ?? 0) + 1);
    return [...sessions].map(([name, count]) => ({ tool: tool.tool, name, sessions: count }));
  }).sort((a, b) => b.sessions - a.sessions || byText10(a.tool, b.tool) || byText10(a.name, b.name));
}
function credentialPlaces(input) {
  const names2 = new Map(input.projects.map((project) => [project.normRoot, project.name]));
  return setupTools(input.tools).sort((a, b) => byText10(a.tool, b.tool)).flatMap((tool) => tool.setup.secrets.map((secret) => ({ tool: tool.tool, scope: secret.scope, server: secret.server, projectName: secret.projectRoot === null ? null : names2.get(secret.projectRoot) ?? null, field: secret.field, key: secret.key, ...secret.copy === void 0 ? {} : { copy: secret.copy } })));
}
function checkupResult(source) {
  const { input, evaluation, collected } = source;
  const coverageByTool = new Map(input.tools.map((tool) => [tool.tool, tool.coverage]));
  const details = { safeguards: evaluation.safeguards, missingInstructions: evaluation.missingInstructions, worstOverlap: evaluation.worstOverlap, unjudgedServers: unjudgedServers(input, evaluation), setupProblems: evaluation.setupProblems, credentialPlaces: credentialPlaces(input), failedMcpServers: failedMcpServers(evaluation) };
  const scoredTools = evaluation.tools.filter((tool) => tool.scored).map((tool) => ({ tool: tool.tool, coverage: coverageByTool.get(tool.tool) }));
  const textDetails = { ...details, mergedTools: Object.fromEntries(evaluation.findings.map((finding) => [finding.ruleId, mergedObserved(finding.ruleId, scoredTools)])) };
  const findings = evaluation.findings.map((finding) => {
    const source2 = { ...finding, tools: finding.tools.map((value) => ({ ...value, observed: observedOf(finding.ruleId, coverageByTool.get(value.tool)) })) };
    return { ...source2, text: textsOf((lang) => findingText(source2, textDetails, lang)) };
  });
  const notices2 = sortNotices([...recordNotices(input, evaluation, collected), ...setupNotices(input, evaluation, source.run)]);
  const categories = findings.map((finding) => finding.category);
  const ignored = [...source.ignored ?? []];
  const next = nextGrade(evaluation.findings.map((finding) => ({ ruleId: finding.ruleId, axis: finding.axis, weight: finding.weight, score: finding.score, gain: finding.gain })), evaluation.score, new Set(ignored));
  const nameOf = (lang) => (ruleId) => findings.find((finding) => finding.ruleId === ruleId).text[lang].name;
  return {
    schema: RESULT_SCHEMA,
    rulesVersion: evaluation.rulesVersion,
    appVersion: source.appVersion,
    evaluatedAt: new Date(input.clock.nowMs).toISOString(),
    timezone: input.clock.timeZone,
    lang: source.lang,
    window: evaluation.windows,
    tools: resultTools(input, evaluation, collected),
    coverage: resultCoverage(input, collected),
    score: evaluation.score,
    text: textsOf((lang) => resultText(evaluation.score, categories, lang)),
    axes: evaluation.axes,
    findings,
    candidates: evaluation.candidates,
    usage: resultUsage(input, evaluation, collected),
    deepHints: deepHints(input),
    notices: notices2.map((notice) => ({ ...notice, text: textsOf((lang) => noticeText(notice, lang)) })),
    details,
    nextGrade: next === null ? null : { ...next, text: textsOf((lang) => nextGradeText(next, nameOf(lang), lang)) },
    ignored
  };
}

// src/core/result/summary.ts
var FIX_FIRST_LIMIT = 3;
function summaryNotice(notice) {
  const tool = "tool" in notice ? notice.tool : null;
  switch (notice.kind) {
    case "score_withheld":
    case "state_reset":
    case "web_exports_reset":
    case "web_export_missing":
      return { kind: notice.kind, tool, detail: null, count: null };
    case "web_export_unreadable":
      return { kind: notice.kind, tool, detail: notice.problem, count: null };
    case "web_export_partial":
      return { kind: notice.kind, tool, detail: notice.truncated ? "truncated" : null, count: notice.skipped };
    case "web_export_until":
      return { kind: notice.kind, tool, detail: notice.lastDate, count: null };
    case "credentials_in_config":
      return { kind: notice.kind, tool, detail: null, count: notice.places.length };
    case "record_unreadable":
      return { kind: notice.kind, tool, detail: null, count: notice.files.length + notice.dirs.length };
    case "record_skipped":
    case "record_partial":
      return { kind: notice.kind, tool, detail: null, count: notice.files.length };
    case "observation_incomplete":
      return { kind: notice.kind, tool, detail: notice.metric, count: null };
    case "setup_unreadable":
      return { kind: notice.kind, tool, detail: notice.what, count: notice.targets.length > 0 ? notice.targets.length : null };
    case "plugins_uncounted":
      return { kind: notice.kind, tool, detail: notice.why, count: notice.plugins.length };
    case "setup_problems_unscored":
      return { kind: notice.kind, tool, detail: null, count: notice.problems.length };
    case "projects_gone":
      return { kind: notice.kind, tool, detail: null, count: notice.projects.length };
    case "version_unverified":
      return { kind: notice.kind, tool, detail: null, count: notice.versions.length };
    case "weak_human_requests":
      return { kind: notice.kind, tool, detail: null, count: notice.weak };
    case "overlapping_responses":
    case "orphan_subsessions":
    case "unverified_inheritance":
    case "parent_record_missing":
    case "merged_sessions":
    case "unknown_mtime_sessions":
      return { kind: notice.kind, tool, detail: null, count: notice.sessions };
    case "unclassified":
    case "id_fallbacks":
      return { kind: notice.kind, tool, detail: null, count: notice.counts.reduce((sum2, item2) => sum2 + item2.count, 0) };
    case "skipped_copies":
    case "unnamed_files":
      return { kind: notice.kind, tool, detail: null, count: notice.count };
  }
}
function beyondZeroMark(ruleId, value) {
  const spec = ruleSpec(ruleId);
  const now = settleScore(value);
  const mark = settleScore(spec.zeroAt);
  return spec.zeroAt > spec.fullAt ? now > mark : now < mark;
}
function fixDetail(fix, lang) {
  const copy2 = SUMMARY_COPY[lang];
  if (fix.gain !== null) {
    const spec = ruleSpec(fix.ruleId);
    const below = spec.zeroAt > spec.fullAt;
    const perTool = fix.tools.length >= 2;
    const beyond = perTool ? fix.tools.some((tool) => beyondZeroMark(fix.ruleId, tool.value)) : fix.value !== null && beyondZeroMark(fix.ruleId, fix.value);
    if (fix.value !== null && fix.score !== null && settleScore(fix.score) === 0 && beyond) {
      const template = perTool ? below ? copy2.gainBelowTools : copy2.gainAboveTools : below ? copy2.gainBelow : copy2.gainAbove;
      const now = perTool ? fix.tools.map((tool) => `${TOOL_NAMES[tool.tool][lang]} ${ruleValueText(fix.ruleId, tool.value, lang)}`).join(copy2.toolJoin) : ruleValueText(fix.ruleId, fix.value, lang);
      return fill(template, { axis: AXIS_NAMES[fix.axis][lang], gain: fix.gain, now, start: ruleValueText(fix.ruleId, spec.zeroAt, lang) });
    }
    return fill(copy2.gain, { axis: AXIS_NAMES[fix.axis][lang], gain: fix.gain });
  }
  if (!fix.measured) return fill(copy2.unmeasured, { candidates: fix.candidates });
  if (fix.unmeasuredTools.length > 0) return fill(copy2.otherTools, { candidates: fix.candidates, tools: fix.unmeasuredTools.map((tool) => TOOL_NAMES[tool][lang]).join(", ") });
  return fill(copy2.candidates, { candidates: fix.candidates });
}
function targetsOf(finding, result) {
  const names2 = (() => {
    switch (finding.ruleId) {
      case "S3":
        return result.details.setupProblems.map((problem) => problem.place);
      case "S5":
        return result.details.failedMcpServers.map((server) => server.name);
      case "F3":
        return result.details.missingInstructions.map((project) => project.name);
      case "F4":
        return result.details.worstOverlap === null ? [] : [result.details.worstOverlap.name];
      default:
        return finding.candidates.map((id) => result.candidates.find((candidate) => candidate.id === id)?.target ?? id);
    }
  })();
  return [...new Set(names2)];
}
function checkupSummary(result, reportPath) {
  const lang = result.lang;
  const secretCount = result.notices.reduce((sum2, notice) => sum2 + (notice.kind === "credentials_in_config" ? notice.places.length : 0), 0);
  const strength = result.findings.find((finding) => finding.category === "strength") ?? null;
  const ignored = new Set(result.ignored);
  const repairs = result.score.aq === null ? [] : result.findings.filter((finding) => finding.category === "repair" && !ignored.has(finding.ruleId)).slice(0, FIX_FIRST_LIMIT);
  const fixFirst = repairs.map((finding) => ({
    ruleId: finding.ruleId,
    axis: finding.axis,
    gain: finding.gain,
    measured: finding.status === "scored",
    candidates: finding.candidates.length,
    unmeasuredTools: finding.tools.filter((value) => value.status === "unmeasured" && value.candidates.length > 0).map((value) => value.tool),
    targets: targetsOf(finding, result),
    value: finding.value,
    score: finding.score,
    tools: finding.tools.flatMap((value) => value.status === "scored" ? [{ tool: value.tool, value: value.value, score: value.score }] : []),
    zeroAt: ruleSpec(finding.ruleId).zeroAt,
    fullAt: ruleSpec(finding.ruleId).fullAt
  }));
  return {
    aq: result.score.aq,
    grade: result.score.grade,
    tier: result.score.tier,
    withheld: [...result.score.withheld],
    axes: result.axes.map((axis) => ({ axis: axis.axis, score: axis.score })),
    best: strength === null ? null : { ruleId: strength.ruleId, axis: strength.axis, kind: strength.kind, value: strength.value },
    fixFirst,
    nextGrade: result.nextGrade === null ? null : { grade: result.nextGrade.grade, need: result.nextGrade.need, reaches: result.nextGrade.reaches, steps: result.nextGrade.steps.map((step) => ({ ...step })) },
    notices: result.notices.map(summaryNotice),
    credentialPlaces: result.details.credentialPlaces.map((place) => ({ ...place })),
    ignored: [...result.ignored],
    reportPath,
    lang,
    text: {
      grade: result.text[lang].grade,
      diagnosis: result.text[lang].diagnosis,
      best: strength === null ? null : { title: strength.text[lang].title, detail: fill(SUMMARY_COPY[lang].best, { name: strength.text[lang].name, value: joinValue(strength.text[lang].value, strength.text[lang].unit, lang) }) },
      noBest: result.text[lang].noStrengths,
      fixFirst: repairs.map((finding, index) => ({ title: finding.text[lang].title, detail: fixDetail(fixFirst[index], lang) })),
      noFixFirst: result.text[lang].noRepairs,
      nextGrade: result.nextGrade?.text[lang] ?? null,
      credentials: secretCount === 0 ? null : fill(SUMMARY_COPY[lang].credentials, { count: secretCount }),
      notices: result.notices.map((notice) => notice.text[lang])
    }
  };
}

// src/report/assets.ts
import { readFile as readFile2 } from "node:fs/promises";
import { basename, dirname, join as join3 } from "node:path";
var ART_FILES = {
  "scene-1": "scene-1.webp",
  "scene-2": "scene-2.webp",
  "scene-3": "scene-3.webp",
  "scene-4": "scene-4.webp",
  "scene-5": "scene-5.webp",
  "scene-few-records": "scene-few-records.webp",
  "scene-unreadable": "scene-unreadable.webp",
  face: "face.webp",
  "sticker-good": "sticker-good.webp",
  "sticker-fix": "sticker-fix.webp",
  "sticker-done": "sticker-done.webp"
};
function sceneFor(tier, unreadable) {
  if (tier !== null) return `scene-${tier}`;
  return unreadable ? "scene-unreadable" : "scene-few-records";
}
function stickerFor(repairs) {
  return repairs > 0 ? "sticker-fix" : "sticker-done";
}
function assetsDirOf(entryFile) {
  if (basename(entryFile) !== "aq.mjs" || basename(dirname(entryFile)) !== "scripts") return null;
  return join3(dirname(dirname(entryFile)), "assets");
}
async function dataUri(dir, name) {
  if (dir === null) return null;
  try {
    return `data:image/webp;base64,${(await readFile2(join3(dir, ART_FILES[name]))).toString("base64")}`;
  } catch {
    return null;
  }
}
async function loadArt(dir, pick) {
  const [scene, face, good, fix] = await Promise.all([
    dataUri(dir, sceneFor(pick.tier, pick.unreadable)),
    dataUri(dir, "face"),
    dataUri(dir, "sticker-good"),
    dataUri(dir, stickerFor(pick.repairs))
  ]);
  return { scene, face, good, fix };
}

// src/report/html.ts
import { createHash } from "node:crypto";

// src/core/copy/lang.ts
var LANGS = ["en", "ko"];
function supportedLang(tag) {
  if (typeof tag !== "string") return null;
  const primary = tag.trim().toLowerCase().split(/[-_.@]/)[0];
  return LANGS.find((lang) => lang === primary) ?? null;
}
function pickLang(flag, osLocale) {
  return supportedLang(flag) ?? supportedLang(osLocale) ?? "en";
}

// src/report/copy.ts
var REPORT_COPY = {
  brand: { en: "Chunsik's Garage", ko: "\uCD98\uC2DD\uC774 \uC815\uBE44\uC18C" },
  title: { en: "AQ Inspection Sheet", ko: "AQ \uC810\uAC80 \uBA85\uC138\uC11C" },
  pageTitle: { en: "AQ Inspection Sheet \xB7 {date}", ko: "AQ \uC810\uAC80 \uBA85\uC138\uC11C \xB7 {date}" },
  langGroup: { en: "Language", ko: "\uD654\uBA74 \uC5B8\uC5B4" },
  date: { en: "Date", ko: "\uC810\uAC80\uC77C" },
  tools: { en: "Tools", ko: "\uB300\uC0C1" },
  period: { en: "Score window", ko: "\uC810\uC218 \uAD6C\uAC04" },
  round: { en: "Check-up", ko: "\uD68C\uCC28" },
  roundValue: { en: "#{n}", ko: "{n}\uD68C" },
  notSaved: { en: "Not saved", ko: "\uC800\uC7A5 \uC548 \uD568" },
  noTools: { en: "None found", ko: "\uCC3E\uC9C0 \uBABB\uD568" },
  scoreAria: { en: "Overall score", ko: "\uC885\uD569 \uC810\uC218" },
  aqLabel: { en: "AQ SCORE", ko: "AQ \uC9C0\uC218" },
  grade: { en: "GRADE", ko: "\uB4F1\uAE09" },
  gradeAria: { en: "Grade {g}", ko: "\uB4F1\uAE09 {g}" },
  noScore: { en: "No score", ko: "\uC810\uC218 \uC5C6\uC74C" },
  axisCounts: { en: "Good {g} \xB7 Fix {f}", ko: "\uC798\uD568 {g} \xB7 \uC815\uBE44 {f}" },
  axisAria: { en: "{axis} {v} out of 100", ko: "{axis} {v}\uC810, 100\uC810 \uB9CC\uC810" },
  axisNone: { en: "{axis} not measured", ko: "{axis} \uC7B4 \uC218 \uC5C6\uC74C" },
  axesTable: { en: "Scores on the four axes", ko: "\uB124 \uAE30\uC900\uC758 \uC810\uC218" },
  thAxis: { en: "Axis", ko: "\uAE30\uC900" },
  thScore: { en: "Score", ko: "\uC810\uC218" },
  thGood: { en: "Good", ko: "\uC798\uD568" },
  thFix: { en: "Fix", ko: "\uC815\uBE44" },
  unmeasured: { en: "Not measured", ko: "\uC7B4 \uC218 \uC5C6\uC74C" },
  verdict: { en: "Verdict", ko: "\uC9C4\uB2E8" },
  best: { en: "Best at", ko: "\uAC00\uC7A5 \uC798\uD558\uB294 \uAC83" },
  fixFirst: { en: "Fix first", ko: "\uBA3C\uC800 \uACE0\uCE60 \uAC83" },
  nextGrade: { en: "Next grade", ko: "\uB2E4\uC74C \uB4F1\uAE09\uAE4C\uC9C0" },
  spotSettings: { en: "Settings", ko: "\uC124\uC815" },
  spotDefaultCopy: { en: "copy in the default location", ko: "\uAE30\uBCF8 \uC704\uCE58\uC758 \uC0AC\uBCF8" },
  spotEnv: { en: "env", ko: "env" },
  spotHeaders: { en: "header", ko: "\uBA38\uB9AC\uB9D0" },
  spotField: { en: "field", ko: "\uCE78" },
  spotArgs: { en: "argument", ko: "\uC778\uC790" },
  spotUrl: { en: "address", ko: "\uC8FC\uC18C" },
  colGood: { en: "What you do well", ko: "\uC798\uD558\uACE0 \uC788\uB294 \uAC83" },
  colFix: { en: "What to tune up", ko: "\uC815\uBE44\uD560 \uAC83" },
  how: { en: "How it was measured", ko: "\uC5B4\uB5BB\uAC8C \uC7C0\uB098" },
  clean: { en: "Clean up", ko: "\uC815\uB9AC\uD558\uAE30" },
  copied: { en: "Copied. Paste it into Claude Code or Codex.", ko: "\uBCF5\uC0AC\uD588\uC2B5\uB2C8\uB2E4. Claude Code\uB098 Codex\uC5D0 \uBD99\uC5EC \uB123\uC73C\uC138\uC694." },
  copyFail: { en: "Copying was blocked. Copy the text below and paste it into Claude Code or Codex.", ko: "\uBCF5\uC0AC\uAC00 \uB9C9\uD614\uC2B5\uB2C8\uB2E4. \uC544\uB798 \uAE00\uC744 \uC9C1\uC811 \uBCF5\uC0AC\uD574 Claude Code\uB098 Codex\uC5D0 \uBD99\uC5EC \uB123\uC73C\uC138\uC694." },
  copyLabel: { en: "Text to paste", ko: "\uBD99\uC5EC \uB123\uC744 \uB9D0" },
  phrase: { en: "Chunsik's Garage tune-up: {name}", ko: "\uCD98\uC2DD\uC774 \uC815\uBE44\uC18C \uC815\uBE44: {name}" },
  targets: { en: "To clean up", ko: "\uC815\uB9AC\uD560 \uAC83" },
  places: { en: "Where", ko: "\uACE0\uCE60 \uACF3" },
  missingProjects: { en: "Projects without instructions", ko: "\uC9C0\uCE68\uC774 \uC5C6\uB294 \uD504\uB85C\uC81D\uD2B8" },
  failedServers: { en: "Servers that failed to connect", ko: "\uC5F0\uACB0\uC5D0 \uC2E4\uD328\uD55C \uC11C\uBC84" },
  nextTitle: { en: "How to reach grade {grade}", ko: "{grade}\uB4F1\uAE09\uC73C\uB85C \uAC00\uB294 \uC14B\uD305 \uBC29\uBC95" },
  kept: { en: "Kept as you chose", ko: "\uADF8\uB300\uB85C \uB450\uAE30\uB85C \uD568" },
  nextLead: { en: "{need} {need:point|points} to grade {grade}. Fix these from the top; each line shows the AQ once everything up to it is fixed.", ko: "{grade}\uB4F1\uAE09\uAE4C\uC9C0 {need}\uC810\uC785\uB2C8\uB2E4. \uC704\uC5D0\uC11C\uBD80\uD130 \uCC28\uB840\uB85C \uACE0\uCE58\uBA74 \uC904\uB9C8\uB2E4 \uC801\uD78C AQ\uAC00 \uB429\uB2C8\uB2E4." },
  nextShort: { en: "These alone reach {last}.", ko: "\uC774\uAC83\uB9CC\uC73C\uB85C\uB294 {last}\uC810\uC785\uB2C8\uB2E4." },
  nextNow: { en: "Now {now} \u2192 aim for {target}", ko: "\uC9C0\uAE08 {now} \u2192 \uBAA9\uD45C {target}" },
  nextNowTool: { en: "{tool}: now {now} \u2192 aim for {target}", ko: "{tool} \uC9C0\uAE08 {now} \u2192 \uBAA9\uD45C {target}" },
  nextBelow: { en: "The score starts to rise below {start}.", ko: "{start}\uBCF4\uB2E4 \uC904\uC5EC\uC57C \uC810\uC218\uAC00 \uC624\uB974\uAE30 \uC2DC\uC791\uD569\uB2C8\uB2E4." },
  nextAbove: { en: "The score starts to rise above {start}.", ko: "{start}\uBCF4\uB2E4 \uB298\uB824\uC57C \uC810\uC218\uAC00 \uC624\uB974\uAE30 \uC2DC\uC791\uD569\uB2C8\uB2E4." },
  nextAfter: { en: "AQ {aq} once fixed up to here", ko: "\uC5EC\uAE30\uAE4C\uC9C0 \uACE0\uCE58\uBA74 AQ {aq}" },
  howTitle: { en: "How the score works", ko: "\uC810\uC218 \uB9E4\uAE30\uB294 \uBC95" },
  howAq: { en: "AQ is the average of the four dimension scores (Setup, Efficiency, Fit, Intensity), rounded. A dimension that could not be measured is left out.", ko: "AQ\uB294 \uB124 \uAE30\uC900(\uC14B\uD305, \uD6A8\uC728, \uC0C1\uD669 \uC801\uD569, \uAC15\uB3C4) \uC810\uC218\uC758 \uD3C9\uADE0\uC744 \uBC18\uC62C\uB9BC\uD55C \uAC12\uC785\uB2C8\uB2E4. \uC7AC\uC9C0 \uBABB\uD55C \uAE30\uC900\uC740 \uBE7C\uACE0 \uD3C9\uADE0\uD569\uB2C8\uB2E4." },
  howAxis: { en: "A dimension score is the weighted average of its rule scores on a scale of 100, rounded. A rule that could not be measured is left out.", ko: "\uAE30\uC900 \uC810\uC218\uB294 \uADF8 \uAE30\uC900\uC5D0 \uB4E0 \uADDC\uCE59 \uC810\uC218\uB97C \uBB34\uAC8C\uB85C \uD3C9\uADE0\uD574 100\uC810 \uB9CC\uC810\uC73C\uB85C \uBC14\uAFB8\uACE0 \uBC18\uC62C\uB9BC\uD55C \uAC12\uC785\uB2C8\uB2E4. \uC7AC\uC9C0 \uBABB\uD55C \uADDC\uCE59\uC740 \uBE8D\uB2C8\uB2E4." },
  howRule: { en: "A rule scores 0 at its zero mark and 1 at its full mark, in proportion in between. A rule measured per tool is scored for each tool, then averaged by the number of responses.", ko: "\uADDC\uCE59 \uC810\uC218\uB294 \uC7B0 \uAC12\uC774 0\uC810 \uAE30\uC900\uC774\uBA74 0, \uB9CC\uC810 \uAE30\uC900\uC774\uBA74 1\uC774\uACE0, \uADF8 \uC0AC\uC774\uB294 \uAC70\uB9AC\uC5D0 \uBE44\uB840\uD569\uB2C8\uB2E4. \uB3C4\uAD6C\uB9C8\uB2E4 \uC7AC\uB294 \uADDC\uCE59\uC740 \uB3C4\uAD6C\uB9C8\uB2E4 \uC810\uC218\uB97C \uB0B8 \uB4A4 \uC751\uB2F5 \uC218\uB85C \uD3C9\uADE0\uD569\uB2C8\uB2E4." },
  howRounded: { en: "Measured values on this page are rounded for display; rule scores use the unrounded values.", ko: "\uD654\uBA74\uC758 \uC7B0 \uAC12\uC740 \uBC18\uC62C\uB9BC\uD574 \uBCF4\uC774\uACE0, \uADDC\uCE59 \uC810\uC218\uB294 \uBC18\uC62C\uB9BC\uD558\uAE30 \uC804 \uAC12\uC73C\uB85C \uACC4\uC0B0\uD569\uB2C8\uB2E4." },
  howGrades: { en: "Grades are S 90 or higher, A 80 to 89, B 65 to 79, C 50 to 64, and D 49 or lower.", ko: "\uB4F1\uAE09\uC740 S 90 \uC774\uC0C1, A 80~89, B 65~79, C 50~64, D 49 \uC774\uD558\uC785\uB2C8\uB2E4." },
  howWithheld: { en: "No AQ is given when the last {days} days have fewer than {requests} requests from you or fewer than {active} days of use.", ko: "\uCD5C\uADFC {days}\uC77C \uB3D9\uC548 \uC0AC\uB78C \uC694\uCCAD\uC774 {requests}\uAC1C\uBCF4\uB2E4 \uC801\uAC70\uB098 \uC4F4 \uB0A0\uC774 {active}\uC77C\uBCF4\uB2E4 \uC801\uC73C\uBA74 AQ\uB97C \uB0B4\uC9C0 \uC54A\uC2B5\uB2C8\uB2E4." },
  howTable: { en: "Weights and marks of the {n} rules", ko: "\uADDC\uCE59 {n}\uAC1C\uC758 \uBB34\uAC8C\uC640 \uAE30\uC900" },
  thRule: { en: "Rule", ko: "\uADDC\uCE59" },
  thWeight: { en: "Weight", ko: "\uBB34\uAC8C" },
  thZero: { en: "Zero mark", ko: "0\uC810 \uAE30\uC900" },
  thFull: { en: "Full mark", ko: "\uB9CC\uC810 \uAE30\uC900" },
  failedSessions: { en: "{n} {n:session|sessions}", ko: "\uC138\uC158 {n}\uAC1C" },
  overlapProject: { en: "Project with the most overlap", ko: "\uAC00\uC7A5 \uB9CE\uC774 \uACB9\uCE58\uB294 \uD504\uB85C\uC81D\uD2B8" },
  serversOut: { en: "{n} {n:server|servers} left out of the judgment", ko: "\uD310\uC815\uC5D0\uC11C \uBE80 \uC11C\uBC84 {n}\uAC1C" },
  judgeFrom: { en: "If nothing else changes, it can be judged from the check-up {n} {n:day|days} from now.", ko: "\uB2E4\uB978 \uC870\uAC74\uC774 \uAC19\uC73C\uBA74 {n}\uC77C \uB4A4\uC758 \uC810\uAC80\uBD80\uD130 \uD310\uC815\uD560 \uC218 \uC788\uC2B5\uB2C8\uB2E4." },
  judgeUnknown: { en: "The day judging can start could not be worked out.", ko: "\uD310\uC815\uC744 \uC2DC\uC791\uD560 \uB0A0\uC744 \uC815\uD558\uC9C0 \uBABB\uD588\uC2B5\uB2C8\uB2E4." },
  judgeChange: { en: "The day moves if the server is called or its definition changes in the meantime.", ko: "\uADF8 \uC0AC\uC774\uC5D0 \uBD80\uB974\uAC70\uB098 \uC815\uC758\uAC00 \uBC14\uB00C\uBA74 \uB0A0\uC774 \uB2EC\uB77C\uC9D1\uB2C8\uB2E4." },
  judgeNotSaved: { en: "This check-up was not saved, so for servers seen for the first time the day may move later.", ko: "\uC774\uBC88 \uC810\uAC80\uC740 \uC800\uC7A5\uD558\uC9C0 \uC54A\uC544, \uC774\uBC88\uC5D0 \uCC98\uC74C \uBCF8 \uC11C\uBC84\uB294 \uB0A0\uC774 \uB4A4\uB85C \uBC00\uB9B4 \uC218 \uC788\uC2B5\uB2C8\uB2E4." },
  blockWith: { en: "Setting to block it", ko: "\uB9C9\uC744 \uB54C \uC4F8 \uC124\uC815" },
  blockNote: { en: 'This is the display name set by claude.ai. It can change, and a name that clashes gets " (N)" added.', ko: '\uC774 \uC774\uB984\uC740 claude.ai\uAC00 \uC815\uD558\uB294 \uD45C\uC2DC \uC774\uB984\uC774\uB77C \uBC14\uB014 \uC218 \uC788\uACE0, \uC774\uB984\uC774 \uACB9\uCE58\uBA74 \uB4A4\uC5D0 " (N)"\uC774 \uBD99\uC2B5\uB2C8\uB2E4.' },
  avgList: { en: "Doing okay", ko: "\uBCF4\uD1B5" },
  unmList: { en: "Not measured", ko: "\uC7B4 \uC218 \uC5C6\uC74C" },
  none: { en: "None", ko: "\uC5C6\uC74C" },
  use: { en: "Mileage", ko: "\uC0AC\uC6A9 \uAE30\uB85D" },
  kMain: { en: "Main sessions", ko: "\uC8FC \uC138\uC158" },
  kDays: { en: "Active days", ko: "\uC0AC\uC6A9\uD55C \uB0A0" },
  kOut: { en: "Output tokens", ko: "\uCD9C\uB825 \uD1A0\uD070" },
  kCache: { en: "Cache hits", ko: "\uCE90\uC2DC \uC801\uC911" },
  hist: { en: "Checkup history", ko: "\uC810\uAC80 \uC774\uB825" },
  histDelta: { en: "{d} since the last checkup", ko: "\uC9C0\uB09C \uC810\uAC80\uBCF4\uB2E4 {d}" },
  histList: { en: "AQ of recent checkups: {list}.", ko: "\uCD5C\uADFC \uC810\uAC80\uC758 AQ\uB294 {list}\uC785\uB2C8\uB2E4." },
  cal: { en: "Replies per day", ko: "\uB0A0\uC9DC\uBCC4 \uC751\uB2F5 \uC218" },
  calAria: { en: "Replies per day from {from} to {to}. {u} {u:day|days} used, {n} not used, {x} with no records kept. Busiest day: {max} {max:reply|replies}.", ko: "{from}\uBD80\uD130 {to}\uAE4C\uC9C0 \uB0A0\uC9DC\uBCC4 \uC751\uB2F5 \uC218. \uC4F4 \uB0A0 {u}\uC77C, \uC548 \uC4F4 \uB0A0 {n}\uC77C, \uAE30\uB85D\uC774 \uB0A8\uC544 \uC788\uC9C0 \uC54A\uC740 \uB0A0 {x}\uC77C, \uAC00\uC7A5 \uB9CE\uC740 \uB0A0 {max}\uAC1C" },
  toolsTable: { en: "Main sessions and output tokens by tool", ko: "\uB3C4\uAD6C\uBCC4 \uC8FC \uC138\uC158\uACFC \uCD9C\uB825 \uD1A0\uD070" },
  thTool: { en: "Tool", ko: "\uB3C4\uAD6C" },
  less: { en: "Less", ko: "\uC801\uC74C" },
  more: { en: "More", ko: "\uB9CE\uC74C" },
  lgUnused: { en: "Not used", ko: "\uC548 \uC4F4 \uB0A0" },
  lgUnseen: { en: "No records kept", ko: "\uAE30\uB85D\uC774 \uB0A8\uC544 \uC788\uC9C0 \uC54A\uC740 \uB0A0" },
  asTable: { en: "Show tables", ko: "\uD45C\uB85C \uBCF4\uAE30" },
  asChart: { en: "Show charts", ko: "\uADF8\uB9BC\uC73C\uB85C \uBCF4\uAE30" },
  thDate: { en: "Date", ko: "\uB0A0\uC9DC" },
  thReplies: { en: "Replies", ko: "\uC751\uB2F5 \uC218" },
  thState: { en: "State", ko: "\uC0C1\uD0DC" },
  stUsed: { en: "Used", ko: "\uC4F4 \uB0A0" },
  byTool: { en: "By tool", ko: "\uB3C4\uAD6C\uBCC4" },
  shell: { en: "Shell commands that ended with a non-zero code: {v} \xB7 not scored", ko: "\uC178 \uBA85\uB839\uC774 0\uC774 \uC544\uB2CC \uAC12\uC73C\uB85C \uB05D\uB09C \uBAAB {v} \xB7 \uC810\uC218\uC5D0 \uB123\uC9C0 \uC54A\uC74C" },
  notices: { en: "Notices", ko: "\uC54C\uB9BC" },
  partialRead: { en: "Only part of the {tool} records could be read. {share} of them could not be read.", ko: "{tool} \uAE30\uB85D\uC744 \uC77C\uBD80\uB9CC \uC77D\uC5C8\uC2B5\uB2C8\uB2E4. \uC77D\uC9C0 \uBABB\uD55C \uBE44\uC728\uC740 {share}\uC785\uB2C8\uB2E4." },
  partialReadAtLeast: { en: "Only part of the {tool} records could be read. At least {share} of them could not be read.", ko: "{tool} \uAE30\uB85D\uC744 \uC77C\uBD80\uB9CC \uC77D\uC5C8\uC2B5\uB2C8\uB2E4. \uC77D\uC9C0 \uBABB\uD55C \uBE44\uC728\uC740 \uC801\uC5B4\uB3C4 {share}\uC785\uB2C8\uB2E4." },
  partialReadUnknown: { en: "Only part of the {tool} records could be read. How much could not be read is unknown.", ko: "{tool} \uAE30\uB85D\uC744 \uC77C\uBD80\uB9CC \uC77D\uC5C8\uC2B5\uB2C8\uB2E4. \uC5BC\uB9C8\uB098 \uC77D\uC9C0 \uBABB\uD588\uB294\uC9C0\uB294 \uC54C \uC218 \uC5C6\uC2B5\uB2C8\uB2E4." },
  footCalc: { en: "Computed on this PC.", ko: "\uC774 PC\uC5D0\uC11C \uACC4\uC0B0\uD588\uC2B5\uB2C8\uB2E4." },
  footPromise: {
    en: "The program and the report page make no network requests. What the program prints goes to the AI in your current session. For a checkup, that is the scores, the counts, the paths of the report and result files, and the names of what to fix, such as MCP servers that failed to connect and where API keys are written. For a tune-up, it is also the names of what to tune up, the paths of the settings files, and the keys and values it proposes to change. The values of API keys, your conversations, and the text of your instructions are not sent. If you ask for a deep checkup, the AI reads only the instruction files you pick.",
    ko: "\uD504\uB85C\uADF8\uB7A8\uACFC \uACB0\uACFC \uD654\uBA74\uC740 \uB124\uD2B8\uC6CC\uD06C\uB85C \uC694\uCCAD\uC744 \uBCF4\uB0B4\uC9C0 \uC54A\uC2B5\uB2C8\uB2E4. \uD504\uB85C\uADF8\uB7A8\uC774 \uB0B4\uB193\uB294 \uAE00\uC740 \uC9C0\uAE08 \uC4F0\uB294 AI \uB300\uD654\uB85C \uC804\uD574\uC9D1\uB2C8\uB2E4. \uC810\uAC80\uC774\uBA74 \uC810\uC218\uC640 \uC9D1\uACC4, \uACB0\uACFC \uD654\uBA74\uACFC \uACB0\uACFC \uD30C\uC77C\uC758 \uACBD\uB85C, \uACE0\uCE60 \uB300\uC0C1\uC758 \uC774\uB984(\uC5F0\uACB0\uC5D0 \uC2E4\uD328\uD55C \uC11C\uBC84, API \uD0A4\uAC00 \uC801\uD78C \uC790\uB9AC \uAC19\uC740 \uAC83)\uC785\uB2C8\uB2E4. \uC815\uBE44\uBA74 \uC815\uBE44\uD560 \uAC83\uC758 \uC774\uB984, \uC124\uC815 \uD30C\uC77C\uC758 \uACBD\uB85C, \uBC14\uAFC0 \uD56D\uBAA9\uACFC \uADF8 \uAC12\uB3C4 \uC804\uD574\uC9D1\uB2C8\uB2E4. API \uD0A4\uC758 \uAC12\uACFC \uB300\uD654 \uB0B4\uC6A9, \uC9C0\uCE68\uC758 \uAE00\uC740 \uBCF4\uB0B4\uC9C0 \uC54A\uC2B5\uB2C8\uB2E4. \uC815\uBC00 \uC810\uAC80\uC744 \uC2DC\uD0A4\uBA74 \uACE0\uB978 \uC9C0\uCE68 \uD30C\uC77C\uB9CC AI\uAC00 \uC77D\uC2B5\uB2C8\uB2E4."
  },
  footNames: { en: "This file contains the names of your skills and project folders. Anyone you send the file to can see them. To share your result, use the card.", ko: "\uC774 \uD30C\uC77C\uC5D0\uB294 \uC2A4\uD0AC\uACFC \uD504\uB85C\uC81D\uD2B8 \uD3F4\uB354\uC758 \uC774\uB984\uC774 \uB4E4\uC5B4 \uC788\uC2B5\uB2C8\uB2E4. \uD30C\uC77C\uC9F8 \uBCF4\uB0B4\uBA74 \uADF8 \uC774\uB984\uB3C4 \uBCF4\uC785\uB2C8\uB2E4. \uACB0\uACFC\uB97C \uB098\uB20C \uB54C\uB294 \uCE74\uB4DC\uB97C \uC4F0\uC138\uC694." },
  cardBtn: { en: "Save as card", ko: "\uCE74\uB4DC\uB85C \uC800\uC7A5" },
  cardTitle: { en: "Share card", ko: "\uACF5\uC720 \uCE74\uB4DC" },
  download: { en: "Download", ko: "\uB0B4\uB824\uBC1B\uAE30" },
  close: { en: "Close", ko: "\uB2EB\uAE30" },
  cardNote: { en: "If the download is blocked, right-click the image, or press and hold it on a phone, to save it.", ko: "\uB0B4\uB824\uBC1B\uAE30\uAC00 \uB9C9\uD788\uBA74 \uADF8\uB9BC\uC744 \uC624\uB978\uCABD \uB2E8\uCD94\uB85C \uB204\uB974\uAC70\uB098, \uD734\uB300\uD3F0\uC5D0\uC11C\uB294 \uAE38\uAC8C \uB20C\uB7EC \uC800\uC7A5\uD558\uC138\uC694." },
  cardFail: { en: "The card could not be drawn in this browser.", ko: "\uC774 \uBE0C\uB77C\uC6B0\uC800\uC5D0\uC11C \uCE74\uB4DC\uB97C \uADF8\uB9AC\uC9C0 \uBABB\uD588\uC2B5\uB2C8\uB2E4." },
  cardAlt: { en: "Share card: AQ {aq}, grade {grade}, {name}, with the four axis scores", ko: "\uACF5\uC720 \uCE74\uB4DC. AQ {aq}, {grade}\uB4F1\uAE09 {name}, \uB124 \uAE30\uC900 \uC810\uC218" },
  cardRepo: { en: "github.com/yeunlee1/chunsik-garage", ko: "github.com/yeunlee1/chunsik-garage" }
};
var WEEKDAYS = { en: ["M", "T", "W", "T", "F", "S", "S"], ko: ["\uC6D4", "\uD654", "\uC218", "\uBAA9", "\uAE08", "\uD1A0", "\uC77C"] };
var STATUS_COPY = {
  critical: { en: "Serious", ko: "\uC2EC\uAC01" },
  caution: { en: "Caution", ko: "\uC8FC\uC758" },
  info: { en: "Note", ko: "\uCC38\uACE0" },
  good: { en: "Good", ko: "\uC591\uD638" },
  average: { en: "Okay", ko: "\uBCF4\uD1B5" },
  unmeasured: { en: "Not measured", ko: "\uC7B4 \uC218 \uC5C6\uC74C" }
};
var PROBLEM_KIND_COPY = {
  unparsable: { en: "unparsable settings file", ko: "\uD480\uB9AC\uC9C0 \uC54A\uB294 \uC124\uC815 \uD30C\uC77C" },
  noFrontmatter: { en: "skill without a header", ko: "\uBA38\uB9AC\uB9D0\uC774 \uC5C6\uB294 \uC2A4\uD0AC" },
  danglingLink: { en: "link that points nowhere", ko: "\uAC00\uB9AC\uD0A4\uB294 \uACF3\uC774 \uC5C6\uB294 \uB9C1\uD06C" }
};
var SCENE_ALT = {
  "scene-1": { en: "An angry Chunsik slashes a messy sheet with a pipe wrench like lightning while Chunsam looks on, startled", ko: "\uD654\uB09C \uCD98\uC2DD\uC774\uAC00 \uD30C\uC774\uD504\uB80C\uCE58\uB85C \uC5C9\uB9DD\uC778 \uBA85\uC138\uC11C\uB97C \uBC88\uAC1C\uCC98\uB7FC \uBCA0\uACE0, \uCD98\uC0BC\uC774\uAC00 \uB4A4\uC5D0\uC11C \uB180\uB77C\uB294 \uADF8\uB9BC" },
  "scene-2": { en: "Chunsik glares at a crumpled sheet while Chunsam waits with a toolbox", ko: "\uCD98\uC2DD\uC774\uAC00 \uAD6C\uACA8\uC9C4 \uBA85\uC138\uC11C\uB97C \uB178\uB824\uBCF4\uACE0, \uCD98\uC0BC\uC774\uAC00 \uACF5\uAD6C\uD568\uC744 \uB4E4\uACE0 \uAE30\uB2E4\uB9AC\uB294 \uADF8\uB9BC" },
  "scene-3": { en: "Chunsik fixes a car while Chunsam hands over a screwdriver", ko: "\uCD98\uC2DD\uC774\uAC00 \uC190\uB2D8 \uCC28\uB97C \uACE0\uCE58\uACE0, \uCD98\uC0BC\uC774\uAC00 \uB4DC\uB77C\uC774\uBC84\uB97C \uAC74\uB124\uB294 \uADF8\uB9BC" },
  "scene-4": { en: "Chunsik stamps a clean sheet while Chunsam gives a thumbs-up", ko: "\uCD98\uC2DD\uC774\uAC00 \uAE68\uB057\uD55C \uBA85\uC138\uC11C\uC5D0 \uD569\uACA9 \uB3C4\uC7A5\uC744 \uCC0D\uACE0, \uCD98\uC0BC\uC774\uAC00 \uC5C4\uC9C0\uB97C \uB4E0 \uADF8\uB9BC" },
  "scene-5": { en: "Chunsik and Chunsam jump and toss sheets into the air", ko: "\uCD98\uC2DD\uC774\uC640 \uCD98\uC0BC\uC774\uAC00 \uB6F0\uC5B4\uC624\uB974\uBA70 \uBA85\uC138\uC11C\uB97C \uD558\uB298\uB85C \uB358\uC9C0\uB294 \uADF8\uB9BC" },
  "scene-few-records": { en: "Chunsam holds a checklist with only a couple of lines while Chunsik sits on a toolbox watching an hourglass", ko: "\uCD98\uC0BC\uC774\uAC00 \uC904\uC774 \uB450\uC5B4 \uAC1C\uBFD0\uC778 \uC810\uAC80\uD45C\uB97C \uB4E4\uACE0, \uCD98\uC2DD\uC774\uAC00 \uACF5\uAD6C\uD568\uC5D0 \uC549\uC544 \uBAA8\uB798\uC2DC\uACC4\uB97C \uBCF4\uB294 \uADF8\uB9BC" },
  "scene-unreadable": { en: "Chunsik cannot open a folder with a lock on it while Chunsam peers at it through a magnifying glass", ko: "\uCD98\uC2DD\uC774\uAC00 \uC790\uBB3C\uC1E0\uAC00 \uADF8\uB824\uC9C4 \uC11C\uB958\uCCA0\uC744 \uC5F4\uC9C0 \uBABB\uD574 \uBA38\uC4F1\uD558\uACE0, \uCD98\uC0BC\uC774\uAC00 \uB3CB\uBCF4\uAE30\uB85C \uB4E4\uC5EC\uB2E4\uBCF4\uB294 \uADF8\uB9BC" }
};

// src/report/format.ts
function percent(share2) {
  return `${oneDecimal(share2 * 100)}%`;
}
function shortTokens(value, lang) {
  if (lang === "ko") {
    if (value < 1e4) return groupDigits(value);
    const man = roundHalfUp(value / 1e4);
    if (man < 1e4) return `${groupDigits(man)}\uB9CC`;
    const eok = Math.floor(man / 1e4);
    const rest = man % 1e4;
    return `${groupDigits(eok)}\uC5B5${rest ? ` ${groupDigits(rest)}\uB9CC` : ""}`;
  }
  if (value < 1e3) return groupDigits(value);
  const units = [
    [1e3, "K"],
    [1e6, "M"],
    [1e9, "B"]
  ];
  let index = value >= 1e9 ? 2 : value >= 1e6 ? 1 : 0;
  let tenths = roundHalfUp(value / units[index][0] * 10);
  if (tenths >= 1e4 && index < units.length - 1) {
    index += 1;
    tenths = roundHalfUp(value / units[index][0] * 10);
  }
  return `${groupDigits(Math.floor(tenths / 10))}${tenths % 10 ? `.${tenths % 10}` : ""}${units[index][1]}`;
}

// src/report/script.ts
var SCRIPT_IDS = {
  /** 스크립트에 넘기는 자료(JSON) */
  data: "aq-data",
  /** 눈에 보이는 알림(화면 읽기 프로그램에는 숨긴다) */
  toast: "toast",
  /** 화면 읽기 프로그램에 알리는 자리 */
  live: "live",
  /** 공유 카드 창과 그 안의 그림, 내려받기, 그리지 못했다는 글, 닫기 */
  dialog: "card-dlg",
  cardImage: "card-img",
  cardLink: "card-dl",
  cardFail: "card-fail",
  cardClose: "card-close",
  /** 카드에 다시 그리는 화면의 장면과 얼굴 그림 */
  scene: "art-scene",
  face: "art-face"
};
var SWAP_TARGETS = ["text", "value", "aria-label", "alt", "title"];
var ID = SCRIPT_IDS;
var REPORT_SCRIPT = String.raw`(() => {
"use strict";
const root = document.documentElement;
const dataNode = document.getElementById("${ID.data}");
const data = dataNode ? JSON.parse(dataNode.textContent || "{}") : {};
const ui = data.ui || {};
const card = data.card || null;
const SWAP = ${JSON.stringify(SWAP_TARGETS)};
const FONT = 'system-ui,-apple-system,"Segoe UI","Malgun Gothic",sans-serif';
const MONO = 'ui-monospace,"Cascadia Mono",Consolas,monospace';
const lang = () => (root.getAttribute("data-ui") === "en" ? "en" : "ko");
const pick = (texts) => (texts ? texts[lang()] || "" : "");

/* 알림. 눈에 보이는 알림과 화면 읽기 프로그램용 자리를 따로 둔다 */
const toast = document.getElementById("${ID.toast}");
const live = document.getElementById("${ID.live}");
let toastTimer = 0;
let liveTimer = 0;
const hideToast = () => {
  clearTimeout(toastTimer);
  if (toast) toast.style.display = "none";
};
const announce = (message) => {
  if (live) {
    clearTimeout(liveTimer);
    live.textContent = "";
    liveTimer = setTimeout(() => { live.textContent = message; }, 60);
  }
  if (toast) {
    clearTimeout(toastTimer);
    toast.textContent = message;
    toast.style.display = "block";
    toastTimer = setTimeout(hideToast, 2600);
  }
};

/* 언어 바꾸기. 다시 그리지 않으므로 펼친 항목과 초점이 그대로다. 떠 있는 알림과 말풍선은 지난 언어의 글이라 닫는다 */
const setLang = (next) => {
  if (next !== "en" && next !== "ko") return;
  hideToast();
  clearTimeout(liveTimer);
  if (live) live.textContent = "";
  document.querySelectorAll(".tip").forEach((tip) => { tip.style.display = "none"; });
  root.setAttribute("data-ui", next);
  root.setAttribute("lang", next);
  document.querySelectorAll("[data-set-lang]").forEach((button) => button.setAttribute("aria-pressed", String(button.getAttribute("data-set-lang") === next)));
  const prefix = "data-" + next + "-";
  document.querySelectorAll("[data-tr]").forEach((el) => {
    Array.from(el.attributes).forEach((attr) => {
      if (!attr.name.startsWith(prefix)) return;
      const target = attr.name.slice(prefix.length);
      if (!SWAP.includes(target)) return;
      if (target === "text") el.textContent = attr.value;
      else if (target === "value") el.value = attr.value;
      else el.setAttribute(target, attr.value);
    });
  });
};

/* 두 언어의 글을 담은 요소 */
const both = (texts, tag) => {
  const holder = document.createElement(tag);
  ["en", "ko"].forEach((code) => {
    const span = document.createElement("span");
    span.setAttribute("lang", code);
    span.setAttribute("data-l", code);
    span.textContent = texts ? texts[code] || "" : "";
    holder.appendChild(span);
  });
  return holder;
};

/* 붙여 넣을 말 복사. 막히면 글상자에 골라 놓고 보인다(설계 13.2). 단추 하나에 글상자는 하나다 */
let boxCount = 0;
const removeCopyBox = (button) => {
  const old = button.nextElementSibling;
  if (old && old.classList.contains("copybox")) old.remove();
};
const showCopyBox = (button, phrases) => {
  hideToast();
  /* 앞선 복사 요청이 늦게 거절돼도 글상자가 겹치지 않게 넣기 직전에 다시 지운다 */
  removeCopyBox(button);
  const box = document.createElement("div");
  box.className = "copybox";
  const note = both(ui.copyFail, "p");
  boxCount += 1;
  note.id = "copy-note-" + boxCount;
  const area = document.createElement("textarea");
  area.readOnly = true;
  area.rows = 2;
  area.setAttribute("data-tr", "");
  ["en", "ko"].forEach((code) => {
    area.setAttribute("data-" + code + "-value", phrases[code]);
    area.setAttribute("data-" + code + "-aria-label", ui.copyLabel ? ui.copyLabel[code] || "" : "");
  });
  area.value = phrases[lang()];
  area.setAttribute("aria-label", pick(ui.copyLabel));
  area.setAttribute("aria-describedby", note.id);
  box.appendChild(note);
  box.appendChild(area);
  button.insertAdjacentElement("afterend", box);
  area.focus();
  area.select();
};
const copy = (button) => {
  const phrases = { en: button.getAttribute("data-phrase-en") || "", ko: button.getAttribute("data-phrase-ko") || "" };
  removeCopyBox(button);
  const clip = navigator.clipboard;
  if (!clip || !window.isSecureContext) {
    showCopyBox(button, phrases);
    return;
  }
  clip.writeText(phrases[lang()]).then(() => announce(pick(ui.copied)), () => showCopyBox(button, phrases));
};

/* 표로 보기와 그림으로 보기 */
const toggleTable = (button) => {
  const section = button.closest(".use");
  if (section) section.classList.toggle("as-table");
};

/* 달력의 말풍선(마우스). 키보드와 화면 읽기 프로그램은 표로 보기를 쓴다 */
const isCell = (node) => node instanceof Element && node.closest("[data-tip-en]") !== null;
document.addEventListener("mouseover", (event) => {
  if (!isCell(event.target)) return;
  const cell = event.target.closest("[data-tip-en]");
  const wrap = cell.closest(".heatwrap");
  const tip = wrap ? wrap.querySelector(".tip") : null;
  if (!tip) return;
  const box = cell.getBoundingClientRect();
  const frame = wrap.getBoundingClientRect();
  tip.textContent = cell.getAttribute("data-tip-" + lang()) || "";
  tip.style.left = box.left - frame.left + box.width / 2 + "px";
  tip.style.top = box.top - frame.top + "px";
  tip.style.display = "block";
});
document.addEventListener("mouseout", (event) => {
  if (!isCell(event.target) || isCell(event.relatedTarget)) return;
  const wrap = event.target.closest(".heatwrap");
  const tip = wrap ? wrap.querySelector(".tip") : null;
  if (tip) tip.style.display = "none";
});

/* 공유 카드 1(명세서 꼴). 브라우저 안에서 1200x630 PNG를 그린다(설계 14) */
const dialog = document.getElementById("${ID.dialog}");
let opener = null;
const imageFrom = (id) => new Promise((resolve) => {
  const source = document.getElementById(id);
  const src = source ? source.getAttribute("src") : null;
  if (!src) {
    resolve(null);
    return;
  }
  const image = new Image();
  image.onload = () => resolve(image);
  image.onerror = () => resolve(null);
  image.src = src;
});
const roundRect = (g, x, y, w, h, r) => {
  g.beginPath();
  g.moveTo(x + r, y);
  g.arcTo(x + w, y, x + w, y + h, r);
  g.arcTo(x + w, y + h, x, y + h, r);
  g.arcTo(x, y + h, x, y, r);
  g.arcTo(x, y, x + w, y, r);
  g.closePath();
};
const drawCard = async () => {
  const [scene, face] = await Promise.all([imageFrom("${ID.scene}"), imageFrom("${ID.face}")]);
  const canvas = document.createElement("canvas");
  canvas.width = 1200;
  canvas.height = 630;
  const g = canvas.getContext("2d");
  if (!g) throw new Error("canvas");
  const ink = "#0b0b0b";
  const ink2 = "#52514e";
  const navy = "#2e3566";
  g.fillStyle = "#fcfcfb";
  g.fillRect(0, 0, 1200, 630);
  g.fillStyle = "#3ab4aa";
  g.fillRect(0, 0, 1200, 12);
  g.save();
  g.beginPath();
  g.arc(82, 62, 22, 0, Math.PI * 2);
  g.clip();
  if (face) g.drawImage(face, 60, 40, 44, 44);
  else {
    g.fillStyle = "#f3f2ee";
    g.fillRect(60, 40, 44, 44);
  }
  g.restore();
  g.textAlign = "left";
  g.fillStyle = ink2;
  g.font = "800 20px " + FONT;
  g.fillText(pick(card.brand), 118, 62, 560);
  g.fillStyle = ink;
  g.font = "800 26px " + FONT;
  g.fillText(pick(card.title), 118, 90, 560);
  g.save();
  roundRect(g, 60, 130, 400, 400, 28);
  g.clip();
  if (scene) g.drawImage(scene, 60, 130, 400, 400);
  else {
    g.fillStyle = "#f3f2ee";
    g.fillRect(60, 130, 400, 400);
  }
  g.restore();
  g.fillStyle = ink;
  g.font = "800 210px " + FONT;
  g.fillText(String(card.aq), 500, 330, 400);
  g.fillStyle = ink2;
  g.font = "700 20px " + FONT;
  g.fillText(pick(card.aqLabel), 508, 366, 400);
  g.save();
  g.translate(1010, 220);
  g.rotate((-13 * Math.PI) / 180);
  g.strokeStyle = navy;
  g.fillStyle = "rgba(252,252,251,.8)";
  g.lineWidth = 4;
  g.beginPath();
  g.arc(0, 0, 78, 0, Math.PI * 2);
  g.fill();
  g.stroke();
  g.lineWidth = 1.5;
  g.beginPath();
  g.arc(0, 0, 70, 0, Math.PI * 2);
  g.stroke();
  g.fillStyle = navy;
  g.textAlign = "center";
  g.font = "800 70px " + FONT;
  g.fillText(card.grade, 0, 22, 120);
  g.font = "800 12px " + FONT;
  g.fillText(pick(card.gradeLabel), 0, 48, 110);
  g.restore();
  g.textAlign = "left";
  g.fillStyle = ink;
  g.font = "800 34px " + FONT;
  g.fillText(pick(card.nick), 508, 412, 632);
  card.axes.forEach((axis, index) => {
    const y = 456 + index * 34;
    g.textAlign = "left";
    g.fillStyle = ink;
    g.font = "700 22px " + FONT;
    g.fillText(pick(axis.name), 508, y + 9, 140);
    g.fillStyle = "#cde2fb";
    roundRect(g, 658, y - 4, 340, 14, 7);
    g.fill();
    if (axis.score !== null && axis.score > 0) {
      g.fillStyle = "#2a78d6";
      roundRect(g, 658, y - 4, Math.max(14, (340 * axis.score) / 100), 14, 7);
      g.fill();
    }
    g.textAlign = "right";
    g.fillStyle = ink;
    g.font = "700 24px " + MONO;
    g.fillText(axis.score === null ? "—" : String(axis.score), 1058, y + 10);
  });
  g.fillStyle = ink2;
  g.font = "700 20px " + MONO;
  g.textAlign = "left";
  g.fillText(card.today, 60, 600);
  g.textAlign = "right";
  g.fillText(pick(card.repo), 1140, 600);
  return canvas;
};
const openCard = (button) => {
  if (!card || !dialog) return;
  const image = document.getElementById("${ID.cardImage}");
  const link = document.getElementById("${ID.cardLink}");
  const fail = document.getElementById("${ID.cardFail}");
  if (!image || !link || !fail) return;
  opener = button;
  image.hidden = true;
  link.hidden = true;
  fail.hidden = true;
  dialog.showModal();
  drawCard()
    .then((canvas) => {
      const url = canvas.toDataURL("image/png");
      image.src = url;
      image.alt = pick(card.alt);
      image.hidden = false;
      link.href = url;
      link.download = card.file;
      link.hidden = false;
    })
    .catch(() => {
      fail.hidden = false;
    });
};
if (dialog) {
  const close = document.getElementById("${ID.cardClose}");
  if (close) close.addEventListener("click", () => dialog.close());
  dialog.addEventListener("close", () => {
    if (opener) opener.focus();
  });
}

document.addEventListener("click", (event) => {
  const target = event.target;
  if (!(target instanceof Element)) return;
  const langButton = target.closest("[data-set-lang]");
  if (langButton) {
    setLang(langButton.getAttribute("data-set-lang"));
    return;
  }
  const action = target.closest("[data-act]");
  if (!action) return;
  const kind = action.getAttribute("data-act");
  if (kind === "copy") copy(action);
  else if (kind === "table") toggleTable(action);
  else if (kind === "card") openCard(action);
});
})();`;

// src/report/style.ts
var REPORT_CSS = `
:root{--font:system-ui,-apple-system,"Segoe UI","Malgun Gothic",sans-serif;--mono:ui-monospace,"Cascadia Mono",Consolas,monospace;--paper:#fcfcfb;--ink:#0b0b0b;--ink2:#52514e;--mute:#898781;--hair:#e1e0d9;--wash:#f3f2ee;--track:#cde2fb;--fill:#2a78d6;--stamp:#2e3566;--up:#006300;--teal:#3ab4aa;--navy:#2e3566}
*{box-sizing:border-box}
html[data-ui="en"] [data-l="ko"],html[data-ui="ko"] [data-l="en"]{display:none!important}
[hidden]{display:none!important}
html{scroll-padding-top:12px}
body{margin:0;font-family:var(--font);font-size:16px;line-height:1.5;background:#dedcd5;color:var(--ink);word-break:keep-all;overflow-wrap:anywhere}
button{font:inherit;cursor:pointer;color:inherit}
a{color:inherit}
button:focus-visible,summary:focus-visible,a:focus-visible,[tabindex]:focus-visible,textarea:focus-visible{outline:3px solid #2a78d6;outline-offset:2px;border-radius:4px}
.sr{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}
.toast{position:fixed;left:50%;bottom:24px;transform:translateX(-50%);max-width:min(560px,calc(100% - 32px));padding:10px 16px;border-radius:8px;background:#0b0b0b;color:#fff;font-size:14px;display:none;z-index:40}
.sheet{max-width:1240px;margin:32px auto 80px;background:var(--paper);padding:40px 52px 30px;position:relative;box-shadow:0 1px 0 rgba(11,11,11,.05),0 18px 44px rgba(11,11,11,.12)}
.sheet::before{content:"";position:absolute;inset:0 0 auto 0;height:10px;background:var(--teal)}
.sheet::after{content:"";position:absolute;left:0;right:0;bottom:-11px;height:12px;background:radial-gradient(circle at 12px -1px,var(--paper) 11px,transparent 12px) repeat-x;background-size:24px 12px}
.hd{display:grid;grid-template-columns:1fr auto;gap:16px 24px;align-items:end;padding-bottom:18px;border-bottom:2px solid var(--ink)}
.brandrow{display:flex;align-items:center;gap:10px}
.brandrow img,.brandrow .noart{width:32px;height:32px;border-radius:50%;display:block;flex:none}
.brandrow .noart{background:var(--wash);border:1px solid var(--hair)}
.brand{font-weight:800;letter-spacing:.14em;font-size:12px;text-transform:uppercase;color:var(--ink2)}
.title{font-size:32px;font-weight:800;letter-spacing:-.02em;margin:2px 0 0;line-height:1.15}
.hdr{display:grid;gap:10px;justify-items:end}
.langsw{display:inline-flex;border:1px solid var(--ink);border-radius:8px}
.langsw button{min-height:44px;min-width:44px;padding:0 14px;border:0;border-radius:0;background:var(--paper);font-size:14px;color:var(--ink2)}
.langsw button:first-child{border-radius:7px 0 0 7px}
.langsw button:last-child{border-radius:0 7px 7px 0}
.langsw button+button{border-left:1px solid var(--ink)}
.langsw button[aria-pressed="true"]{background:var(--ink);color:#fff;font-weight:700}
.langsw button:focus-visible{position:relative;z-index:1}
.info{display:grid;grid-auto-flow:column;gap:0;margin:0;border:1px solid var(--ink);border-radius:2px}
.info div{padding:7px 16px;border-left:1px solid var(--ink)}
.info div:first-child{border-left:0}
.info dt{font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--ink2)}
.info dd{margin:0;font-family:var(--mono);font-size:13px;font-weight:700;white-space:nowrap}
.info dd.tx{font-family:var(--font)}
.hero{display:grid;grid-template-columns:264px 330px 1fr;gap:26px 40px;align-items:center;padding:28px 0 26px}
.scene{margin:0}
.scene .pic{width:264px;height:264px;border-radius:20px;overflow:hidden}
.scene img{width:100%;height:100%;object-fit:cover;display:block}
.scene .ph{width:100%;height:100%;display:grid;place-items:center;text-align:center;padding:20px;border:2px dashed var(--mute);border-radius:20px;background:repeating-linear-gradient(135deg,#f3f2ee 0 10px,#ecebe5 10px 20px);color:var(--ink2);font-size:14px;font-weight:700}
.scene figcaption{margin-top:8px;font-size:13px;font-weight:700;color:var(--ink2);text-align:center;line-height:1.4}
.scene figcaption.why{text-align:left;font-weight:400;width:0;min-width:100%}
.score{position:relative;height:170px}
.score .n{font-size:176px;line-height:.86;font-weight:800;letter-spacing:-.06em}
.score .n.none{color:var(--ink2);font-size:52px;letter-spacing:-.02em;line-height:1.1;padding-top:44px}
.score .lb{position:absolute;left:4px;bottom:-6px;font-size:12px;font-weight:700;letter-spacing:.14em;color:var(--ink2)}
.stamp{position:absolute;right:0;top:-2px;width:124px;height:124px;border-radius:50%;border:3px solid var(--stamp);color:var(--stamp);display:grid;place-items:center;text-align:center;transform:rotate(-13deg);font-weight:800;background:rgba(252,252,251,.72)}
.stamp::before{content:"";position:absolute;inset:6px;border:1px solid var(--stamp);border-radius:50%}
.stamp b{display:block;font-size:58px;line-height:1}
.stamp em{font-style:normal;font-size:10px;letter-spacing:.2em}
.axes{display:grid;gap:12px}
.ax{display:grid;grid-template-columns:112px 1fr 64px;gap:16px;align-items:center}
.ax .nm{font-size:15px;font-weight:700;line-height:1.25}
.ax .tr{height:12px;border-radius:6px;background:var(--track);position:relative;overflow:hidden}
.ax .tr.none{background:repeating-linear-gradient(135deg,#ecebe5 0 6px,#f6f5f1 6px 12px)}
.ax .tr i{position:absolute;inset:0 auto 0 0;border-radius:0 4px 4px 0;background:var(--fill)}
.ax .v{font-family:var(--mono);font-size:20px;font-weight:700;text-align:right}
.ax .v.none{font-size:12px;font-family:var(--font);color:var(--ink2);line-height:1.2;overflow-wrap:normal}
.ax .ct{display:block;font-size:12px;font-weight:400;color:var(--ink2);white-space:nowrap}
.ax .ct b{color:var(--ink)}
.verdict{grid-column:1/-1;display:grid;grid-template-columns:1.15fr 1fr 1fr;gap:32px;align-items:start;border-top:1px dashed var(--mute);padding-top:20px}
.verdict h2{margin:0 0 4px;font-size:12px;letter-spacing:.14em;color:var(--ink2);font-weight:700}
.verdict p{margin:0;font-size:17px;line-height:1.5;font-weight:700;letter-spacing:-.01em}
.verdict .pt{display:grid;grid-template-columns:20px 1fr;gap:8px;align-items:start;font-size:14px;line-height:1.45}
.verdict .pt b{display:block;font-size:12px;letter-spacing:.04em;color:var(--ink2);font-weight:700}
.verdict .pt svg{margin-top:2px}
.verdict .pt .nx{display:block;margin-top:6px;color:var(--ink2);font-size:13px}.nw{white-space:nowrap}
h2{font-size:14px;letter-spacing:.06em;text-transform:uppercase;margin:0;color:var(--ink);font-weight:800}
h2 .no{font-family:var(--mono);color:var(--ink2);margin-right:10px;font-weight:700}
h2 .cnt{font-family:var(--mono);margin-left:10px;color:var(--ink2);font-weight:700}
.cols{display:grid;grid-template-columns:1fr 1fr;border-top:1px dashed var(--mute)}
.col{padding:22px 0 8px;min-width:0}
.col:first-child{padding-right:36px;border-right:1px dashed var(--mute)}
.col:last-child{padding-left:36px}
.col>h2{display:flex;align-items:center;padding-bottom:6px;min-height:62px}
.stk{width:56px;height:56px;border-radius:50%;flex:none;margin-left:auto;display:block;object-fit:cover}
.it{display:grid;grid-template-columns:108px minmax(0,1fr);gap:18px;padding:16px 0;border-top:1px solid var(--hair);scroll-margin-top:16px}
.col>.it:first-of-type,.lists .it:first-of-type{border-top:0}
.fig{font-family:var(--mono);font-weight:700;font-size:30px;line-height:1.1;letter-spacing:-.03em;overflow-wrap:normal}
.good .fig{color:var(--up)}
.fig small{display:block;font-family:var(--font);font-size:12px;font-weight:700;letter-spacing:.01em;color:var(--ink2);margin-top:3px;line-height:1.3}
.fig .u{display:block;font-family:var(--font);font-size:13px;font-weight:700;letter-spacing:0;color:var(--ink);margin-top:2px}
.fig.lg{font-size:26px}
.fig.nv{font-family:var(--font);font-size:16px;letter-spacing:0;line-height:1.3;color:var(--ink)}
.sev{display:inline-flex;align-items:flex-start;gap:6px;font-size:12px;font-weight:700;line-height:18px;margin-top:8px}
.sev svg{flex:none}
.it h3{margin:0;font-size:17px;line-height:1.35;letter-spacing:-.01em}
.it .top{display:flex;flex-wrap:wrap;justify-content:space-between;gap:4px 12px;align-items:baseline}
.it .top h3{flex:1 1 12em;min-width:0}
.it .top .tags{display:flex;gap:8px;align-items:baseline;flex-wrap:wrap;justify-content:flex-end}
.it p{margin:4px 0 0;font-size:14px;color:var(--ink2)}
.it p.fix{color:var(--ink)}
.tag{font-size:12px;font-weight:700;white-space:nowrap;color:var(--ink2)}
.tag.up{font-family:var(--mono);color:var(--up)}.tag.kept{color:var(--ink2);border:1px solid var(--hair);border-radius:10px;padding:0 7px;font-weight:600}
.chips{margin:8px 0 0;padding:0;list-style:none;display:flex;flex-wrap:wrap;gap:6px;font-size:12px}
.chips li{font-family:var(--mono);padding:2px 8px;border:1px solid var(--hair);border-radius:12px;background:#fff}
.chips li.k{font-family:var(--font);font-weight:700;color:var(--ink2);border:0;background:none;padding:2px 0}
.chips li small{font-family:var(--font);color:var(--ink2);margin-left:4px}
details{margin-top:2px}
summary{font-size:13px;color:var(--ink2);cursor:pointer;width:max-content;max-width:100%;min-height:44px;padding:12px 0;line-height:20px}
.how p{font-size:13px;background:var(--wash);border-radius:4px;padding:8px 10px;margin-top:4px;color:var(--ink)}
.how p.ln{font-size:12.5px;font-variant-numeric:tabular-nums}
.act{margin-top:10px;min-height:44px;padding:0 14px;border-radius:6px;border:1px solid var(--ink);background:var(--paper);font-size:14px;font-weight:700}
.copybox{margin-top:8px;display:grid;gap:4px;font-size:13px;color:var(--ink)}
.copybox textarea{font-family:var(--mono);font-size:13px;padding:8px;border:1px solid var(--ink);border-radius:4px;resize:vertical;min-height:44px;width:100%}
.names{margin:4px 0 0;padding:0;list-style:none;display:grid;gap:6px}
.names li{font-size:12px;color:var(--ink)}
.names li>b{display:block;font-weight:700;color:var(--ink2);margin-bottom:2px}
.names code{font-family:var(--mono);font-size:12px;background:#fff;border:1px solid var(--hair);border-radius:10px;padding:1px 7px;margin:0 4px 2px 0;display:inline-block}
.names small{font-size:12px;color:var(--ink2);margin:0 8px 2px -2px}
.names .when{display:block;margin:2px 0 4px;color:var(--ink2)}
.names pre{margin:4px 0;padding:6px 8px;background:#fff;border:1px solid var(--hair);border-radius:4px;font-family:var(--mono);font-size:12px;white-space:pre-wrap;overflow-wrap:anywhere}
.lists{border-top:1px dashed var(--mute);padding:6px 0 10px;display:grid;grid-template-columns:1fr 1fr;gap:0 36px}
.lists>details{margin:0;padding:12px 0;min-width:0}
.lists>details>summary{font-size:14px;font-weight:800;color:var(--ink);letter-spacing:.04em}
.lists>details>summary .cnt{font-family:var(--mono);color:var(--ink2)}
.empty{font-size:14px;color:var(--ink2);margin:6px 0 0}
.use{border-top:1px dashed var(--mute);padding:22px 0 20px}
.usehd{display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap}
.use.as-table .chart,.use:not(.as-table) .table,.use.as-table .when-chart,.use:not(.as-table) .when-table{display:none}
.grid2{display:grid;grid-template-columns:minmax(0,320px) minmax(0,1fr);gap:48px;margin-top:22px;align-items:start}
.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-top:14px;border:1px solid var(--hair);border-radius:4px}
.kpi{padding:14px 18px;border-left:1px solid var(--hair)}
.kpi:first-child{border-left:0}
.kpi b{display:block;font-size:30px;letter-spacing:-.03em;line-height:1.15;white-space:nowrap}
.kpi>span{font-size:12px;color:var(--ink2)}
.sub{font-size:12px;font-weight:700;color:var(--ink2);margin:0 0 8px}
.mini-btn{min-height:44px;padding:0 10px;border:1px solid var(--hair);border-radius:6px;background:#fff;font-size:12px;font-weight:700;color:var(--ink)}
.heat{display:grid;grid-template-columns:repeat(7,1fr);gap:3px}
.heat>span{aspect-ratio:1;border-radius:3px}
.heat .wd{aspect-ratio:auto;font-size:11px;color:var(--ink2);text-align:center}
.heat .pad{visibility:hidden}
.heat .unused,.legend .unused{background:#fff;box-shadow:inset 0 0 0 1px var(--hair)}
.heat .unseen,.legend .unseen{background:repeating-linear-gradient(135deg,#d9d7cf 0 2px,#fff 2px 5px)}
.heatwrap{position:relative}
.tip{position:absolute;z-index:5;pointer-events:none;padding:4px 8px;border-radius:6px;font-size:12px;white-space:nowrap;background:#0b0b0b;color:#fff;transform:translate(-50%,-130%);display:none}
.legend{display:flex;flex-wrap:wrap;gap:6px 10px;align-items:center;font-size:12px;margin-top:8px;color:var(--ink2)}
.legend .ramp{display:inline-flex;gap:3px;align-items:center}
.legend i{width:11px;height:11px;border-radius:3px;display:inline-block}
.legend .k{display:inline-flex;gap:5px;align-items:center}
table.tv{border-collapse:collapse;font-size:12px;width:100%}
table.tv th,table.tv td{border-bottom:1px solid var(--hair);padding:4px 6px;text-align:left}
table.tv td.n{font-family:var(--mono);text-align:right}
.tvwrap{max-height:280px;overflow:auto;border:1px solid var(--hair);border-radius:4px}
.tools{display:grid;gap:14px}
.tools .t{display:grid;grid-template-columns:1fr auto;font-size:14px;gap:4px 12px}
.tools .t>b{font-family:var(--mono)}
.splitbar{grid-column:1/-1;display:flex;gap:2px;height:8px;border-radius:4px;overflow:hidden;background:var(--track)}
.splitbar i{display:block;height:100%}
/* \uB3C4\uAD6C \uC774\uB984\uD45C\uB294 \uB760\uC758 \uCC28\uB840\uB300\uB85C \uD55C \uC904\uC5D0 \uB450\uACE0, \uC881\uC73C\uBA74 \uB2E4\uC74C \uC904\uB85C \uB118\uAE34\uB2E4(\uB3C4\uAD6C\uAC00 \uC14B\uC774\uC5B4\uB3C4 \uC77D\uB294 \uCC28\uB840\uAC00 \uB760\uC640 \uAC19\uB2E4) */
.tools .lg{grid-column:1/-1;display:flex;flex-wrap:wrap;gap:4px 16px}
.sw{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:6px}
.tools small{font-size:12px;color:var(--ink2)}
.shell{margin:16px 0 0;font-size:13px;color:var(--ink2)}
.hist{margin:20px 0 0}.histsvg{display:block;width:100%;max-width:420px;height:auto;color:var(--fill)}.histsvg polyline{fill:none;stroke:currentColor;stroke-width:2}.histsvg circle{fill:currentColor}.histd{margin:4px 0 0;font-size:13px;color:var(--ink2)}
.partial{display:grid;grid-template-columns:20px 1fr;gap:8px;align-items:start;margin:18px 0 0;padding:10px 14px;border:1px solid #fab219;border-radius:6px;background:#fff7e0}
.partial svg{margin-top:2px}
.partial p{margin:0;font-size:14px;color:var(--ink)}
.partial p+p{margin-top:4px}
.next{border-top:1px dashed var(--mute);padding:22px 0 14px}.next .lead{margin:6px 0 0;font-size:14px;color:var(--ink2)}.steps{margin:10px 0 0;padding:0;list-style:none;counter-reset:step}.step{counter-increment:step;position:relative;padding:12px 0 12px 36px;border-top:1px solid var(--hair)}.step:first-child{border-top:0}.step::before{content:counter(step);position:absolute;left:0;top:13px;width:24px;height:24px;border-radius:50%;background:var(--teal);color:#fff;font:700 12px/24px var(--mono);text-align:center}.step .sh{display:flex;flex-wrap:wrap;justify-content:space-between;gap:2px 12px;align-items:baseline}.step .sh b{font-size:16px;line-height:1.35;letter-spacing:-.01em;flex:1 1 12em;min-width:0}.step .aq{font-family:var(--mono);font-size:12px;font-weight:700;color:var(--up);white-space:nowrap}.step p{margin:4px 0 0;font-size:14px;color:var(--ink2)}.step p.fix{color:var(--ink)}.step .now{font-variant-numeric:tabular-nums}.how-score{border-top:1px dashed var(--mute);padding:22px 0 18px}.rulesum{margin:10px 0 0;padding:0 0 0 18px;display:grid;gap:4px;font-size:14px;color:var(--ink);line-height:1.5}.ruletable{margin-top:12px}.ruletable>summary{font-size:13px;font-weight:700;color:var(--ink2);cursor:pointer}.ruletable .tvwrap{max-height:none;margin-top:8px}table.rules tr.grp th{background:var(--wash);font-weight:800;color:var(--ink)}table.tv th.n{text-align:right;white-space:nowrap}table.rules td{white-space:nowrap}table.rules th[scope=row]{min-width:9em}.notices{border-top:1px dashed var(--mute);padding:18px 0 16px}
.notices ul{margin:10px 0 0;padding:0;list-style:none;display:grid;gap:8px}
.notices li{display:grid;grid-template-columns:20px 1fr;gap:8px;font-size:14px;color:var(--ink)}
.notices .spots{grid-column:2;margin:2px 0 0;gap:2px}
.notices .spots li{display:block;font-size:13px;color:var(--ink2);overflow-wrap:anywhere}
.ft{display:grid;grid-template-columns:1fr auto;align-items:center;gap:10px 24px;border-top:2px solid var(--ink);padding-top:16px;font-size:13px;color:var(--ink2)}
.ft .lock{display:grid;grid-template-columns:16px 1fr;gap:8px;align-items:start}
.ft .lock svg{margin-top:2px}
.ft .names-note{grid-column:1/-1;margin:0;font-size:13px;color:var(--ink)}
.share{min-height:44px;padding:0 20px;border-radius:6px;border:0;background:var(--ink);color:#fff;font-size:14px;font-weight:700}
dialog.card{width:min(1040px,calc(100% - 24px));max-height:calc(100% - 24px);border:0;border-radius:10px;padding:20px;background:var(--paper)}
dialog.card::backdrop{background:rgba(11,11,11,.55)}
dialog.card h2{font-size:16px;text-transform:none;letter-spacing:0;margin:0 0 12px}
.cardimg{display:block;width:100%;height:auto;border:1px solid var(--hair);border-radius:6px;background:#fff}
.cardft{display:flex;gap:10px;align-items:center;justify-content:space-between;flex-wrap:wrap;margin-top:12px;font-size:13px;color:var(--ink2)}
.cardft .btns{display:flex;gap:8px}
.cardft a,.cardft button{min-height:44px;display:inline-flex;align-items:center;padding:0 16px;border-radius:6px;font-size:14px;font-weight:700;text-decoration:none}
.cardft a{background:var(--ink);color:#fff}
.cardft button{border:1px solid var(--ink);background:var(--paper)}
@media (max-width:1100px){
.sheet{padding:32px 28px 24px}
.hero{grid-template-columns:208px 300px 1fr;gap:22px 28px}
.scene .pic{width:208px;height:208px}
.score{height:146px}.score .n{font-size:150px}
.stamp{width:104px;height:104px}.stamp b{font-size:48px}
.verdict{gap:22px}
.grid2{gap:32px}
}
@media (max-width:920px){
.hero{grid-template-columns:208px 1fr}.axes{grid-column:1/-1}.score{max-width:300px}
.kpis{grid-template-columns:1fr 1fr}.kpi:nth-child(odd){border-left:0}.kpi:nth-child(n+3){border-top:1px solid var(--hair)}
.grid2{grid-template-columns:1fr}
}
@media (max-width:760px){
.scene{justify-self:center}.verdict{grid-template-columns:1fr;gap:14px}
.sheet{margin:0 0 40px;padding:28px 18px 22px}
.hd{grid-template-columns:1fr}.hdr{justify-items:start}
.info{grid-auto-flow:row;grid-template-columns:1fr 1fr}.info div:nth-child(odd){border-left:0}.info div:nth-child(n+3){border-top:1px solid var(--ink)}
.info dd.tl{white-space:normal}.info dd.tl .nm{white-space:nowrap}
.title{font-size:26px}
.hero{grid-template-columns:1fr}.score{height:150px;max-width:330px}.score .n{font-size:150px}
.ax{grid-template-columns:100px 1fr 60px;gap:12px}
.kpi b{font-size:24px}
.cols,.lists{grid-template-columns:1fr}.col:first-child{padding-right:0;border-right:0;border-bottom:1px dashed var(--mute)}.col:last-child{padding-left:0}
.it{grid-template-columns:84px minmax(0,1fr);gap:12px}.fig{font-size:24px}.fig.lg{font-size:21px}
.it .top{flex-direction:column;gap:2px}.it .top h3{flex:none}.it .top .tags{justify-content:flex-start}
.ft{grid-template-columns:1fr}.share{width:100%}
}
@media (prefers-reduced-motion:no-preference){.ax .tr i{transition:width .5s ease-out}}
`;

// src/report/html.ts
var RAMP = ["#cde2fb", "#86b6ef", "#3987e5", "#184f95"];
var TOOL_COLORS = { "claude-code": "#2a78d6", codex: "#c8660a", gemini: "#199e70", "web-chatgpt": "#e87ba4", "web-claude": "#4a3aa7" };
var REPO = "chunsik-garage";
function esc(value) {
  return value.replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[char]);
}
var textsOf2 = (make2) => ({ en: make2("en"), ko: make2("ko") });
var copy = (key, values) => textsOf2((lang) => values === void 0 ? REPORT_COPY[key][lang] : fill(REPORT_COPY[key][lang], values));
var pairHtml = (html) => LANGS.map((lang) => `<span lang="${lang}" data-l="${lang}">${html[lang]}</span>`).join("");
var both = (texts) => pairHtml(textsOf2((lang) => esc(texts[lang])));
var perLang = (make2) => LANGS.map((lang) => make2(lang).replace(/^<([a-z0-9]+)/, `<$1 lang="${lang}" data-l="${lang}"`)).join("");
var swap = (lang, attrs) => ` data-tr${Object.entries(attrs).map(([name, texts]) => ` ${name}="${esc(texts[lang])}" data-en-${name}="${esc(texts.en)}" data-ko-${name}="${esc(texts.ko)}"`).join("")}`;
var keepArrows = (html) => html.replace(/\(→ (\d+)\)/g, '<span class="nw">(\u2192 $1)</span>');
var fillHtml = (template, values) => fill(esc(template), values);
var dayNumber = (date) => {
  const [year, month, day] = date.split("-").map(Number);
  return Date.UTC(year, month - 1, day) / 864e5;
};
var ICONS = {
  critical: '<svg width="18" height="18" viewBox="0 0 18 18" aria-hidden="true"><path d="M9 1.5 17 16H1z" fill="#ec835a"/><rect x="8.1" y="6.2" width="1.8" height="5" fill="#0b0b0b"/><rect x="8.1" y="12.4" width="1.8" height="1.8" fill="#0b0b0b"/></svg>',
  caution: '<svg width="18" height="18" viewBox="0 0 18 18" aria-hidden="true"><path d="M9 1.5 17 16H1z" fill="#fab219"/><rect x="8.1" y="6.2" width="1.8" height="5" fill="#0b0b0b"/><rect x="8.1" y="12.4" width="1.8" height="1.8" fill="#0b0b0b"/></svg>',
  info: '<svg width="18" height="18" viewBox="0 0 18 18" aria-hidden="true"><circle cx="9" cy="9" r="8" fill="#898781"/><rect x="8.1" y="7.6" width="1.8" height="5.4" fill="#fff"/><rect x="8.1" y="4.6" width="1.8" height="1.8" fill="#fff"/></svg>',
  good: '<svg width="18" height="18" viewBox="0 0 18 18" aria-hidden="true"><circle cx="9" cy="9" r="8" fill="#0ca30c"/><path d="M5 9.2 8 12l5-6" stroke="#fff" stroke-width="2" fill="none"/></svg>',
  average: '<svg width="18" height="18" viewBox="0 0 18 18" aria-hidden="true"><circle cx="9" cy="9" r="8" fill="none" stroke="#898781" stroke-width="2"/><rect x="5" y="8.1" width="8" height="1.8" fill="#898781"/></svg>',
  unmeasured: '<svg width="18" height="18" viewBox="0 0 18 18" aria-hidden="true"><circle cx="9" cy="9" r="8" fill="none" stroke="#898781" stroke-width="2" stroke-dasharray="3 2.2"/><rect x="8.1" y="12.2" width="1.8" height="1.8" fill="#52514e"/><path d="M6.6 6.8a2.4 2.4 0 1 1 3.4 2.2c-.7.3-1 .8-1 1.6" stroke="#52514e" stroke-width="1.8" fill="none"/></svg>'
};
var LOCK = '<svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true"><rect x="2.5" y="7" width="11" height="7.5" rx="1.5" fill="#52514e"/><path d="M5 7V5a3 3 0 0 1 6 0v2" stroke="#52514e" stroke-width="1.8" fill="none"/></svg>';
function statusOf(finding) {
  if (finding.category === "strength") return "good";
  if (finding.category === "average") return "average";
  if (finding.category === "unmeasured") return "unmeasured";
  return finding.severity === "critical" ? "critical" : finding.severity === "caution" ? "caution" : "info";
}
function chips(lang, label, items) {
  if (items.length === 0) return "";
  return `<ul class="chips"${swap(lang, { "aria-label": label })}><li class="k" aria-hidden="true">${both(label)}</li>${items.join("")}</ul>`;
}
function figure(finding) {
  return perLang((lang) => {
    const text = finding.text[lang];
    if (text.value === null) return `<div class="fig nv">${esc(REPORT_COPY.unmeasured[lang])}<small>${esc(text.reason ?? "")}</small></div>`;
    const unit = text.unit === null ? "" : text.unit === "%" ? "%" : `<span class="u">${esc(text.unit)}</span>`;
    const long = `${text.value}${text.unit === "%" ? "%" : ""}`.length >= 6 ? " lg" : "";
    return `<div class="fig${long}">${esc(text.value)}${unit}<small>${esc(text.name)}</small></div>`;
  });
}
function serverLine(server) {
  const project = server.projectName === null ? "" : `<small>${esc(server.projectName)}</small>`;
  if (server.why !== "not_established") return `<code>${esc(server.name)}</code>${project}`;
  const day = server.daysUntil !== null && server.daysUntil >= 1 ? copy("judgeFrom", { n: server.daysUntil }) : copy("judgeUnknown");
  return `<span class="srv"><code>${esc(server.name)}</code>${project}<span class="when">${both(day)}</span></span>`;
}
function serversBlock(finding, view) {
  if (finding.ruleId !== "E6" || view.servers.length === 0) return "";
  const notes = perLang((lang) => `<div>${finding.text[lang].notes.map((line) => `<p>${esc(line)}</p>`).join("")}</div>`);
  const order = Object.keys(UNJUDGED_COPY.en.why);
  const groups = order.map((why) => ({ why, servers: view.servers.filter((server) => server.why === why) })).filter((group) => group.servers.length > 0);
  const items = groups.map((group) => {
    const watch = group.why === "not_established" ? `<span class="when">${both(copy("judgeChange"))}</span>${view.saved ? "" : `<span class="when">${both(copy("judgeNotSaved"))}</span>`}` : "";
    return `<li><b>${both(textsOf2((lang) => UNJUDGED_COPY[lang].why[group.why]))}</b>${group.servers.map(serverLine).join("")}${watch}</li>`;
  }).join("");
  const connectors = view.servers.filter((server) => server.scope === "claude-ai");
  const deny = connectors.length === 0 ? "" : `<li><b>${both(copy("blockWith"))}</b><pre>${esc(`[
${connectors.map((server) => `  { "serverName": ${JSON.stringify(server.name)} }`).join(",\n")}
]`)}</pre><span class="when">${both(copy("blockNote"))}</span></li>`;
  return `<details class="how"><summary>${both(copy("serversOut", { n: view.servers.length }))}</summary>${notes}<ul class="names">${items}${deny}</ul></details>`;
}
function ruleChips(finding, view, lang, withTargets) {
  const targets = withTargets ? chips(lang, REPORT_COPY.targets, finding.targets.map((name) => `<li>${esc(name)}</li>`)) : "";
  const places = finding.ruleId === "S3" ? chips(lang, REPORT_COPY.places, view.setupProblems.map((problem) => `<li>${esc(problem.place)}<small>${both(PROBLEM_KIND_COPY[problem.kind])}</small></li>`)) : "";
  const failed = finding.ruleId === "S5" ? chips(lang, REPORT_COPY.failedServers, view.failedServers.map((server) => `<li>${esc(server.name)}<small>${both(copy("failedSessions", { n: server.sessions }))}</small></li>`)) : "";
  const missing = finding.ruleId === "F3" ? chips(lang, REPORT_COPY.missingProjects, view.missingInstructions.map((name) => `<li>${esc(name)}</li>`)) : "";
  const overlap = finding.ruleId === "F4" && view.worstOverlap !== null ? chips(lang, REPORT_COPY.overlapProject, [`<li>${esc(view.worstOverlap)}</li>`]) : "";
  return `${targets}${places}${failed}${missing}${overlap}`;
}
function nextPath(view, lang) {
  const plan = view.nextPlan;
  if (view.score.aq === null || plan === null) return "";
  const lead = textsOf2((l) => fill(REPORT_COPY.nextLead[l], { need: plan.need, grade: plan.grade }) + (plan.reaches ? "" : ` ${fill(REPORT_COPY.nextShort[l], { last: plan.steps.at(-1).aq })}`));
  const steps = plan.steps.map((step) => {
    const finding = view.findings.find((candidate) => candidate.ruleId === step.ruleId);
    if (finding === void 0) return "";
    const spec = ruleSpec(step.ruleId);
    const nowLine = (l, now, value, score, tool) => {
      const target = ruleValueText(step.ruleId, spec.fullAt, l);
      const line = tool === null ? fill(REPORT_COPY.nextNow[l], { now, target }) : fill(REPORT_COPY.nextNowTool[l], { tool: TOOL_NAMES[tool][l], now, target });
      if (settleScore(score) !== 0 || !beyondZeroMark(step.ruleId, value)) return line;
      return `${line} \xB7 ${fill((spec.zeroAt > spec.fullAt ? REPORT_COPY.nextBelow : REPORT_COPY.nextAbove)[l], { start: ruleValueText(step.ruleId, spec.zeroAt, l) })}`;
    };
    const short = finding.tools.length >= 2 ? finding.tools.filter((tool) => settleScore(tool.score) < 1) : [];
    const lines = short.length > 0 ? short.map((tool) => textsOf2((l) => nowLine(l, ruleValueText(step.ruleId, tool.value, l), tool.value, tool.score, tool.tool))) : finding.value === null || finding.score === null || finding.text.en.value === null ? [] : [textsOf2((l) => nowLine(l, joinValue(finding.text[l].value, finding.text[l].unit, l), finding.value, finding.score, null))];
    const fix = finding.text.en.prescription !== null ? `<p class="fix">\u2192 ${both(textsOf2((l) => finding.text[l].prescription ?? ""))}</p>` : "";
    return `<li class="step"><div class="sh"><b>${both(textsOf2((l) => finding.text[l].title))}</b><span class="aq">${both(copy("nextAfter", { aq: step.aq }))}</span></div>${lines.map((line) => `<p class="now">${both(line)}</p>`).join("")}${fix}${ruleChips(finding, view, lang, true)}</li>`;
  }).join("");
  return `<section class="next" aria-labelledby="h-next"><h2 id="h-next">${both(copy("nextTitle", { grade: plan.grade }))}</h2><p class="lead">${both(lead)}</p><ol class="steps">${steps}</ol></section>`;
}
function howScore() {
  const lines = [REPORT_COPY.howAq, REPORT_COPY.howAxis, REPORT_COPY.howRule, REPORT_COPY.howRounded, REPORT_COPY.howGrades, copy("howWithheld", { days: SCORE_WINDOW_DAYS, requests: MIN_REQUESTS_FOR_AQ, active: MIN_DAYS_FOR_AQ })];
  const mark = (ruleId, value) => both(textsOf2((l) => ruleValueText(ruleId, value, l)));
  const rows = AXES.map(
    (axis) => `<tr class="grp"><th colspan="4" scope="colgroup">${both(AXIS_NAMES[axis])}</th></tr>` + RULES.filter((spec) => spec.axis === axis).map((spec) => `<tr class="rule"><th scope="row">${both(textsOf2((l) => RULE_COPY[spec.id][l].name))}</th><td class="n">${spec.weight}</td><td>${mark(spec.id, spec.zeroAt)}</td><td>${mark(spec.id, spec.fullAt)}</td></tr>`).join("")
  ).join("");
  const table = `<table class="tv rules"><thead><tr><th scope="col">${both(REPORT_COPY.thRule)}</th><th scope="col" class="n">${both(REPORT_COPY.thWeight)}</th><th scope="col">${both(REPORT_COPY.thZero)}</th><th scope="col">${both(REPORT_COPY.thFull)}</th></tr></thead><tbody>${rows}</tbody></table>`;
  return `<section class="how-score" aria-labelledby="h-how"><h2 id="h-how"><span class="no">04</span>${both(REPORT_COPY.howTitle)}</h2><ul class="rulesum">${lines.map((line) => `<li>${both(line)}</li>`).join("")}</ul><details class="ruletable"><summary>${both(copy("howTable", { n: RULES.length }))}</summary><div class="tvwrap">${table}</div></details></section>`;
}
function item(finding, view, lang) {
  const status = statusOf(finding);
  const repair = finding.category === "repair";
  const gain = repair && view.score.aq !== null && finding.gain !== null ? finding.gain : null;
  const tag = gain === null ? `<span class="tag">${both(AXIS_NAMES[finding.axis])}</span>` : `<span class="tag up">${both(textsOf2((l) => fill(SUMMARY_COPY[l].gain, { axis: AXIS_NAMES[finding.axis][l], gain })))}</span>`;
  const kept = view.ignored.includes(finding.ruleId) ? `<span class="tag kept">${both(REPORT_COPY.kept)}</span>` : "";
  const description2 = finding.text.en.description || finding.text.ko.description ? `<p>${both(textsOf2((l) => finding.text[l].description))}</p>` : "";
  const prescription = finding.category !== "strength" && finding.text.en.prescription !== null ? `<p class="fix">\u2192 ${both(textsOf2((l) => finding.text[l].prescription ?? ""))}</p>` : "";
  const named2 = ruleChips(finding, view, lang, repair);
  const phrase = textsOf2((l) => fill(REPORT_COPY.phrase[l], { name: finding.text[l].name }));
  const button = repair && finding.targets.length > 0 ? `<button type="button" class="act" data-act="copy" data-phrase-en="${esc(phrase.en)}" data-phrase-ko="${esc(phrase.ko)}">${both(REPORT_COPY.clean)}</button>` : "";
  const how = finding.text.en.method.length + finding.text.ko.method.length === 0 ? "" : `<details class="how"><summary>${both(REPORT_COPY.how)}</summary>${perLang((l) => `<div>${finding.text[l].method.map((line, index) => `<p${index > 0 ? ' class="ln"' : ""}>${esc(line)}</p>`).join("")}</div>`)}</details>`;
  return `<div class="it" id="it-${finding.ruleId}"><div>${figure(finding)}<span class="sev">${ICONS[status]}${both(STATUS_COPY[status])}</span></div><div><div class="top"><h3>${both(textsOf2((l) => finding.text[l].title))}</h3><span class="tags">${kept}${tag}</span></div>${description2}${prescription}${named2}${button}${how}${serversBlock(finding, view)}</div></div>`;
}
function header(view, art, lang) {
  const face = art.face === null ? '<span class="noart" aria-hidden="true"></span>' : `<img id="${SCRIPT_IDS.face}" src="${esc(art.face)}" alt="" width="32" height="32">`;
  const tools2 = view.tools.length === 0 ? `<dd class="tx">${both(REPORT_COPY.noTools)}</dd>` : view.tools.length > 2 ? `<dd class="tl">${pairHtml(textsOf2((l) => view.tools.map((tool) => `<span class="nm">${esc(TOOL_NAMES[tool][l])}</span>`).join(" \xB7 ")))}</dd>` : `<dd>${both(textsOf2((l) => view.tools.map((tool) => TOOL_NAMES[tool][l]).join(" \xB7 ")))}</dd>`;
  const round = !view.saved ? `<dd class="tx">${both(REPORT_COPY.notSaved)}</dd>` : `<dd>${view.round === null ? "\u2014" : both(copy("roundValue", { n: view.round }))}</dd>`;
  const langButton = (code, label) => `<button type="button" data-set-lang="${code}" aria-pressed="${code === lang}" lang="${code}">${label}</button>`;
  return `<header class="hd"><div><div class="brandrow">${face}<div class="brand">${both(REPORT_COPY.brand)}</div></div><h1 class="title" id="h-title">${both(REPORT_COPY.title)}</h1></div><div class="hdr"><div class="langsw" role="group"${swap(lang, { "aria-label": REPORT_COPY.langGroup })}>${langButton("en", "English")}${langButton("ko", "\uD55C\uAD6D\uC5B4")}</div><dl class="info"><div><dt>${both(REPORT_COPY.date)}</dt><dd>${esc(view.today)}</dd></div><div><dt>${both(REPORT_COPY.tools)}</dt>${tools2}</div><div><dt>${both(REPORT_COPY.period)}</dt><dd>${esc(view.window.from.slice(5))} ~ ${esc(view.window.to.slice(5))}</dd></div><div><dt>${both(REPORT_COPY.round)}</dt>${round}</div></dl></div></header>`;
}
function hero(view, art, lang) {
  const scored2 = view.score.aq !== null;
  const alt = SCENE_ALT[sceneFor(view.score.tier, view.unreadable)];
  const picture = art.scene === null ? `<div class="ph" role="img"${swap(lang, { "aria-label": alt })}>${both(alt)}</div>` : `<img id="${SCRIPT_IDS.scene}" src="${esc(art.scene)}" width="264" height="264"${swap(lang, { alt })}>`;
  const caption = scored2 ? `<figcaption>${both(textsOf2((l) => view.text[l].grade ?? ""))}</figcaption>` : view.withheldText === null ? "" : `<figcaption class="why">${both(view.withheldText)}</figcaption>`;
  const score = scored2 ? `<div class="score"><div class="n">${view.score.aq}</div><div class="lb">${both(REPORT_COPY.aqLabel)}</div><div class="stamp" role="img"${swap(lang, { "aria-label": copy("gradeAria", { g: view.score.grade }) })}><div><b>${esc(view.score.grade ?? "")}</b><em>${both(REPORT_COPY.grade)}</em></div></div></div>` : `<div class="score"><div class="n none">${both(REPORT_COPY.noScore)}</div><div class="lb">${both(REPORT_COPY.aqLabel)}</div></div>`;
  const axes = view.axes.map((axis) => {
    const name = AXIS_NAMES[axis.axis];
    const counts = pairHtml(textsOf2((l) => fillHtml(REPORT_COPY.axisCounts[l], { g: `<b>${groupDigits(axis.strengths)}</b>`, f: `<b>${groupDigits(axis.repairs)}</b>` })));
    if (axis.score === null) return `<div class="ax"><span class="nm">${both(name)}<span class="ct">${counts}</span></span><span class="tr none" role="img"${swap(lang, { "aria-label": textsOf2((l) => fill(REPORT_COPY.axisNone[l], { axis: name[l] })) })}></span><span class="v none">${both(REPORT_COPY.unmeasured)}</span></div>`;
    return `<div class="ax"><span class="nm">${both(name)}<span class="ct">${counts}</span></span><span class="tr" role="img"${swap(lang, { "aria-label": textsOf2((l) => fill(REPORT_COPY.axisAria[l], { axis: name[l], v: axis.score })) })}><i style="width:${axis.score}%"></i></span><span class="v">${axis.score}</span></div>`;
  }).join("");
  const rows = view.axes.map((axis) => `<tr><th scope="row">${both(AXIS_NAMES[axis.axis])}</th><td>${axis.score === null ? both(REPORT_COPY.unmeasured) : axis.score}</td><td>${axis.strengths}</td><td>${axis.repairs}</td></tr>`).join("");
  const table = `<table class="sr"><caption>${both(REPORT_COPY.axesTable)}</caption><thead><tr><th scope="col">${both(REPORT_COPY.thAxis)}</th><th scope="col">${both(REPORT_COPY.thScore)}</th><th scope="col">${both(REPORT_COPY.thGood)}</th><th scope="col">${both(REPORT_COPY.thFix)}</th></tr></thead><tbody>${rows}</tbody></table>`;
  const best = view.findings.find((finding) => finding.category === "strength") ?? null;
  const first = scored2 ? view.findings.find((finding) => finding.category === "repair" && !view.ignored.includes(finding.ruleId)) ?? null : null;
  const bestLine = best === null ? "<div></div>" : `<div class="pt">${ICONS.good}<span><b>${both(REPORT_COPY.best)}</b>${both(
    textsOf2((l) => {
      const text = best.text[l];
      const value = text.value === null ? REPORT_COPY.unmeasured[l] : text.unit === null ? text.value : joinValue(text.value, text.unit, l);
      return `${text.title} \xB7 ${fill(SUMMARY_COPY[l].best, { name: text.name, value })}`;
    })
  )}</span></div>`;
  const next = scored2 && view.nextGrade !== null ? `<span class="nx">${pairHtml(textsOf2((l) => keepArrows(esc(view.nextGrade[l]))))}</span>` : "";
  const fixLine = first === null ? next === "" ? "" : `<div class="pt">${ICONS.info}<span><b>${both(REPORT_COPY.nextGrade)}</b>${next}</span></div>` : `<div class="pt">${ICONS[statusOf(first)]}<span><b>${both(REPORT_COPY.fixFirst)}</b>${both(
    textsOf2((l) => `${first.text[l].title} \xB7 ${fixDetail({ ruleId: first.ruleId, axis: first.axis, gain: first.gain, measured: first.measured, candidates: first.targets.length, unmeasuredTools: first.unmeasuredTools, value: first.value, score: first.score, tools: first.tools }, l)}`)
  )}${next}</span></div>`;
  return `<section class="hero"${swap(lang, { "aria-label": REPORT_COPY.scoreAria })}><figure class="scene"><div class="pic">${picture}</div>${caption}</figure>${score}<div class="axes">${axes}${table}</div><div class="verdict"><div><h2>${both(REPORT_COPY.verdict)}</h2><p>${both(textsOf2((l) => view.text[l].diagnosis))}</p></div>${bestLine}${fixLine}</div></section>`;
}
function columns(view, art, lang) {
  const strengths = view.findings.filter((finding) => finding.category === "strength");
  const repairs = view.findings.filter((finding) => finding.category === "repair");
  const sticker = (src) => src === null ? "" : `<img class="stk" src="${esc(src)}" alt="" width="56" height="56">`;
  const good = strengths.length > 0 ? strengths.map((finding) => item(finding, view, lang)).join("") : `<p class="empty">${both(textsOf2((l) => view.text[l].noStrengths ?? ""))}</p>`;
  const fix = repairs.length > 0 ? repairs.map((finding) => item(finding, view, lang)).join("") : `<p class="empty">${both(textsOf2((l) => view.text[l].noRepairs ?? ""))}</p>`;
  return `<div class="cols"><section class="col good" aria-labelledby="h-good"><h2 id="h-good"><span class="no">01</span>${both(REPORT_COPY.colGood)}<span class="cnt">${strengths.length}</span>${sticker(art.good)}</h2>${good}</section><section class="col" aria-labelledby="h-fix"><h2 id="h-fix"><span class="no">02</span>${both(REPORT_COPY.colFix)}<span class="cnt">${repairs.length}</span>${sticker(art.fix)}</h2>${fix}</section></div>`;
}
function lists(view, lang) {
  const block = (key, category) => {
    const found = view.findings.filter((finding) => finding.category === category);
    const body = found.length > 0 ? found.map((finding) => item(finding, view, lang)).join("") : `<p class="empty">${both(REPORT_COPY.none)}</p>`;
    return `<details><summary>${both(REPORT_COPY[key])} <span class="cnt">${found.length}</span></summary>${body}</details>`;
  };
  return `<div class="lists">${block("avgList", "average")}${block("unmList", "unmeasured")}</div>`;
}
var stateWord = (state) => state === "used" ? REPORT_COPY.stUsed : state === "unused" ? REPORT_COPY.lgUnused : REPORT_COPY.lgUnseen;
var tip = (date, texts) => ` data-tip-en="${esc(`${date} \xB7 ${texts.en}`)}" data-tip-ko="${esc(`${date} \xB7 ${texts.ko}`)}"`;
function calendar(view, lang) {
  const cells = view.usage.calendar;
  if (cells.length === 0) return { chart: `<p class="empty">${both(REPORT_COPY.none)}</p>`, table: `<p class="empty">${both(REPORT_COPY.none)}</p>` };
  const used = cells.filter((cell) => cell.state === "used");
  const busiest = used.length > 0 ? Math.max(...used.map((cell) => cell.responses)) : 0;
  const scale = Math.max(1, busiest);
  const aria = copy("calAria", { from: cells[0].date, to: cells.at(-1).date, u: used.length, n: cells.filter((cell) => cell.state === "unused").length, x: cells.filter((cell) => cell.state === "unseen").length, max: busiest });
  const pad = (new Date(dayNumber(cells[0].date) * 864e5).getUTCDay() + 6) % 7;
  const heads = WEEKDAYS.en.map((_, index) => `<span class="wd" aria-hidden="true">${both({ en: WEEKDAYS.en[index], ko: WEEKDAYS.ko[index] })}</span>`).join("");
  const days = cells.map((cell) => {
    if (cell.state === "unseen") return `<span class="unseen"${tip(cell.date, REPORT_COPY.lgUnseen)}></span>`;
    if (cell.state === "unused" || cell.responses === 0) return `<span class="unused"${tip(cell.date, REPORT_COPY.lgUnused)}></span>`;
    const level = Math.max(0, Math.min(3, Math.floor(cell.responses / scale * 4 - 1e-9)));
    const count = groupDigits(cell.responses);
    return `<span style="background:${RAMP[level]}"${tip(cell.date, { en: count, ko: count })}></span>`;
  }).join("");
  const legend = `<div class="legend"><span class="k">${both(REPORT_COPY.less)}<span class="ramp">${RAMP.map((color) => `<i style="background:${color}"></i>`).join("")}</span>${both(REPORT_COPY.more)}</span><span class="k"><i class="unused"></i>${both(REPORT_COPY.lgUnused)}</span><span class="k"><i class="unseen"></i>${both(REPORT_COPY.lgUnseen)}</span></div>`;
  const chart = `<div class="heatwrap"><div class="heat" role="img"${swap(lang, { "aria-label": aria })}>${heads}${'<span class="pad" aria-hidden="true"></span>'.repeat(pad)}${days}</div><div class="tip" aria-hidden="true"></div></div>${legend}`;
  const rows = cells.map((cell) => `<tr><td>${cell.date}</td><td class="n">${cell.state === "unseen" ? "\u2014" : groupDigits(cell.responses)}</td><td>${both(stateWord(cell.state))}</td></tr>`).join("");
  const table = `<table class="tv"><caption class="sr">${both(aria)}</caption><thead><tr><th scope="col">${both(REPORT_COPY.thDate)}</th><th scope="col">${both(REPORT_COPY.thReplies)}</th><th scope="col">${both(REPORT_COPY.thState)}</th></tr></thead><tbody>${rows}</tbody></table>`;
  return { chart, table };
}
function tools(view) {
  const list = view.usage.byTool;
  if (list.length === 0) return { chart: `<p class="empty">${both(REPORT_COPY.noTools)}</p>`, table: `<p class="empty">${both(REPORT_COPY.noTools)}</p>` };
  const width = (part, total) => Math.round(part / (total || 1) * 1e4) / 100;
  const row = (label, pick, format) => {
    const shown = list.filter((tool) => pick(tool) !== null);
    const value = (tool) => pick(tool) ?? 0;
    const total = shown.reduce((sum2, tool) => sum2 + value(tool), 0);
    if (shown.length === 0) return "";
    return perLang(
      (lang) => `<div class="t"><span>${esc(label[lang])}</span><b>${esc(format(total, lang))}</b><div class="splitbar" role="img" aria-label="${esc(shown.map((tool) => `${TOOL_NAMES[tool.tool][lang]} ${format(value(tool), lang)}`).join(", "))}">${shown.map((tool) => `<i style="width:${width(value(tool), total)}%;background:${TOOL_COLORS[tool.tool]}"></i>`).join("")}</div><div class="lg">${shown.map((tool) => `<small><i class="sw" style="background:${TOOL_COLORS[tool.tool]}"></i>${esc(TOOL_NAMES[tool.tool][lang])} ${esc(format(value(tool), lang))}</small>`).join("")}</div></div>`
    );
  };
  const chart = `<div class="tools">${row(REPORT_COPY.kMain, (tool) => tool.mainSessions, (count) => groupDigits(count))}${row(REPORT_COPY.kOut, (tool) => tool.outputTokens, shortTokens)}</div>`;
  const rows = list.map((tool) => `<tr><th scope="row">${both(TOOL_NAMES[tool.tool])}</th><td class="n">${groupDigits(tool.mainSessions)}</td><td class="n">${tool.outputTokens === null ? "\u2014" : groupDigits(tool.outputTokens)}</td></tr>`).join("");
  const table = `<table class="tv"><caption class="sr">${both(REPORT_COPY.toolsTable)}</caption><thead><tr><th scope="col">${both(REPORT_COPY.thTool)}</th><th scope="col">${both(REPORT_COPY.kMain)}</th><th scope="col">${both(REPORT_COPY.kOut)}</th></tr></thead><tbody>${rows}</tbody></table>`;
  return { chart, table };
}
function historyChart(view) {
  const points = view.history.flatMap((entry) => entry.aq === null ? [] : [{ at: entry.at, aq: Math.max(0, Math.min(100, entry.aq)) }]);
  if (points.length < 2) return "";
  const [width, height, pad] = [320, 80, 6];
  const x = (index) => (pad + index * (width - 2 * pad) / (points.length - 1)).toFixed(1);
  const y = (aq) => (height - pad - aq / 100 * (height - 2 * pad)).toFixed(1);
  const line = points.map((point, index) => `${x(index)},${y(point.aq)}`).join(" ");
  const dots = points.map((point, index) => `<circle cx="${x(index)}" cy="${y(point.aq)}" r="2.5"/>`).join("");
  const delta = points[points.length - 1].aq - points[points.length - 2].aq;
  const d = delta > 0 ? `+${delta}` : String(delta);
  return `<div class="hist"><p class="sub">${both(REPORT_COPY.hist)}</p><svg class="histsvg" viewBox="0 0 ${width} ${height}" aria-hidden="true"><polyline points="${line}"/>${dots}</svg><p class="histd">${both(copy("histDelta", { d }))}</p><p class="sr">${both(copy("histList", { list: points.map((point) => point.aq).join(", ") }))}</p></div>`;
}
function usage(view, lang) {
  const days = dayNumber(view.window.to) - dayNumber(view.window.from) + 1;
  const kpi = (value, label) => `<div class="kpi"><b>${value}</b><span>${both(label)}</span></div>`;
  const kpis = [
    kpi(groupDigits(view.usage.mainSessions), REPORT_COPY.kMain),
    kpi(`${view.usage.activeDays}/${days}`, REPORT_COPY.kDays),
    kpi(view.usage.outputTokens === null ? "\u2014" : both(textsOf2((l) => shortTokens(view.usage.outputTokens, l))), REPORT_COPY.kOut),
    kpi(view.usage.cacheHit === null ? "\u2014" : percent(view.usage.cacheHit), REPORT_COPY.kCache)
  ].join("");
  const cal = calendar(view, lang);
  const byTool = tools(view);
  const shell = view.usage.shellNonZero === null ? "" : `<p class="shell">${both(copy("shell", { v: percent(view.usage.shellNonZero) }))}</p>`;
  return `<section class="use" aria-labelledby="h-use"><div class="usehd"><h2 id="h-use"><span class="no">03</span>${both(REPORT_COPY.use)}</h2><button type="button" class="mini-btn" data-act="table"><span class="when-chart">${both(REPORT_COPY.asTable)}</span><span class="when-table">${both(REPORT_COPY.asChart)}</span></button></div><div class="kpis">${kpis}</div><div class="grid2"><div><p class="sub">${both(REPORT_COPY.cal)}</p><div class="chart">${cal.chart}</div><div class="table tvwrap">${cal.table}</div></div><div><p class="sub">${both(REPORT_COPY.byTool)}</p><div class="chart">${byTool.chart}</div><div class="table tvwrap">${byTool.table}</div></div></div>${shell}${historyChart(view)}</section>`;
}
function partialBand(view) {
  if (view.partialReads.length === 0) return "";
  const lines = view.partialReads.map((read) => {
    const key = read.share === null ? "partialReadUnknown" : read.lowerBound ? "partialReadAtLeast" : "partialRead";
    return `<p>${both(textsOf2((l) => fill(REPORT_COPY[key][l], { tool: TOOL_NAMES[read.tool][l], share: read.share === null ? null : percent(read.share) })))}</p>`;
  });
  return `<div class="partial" role="note">${ICONS.caution}<div>${lines.join("")}</div></div>`;
}
var SPOT_FIELDS = { env: REPORT_COPY.spotEnv, headers: REPORT_COPY.spotHeaders, field: REPORT_COPY.spotField, args: REPORT_COPY.spotArgs, url: REPORT_COPY.spotUrl };
var spotLabel = (place, lang) => `${place.server ?? REPORT_COPY.spotSettings[lang]}${place.projectName === null ? "" : ` (${place.projectName})`} \xB7 ${SPOT_FIELDS[place.field][lang]} ${place.key}${place.copy === "default" ? ` \xB7 ${REPORT_COPY.spotDefaultCopy[lang]}` : ""}`;
function notices(view) {
  if (view.notices.length === 0) return "";
  const spots = (notice) => {
    if (notice.kind !== "credentials_in_config") return "";
    const places = view.credentialPlaces.filter((place) => place.tool === notice.tool);
    return places.length === 0 ? "" : `<ul class="spots">${places.map((place) => `<li>${both(textsOf2((l) => spotLabel(place, l)))}</li>`).join("")}</ul>`;
  };
  return `<section class="notices" aria-labelledby="h-notice"><h2 id="h-notice">${both(REPORT_COPY.notices)}</h2><ul>${view.notices.map((notice) => `<li>${ICONS.info}<span>${both(notice.text)}</span>${spots(notice)}</li>`).join("")}</ul></section>`;
}
function footer(hasCard) {
  const share2 = hasCard ? `<button type="button" class="share" data-act="card" aria-haspopup="dialog">${both(REPORT_COPY.cardBtn)}</button>` : "<span></span>";
  return `<footer class="ft"><span class="lock">${LOCK}<span>${both(textsOf2((l) => `${REPORT_COPY.footCalc[l]} ${REPORT_COPY.footPromise[l]}`))}</span></span>${share2}<p class="names-note">${both(REPORT_COPY.footNames)}</p></footer>`;
}
function cardDialog(hasCard) {
  if (!hasCard) return "";
  return `<dialog class="card" id="${SCRIPT_IDS.dialog}" aria-labelledby="card-title"><h2 id="card-title">${both(REPORT_COPY.cardTitle)}</h2><img class="cardimg" id="${SCRIPT_IDS.cardImage}" alt="" width="1200" height="630" hidden><p class="empty" id="${SCRIPT_IDS.cardFail}" hidden>${both(REPORT_COPY.cardFail)}</p><div class="cardft"><span>${both(REPORT_COPY.cardNote)}</span><div class="btns"><a id="${SCRIPT_IDS.cardLink}" href="#" hidden>${both(REPORT_COPY.download)}</a><button type="button" id="${SCRIPT_IDS.cardClose}">${both(REPORT_COPY.close)}</button></div></div></dialog>`;
}
function clientData(view) {
  const aq = view.score.aq;
  const grade = view.score.grade;
  return {
    ui: { copied: REPORT_COPY.copied, copyFail: REPORT_COPY.copyFail, copyLabel: REPORT_COPY.copyLabel },
    card: aq === null || grade === null ? null : {
      aq,
      grade,
      today: view.today,
      file: `${REPO}-aq-${view.today}.png`,
      brand: textsOf2((l) => REPORT_COPY.brand[l].toUpperCase()),
      title: REPORT_COPY.title,
      aqLabel: REPORT_COPY.aqLabel,
      gradeLabel: REPORT_COPY.grade,
      nick: textsOf2((l) => view.text[l].grade ?? ""),
      repo: REPORT_COPY.cardRepo,
      alt: textsOf2((l) => fill(REPORT_COPY.cardAlt[l], { aq, grade, name: view.text[l].grade ?? "" })),
      axes: view.axes.map((axis) => ({ name: AXIS_NAMES[axis.axis], score: axis.score }))
    }
  };
}
function reportHtml(view, art) {
  const lang = view.lang;
  const hash = createHash("sha256").update(REPORT_SCRIPT, "utf8").digest("base64");
  const csp = `default-src 'none'; img-src data:; style-src 'unsafe-inline'; script-src 'sha256-${hash}'; base-uri 'none'; form-action 'none'`;
  const title = copy("pageTitle", { date: view.today });
  const client = clientData(view);
  const data = JSON.stringify(client).replace(/</g, "\\u003c");
  return `<!doctype html>
<html lang="${lang}" data-ui="${lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light">
<meta http-equiv="Content-Security-Policy" content="${csp}">
<title data-tr data-en-text="${esc(title.en)}" data-ko-text="${esc(title.ko)}">${esc(title[lang])}</title>
<style>${REPORT_CSS}</style>
</head>
<body>
<div class="sr" id="${SCRIPT_IDS.live}" role="status" aria-live="polite"></div>
<main><article class="sheet" aria-labelledby="h-title">${header(view, art, lang)}${partialBand(view)}${hero(view, art, lang)}${nextPath(view, lang)}${columns(view, art, lang)}${lists(view, lang)}${usage(view, lang)}${howScore()}${notices(view)}${footer(client.card !== null)}</article></main>
${cardDialog(client.card !== null)}
<div class="toast" id="${SCRIPT_IDS.toast}" aria-hidden="true"></div>
<script type="application/json" id="${SCRIPT_IDS.data}">${data}</script>
<script>${REPORT_SCRIPT}</script>
</body>
</html>
`;
}

// src/report/view.ts
function reportView(result, run2) {
  const targetsOf2 = (finding) => finding.candidates.map((id) => result.candidates.find((candidate) => candidate.id === id)?.target ?? id);
  const withheld = result.score.aq === null ? result.notices.find((notice) => notice.kind === "score_withheld")?.text ?? null : null;
  return {
    lang: result.lang,
    today: result.window.today,
    window: { from: result.window.score.from, to: result.window.score.to },
    tools: result.tools.filter((tool) => tool.detected).map((tool) => tool.tool),
    saved: run2.saved,
    round: run2.saved ? run2.round : null,
    history: run2.saved ? [...run2.history ?? []] : [],
    score: { aq: result.score.aq, grade: result.score.grade, tier: result.score.tier, withheld: [...result.score.withheld] },
    withheldText: withheld,
    // 건너뛴 압축 파일도 읽지 못한 기록이다(설계 「5단계 계획 전 결정」 2번, 「5단계 4부 계획 전 결정」 2번)
    unreadable: result.notices.some((notice) => notice.kind === "record_unreadable" || notice.kind === "record_skipped"),
    text: result.text,
    axes: result.axes,
    findings: result.findings.map((finding) => ({
      ruleId: finding.ruleId,
      axis: finding.axis,
      category: finding.category,
      severity: finding.severity,
      measured: finding.status === "scored",
      gain: finding.gain,
      value: finding.value,
      score: finding.score,
      tools: finding.tools.flatMap((value) => value.status === "scored" ? [{ tool: value.tool, value: value.value, score: value.score }] : []),
      targets: targetsOf2(finding),
      unmeasuredTools: finding.tools.filter((value) => value.status === "unmeasured" && value.candidates.length > 0).map((value) => value.tool),
      text: finding.text
    })),
    usage: result.usage,
    notices: result.notices.filter((notice) => !(notice.kind === "score_withheld" && result.score.aq === null)).map((notice) => ({ kind: notice.kind, tool: "tool" in notice ? notice.tool : null, text: notice.text })),
    credentialPlaces: result.details.credentialPlaces,
    failedServers: result.details.failedMcpServers.map((server) => ({ ...server })),
    servers: result.details.unjudgedServers.map((server) => ({
      tool: server.tool,
      name: server.name,
      scope: server.scope,
      projectName: server.projectName,
      why: server.why,
      daysUntil: server.judgeFrom === null ? null : daysBefore(server.judgeFrom, result.window.today)
    })),
    setupProblems: result.details.setupProblems,
    missingInstructions: result.details.missingInstructions.map((project) => project.name),
    worstOverlap: result.details.worstOverlap?.name ?? null,
    nextGrade: result.nextGrade?.text ?? null,
    ignored: [...result.ignored],
    nextPlan: result.nextGrade === null ? null : { grade: result.nextGrade.grade, need: result.nextGrade.need, reaches: result.nextGrade.reaches, steps: result.nextGrade.steps.map((step) => ({ ruleId: step.ruleId, aq: step.aq })) },
    partialReads: result.coverage.filter((coverage) => coverage.partial).map((coverage) => ({ tool: coverage.tool, share: coverage.unreadableShare, lowerBound: coverage.lowerBound }))
  };
}

// src/state/cache.ts
import { createHash as createHash3 } from "node:crypto";
import { lstat as lstat2, mkdir as mkdir3, open as open2, readdir as readdir3, readFile as readFile3, realpath as realpath2, rename as rename2, writeFile as writeFile2 } from "node:fs/promises";
import { join as join6 } from "node:path";

// src/adapters/claude/locate.ts
import { readdir, stat } from "node:fs/promises";
import { join as join4, resolve } from "node:path";
function claudeHome(env, homedir2) {
  const fromEnv = env.CLAUDE_CONFIG_DIR?.trim();
  return fromEnv ? resolve(fromEnv) : join4(homedir2, ".claude");
}
function normalizePath(path, platform = process.platform) {
  const absolute = resolve(path).replace(/\\/g, "/");
  return platform === "win32" ? absolute.toLowerCase() : absolute;
}
var isMissing = (error) => error?.code === "ENOENT";
async function listClaudeFiles(home, minMtimeMs) {
  const projects = join4(home, "projects");
  const files = [];
  const unreadableDirs = [];
  const unreadableFiles = [];
  let olderThanWindow = 0;
  let projectEntries;
  try {
    projectEntries = await readdir(projects, { withFileTypes: true });
  } catch (error) {
    if (isMissing(error)) return { projectsFound: false, files: [], olderThanWindow: 0, unreadableDirs: [], unreadableFiles: [] };
    return { projectsFound: true, files: [], olderThanWindow: 0, unreadableDirs: [projects], unreadableFiles: [] };
  }
  const consider = async (path, sessionId, kind, parentSessionId) => {
    try {
      const info = await stat(path);
      if (minMtimeMs !== null && info.mtimeMs < minMtimeMs) {
        olderThanWindow++;
        return;
      }
      files.push({ path, normPath: normalizePath(path), size: info.size, mtimeMs: info.mtimeMs, sessionId, kind, parentSessionId });
    } catch {
      unreadableFiles.push(path);
    }
  };
  for (const project of projectEntries) {
    if (!project.isDirectory()) continue;
    const projectDir = join4(projects, project.name);
    let entries;
    try {
      entries = await readdir(projectDir, { withFileTypes: true });
    } catch {
      unreadableDirs.push(projectDir);
      continue;
    }
    for (const entry of entries) {
      if (entry.isFile() && entry.name.endsWith(".jsonl")) {
        await consider(join4(projectDir, entry.name), entry.name.slice(0, -".jsonl".length), "main", null);
        continue;
      }
      if (!entry.isDirectory()) continue;
      const subDir = join4(projectDir, entry.name, "subagents");
      let subs;
      try {
        subs = await readdir(subDir, { withFileTypes: true });
      } catch (error) {
        if (!isMissing(error)) unreadableDirs.push(subDir);
        continue;
      }
      for (const sub of subs) {
        if (sub.isFile() && sub.name.endsWith(".jsonl")) {
          await consider(join4(subDir, sub.name), sub.name.slice(0, -".jsonl".length), "sub", entry.name);
        }
      }
    }
  }
  files.sort((a, b) => a.normPath < b.normPath ? -1 : a.normPath > b.normPath ? 1 : 0);
  unreadableDirs.sort();
  unreadableFiles.sort();
  return { projectsFound: true, files, olderThanWindow, unreadableDirs, unreadableFiles };
}

// src/adapters/codex/fingerprints.ts
import { createHash as createHash2 } from "node:crypto";
var KINDS = ["itemIds", "callIds", "totals", "responseIds"];
var PRINT = /^[0-9a-f]{16}$/;
var DIGEST = /^[0-9a-f]{64}$/;
var isObject = (value) => value !== null && typeof value === "object" && !Array.isArray(value);
function toLists(prints) {
  return { itemIds: [...prints.itemIds].sort(), callIds: [...prints.callIds].sort(), totals: [...prints.totals].sort(), responseIds: [...prints.responseIds].sort() };
}
function fromLists(value) {
  if (!isObject(value)) return null;
  const out = {};
  for (const kind of KINDS) {
    const list = value[kind];
    if (!Array.isArray(list) || !list.every((print) => typeof print === "string" && PRINT.test(print))) return null;
    out[kind] = new Set(list);
  }
  return { itemIds: out.itemIds, callIds: out.callIds, totals: out.totals, responseIds: out.responseIds };
}
function unionOf(list) {
  const merge = (kind) => new Set(list.flatMap((prints) => [...prints[kind]]));
  return { itemIds: merge("itemIds"), callIds: merge("callIds"), totals: merge("totals"), responseIds: merge("responseIds") };
}
function sharedDigest(own, inherited) {
  const hash = createHash2("sha256");
  for (const kind of KINDS) {
    const shared = inherited === null ? [] : [...own[kind]].filter((print) => inherited[kind].has(print)).sort();
    hash.update(`${kind}:${shared.join(",")};`);
  }
  return hash.digest("hex");
}
function reviveCodexExtra(value) {
  if (!isObject(value) || typeof value.sharedDigest !== "string" || !DIGEST.test(value.sharedDigest)) return null;
  const prints = fromLists(value.fingerprints);
  return prints === null ? null : { fingerprints: toLists(prints), sharedDigest: value.sharedDigest };
}

// src/adapters/common/canonical.ts
function nameRecord() {
  return /* @__PURE__ */ Object.create(null);
}
function sortedRecord(record) {
  const out = nameRecord();
  for (const key of Object.keys(record).sort()) out[key] = record[key];
  return out;
}

// src/adapters/types.ts
function emptyToolCounts() {
  return { calls: 0, results: 0, errors: 0, deniedByUser: 0, deniedByPermission: 0, deniedByHook: 0, interrupted: 0, unknownDenial: 0 };
}
function emptySkillSignalCounts() {
  return { tool: 0, attribution: 0, slash: 0, injected: 0 };
}
function emptyHookCounts() {
  return { runs: 0, failures: 0, unclassifiedBlocks: 0 };
}
function emptyDay() {
  return {
    humanRequests: 0,
    weakHumanRequests: 0,
    nonHumanInputs: nameRecord(),
    permissionModes: nameRecord(),
    responses: 0,
    tokens: { input: 0, cacheRead: 0, cacheWrite: 0, output: 0, thinking: 0 },
    models: nameRecord(),
    efforts: nameRecord(),
    unknownEffort: 0,
    tools: nameRecord(),
    unknownDenialKinds: nameRecord(),
    autoCompactions: 0,
    unknownCompactions: 0,
    lengthStops: 0,
    interruptedTurns: 0,
    subagentCalls: 0,
    mcpConnectionFailure: false,
    mcpFailedServers: nameRecord(),
    skillSignals: nameRecord(),
    mcpCalls: nameRecord(),
    mcpAttributions: nameRecord(),
    hooks: nameRecord(),
    loadedSkills: [],
    loadedMcpServers: [],
    reloadedSkills: [],
    reloadedMcpServers: []
  };
}
function canonicalDay(day) {
  return {
    ...day,
    nonHumanInputs: sortedRecord(day.nonHumanInputs),
    permissionModes: sortedRecord(day.permissionModes),
    models: sortedRecord(day.models),
    efforts: sortedRecord(day.efforts),
    tools: sortedRecord(day.tools),
    unknownDenialKinds: sortedRecord(day.unknownDenialKinds),
    mcpFailedServers: sortedRecord(day.mcpFailedServers),
    skillSignals: sortedRecord(day.skillSignals),
    mcpCalls: sortedRecord(day.mcpCalls),
    mcpAttributions: sortedRecord(day.mcpAttributions),
    hooks: sortedRecord(day.hooks)
  };
}
var DAY_SHAPE = {
  humanRequests: "number",
  weakHumanRequests: "number",
  nonHumanInputs: "numbers",
  permissionModes: "numbers",
  responses: "number",
  tokens: "tokens",
  models: "numbers",
  efforts: "numbers",
  unknownEffort: "number",
  tools: "tools",
  unknownDenialKinds: "numbers",
  autoCompactions: "number",
  unknownCompactions: "number",
  lengthStops: "number",
  interruptedTurns: "number",
  subagentCalls: "number",
  mcpConnectionFailure: "boolean",
  mcpFailedServers: "numbers",
  skillSignals: "skills",
  mcpCalls: "numbers",
  mcpAttributions: "numbers",
  hooks: "hooks",
  loadedSkills: "names",
  loadedMcpServers: "names",
  reloadedSkills: "names",
  reloadedMcpServers: "names"
};
var DATE_KEY = /^\d{4}-\d{2}-\d{2}$/;
function addDayInto(into, from) {
  const target = into;
  const source = from;
  const addNumbers2 = (a, b) => {
    for (const [key, value] of Object.entries(b)) a[key] = (Object.hasOwn(a, key) ? a[key] : 0) + value;
  };
  for (const key of Object.keys(DAY_SHAPE)) {
    const a = target[key];
    const b = source[key];
    switch (DAY_SHAPE[key]) {
      case "number":
        target[key] = a + b;
        break;
      case "boolean":
        target[key] = a || b;
        break;
      case "names":
        target[key] = [.../* @__PURE__ */ new Set([...a, ...b])].sort();
        break;
      case "numbers":
      case "tokens":
        addNumbers2(a, b);
        break;
      case "tools":
      case "skills":
      case "hooks": {
        const outer = a;
        for (const [name, counts] of Object.entries(b)) {
          if (Object.hasOwn(outer, name)) addNumbers2(outer[name], counts);
          else outer[name] = { ...counts };
        }
        break;
      }
    }
  }
}
var isObject2 = (v) => v !== null && typeof v === "object" && !Array.isArray(v);
var isNumber = (v) => typeof v === "number" && Number.isSafeInteger(v) && v >= 0;
var isNullableString = (v) => v === null || typeof v === "string";
function fixed(v, fields) {
  if (!isObject2(v)) return null;
  const out = {};
  for (const field of fields) {
    const x = v[field];
    if (!isNumber(x)) return null;
    out[field] = x;
  }
  return out;
}
function named(v, each) {
  if (!isObject2(v)) return null;
  const out = nameRecord();
  for (const key of Object.keys(v).sort()) {
    const x = each(v[key]);
    if (x === null) return null;
    out[key] = x;
  }
  return out;
}
function names(v) {
  return Array.isArray(v) && v.every((x) => typeof x === "string") ? [...v] : null;
}
function reviveValue(v, shape) {
  switch (shape) {
    case "number":
      return isNumber(v) ? v : null;
    case "boolean":
      return typeof v === "boolean" ? v : null;
    case "names":
      return names(v);
    case "numbers":
      return named(v, (x) => isNumber(x) ? x : null);
    case "tokens":
      return fixed(v, Object.keys(emptyDay().tokens));
    case "tools":
      return named(v, (x) => fixed(x, Object.keys(emptyToolCounts())));
    case "skills":
      return named(v, (x) => fixed(x, Object.keys(emptySkillSignalCounts())));
    case "hooks":
      return named(v, (x) => fixed(x, Object.keys(emptyHookCounts())));
  }
}
function reviveDay(v) {
  if (!isObject2(v)) return null;
  const out = {};
  for (const key of Object.keys(emptyDay())) {
    const value = reviveValue(v[key], DAY_SHAPE[key]);
    if (value === null) return null;
    out[key] = value;
  }
  return out;
}
var TOOL_IDS = /* @__PURE__ */ new Set(["claude-code", "codex", "gemini", "web-chatgpt", "web-claude"]);
var ID_FALLBACKS = /* @__PURE__ */ new Set(["first-line-unreadable", "first-line-not-meta", "meta-without-id", "no-lines"]);
function reviveCodex(v) {
  if (!isObject2(v) || typeof v.recordId !== "string" || !isNullableString(v.unknownThreadSource) || typeof v.baselineMissing !== "boolean") return null;
  if (v.idFallback !== null && !ID_FALLBACKS.has(v.idFallback)) return null;
  const unknownItemTypes = named(v.unknownItemTypes, (x) => isNumber(x) ? x : null);
  const skipped = fixed(v.inheritedSkipped, ["items", "totals", "responses"]);
  if (unknownItemTypes === null || skipped === null) return null;
  return {
    recordId: v.recordId,
    unknownThreadSource: v.unknownThreadSource,
    idFallback: v.idFallback,
    unknownItemTypes,
    inheritedSkipped: { items: skipped.items, totals: skipped.totals, responses: skipped.responses },
    baselineMissing: v.baselineMissing
  };
}
function reviveSummary(value) {
  if (!isObject2(value)) return null;
  const v = value;
  if (!TOOL_IDS.has(v.tool) || typeof v.sessionId !== "string" || v.kind !== "main" && v.kind !== "sub") return null;
  if (!isNullableString(v.parentSessionId) || !isNullableString(v.cwd) || !isNullableString(v.version)) return null;
  if (!isNullableString(v.firstDate) || v.firstDate !== null && !DATE_KEY.test(v.firstDate)) return null;
  if (!isObject2(v.days)) return null;
  const days = {};
  for (const date of Object.keys(v.days).sort()) {
    const day = DATE_KEY.test(date) ? reviveDay(v.days[date]) : null;
    if (day === null) return null;
    days[date] = day;
  }
  const instructionChars = v.instructionChars === null ? null : fixed(v.instructionChars, ["ascii", "other"]);
  if (v.instructionChars !== null && instructionChars === null) return null;
  const missing = fixed(v.missing, ["lines", "brokenLines", "tailFragments", "tooLongLines"]);
  const unconfirmedTypes = isObject2(v.missing) ? named(v.missing.unconfirmedTypes, (x) => isNumber(x) ? x : null) : null;
  const notes = fixed(v.notes, ["syntheticResponses", "responsesWithoutId", "undatedLines"]);
  const unknownHookKinds = isObject2(v.notes) ? named(v.notes.unknownHookKinds, (x) => isNumber(x) ? x : null) : null;
  const hashes = names(v.firstResponseIdHashes);
  const initialSkills = v.initialSkills === null ? null : names(v.initialSkills);
  const initialMcpServers = v.initialMcpServers === null ? null : names(v.initialMcpServers);
  if (missing === null || unconfirmedTypes === null || notes === null || unknownHookKinds === null || hashes === null) return null;
  if (v.initialSkills !== null && initialSkills === null || v.initialMcpServers !== null && initialMcpServers === null) return null;
  const codex = v.tool === "codex" ? reviveCodex(v.codex) : void 0;
  if (codex === null || v.tool !== "codex" && v.codex !== void 0) return null;
  return {
    tool: v.tool,
    sessionId: v.sessionId,
    kind: v.kind,
    parentSessionId: v.parentSessionId,
    cwd: v.cwd,
    version: v.version,
    firstDate: v.firstDate,
    days,
    instructionChars: instructionChars === null ? null : { ascii: instructionChars.ascii, other: instructionChars.other },
    initialSkills,
    initialMcpServers,
    missing: {
      lines: missing.lines,
      brokenLines: missing.brokenLines,
      tailFragments: missing.tailFragments,
      tooLongLines: missing.tooLongLines,
      ...isObject2(v.missing) && isNumber(v.missing.tooLongSkillLines) ? { tooLongSkillLines: v.missing.tooLongSkillLines } : {},
      ...isObject2(v.missing) && isNumber(v.missing.tooLongMcpLines) ? { tooLongMcpLines: v.missing.tooLongMcpLines } : {},
      unconfirmedTypes
    },
    firstResponseIdHashes: hashes,
    notes: {
      syntheticResponses: notes.syntheticResponses,
      responsesWithoutId: notes.responsesWithoutId,
      undatedLines: notes.undatedLines,
      unknownHookKinds
    },
    ...codex === void 0 ? {} : { codex }
  };
}

// src/state/folder.ts
import { lstat, readdir as readdir2, realpath, rmdir, unlink } from "node:fs/promises";
import { basename as basename2, dirname as dirname2, join as join5, relative } from "node:path";
var STATE_DIR_NAME = ".chunsik-garage";
function stateDir(homedir2) {
  return join5(homedir2, STATE_DIR_NAME);
}
var STATE_ENTRIES = [
  { name: "cache", kind: "dir", removedBy: "clean" },
  { name: "reports", kind: "dir", removedBy: "clean" },
  { name: "history.jsonl", kind: "file", removedBy: "all" },
  { name: "state.json", kind: "file", removedBy: "all" },
  { name: "notified", kind: "dir", removedBy: "all" },
  { name: "tune", kind: "dir", removedBy: "all" },
  // AQ 배지 그림(0.2.0). 가장 최근 것 하나만 둔다
  { name: "badge.svg", kind: "file", removedBy: "all" },
  // 가져온 웹 채팅 내보내기 파일의 자리(0.5.0). 내보내기 파일 자체는 복사하지 않는다
  { name: "web-exports.json", kind: "file", removedBy: "all" }
];
var isMissing2 = (error) => error?.code === "ENOENT";
async function treeSize(path) {
  const total = { files: 0, bytes: 0, links: 0 };
  const walk = async (current) => {
    let info;
    try {
      info = await lstat(current);
    } catch (error) {
      if (isMissing2(error)) return;
      throw error;
    }
    if (info.isSymbolicLink()) {
      total.links++;
      return;
    }
    if (info.isDirectory()) {
      for (const name of (await readdir2(current)).sort()) await walk(join5(current, name));
      return;
    }
    total.files++;
    total.bytes += info.size;
  };
  await walk(path);
  return total;
}
async function removeLink(path) {
  try {
    await unlink(path);
  } catch (error) {
    const code = error.code;
    if (code === "EPERM" || code === "EISDIR") {
      await rmdir(path);
      return;
    }
    throw error;
  }
}
async function expectedRealDir(dir) {
  return normalizePath(join5(await realpath(dirname2(dir)), basename2(dir)));
}
var outside = (path) => Object.assign(new Error(`outside of the state folder: ${path}`), { code: "EOUTSIDE" });
async function assertInside(path, boundary, allowEqual) {
  const real = normalizePath(await realpath(path));
  if (real === boundary ? allowEqual : real.startsWith(`${boundary}/`)) return;
  throw outside(path);
}
async function removeFiles(paths, root, boundary) {
  const report = { removed: 0, linked: 0 };
  for (const path of paths) {
    let info;
    try {
      info = await lstat(path);
    } catch (error) {
      if (isMissing2(error)) continue;
      throw error;
    }
    if (!info.isFile()) continue;
    const parent = dirname2(path);
    await assertInside(parent, boundary, true);
    if (normalizePath(await realpath(parent)) !== normalizePath(join5(boundary, relative(root, parent)))) {
      report.linked++;
      continue;
    }
    await unlink(path);
    report.removed++;
  }
  return report;
}
async function removeTree(path, boundary) {
  const removed = { files: 0, bytes: 0, links: 0 };
  const walk = async (current) => {
    let info;
    try {
      info = await lstat(current);
    } catch (error) {
      if (isMissing2(error)) return;
      throw error;
    }
    if (info.isSymbolicLink()) {
      await assertInside(dirname2(current), boundary, true);
      await removeLink(current);
      removed.links++;
      return;
    }
    if (info.isDirectory()) {
      await assertInside(current, boundary, false);
      for (const name of await readdir2(current)) await walk(join5(current, name));
      await assertInside(current, boundary, false);
      await rmdir(current);
      return;
    }
    await assertInside(dirname2(current), boundary, true);
    await unlink(current);
    removed.files++;
    removed.bytes += info.size;
  };
  await walk(path);
  return removed;
}

// src/state/cache.ts
var CACHE_FORMAT_VERSION = 1;
var EDGE_BYTES = 4096;
var sha256 = (data) => createHash3("sha256").update(data).digest("hex");
async function cacheKeyFor(file, parser, timeZone) {
  const handle = await open2(file.path, "r");
  try {
    const length = Math.min(EDGE_BYTES, file.size);
    const head = Buffer.alloc(length);
    const tail = Buffer.alloc(length);
    const fill2 = async (buffer, position) => {
      for (let offset = 0; offset < buffer.length; ) {
        const { bytesRead } = await handle.read(buffer, offset, buffer.length - offset, position + offset);
        if (bytesRead === 0) return false;
        offset += bytesRead;
      }
      return true;
    };
    if (!await fill2(head, 0) || !await fill2(tail, file.size - length)) return null;
    const after = await handle.stat();
    if (after.size !== file.size || after.mtimeMs !== file.mtimeMs) return null;
    return {
      normPath: file.normPath,
      size: file.size,
      mtimeMs: file.mtimeMs,
      head: sha256(head),
      tail: sha256(tail),
      cacheFormat: CACHE_FORMAT_VERSION,
      parser,
      timeZone
    };
  } finally {
    await handle.close();
  }
}
function sameKey(a, b) {
  return a.normPath === b.normPath && a.size === b.size && a.mtimeMs === b.mtimeMs && a.head === b.head && a.tail === b.tail && a.cacheFormat === b.cacheFormat && a.parser === b.parser && a.timeZone === b.timeZone;
}
async function keyStillMatches(path, key) {
  const now = await cacheKeyFor({ path, normPath: key.normPath, size: key.size, mtimeMs: key.mtimeMs }, key.parser, key.timeZone);
  return now !== null && sameKey(now, key);
}
function entryPath(dir, normPath) {
  return join6(dir, `${sha256(normPath).slice(0, 32)}.json`);
}
async function loadCached(dir, key) {
  try {
    const entry = JSON.parse(await readFile3(entryPath(dir, key.normPath), "utf8"));
    if (entry.key === void 0 || typeof entry.bytesRead !== "number" || !Number.isSafeInteger(entry.bytesRead) || entry.bytesRead < 0 || entry.bytesRead > key.size || !sameKey(entry.key, key)) return null;
    const summary = reviveSummary(entry.summary);
    if (summary === null) return null;
    if (summary.tool !== "codex") return entry.codex === void 0 ? { key: entry.key, summary, bytesRead: entry.bytesRead } : null;
    const codex = reviveCodexExtra(entry.codex);
    return codex === null ? null : { key: entry.key, summary, bytesRead: entry.bytesRead, codex };
  } catch {
    return null;
  }
}
async function storeCached(dir, entry) {
  await mkdir3(dir, { recursive: true });
  const target = entryPath(dir, entry.key.normPath);
  const temporary = `${target}.${process.pid}.tmp`;
  await writeFile2(temporary, JSON.stringify(entry));
  await rename2(temporary, target);
}
var ENTRY_NAME = /^[0-9a-f]{32}\.json$/;
async function readCacheEntry(path) {
  let text;
  try {
    text = await readFile3(path, "utf8");
  } catch {
    return { status: "unreadable" };
  }
  let normPath;
  try {
    normPath = JSON.parse(text)?.key?.normPath;
  } catch {
    return { status: "broken" };
  }
  return typeof normPath === "string" && normPath !== "" ? { status: "ok", normPath } : { status: "broken" };
}
async function isStaleCacheEntry(path) {
  const entry = await readCacheEntry(path);
  if (entry.status === "unreadable") return false;
  if (entry.status === "broken") return true;
  try {
    await lstat2(entry.normPath);
    return false;
  } catch (error) {
    return error.code === "ENOENT";
  }
}
async function staleCacheEntries(stateDir2) {
  let dirInfo;
  try {
    dirInfo = await lstat2(stateDir2);
  } catch (error) {
    if (error.code === "ENOENT") return { skipped: null, boundary: null, paths: [] };
    throw error;
  }
  const boundary = await expectedRealDir(stateDir2);
  if (dirInfo.isSymbolicLink() || normalizePath(await realpath2(stateDir2)) !== boundary) return { skipped: "state", boundary: null, paths: [] };
  const cacheDir = join6(stateDir2, "cache");
  let info;
  try {
    info = await lstat2(cacheDir);
  } catch (error) {
    if (error.code === "ENOENT") return { skipped: null, boundary, paths: [] };
    throw error;
  }
  if (info.isSymbolicLink()) return { skipped: "cache", boundary: null, paths: [] };
  if (!info.isDirectory()) return { skipped: null, boundary, paths: [] };
  const paths = [];
  for (const tool of (await readdir3(cacheDir)).sort()) {
    const toolDir = join6(cacheDir, tool);
    if (!(await lstat2(toolDir)).isDirectory()) continue;
    for (const name of (await readdir3(toolDir)).sort()) {
      if (!ENTRY_NAME.test(name)) continue;
      const path = join6(toolDir, name);
      if (!(await lstat2(path)).isFile()) continue;
      if (await isStaleCacheEntry(path)) paths.push(path);
    }
  }
  return { skipped: null, boundary, paths };
}
async function pruneCache(stateDir2) {
  const stale = await staleCacheEntries(stateDir2);
  if (stale.boundary === null || stale.paths.length === 0) return { removed: 0, skipped: stale.skipped };
  const result = await removeFiles(stale.paths, stateDir2, stale.boundary);
  return { removed: result.removed, skipped: result.linked > 0 ? "cache" : null };
}

// src/scan/identity.ts
import { join as join7 } from "node:path";

// src/state/observations.ts
function installKey(parts) {
  return JSON.stringify(parts);
}
function updateInstalls(previous, currentKeys, today, keepUnseen = () => false) {
  const before = new Map((previous ?? []).map((record) => [record.key, record]));
  const firstCheckup = previous === null;
  const current = new Set(currentKeys);
  const records = [...current].map((key) => before.get(key) ?? { key, firstSeen: today, appeared: !firstCheckup });
  for (const record of previous ?? []) {
    if (!current.has(record.key) && keepUnseen(record.key)) records.push(record);
  }
  return records.sort((a, b) => a.key < b.key ? -1 : a.key > b.key ? 1 : 0);
}

// src/scan/identity.ts
var skillKey = (skill, tool) => installKey(["skill", tool, skill.scope, skill.projectRoot ?? "", skill.name, skill.realPath ?? normalizePath(skill.path)]);
var mcpKey = (server, tool) => server.definitionHash === null ? null : installKey(["mcp", tool, server.scope, server.projectRoot ?? "", server.pluginId ?? "", server.name, server.definitionHash]);
function skillInstallKey(skill) {
  return skillKey(skill, "claude-code");
}
function mcpInstallKey(server) {
  return mcpKey(server, "claude-code");
}
function codexSkillInstallKey(skill) {
  return skillKey(skill, "codex");
}
function codexMcpInstallKey(server) {
  return mcpKey(server, "codex");
}
function installKeysOf(facts) {
  const keys = facts.skills.map(skillInstallKey);
  for (const server of facts.mcpServers) {
    const key = mcpInstallKey(server);
    if (key !== null) keys.push(key);
  }
  return [...new Set(keys)].sort();
}
var unread3 = (status) => status === "unparsable" || status === "unreadable";
var inside = (path, base) => path === base || path.startsWith(base.endsWith("/") ? base : `${base}/`);
function unseenInUnreadablePlace(facts) {
  const unreadableDirs = facts.unreadableDirs.map((dir) => normalizePath(dir));
  const linkedRoots = facts.plugins.flatMap((plugin) => {
    const shown = normalizePath(plugin.installPath);
    return plugin.installRealPath === null || plugin.installRealPath === shown ? [] : [{ shown, real: plugin.installRealPath }];
  });
  const unreadablePluginDirs = unreadableDirs.flatMap((dir) => [dir, ...linkedRoots.filter((root) => inside(dir, root.shown)).map((root) => `${root.real}${dir.slice(root.shown.length)}`)]);
  const userSkillsDir = normalizePath(join7(facts.home, "skills"));
  const scanned2 = new Map(facts.projects.filter((project) => project.exists && !project.excluded).map((project) => [project.normRoot, project]));
  const claudeJsonUnread = unread3(facts.claudeJson);
  const pluginsFileUnread = unread3(facts.pluginsFile);
  const unknownPluginRoots = facts.plugins.filter((plugin) => plugin.exists && !plugin.compositionKnown).map((plugin) => plugin.installRealPath ?? normalizePath(plugin.installPath));
  const mcpUnreadPlugins = new Set(facts.plugins.filter((plugin) => plugin.exists && plugin.mcpUnreadable).map((plugin) => plugin.id));
  return (key) => {
    let parsed;
    try {
      parsed = JSON.parse(key);
    } catch {
      return false;
    }
    if (!Array.isArray(parsed) || !parsed.every((part) => typeof part === "string") || parsed[1] !== "claude-code") return false;
    const scope = parsed[2] ?? "";
    const projectRoot = parsed[3] ?? "";
    if (parsed[0] === "skill" && parsed.length === 6) {
      const realPath = parsed[5] ?? "";
      if (scope === "user") return unreadableDirs.includes(userSkillsDir);
      if (scope === "project") {
        const project = scanned2.get(projectRoot);
        return project !== void 0 && unreadableDirs.includes(normalizePath(join7(project.root, ".claude", "skills")));
      }
      if (scope === "plugin") return pluginsFileUnread || unknownPluginRoots.some((root) => inside(realPath, root)) || unreadablePluginDirs.some((dir) => inside(realPath, dir));
      return false;
    }
    if (parsed[0] === "mcp" && parsed.length === 7) {
      if (scope === "user") return claudeJsonUnread;
      if (scope === "local") return scanned2.has(projectRoot) && claudeJsonUnread;
      if (scope === "project") return unread3(scanned2.get(projectRoot)?.mcpJsonStatus);
      if (scope === "plugin") return pluginsFileUnread || mcpUnreadPlugins.has(parsed[4] ?? "");
      return false;
    }
    return false;
  };
}
function codexInstallKeysOf(facts) {
  const keys = facts.skills.map((skill) => skill.installKey);
  for (const server of facts.mcpServers) if (server.installKey !== null) keys.push(server.installKey);
  return [...new Set(keys)].sort();
}
function codexUnseenInUnreadablePlace(facts) {
  const configUnread = unread3(facts.config);
  const scanned2 = new Map(facts.projects.filter((project) => project.scanned).map((project) => [project.normRoot, project]));
  const unknownPlugins = new Set(facts.plugins.filter((plugin) => !plugin.compositionKnown || plugin.mcpUnreadable).map((plugin) => plugin.id));
  const pluginSkillsUnseen = configUnread || facts.plugins.some((plugin) => plugin.configured && !plugin.compositionKnown) || facts.unreadableSkillPlaces.plugins.length > 0;
  return (key) => {
    let parsed;
    try {
      parsed = JSON.parse(key);
    } catch {
      return false;
    }
    if (!Array.isArray(parsed) || !parsed.every((part) => typeof part === "string") || parsed[1] !== "codex") return false;
    const scope = parsed[2] ?? "";
    const projectRoot = parsed[3] ?? "";
    if (parsed[0] === "skill" && parsed.length === 6) {
      if (scope === "user") return facts.unreadableSkillPlaces.user;
      if (scope === "project") return scanned2.has(projectRoot) && facts.unreadableSkillPlaces.projects.includes(projectRoot);
      if (scope === "plugin") return pluginSkillsUnseen;
      return false;
    }
    if (parsed[0] === "mcp" && parsed.length === 7) {
      if (scope === "project" && !scanned2.has(projectRoot)) return false;
      if (configUnread) return scope === "user" || scope === "project" || scope === "plugin";
      if (scope === "project") return unread3(scanned2.get(projectRoot)?.configStatus);
      if (scope === "plugin") return unknownPlugins.has(parsed[4] ?? "");
      return false;
    }
    return false;
  };
}

// src/state/state.ts
import { randomBytes } from "node:crypto";
import { mkdir as mkdir4, readFile as readFile4, rename as rename3, rm as rm2, writeFile as writeFile3 } from "node:fs/promises";
import { join as join8 } from "node:path";
var STATE_SCHEMA = 1;
var STATE_FILE = "state.json";
var DATE = /^\d{4}-\d{2}-\d{2}$/;
var SALT = /^[0-9a-f]{64}$/;
function newState() {
  return { schema: STATE_SCHEMA, salt: randomBytes(32).toString("hex"), lastCheckupAt: null, installs: null, notify: null };
}
function reviveRecord(value) {
  if (value === null || typeof value !== "object" || Array.isArray(value)) return null;
  const v = value;
  if (typeof v.key !== "string" || typeof v.firstSeen !== "string" || !DATE.test(v.firstSeen) || typeof v.appeared !== "boolean") return null;
  return { key: v.key, firstSeen: v.firstSeen, appeared: v.appeared };
}
function reviveNotify(value) {
  if (value === void 0 || value === null) return null;
  if (typeof value !== "object" || Array.isArray(value)) return void 0;
  const v = value;
  if (typeof v.on !== "boolean" || v.lang !== "en" && v.lang !== "ko") return void 0;
  if (v.names !== null && (!Array.isArray(v.names) || !v.names.every((name) => typeof name === "string"))) return void 0;
  return { on: v.on, lang: v.lang, names: v.names === null ? null : [...v.names].sort() };
}
var RULE_ORDER = new Map(RULES.map((spec, index) => [spec.id, index]));
function reviveIgnoredRules(value) {
  if (!Array.isArray(value)) return [];
  const known2 = value.filter((id) => typeof id === "string" && RULE_ORDER.has(id));
  return [...new Set(known2)].sort((a, b) => RULE_ORDER.get(a) - RULE_ORDER.get(b));
}
function reviveState(value) {
  if (value === null || typeof value !== "object" || Array.isArray(value)) return null;
  const v = value;
  if (v.schema !== STATE_SCHEMA || typeof v.salt !== "string" || !SALT.test(v.salt)) return null;
  if (v.lastCheckupAt !== null && (typeof v.lastCheckupAt !== "string" || !Number.isFinite(Date.parse(v.lastCheckupAt)))) return null;
  let installs = null;
  if (v.installs !== null) {
    if (!Array.isArray(v.installs)) return null;
    installs = [];
    for (const item2 of v.installs) {
      const record = reviveRecord(item2);
      if (record === null) return null;
      installs.push(record);
    }
    installs.sort((a, b) => a.key < b.key ? -1 : a.key > b.key ? 1 : 0);
  }
  const notify = reviveNotify(v.notify);
  if (notify === void 0) return null;
  const ignoredRules = reviveIgnoredRules(v.ignoredRules);
  return { schema: STATE_SCHEMA, salt: v.salt, lastCheckupAt: v.lastCheckupAt, installs, notify, ...ignoredRules.length > 0 ? { ignoredRules } : {} };
}
async function loadState(dir) {
  let text;
  try {
    text = await readFile4(join8(dir, STATE_FILE), "utf8");
  } catch (error) {
    const code = error.code;
    if (code === "ENOENT" || code === "ENOTDIR") return { status: "missing" };
    return { status: "broken" };
  }
  try {
    const state = reviveState(JSON.parse(text));
    return state === null ? { status: "broken" } : { status: "ok", state };
  } catch {
    return { status: "broken" };
  }
}
async function saveState(dir, state) {
  await mkdir4(dir, { recursive: true });
  const target = join8(dir, STATE_FILE);
  const temporary = `${target}.${process.pid}.tmp`;
  try {
    await writeFile3(temporary, `${JSON.stringify(state, null, 2)}
`);
    await rename3(temporary, target);
  } catch (error) {
    await rm2(temporary, { force: true }).catch(() => void 0);
    throw error;
  }
}

// src/state/next-state.ts
async function openState(stateDir2) {
  const loaded = await loadState(stateDir2);
  if (loaded.status === "ok") return { state: loaded.state, fresh: false, broken: false };
  return { state: newState(), fresh: loaded.status === "missing", broken: loaded.status === "broken" };
}
function toolOfKey(key) {
  try {
    const parts = JSON.parse(key);
    return Array.isArray(parts) && typeof parts[1] === "string" ? parts[1] : null;
  } catch {
    return null;
  }
}
function nextState(state, facts, today, startedAt) {
  const claudeUnseen = unseenInUnreadablePlace(facts.claude);
  const codexUnseen = codexUnseenInUnreadablePlace(facts.codex);
  const keys = [...installKeysOf(facts.claude), ...codexInstallKeysOf(facts.codex)];
  const keepUnseen = (key) => toolOfKey(key) === "codex" ? codexUnseen(key) : claudeUnseen(key);
  return { ...state, lastCheckupAt: startedAt, installs: updateInstalls(state.installs, keys, today, keepUnseen) };
}

// src/state/reports.ts
import { lstat as lstat3, mkdir as mkdir5, readdir as readdir4, realpath as realpath3, rename as rename4, rm as rm3, writeFile as writeFile4 } from "node:fs/promises";
import { join as join9 } from "node:path";
var REPORTS_DIR = "reports";
var KEEP_REPORTS = 20;
var TEMP_PREFIX = "chunsik-garage-result-";
var TEMP_REPORT_PREFIX = "chunsik-garage-report-";
var STAMPED = /^(\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}-\d{3}Z)\.(json|html)$/;
function resultStamp(nowMs) {
  return new Date(nowMs).toISOString().replace(/[:.]/g, "-");
}
async function writeText(path, text) {
  const temporary = `${path}.${process.pid}.tmp`;
  try {
    await writeFile4(temporary, text);
    await rename4(temporary, path);
  } catch (error) {
    await rm3(temporary, { force: true }).catch(() => void 0);
    throw error;
  }
}
async function writeJson(path, value) {
  await writeText(path, `${JSON.stringify(value, null, 2)}
`);
}
async function writeResult(stateDir2, stamp, result) {
  const reports = join9(stateDir2, REPORTS_DIR);
  await mkdir5(reports, { recursive: true });
  const path = join9(reports, `${stamp}.json`);
  await writeJson(path, result);
  return path;
}
async function writeTempResult(tmpdir3, stamp, result) {
  const path = join9(tmpdir3, `${TEMP_PREFIX}${stamp}.json`);
  await writeJson(path, result);
  return path;
}
async function writeReport(stateDir2, stamp, html) {
  const reports = join9(stateDir2, REPORTS_DIR);
  await mkdir5(reports, { recursive: true });
  const path = join9(reports, `${stamp}.html`);
  await writeText(path, html);
  return path;
}
async function writeTempReport(tmpdir3, stamp, html) {
  const path = join9(tmpdir3, `${TEMP_REPORT_PREFIX}${stamp}.html`);
  await writeText(path, html);
  return path;
}
async function staleReports(stateDir2, keep = KEEP_REPORTS, keepStamp = null) {
  let dirInfo;
  try {
    dirInfo = await lstat3(stateDir2);
  } catch (error) {
    if (error.code === "ENOENT") return { skipped: null, boundary: null, paths: [] };
    throw error;
  }
  const boundary = await expectedRealDir(stateDir2);
  if (dirInfo.isSymbolicLink() || normalizePath(await realpath3(stateDir2)) !== boundary) return { skipped: "state", boundary: null, paths: [] };
  const reports = join9(stateDir2, REPORTS_DIR);
  let info;
  try {
    info = await lstat3(reports);
  } catch (error) {
    if (error.code === "ENOENT") return { skipped: null, boundary, paths: [] };
    throw error;
  }
  if (info.isSymbolicLink()) return { skipped: "reports", boundary: null, paths: [] };
  if (!info.isDirectory()) return { skipped: null, boundary, paths: [] };
  const files = [];
  for (const name of await readdir4(reports)) {
    const match = STAMPED.exec(name);
    if (match === null) continue;
    if ((await lstat3(join9(reports, name))).isFile()) files.push({ name, stamp: match[1] });
  }
  const stamps = new Set(files.map((file) => file.stamp));
  const others = [...stamps].filter((stamp) => stamp !== keepStamp).sort().reverse();
  const kept = new Set(keepStamp !== null && stamps.has(keepStamp) ? [keepStamp, ...others.slice(0, Math.max(keep - 1, 0))] : others.slice(0, keep));
  const paths = files.filter((file) => !kept.has(file.stamp)).map((file) => join9(reports, file.name)).sort();
  return { skipped: null, boundary, paths };
}
async function pruneReports(stateDir2, keep = KEEP_REPORTS, keepStamp = null) {
  const stale = await staleReports(stateDir2, keep, keepStamp);
  if (stale.boundary === null || stale.paths.length === 0) return { removed: 0, skipped: stale.skipped };
  const result = await removeFiles(stale.paths, stateDir2, stale.boundary);
  return { removed: result.removed, skipped: result.linked > 0 ? "reports" : null };
}

// src/state/web-exports.ts
import { mkdir as mkdir6, readFile as readFile5, rename as rename5, rm as rm4, writeFile as writeFile5 } from "node:fs/promises";
import { join as join10 } from "node:path";

// src/adapters/web/observation.ts
var WEB_TOOLS = ["web-chatgpt", "web-claude"];
var WEB_COVERAGE = {
  responsesAndTokens: "unsupported",
  humanRequests: "measured",
  toolCalls: "unsupported",
  toolErrors: "unsupported",
  shellExitCodes: "unsupported",
  deniedAndLengthStops: "unsupported",
  interruptedTurns: "unsupported",
  autoCompaction: "unsupported",
  effort: "unsupported",
  loadedNames: "unsupported",
  skillUsage: "unsupported",
  mcpCalls: "unsupported",
  mcpFailuresAndHooks: "unsupported",
  instructionSize: "unsupported",
  subagents: "unsupported"
};
var WEB_OBSERVATION = { complete: false, reasons: ["not-recorded"] };

// src/state/web-exports.ts
var WEB_EXPORTS_FILE = "web-exports.json";
var WEB_EXPORTS_SCHEMA = 1;
var isTool = (value) => WEB_TOOLS.includes(value);
async function readWebExports(stateDir2) {
  let text;
  try {
    text = await readFile5(join10(stateDir2, WEB_EXPORTS_FILE), "utf8");
  } catch (error) {
    if (error.code === "ENOENT") return { status: "missing", entries: [] };
    return { status: "broken", entries: [] };
  }
  try {
    const value = JSON.parse(text);
    if (value === null || typeof value !== "object" || value.schema !== WEB_EXPORTS_SCHEMA || !Array.isArray(value.exports)) return { status: "broken", entries: [] };
    const entries = [];
    for (const item2 of value.exports) {
      const entry = item2;
      if (entry === null || typeof entry !== "object" || !isTool(entry.tool) || typeof entry.path !== "string" || entry.path === "" || typeof entry.addedAt !== "string") return { status: "broken", entries: [] };
      if (entries.some((other) => other.tool === entry.tool)) return { status: "broken", entries: [] };
      entries.push({ tool: entry.tool, path: entry.path, addedAt: entry.addedAt });
    }
    entries.sort((a, b) => a.tool < b.tool ? -1 : 1);
    return { status: "ok", entries };
  } catch {
    return { status: "broken", entries: [] };
  }
}
async function writeWebExports(stateDir2, entries) {
  const path = join10(stateDir2, WEB_EXPORTS_FILE);
  if (entries.length === 0) {
    await rm4(path, { force: true });
    return;
  }
  await mkdir6(stateDir2, { recursive: true });
  const sorted = [...entries].sort((a, b) => a.tool < b.tool ? -1 : 1);
  const temporary = `${path}.${process.pid}.tmp`;
  await writeFile5(temporary, `${JSON.stringify({ schema: WEB_EXPORTS_SCHEMA, exports: sorted }, null, 2)}
`);
  await rename5(temporary, path);
}
function withExport(entries, entry) {
  return [...entries.filter((other) => other.tool !== entry.tool), entry];
}

// src/hook/notify.ts
import { mkdirSync, readdirSync, readFileSync, unlinkSync, writeFileSync } from "node:fs";
import { join as join11 } from "node:path";
var isMissing3 = (error) => {
  const code = error?.code;
  return code === "ENOENT" || code === "ENOTDIR";
};
function readObject(path) {
  try {
    const value = JSON.parse(readFileSync(path, "utf8").replace(/^﻿/, ""));
    return typeof value === "object" && value !== null && !Array.isArray(value) ? value : void 0;
  } catch (error) {
    return isMissing3(error) ? null : void 0;
  }
}
var keysOf = (value) => typeof value === "object" && value !== null && !Array.isArray(value) ? Object.keys(value) : [];
function notifyNames(env, homedir2) {
  const configDir = env.CLAUDE_CONFIG_DIR || join11(homedir2, ".claude");
  const names2 = /* @__PURE__ */ new Set();
  let complete = true;
  try {
    for (const entry of readdirSync(join11(configDir, "skills"), { withFileTypes: true })) if (entry.isDirectory() || entry.isSymbolicLink()) names2.add(`skill:${entry.name}`);
  } catch (error) {
    if (!isMissing3(error)) complete = false;
  }
  const settings = readObject(join11(configDir, "settings.json"));
  if (settings === void 0) complete = false;
  for (const id of keysOf(settings?.enabledPlugins)) names2.add(`plugin:${id}`);
  const global = readObject(env.CLAUDE_CONFIG_DIR ? join11(env.CLAUDE_CONFIG_DIR, ".claude.json") : join11(homedir2, ".claude.json"));
  if (global === void 0) complete = false;
  for (const name of keysOf(global?.mcpServers)) names2.add(`mcp:${name}`);
  return { names: [...names2].sort(), complete };
}
function nextNames(previous, current) {
  return current.complete || previous === null ? current.names : [.../* @__PURE__ */ new Set([...previous, ...current.names])].sort();
}

// src/version.ts
var PROGRAM_VERSION = "0.5.0";

// src/adapters/claude/observation.ts
var CLAUDE_COVERAGE = {
  responsesAndTokens: "measured",
  humanRequests: "measured",
  toolCalls: "measured",
  toolErrors: "measured",
  shellExitCodes: "measured",
  deniedAndLengthStops: "measured",
  interruptedTurns: "measured",
  autoCompaction: "measured",
  effort: "measured",
  loadedNames: "measured",
  skillUsage: "measured",
  mcpCalls: "measured",
  mcpFailuresAndHooks: "measured",
  instructionSize: "measured",
  subagents: "measured"
};
var SKILL_NON_SIGNAL_TYPES = /* @__PURE__ */ new Set([
  "system",
  "api-request",
  "api-request-blob",
  "mode",
  "permission-mode",
  "ai-title",
  "session-owner",
  "pr-link",
  "last-prompt",
  "cost-state"
]);
var MCP_NON_SIGNAL_TYPES = /* @__PURE__ */ new Set([...SKILL_NON_SIGNAL_TYPES, "user", "attachment"]);
var REASON_ORDER = ["unreadable-files", "too-long-lines", "unconfirmed-pieces"];
function mostlyBroken(summary) {
  return summary.missing.brokenLines * 2 > summary.missing.lines;
}
function observeRecords(summaries, unreadableCount2, harmless, longLines = (summary) => summary.missing.tooLongLines) {
  const found = /* @__PURE__ */ new Set();
  if (unreadableCount2 > 0) found.add("unreadable-files");
  for (const summary of summaries) {
    if (longLines(summary) > 0) found.add("too-long-lines");
    for (const [type, count] of Object.entries(summary.missing.unconfirmedTypes)) {
      if (count > 0 && !harmless.has(type)) found.add("unconfirmed-pieces");
    }
  }
  const reasons = REASON_ORDER.filter((reason) => found.has(reason));
  return { complete: reasons.length === 0, reasons };
}
function claudeObservation(summaries, unreadableCount2, metric) {
  const longLines = (summary) => (metric === "skill" ? summary.missing.tooLongSkillLines : summary.missing.tooLongMcpLines) ?? summary.missing.tooLongLines;
  return observeRecords(summaries, unreadableCount2, metric === "skill" ? SKILL_NON_SIGNAL_TYPES : MCP_NON_SIGNAL_TYPES, longLines);
}
var marker = (name, text) => ({ name, bytes: Buffer.from(text, "utf8") });
var CLAUDE_USAGE_MARKERS = [
  marker("skill", '"Skill"'),
  marker("skill", "<command-name>"),
  marker("skill", '"attributionSkill"'),
  marker("skill", '"invoked_skills"'),
  marker("mcp", '"mcp__'),
  marker("mcp", '"attributionMcpServer"')
];

// src/adapters/common/hash.ts
var OFFSET = 0xcbf29ce484222325n;
var PRIME = 0x100000001b3n;
var MASK = 0xffffffffffffffffn;
var encoder = new TextEncoder();
function fnv1a64(text) {
  let hash = OFFSET;
  for (const byte of encoder.encode(text)) {
    hash ^= BigInt(byte);
    hash = hash * PRIME & MASK;
  }
  return hash.toString(16).padStart(16, "0");
}

// src/adapters/common/outer-type.ts
var SIMPLE_ESCAPES = { '"': '"', "\\": "\\", "/": "/", b: "\b", f: "\f", n: "\n", r: "\r", t: "	" };
var LITERAL = /^(?:-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?|true|false|null)/;
function outerTypeOf(text) {
  const n = text.length;
  let i = 0;
  const skipWhitespace = () => {
    while (i < n) {
      const code = text.charCodeAt(i);
      if (code === 32 || code === 9 || code === 10 || code === 13) i++;
      else break;
    }
  };
  const readString = (keep) => {
    i++;
    let out = "";
    while (i < n) {
      const ch = text[i];
      if (ch === '"') {
        i++;
        return out;
      }
      if (ch === "\\") {
        if (i + 1 >= n) return null;
        const escape = text[i + 1];
        if (escape === "u") {
          const hex = text.slice(i + 2, i + 6);
          if (!/^[0-9a-fA-F]{4}$/.test(hex)) return null;
          if (keep) out += String.fromCharCode(Number.parseInt(hex, 16));
          i += 6;
          continue;
        }
        const simple = SIMPLE_ESCAPES[escape];
        if (simple === void 0) return null;
        if (keep) out += simple;
        i += 2;
        continue;
      }
      if (keep) out += ch;
      i++;
    }
    return null;
  };
  const skipValue = () => {
    skipWhitespace();
    if (i >= n) return false;
    const ch = text[i];
    if (ch === '"') return readString(false) !== null;
    if (ch === "{" || ch === "[") {
      let depth = 0;
      while (i < n) {
        const c = text[i];
        if (c === '"') {
          if (readString(false) === null) return false;
          continue;
        }
        if (c === "{" || c === "[") depth++;
        else if (c === "}" || c === "]") {
          depth--;
          if (depth === 0) {
            i++;
            return true;
          }
        }
        i++;
      }
      return false;
    }
    const literal = LITERAL.exec(text.slice(i, i + 400));
    if (literal === null) return false;
    i += literal[0].length;
    skipWhitespace();
    return i < n;
  };
  skipWhitespace();
  if (text[i] !== "{") return null;
  i++;
  for (; ; ) {
    skipWhitespace();
    if (i >= n || text[i] !== '"') return null;
    const key = readString(true);
    if (key === null) return null;
    skipWhitespace();
    if (text[i] !== ":") return null;
    i++;
    skipWhitespace();
    if (key === "type") return text[i] === '"' ? readString(true) : null;
    if (!skipValue()) return null;
    skipWhitespace();
    if (text[i] === ",") {
      i++;
      continue;
    }
    return null;
  }
}

// src/adapters/claude/classify.ts
var INTERRUPT_PREFIX = "[Request interrupted by user";
var COMMAND = /^(?:<command-message>[\s\S]*?<\/command-message>\s*)?<command-name>\/?([^<]*)<\/command-name>/;
var TAG = /^<([A-Za-z][\w-]*)>/;
var isObject3 = (value) => value !== null && typeof value === "object" && !Array.isArray(value);
function userText(content) {
  if (typeof content === "string") return content;
  if (Array.isArray(content)) {
    for (const block of content) {
      if (isObject3(block) && block.type === "text") return typeof block.text === "string" ? block.text : "";
    }
  }
  return "";
}
function hasToolResult(content) {
  return Array.isArray(content) && content.some((block) => isObject3(block) && block.type === "tool_result");
}
var toolInserted = (line) => line.isMeta === true || line.isCompactSummary === true || line.isVisibleInTranscriptOnly === true;
function commandNameOf(text) {
  const command = COMMAND.exec(text.trimStart());
  return command === null ? null : command[1].trim();
}
function classifyOwnUser(line) {
  const message = isObject3(line.message) ? line.message : {};
  if (hasToolResult(message.content)) return { kind: "tool-result" };
  if (toolInserted(line)) return { kind: "skip", reason: "meta" };
  if (isObject3(line.origin)) {
    const kind = line.origin.kind;
    if (kind === "human") return { kind: "human", weak: false };
    return { kind: "skip", reason: `origin:${typeof kind === "string" ? kind : "?"}` };
  }
  if (line.turnOrigin === "sdk" || line.turnOrigin === "scheduled") return { kind: "skip", reason: `turn:${line.turnOrigin}` };
  const text = userText(message.content).trimStart();
  const command = commandNameOf(text);
  if (command !== null) return { kind: "command", name: command };
  const tag = TAG.exec(text);
  if (tag !== null) return { kind: "skip", reason: `tag:${tag[1]}` };
  if (text.startsWith(INTERRUPT_PREFIX)) return { kind: "skip", reason: "interrupt" };
  return { kind: "human", weak: true };
}
function classifyUser(line, isSubSession) {
  if (isSubSession || line.isSidechain === true) return { kind: "skip", reason: "subagent-input" };
  return classifyOwnUser(line);
}
function isInterruptMarker(line) {
  const verdict = classifyOwnUser(line);
  return verdict.kind === "skip" && verdict.reason === "interrupt";
}
function slashCommandOf(line) {
  const message = isObject3(line.message) ? line.message : {};
  if (hasToolResult(message.content) || toolInserted(line)) return null;
  return commandNameOf(userText(message.content));
}
function denialOf(line) {
  const kind = line.toolDenialKind;
  const decision = isObject3(line.permissionDecision) ? line.permissionDecision : null;
  const rejected = decision !== null && decision.decision === "reject";
  if (kind === "user-rejected") return { kind: "user", raw: null };
  if (rejected && decision.source === "hook") return { kind: "hook", raw: null };
  if (kind === "interrupted") return { kind: "interrupted", raw: null };
  if (kind === "permission-rule" || rejected) return { kind: "permission", raw: null };
  if (typeof kind === "string" && kind !== "") return { kind: "unknown", raw: kind };
  return null;
}

// src/adapters/claude/responses.ts
var DATE2 = 0;
var MODEL = 1;
var EFFORT = 2;
var SKILL = 3;
var SERVER = 4;
var NAME_WIDTH = 5;
var USAGE_WIDTH = 5;
var NONE = -1;
var SYNTHETIC = 1;
var HAS_USAGE = 2;
var LENGTH_STOP = 4;
var FIRST_CAPACITY = 1024;
var ResponseTable = class {
  rows = /* @__PURE__ */ new Map();
  names = [];
  nameIds = /* @__PURE__ */ new Map();
  capacity = FIRST_CAPACITY;
  nameCells = new Int32Array(NAME_WIDTH * FIRST_CAPACITY);
  flagCells = new Uint8Array(FIRST_CAPACITY);
  usageCells = new Float64Array(USAGE_WIDTH * FIRST_CAPACITY);
  get size() {
    return this.rows.size;
  }
  /** 응답 ID의 줄 번호. 처음 보는 ID면 줄을 더하고 isNew를 참으로 돌려준다. */
  row(id, date, synthetic) {
    const known2 = this.rows.get(id);
    if (known2 !== void 0) return { row: known2, isNew: false };
    const row = this.rows.size;
    if (row === this.capacity) this.grow();
    const base = row * NAME_WIDTH;
    this.nameCells[base + DATE2] = this.nameId(date);
    this.nameCells.fill(NONE, base + MODEL, base + NAME_WIDTH);
    this.flagCells[row] = synthetic ? SYNTHETIC : 0;
    this.usageCells.fill(0, row * USAGE_WIDTH, (row + 1) * USAGE_WIDTH);
    this.rows.set(id, row);
    return { row, isNew: true };
  }
  grow() {
    const capacity = Math.ceil(this.capacity * 1.5);
    const names2 = new Int32Array(NAME_WIDTH * capacity);
    names2.set(this.nameCells);
    this.nameCells = names2;
    const flags = new Uint8Array(capacity);
    flags.set(this.flagCells);
    this.flagCells = flags;
    const usage2 = new Float64Array(USAGE_WIDTH * capacity);
    usage2.set(this.usageCells);
    this.usageCells = usage2;
    this.capacity = capacity;
  }
  isSynthetic(row) {
    return (this.flagCells[row] & SYNTHETIC) !== 0;
  }
  /** 아직 값이 없을 때만 채운다(모델·강도는 처음 값을 쓴다). */
  fillFirst(row, column, value) {
    const at = row * NAME_WIDTH + (column === "model" ? MODEL : EFFORT);
    if (value !== null && this.nameCells[at] === NONE) this.nameCells[at] = this.nameId(value);
  }
  /** 마지막 값으로 바꾼다(귀속). */
  setLast(row, column, value) {
    if (value !== null) this.nameCells[row * NAME_WIDTH + (column === "skill" ? SKILL : SERVER)] = this.nameId(value);
  }
  setUsage(row, usage2) {
    const base = row * USAGE_WIDTH;
    this.usageCells[base] = usage2.input;
    this.usageCells[base + 1] = usage2.cacheRead;
    this.usageCells[base + 2] = usage2.cacheWrite;
    this.usageCells[base + 3] = usage2.output;
    this.usageCells[base + 4] = usage2.thinking;
    this.flagCells[row] = this.flagCells[row] | HAS_USAGE;
  }
  /** 마지막으로 적힌 끊긴 까닭이 길이 제한인지 적는다. */
  setStop(row, stop) {
    const flags = this.flagCells[row];
    this.flagCells[row] = stop === "max_tokens" ? flags | LENGTH_STOP : flags & ~LENGTH_STOP;
  }
  /** 들어온 차례로 응답을 하나씩 돌려준다. */
  *fold() {
    for (let row = 0; row < this.rows.size; row++) {
      const names2 = row * NAME_WIDTH;
      const usage2 = row * USAGE_WIDTH;
      const flags = this.flagCells[row];
      yield {
        date: this.name(this.nameCells[names2 + DATE2]),
        synthetic: (flags & SYNTHETIC) !== 0,
        model: this.name(this.nameCells[names2 + MODEL]),
        effort: this.name(this.nameCells[names2 + EFFORT]),
        lengthStop: (flags & LENGTH_STOP) !== 0,
        usage: (flags & HAS_USAGE) === 0 ? null : {
          input: this.usageCells[usage2],
          cacheRead: this.usageCells[usage2 + 1],
          cacheWrite: this.usageCells[usage2 + 2],
          output: this.usageCells[usage2 + 3],
          thinking: this.usageCells[usage2 + 4]
        },
        skill: this.name(this.nameCells[names2 + SKILL]),
        mcpServer: this.name(this.nameCells[names2 + SERVER])
      };
    }
  }
  nameId(value) {
    if (value === null) return NONE;
    let id = this.nameIds.get(value);
    if (id === void 0) {
      id = this.names.length;
      this.names.push(value);
      this.nameIds.set(value, id);
    }
    return id;
  }
  name(id) {
    return id === NONE ? null : this.names[id];
  }
};

// src/adapters/claude/parser.ts
var CLAUDE_PARSER_VERSION = 3;
var COUNTED_TYPES = /* @__PURE__ */ new Set(["assistant", "user", "attachment", "system"]);
var FIRST_RESPONSE_IDS = 20;
var SHELL_TOOLS = /* @__PURE__ */ new Set(["Bash", "PowerShell"]);
var SUBAGENT_TOOLS = /* @__PURE__ */ new Set(["Agent", "Task"]);
var UNKNOWN_TOOL = "?";
function toolKey(name) {
  if (!name.startsWith("mcp__")) return name;
  const parts = name.split("__");
  return `mcp__${parts[1] !== void 0 && parts[1] !== "" ? parts[1] : UNKNOWN_TOOL}`;
}
var KNOWN_HOOK_ATTACHMENTS = /* @__PURE__ */ new Set([
  "hook_success",
  "hook_non_blocking_error",
  "hook_blocking_error",
  "hook_additional_context"
]);
var strings = (value) => Array.isArray(value) ? value.filter((v) => typeof v === "string") : [];
var HOOK_FAILURE_MARKERS = ["blocking because onFailure is", "blocking because Git Bash wasn't found"];
function hasFailureMarker(blockingError) {
  const text = typeof blockingError === "string" ? blockingError : str(obj(blockingError)?.blockingError) ?? "";
  return HOOK_FAILURE_MARKERS.some((marker2) => text.includes(marker2));
}
var num = (value) => typeof value === "number" && Number.isFinite(value) ? value : 0;
var str = (value) => typeof value === "string" && value !== "" ? value : null;
var obj = (value) => value !== null && typeof value === "object" && !Array.isArray(value) ? value : null;
var bump = (record, key, by = 1) => {
  record[key] = (Object.hasOwn(record, key) ? record[key] : 0) + by;
};
function parseObject(text) {
  try {
    return obj(JSON.parse(text));
  } catch {
    return null;
  }
}
var ClaudeSessionParser = class {
  constructor(ctx) {
    this.ctx = ctx;
  }
  ctx;
  days = /* @__PURE__ */ new Map();
  responses = new ResponseTable();
  firstIds = [];
  lastDate = null;
  firstDate = null;
  version = null;
  cwd = null;
  lines = 0;
  brokenLines = 0;
  tailFragments = 0;
  tooLongLines = 0;
  tooLongSkillLines = 0;
  tooLongMcpLines = 0;
  unconfirmedTypes = nameRecord();
  responsesWithoutId = 0;
  undatedLines = 0;
  unknownHookKinds = nameRecord();
  toolNames = /* @__PURE__ */ new Map();
  pendingCommand = null;
  slashCommands = [];
  lastUserWasUserRejection = false;
  loadedSkills = /* @__PURE__ */ new Set();
  everLoadedSkills = /* @__PURE__ */ new Set();
  droppedSkills = /* @__PURE__ */ new Set();
  loadedMcp = /* @__PURE__ */ new Set();
  droppedMcp = /* @__PURE__ */ new Set();
  dayLoaded = /* @__PURE__ */ new Map();
  loadedMarkDate = null;
  loadedDirty = false;
  instructionChars = null;
  initialSkills = null;
  initialMcp = null;
  /** 줄바꿈으로 끝난 줄 하나를 받는다. 빈 줄(공백만 있는 줄)은 세지 않는다. 모든 줄을 JSON으로 풀어 보고, 숫자는 세는 종류의 줄에서만 센다. */
  line(text) {
    if (text.trim() === "") return;
    this.lines++;
    const parsed = parseObject(text);
    if (parsed === null) this.missing(text, "broken");
    else this.accept(parsed);
  }
  /** 상한을 넘은 줄 하나를 받는다. found는 줄의 바이트에서 찾은 사용 흔적의 표지다(0.3.0) */
  tooLong(found) {
    this.lines++;
    this.tooLongLines++;
    if (found?.has("skill")) this.tooLongSkillLines++;
    if (found?.has("mcp")) this.tooLongMcpLines++;
  }
  /** 끝 조각을 정리하고 요약을 낸다. 한 번만 부른다. */
  finish(tail, inProgress) {
    if (tail !== null && tail.trim() !== "") {
      this.lines++;
      const parsed = parseObject(tail);
      if (parsed !== null) this.accept(parsed);
      else this.missing(tail, inProgress ? "tail" : "broken");
    }
    const syntheticResponses = this.foldResponses();
    for (const command of this.slashCommands) {
      if (this.everLoadedSkills.has(command.name)) this.skillSignal(this.day(command.date), command.name).slash++;
    }
    for (const [date, loaded] of this.dayLoaded) {
      const day = this.day(date);
      day.loadedSkills = [...loaded.skills].sort();
      day.loadedMcpServers = [...loaded.mcp].sort();
      day.reloadedSkills = [...loaded.reloadedSkills].sort();
      day.reloadedMcpServers = [...loaded.reloadedMcp].sort();
    }
    const days = {};
    for (const date of [...this.days.keys()].sort()) days[date] = canonicalDay(this.days.get(date));
    return {
      tool: "claude-code",
      sessionId: this.ctx.sessionId,
      kind: this.ctx.kind,
      parentSessionId: this.ctx.parentSessionId,
      cwd: this.cwd,
      version: this.version,
      firstDate: this.firstDate,
      days,
      instructionChars: this.instructionChars,
      initialSkills: this.initialSkills,
      initialMcpServers: this.initialMcp,
      missing: {
        lines: this.lines,
        brokenLines: this.brokenLines,
        tailFragments: this.tailFragments,
        tooLongLines: this.tooLongLines,
        tooLongSkillLines: this.tooLongSkillLines,
        tooLongMcpLines: this.tooLongMcpLines,
        unconfirmedTypes: sortedRecord(this.unconfirmedTypes)
      },
      firstResponseIdHashes: this.firstIds.map(fnv1a64),
      notes: {
        syntheticResponses,
        responsesWithoutId: this.responsesWithoutId,
        undatedLines: this.undatedLines,
        unknownHookKinds: sortedRecord(this.unknownHookKinds)
      }
    };
  }
  /** 응답마다 마지막 사용량을 날짜 칸에 더한다. 합성 응답의 수를 돌려준다. */
  foldResponses() {
    let synthetic = 0;
    for (const response of this.responses.fold()) {
      if (response.synthetic) {
        synthetic++;
        continue;
      }
      if (response.date === null) continue;
      const day = this.day(response.date);
      day.responses++;
      if (response.usage !== null) {
        day.tokens.input += response.usage.input;
        day.tokens.cacheRead += response.usage.cacheRead;
        day.tokens.cacheWrite += response.usage.cacheWrite;
        day.tokens.output += response.usage.output;
        day.tokens.thinking += response.usage.thinking;
      }
      if (response.model !== null) bump(day.models, response.model);
      if (response.effort !== null) bump(day.efforts, response.effort);
      else day.unknownEffort++;
      if (response.lengthStop) day.lengthStops++;
      if (response.skill !== null) this.skillSignal(day, response.skill).attribution++;
      if (response.mcpServer !== null) bump(day.mcpAttributions, response.mcpServer);
    }
    return synthetic;
  }
  missing(text, kind) {
    if (kind === "broken") this.brokenLines++;
    else this.tailFragments++;
    bump(this.unconfirmedTypes, outerTypeOf(text) ?? "?");
  }
  /** 풀린 줄 하나. 종류와 상관없이 그 줄의 시각을 앞 줄의 날짜와 가장 이른 날짜에 쓰고, 세는 종류면 해석한다. */
  accept(line) {
    const own = localDateOfIso(line.timestamp, this.ctx.timeZone);
    if (own !== null) {
      this.lastDate = own;
      if (this.firstDate === null || own < this.firstDate) this.firstDate = own;
    }
    if (typeof line.type === "string" && COUNTED_TYPES.has(line.type)) this.handle(line, this.dateOf(own));
  }
  /** 세는 줄의 날짜. 시각이 없으면 앞 줄(종류와 상관없이)의 날짜를 쓰고, 앞 줄도 없으면 날짜 없는 줄로 센다. */
  dateOf(own) {
    if (own !== null) return own;
    if (this.lastDate === null) this.undatedLines++;
    return this.lastDate;
  }
  day(date) {
    let day = this.days.get(date);
    if (day === void 0) {
      day = emptyDay();
      this.days.set(date, day);
    }
    return day;
  }
  skillSignal(day, name) {
    let counts = day.skillSignals[name];
    if (counts === void 0) {
      counts = emptySkillSignalCounts();
      day.skillSignals[name] = counts;
    }
    return counts;
  }
  handle(line, date) {
    if (this.cwd === null) this.cwd = str(line.cwd);
    if (line.type === "assistant") {
      if (this.initialMcp === null) this.initialMcp = [...this.loadedMcp].sort();
      this.onAssistant(line, date);
    } else if (line.type === "user") this.onUser(line, date);
    else if (line.type === "attachment") this.onAttachment(line, date);
    else if (line.type === "system") this.onSystem(line, date);
    this.markLoaded(date);
  }
  onAssistant(line, date) {
    this.lastUserWasUserRejection = false;
    const version = str(line.version);
    if (version !== null) this.version = maxVersion([this.version, version]);
    const message = obj(line.message) ?? {};
    const id = str(message.id);
    if (id === null) {
      this.responsesWithoutId++;
    } else {
      const { row, isNew } = this.responses.row(id, date, message.model === "<synthetic>");
      if (isNew && !this.responses.isSynthetic(row)) {
        if (this.firstIds.length < FIRST_RESPONSE_IDS) this.firstIds.push(id);
        this.resolvePending(true);
      }
      this.responses.fillFirst(row, "model", str(message.model));
      this.responses.fillFirst(row, "effort", str(line.effort));
      const usage2 = obj(message.usage);
      if (usage2 !== null) {
        this.responses.setUsage(row, {
          input: num(usage2.input_tokens),
          cacheRead: num(usage2.cache_read_input_tokens),
          cacheWrite: num(usage2.cache_creation_input_tokens),
          output: num(usage2.output_tokens),
          thinking: num(obj(usage2.output_tokens_details)?.thinking_tokens)
        });
      }
      const stop = str(message.stop_reason);
      if (stop !== null) this.responses.setStop(row, stop);
      this.responses.setLast(row, "skill", str(line.attributionSkill));
      this.responses.setLast(row, "mcpServer", str(line.attributionMcpServer));
    }
    if (date === null || !Array.isArray(message.content)) return;
    for (const raw of message.content) {
      const block = obj(raw);
      if (block === null || block.type !== "tool_use") continue;
      const blockId = str(block.id);
      if (blockId === null || this.toolNames.has(blockId)) continue;
      const name = str(block.name) ?? UNKNOWN_TOOL;
      const key = toolKey(name);
      this.toolNames.set(blockId, key);
      const day = this.day(date);
      this.tool(day, key).calls++;
      if (key.startsWith("mcp__")) bump(day.mcpCalls, key.slice("mcp__".length));
      if (SUBAGENT_TOOLS.has(name)) day.subagentCalls++;
      if (name === "Skill") {
        const skill = str(obj(block.input)?.skill);
        if (skill !== null) this.skillSignal(day, skill).tool++;
      }
    }
  }
  /**
   * user 줄. 사람 요청은 판별표로 가르고(하위 세션은 세지 않는다), 도구 결과·거절·끊은 표지·슬래시 명령은
   * 판별표와 따로 본다. 하위 세션의 도구 결과, 끊은 표지, 슬래시 명령도 센다(설계 9.2, 9.5).
   */
  onUser(line, date) {
    const verdict = classifyUser(line, this.ctx.kind === "sub");
    const denial = denialOf(line);
    const afterUserRejection = this.lastUserWasUserRejection;
    this.lastUserWasUserRejection = denial !== null && denial.kind === "user";
    if (date === null) return;
    const day = this.day(date);
    this.toolResults(line, day, denial);
    if (isInterruptMarker(line) && !afterUserRejection) day.interruptedTurns++;
    const slash = slashCommandOf(line);
    if (slash !== null) this.slashCommands.push({ name: slash, date });
    switch (verdict.kind) {
      case "human":
        this.resolvePending(false);
        day.humanRequests++;
        if (verdict.weak) day.weakHumanRequests++;
        this.countMode(day, line);
        break;
      case "command":
        this.resolvePending(false);
        this.pendingCommand = { date, mode: str(line.permissionMode) };
        break;
      case "skip":
        bump(day.nonHumanInputs, verdict.reason);
        break;
      case "tool-result":
        break;
    }
  }
  /** 도구 결과를 센다. 거절 표시가 붙은 줄은 한 건으로, 첫 결과의 도구에 종류별로 적는다. 결과도 거절 표시도 없으면 아무것도 세지 않는다. */
  toolResults(line, day, denial) {
    const message = obj(line.message) ?? {};
    const results = [];
    if (Array.isArray(message.content)) {
      for (const raw of message.content) {
        const block = obj(raw);
        if (block !== null && block.type === "tool_result") results.push(block);
      }
    }
    if (denial !== null) {
      const first = results[0];
      const counts = this.tool(day, first === void 0 ? UNKNOWN_TOOL : this.toolNameOf(first));
      if (denial.kind === "user") counts.deniedByUser++;
      else if (denial.kind === "hook") counts.deniedByHook++;
      else if (denial.kind === "permission") counts.deniedByPermission++;
      else if (denial.kind === "interrupted") counts.interrupted++;
      else {
        counts.unknownDenial++;
        bump(day.unknownDenialKinds, denial.raw ?? UNKNOWN_TOOL);
      }
      return;
    }
    for (const block of results) {
      const counts = this.tool(day, this.toolNameOf(block));
      counts.results++;
      if (block.is_error === true) counts.errors++;
    }
  }
  toolNameOf(block) {
    const id = str(block.tool_use_id);
    return (id === null ? void 0 : this.toolNames.get(id)) ?? UNKNOWN_TOOL;
  }
  tool(day, name) {
    let counts = day.tools[name];
    if (counts === void 0) {
      counts = emptyToolCounts();
      day.tools[name] = counts;
    }
    return counts;
  }
  countMode(day, line) {
    const mode = str(line.permissionMode);
    if (mode !== null) bump(day.permissionModes, mode);
  }
  /** 기다리는 명령을 정리한다. 응답이 뒤따랐으면 명령의 날짜에 사람 요청으로 센다. */
  resolvePending(responded) {
    if (this.pendingCommand === null) return;
    if (responded) {
      const day = this.day(this.pendingCommand.date);
      day.humanRequests++;
      if (this.pendingCommand.mode !== null) bump(day.permissionModes, this.pendingCommand.mode);
    }
    this.pendingCommand = null;
  }
  onAttachment(line, date) {
    const body = obj(line.attachment);
    const type = body === null ? null : str(body.type);
    if (body === null || type === null) return;
    if (type === "skill_listing") {
      const names2 = strings(body.names);
      if (body.isInitial === true) {
        const next = new Set(names2);
        if (this.initialSkills === null) this.initialSkills = [...next].sort();
        for (const name of this.loadedSkills) if (!next.has(name)) this.droppedSkills.add(name);
        this.loadedSkills = next;
      } else {
        for (const name of names2) this.loadedSkills.add(name);
      }
      for (const name of names2) {
        this.everLoadedSkills.add(name);
        if (this.droppedSkills.delete(name) && date !== null) this.loadedOn(date).reloadedSkills.add(name);
      }
      this.loadedDirty = true;
      return;
    }
    if (type === "mcp_instructions_delta") {
      for (const name of strings(body.removedNames)) {
        this.loadedMcp.delete(name);
        this.droppedMcp.add(name);
      }
      for (const name of strings(body.addedNames)) {
        this.loadedMcp.add(name);
        if (this.droppedMcp.delete(name) && date !== null) this.loadedOn(date).reloadedMcp.add(name);
      }
      this.loadedDirty = true;
      return;
    }
    if (type === "instructions") {
      if (this.instructionChars !== null || !Array.isArray(body.files)) return;
      let ascii = 0;
      let other = 0;
      for (const file of body.files) {
        const content = obj(file)?.content;
        if (typeof content !== "string") continue;
        for (const ch of content) {
          if (ch.codePointAt(0) < 128) ascii++;
          else other++;
        }
      }
      this.instructionChars = { ascii, other };
      return;
    }
    if (date === null) return;
    const day = this.day(date);
    if (type === "invoked_skills") {
      for (const skill of Array.isArray(body.skills) ? body.skills : []) {
        const name = str(obj(skill)?.name);
        if (name !== null) this.skillSignal(day, name).injected++;
      }
      return;
    }
    if (type === "deferred_tools_delta") {
      if (Array.isArray(body.failedMcpServers) && body.failedMcpServers.length > 0) {
        day.mcpConnectionFailure = true;
        for (const item2 of body.failedMcpServers) {
          const name = typeof item2 === "string" ? item2 : str(obj(item2)?.name);
          if (name !== null && name !== "") bump(day.mcpFailedServers, name);
        }
      }
      return;
    }
    if (type === "hook_success" || type === "hook_non_blocking_error") {
      const counts = this.hook(day, str(body.hookEvent) ?? UNKNOWN_TOOL);
      counts.runs++;
      if (type === "hook_non_blocking_error") counts.failures++;
      return;
    }
    if (type === "hook_blocking_error") {
      const counts = this.hook(day, str(body.hookEvent) ?? UNKNOWN_TOOL);
      if (hasFailureMarker(body.blockingError)) {
        counts.runs++;
        counts.failures++;
      } else {
        counts.unclassifiedBlocks++;
      }
      return;
    }
    if (type.startsWith("hook_") && !KNOWN_HOOK_ATTACHMENTS.has(type)) bump(this.unknownHookKinds, type);
  }
  onSystem(line, date) {
    if (line.subtype !== "compact_boundary" || date === null) return;
    const trigger = obj(line.compactMetadata)?.trigger;
    if (trigger === "auto") this.day(date).autoCompactions++;
    else if (trigger !== "manual") this.day(date).unknownCompactions++;
  }
  loadedOn(date) {
    let loaded = this.dayLoaded.get(date);
    if (loaded === void 0) {
      loaded = { skills: /* @__PURE__ */ new Set(), mcp: /* @__PURE__ */ new Set(), reloadedSkills: /* @__PURE__ */ new Set(), reloadedMcp: /* @__PURE__ */ new Set() };
      this.dayLoaded.set(date, loaded);
    }
    return loaded;
  }
  /** 그 날짜 칸에 지금 실려 있는 스킬과 MCP 서버의 이름을 더한다. 날짜나 실린 것이 바뀔 때만 계산한다. */
  markLoaded(date) {
    if (date === null || date === this.loadedMarkDate && !this.loadedDirty) return;
    const loaded = this.loadedOn(date);
    for (const name of this.loadedSkills) loaded.skills.add(name);
    for (const name of this.loadedMcp) loaded.mcp.add(name);
    this.loadedMarkDate = date;
    this.loadedDirty = false;
  }
  hook(day, event) {
    let counts = day.hooks[event];
    if (counts === void 0) {
      counts = emptyHookCounts();
      day.hooks[event] = counts;
    }
    return counts;
  }
};

// src/adapters/codex/observation.ts
var CODEX_COVERAGE = {
  responsesAndTokens: "measured",
  humanRequests: "proxy",
  toolCalls: "proxy",
  toolErrors: "measured",
  shellExitCodes: "measured",
  deniedAndLengthStops: "unsupported",
  interruptedTurns: "measured",
  autoCompaction: "proxy",
  effort: "measured",
  loadedNames: "unsupported",
  skillUsage: "unsupported",
  mcpCalls: "measured",
  mcpFailuresAndHooks: "unsupported",
  instructionSize: "measured",
  subagents: "unsupported"
};
var CODEX_MCP_NON_SIGNAL_TYPES = /* @__PURE__ */ new Set(["session_meta", "turn_context", "token_usage_record", "world_state", "compacted"]);
function codexMcpObservation(summaries, unreadableCount2) {
  return observeRecords(summaries, unreadableCount2, CODEX_MCP_NON_SIGNAL_TYPES, (summary) => summary.missing.tooLongMcpLines ?? summary.missing.tooLongLines);
}
var CODEX_USAGE_MARKERS = [
  { name: "mcp", bytes: Buffer.from('"McpToolCall"', "utf8") },
  { name: "mcp", bytes: Buffer.from('"mcp__', "utf8") }
];

// src/adapters/codex/parser.ts
var EXEC_TOOLS = /* @__PURE__ */ new Map([
  ["CommandExecution", { name: "shell", status: true }],
  ["FileChange", { name: "file_change", status: true }],
  ["McpToolCall", { name: "mcp", status: true }],
  ["ImageView", { name: "image_view", status: false }],
  ["Extension", { name: "extension", status: false }],
  ["WebSearch", { name: "web_search", status: false }],
  // 0.3.0. Codex 0.166.0~0.169.0의 TurnItem(공개 소스 codex-rs/protocol/src/items.rs)에서 도구 호출인 나머지 넷. 상태의 값을 기록으로 확인하지 못해 호출만 센다(다른 PC 피드백 8번)
  ["DynamicToolCall", { name: "dynamic_tool", status: false }],
  ["CollabAgentToolCall", { name: "collab_agent", status: false }],
  ["ImageGeneration", { name: "image_generation", status: false }],
  ["FunctionCallOutput", { name: "function", status: false }]
]);
var CODEX_SHELL_TOOLS = ["shell"];
var NON_TOOL_ITEMS = /* @__PURE__ */ new Set(["UserMessage", "AgentMessage", "Reasoning", "ContextCompaction", "Plan", "HookPrompt", "SubAgentActivity", "EnteredReviewMode", "ExitedReviewMode"]);
var CALL_TYPES = /* @__PURE__ */ new Set(["function_call", "custom_tool_call", "web_search_call"]);
var CODEX_PARSER_VERSION = 2;
var SUB_THREAD_SOURCES = /* @__PURE__ */ new Set(["subagent", "guardian_review", "memory_consolidation"]);
var obj2 = (value) => value !== null && typeof value === "object" && !Array.isArray(value) ? value : null;
var num2 = (value) => typeof value === "number" && Number.isFinite(value) ? value : 0;
var str2 = (value) => typeof value === "string" && value !== "" ? value : null;
function parseObject2(text) {
  try {
    return obj2(JSON.parse(text));
  } catch {
    return null;
  }
}
function usageOf(value) {
  const raw = obj2(value);
  if (raw === null) return null;
  return { input: num2(raw.input_tokens), cacheRead: num2(raw.cached_input_tokens), cacheWrite: num2(raw.cache_write_input_tokens), output: num2(raw.output_tokens), thinking: num2(raw.reasoning_output_tokens) };
}
var KEYS = ["input", "cacheRead", "cacheWrite", "output", "thinking"];
function compareUsage(current, previous) {
  if (KEYS.some((key) => current[key] < previous[key])) return "smaller";
  return KEYS.every((key) => current[key] === previous[key]) ? "equal" : "greater";
}
var totalPrint = (total) => fnv1a64(KEYS.map((key) => total[key]).join("|"));
function normalizeVersion(value) {
  const text = str2(value);
  const match = text === null ? null : /^(\d+\.\d+\.\d+)(?:[-+].*)?$/.exec(text.trim());
  return match === null ? null : match[1];
}
var CodexSessionParser = class {
  constructor(ctx) {
    this.ctx = ctx;
  }
  ctx;
  days = /* @__PURE__ */ new Map();
  firstDate = null;
  /** 시각이 있는 마지막 줄(종류와 상관없이)의 날짜 */
  lastDate = null;
  sessionId = null;
  kind = "main";
  parentSessionId = null;
  cwd = null;
  version = null;
  unknownThreadSource = null;
  /** 빈 줄이 아닌 첫 물리적 줄을 받았는지, 그 줄이 session_meta라서 그 줄로 정체를 정하는 중인지, 세션 ID를 기록 파일의 식별자로 대신 쓴 까닭(「5단계 계획 전 결정」 7번) */
  firstLineSeen = false;
  identityPending = false;
  idFallback = null;
  lines = 0;
  brokenLines = 0;
  tailFragments = 0;
  tooLongLines = 0;
  tooLongMcpLines = 0;
  undatedLines = 0;
  /** 깨진 줄과 끝 조각의 맨 바깥 종류(온전히 읽히지 않으면 ?)별 수. MCP 호출의 관측이 빠짐없는지 가른다(설계 9.8) */
  unconfirmedTypes = nameRecord();
  /** 새 구간에 들어섰는지(token_usage_record를 한 번이라도 봤는지) */
  inNew = false;
  /** 옛 구간에서 마지막으로 본 누적값. 새 구간의 첫 기록과 견준다 */
  lastOldTotal = null;
  seenResponses = /* @__PURE__ */ new Set();
  /** 지금 창(앞 턴이 끝난 뒤부터 이 턴이 끝날 때까지)의 turn_context의 모델과 추론 강도, 그 창에서 문맥을 봤는지, 문맥보다 앞에 와서 아직 문맥을 붙이지 못한 응답의 칸 */
  model = null;
  effort = null;
  contextSeen = false;
  pendingCells = [];
  /** 지금 묶음(턴, 또는 턴 밖)에서 날짜마다 센 호출 층과 실행 층의 도구 수. 날짜를 몰라 세지 못한 줄은 넣지 않는다 */
  groupCalls = /* @__PURE__ */ new Map();
  groupExec = /* @__PURE__ */ new Map();
  unknownItemTypes = nameRecord();
  instructionChars = null;
  /** 자기 기록의 지문(이어받아 뺀 것도 넣는다. 손자 세션이 같은 앞부분을 다시 이어받을 수 있다) */
  myItemIds = /* @__PURE__ */ new Set();
  myCallIds = /* @__PURE__ */ new Set();
  myTotals = /* @__PURE__ */ new Set();
  myResponseIds = /* @__PURE__ */ new Set();
  inheritedSkipped = { items: 0, totals: 0, responses: 0 };
  /**
   * 이어받아 뺀 강한 것(도구와 사람 요청의 항목, 호출, 누적값, 응답)의 마지막 줄 자리와, 뺄 지문을 받고 처음 센 옛 구간 누적값의 줄 자리. 뒤의 것이 앞의 것보다 앞이면
   * 복사된 앞부분 안에서 뺄 지문에 없는 누적값을 센 것이라 기준을 찾지 못한 기록이다(「5단계 계획 전 결정」 7번)
   */
  lastInheritedLine = -1;
  firstCountedOldLine = -1;
  tool(cell, name) {
    let counts = cell.tools[name];
    if (!counts) {
      counts = emptyToolCounts();
      cell.tools[name] = counts;
    }
    return counts;
  }
  /**
   * 묶음을 닫는다. 호출 층이 실행 층보다 많으면 그 차이를 이름 모름의 호출로 더한다(설계 9.6). 차이는 날짜 차례로, 그날 호출 층이 실행 층보다 많은 만큼까지
   * 그날에 나눈다. 날짜를 몰라 세지 못한 줄은 어느 층에도 넣지 않았다(「5단계 1부 계획에서 보완」)
   */
  closeGroup() {
    const sum2 = (counts) => [...counts.values()].reduce((total, n) => total + n, 0);
    let extra = sum2(this.groupCalls) - sum2(this.groupExec);
    for (const date of [...this.groupCalls.keys()].sort()) {
      if (extra <= 0) break;
      const give = Math.min(extra, this.groupCalls.get(date) - (this.groupExec.get(date) ?? 0));
      if (give <= 0) continue;
      this.tool(this.day(date), UNKNOWN_TOOL).calls += give;
      extra -= give;
    }
    this.groupCalls.clear();
    this.groupExec.clear();
  }
  /** 문맥의 창을 닫는다. 창에서 문맥을 보지 못한 응답은 모델을 모르고 추론 강도를 모르는 것으로 센다(설계 9.6 「그 턴의 응답들에 적용」) */
  closeContext() {
    for (const cell of this.pendingCells.splice(0)) cell.unknownEffort++;
    this.model = null;
    this.effort = null;
    this.contextSeen = false;
  }
  /** 응답 하나의 칸에 지금 창의 모델과 추론 강도를 붙인다 */
  attribute(cell) {
    if (this.model !== null) cell.models[this.model] = (Object.hasOwn(cell.models, this.model) ? cell.models[this.model] : 0) + 1;
    if (this.effort !== null) cell.efforts[this.effort] = (Object.hasOwn(cell.efforts, this.effort) ? cell.efforts[this.effort] : 0) + 1;
    else cell.unknownEffort++;
  }
  /** 줄바꿈으로 끝난 줄 하나를 받는다. 빈 줄(공백만 있는 줄)은 세지 않는다 */
  line(text) {
    if (text.trim() === "") return;
    this.lines++;
    const parsed = parseObject2(text);
    this.firstLine(parsed);
    if (parsed === null) this.missing(text, "broken");
    else this.accept(parsed);
  }
  /** 풀리지 않는 줄이나 끝 조각 하나. 맨 바깥 종류를 센다(1단계와 같다) */
  missing(text, kind) {
    if (kind === "broken") this.brokenLines++;
    else this.tailFragments++;
    const type = outerTypeOf(text) ?? "?";
    this.unconfirmedTypes[type] = (Object.hasOwn(this.unconfirmedTypes, type) ? this.unconfirmedTypes[type] : 0) + 1;
  }
  /** 빈 줄이 아닌 첫 물리적 줄 하나만 본다. 풀리지 않거나 너무 길면 첫 줄을 읽지 못한 것이고, 풀렸는데 session_meta가 아니면 정체를 모르는 것이다. 그 뒤의 session_meta로 정체를 정하지 않는다(「5단계 계획 전 결정」 7번) */
  firstLine(parsed) {
    if (this.firstLineSeen) return;
    this.firstLineSeen = true;
    if (parsed === null) this.idFallback = "first-line-unreadable";
    else if (parsed.type !== "session_meta") this.idFallback = "first-line-not-meta";
    else this.identityPending = true;
  }
  /** 상한을 넘은 줄 하나를 받는다. found는 줄의 바이트에서 찾은 MCP 호출의 표지다(0.3.0) */
  tooLong(found) {
    this.lines++;
    this.tooLongLines++;
    if (found?.has("mcp")) this.tooLongMcpLines++;
    this.firstLine(null);
  }
  day(date) {
    let cell = this.days.get(date);
    if (!cell) {
      cell = emptyDay();
      this.days.set(date, cell);
    }
    return cell;
  }
  /** 세는 줄의 날짜. 시각이 없으면 앞 줄(종류와 상관없이)의 날짜를 쓰고, 앞 줄도 없으면 날짜 없는 줄로 센다(1단계와 같다). 세는 줄마다 한 번만 부른다 */
  dateOf() {
    if (this.lastDate === null) this.undatedLines++;
    return this.lastDate;
  }
  /** 풀린 줄 하나. 종류와 상관없이 그 줄의 시각을 앞 줄의 날짜와 가장 이른 날짜에 쓰고, 종류에 따라 해석한다 */
  accept(row) {
    const own = localDateOfIso(row.timestamp, this.ctx.timeZone);
    if (own !== null) {
      this.lastDate = own;
      if (this.firstDate === null || own < this.firstDate) this.firstDate = own;
    }
    const payload = obj2(row.payload) ?? {};
    if (row.type === "session_meta") {
      this.meta(payload, this.identityPending);
      this.identityPending = false;
      return;
    }
    if (row.type === "event_msg" && payload.type === "token_count") {
      if (!this.inNew) this.oldCount(usageOf(obj2(payload.info)?.total_token_usage));
      return;
    }
    if (row.type === "token_usage_record") return this.newRecord(payload);
    if (row.type === "turn_context") {
      this.model = str2(payload.model);
      this.effort = str2(payload.effort);
      if (!this.contextSeen) {
        this.contextSeen = true;
        for (const cell of this.pendingCells.splice(0)) this.attribute(cell);
      }
      return;
    }
    if (row.type === "event_msg" && (payload.type === "task_started" || payload.type === "task_complete" || payload.type === "turn_aborted")) {
      this.closeGroup();
      if (payload.type !== "task_started") this.closeContext();
      if (payload.type === "turn_aborted") {
        const date = this.dateOf();
        if (date !== null) this.day(date).interruptedTurns++;
      }
      return;
    }
    if (row.type === "response_item" && typeof payload.type === "string" && CALL_TYPES.has(payload.type)) {
      const callId = str2(payload.call_id);
      if (callId !== null) {
        const print = fnv1a64(callId);
        this.myCallIds.add(print);
        if (this.ctx.inherited?.callIds.has(print)) {
          this.lastInheritedLine = this.lines;
          return;
        }
      }
      const date = this.dateOf();
      if (date !== null) this.groupCalls.set(date, (this.groupCalls.get(date) ?? 0) + 1);
      return;
    }
    if (row.type === "event_msg" && payload.type === "item_completed") return this.item(obj2(payload.item));
    if (row.type === "compacted") {
      const date = this.dateOf();
      if (date !== null) this.day(date).autoCompactions++;
      return;
    }
    if (row.type === "world_state" && this.instructionChars === null) {
      const text = obj2(obj2(obj2(payload.state)?.agents_md))?.text;
      if (typeof text === "string") {
        let ascii = 0;
        let other = 0;
        for (const char of text) {
          if (char.codePointAt(0) < 128) ascii++;
          else other++;
        }
        this.instructionChars = { ascii, other };
      }
    }
  }
  /** 실행 층의 사건 하나. 도구면 이름별로 세고, 사람 요청이면 세고, 도구가 아닌 종류는 넘기며, 모르는 종류는 따로 센다 */
  item(item2) {
    if (item2 === null) return;
    const type = str2(item2.type);
    if (type === null) return;
    const itemId = str2(item2.id);
    if (itemId !== null) {
      const print = fnv1a64(itemId);
      this.myItemIds.add(print);
      if (this.ctx.inherited?.itemIds.has(print)) {
        this.inheritedSkipped.items++;
        if (type === "UserMessage" || EXEC_TOOLS.has(type)) this.lastInheritedLine = this.lines;
        return;
      }
    }
    if (type === "UserMessage") {
      const date2 = this.dateOf();
      if (date2 !== null) this.day(date2).humanRequests++;
      return;
    }
    if (NON_TOOL_ITEMS.has(type)) return;
    const kind = EXEC_TOOLS.get(type);
    if (kind === void 0) {
      this.unknownItemTypes[type] = (Object.hasOwn(this.unknownItemTypes, type) ? this.unknownItemTypes[type] : 0) + 1;
      return;
    }
    const date = this.dateOf();
    if (date === null) return;
    this.groupExec.set(date, (this.groupExec.get(date) ?? 0) + 1);
    const cell = this.day(date);
    const server = type === "McpToolCall" ? str2(item2.server) : null;
    const name = type === "McpToolCall" ? `mcp__${server ?? UNKNOWN_TOOL}` : kind.name;
    const counts = this.tool(cell, name);
    counts.calls++;
    if (type === "McpToolCall" && server !== null) cell.mcpCalls[server] = (Object.hasOwn(cell.mcpCalls, server) ? cell.mcpCalls[server] : 0) + 1;
    if (!kind.status) return;
    counts.results++;
    const failed = type === "CommandExecution" ? typeof item2.exit_code === "number" && item2.exit_code !== 0 : item2.status === "failed";
    if (failed) counts.errors++;
  }
  /** session_meta 하나. 버전은 모든 session_meta에서 가장 높은 것을 남기고(설계 9.3), 정체(세션 ID, 작업 폴더, 주·하위, 부모)는 첫 줄의 것에서만 정한다 */
  meta(payload, first) {
    this.version = maxVersion([this.version, normalizeVersion(payload.cli_version)]);
    if (!first) return;
    this.sessionId = str2(payload.id);
    if (this.sessionId === null) this.idFallback = "meta-without-id";
    this.cwd = str2(payload.cwd);
    const source = payload.thread_source;
    if (source === "user") this.kind = "main";
    else if (typeof source === "string" && SUB_THREAD_SOURCES.has(source)) {
      this.kind = "sub";
      this.parentSessionId = str2(payload.parent_thread_id);
    } else {
      this.kind = "main";
      this.unknownThreadSource = typeof source === "string" ? source : "(\uC5C6\uC74C)";
    }
  }
  /** 응답 하나를 그 날의 칸에 더한다. 날짜를 얻지 못하면 세지 않는다(날짜 없는 줄로는 dateOf가 센다) */
  count(add) {
    const date = this.dateOf();
    if (date === null) return;
    const cell = this.day(date);
    cell.responses++;
    for (const key of KEYS) cell.tokens[key] += add[key];
    if (this.contextSeen) this.attribute(cell);
    else this.pendingCells.push(cell);
  }
  oldCount(total) {
    if (total === null) return;
    const previous = this.lastOldTotal;
    this.lastOldTotal = total;
    const print = totalPrint(total);
    this.myTotals.add(print);
    if (this.ctx.inherited?.totals.has(print)) {
      this.inheritedSkipped.totals++;
      this.lastInheritedLine = this.lines;
      return;
    }
    if (this.ctx.inherited && this.firstCountedOldLine < 0 && (previous === null || compareUsage(total, previous) !== "equal")) this.firstCountedOldLine = this.lines;
    if (previous === null) return this.count(total);
    const relation = compareUsage(total, previous);
    if (relation === "equal") return;
    if (relation === "smaller") return this.count(total);
    const diff = { ...total };
    for (const key of KEYS) diff[key] = total[key] - previous[key];
    this.count(diff);
  }
  newRecord(payload) {
    const responseId = str2(payload.response_id);
    const use = usageOf(payload.usage);
    const first = !this.inNew;
    this.inNew = true;
    if (responseId !== null) {
      if (this.seenResponses.has(responseId)) return;
      this.seenResponses.add(responseId);
      const print = fnv1a64(responseId);
      this.myResponseIds.add(print);
      if (this.ctx.inherited?.responseIds.has(print)) {
        this.inheritedSkipped.responses++;
        this.lastInheritedLine = this.lines;
        return;
      }
    }
    if (use === null) return;
    if (first && this.lastOldTotal !== null) {
      const thread = usageOf(payload.thread_token_usage);
      if (thread !== null && compareUsage(thread, this.lastOldTotal) === "equal") return;
    }
    this.count(use);
  }
  /** 자기 기록의 지문. finish 뒤에 부른다 */
  fingerprints() {
    return { itemIds: this.myItemIds, callIds: this.myCallIds, totals: this.myTotals, responseIds: this.myResponseIds };
  }
  /** 파일 끝의 줄바꿈 없는 조각을 받고 요약을 낸다. 조각이 풀리면 받아들이고, 안 풀리면 쓰는 중일 때만 끝 조각이고 아니면 깨진 줄이다(1단계와 같다) */
  finish(tail, inProgress) {
    if (tail !== null && tail.trim() !== "") {
      this.lines++;
      const parsed = parseObject2(tail);
      this.firstLine(parsed);
      if (parsed !== null) this.accept(parsed);
      else this.missing(tail, inProgress ? "tail" : "broken");
    }
    this.closeGroup();
    this.closeContext();
    if (!this.firstLineSeen) this.idFallback = "no-lines";
    const days = {};
    for (const date of [...this.days.keys()].sort()) days[date] = canonicalDay(this.days.get(date));
    return {
      tool: "codex",
      sessionId: this.sessionId ?? this.ctx.recordId,
      kind: this.kind,
      parentSessionId: this.kind === "sub" ? this.parentSessionId : null,
      cwd: this.cwd,
      version: this.version,
      firstDate: this.firstDate,
      days,
      instructionChars: this.instructionChars,
      initialSkills: null,
      initialMcpServers: null,
      missing: { lines: this.lines, brokenLines: this.brokenLines, tailFragments: this.tailFragments, tooLongLines: this.tooLongLines, tooLongMcpLines: this.tooLongMcpLines, unconfirmedTypes: sortedRecord(this.unconfirmedTypes) },
      firstResponseIdHashes: [],
      notes: { syntheticResponses: 0, responsesWithoutId: 0, undatedLines: this.undatedLines, unknownHookKinds: nameRecord() },
      codex: { recordId: this.ctx.recordId, unknownThreadSource: this.unknownThreadSource, idFallback: this.idFallback, unknownItemTypes: sortedRecord(this.unknownItemTypes), inheritedSkipped: { ...this.inheritedSkipped }, baselineMissing: this.firstCountedOldLine >= 0 && this.firstCountedOldLine < this.lastInheritedLine }
    };
  }
};

// src/adapters/gemini/observation.ts
var GEMINI_COVERAGE = {
  responsesAndTokens: "measured",
  humanRequests: "proxy",
  toolCalls: "measured",
  toolErrors: "measured",
  shellExitCodes: "proxy",
  deniedAndLengthStops: "unsupported",
  interruptedTurns: "unsupported",
  autoCompaction: "unsupported",
  effort: "unsupported",
  loadedNames: "unsupported",
  skillUsage: "unsupported",
  mcpCalls: "measured",
  mcpFailuresAndHooks: "unsupported",
  instructionSize: "unsupported",
  subagents: "measured"
};
var GEMINI_MCP_NON_SIGNAL_TYPES = /* @__PURE__ */ new Set(["user", "info", "error", "warning"]);
function geminiMcpObservation(summaries, unreadableCount2) {
  return observeRecords(summaries, unreadableCount2, GEMINI_MCP_NON_SIGNAL_TYPES, (summary) => summary.missing.tooLongMcpLines ?? summary.missing.tooLongLines);
}
var GEMINI_USAGE_MARKERS = [
  { name: "mcp", bytes: Buffer.from('"mcp_', "utf8") },
  { name: "skill", bytes: Buffer.from('"activate_skill"', "utf8") }
];

// src/adapters/gemini/parser.ts
var GEMINI_PARSER_VERSION = 2;
var GEMINI_SHELL_TOOLS = ["run_shell_command"];
var SUBAGENT_TOOLS2 = /* @__PURE__ */ new Set(["invoke_agent"]);
var SKILL_TOOL = "activate_skill";
var MCP_PREFIX = "mcp_";
var MESSAGE_TYPES = /* @__PURE__ */ new Set(["user", "gemini", "info", "error", "warning"]);
var FIRST_RESPONSE_IDS2 = 20;
var UNKNOWN_TOOL2 = "?";
var num3 = (value) => typeof value === "number" && Number.isFinite(value) ? value : 0;
var str3 = (value) => typeof value === "string" && value !== "" ? value : null;
var obj3 = (value) => value !== null && typeof value === "object" && !Array.isArray(value) ? value : null;
var bump2 = (record, key, by = 1) => {
  record[key] = (Object.hasOwn(record, key) ? record[key] : 0) + by;
};
function parseObject3(text) {
  try {
    return obj3(JSON.parse(text));
  } catch {
    return null;
  }
}
function geminiMcpServerKey(toolName) {
  if (!toolName.startsWith(MCP_PREFIX)) return null;
  const rest = toolName.slice(MCP_PREFIX.length);
  const cut = rest.indexOf("_");
  const server = cut === -1 ? rest : rest.slice(0, cut);
  return server === "" ? null : server;
}
var NOT_HUMAN_HEADS = ["/", "?", "<session_context>", "<hook_context>", "<state_snapshot>"];
var humanText = (text) => {
  const trimmed = text.trim();
  return trimmed.length > 0 && !NOT_HUMAN_HEADS.some((head) => trimmed.startsWith(head));
};
function isHumanContent(content) {
  if (typeof content === "string") return humanText(content);
  const parts = Array.isArray(content) ? content : [content];
  return parts.some((part) => {
    if (typeof part === "string") return humanText(part);
    const piece = obj3(part);
    return piece !== null && typeof piece.text === "string" && piece.thought !== true && humanText(piece.text);
  });
}
var EXIT_CODE = /\nExit Code: (-?\d+)(?:\n(?:Signal|Background PIDs|Process Group PGID): [^\n]*)*\s*$/;
var UNTRUSTED = /^<untrusted_context(?: [^>]*)?>\n([\s\S]*)\n<\/untrusted_context>\s*$/;
var unwrapped = (text) => UNTRUSTED.exec(text)?.[1] ?? text;
var POLICY_DENIAL = "Tool execution denied by policy";
function responseTexts(result) {
  const parts = Array.isArray(result) ? result : [result];
  const texts = [];
  for (const part of parts) {
    const response = obj3(obj3(obj3(part)?.functionResponse)?.response);
    if (response === null) continue;
    for (const value of Object.values(response)) if (typeof value === "string") texts.push(value);
  }
  return texts;
}
var GeminiSessionParser = class {
  constructor(ctx) {
    this.ctx = ctx;
  }
  ctx;
  days = /* @__PURE__ */ new Map();
  /** 메시지 ID → 마지막 줄. 같은 ID가 다시 적히면 뒤의 줄이 이긴다(소스 chatRecordingService의 pushMessage). Map은 처음 나온 차례를 지킨다 */
  messages = /* @__PURE__ */ new Map();
  toolIds = /* @__PURE__ */ new Set();
  /** 메시지 ID → 처음 나온 차례 */
  firstSeen = /* @__PURE__ */ new Map();
  /** 이력 동기화가 새 ID로 다시 적은 user 메시지(압축 요약, 남겨 둔 대화의 사본). 사람 요청으로 세지 않는다 */
  copies = /* @__PURE__ */ new Set();
  firstIds = [];
  unconfirmedTypes = nameRecord();
  metaSessionId = null;
  firstDate = null;
  lines = 0;
  brokenLines = 0;
  tailFragments = 0;
  tooLongLines = 0;
  tooLongSkillLines = 0;
  tooLongMcpLines = 0;
  undatedLines = 0;
  withoutId = 0;
  /** 줄바꿈으로 끝난 줄 하나. 빈 줄은 세지 않는다 */
  line(text) {
    if (text.trim() === "") return;
    this.lines++;
    const parsed = parseObject3(text);
    if (parsed === null) this.missing(text, "broken");
    else this.accept(parsed);
  }
  /** 옛 꼴(.json) 파일 하나. 세션 정보와 메시지 목록이 든 JSON 한 덩어리다. 풀리지 않으면 깨진 줄 하나로 센다 */
  legacy(text) {
    const parsed = parseObject3(text);
    if (parsed === null) {
      this.lines++;
      this.missing(text, "broken");
      return;
    }
    const { messages, ...meta } = parsed;
    this.lines++;
    this.accept(meta);
    if (!Array.isArray(messages)) return;
    for (const message of messages) {
      this.lines++;
      const record = obj3(message);
      if (record === null) {
        this.brokenLines++;
        bump2(this.unconfirmedTypes, "?");
      } else this.accept(record);
    }
  }
  /** 상한을 넘은 줄 하나. found는 줄의 바이트에서 찾은 사용 흔적의 표지다 */
  tooLong(found) {
    this.lines++;
    this.tooLongLines++;
    if (found?.has("skill")) this.tooLongSkillLines++;
    if (found?.has("mcp")) this.tooLongMcpLines++;
  }
  /** 끝 조각을 정리하고 요약을 낸다. 한 번만 부른다 */
  finish(tail, inProgress) {
    if (tail !== null && tail.trim() !== "") {
      this.lines++;
      const parsed = parseObject3(tail);
      if (parsed !== null) this.accept(parsed);
      else this.missing(tail, inProgress ? "tail" : "broken");
    }
    for (const [id, record] of this.messages) this.count(id, record);
    const days = {};
    for (const date of [...this.days.keys()].sort()) days[date] = canonicalDay(this.days.get(date));
    return {
      tool: "gemini",
      sessionId: this.metaSessionId ?? this.ctx.sessionId,
      kind: this.ctx.kind,
      parentSessionId: this.ctx.parentSessionId,
      cwd: this.ctx.cwd,
      // 제미나이 CLI는 세션 기록에 자기 버전을 적지 않는다
      version: null,
      firstDate: this.firstDate,
      days,
      instructionChars: null,
      initialSkills: null,
      initialMcpServers: null,
      missing: {
        lines: this.lines,
        brokenLines: this.brokenLines,
        tailFragments: this.tailFragments,
        tooLongLines: this.tooLongLines,
        tooLongSkillLines: this.tooLongSkillLines,
        tooLongMcpLines: this.tooLongMcpLines,
        unconfirmedTypes: sortedRecord(this.unconfirmedTypes)
      },
      firstResponseIdHashes: this.firstIds.map(fnv1a64),
      notes: { syntheticResponses: 0, responsesWithoutId: this.withoutId, undatedLines: this.undatedLines, unknownHookKinds: nameRecord() }
    };
  }
  missing(text, kind) {
    if (kind === "broken") this.brokenLines++;
    else this.tailFragments++;
    bump2(this.unconfirmedTypes, outerTypeOf(text) ?? "?");
  }
  /** 고침 줄의 도구 결과를 이미 읽은 메시지에 얹는다(셸의 종료 코드가 결과로 나중에 붙을 수 있다). 내용 고침, 지우기, 차례 바꾸기는 세는 것을 바꾸지 않아 보지 않는다 */
  patch(patch) {
    const single = (update) => {
      const target = this.messages.get(str3(update.id) ?? "");
      if (target === void 0 || !Array.isArray(update.toolCalls) || !Array.isArray(target.toolCalls)) return;
      for (const raw of update.toolCalls) {
        const change = obj3(raw);
        const callId = str3(change?.id);
        if (change === null || callId === null || !Object.hasOwn(change, "result")) continue;
        for (const call of target.toolCalls) {
          const shaped = obj3(call);
          if (shaped !== null && shaped.id === callId) shaped.result = change.result;
        }
      }
    };
    single(patch);
    if (Array.isArray(patch.updates)) {
      for (const update of patch.updates) if (obj3(update) !== null) single(obj3(update));
    }
    if (Array.isArray(patch.removeIds)) this.markCopies(new Set(patch.removeIds.filter((id) => typeof id === "string")));
  }
  /**
   * 이력을 새 ID로 다시 적으면(압축 뒤의 요약·확인과 남긴 대화, 압축이 실패한 뒤의 잘라내기) 제미나이는 다시 적은 메시지를 한 번에 붙이고 옛 메시지를 지우는 고침 줄(removeIds)을 붙인다.
   * 다시 적은 gemini 메시지에는 모델 이름도 토큰도 없다. 지운 메시지 가운데 마지막 것보다 뒤에 처음 나온 메시지가 그 구간이고, 구간의 user 메시지 가운데
   * 다음 user 메시지 전까지 실제 응답(모델 이름이나 토큰이 있는 gemini)이 따르지 않는 것을 사본으로 본다. 실제 응답이 따르는 요청은 압축이 아닌 이력 고침 뒤에 남은 새 요청이라 센다.
   * 구간 안에서 응답을 받지 못하고 끝난 진짜 새 요청은 사본과 가를 정보가 기록에 없어 사본으로 본다(사람 요청은 대신 보는 값이다)
   * (소스 geminiChat.ts의 생성자·initialize·setHistory, chatRecordingService.ts의 updateMessagesFromHistory, context/chatCompressionService.ts, 짝 검토 4차 필수 1)
   */
  markCopies(removed) {
    let last = -1;
    for (const id of removed) last = Math.max(last, this.firstSeen.get(id) ?? -1);
    if (last < 0) return;
    const window = [...this.messages.keys()].filter((id) => !removed.has(id) && this.firstSeen.get(id) > last);
    const answer = (record) => record.type === "gemini" && (str3(record.model) !== null || obj3(record.tokens) !== null);
    for (let index = 0; index < window.length; index++) {
      if (this.messages.get(window[index]).type !== "user") continue;
      let answered = false;
      for (let next = index + 1; next < window.length && !answered; next++) {
        const after = this.messages.get(window[next]);
        if (after.type === "user") break;
        answered = answer(after);
      }
      if (!answered) this.copies.add(window[index]);
    }
  }
  /** 풀린 줄 하나. 되감기 줄은 세지 않는다(되감은 메시지도 사용량이 든 것이라 센다). 고침 줄은 도구 결과만 얹고, 설정 줄은 옛 체크포인트의 메시지만 읽는다. 종류가 없는 줄은 세션 정보 줄이다 */
  accept(record) {
    if (Object.hasOwn(record, "$patch")) {
      const patch = obj3(record.$patch);
      if (patch !== null) this.patch(patch);
      return;
    }
    if (Object.hasOwn(record, "$set")) {
      const set = obj3(record.$set);
      if (set !== null && Array.isArray(set.messages)) {
        for (const message of set.messages) if (obj3(message) !== null && str3(obj3(message).type) !== null) this.accept(obj3(message));
      }
      return;
    }
    if (Object.hasOwn(record, "$rewindTo")) return;
    const type = str3(record.type);
    if (type === null) {
      if (typeof record.sessionId === "string" && this.metaSessionId === null) this.metaSessionId = record.sessionId;
      this.noteDate(localDateOfIso(record.startTime, this.ctx.timeZone));
      return;
    }
    if (!MESSAGE_TYPES.has(type)) {
      bump2(this.unconfirmedTypes, type);
      return;
    }
    const id = str3(record.id);
    if (id === null) {
      this.withoutId++;
      this.messages.set(`#${this.withoutId}`, record);
      return;
    }
    if (!this.firstSeen.has(id)) this.firstSeen.set(id, this.firstSeen.size);
    this.messages.set(id, record);
  }
  noteDate(date) {
    if (date !== null && (this.firstDate === null || date < this.firstDate)) this.firstDate = date;
  }
  day(date) {
    let cell = this.days.get(date);
    if (cell === void 0) {
      cell = emptyDay();
      this.days.set(date, cell);
    }
    return cell;
  }
  tool(day, name) {
    let counts = day.tools[name];
    if (counts === void 0) {
      counts = emptyToolCounts();
      day.tools[name] = counts;
    }
    return counts;
  }
  skillSignal(day, name) {
    let counts = day.skillSignals[name];
    if (counts === void 0) {
      counts = emptySkillSignalCounts();
      day.skillSignals[name] = counts;
    }
    return counts;
  }
  /** 메시지 하나(그 ID의 마지막 줄)를 날짜 칸에 센다 */
  count(id, record) {
    const date = localDateOfIso(record.timestamp, this.ctx.timeZone);
    if (date === null) {
      this.undatedLines++;
      return;
    }
    this.noteDate(date);
    const day = this.day(date);
    if (record.type === "user") {
      if (this.ctx.kind === "main" && !this.copies.has(id) && isHumanContent(record.content)) day.humanRequests++;
      return;
    }
    if (record.type !== "gemini") return;
    const model = str3(record.model);
    const tokens = obj3(record.tokens);
    if (model !== null || tokens !== null) {
      day.responses++;
      const responseId = str3(record.id);
      if (responseId !== null && this.firstIds.length < FIRST_RESPONSE_IDS2) this.firstIds.push(responseId);
      if (tokens !== null) {
        day.tokens.input += num3(tokens.input);
        day.tokens.cacheRead += num3(tokens.cached);
        day.tokens.output += num3(tokens.output);
        day.tokens.thinking += num3(tokens.thoughts);
      }
      if (model !== null) bump2(day.models, model);
      day.unknownEffort++;
    }
    if (!Array.isArray(record.toolCalls)) return;
    for (const raw of record.toolCalls) {
      const call = obj3(raw);
      if (call === null) continue;
      const callId = str3(call.id);
      if (callId !== null) {
        if (this.toolIds.has(callId)) continue;
        this.toolIds.add(callId);
      }
      const name = str3(call.name) ?? UNKNOWN_TOOL2;
      const server = geminiMcpServerKey(name);
      const counts = this.tool(day, server === null ? name : `${MCP_PREFIX}${server}`);
      counts.calls++;
      const status = str3(call.status);
      const texts = responseTexts(call.result);
      if (status === "error" && texts.some((text) => text.startsWith(POLICY_DENIAL))) {
        counts.deniedByPermission++;
      } else if (status === "success" || status === "error") {
        counts.results++;
        const failedExit = GEMINI_SHELL_TOOLS.includes(name) && texts.some((text) => Number(EXIT_CODE.exec(unwrapped(text))?.[1] ?? 0) !== 0);
        if (status === "error" || failedExit) counts.errors++;
      } else if (status === "cancelled") {
        counts.unknownDenial++;
      }
      if (server !== null) bump2(day.mcpCalls, server);
      if (name === SKILL_TOOL) {
        const skill = str3(obj3(call.args)?.name);
        if (skill !== null) this.skillSignal(day, skill).tool++;
      }
      if (SUBAGENT_TOOLS2.has(name)) day.subagentCalls++;
    }
  }
};

// src/collect/claude.ts
import { join as join12 } from "node:path";

// src/adapters/common/lines.ts
import { open as open3, stat as stat2 } from "node:fs/promises";
var MAX_LINE_BYTES = 16 * 1024 * 1024;
var IN_PROGRESS_WINDOW_MS = 2e3;
function decode(buffer, start, end) {
  return buffer.toString("utf8", start, end > start && buffer[end - 1] === 13 ? end - 1 : end);
}
var BACKSLASH = 92;
var LOWER_U = 117;
function hexValue(byte) {
  if (byte >= 48 && byte <= 57) return byte - 48;
  if (byte >= 65 && byte <= 70) return byte - 55;
  if (byte >= 97 && byte <= 102) return byte - 87;
  return -1;
}
function escapeDecoder() {
  let held = Buffer.alloc(0);
  return {
    push(piece) {
      const input = held.length > 0 ? Buffer.concat([held, piece]) : piece;
      held = Buffer.alloc(0);
      if (input.indexOf(BACKSLASH) === -1) return input;
      const out = Buffer.allocUnsafe(input.length);
      let written = 0;
      let index = 0;
      while (index < input.length) {
        const slash = input.indexOf(BACKSLASH, index);
        written += input.copy(out, written, index, slash === -1 ? input.length : slash);
        if (slash === -1) break;
        if (slash + 1 >= input.length || input[slash + 1] === LOWER_U && slash + 6 > input.length) {
          held = Buffer.from(input.subarray(slash));
          break;
        }
        if (input[slash + 1] !== LOWER_U) {
          out[written++] = BACKSLASH;
          out[written++] = input[slash + 1];
          index = slash + 2;
          continue;
        }
        let code = 0;
        for (let at = slash + 2; at < slash + 6; at++) {
          const digit = hexValue(input[at]);
          code = digit < 0 || code < 0 ? -1 : code * 16 + digit;
        }
        if (code < 0) {
          out[written++] = BACKSLASH;
          out[written++] = LOWER_U;
          index = slash + 2;
          continue;
        }
        if (code === 34 || code === BACKSLASH) {
          out[written++] = BACKSLASH;
          out[written++] = code;
        } else if (code < 128) {
          out[written++] = code;
        } else {
          written += input.copy(out, written, slash, slash + 6);
        }
        index = slash + 6;
      }
      return out.subarray(0, written);
    },
    reset() {
      held = Buffer.alloc(0);
    }
  };
}
function lineSplitter(sink, maxLine = MAX_LINE_BYTES, markers = []) {
  let carry = Buffer.allocUnsafe(Math.min(maxLine, 64 * 1024));
  let carryBytes = 0;
  let skipping = false;
  const longest = markers.reduce((most, marker2) => Math.max(most, marker2.bytes.length), 0);
  const decoder = escapeDecoder();
  let found = /* @__PURE__ */ new Set();
  let edge = Buffer.alloc(0);
  const scan = (raw) => {
    if (markers.length === 0 || raw.length === 0) return;
    const piece = decoder.push(raw);
    const joined = edge.length > 0 ? Buffer.concat([edge, piece]) : piece;
    for (const marker2 of markers) if (!found.has(marker2.name) && joined.indexOf(marker2.bytes) !== -1) found.add(marker2.name);
    edge = Buffer.from(joined.subarray(Math.max(0, joined.length - (longest - 1))));
  };
  const endLong = () => {
    sink.tooLong(found);
    found = /* @__PURE__ */ new Set();
    edge = Buffer.alloc(0);
    decoder.reset();
  };
  return {
    push(view) {
      let start = 0;
      for (; ; ) {
        const newline = view.indexOf(10, start);
        const end = newline === -1 ? view.length : newline;
        if (!skipping) {
          const length = end - start;
          if (carryBytes + length > maxLine) {
            skipping = true;
            scan(carry.subarray(0, carryBytes));
            scan(view.subarray(start, end));
            carryBytes = 0;
          } else if (newline !== -1 && carryBytes === 0) {
            sink.line(decode(view, start, end));
            start = newline + 1;
            continue;
          } else if (length > 0) {
            if (carry.length < carryBytes + length) {
              const grown = Buffer.allocUnsafe(Math.min(maxLine, Math.max(carryBytes + length, carry.length * 2)));
              carry.copy(grown, 0, 0, carryBytes);
              carry = grown;
            }
            view.copy(carry, carryBytes, start, end);
            carryBytes += length;
          }
        } else {
          scan(view.subarray(start, end));
        }
        if (newline === -1) break;
        if (skipping) {
          endLong();
          skipping = false;
        } else {
          sink.line(decode(carry, 0, carryBytes));
        }
        carryBytes = 0;
        start = newline + 1;
      }
    },
    finish() {
      if (skipping) {
        endLong();
        return null;
      }
      return carryBytes > 0 ? decode(carry, 0, carryBytes) : null;
    }
  };
}
async function readLines(path, nowMs, sink, options = {}) {
  const maxLine = options.maxLineBytes ?? MAX_LINE_BYTES;
  const chunkSize = options.chunkBytes ?? 1024 * 1024;
  const handle = await open3(path, "r");
  try {
    const opened = await handle.stat();
    const sizeAtOpen = opened.size;
    const mtimeMsAtOpen = opened.mtimeMs;
    if (options.afterOpen) await options.afterOpen();
    const buffer = Buffer.allocUnsafe(chunkSize);
    const splitter = lineSplitter(sink, maxLine, options.markers ?? []);
    let position = 0;
    while (position < sizeAtOpen) {
      const { bytesRead } = await handle.read(buffer, 0, Math.min(chunkSize, sizeAtOpen - position), position);
      if (bytesRead === 0) break;
      position += bytesRead;
      splitter.push(buffer.subarray(0, bytesRead));
    }
    const tail = splitter.finish();
    const after = await stat2(path);
    const inProgress = after.size !== sizeAtOpen || after.mtimeMs !== mtimeMsAtOpen || nowMs - mtimeMsAtOpen < IN_PROGRESS_WINDOW_MS;
    return { sizeAtOpen, mtimeMsAtOpen, bytesRead: position, tail, inProgress: inProgress || position < sizeAtOpen, endedEarly: position < sizeAtOpen };
  } finally {
    await handle.close();
  }
}

// src/collect/claude.ts
var CLAUDE_PARSER_ID = `claude-code@${CLAUDE_PARSER_VERSION}`;
function unreadableCount(read) {
  return read.unreadableFiles.length + read.unreadableDirs.length;
}
async function collectClaude(options) {
  const home = claudeHome(options.env, options.homedir);
  const windows = makeWindows(options.clock.nowMs, options.clock.timeZone);
  const list = await listClaudeFiles(home, options.rescan ? null : windows.collectStartLowerBoundMs);
  return collectFromList(home, list, options);
}
async function collectFromList(home, list, options) {
  const windows = makeWindows(options.clock.nowMs, options.clock.timeZone);
  const cacheDir = options.cacheDir === null ? null : join12(options.cacheDir, "claude-code");
  const files = [...list.files].sort((a, b) => a.normPath < b.normPath ? -1 : a.normPath > b.normPath ? 1 : 0);
  const summaries = [];
  const unreadableFiles = [...list.unreadableFiles];
  let unreadableFileBytes = 0;
  let bytes = 0;
  let fromCache = 0;
  let inProgress = 0;
  const markUnreadable = (path, size) => {
    unreadableFiles.push(path);
    unreadableFileBytes += size;
  };
  for (const file of files) {
    let key = null;
    try {
      if (cacheDir !== null) {
        key = await cacheKeyFor(file, CLAUDE_PARSER_ID, options.clock.timeZone);
        if (!options.rescan && key !== null) {
          const hit = await loadCached(cacheDir, key);
          if (hit !== null) {
            summaries.push(hit.summary);
            bytes += hit.bytesRead;
            fromCache++;
            if (mostlyBroken(hit.summary)) markUnreadable(file.path, file.size);
            continue;
          }
        }
      }
      const parser = new ClaudeSessionParser({
        sessionId: file.sessionId,
        kind: file.kind,
        parentSessionId: file.parentSessionId,
        timeZone: options.clock.timeZone
      });
      const outcome = await readLines(
        file.path,
        options.clock.nowMs,
        {
          line: (text) => parser.line(text),
          tooLong: (found) => parser.tooLong(found)
        },
        { markers: CLAUDE_USAGE_MARKERS }
      );
      const summary = parser.finish(outcome.tail, outcome.inProgress);
      summaries.push(summary);
      bytes += outcome.bytesRead;
      if (mostlyBroken(summary) || outcome.endedEarly) markUnreadable(file.path, file.size);
      if (outcome.inProgress) {
        inProgress++;
        continue;
      }
      if (key !== null && cacheDir !== null && outcome.sizeAtOpen === file.size && outcome.mtimeMsAtOpen === file.mtimeMs) {
        try {
          if (await keyStillMatches(file.path, key)) await storeCached(cacheDir, { key, summary, bytesRead: outcome.bytesRead });
        } catch {
        }
      }
    } catch {
      markUnreadable(file.path, file.size);
    }
  }
  unreadableFiles.sort();
  return {
    tool: "claude-code",
    home,
    detected: list.projectsFound,
    summaries,
    read: {
      files: files.length + list.unreadableFiles.length,
      listedBytes: files.reduce((sum2, file) => sum2 + file.size, 0),
      bytes,
      fromCache,
      inProgress,
      olderThanWindow: list.olderThanWindow,
      unreadableFiles,
      unreadableFileBytes,
      unknownSizeFiles: list.unreadableFiles.length,
      unreadableDirs: [...list.unreadableDirs].sort()
    },
    visibleFrom: visibleFrom(summaries, list.olderThanWindow, windows.collectDates[0]),
    overlappingSessions: overlappingSessions(summaries)
  };
}
function visibleFrom(summaries, olderThanWindow, collectStart) {
  if (olderThanWindow > 0) return collectStart;
  let earliest = null;
  for (const summary of summaries) {
    if (summary.firstDate !== null && (earliest === null || summary.firstDate < earliest)) earliest = summary.firstDate;
  }
  if (earliest === null) return null;
  return earliest < collectStart ? collectStart : earliest;
}
function overlappingSessions(summaries) {
  const owners = /* @__PURE__ */ new Map();
  summaries.forEach((summary, index) => {
    for (const hash of summary.firstResponseIdHashes) {
      let set = owners.get(hash);
      if (set === void 0) {
        set = /* @__PURE__ */ new Set();
        owners.set(hash, set);
      }
      set.add(index);
    }
  });
  const overlapping = /* @__PURE__ */ new Set();
  for (const set of owners.values()) {
    if (set.size > 1) for (const index of set) overlapping.add(index);
  }
  return overlapping.size;
}

// src/collect/codex.ts
import { join as join14 } from "node:path";

// src/adapters/codex/locate.ts
import { readdir as readdir5, stat as stat3 } from "node:fs/promises";
import { join as join13, resolve as resolve2 } from "node:path";
function codexHome(env, homedir2) {
  const fromEnv = env.CODEX_HOME?.trim();
  return fromEnv ? resolve2(fromEnv) : join13(homedir2, ".codex");
}
var isMissing4 = (error) => error?.code === "ENOENT";
var DIGITS = /^\d+$/;
var ROLLOUT = /^rollout-.*?-(?:([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})_)?([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\.jsonl(\.zst)?$/i;
async function listCodexFiles(home, minChangedMs, statFile = stat3) {
  const sessions = join13(home, "sessions");
  const files = [];
  const unreadableDirs = [];
  let olderThanWindow = 0;
  let unnamedFiles = 0;
  const walk = async (dir, depth) => {
    let entries;
    try {
      entries = await readdir5(dir, { withFileTypes: true });
    } catch (error) {
      if (depth === 0 && isMissing4(error)) return false;
      if (!isMissing4(error)) unreadableDirs.push(dir);
      return true;
    }
    for (const entry of entries) {
      const path = join13(dir, entry.name);
      if (depth < 3) {
        if (DIGITS.test(entry.name) && !entry.isFile()) await walk(path, depth + 1);
        else if (DIGITS.test(entry.name) && entry.isFile()) unreadableDirs.push(path);
        continue;
      }
      if (!entry.isFile() || !/^rollout-.*\.jsonl(\.zst)?$/i.test(entry.name)) continue;
      const match = ROLLOUT.exec(entry.name);
      if (match === null) {
        unnamedFiles++;
        continue;
      }
      const baseId = match[1]?.toLowerCase() ?? null;
      const recordId = match[2].toLowerCase();
      const compressed = match[3] !== void 0;
      try {
        const info = await statFile(path);
        const changedMs = Math.max(info.mtimeMs, info.ctimeMs);
        if (minChangedMs !== null && changedMs < minChangedMs) {
          olderThanWindow++;
          continue;
        }
        files.push({ path, normPath: normalizePath(path), size: info.size, mtimeMs: info.mtimeMs, changedMs, recordId, baseId, compressed });
      } catch {
        files.push({ path, normPath: normalizePath(path), size: null, mtimeMs: null, changedMs: null, recordId, baseId, compressed });
      }
    }
    return true;
  };
  const found = await walk(sessions, 0);
  if (!found) return { sessionsFound: false, files: [], olderThanWindow: 0, unreadableDirs: [], unnamedFiles: 0 };
  files.sort((a, b) => a.normPath < b.normPath ? -1 : a.normPath > b.normPath ? 1 : 0);
  unreadableDirs.sort();
  return { sessionsFound: true, files, olderThanWindow, unreadableDirs, unnamedFiles };
}
function canonicalOrder(a, b) {
  if (a.compressed !== b.compressed) return a.compressed ? 1 : -1;
  if (a.changedMs !== b.changedMs) {
    if (a.changedMs === null) return 1;
    if (b.changedMs === null) return -1;
    return b.changedMs - a.changedMs;
  }
  return a.normPath < b.normPath ? -1 : a.normPath > b.normPath ? 1 : 0;
}
function groupCopies(files) {
  const groups = /* @__PURE__ */ new Map();
  for (const file of files) {
    const list = groups.get(file.recordId);
    if (list) list.push(file);
    else groups.set(file.recordId, [file]);
  }
  return [...groups.entries()].sort(([a], [b]) => a < b ? -1 : a > b ? 1 : 0).map(([recordId, copies]) => ({ recordId, copies: [...copies].sort(canonicalOrder) }));
}

// src/adapters/codex/merge.ts
var recordIdOf = (summary) => summary.codex?.recordId ?? summary.sessionId;
var byRecordId = (a, b) => recordIdOf(a) < recordIdOf(b) ? -1 : recordIdOf(a) > recordIdOf(b) ? 1 : 0;
function addNumbers(into, from) {
  for (const [key, value] of Object.entries(from)) into[key] = (Object.hasOwn(into, key) ? into[key] : 0) + value;
}
function mergeRecords(records, outside2 = []) {
  if (records.length === 1 && outside2.length === 0) return records[0];
  const sorted = [...records].sort(byRecordId);
  const all = [...records, ...outside2].sort(byRecordId);
  const base = all.find((summary) => recordIdOf(summary) === summary.sessionId) ?? all[0];
  const first = (pick) => pick(base) ?? all.map(pick).find((value) => value !== null) ?? null;
  const cells = /* @__PURE__ */ new Map();
  const unconfirmedTypes = nameRecord();
  const unknownHookKinds = nameRecord();
  const unknownItemTypes = nameRecord();
  const missing = { lines: 0, brokenLines: 0, tailFragments: 0, tooLongLines: 0 };
  let longMcp = 0;
  let mcpCounted = true;
  const notes = { syntheticResponses: 0, responsesWithoutId: 0, undatedLines: 0 };
  const inheritedSkipped = { items: 0, totals: 0, responses: 0 };
  let firstDate = null;
  for (const summary of sorted) {
    for (const [date, cell] of Object.entries(summary.days)) {
      let into = cells.get(date);
      if (into === void 0) {
        into = emptyDay();
        cells.set(date, into);
      }
      addDayInto(into, cell);
    }
    missing.lines += summary.missing.lines;
    missing.brokenLines += summary.missing.brokenLines;
    missing.tailFragments += summary.missing.tailFragments;
    missing.tooLongLines += summary.missing.tooLongLines;
    if (summary.missing.tooLongMcpLines === void 0) mcpCounted = false;
    else longMcp += summary.missing.tooLongMcpLines;
    addNumbers(unconfirmedTypes, summary.missing.unconfirmedTypes);
    notes.syntheticResponses += summary.notes.syntheticResponses;
    notes.responsesWithoutId += summary.notes.responsesWithoutId;
    notes.undatedLines += summary.notes.undatedLines;
    addNumbers(unknownHookKinds, summary.notes.unknownHookKinds);
    if (summary.codex !== void 0) {
      addNumbers(unknownItemTypes, summary.codex.unknownItemTypes);
      inheritedSkipped.items += summary.codex.inheritedSkipped.items;
      inheritedSkipped.totals += summary.codex.inheritedSkipped.totals;
      inheritedSkipped.responses += summary.codex.inheritedSkipped.responses;
    }
  }
  for (const summary of all) {
    if (summary.firstDate !== null && (firstDate === null || summary.firstDate < firstDate)) firstDate = summary.firstDate;
  }
  const days = {};
  for (const date of [...cells.keys()].sort()) days[date] = canonicalDay(cells.get(date));
  const instructionChars = first((summary) => summary.instructionChars);
  const codex = base.codex;
  return {
    tool: base.tool,
    sessionId: base.sessionId,
    kind: base.kind,
    parentSessionId: base.parentSessionId,
    cwd: first((summary) => summary.cwd),
    version: maxVersion(all.map((summary) => summary.version)),
    firstDate,
    days,
    instructionChars: instructionChars === null ? null : { ascii: instructionChars.ascii, other: instructionChars.other },
    initialSkills: base.initialSkills === null ? null : [...base.initialSkills],
    initialMcpServers: base.initialMcpServers === null ? null : [...base.initialMcpServers],
    missing: { ...missing, ...mcpCounted ? { tooLongMcpLines: longMcp } : {}, unconfirmedTypes: sortedRecord(unconfirmedTypes) },
    firstResponseIdHashes: [...base.firstResponseIdHashes],
    notes: { ...notes, unknownHookKinds: sortedRecord(unknownHookKinds) },
    ...codex === void 0 ? {} : {
      codex: {
        recordId: codex.recordId,
        unknownThreadSource: first((summary) => summary.codex?.unknownThreadSource ?? null),
        idFallback: codex.idFallback,
        unknownItemTypes: sortedRecord(unknownItemTypes),
        inheritedSkipped,
        baselineMissing: sorted.some((summary) => summary.codex?.baselineMissing === true)
      }
    }
  };
}

// src/adapters/codex/zstd.ts
import { createReadStream } from "node:fs";
import { open as open4, stat as stat4 } from "node:fs/promises";
import * as zlib from "node:zlib";
var ZSTD_MAGIC = 4247762216;
var SKIPPABLE_MASK = 4294967280;
var SKIPPABLE_MAGIC = 407710288;
var MAGIC_BYTES = [40, 181, 47, 253];
var SKIPPABLE_BYTES = [80, 42, 77, 24];
function magicPrefix(bytes) {
  const data = bytes.every((byte, index) => byte === MAGIC_BYTES[index]);
  const skippable = bytes.every((byte, index) => index === 0 ? (byte & 240) === SKIPPABLE_BYTES[0] : byte === SKIPPABLE_BYTES[index]);
  return data || skippable;
}
function zstdAvailable() {
  return typeof zlib.createZstdDecompress === "function";
}
async function scanZstdFrames(path, maxBytes = Infinity, seen = { endedEarly: false }) {
  const handle = await open4(path, "r");
  try {
    const size = Math.min((await handle.stat()).size, maxBytes);
    if (Number.isFinite(maxBytes) && size < maxBytes) seen.endedEarly = true;
    const small = Buffer.alloc(18);
    const readAt2 = async (position2, length) => {
      let offset = 0;
      while (offset < length) {
        const { bytesRead } = await handle.read(small, offset, length - offset, position2 + offset);
        if (bytesRead === 0) break;
        offset += bytesRead;
      }
      if (offset < length) seen.endedEarly = true;
      return small.subarray(0, offset);
    };
    let position = 0;
    let frames = 0;
    const ranges = [];
    let frameStart = null;
    if (size === 0) return { status: "invalid", frames: 0, ranges, brokenFrameStart: null };
    while (position < size) {
      const left = size - position;
      const lead = await readAt2(position, Math.min(4, left));
      if (lead.length < 4) return { status: magicPrefix(lead) ? "truncated" : "invalid", frames, ranges, brokenFrameStart: null };
      const magic = lead.readUInt32LE(0);
      frameStart = null;
      if ((magic & SKIPPABLE_MASK) >>> 0 === SKIPPABLE_MAGIC) {
        if (left < 8) return { status: "truncated", frames, ranges, brokenFrameStart: frameStart };
        const field = await readAt2(position + 4, 4);
        if (field.length < 4) return { status: "truncated", frames, ranges, brokenFrameStart: frameStart };
        const length = field.readUInt32LE(0);
        position += 8 + length;
        if (position > size) return { status: "truncated", frames, ranges, brokenFrameStart: frameStart };
        continue;
      }
      if (magic !== ZSTD_MAGIC) return { status: "invalid", frames, ranges, brokenFrameStart: null };
      frameStart = position;
      position += 4;
      if (position >= size) return { status: "truncated", frames, ranges, brokenFrameStart: frameStart };
      const descriptorByte = await readAt2(position, 1);
      if (descriptorByte.length < 1) return { status: "truncated", frames, ranges, brokenFrameStart: frameStart };
      const descriptor = descriptorByte[0];
      const fcsFlag = descriptor >> 6;
      const singleSegment = descriptor >> 5 & 1;
      const reserved = descriptor >> 3 & 1;
      const checksum = descriptor >> 2 & 1;
      const dictFlag = descriptor & 3;
      if (reserved !== 0) return { status: "invalid", frames, ranges, brokenFrameStart: frameStart };
      const headerBytes = 1 + (singleSegment ? 0 : 1) + [0, 1, 2, 4][dictFlag] + [singleSegment ? 1 : 0, 2, 4, 8][fcsFlag];
      position += headerBytes;
      if (position > size) return { status: "truncated", frames, ranges, brokenFrameStart: frameStart };
      for (; ; ) {
        if (size - position < 3) return { status: "truncated", frames, ranges, brokenFrameStart: frameStart };
        const head = await readAt2(position, 3);
        if (head.length < 3) return { status: "truncated", frames, ranges, brokenFrameStart: frameStart };
        const value = head[0] | head[1] << 8 | head[2] << 16;
        const last = value & 1;
        const type = value >> 1 & 3;
        const blockSize = value >>> 3;
        if (type === 3) return { status: "invalid", frames, ranges, brokenFrameStart: frameStart };
        position += 3 + (type === 1 ? 1 : blockSize);
        if (position > size) return { status: "truncated", frames, ranges, brokenFrameStart: frameStart };
        if (last) break;
      }
      if (checksum) {
        position += 4;
        if (position > size) return { status: "truncated", frames, ranges, brokenFrameStart: frameStart };
      }
      frames++;
      ranges.push([frameStart, position]);
      frameStart = null;
    }
    return { status: frames > 0 ? "complete" : "invalid", frames, ranges, brokenFrameStart: null };
  } finally {
    await handle.close();
  }
}
async function decodeRange(path, start, end, push) {
  const source = createReadStream(path, { start, end: end - 1 });
  let bytesRead = 0;
  let decodedBytes = 0;
  source.on("data", (chunk) => {
    bytesRead += typeof chunk === "string" ? Buffer.byteLength(chunk) : chunk.length;
  });
  const decoder = zlib.createZstdDecompress();
  source.on("error", (error) => decoder.destroy(error));
  source.pipe(decoder);
  try {
    for await (const chunk of decoder) {
      decodedBytes += chunk.length;
      push(chunk);
    }
    return { bytesRead, decodedBytes, error: bytesRead === end - start ? null : "SHORT_INPUT" };
  } catch (error) {
    source.destroy();
    return { bytesRead, decodedBytes, error: error.code ?? String(error.message ?? error) };
  }
}
async function readZstdLines(path, nowMs, sink, options = {}) {
  const opened = await stat4(path);
  const sizeAtOpen = opened.size;
  const mtimeMsAtOpen = opened.mtimeMs;
  if (options.afterOpen) await options.afterOpen();
  const seen = { endedEarly: false };
  const frames = await scanZstdFrames(path, sizeAtOpen, seen);
  const splitter = lineSplitter(sink, options.maxLineBytes ?? MAX_LINE_BYTES, options.markers ?? []);
  let bytesRead = 0;
  let decodedBytes = 0;
  let decodeError = sizeAtOpen === 0 ? "EMPTY" : null;
  const targets = [...frames.ranges];
  if (frames.brokenFrameStart !== null) targets.push([frames.brokenFrameStart, sizeAtOpen]);
  for (const [start, end] of targets) {
    const result = await decodeRange(path, start, end, (chunk) => splitter.push(chunk));
    bytesRead += result.bytesRead;
    decodedBytes += result.decodedBytes;
    if (result.error !== null) {
      decodeError = result.error;
      break;
    }
  }
  if (decodeError === null && frames.status === "invalid" && targets.length === 0) decodeError = "INVALID";
  const tail = splitter.finish();
  const after = await stat4(path);
  const inProgress = after.size !== sizeAtOpen || after.mtimeMs !== mtimeMsAtOpen || nowMs - mtimeMsAtOpen < IN_PROGRESS_WINDOW_MS;
  return { sizeAtOpen, mtimeMsAtOpen, bytesRead, decodedBytes, tail, inProgress: inProgress || seen.endedEarly || decodeError === "SHORT_INPUT", endedEarly: seen.endedEarly || decodeError === "SHORT_INPUT", decodeError, frames };
}

// src/collect/codex.ts
var CODEX_PARSER_ID = `codex@${CODEX_PARSER_VERSION}`;
function codexUnreadableCount(read) {
  return read.unreadableFiles.length + read.unreadableDirs.length + read.skippedFiles.length + read.partialFiles.length;
}
var byPath = (a, b) => a.normPath < b.normPath ? -1 : a.normPath > b.normPath ? 1 : 0;
var baseName = (path) => path.slice(Math.max(path.lastIndexOf("/"), path.lastIndexOf("\\")) + 1);
var siblingOrder = (a, b) => {
  const original = (record) => record.canonical.recordId === record.summary.sessionId ? 0 : 1;
  if (original(a) !== original(b)) return original(a) - original(b);
  const an = baseName(a.canonical.path);
  const bn = baseName(b.canonical.path);
  return an < bn ? -1 : an > bn ? 1 : byPath(a.canonical, b.canonical);
};
var keysOf2 = (group) => [.../* @__PURE__ */ new Set([group.recordId, ...group.copies.flatMap((copy2) => copy2.baseId === null ? [] : [copy2.baseId])])];
var recentlyChanged = (file, options) => file.changedMs !== null && options.clock.nowMs - file.changedMs < IN_PROGRESS_WINDOW_MS;
async function parseCopy(file, inherited, options) {
  const parser = new CodexSessionParser({ recordId: file.recordId, timeZone: options.clock.timeZone, inherited });
  const sink = { line: (text) => parser.line(text), tooLong: (found) => parser.tooLong(found) };
  if (!file.compressed) {
    const outcome2 = await readLines(file.path, options.clock.nowMs, sink, { markers: CODEX_USAGE_MARKERS });
    const stable2 = outcome2.sizeAtOpen === file.size && outcome2.mtimeMsAtOpen === file.mtimeMs;
    const inProgress2 = outcome2.inProgress || !stable2 || recentlyChanged(file, options);
    const summary2 = parser.finish(outcome2.tail, inProgress2);
    return { summary: summary2, prints: parser.fingerprints(), bytesRead: outcome2.bytesRead, inProgress: inProgress2, partial: outcome2.endedEarly, storable: !inProgress2 };
  }
  const outcome = await readZstdLines(file.path, options.clock.nowMs, sink, { markers: CODEX_USAGE_MARKERS });
  const incomplete = outcome.frames.status !== "complete" || outcome.decodeError !== null || outcome.endedEarly;
  if (incomplete && outcome.decodedBytes === 0) throw new Error(outcome.decodeError ?? outcome.frames.status);
  const stable = outcome.sizeAtOpen === file.size && outcome.mtimeMsAtOpen === file.mtimeMs;
  const inProgress = outcome.inProgress || !stable || recentlyChanged(file, options);
  const summary = parser.finish(outcome.tail, inProgress);
  return { summary, prints: parser.fingerprints(), bytesRead: outcome.bytesRead, inProgress, partial: incomplete, storable: !inProgress && !incomplete };
}
async function readGroup(group, options, zstd, cacheDir) {
  const canonical = group.copies[0];
  let failure6 = null;
  for (const file of group.copies) {
    if (file.size === null || file.mtimeMs === null) {
      failure6 ??= "unknown-size";
      continue;
    }
    if (file.compressed && !zstd) {
      failure6 ??= "skipped";
      continue;
    }
    try {
      let key = null;
      if (cacheDir !== null) {
        key = await cacheKeyFor({ path: file.path, normPath: file.normPath, size: file.size, mtimeMs: file.mtimeMs }, CODEX_PARSER_ID, options.clock.timeZone);
        if (key !== null && !options.rescan && !recentlyChanged(file, options)) {
          const hit = await loadCached(cacheDir, key);
          const prints = hit?.codex === void 0 ? null : fromLists(hit.codex.fingerprints);
          if (hit !== null && hit.codex !== void 0 && prints !== null) {
            return { canonical, file, key, summary: hit.summary, prints, digest: hit.codex.sharedDigest, bytesRead: hit.bytesRead, fromCache: true, storable: false, inProgress: false, partial: false, failed: false };
          }
        }
      }
      const parsed = await parseCopy(file, null, options);
      return { canonical, file, key, ...parsed, digest: sharedDigest(parsed.prints, null), fromCache: false, failed: false };
    } catch {
      failure6 ??= "failed";
    }
  }
  return failure6 ?? "failed";
}
async function collectCodex(options) {
  const home = codexHome(options.env, options.homedir);
  return collectCodexFromList(home, await listCodexFiles(home, null, options.statFile), options);
}
async function collectCodexFromList(home, list, options) {
  const windows = makeWindows(options.clock.nowMs, options.clock.timeZone);
  const lowerBound = options.rescan ? null : windows.collectStartLowerBoundMs;
  const cacheDir = options.cacheDir === null ? null : join14(options.cacheDir, "codex");
  const zstd = options.zstd ?? zstdAvailable();
  const groups = groupCopies(list.files).map((group) => ({ ...group, copies: [...group.copies] })).sort((a, b) => byPath(a.copies[0], b.copies[0]));
  const inWindow = groups.filter((group) => lowerBound === null || group.copies[0].changedMs === null || group.copies[0].changedMs >= lowerBound);
  const inside2 = new Set(inWindow);
  const outside2 = /* @__PURE__ */ new Map();
  for (const group of groups) {
    if (inside2.has(group)) continue;
    for (const key of keysOf2(group)) {
      const found = outside2.get(key);
      if (found === void 0) outside2.set(key, [group]);
      else found.push(group);
    }
  }
  const read = {
    files: inWindow.length,
    listedBytes: 0,
    bytes: 0,
    fromCache: 0,
    inProgress: 0,
    olderThanWindow: list.olderThanWindow + groups.length - inWindow.length,
    unreadableFiles: [],
    unreadableFileBytes: 0,
    unknownSizeFiles: 0,
    unreadableDirs: [...list.unreadableDirs].sort(),
    skippedFiles: [],
    skippedFileBytes: 0,
    partialFiles: [],
    skippedCopies: inWindow.reduce((sum2, group) => sum2 + group.copies.length - 1, 0),
    unnamedFiles: list.unnamedFiles
  };
  const reads = [];
  const failedGroups = [];
  const readOf = /* @__PURE__ */ new Map();
  for (const group of inWindow) {
    const result = await readGroup(group, options, zstd, cacheDir);
    read.unknownSizeFiles += group.copies.filter((copy2) => copy2.size === null).length;
    if (typeof result !== "string") {
      reads.push(result);
      readOf.set(group, result);
      read.listedBytes += result.file.size ?? 0;
      continue;
    }
    failedGroups.push(group);
    const canonical = group.copies[0];
    read.listedBytes += canonical.size ?? 0;
    if (result === "skipped") {
      read.skippedFiles.push(canonical.path);
      read.skippedFileBytes += canonical.size ?? 0;
      continue;
    }
    read.unreadableFiles.push(canonical.path);
    read.unreadableFileBytes += canonical.size ?? 0;
  }
  const unknownMtime = /* @__PURE__ */ new Set();
  for (const group of inWindow) {
    if (!group.copies.some((copy2) => copy2.mtimeMs === null)) continue;
    const record = readOf.get(group);
    unknownMtime.add(record === void 0 ? `record:${group.recordId}` : `session:${record.summary.sessionId}`);
  }
  const failedKeys = new Set(failedGroups.flatMap(keysOf2));
  const damaged = new Set(reads.filter((record) => record.partial || mostlyBroken(record.summary)).map((record) => record.summary.sessionId));
  const extra = /* @__PURE__ */ new Map();
  const parentPrints = /* @__PURE__ */ new Map();
  const parentOriginal = /* @__PURE__ */ new Map();
  const printsOf = async (parentId) => {
    if (parentPrints.has(parentId)) return parentPrints.get(parentId);
    const found = reads.filter((record) => record.summary.sessionId === parentId);
    for (const old of outside2.get(parentId) ?? []) {
      if (!extra.has(old)) extra.set(old, await readGroup(old, options, zstd, cacheDir));
      const result = extra.get(old);
      if (typeof result === "string") failedKeys.add(parentId);
      else if (result.summary.sessionId === parentId) {
        found.push(result);
        if (result.partial || mostlyBroken(result.summary)) damaged.add(parentId);
      }
    }
    const prints = found.length === 0 ? null : unionOf(found.map((record) => record.prints));
    parentPrints.set(parentId, prints);
    parentOriginal.set(parentId, found.some((record) => record.canonical.recordId === parentId));
    return prints;
  };
  const siblings = /* @__PURE__ */ new Map();
  for (const record of reads) {
    const list2 = siblings.get(record.summary.sessionId);
    if (list2 === void 0) siblings.set(record.summary.sessionId, [record]);
    else list2.push(record);
  }
  const outsideOf = /* @__PURE__ */ new Map();
  for (const [sessionId, list2] of siblings) {
    for (const old of outside2.get(sessionId) ?? []) {
      if (!extra.has(old)) extra.set(old, await readGroup(old, options, zstd, cacheDir));
      const result = extra.get(old);
      if (typeof result === "string") failedKeys.add(sessionId);
      else if (result.summary.sessionId === sessionId) {
        list2.push(result);
        outsideOf.set(sessionId, [...outsideOf.get(sessionId) ?? [], result.summary]);
        if (result.partial || mostlyBroken(result.summary)) damaged.add(sessionId);
      }
    }
  }
  for (const list2 of siblings.values()) list2.sort(siblingOrder);
  const parentOf = (record) => record.summary.kind === "sub" && record.summary.parentSessionId !== null && record.summary.parentSessionId !== record.summary.sessionId ? record.summary.parentSessionId : null;
  const plans = [];
  for (const record of reads) {
    const parentId = parentOf(record);
    const parent = parentId === null ? null : await printsOf(parentId);
    const list2 = siblings.get(record.summary.sessionId);
    const sources = [...parent === null ? [] : [parent], ...list2.slice(0, list2.indexOf(record)).map((sibling) => sibling.prints)];
    plans.push({ record, inherited: sources.length === 0 ? null : unionOf(sources) });
  }
  for (const { record, inherited } of plans) {
    const digest = sharedDigest(record.prints, inherited);
    if (digest === record.digest) continue;
    try {
      const parsed = await parseCopy(record.file, inherited, options);
      if (parsed.summary.sessionId !== record.summary.sessionId) throw new Error("\uB2E4\uC2DC \uC77D\uC740 \uAE30\uB85D\uC758 \uC138\uC158 ID\uAC00 \uCC98\uC74C\uACFC \uB2E4\uB974\uB2E4");
      Object.assign(record, parsed, { digest: sharedDigest(parsed.prints, inherited), fromCache: false });
    } catch {
      record.failed = true;
    }
  }
  for (const record of reads) {
    if (record.failed) failedKeys.add(record.summary.sessionId);
    else if (record.partial || mostlyBroken(record.summary)) damaged.add(record.summary.sessionId);
  }
  const orphans = /* @__PURE__ */ new Set();
  const unverified = /* @__PURE__ */ new Set();
  for (const record of reads) {
    if (record.failed) continue;
    const { sessionId } = record.summary;
    const parentId = parentOf(record);
    const parent = parentId === null ? null : await printsOf(parentId);
    if (parentId !== null && parent === null) orphans.add(sessionId);
    if (record.summary.kind === "sub" && parentId === null) unverified.add(sessionId);
    if (parentId !== null && (parent === null || parentOriginal.get(parentId) !== true || failedKeys.has(parentId) || damaged.has(parentId))) unverified.add(sessionId);
    const list2 = siblings.get(sessionId);
    if (failedKeys.has(sessionId) || list2.length > 1 && damaged.has(sessionId) || !list2.some((sibling) => sibling.canonical.recordId === sessionId)) unverified.add(sessionId);
    if (record.summary.codex?.baselineMissing === true) unverified.add(sessionId);
  }
  const kept = [];
  const idFallbacks = nameRecord();
  const unreadable = (record) => {
    read.unreadableFiles.push(record.file.path);
    read.unreadableFileBytes += record.file.size ?? 0;
  };
  for (const record of reads) {
    if (record.failed) {
      unreadable(record);
      continue;
    }
    kept.push(record);
    const fallback = record.summary.codex?.idFallback ?? null;
    if (fallback !== null) idFallbacks[fallback] = (Object.hasOwn(idFallbacks, fallback) ? idFallbacks[fallback] : 0) + 1;
    read.bytes += record.bytesRead;
    if (record.fromCache) read.fromCache++;
    if (record.inProgress) read.inProgress++;
    if (mostlyBroken(record.summary)) unreadable(record);
    else if (record.partial) read.partialFiles.push(record.file.path);
  }
  if (cacheDir !== null) {
    for (const record of [...kept, ...[...extra.values()].filter((result) => typeof result !== "string")]) {
      if (record.fromCache || !record.storable || record.key === null) continue;
      try {
        if (await keyStillMatches(record.file.path, record.key)) await storeCached(cacheDir, { key: record.key, summary: record.summary, bytesRead: record.bytesRead, codex: { fingerprints: toLists(record.prints), sharedDigest: record.digest } });
      } catch {
      }
    }
  }
  const sessions = /* @__PURE__ */ new Map();
  for (const record of kept) {
    const list2 = sessions.get(record.summary.sessionId);
    if (list2 === void 0) sessions.set(record.summary.sessionId, [record]);
    else list2.push(record);
  }
  const ordered = [...sessions.values()].sort((a, b) => byPath(a[0].canonical, b[0].canonical));
  const outsideFor = (records) => outsideOf.get(records[0].summary.sessionId) ?? [];
  const summaries = ordered.map((records) => mergeRecords(records.map((record) => record.summary), outsideFor(records)));
  read.unreadableFiles.sort();
  read.skippedFiles.sort();
  read.partialFiles.sort();
  return {
    tool: "codex",
    home,
    detected: list.sessionsFound,
    summaries,
    read,
    visibleFrom: visibleFrom(summaries, read.olderThanWindow, windows.collectDates[0]),
    parentRecordMissing: orphans.size,
    mergedSessions: ordered.filter((records) => records.length + outsideFor(records).length > 1).length,
    unknownMtimeSessions: unknownMtime.size,
    unverifiedInheritance: unverified.size,
    idFallbacks: sortedRecord(idFallbacks)
  };
}

// src/collect/gemini.ts
import { readFile as readFile7 } from "node:fs/promises";
import { join as join16 } from "node:path";

// src/adapters/gemini/locate.ts
import { readdir as readdir6, readFile as readFile6, stat as stat5 } from "node:fs/promises";
import { join as join15, resolve as resolve3 } from "node:path";
function geminiHome(env, homedir2) {
  const fromEnv = env.GEMINI_CLI_HOME?.trim();
  return join15(fromEnv ? resolve3(fromEnv) : homedir2, ".gemini");
}
function geminiRecordHomes(env, homedir2) {
  const fromEnv = env.GEMINI_CLI_HOME?.trim();
  const base = fromEnv ? resolve3(fromEnv) : homedir2;
  return [join15(base, ".gemini"), join15(base, ".cache", ".gemini")];
}
var isMissing5 = (error) => error?.code === "ENOENT";
var MAIN_FILE = /^session-.*\.(jsonl|json)$/;
var PROJECT_ROOT_FILE = ".project_root";
var PROJECT_ROOT_MAX = 4096;
async function projectRootOf(dir) {
  try {
    const info = await stat5(join15(dir, PROJECT_ROOT_FILE));
    if (!info.isFile() || info.size > PROJECT_ROOT_MAX) return null;
    const text = (await readFile6(join15(dir, PROJECT_ROOT_FILE), "utf8")).trim();
    return text === "" ? null : text;
  } catch {
    return null;
  }
}
async function listGeminiFiles(home, minMtimeMs) {
  const tmp = join15(home, "tmp");
  const files = [];
  const unreadableDirs = [];
  const unreadableFiles = [];
  let olderThanWindow = 0;
  let projectEntries;
  try {
    projectEntries = await readdir6(tmp, { withFileTypes: true });
  } catch (error) {
    if (isMissing5(error)) return { tmpFound: false, files: [], olderThanWindow: 0, unreadableDirs: [], unreadableFiles: [] };
    return { tmpFound: true, files: [], olderThanWindow: 0, unreadableDirs: [tmp], unreadableFiles: [] };
  }
  const consider = async (path, entry) => {
    try {
      const info = await stat5(path);
      if (minMtimeMs !== null && info.mtimeMs < minMtimeMs) {
        olderThanWindow++;
        return;
      }
      const big = await stat5(path, { bigint: true });
      const identity = big.ino !== 0n ? `${big.dev}:${big.ino}` : normalizePath(path);
      files.push({ path, normPath: normalizePath(path), size: info.size, mtimeMs: info.mtimeMs, identity, ...entry });
    } catch {
      unreadableFiles.push(path);
    }
  };
  for (const project of projectEntries) {
    if (!project.isDirectory()) continue;
    const projectDir = join15(tmp, project.name);
    const chats = join15(projectDir, "chats");
    let entries;
    try {
      entries = await readdir6(chats, { withFileTypes: true });
    } catch (error) {
      if (!isMissing5(error)) unreadableDirs.push(chats);
      continue;
    }
    const cwd = await projectRootOf(projectDir);
    const names2 = new Set(entries.map((entry) => entry.name));
    for (const entry of entries) {
      if (entry.isFile() && MAIN_FILE.test(entry.name)) {
        const legacy = entry.name.endsWith(".json");
        if (legacy && names2.has(`${entry.name}l`)) continue;
        await consider(join15(chats, entry.name), { sessionId: entry.name.slice(0, entry.name.lastIndexOf(".")), kind: "main", parentSessionId: null, cwd, legacy });
        continue;
      }
      if (!entry.isDirectory()) continue;
      const subDir = join15(chats, entry.name);
      let subs;
      try {
        subs = await readdir6(subDir, { withFileTypes: true });
      } catch {
        unreadableDirs.push(subDir);
        continue;
      }
      for (const sub of subs) {
        if (sub.isFile() && sub.name.endsWith(".jsonl")) {
          await consider(join15(subDir, sub.name), { sessionId: sub.name.slice(0, -".jsonl".length), kind: "sub", parentSessionId: entry.name, cwd, legacy: false });
        }
      }
    }
  }
  files.sort((a, b) => a.normPath < b.normPath ? -1 : a.normPath > b.normPath ? 1 : 0);
  unreadableDirs.sort();
  unreadableFiles.sort();
  return { tmpFound: true, files, olderThanWindow, unreadableDirs, unreadableFiles };
}
async function listGeminiRecordFiles(homes, minMtimeMs) {
  const merged = { tmpFound: false, files: [], olderThanWindow: 0, unreadableDirs: [], unreadableFiles: [] };
  const seen = /* @__PURE__ */ new Set();
  for (const home of homes) {
    const list = await listGeminiFiles(home, minMtimeMs);
    merged.tmpFound ||= list.tmpFound;
    merged.olderThanWindow += list.olderThanWindow;
    merged.unreadableDirs.push(...list.unreadableDirs);
    merged.unreadableFiles.push(...list.unreadableFiles);
    for (const file of list.files) {
      if (seen.has(file.identity)) continue;
      seen.add(file.identity);
      merged.files.push(file);
    }
  }
  merged.files.sort((a, b) => a.normPath < b.normPath ? -1 : a.normPath > b.normPath ? 1 : 0);
  merged.unreadableDirs.sort();
  merged.unreadableFiles.sort();
  return merged;
}

// src/collect/gemini.ts
var GEMINI_PARSER_ID = `gemini@${GEMINI_PARSER_VERSION}`;
async function collectGemini(options) {
  const home = geminiHome(options.env, options.homedir);
  const windows = makeWindows(options.clock.nowMs, options.clock.timeZone);
  const list = await listGeminiRecordFiles(geminiRecordHomes(options.env, options.homedir), options.rescan ? null : windows.collectStartLowerBoundMs);
  return collectGeminiFromList(home, list, options);
}
async function parseLegacy(file, parser) {
  if (file.size > MAX_LINE_BYTES) {
    parser.tooLong();
    return { bytesRead: 0 };
  }
  const text = await readFile7(file.path, "utf8");
  parser.legacy(text);
  return { bytesRead: Buffer.byteLength(text) };
}
async function collectGeminiFromList(home, list, options) {
  const windows = makeWindows(options.clock.nowMs, options.clock.timeZone);
  const cacheDir = options.cacheDir === null ? null : join16(options.cacheDir, "gemini");
  const files = [...list.files].sort((a, b) => a.normPath < b.normPath ? -1 : a.normPath > b.normPath ? 1 : 0);
  const summaries = [];
  const unreadableFiles = [...list.unreadableFiles];
  let unreadableFileBytes = 0;
  let bytes = 0;
  let fromCache = 0;
  let inProgress = 0;
  const markUnreadable = (path, size) => {
    unreadableFiles.push(path);
    unreadableFileBytes += size;
  };
  for (const file of files) {
    let key = null;
    try {
      if (cacheDir !== null) {
        key = await cacheKeyFor(file, GEMINI_PARSER_ID, options.clock.timeZone);
        if (!options.rescan && key !== null) {
          const hit = await loadCached(cacheDir, key);
          if (hit !== null) {
            summaries.push({ ...hit.summary, cwd: file.cwd });
            bytes += hit.bytesRead;
            fromCache++;
            if (mostlyBroken(hit.summary)) markUnreadable(file.path, file.size);
            continue;
          }
        }
      }
      const parser = new GeminiSessionParser({ sessionId: file.sessionId, kind: file.kind, parentSessionId: file.parentSessionId, cwd: file.cwd, timeZone: options.clock.timeZone });
      if (file.legacy) {
        const outcome2 = await parseLegacy(file, parser);
        const summary2 = parser.finish(null, false);
        summaries.push(summary2);
        bytes += outcome2.bytesRead;
        if (mostlyBroken(summary2)) markUnreadable(file.path, file.size);
        continue;
      }
      const outcome = await readLines(file.path, options.clock.nowMs, { line: (text) => parser.line(text), tooLong: (found) => parser.tooLong(found) }, { markers: GEMINI_USAGE_MARKERS });
      const summary = parser.finish(outcome.tail, outcome.inProgress);
      summaries.push(summary);
      bytes += outcome.bytesRead;
      if (mostlyBroken(summary) || outcome.endedEarly) markUnreadable(file.path, file.size);
      if (outcome.inProgress) {
        inProgress++;
        continue;
      }
      if (key !== null && cacheDir !== null && outcome.sizeAtOpen === file.size && outcome.mtimeMsAtOpen === file.mtimeMs) {
        try {
          if (await keyStillMatches(file.path, key)) await storeCached(cacheDir, { key, summary, bytesRead: outcome.bytesRead });
        } catch {
        }
      }
    } catch {
      markUnreadable(file.path, file.size);
    }
  }
  unreadableFiles.sort();
  return {
    tool: "gemini",
    home,
    detected: list.tmpFound,
    summaries,
    read: {
      files: files.length + list.unreadableFiles.length,
      listedBytes: files.reduce((sum2, file) => sum2 + file.size, 0),
      bytes,
      fromCache,
      inProgress,
      olderThanWindow: list.olderThanWindow,
      unreadableFiles,
      unreadableFileBytes,
      unknownSizeFiles: list.unreadableFiles.length,
      unreadableDirs: [...list.unreadableDirs].sort()
    },
    visibleFrom: visibleFrom(summaries, list.olderThanWindow, windows.collectDates[0]),
    overlappingSessions: overlappingSessions(summaries)
  };
}

// src/collect/web.ts
import { createHash as createHash4 } from "node:crypto";
import { mkdir as mkdir7, open as open7, readFile as readFile8, rename as rename6, stat as stat7, writeFile as writeFile6 } from "node:fs/promises";
import { join as join18 } from "node:path";

// src/adapters/web/source.ts
import { createReadStream as createReadStream3 } from "node:fs";
import { mkdtemp, open as open6, readdir as readdir7, rm as rm5, stat as stat6 } from "node:fs/promises";
import { tmpdir } from "node:os";
import { basename as basename3, join as join17 } from "node:path";

// src/adapters/web/chatgpt.ts
var obj4 = (value) => value !== null && typeof value === "object" && !Array.isArray(value) ? value : null;
var str4 = (value) => typeof value === "string" && value.length > 0 ? value : null;
function secondsToMs(value) {
  return typeof value === "number" && Number.isFinite(value) && value > 0 ? Math.round(value * 1e3) : null;
}
var CONTEXT_TYPES = /* @__PURE__ */ new Set(["user_editable_context", "model_editable_context"]);
var KNOWN_TYPES = /* @__PURE__ */ new Set([
  "text",
  "multimodal_text",
  "code",
  "execution_output",
  "thoughts",
  "reasoning_recap",
  "tether_browsing_display",
  "tether_quote",
  "system_error",
  "sonic_webpage",
  "computer_output",
  ...CONTEXT_TYPES
]);
var KNOWN_ROLES = /* @__PURE__ */ new Set(["user", "assistant", "tool", "system"]);
function chatgptConversation(value) {
  const conversation = obj4(value);
  if (conversation === null) return null;
  const mapping = obj4(conversation.mapping);
  const id = str4(conversation.conversation_id) ?? str4(conversation.id);
  if (mapping === null || id === null) return null;
  const defaultModel = str4(conversation.default_model_slug);
  const fallbackMs = secondsToMs(conversation.create_time);
  const unknownKinds = nameRecord();
  const note = (kind) => {
    unknownKinds[kind] = (unknownKinds[kind] ?? 0) + 1;
  };
  const nodes = /* @__PURE__ */ new Map();
  for (const [key, raw] of Object.entries(mapping)) {
    const node = obj4(raw);
    if (node === null) {
      note("(node)");
      continue;
    }
    const parent = str4(node.parent);
    const message = obj4(node.message);
    if (message === null) {
      nodes.set(key, { key, parent, role: null, atMs: null, model: null });
      continue;
    }
    const role = str4(obj4(message.author)?.role);
    const metadata = obj4(message.metadata);
    const contentType = str4(obj4(message.content)?.content_type);
    if (contentType !== null && !KNOWN_TYPES.has(contentType)) note(contentType);
    if (role !== null && !KNOWN_ROLES.has(role)) note(`role:${role}`);
    const hidden = metadata?.is_visually_hidden_from_conversation === true || metadata?.is_user_system_message === true || contentType !== null && CONTEXT_TYPES.has(contentType);
    const shown = hidden ? null : role === "user" || role === "assistant" ? role : role === "tool" ? "tool" : null;
    nodes.set(key, { key, parent, role: shown, atMs: secondsToMs(message.create_time) ?? fallbackMs, model: shown === "assistant" ? str4(metadata?.model_slug) ?? defaultModel : null });
  }
  const BROKEN_DEPTH = 1e6;
  const depthCache = /* @__PURE__ */ new Map();
  const depthOf = (start) => {
    const chain = [];
    const seen = /* @__PURE__ */ new Set();
    let node = start;
    let base = 0;
    while (node !== void 0) {
      if (seen.has(node.key)) {
        base = BROKEN_DEPTH;
        break;
      }
      const known2 = depthCache.get(node.key);
      if (known2 !== void 0) {
        base = known2 + 1;
        break;
      }
      seen.add(node.key);
      chain.push(node);
      if (node.parent === null) break;
      const parent = nodes.get(node.parent);
      if (parent === void 0) {
        base = BROKEN_DEPTH;
        break;
      }
      node = parent;
    }
    for (let index = chain.length - 1; index >= 0; index--) depthCache.set(chain[index].key, base + (chain.length - 1 - index));
    return depthCache.get(start.key);
  };
  const visibleAbove = (start) => {
    const seen = /* @__PURE__ */ new Set();
    for (let key = start; key !== null; ) {
      if (seen.has(key)) return "missing";
      seen.add(key);
      const node = nodes.get(key);
      if (node === void 0) return "missing";
      if (node.role === "user" || node.role === "assistant") return node.role;
      key = node.parent;
    }
    return "root";
  };
  for (const key of [...nodes.keys()].sort()) depthOf(nodes.get(key));
  const order = (a, b) => (a.atMs ?? Number.POSITIVE_INFINITY) - (b.atMs ?? Number.POSITIVE_INFINITY) || depthOf(a) - depthOf(b) || (a.key < b.key ? -1 : a.key > b.key ? 1 : 0);
  const visible = [...nodes.values()].filter((node) => node.role === "user" || node.role === "assistant").sort(order);
  const events = [];
  visible.forEach((node, index) => {
    if (node.role === "user") {
      events.push({ kind: "request", atMs: node.atMs, model: null });
      return;
    }
    const above = visibleAbove(node.parent);
    const starts = above === "missing" ? index === 0 || visible[index - 1].role === "user" : above === "user" || above === "root";
    if (starts) events.push({ kind: "response", atMs: node.atMs, model: node.model });
  });
  return { id, events, unknownKinds };
}
var looksLikeChatgpt = (value) => {
  const conversation = obj4(value);
  return conversation !== null && obj4(conversation.mapping) !== null;
};

// src/adapters/web/claude-ai.ts
var obj5 = (value) => value !== null && typeof value === "object" && !Array.isArray(value) ? value : null;
var str5 = (value) => typeof value === "string" && value.length > 0 ? value : null;
function isoToMs(value) {
  if (typeof value !== "string") return null;
  const ms = Date.parse(value);
  return Number.isFinite(ms) && ms > 0 ? ms : null;
}
function claudeConversation(value) {
  const conversation = obj5(value);
  if (conversation === null) return null;
  const id = str5(conversation.uuid);
  const messages = conversation.chat_messages;
  if (id === null || !Array.isArray(messages)) return null;
  const fallbackMs = isoToMs(conversation.created_at);
  const model = str5(conversation.model);
  const events = [];
  const unknownKinds = nameRecord();
  for (const raw of messages) {
    const message = obj5(raw);
    const sender = message === null ? null : str5(message.sender);
    if (message === null || sender === null) {
      unknownKinds["(message)"] = (unknownKinds["(message)"] ?? 0) + 1;
      continue;
    }
    const atMs = isoToMs(message.created_at) ?? fallbackMs;
    if (sender === "human") events.push({ kind: "request", atMs, model: null });
    else if (sender === "assistant") events.push({ kind: "response", atMs, model });
    else unknownKinds[`sender:${sender}`] = (unknownKinds[`sender:${sender}`] ?? 0) + 1;
  }
  return { id, events, unknownKinds };
}
var looksLikeClaude = (value) => {
  const conversation = obj5(value);
  return conversation !== null && str5(conversation.uuid) !== null && Array.isArray(conversation.chat_messages);
};

// src/adapters/web/conversation.ts
var conversationKey = (tool, id) => `${tool}:${fnv1a64(id)}`;
function webSummary(tool, conversation, timeZone, keepFrom) {
  const days = {};
  let firstDate = null;
  let undated = 0;
  for (const event of conversation.events) {
    if (event.atMs === null) {
      undated++;
      continue;
    }
    const date = localDateOf(event.atMs, timeZone);
    if (firstDate === null || date < firstDate) firstDate = date;
    if (keepFrom !== null && date < keepFrom) continue;
    const day = days[date] ??= emptyDay();
    if (event.kind === "request") day.humanRequests++;
    else {
      day.responses++;
      if (event.model !== null) day.models[event.model] = (Object.hasOwn(day.models, event.model) ? day.models[event.model] : 0) + 1;
    }
  }
  const sorted = {};
  for (const date of Object.keys(days).sort()) sorted[date] = canonicalDay(days[date]);
  const unconfirmedTypes = nameRecord();
  for (const kind of Object.keys(conversation.unknownKinds).sort()) unconfirmedTypes[kind] = conversation.unknownKinds[kind];
  return {
    tool,
    sessionId: conversationKey(tool, conversation.id),
    kind: "main",
    parentSessionId: null,
    cwd: null,
    version: null,
    firstDate,
    days: sorted,
    instructionChars: null,
    initialSkills: null,
    initialMcpServers: null,
    missing: { lines: conversation.events.length, brokenLines: 0, tailFragments: 0, tooLongLines: 0, unconfirmedTypes },
    firstResponseIdHashes: [],
    notes: { syntheticResponses: 0, responsesWithoutId: 0, undatedLines: undated, unknownHookKinds: nameRecord() }
  };
}

// src/adapters/web/json-array.ts
var OPEN_BRACE = 123;
var CLOSE_BRACE = 125;
var OPEN_BRACKET = 91;
var CLOSE_BRACKET = 93;
var QUOTE = 34;
var BACKSLASH2 = 92;
var COMMA = 44;
var isSpace = (byte) => byte === 32 || byte === 9 || byte === 10 || byte === 13;
var JsonArraySplitter = class {
  constructor(sink, maxElementBytes) {
    this.sink = sink;
    this.maxElementBytes = maxElementBytes;
  }
  sink;
  maxElementBytes;
  state = "start";
  depth = 0;
  inString = false;
  escaped = false;
  /** 원소가 괄호 없는 값(수, 문자열, 참거짓)이다 */
  bare = false;
  parts = [];
  size = 0;
  dropped = false;
  bom = 0;
  push(chunk) {
    let index = 0;
    while (this.state === "start" && this.bom < 3 && index < chunk.length && chunk[index] === [239, 187, 191][this.bom]) {
      this.bom++;
      index++;
    }
    let elementStart = -1;
    for (; index < chunk.length; index++) {
      const byte = chunk[index];
      switch (this.state) {
        case "start":
          if (isSpace(byte)) continue;
          if (byte === OPEN_BRACKET) this.state = "between";
          else {
            this.state = "notArray";
            return;
          }
          continue;
        case "between":
          if (isSpace(byte) || byte === COMMA) continue;
          if (byte === CLOSE_BRACKET) {
            this.state = "done";
            return;
          }
          this.state = "element";
          this.depth = 0;
          this.inString = false;
          this.escaped = false;
          this.bare = byte !== OPEN_BRACE && byte !== OPEN_BRACKET;
          this.parts = [];
          this.size = 0;
          this.dropped = false;
          elementStart = index;
          index--;
          continue;
        case "element": {
          if (this.inString) {
            if (this.escaped) this.escaped = false;
            else if (byte === BACKSLASH2) this.escaped = true;
            else if (byte === QUOTE) this.inString = false;
            continue;
          }
          if (byte === QUOTE) {
            this.inString = true;
            continue;
          }
          if (this.bare) {
            if (byte === COMMA || byte === CLOSE_BRACKET || isSpace(byte)) {
              this.finishElement(chunk, elementStart, index);
              elementStart = -1;
              this.state = byte === CLOSE_BRACKET ? "done" : "between";
              if (this.state === "done") return;
            }
            continue;
          }
          if (byte === OPEN_BRACE || byte === OPEN_BRACKET) this.depth++;
          else if (byte === CLOSE_BRACE || byte === CLOSE_BRACKET) {
            this.depth--;
            if (this.depth === 0) {
              this.finishElement(chunk, elementStart, index + 1);
              elementStart = -1;
              this.state = "between";
            }
          }
          continue;
        }
        case "done":
        case "notArray":
          return;
      }
    }
    if (this.state === "element") this.keep(chunk, elementStart === -1 ? 0 : elementStart, chunk.length);
  }
  /** 파일이 끝났다. 닫히지 않은 원소는 내지 않는다 */
  end() {
    return { closed: this.state === "done", notArray: this.state === "notArray" || this.state === "start" };
  }
  keep(chunk, from, to) {
    if (this.dropped || to <= from) return;
    this.size += to - from;
    if (this.size > this.maxElementBytes) {
      this.dropped = true;
      this.parts = [];
      return;
    }
    this.parts.push(Buffer.from(chunk.subarray(from, to)));
  }
  finishElement(chunk, from, to) {
    this.keep(chunk, from === -1 ? 0 : from, to);
    if (this.dropped) this.sink.tooLong();
    else this.sink.element(Buffer.concat(this.parts, this.size).toString("utf8"));
    this.parts = [];
    this.size = 0;
    this.dropped = false;
  }
};

// src/adapters/web/zip.ts
import { createReadStream as createReadStream2 } from "node:fs";
import { open as open5 } from "node:fs/promises";
import { pipeline } from "node:stream";
import * as zlib2 from "node:zlib";
var ZipError = class extends Error {
  constructor(code) {
    super(`zip: ${code}`);
    this.code = code;
  }
  code;
};
var EOCD = 101010256;
var ZIP64_LOCATOR = 117853008;
var ZIP64_EOCD = 101075792;
var CENTRAL = 33639248;
var LOCAL = 67324752;
var TAIL_SEARCH = 22 + 65535;
async function readAt(handle, position, length) {
  const buffer = Buffer.alloc(length);
  let offset = 0;
  while (offset < length) {
    const { bytesRead } = await handle.read(buffer, offset, length - offset, position + offset);
    if (bytesRead === 0) break;
    offset += bytesRead;
  }
  return offset === length ? buffer : buffer.subarray(0, offset);
}
var u64 = (buffer, offset) => {
  const value = buffer.readBigUInt64LE(offset);
  if (value > BigInt(Number.MAX_SAFE_INTEGER)) throw new ZipError("broken-directory");
  return Number(value);
};
async function candidateDirectory(handle, source, eocdAt, record) {
  const disk = record.readUInt16LE(4);
  const directoryDisk = record.readUInt16LE(6);
  if (disk !== 0 || directoryDisk !== 0) return "multi-disk";
  let entries = record.readUInt16LE(10);
  let size = record.readUInt32LE(12);
  let offset = record.readUInt32LE(16);
  const needs64 = entries === 65535 || size === 4294967295 || offset === 4294967295;
  let directoryEnd = eocdAt;
  const locator = eocdAt >= 20 ? await readAt(handle, source.start + eocdAt - 20, 20) : Buffer.alloc(0);
  if (locator.length === 20 && locator.readUInt32LE(0) === ZIP64_LOCATOR) {
    if (locator.readUInt32LE(4) !== 0 || locator.readUInt32LE(16) > 1) return "multi-disk";
    const recordAt = u64(locator, 8);
    if (recordAt + 56 > eocdAt - 20) return null;
    const zip64 = await readAt(handle, source.start + recordAt, 56);
    if (zip64.length < 56 || zip64.readUInt32LE(0) !== ZIP64_EOCD) return null;
    if (zip64.readUInt32LE(16) !== 0 || zip64.readUInt32LE(20) !== 0) return "multi-disk";
    entries = u64(zip64, 32);
    size = u64(zip64, 40);
    offset = u64(zip64, 48);
    directoryEnd = recordAt;
  } else if (needs64) return null;
  if (offset + size !== directoryEnd) return null;
  if (entries === 0) return size === 0 ? { offset, size, entries } : null;
  const head = await readAt(handle, source.start + offset, 4);
  if (head.length < 4 || head.readUInt32LE(0) !== CENTRAL) return null;
  return { offset, size, entries };
}
async function* directoryCandidates(handle, source) {
  const from = Math.max(0, source.size - TAIL_SEARCH);
  const tail = await readAt(handle, source.start + from, source.size - from);
  for (let index = tail.length - 22; index >= 0; index--) {
    if (tail.readUInt32LE(index) !== EOCD || index + 22 + tail.readUInt16LE(index + 20) > tail.length) continue;
    const directory = await candidateDirectory(handle, source, from + index, tail.subarray(index, index + 22));
    if (directory !== null) yield directory;
  }
}
function zip64Values(extra, wanted) {
  if (!wanted.size && !wanted.compressed && !wanted.offset) return {};
  for (let at = 0; at + 4 <= extra.length; ) {
    const id = extra.readUInt16LE(at);
    const length = extra.readUInt16LE(at + 2);
    const body = extra.subarray(at + 4, at + 4 + length);
    if (id === 1) {
      const out = {};
      let cursor = 0;
      const take = () => {
        if (cursor + 8 > body.length) throw new ZipError("broken-directory");
        const value = u64(body, cursor);
        cursor += 8;
        return value;
      };
      if (wanted.size) out.size = take();
      if (wanted.compressed) out.compressed = take();
      if (wanted.offset) out.offset = take();
      return out;
    }
    at += 4 + length;
  }
  throw new ZipError("broken-directory");
}
async function wholeFile(path) {
  const handle = await open5(path, "r");
  try {
    return { path, start: 0, size: (await handle.stat()).size };
  } finally {
    await handle.close();
  }
}
async function readDirectory(handle, source, directory) {
  const data = await readAt(handle, source.start + directory.offset, directory.size);
  if (data.length !== directory.size) throw new ZipError("truncated");
  const entries = [];
  let at = 0;
  for (let count = 0; count < directory.entries; count++) {
    if (at + 46 > data.length || data.readUInt32LE(at) !== CENTRAL) throw new ZipError("broken-directory");
    const flags = data.readUInt16LE(at + 8);
    const method = data.readUInt16LE(at + 10);
    const crc322 = data.readUInt32LE(at + 16);
    let compressedSize = data.readUInt32LE(at + 20);
    let size = data.readUInt32LE(at + 24);
    const nameLength = data.readUInt16LE(at + 28);
    const extraLength = data.readUInt16LE(at + 30);
    const commentLength = data.readUInt16LE(at + 32);
    let localOffset = data.readUInt32LE(at + 42);
    const nameStart = at + 46;
    const extraStart = nameStart + nameLength;
    const next = extraStart + extraLength + commentLength;
    if (next > data.length) throw new ZipError("broken-directory");
    const name = data.subarray(nameStart, extraStart).toString((flags & 2048) !== 0 ? "utf8" : "latin1");
    const big = zip64Values(data.subarray(extraStart, extraStart + extraLength), { size: size === 4294967295, compressed: compressedSize === 4294967295, offset: localOffset === 4294967295 });
    if (big.size !== void 0) size = big.size;
    if (big.compressed !== void 0) compressedSize = big.compressed;
    if (big.offset !== void 0) localOffset = big.offset;
    entries.push({ name, method, compressedSize, size, crc32: crc322, localOffset, encrypted: (flags & 1) !== 0 });
    at = next;
  }
  if (at !== data.length) throw new ZipError("broken-directory");
  return entries;
}
async function zipEntries(source) {
  const handle = await open5(source.path, "r");
  try {
    let found = false;
    let multiDisk = false;
    let failure6 = null;
    for await (const directory of directoryCandidates(handle, source)) {
      found = true;
      if (directory === "multi-disk") {
        multiDisk = true;
        continue;
      }
      try {
        return await readDirectory(handle, source, directory);
      } catch (error) {
        if (!(error instanceof ZipError)) throw error;
        failure6 ??= error;
      }
    }
    if (multiDisk) throw new ZipError("multi-disk");
    if (failure6 !== null) throw failure6;
    throw new ZipError(found ? "broken-directory" : await hasEndRecord(handle, source) ? "broken-directory" : "not-zip");
  } finally {
    await handle.close();
  }
}
async function hasEndRecord(handle, source) {
  const from = Math.max(0, source.size - TAIL_SEARCH);
  const tail = await readAt(handle, source.start + from, source.size - from);
  for (let index = tail.length - 22; index >= 0; index--) if (tail.readUInt32LE(index) === EOCD && index + 22 + tail.readUInt16LE(index + 20) <= tail.length) return true;
  return false;
}
async function dataStartOf(source, entry) {
  const handle = await open5(source.path, "r");
  try {
    const header2 = await readAt(handle, source.start + entry.localOffset, 30);
    if (header2.length < 30 || header2.readUInt32LE(0) !== LOCAL) throw new ZipError("broken-directory");
    const start = entry.localOffset + 30 + header2.readUInt16LE(26) + header2.readUInt16LE(28);
    if (start + entry.compressedSize > source.size) throw new ZipError("truncated");
    return source.start + start;
  } finally {
    await handle.close();
  }
}
async function storedSource(source, entry) {
  if (entry.method !== 0 || entry.encrypted || entry.compressedSize !== entry.size) return null;
  return { path: source.path, start: await dataStartOf(source, entry), size: entry.size };
}
async function* zipEntryChunks(source, entry) {
  if (entry.encrypted) throw new ZipError("encrypted");
  if (entry.method !== 0 && entry.method !== 8) throw new ZipError("method");
  const dataStart = await dataStartOf(source, entry);
  if (entry.compressedSize === 0) {
    if (entry.size !== 0) throw new ZipError("truncated");
    return;
  }
  const input = createReadStream2(source.path, { start: dataStart, end: dataStart + entry.compressedSize - 1 });
  const output = entry.method === 0 ? input : pipeline(input, zlib2.createInflateRaw(), () => {
  });
  const crc = typeof zlib2.crc32 === "function" ? zlib2.crc32 : null;
  let produced = 0;
  let check = 0;
  try {
    for await (const chunk of output) {
      produced += chunk.length;
      if (produced > entry.size) throw new ZipError("truncated");
      if (crc !== null) check = crc(chunk, check);
      yield chunk;
    }
  } catch (error) {
    if (error instanceof ZipError) throw error;
    throw new ZipError("truncated");
  } finally {
    input.destroy();
    if (output !== input) output.destroy();
  }
  if (produced !== entry.size) throw new ZipError("truncated");
  if (crc !== null && check >>> 0 !== entry.crc32) throw new ZipError("crc");
}

// src/adapters/web/source.ts
var MAX_CONVERSATION_BYTES = 64 * 1024 * 1024;
var CONVERSATION_FILE = /^conversations(?:-\d+)?\.json$/i;
var CONVERSATION_ZIP = /^conversations.*\.zip$/i;
var ExportError = class extends Error {
  constructor(problem) {
    super(`web export: ${problem}`);
    this.problem = problem;
  }
  problem;
};
function consume(collector, text, timeZone, keepFrom) {
  let value;
  try {
    value = JSON.parse(text);
  } catch {
    collector.skipped.broken++;
    return;
  }
  if (collector.tool === null) {
    if (looksLikeChatgpt(value)) collector.tool = "web-chatgpt";
    else if (looksLikeClaude(value)) collector.tool = "web-claude";
  }
  const conversation = collector.tool === "web-chatgpt" ? chatgptConversation(value) : collector.tool === "web-claude" ? claudeConversation(value) : null;
  if (conversation === null || collector.tool === null) {
    collector.skipped.unrecognized++;
    return;
  }
  const key = conversationKey(collector.tool, conversation.id);
  if (collector.seen.has(key)) return;
  collector.seen.add(key);
  for (const event of conversation.events) {
    if (event.kind === "request") collector.totals.requests++;
    else collector.totals.responses++;
    if (event.atMs === null) continue;
    if (collector.totals.firstMs === null || event.atMs < collector.totals.firstMs) collector.totals.firstMs = event.atMs;
    if (collector.totals.lastMs === null || event.atMs > collector.totals.lastMs) collector.totals.lastMs = event.atMs;
  }
  collector.summaries.push(webSummary(collector.tool, conversation, timeZone, keepFrom));
}
async function readArray(name, chunks, collector, timeZone, keepFrom) {
  const splitter = new JsonArraySplitter({ element: (text) => consume(collector, text, timeZone, keepFrom), tooLong: () => collector.skipped.tooLong++ }, MAX_CONVERSATION_BYTES);
  for await (const chunk of chunks) {
    collector.bytesRead += chunk.length;
    splitter.push(chunk);
  }
  const end = splitter.end();
  if (end.notArray) throw new ExportError("not-array");
  collector.files.push(name);
  if (!end.closed) collector.complete = false;
}
var byName = (a, b) => a.name < b.name ? -1 : a.name > b.name ? 1 : 0;
var baseName2 = (name) => basename3(name.replaceAll("\\", "/"));
async function readZip(source, prefix, collector, timeZone, keepFrom) {
  const entries = await zipEntries(source);
  const files = entries.filter((entry) => CONVERSATION_FILE.test(baseName2(entry.name))).sort(byName);
  for (const entry of files) await readArray(prefix + entry.name, zipEntryChunks(source, entry), collector, timeZone, keepFrom);
  if (files.length > 0 || prefix !== "") return files.length;
  let count = 0;
  for (const entry of entries.filter((item2) => CONVERSATION_ZIP.test(baseName2(item2.name))).sort(byName)) {
    const inner = await storedSource(source, entry);
    if (inner !== null) {
      count += await readZip(inner, `${entry.name}/`, collector, timeZone, keepFrom);
      continue;
    }
    const dir = await mkdtemp(join17(tmpdir(), "aq-web-"));
    try {
      const path = join17(dir, "inner.zip");
      const handle = await open6(path, "w");
      try {
        for await (const chunk of zipEntryChunks(source, entry)) await handle.write(chunk);
      } finally {
        await handle.close();
      }
      count += await readZip(await wholeFile(path), `${entry.name}/`, collector, timeZone, keepFrom);
    } finally {
      await rm5(dir, { recursive: true, force: true });
    }
  }
  return count;
}
var FOLDER_DEPTH = 2;
var FOLDER_ENTRY_LIMIT = 2e4;
async function exportFolderFiles(dir, limit = FOLDER_ENTRY_LIMIT) {
  const found = [];
  let seen = 0;
  let limited = false;
  const walk = async (path, rel, depth) => {
    const entries = await readdir7(path, { withFileTypes: true });
    for (const entry of entries.sort((a, b) => a.name < b.name ? -1 : a.name > b.name ? 1 : 0)) {
      if (limited) return;
      if (++seen > limit) {
        limited = true;
        return;
      }
      const childRel = rel === "" ? entry.name : `${rel}/${entry.name}`;
      const child = join17(path, entry.name);
      if (entry.isDirectory()) {
        if (depth < FOLDER_DEPTH) await walk(child, childRel, depth + 1);
        continue;
      }
      if (!entry.isFile()) continue;
      const zip = CONVERSATION_ZIP.test(entry.name);
      if (!zip && !CONVERSATION_FILE.test(entry.name)) continue;
      const info = await stat6(child);
      found.push({ rel: childRel, path: child, size: info.size, mtimeMs: info.mtimeMs, zip });
    }
  };
  await walk(dir, "", 0);
  return { files: found.sort((a, b) => a.rel < b.rel ? -1 : a.rel > b.rel ? 1 : 0), limited };
}
var isZip = async (path) => {
  const handle = await open6(path, "r");
  try {
    const head = Buffer.alloc(4);
    const { bytesRead } = await handle.read(head, 0, 4, 0);
    return bytesRead === 4 && head.readUInt32LE(0) === 67324752;
  } finally {
    await handle.close();
  }
};
async function readExport(path, timeZone, keepFrom, folderLimit = FOLDER_ENTRY_LIMIT) {
  const info = await stat6(path);
  if (!info.isFile() && !info.isDirectory()) throw new ExportError("not-file");
  const collector = { tool: null, summaries: [], seen: /* @__PURE__ */ new Set(), skipped: { tooLong: 0, broken: 0, unrecognized: 0 }, totals: { requests: 0, responses: 0, firstMs: null, lastMs: null }, files: [], bytesRead: 0, complete: true };
  try {
    if (info.isDirectory()) {
      const { files, limited } = await exportFolderFiles(path, folderLimit);
      if (files.length === 0) throw new ExportError(limited ? "folder-too-large" : "no-conversations");
      if (limited) collector.complete = false;
      for (const file of files) {
        if (file.zip) await readZip(await wholeFile(file.path), `${file.rel}/`, collector, timeZone, keepFrom);
        else await readArray(file.rel, createReadStream3(file.path), collector, timeZone, keepFrom);
      }
    } else if (await isZip(path)) {
      if (await readZip(await wholeFile(path), "", collector, timeZone, keepFrom) === 0) throw new ExportError("no-conversations");
    } else await readArray(basename3(path), createReadStream3(path), collector, timeZone, keepFrom);
  } catch (error) {
    if (error instanceof ZipError) throw new ExportError(`zip-${error.code}`);
    throw error;
  }
  if (collector.tool === null) throw new ExportError("unknown-service");
  return { tool: collector.tool, summaries: collector.summaries, skipped: collector.skipped, files: collector.files, bytesRead: collector.bytesRead, totals: collector.totals, complete: collector.complete };
}

// src/collect/web.ts
var WEB_PARSER_VERSION = 2;
var WEB_PARSER_ID = `web@${WEB_PARSER_VERSION}`;
var emptyRead = () => ({ files: 0, listedBytes: 0, bytes: 0, fromCache: 0, inProgress: 0, olderThanWindow: 0, unreadableFiles: [], unreadableFileBytes: 0, unknownSizeFiles: 0, unreadableDirs: [] });
var DATE3 = /^\d{4}-\d{2}-\d{2}$/;
async function loadWebCached(dir, key, keepFrom, tool) {
  try {
    const entry = JSON.parse(await readFile8(entryPath(dir, key.normPath), "utf8"));
    if (entry.key === void 0 || !sameKey(entry.key, key) || typeof entry.keptFrom !== "string" || !DATE3.test(entry.keptFrom) || entry.keptFrom > keepFrom) return null;
    if (!Array.isArray(entry.summaries) || typeof entry.skipped !== "number" || !Number.isSafeInteger(entry.skipped) || entry.skipped < 0 || typeof entry.complete !== "boolean") return null;
    if (entry.lastMs !== null && (typeof entry.lastMs !== "number" || !Number.isFinite(entry.lastMs))) return null;
    const summaries = [];
    for (const value of entry.summaries) {
      const summary = reviveSummary(value);
      if (summary === null || summary.tool !== tool) return null;
      summaries.push(summary);
    }
    return { key: entry.key, keptFrom: entry.keptFrom, summaries, skipped: entry.skipped, complete: entry.complete, lastMs: entry.lastMs ?? null };
  } catch {
    return null;
  }
}
async function storeWebCached(dir, entry) {
  await mkdir7(dir, { recursive: true });
  const target = entryPath(dir, entry.key.normPath);
  const temporary = `${target}.${process.pid}.tmp`;
  await writeFile6(temporary, JSON.stringify(entry));
  await rename6(temporary, target);
}
var sha2562 = (text) => createHash4("sha256").update(text).digest("hex");
async function readFull(handle, buffer, position) {
  for (let offset = 0; offset < buffer.length; ) {
    const { bytesRead } = await handle.read(buffer, offset, buffer.length - offset, position + offset);
    if (bytesRead === 0) return false;
    offset += bytesRead;
  }
  return true;
}
async function edges(path, size) {
  const handle = await open7(path, "r");
  try {
    const length = Math.min(4096, size);
    const head = Buffer.alloc(length);
    const tail = Buffer.alloc(length);
    if (!await readFull(handle, head, 0) || !await readFull(handle, tail, size - length)) return null;
    return createHash4("sha256").update(head).update(tail).digest("hex");
  } finally {
    await handle.close();
  }
}
async function exportKey(path, timeZone) {
  const info = await stat7(path);
  if (info.isFile()) return cacheKeyFor({ path, normPath: normalizePath(path), size: info.size, mtimeMs: info.mtimeMs }, WEB_PARSER_ID, timeZone);
  if (!info.isDirectory()) return null;
  const { files, limited } = await exportFolderFiles(path);
  const lines = [];
  for (const file of files) {
    const fingerprint = await edges(file.path, file.size);
    if (fingerprint === null) return null;
    lines.push(`${file.rel}|${file.size}|${file.mtimeMs}|${fingerprint}`);
  }
  const list = `${limited ? "limited" : "all"}
${lines.join("\n")}`;
  return {
    normPath: normalizePath(path),
    size: files.reduce((sum2, file) => sum2 + file.size, 0),
    mtimeMs: files.reduce((latest, file) => Math.max(latest, file.mtimeMs), 0),
    head: sha2562(list),
    tail: sha2562(`folder:${files.length}`),
    cacheFormat: CACHE_FORMAT_VERSION,
    parser: WEB_PARSER_ID,
    timeZone
  };
}
async function collectOne(tool, entry, options) {
  const windows = makeWindows(options.clock.nowMs, options.clock.timeZone);
  const keepFrom = windows.collectDates[0];
  const state = { path: entry?.path ?? null, missing: false, problem: null, skipped: 0, truncated: false, lastDate: null };
  const read = emptyRead();
  const result = (summaries) => ({ tool, detected: entry !== void 0, summaries, read, visibleFrom: visibleFrom(summaries, 0, keepFrom), state });
  if (entry === void 0) return result([]);
  let info;
  try {
    info = await stat7(entry.path);
  } catch (error) {
    if (error.code === "ENOENT") state.missing = true;
    else {
      state.problem = "unreadable";
      read.files = 1;
      read.unreadableFiles = [entry.path];
      read.unknownSizeFiles = 1;
    }
    return result([]);
  }
  read.files = 1;
  read.listedBytes = info.isFile() ? info.size : 0;
  const isFolder = info.isDirectory();
  const fail = (problem) => {
    state.problem = problem;
    read.unreadableFiles = [entry.path];
    read.unreadableFileBytes = read.listedBytes;
    return result([]);
  };
  if (!info.isFile() && !isFolder) return fail("not-file");
  const cacheDir = options.cacheDir === null ? null : join18(options.cacheDir, "web");
  let key = null;
  try {
    if (cacheDir !== null || isFolder) key = await exportKey(entry.path, options.clock.timeZone);
    if (isFolder && key !== null) read.listedBytes = key.size;
    if (cacheDir !== null) {
      const hit = key === null || options.rescan ? null : await loadWebCached(cacheDir, key, keepFrom, tool);
      if (hit !== null) {
        read.bytes = read.listedBytes;
        read.fromCache = 1;
        state.skipped = hit.skipped;
        state.truncated = !hit.complete;
        state.lastDate = hit.lastMs === null ? null : localDateOf(hit.lastMs, options.clock.timeZone);
        return result(hit.summaries);
      }
    }
  } catch {
    key = null;
  }
  let exported;
  try {
    exported = await readExport(entry.path, options.clock.timeZone, keepFrom);
  } catch (error) {
    return fail(error instanceof ExportError ? error.problem : "unreadable");
  }
  if (exported.tool !== tool) return fail("unknown-service");
  read.bytes = read.listedBytes;
  state.skipped = exported.skipped.tooLong + exported.skipped.broken + exported.skipped.unrecognized;
  state.truncated = !exported.complete;
  state.lastDate = exported.totals.lastMs === null ? null : localDateOf(exported.totals.lastMs, options.clock.timeZone);
  if (options.cacheDir !== null) await primeWebCache(options.cacheDir, entry.path, key, exported, keepFrom, options.clock.timeZone);
  return result(exported.summaries);
}
async function primeWebCache(cacheRoot, path, before, exported, keepFrom, timeZone) {
  try {
    if (before === null) return;
    const key = await exportKey(path, timeZone);
    if (key === null || !sameKey(key, before)) return;
    const skipped = exported.skipped.tooLong + exported.skipped.broken + exported.skipped.unrecognized;
    await storeWebCached(join18(cacheRoot, "web"), { key, keptFrom: keepFrom, summaries: exported.summaries, skipped, complete: exported.complete, lastMs: exported.totals.lastMs });
  } catch {
  }
}
async function collectWeb(entries, options) {
  const out = [];
  for (const tool of WEB_TOOLS) out.push(await collectOne(tool, entries.find((entry) => entry.tool === tool), options));
  return out;
}

// src/scan/claude.ts
import { basename as basename7, join as join25, relative as relative3 } from "node:path";

// src/scan/claude-json.ts
import { join as join20, resolve as resolve5 } from "node:path";

// src/scan/fs.ts
import { lstat as lstat4, readdir as readdir8, readFile as readFile9, realpath as realpath4, stat as stat8 } from "node:fs/promises";
var isMissing6 = (error) => {
  const code = error?.code;
  return code === "ENOENT" || code === "ENOTDIR";
};
var stripBom = (text) => text.charCodeAt(0) === 65279 ? text.slice(1) : text;
async function readText(path) {
  try {
    return { status: "ok", text: stripBom(await readFile9(path, "utf8")) };
  } catch (error) {
    return isMissing6(error) ? { status: "missing" } : { status: "unreadable" };
  }
}
async function readJson(path) {
  const text = await readText(path);
  if (text.status !== "ok") return text;
  try {
    return { status: "ok", value: JSON.parse(text.text) };
  } catch {
    return { status: "unparsable" };
  }
}
async function listDir(path) {
  try {
    return { status: "ok", names: (await readdir8(path)).sort() };
  } catch (error) {
    return isMissing6(error) ? { status: "missing" } : { status: "unreadable" };
  }
}
function createdMsOf(info) {
  const ms = info.birthtimeMs;
  return Number.isFinite(ms) && ms > 0 ? ms : null;
}
var MISSING = { exists: false, isLink: false, isDir: false, isFile: false, createdMs: null, targetCreatedMs: null, dangling: false, realPath: null };
async function entryInfo(path) {
  let own;
  try {
    own = await lstat4(path);
  } catch {
    return MISSING;
  }
  const isLink = own.isSymbolicLink();
  let target = own;
  if (isLink) {
    try {
      target = await stat8(path);
    } catch {
      target = null;
    }
  }
  let real = null;
  try {
    real = normalizePath(await realpath4(path));
  } catch {
    real = null;
  }
  return {
    exists: true,
    isLink,
    isDir: target?.isDirectory() ?? false,
    isFile: target?.isFile() ?? false,
    createdMs: createdMsOf(own),
    targetCreatedMs: isLink && target !== null ? createdMsOf(target) : null,
    dangling: isLink && target === null,
    realPath: real
  };
}

// src/scan/plugins.ts
import { basename as basename4, join as join19, resolve as resolve4 } from "node:path";

// src/scan/hooks.ts
var SHELL_TOOLS2 = ["Bash", "PowerShell"];
var isObject4 = (v) => v !== null && typeof v === "object" && !Array.isArray(v);
function matcherMatches(matcher, tool) {
  if (matcher === void 0 || matcher === null || matcher === "" || matcher === "*") return true;
  if (typeof matcher !== "string") return false;
  if (/^[A-Za-z0-9_\- ,|]+$/.test(matcher)) {
    return matcher.split(/[|,]/).map((name) => name.trim()).includes(tool);
  }
  try {
    return new RegExp(matcher).test(tool);
  } catch {
    return false;
  }
}
function ifTool(rule2) {
  if (rule2 === void 0) return null;
  if (typeof rule2 !== "string") return "unreadable";
  const match = /^\s*([A-Za-z0-9_]+)\s*(?:\(.*\))?\s*$/s.exec(rule2);
  return match === null ? "unreadable" : match[1];
}
function coversShell(matcher, rule2) {
  const tool = ifTool(rule2);
  if (tool === "unreadable") return false;
  return SHELL_TOOLS2.some((shell) => matcherMatches(matcher, shell) && (tool === null || tool === shell));
}
var REQUIRED_FIELDS = /* @__PURE__ */ new Map([
  ["command", ["command"]],
  ["http", ["url"]],
  ["mcp_tool", ["server", "tool"]],
  ["prompt", ["prompt"]],
  ["agent", ["prompt"]]
]);
function isHandler(handler) {
  if (!isObject4(handler) || typeof handler.type !== "string") return false;
  const required = REQUIRED_FIELDS.get(handler.type);
  return required !== void 0 && required.every((field) => typeof handler[field] === "string" && handler[field] !== "");
}
function hookMapValid(events) {
  if (!isObject4(events)) return false;
  for (const groups of Object.values(events)) {
    if (!Array.isArray(groups)) return false;
    for (const group of groups) if (!isObject4(group) || !Array.isArray(group.hooks) || !group.hooks.every(isHandler)) return false;
  }
  return true;
}
function hookFileEvents(file) {
  return isObject4(file) && hookMapValid(file.hooks) ? file.hooks : null;
}
function inlineHookEvents(inline) {
  return hookMapValid(inline) ? inline : null;
}
function preToolUseGuards(events, source, pluginId) {
  if (!isObject4(events) || !Array.isArray(events.PreToolUse)) return [];
  const out = [];
  for (const group of events.PreToolUse) {
    if (!isObject4(group) || !Array.isArray(group.hooks)) continue;
    for (const handler of group.hooks) {
      if (!isHandler(handler)) continue;
      out.push({ source, pluginId, coversShell: coversShell(group.matcher, handler.if), canBlock: handler.async !== true && handler.asyncRewake !== true });
    }
  }
  return out;
}
function hookCommandTexts(events) {
  if (!isObject4(events)) return [];
  const out = [];
  for (const groups of Object.values(events)) {
    if (!Array.isArray(groups)) continue;
    for (const group of groups) {
      if (!isObject4(group) || !Array.isArray(group.hooks)) continue;
      for (const handler of group.hooks) {
        if (!isObject4(handler)) continue;
        const parts = [];
        if (typeof handler.command === "string") parts.push(handler.command);
        if (Array.isArray(handler.args)) {
          for (const arg of handler.args) if (typeof arg === "string") parts.push(arg);
        }
        if (parts.length > 0) out.push(parts.join(" "));
      }
    }
  }
  return out;
}

// src/scan/json.ts
var MAX_JSON_DEPTH = 64;
var isObject5 = (v) => v !== null && typeof v === "object" && !Array.isArray(v);
function canonicalJson(value, depth = 0) {
  if (depth > MAX_JSON_DEPTH) return null;
  if (Array.isArray(value)) {
    const parts = [];
    for (const item2 of value) {
      const part = canonicalJson(item2, depth + 1);
      if (part === null) return null;
      parts.push(part);
    }
    return `[${parts.join(",")}]`;
  }
  if (isObject5(value)) {
    const parts = [];
    for (const key of Object.keys(value).sort()) {
      const part = canonicalJson(value[key], depth + 1);
      if (part === null) return null;
      parts.push(`${JSON.stringify(key)}:${part}`);
    }
    return `{${parts.join(",")}}`;
  }
  return JSON.stringify(value) ?? "null";
}

// src/scan/plugins.ts
var DEFAULT_ENTRIES = {
  skills: "skills",
  commands: "commands",
  agents: "agents",
  workflows: "workflows",
  "output-styles": "outputStyles",
  themes: "themes",
  monitors: "monitors",
  hooks: "hooks",
  bin: "bin",
  "settings.json": "settings",
  ".mcp.json": "mcpServers",
  ".lsp.json": "lspServers"
};
var MANIFEST_COMPONENTS = [
  ["skills", "skills"],
  ["commands", "commands"],
  ["agents", "agents"],
  ["workflows", "workflows"],
  ["outputStyles", "outputStyles"],
  ["hooks", "hooks"],
  ["mcpServers", "mcpServers"],
  ["lspServers", "lspServers"],
  ["userConfig", "userConfig"],
  ["channels", "channels"]
];
var COMPONENT_KEYS = new Set(MANIFEST_COMPONENTS.map(([key]) => key));
var ENTRY_APPENDED = /* @__PURE__ */ new Set(["commands", "agents", "skills", "hooks", "outputStyles", "themes"]);
var INTRO_FILES = /^(readme|license|changelog)|^package\.json$/i;
var HELPER_DIRS = /* @__PURE__ */ new Set(["docs", "tests", "test", "examples", "assets", "images", "scripts"]);
var MARKET_ROOT_SOURCES = /* @__PURE__ */ new Set([".", "./"]);
var URL_LIKE = /^[a-z][a-z0-9+.-]*:\/\//i;
var wellFormedPath = (path) => path.startsWith("./") && !path.split(/[\\/]/).includes("..");
function declarationsOf(value) {
  if (value === void 0) return [];
  const items = Array.isArray(value) ? value : [value];
  return items.map((item2) => typeof item2 === "string" ? item2 : isObject5(item2) ? item2 : null);
}
var SKILLS_DIR = "skills-dir";
async function isIntroEntry(root, name) {
  const lower = name.toLowerCase();
  const info = await entryInfo(join19(root, name));
  if (info.isFile) return INTRO_FILES.test(name) || lower.endsWith(".md") && lower !== "skill.md";
  if (info.isDir) return HELPER_DIRS.has(lower);
  return false;
}
var INTRO_KEYS = /* @__PURE__ */ new Set(["$schema", "name", "displayName", "version", "description", "author", "homepage", "repository", "license", "keywords", "metadata", "defaultEnabled", "dependencies"]);
var ENTRY_INTRO_KEYS = /* @__PURE__ */ new Set([...INTRO_KEYS, "source", "category", "tags", "strict", "relevance", "headers", "headersHelper"]);
var pathsOf = (v) => typeof v === "string" ? [v] : Array.isArray(v) ? v.filter((x) => typeof x === "string") : [];
var firstSegment = (path) => path.replace(/\\/g, "/").replace(/^\.\//, "").split("/")[0] ?? "";
var bareName = (name) => name.includes("@") ? name.slice(0, name.indexOf("@")) : name;
var cmp = (a, b) => a < b ? -1 : a > b ? 1 : 0;
function mcpMapOf(value) {
  if (!isObject5(value)) return null;
  let map = value;
  if (Object.hasOwn(value, "mcpServers")) {
    if (!isObject5(value.mcpServers)) return null;
    map = value.mcpServers;
  }
  return Object.keys(map).sort().map((name) => ({ name, definition: isObject5(map[name]) ? map[name] : null }));
}
async function readMarketplaceEntries(claudeHome2) {
  const markets = /* @__PURE__ */ new Map();
  const known2 = await readJson(join19(claudeHome2, "plugins", "known_marketplaces.json"));
  if (known2.status === "missing") return { file: "missing", markets };
  if (known2.status !== "ok" || !isObject5(known2.value)) return { file: "unreadable", markets };
  for (const [market, info] of Object.entries(known2.value)) {
    if (!isObject5(info) || typeof info.installLocation !== "string") {
      markets.set(market, "unreadable");
      continue;
    }
    const location = info.installLocation;
    const read = await readJson((await entryInfo(location)).isFile ? location : join19(location, ".claude-plugin", "marketplace.json"));
    if (read.status === "missing") {
      markets.set(market, "missing");
      continue;
    }
    if (read.status !== "ok" || !isObject5(read.value) || !Array.isArray(read.value.plugins)) {
      markets.set(market, "unreadable");
      continue;
    }
    const entries = /* @__PURE__ */ new Map();
    for (const entry of read.value.plugins) if (isObject5(entry) && typeof entry.name === "string" && !entries.has(entry.name)) entries.set(entry.name, entry);
    markets.set(market, entries);
  }
  return { file: "ok", markets };
}
function mergeEvents(base, replace) {
  const merged = /* @__PURE__ */ Object.create(null);
  for (const events of base) {
    if (!isObject5(events)) continue;
    for (const [event, groups] of Object.entries(events)) if (Array.isArray(groups)) merged[event] = [...merged[event] ?? [], ...groups];
  }
  if (isObject5(replace)) {
    for (const [event, groups] of Object.entries(replace)) if (Array.isArray(groups)) merged[event] = [...groups];
  }
  return merged;
}
async function readPluginInstall(group, markets) {
  const { id, installPath } = group;
  const at = id.lastIndexOf("@");
  const entryName = at === -1 ? id : id.slice(0, at);
  const marketplace = at === -1 ? "" : id.slice(at + 1);
  const plugin = {
    id,
    entryName,
    marketplace,
    name: entryName,
    scopes: [...group.scopes].sort(),
    projectPaths: [...group.projectPaths].sort(),
    installPath,
    installRealPath: null,
    exists: false,
    manifest: "missing",
    marketplaceEntry: "missing",
    defaultEnabled: true,
    components: [],
    unknownEntries: [],
    dependencies: null,
    compositionKnown: false,
    hookEvents: [],
    hooksUnreadable: false,
    mcpServers: [],
    mcpUnreadable: false,
    skillRoots: []
  };
  const unknown = () => {
    plugin.hooksUnreadable = true;
    plugin.mcpUnreadable = true;
    return plugin;
  };
  const market = markets.markets.get(marketplace);
  const fromSkillsDir = marketplace === SKILLS_DIR;
  const entry = fromSkillsDir ? {} : market instanceof Map ? market.get(entryName) : void 0;
  const marketUnreadable = market === "unreadable" || market === void 0 && markets.file === "unreadable";
  plugin.marketplaceEntry = fromSkillsDir ? "none" : entry !== void 0 ? "ok" : marketUnreadable ? "unreadable" : "missing";
  const installInfo = await entryInfo(installPath);
  plugin.exists = installInfo.isDir;
  if (!plugin.exists) return unknown();
  plugin.installRealPath = installInfo.realPath;
  const listing = await listDir(installPath);
  const manifestRead = await readJson(join19(installPath, ".claude-plugin", "plugin.json"));
  let manifest = null;
  if (manifestRead.status === "ok" && isObject5(manifestRead.value) && typeof manifestRead.value.name === "string" && manifestRead.value.name !== "") {
    plugin.manifest = "ok";
    manifest = manifestRead.value;
    plugin.name = manifestRead.value.name;
  } else {
    plugin.manifest = manifestRead.status === "ok" ? "unparsable" : manifestRead.status;
  }
  if (entry !== void 0 && typeof entry.defaultEnabled === "boolean") plugin.defaultEnabled = entry.defaultEnabled;
  else if (manifest !== null) plugin.defaultEnabled = manifest.defaultEnabled !== false;
  if (listing.status !== "ok") return unknown();
  if (plugin.manifest === "unparsable" || plugin.manifest === "unreadable") return unknown();
  if (entry === void 0) return unknown();
  if (manifest !== null && entry.strict === false && Object.keys(entry).some((key) => ENTRY_APPENDED.has(key))) return unknown();
  const base = manifest ?? entry;
  const appended = manifest !== null ? Object.fromEntries(Object.entries(entry).filter(([key]) => ENTRY_APPENDED.has(key))) : {};
  plugin.compositionKnown = true;
  const deps = [...Array.isArray(base.dependencies) ? base.dependencies : [], ...manifest !== null && Array.isArray(entry.dependencies) ? entry.dependencies : []];
  plugin.dependencies = [...new Set(deps.flatMap((d) => typeof d === "string" ? [bareName(d)] : isObject5(d) && typeof d.name === "string" ? [bareName(d.name)] : []))].sort();
  const kinds = /* @__PURE__ */ new Set();
  const referenced = /* @__PURE__ */ new Set();
  const addComponents = (source) => {
    for (const [key, kind] of MANIFEST_COMPONENTS) {
      if (source[key] === void 0) continue;
      kinds.add(kind);
      for (const path of pathsOf(source[key])) referenced.add(firstSegment(path));
    }
    const experimental = isObject5(source.experimental) ? source.experimental : {};
    for (const [key, kind] of [["themes", "themes"], ["monitors", "monitors"]]) {
      if (experimental[key] === void 0) continue;
      kinds.add(kind);
      for (const path of pathsOf(experimental[key])) referenced.add(firstSegment(path));
    }
    if (source.themes !== void 0) {
      kinds.add("themes");
      for (const path of pathsOf(source.themes)) referenced.add(firstSegment(path));
    }
  };
  addComponents(base);
  addComponents(appended);
  const prefix = manifest !== null ? "manifest" : "entry";
  const unknownKeys = (source, from, known2) => {
    for (const key of Object.keys(source)) {
      if (key === "experimental") {
        const experimental = isObject5(source.experimental) ? source.experimental : {};
        for (const inner of Object.keys(experimental)) if (inner !== "themes" && inner !== "monitors") plugin.unknownEntries.push(`${from}:experimental.${inner}`);
        continue;
      }
      if (!known2.has(key) && !COMPONENT_KEYS.has(key) && key !== "themes") plugin.unknownEntries.push(`${from}:${key}`);
    }
  };
  if (manifest !== null) unknownKeys(manifest, "manifest", INTRO_KEYS);
  unknownKeys(entry, "entry", ENTRY_INTRO_KEYS);
  for (const name of listing.names) {
    const kind = Object.hasOwn(DEFAULT_ENTRIES, name) ? DEFAULT_ENTRIES[name] : void 0;
    if (kind !== void 0) {
      kinds.add(kind);
      continue;
    }
    if (name.startsWith(".") || referenced.has(name) || await isIntroEntry(installPath, name)) continue;
    plugin.unknownEntries.push(name);
  }
  plugin.components = [...kinds].sort();
  const root = normalizePath(installPath);
  const rootReal = plugin.installRealPath;
  const within = (path, base2) => path === base2 || path.startsWith(base2.endsWith("/") ? base2 : `${base2}/`);
  const insideRoot = async (path) => {
    const real = (await entryInfo(path)).realPath;
    return real === null || rootReal === null || within(real, rootReal);
  };
  const declaredPath = async (declared2) => {
    if (!wellFormedPath(declared2)) return null;
    const path = resolve4(installPath, declared2);
    return await insideRoot(path) ? path : null;
  };
  const hookSources = [];
  const hookFileStatus = /* @__PURE__ */ new Map();
  const addHookFile = async (path, declared2) => {
    const key = normalizePath(path);
    let status = hookFileStatus.get(key);
    if (status === void 0) {
      const read = await readJson(path);
      const events = read.status === "ok" ? hookFileEvents(read.value) : null;
      status = read.status === "missing" ? "missing" : events !== null ? "ok" : "bad";
      hookFileStatus.set(key, status);
      if (events !== null) hookSources.push(events);
    }
    if (status === "missing" ? declared2 : status === "bad") plugin.hooksUnreadable = true;
  };
  const addInlineHooks = (inline) => {
    const events = inlineHookEvents(inline);
    if (events === null) plugin.hooksUnreadable = true;
    else hookSources.push(events);
  };
  const defaultHooks = join19(installPath, "hooks", "hooks.json");
  if (await insideRoot(defaultHooks)) await addHookFile(defaultHooks, false);
  else plugin.hooksUnreadable = true;
  if (manifest !== null) {
    for (const declaration of declarationsOf(manifest.hooks)) {
      if (declaration === null) plugin.hooksUnreadable = true;
      else if (typeof declaration === "string") {
        const path = await declaredPath(declaration);
        if (path !== null) await addHookFile(path, true);
        else plugin.hooksUnreadable = true;
      } else addInlineHooks(declaration);
    }
  }
  const entryHooks = isObject5(entry.hooks) ? inlineHookEvents(entry.hooks) : void 0;
  if (entryHooks === null) plugin.hooksUnreadable = true;
  plugin.hookEvents = [manifest !== null ? mergeEvents(hookSources, entryHooks) : mergeEvents([...hookSources, entryHooks], void 0)];
  const servers = /* @__PURE__ */ new Map();
  const addMap = (entries) => {
    if (entries === null) {
      plugin.mcpUnreadable = true;
      return;
    }
    for (const e of entries) servers.set(e.name, e);
  };
  const addMcpFile = async (path, declared2) => {
    const read = await readJson(path);
    if (read.status === "missing") {
      if (declared2) plugin.mcpUnreadable = true;
      return;
    }
    addMap(read.status === "ok" ? mcpMapOf(read.value) : null);
  };
  await addMcpFile(join19(installPath, ".mcp.json"), false);
  for (const declaration of declarationsOf(base.mcpServers)) {
    if (declaration === null || typeof declaration === "string" && URL_LIKE.test(declaration)) plugin.mcpUnreadable = true;
    else if (typeof declaration === "string") {
      const path = await declaredPath(declaration);
      if (path !== null) await addMcpFile(path, true);
      else plugin.mcpUnreadable = true;
    } else addMap(mcpMapOf({ mcpServers: declaration }));
  }
  plugin.mcpServers = [...servers.values()].sort((a, b) => cmp(a.name, b.name));
  const isPluginRoot = async (path) => {
    if (normalizePath(path) === root) return true;
    const real = (await entryInfo(path)).realPath;
    return real !== null && rootReal !== null && real === rootReal;
  };
  const declared = [...pathsOf(base.skills).map((path) => ({ path, from: prefix })), ...pathsOf(appended.skills).map((path) => ({ path, from: "entry" }))];
  const skillRoots = [];
  for (const { path, from } of declared) {
    if (await isPluginRoot(resolve4(installPath, path))) {
      plugin.unknownEntries.push(`${from}:skills=.`);
      continue;
    }
    const accepted = await declaredPath(path);
    if (accepted === null) plugin.unknownEntries.push(`${from}:skills=..`);
    else skillRoots.push(accepted);
  }
  const defaultSkills = join19(installPath, "skills");
  const defaultIsRoot = await isPluginRoot(defaultSkills);
  if (defaultIsRoot) plugin.unknownEntries.push("skills=.");
  const entrySkillsOnly = entry.skills !== void 0 && typeof entry.source === "string" && MARKET_ROOT_SOURCES.has(entry.source);
  plugin.skillRoots = [.../* @__PURE__ */ new Set([...entrySkillsOnly || defaultIsRoot ? [] : [defaultSkills], ...skillRoots])];
  plugin.unknownEntries = [...new Set(plugin.unknownEntries)].sort();
  return plugin;
}
async function readSkillsDirPlugins(refs) {
  const out = [];
  for (const ref of refs) {
    const read = await readJson(join19(ref.path, ".claude-plugin", "plugin.json"));
    const declared = read.status === "ok" && isObject5(read.value) ? read.value.name : void 0;
    const name = typeof declared === "string" && declared !== "" ? declared : basename4(ref.path);
    const group = { id: `${name}@${SKILLS_DIR}`, installPath: ref.path, scopes: /* @__PURE__ */ new Set([ref.scope]), projectPaths: new Set(ref.projectRoot === null ? [] : [ref.projectRoot]) };
    out.push(await readPluginInstall(group, { file: "ok", markets: /* @__PURE__ */ new Map() }));
  }
  return out;
}
async function scanPlugins(claudeHome2) {
  const read = await readJson(join19(claudeHome2, "plugins", "installed_plugins.json"));
  if (read.status !== "ok") return { file: read.status, plugins: [] };
  if (!isObject5(read.value) || !isObject5(read.value.plugins)) return { file: "unparsable", plugins: [] };
  const groups = /* @__PURE__ */ new Map();
  for (const id of Object.keys(read.value.plugins)) {
    if (id.endsWith("@builtin")) continue;
    const entries = read.value.plugins[id];
    for (const entry of Array.isArray(entries) ? entries : []) {
      if (!isObject5(entry) || typeof entry.installPath !== "string") continue;
      const key = `${id}\0${normalizePath(entry.installPath)}`;
      let group = groups.get(key);
      if (group === void 0) {
        group = { id, installPath: entry.installPath, scopes: /* @__PURE__ */ new Set(), projectPaths: /* @__PURE__ */ new Set() };
        groups.set(key, group);
      }
      if (entry.installPath < group.installPath) group.installPath = entry.installPath;
      group.scopes.add(typeof entry.scope === "string" ? entry.scope : "unknown");
      if (typeof entry.projectPath === "string") group.projectPaths.add(normalizePath(entry.projectPath));
    }
  }
  const markets = await readMarketplaceEntries(claudeHome2);
  const plugins = [];
  for (const key of [...groups.keys()].sort()) plugins.push(await readPluginInstall(groups.get(key), markets));
  return { file: "ok", plugins };
}

// src/scan/claude-json.ts
function claudeJsonPath(env, homedir2) {
  const fromEnv = env.CLAUDE_CONFIG_DIR?.trim();
  return fromEnv ? join20(resolve5(fromEnv), ".claude.json") : join20(homedir2, ".claude.json");
}
var MAX_DATE_MS = 864e13;
var isObject6 = (v) => v !== null && typeof v === "object" && !Array.isArray(v);
var strings2 = (v) => Array.isArray(v) ? v.filter((x) => typeof x === "string") : [];
function isDateMs(v) {
  return typeof v === "number" && Number.isFinite(v) && Math.abs(v) <= MAX_DATE_MS;
}
function lastUsed(v) {
  const out = /* @__PURE__ */ Object.create(null);
  if (!isObject6(v)) return out;
  for (const [name, entry] of Object.entries(v)) {
    out[name] = isObject6(entry) && isDateMs(entry.lastUsedAt) ? entry.lastUsedAt : null;
  }
  return out;
}
function emptyClaudeJson(status) {
  return {
    status,
    userMcpServers: [],
    projects: [],
    skillUsage: /* @__PURE__ */ Object.create(null),
    pluginUsage: /* @__PURE__ */ Object.create(null),
    claudeAiEverConnected: []
  };
}
async function readClaudeJson(path) {
  let read = await readJson(path);
  if (read.status === "unparsable") read = await readJson(path);
  if (read.status !== "ok") return emptyClaudeJson(read.status);
  if (!isObject6(read.value)) return emptyClaudeJson("unparsable");
  const v = read.value;
  const facts = emptyClaudeJson("ok");
  facts.userMcpServers = isObject6(v.mcpServers) ? mcpMapOf({ mcpServers: v.mcpServers }) ?? [] : [];
  if (isObject6(v.projects)) {
    for (const key of Object.keys(v.projects)) {
      const entry = v.projects[key];
      if (!isObject6(entry)) continue;
      facts.projects.push({
        key,
        normKey: normalizePath(key),
        mcpServers: isObject6(entry.mcpServers) ? mcpMapOf({ mcpServers: entry.mcpServers }) ?? [] : [],
        enabledMcpjsonServers: strings2(entry.enabledMcpjsonServers),
        disabledMcpjsonServers: strings2(entry.disabledMcpjsonServers),
        disabledMcpServers: strings2(entry.disabledMcpServers)
      });
    }
    facts.projects.sort((a, b) => a.normKey !== b.normKey ? a.normKey < b.normKey ? -1 : 1 : a.key < b.key ? -1 : 1);
  }
  facts.skillUsage = lastUsed(v.skillUsage);
  facts.pluginUsage = lastUsed(v.pluginUsage);
  facts.claudeAiEverConnected = [...new Set(strings2(v.claudeAiMcpEverConnected))].sort();
  return facts;
}

// src/scan/instructions.ts
import { createHash as createHash5 } from "node:crypto";
import { lstat as lstat5, readlink } from "node:fs/promises";
import { basename as basename5, dirname as dirname3, isAbsolute, join as join21, parse, resolve as resolve6 } from "node:path";
var MIN_LINE_CHARS = 20;
var RULES_MAX_DEPTH = 8;
var MAX_IMPORT_HOPS = 4;
var GEMINI_IMPORT_HOPS = 5;
function emptyInstructionSet() {
  return { files: [], bytes: 0, chars: { ascii: 0, other: 0 }, lineHashes: [], unreadable: [], unreadableDirs: [] };
}
function lineHash(line) {
  return createHash5("sha256").update(line).digest("hex").slice(0, 32);
}
function countChars(text) {
  let ascii = 0;
  let other = 0;
  for (const ch of text) {
    if (ch.codePointAt(0) < 128) ascii++;
    else other++;
  }
  return { ascii, other };
}
function linesForOverlap(text) {
  const out = [];
  for (const raw of text.split("\n")) {
    const line = raw.trim();
    if ([...line].length >= MIN_LINE_CHARS) out.push(lineHash(line));
  }
  return out;
}
async function markdownFilesUnder(dir) {
  const paths = [];
  const unreadableDirs = [];
  const walk = async (current, depth) => {
    const listing = await listDir(current);
    if (listing.status === "unreadable") unreadableDirs.push(current);
    if (listing.status !== "ok") return;
    for (const name of listing.names) {
      const path = join21(current, name);
      let info;
      try {
        info = await lstat5(path);
      } catch {
        continue;
      }
      if (info.isDirectory()) {
        if (depth < RULES_MAX_DEPTH) await walk(path, depth + 1);
        continue;
      }
      if (name.toLowerCase().endsWith(".md") && (info.isFile() || info.isSymbolicLink())) paths.push(path);
    }
  };
  await walk(dir, 0);
  return { paths: paths.sort(), unreadableDirs: unreadableDirs.sort() };
}
var escapeRegExp = (text) => text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
function countMentions(text, targets) {
  const unified = text.replace(/\\/g, "/").toLowerCase();
  const out = /* @__PURE__ */ Object.create(null);
  for (const target of targets) {
    const path = target.normRoot.toLowerCase();
    let count = unified.split(path).length - 1;
    const name = basename5(target.root).toLowerCase();
    if ([...name].length >= 3) {
      const word = new RegExp(`(?<![\\p{L}\\p{N}_])${escapeRegExp(name)}(?![\\p{L}\\p{N}_])`, "gu");
      const withoutPaths = path.length > 0 ? unified.split(path).join(" ") : unified;
      count += (withoutPaths.match(word) ?? []).length;
    }
    if (count > 0) out[target.normRoot] = count;
  }
  return out;
}
function importsOf(text, style = "claude") {
  const prose = [];
  let fence = null;
  for (const raw of text.split("\n")) {
    const body = raw.replace(/^(?:[ \t]*(?:[-*+]|\d{1,9}[.)]|>)(?=[ \t]|$))*[ \t]*/, "");
    const marker2 = /^(`{3,}|~{3,})/.exec(body)?.[1] ?? null;
    if (fence !== null) {
      if (marker2 !== null && marker2[0] === fence[0] && marker2.length >= fence.length && body.slice(marker2.length).trim() === "") fence = null;
      prose.push("");
      continue;
    }
    if (marker2 !== null) {
      fence = marker2;
      prose.push("");
      continue;
    }
    prose.push(raw);
  }
  const cleaned = prose.join("\n").replace(/(`+)(?:(?!\n[ \t]*\n)[\s\S])*?\1/g, " ");
  const out = [];
  if (style === "gemini") {
    const space = (char) => char === " " || char === "	" || char === "\n" || char === "\r";
    let index = 0;
    while (index < cleaned.length) {
      index = cleaned.indexOf("@", index);
      if (index === -1) break;
      if (index > 0 && !space(cleaned[index - 1])) {
        index++;
        continue;
      }
      let end = index + 1;
      while (end < cleaned.length && !space(cleaned[end])) end++;
      const token = cleaned.slice(index + 1, end);
      if (/^[./A-Za-z]/.test(token)) out.push(token);
      index = end + 1;
    }
    return out;
  }
  for (const match of cleaned.matchAll(/(?<!\S)@((?:\\ |\S)+)/g)) {
    const token = match[1].replace(/\\ /g, " ");
    if (token.startsWith('"') || token.startsWith("'")) continue;
    out.push(token);
  }
  return out;
}
var NETWORK_PATH = /^(\\\\|\/\/)/;
function importTarget(token, from, homedir2) {
  if (NETWORK_PATH.test(token)) return null;
  const target = token.startsWith("~/") || token.startsWith("~\\") ? join21(homedir2, token.slice(2)) : isAbsolute(token) ? token : resolve6(dirname3(from), token);
  return NETWORK_PATH.test(target) ? null : target;
}
function geminiImportTarget(token, from) {
  if (/^(file|https?):\/\//i.test(token) || NETWORK_PATH.test(token)) return null;
  const target = resolve6(dirname3(from), token);
  return NETWORK_PATH.test(target) ? null : target;
}
var MAX_LINK_HOPS = 40;
async function reachesNetwork(path, ops = { lstat: lstat5, readlink }) {
  let pending = resolve6(path);
  for (let hops = 0; hops <= MAX_LINK_HOPS; hops++) {
    if (NETWORK_PATH.test(pending)) return true;
    const { root } = parse(pending);
    const parts = pending.slice(root.length).split(/[\\/]+/).filter((part) => part !== "");
    let current = root;
    let followed = false;
    for (let index = 0; index < parts.length && !followed; index++) {
      current = join21(current, parts[index]);
      let info;
      try {
        info = await ops.lstat(current);
      } catch {
        return false;
      }
      if (!info.isSymbolicLink()) continue;
      let target;
      try {
        target = await ops.readlink(current);
      } catch {
        return false;
      }
      if (NETWORK_PATH.test(target)) return true;
      pending = join21(resolve6(dirname3(current), target), ...parts.slice(index + 1));
      followed = true;
    }
    if (!followed) return false;
  }
  return true;
}
var insideOf = (path, folder) => normalizePath(path).startsWith(`${normalizePath(folder).replace(/\/$/, "")}/`);
async function readInstructionSet(paths, mentionTargets = [], sameAsGlobal = /* @__PURE__ */ new Set(), imports = null) {
  const set = emptyInstructionSet();
  const hashes = /* @__PURE__ */ new Set();
  const mentions = /* @__PURE__ */ Object.create(null);
  const queue = [...new Set(paths)].sort().map((path) => ({ path, hops: 0 }));
  const seen = new Set(queue.map((item2) => normalizePath(item2.path)));
  const readReal = /* @__PURE__ */ new Set();
  const rootReal = imports?.within ? ((await entryInfo(imports.within)).realPath ?? normalizePath(imports.within)).replace(/\/$/, "") : null;
  for (let index = 0; index < queue.length; index++) {
    const { path, hops } = queue[index];
    if (hops > 0) {
      if (await reachesNetwork(path)) continue;
      const target = await entryInfo(path);
      if (!target.isFile) continue;
      if (rootReal !== null && (target.realPath === null || !target.realPath.startsWith(`${rootReal}/`))) continue;
    }
    const read = await readText(path);
    if (read.status === "missing") continue;
    if (read.status === "unreadable") {
      set.unreadable.push(path);
      continue;
    }
    const info = await entryInfo(path);
    if (hops > 0 && info.realPath !== null && readReal.has(info.realPath)) continue;
    if (info.realPath !== null) readReal.add(info.realPath);
    if (imports !== null && hops < (imports.style === "gemini" ? GEMINI_IMPORT_HOPS : MAX_IMPORT_HOPS)) {
      const gemini = imports.style === "gemini";
      for (const token of importsOf(read.text, gemini ? "gemini" : "claude")) {
        const target = gemini ? geminiImportTarget(token, path) : importTarget(token, path, imports.homedir);
        if (target === null) continue;
        if (imports.within !== null && !gemini && !insideOf(target, imports.within)) continue;
        const key = normalizePath(target);
        if (seen.has(key)) continue;
        seen.add(key);
        queue.push({ path: target, hops: hops + 1 });
      }
    }
    const same = info.realPath !== null && sameAsGlobal.has(info.realPath);
    const bytes = Buffer.byteLength(read.text, "utf8");
    set.files.push({ path, realPath: info.realPath, bytes, hasContent: /\S/u.test(read.text), sameAsGlobal: same });
    set.bytes += bytes;
    const chars = countChars(read.text);
    set.chars.ascii += chars.ascii;
    set.chars.other += chars.other;
    if (!same) for (const hash of linesForOverlap(read.text)) hashes.add(hash);
    for (const [key, count] of Object.entries(countMentions(read.text, mentionTargets))) mentions[key] = (mentions[key] ?? 0) + count;
  }
  set.lineHashes = [...hashes].sort();
  set.files.sort((a, b) => a.path < b.path ? -1 : a.path > b.path ? 1 : 0);
  set.unreadable.sort();
  return { set, mentions };
}
async function globalInstructionPaths(claudeHome2) {
  const rules = await markdownFilesUnder(join21(claudeHome2, "rules"));
  return { paths: [join21(claudeHome2, "CLAUDE.md"), ...rules.paths], unreadableDirs: rules.unreadableDirs };
}
async function projectInstructionPaths(root) {
  const claudeFiles = [join21(root, "CLAUDE.md"), join21(root, ".claude", "CLAUDE.md"), join21(root, "CLAUDE.local.md")];
  const present = [];
  for (const path of claudeFiles) if ((await entryInfo(path)).isFile) present.push(path);
  const rules = await markdownFilesUnder(join21(root, ".claude", "rules"));
  const paths = present.length > 0 ? [...present, ...rules.paths] : [join21(root, "AGENTS.md"), join21(root, ".claude", "AGENTS.md"), ...rules.paths];
  return { paths, unreadableDirs: rules.unreadableDirs };
}
async function readGlobalInstructions(claudeHome2, mentionTargets, options = null) {
  const found = await globalInstructionPaths(claudeHome2);
  const read = await readInstructionSet(found.paths, mentionTargets, /* @__PURE__ */ new Set(), options === null ? null : { homedir: options.homedir, within: null });
  read.set.unreadableDirs = found.unreadableDirs;
  return read;
}
async function readProjectInstructions(root, global, options = null) {
  const found = await projectInstructionPaths(root);
  const { set } = await readInstructionSet(found.paths, [], realPaths(global), options === null ? null : { homedir: options.homedir, within: root });
  set.unreadableDirs = found.unreadableDirs;
  return set;
}
function realPaths(set) {
  return new Set(set.files.map((file) => file.realPath ?? normalizePath(file.path)));
}

// src/scan/mcp.ts
import { createHmac } from "node:crypto";
function definitionHash(saltHex, definition) {
  const text = canonicalJson(definition);
  return text === null ? null : createHmac("sha256", Buffer.from(saltHex, "hex")).update(text).digest("hex");
}
var wildcard = (pattern) => new RegExp(`^${pattern.split("*").map((part) => part.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join(".*")}$`);
function matcherHits(matcher, names2, definition, byName2 = true) {
  if (byName2 && matcher.serverName !== void 0 && names2.includes(matcher.serverName)) return true;
  if (matcher.serverUrl !== void 0 && definition !== null && typeof definition.url === "string" && wildcard(matcher.serverUrl).test(definition.url)) return true;
  if (matcher.serverCommand !== void 0 && definition !== null && typeof definition.command === "string") {
    const args = Array.isArray(definition.args) ? definition.args : [];
    const command = [definition.command, ...args];
    if (command.length === matcher.serverCommand.length && command.every((part, i) => part === matcher.serverCommand[i])) return true;
  }
  return false;
}
function mcpAllowed(context, names2, definition, plugin = false) {
  for (const layer of context.layers) if (layer.deniedMcpServers.some((m) => matcherHits(m, names2, definition))) return false;
  for (const layer of context.layers) if (layer.allowedMcpServers !== null && !layer.allowedMcpServers.some((m) => matcherHits(m, names2, definition, !plugin))) return false;
  if (context.project !== null && names2.some((name) => context.project.disabledMcpServers.includes(name))) return false;
  return true;
}
function projectServerApproved(context, name) {
  const disabled = /* @__PURE__ */ new Set([...context.layers.flatMap((l) => l.disabledMcpjsonServers), ...context.project?.disabledMcpjsonServers ?? []]);
  if (disabled.has(name)) return false;
  let approveAll = null;
  for (const layer of context.layers) if (layer.enableAllProjectMcpServers !== null) approveAll = layer.enableAllProjectMcpServers;
  if (approveAll === true) return true;
  const enabled = /* @__PURE__ */ new Set([...context.layers.flatMap((l) => l.enabledMcpjsonServers), ...context.project?.enabledMcpjsonServers ?? []]);
  return enabled.has(name);
}

// src/scan/secrets.ts
var KNOWN = [
  /\bsk-(?:ant-|proj-)?[A-Za-z0-9_-]{20,}/,
  /\bgh[pousr]_[A-Za-z0-9]{30,}/,
  /\bgithub_pat_[A-Za-z0-9_]{30,}/,
  /\bxox[abeprs]-[A-Za-z0-9-]{10,}/,
  /\b(?:AKIA|ASIA)[0-9A-Z]{16}\b/,
  /\bBearer\s+[A-Za-z0-9._~+/=-]{16,}/i,
  /\bAIza[0-9A-Za-z_-]{30,}/,
  /\bglpat-[A-Za-z0-9_-]{20,}/,
  /\bhf_[A-Za-z0-9]{30,}/,
  /\bya29\.[A-Za-z0-9_-]{20,}/,
  /\bntn_[A-Za-z0-9]{30,}/,
  /\bsecret_[A-Za-z0-9]{30,}/,
  /\bfigd_[A-Za-z0-9_-]{30,}/,
  /\blin_api_[A-Za-z0-9]{30,}/,
  /\b[sr]k_live_[A-Za-z0-9]{20,}/,
  /\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}/
];
var SECRET_WORDS = ["token", "secret", "password", "passwd", "apikey", "accesskey", "privatekey", "authorization", "bearer", "credential", "cookie"];
var NOT_VALUE_ENDINGS = ["envvar", "var", "name", "path", "file", "dir", "url", "uri", "type", "id", "mode", "count", "length", "ttl", "expiry", "expires", "timeout"];
var PLAIN_FIELDS = /* @__PURE__ */ new Set(["command", "type", "url", "cwd", "transport", "enabled"]);
var MIN_LENGTH = 8;
var isObject7 = (value) => typeof value === "object" && value !== null && !Array.isArray(value);
var normalized = (name) => name.toLowerCase().replace(/[^a-z0-9]/g, "");
function secretName(name) {
  const n = normalized(name);
  if (NOT_VALUE_ENDINGS.some((ending) => n.endsWith(ending))) return false;
  return SECRET_WORDS.some((word) => n.includes(word)) || n.endsWith("key");
}
var isReference = (value) => /\$\{[^}]*\}/.test(value) || /(?:^|\s)(?:\$[A-Za-z_][A-Za-z0-9_]*|%[A-Za-z_][A-Za-z0-9_]*%)(?=\s|$)/.test(value);
var safeDecode = (value) => {
  try {
    return decodeURIComponent(value);
  } catch {
    return value;
  }
};
var isPlaceholder = (value) => /^(<[^>]*>|\[[^\]]*\]|\{[^}]*\}|your[\s_-].*|.*placeholder.*|(.)\2{5,}|change[\s_-]?me|example|test|dummy|none|null|undefined|true|false|todo|tbd)$/i.test(value.trim());
var isKnown = (value) => KNOWN.some((pattern) => pattern.test(value));
function literalSecret(value) {
  const text = value.trim();
  if (text.length < MIN_LENGTH || isReference(text) || isPlaceholder(text)) return false;
  if (/^[A-Z][A-Z0-9_]*$/.test(text)) return false;
  if (/^(\/|~|[A-Za-z]:[\\/]|\.{1,2}[\\/]|https?:\/\/)/.test(text)) return false;
  return true;
}
var secretPair = (name, value) => typeof value === "string" && !isReference(value) && (isKnown(value) || secretName(name) && literalSecret(value));
function tableSpots(field, table) {
  if (!isObject7(table)) return [];
  return Object.entries(table).filter(([name, value]) => secretPair(name, value)).map(([name]) => ({ field, key: name }));
}
var HEADER_FLAGS = /* @__PURE__ */ new Set(["--header", "--headers", "-H"]);
function headerForm(text) {
  const match = /^\s*([A-Za-z][A-Za-z0-9-]*)\s*:\s*(.+)$/.exec(text);
  return match === null ? null : { name: match[1], value: match[2].trim() };
}
function headerSecret(text) {
  const header2 = headerForm(text);
  return header2 !== null && secretName(header2.name) && secretPair(header2.name, header2.value) ? header2.name : null;
}
function argSpots(args) {
  if (!Array.isArray(args)) return [];
  const spots = [];
  args.forEach((arg, index) => {
    if (typeof arg !== "string") return;
    const flag = /^(--?[A-Za-z][A-Za-z0-9_-]*)=(.*)$/.exec(arg);
    if (flag !== null) {
      const header3 = HEADER_FLAGS.has(flag[1]) ? headerSecret(flag[2]) : null;
      if (header3 !== null) spots.push({ field: "args", key: header3 });
      else if (secretPair(flag[1], flag[2])) spots.push({ field: "args", key: flag[1] });
      return;
    }
    const header2 = headerSecret(arg);
    if (header2 !== null) {
      spots.push({ field: "args", key: header2 });
      return;
    }
    const previous = index > 0 ? args[index - 1] : void 0;
    if (typeof previous === "string" && /^--?[A-Za-z]/.test(previous) && !previous.includes("=") && !arg.startsWith("-") && secretName(previous) && literalSecret(arg) && !isReference(arg)) {
      spots.push({ field: "args", key: previous });
      return;
    }
    if (!isReference(arg) && isKnown(arg)) spots.push({ field: "args", key: `#${index + 1}` });
  });
  return spots;
}
function urlSpots(url) {
  if (typeof url !== "string") return [];
  let parsed;
  try {
    parsed = new URL(url);
  } catch {
    return [];
  }
  const spots = [];
  if (parsed.username !== "" && isKnown(safeDecode(parsed.username))) spots.push({ field: "url", key: "username" });
  if (parsed.password !== "" && !isReference(parsed.password) && !isReference(safeDecode(parsed.password))) spots.push({ field: "url", key: "password" });
  for (const [name, value] of parsed.searchParams) if (secretPair(name, value) || normalized(name) === "key" && literalSecret(value)) spots.push({ field: "url", key: name });
  return spots;
}
function secretSpots(definition) {
  try {
    return spotsOf(definition);
  } catch {
    return [];
  }
}
function spotsOf(definition) {
  if (definition === null || !isObject7(definition)) return [];
  const fields = Object.entries(definition).filter(([name, value]) => !PLAIN_FIELDS.has(name) && typeof value === "string" && secretPair(name, value)).map(([name]) => ({ field: "field", key: name }));
  const all = [...tableSpots("env", definition.env), ...tableSpots("headers", definition.headers), ...tableSpots("headers", definition.http_headers), ...fields, ...argSpots(definition.args), ...urlSpots(definition.url)];
  const seen = /* @__PURE__ */ new Set();
  return all.filter((spot) => {
    const id = `${spot.field}\0${spot.key}`;
    if (seen.has(id)) return false;
    seen.add(id);
    return true;
  });
}
var SCOPE_ORDER4 = { settings: 0, user: 1, local: 2, project: 3 };
var FIELD_ORDER = { env: 0, headers: 1, field: 2, args: 3, url: 4 };
var byText11 = (a, b) => (a ?? "") < (b ?? "") ? -1 : (a ?? "") > (b ?? "") ? 1 : 0;
function sortSecrets(list) {
  return [...list].sort((a, b) => SCOPE_ORDER4[a.scope] - SCOPE_ORDER4[b.scope] || byText11(a.projectRoot, b.projectRoot) || byText11(a.server, b.server) || FIELD_ORDER[a.field] - FIELD_ORDER[b.field] || byText11(a.key, b.key));
}
function envSecretKeys(env) {
  try {
    return tableSpots("env", env).map((spot) => spot.key);
  } catch {
    return [];
  }
}

// src/scan/names.ts
function toolForm(name) {
  return name.replace(/[^A-Za-z0-9_-]/g, "_");
}
function callForm(name) {
  return toolForm(name).split("__")[0];
}
function mcpRecordNames(name, pluginName) {
  const forms = pluginName === null ? [name, callForm(name)] : [`plugin:${pluginName}:${name}`, callForm(`plugin_${pluginName}_${name}`)];
  return [...new Set(forms)].sort();
}
function skillRecordNames(dirName, declaredName, pluginName) {
  const bare = [dirName, ...declaredName === null ? [] : [declaredName]];
  if (pluginName === null) return [...new Set(bare)].sort();
  const prefix = `${pluginName}:`;
  return [...new Set(bare.map((name) => name.startsWith(prefix) ? name : `${prefix}${name}`))].sort();
}

// src/scan/permissions.ts
function conflictPairs(user, project, local) {
  const projectAllow = /* @__PURE__ */ new Set([...project?.allow ?? [], ...local?.allow ?? []]);
  const projectDeny = /* @__PURE__ */ new Set([...project?.deny ?? [], ...local?.deny ?? []]);
  let pairs = 0;
  for (const rule2 of new Set(user.allow)) if (projectDeny.has(rule2)) pairs++;
  for (const rule2 of new Set(user.deny)) if (projectAllow.has(rule2)) pairs++;
  return pairs;
}

// src/scan/projects.ts
import { dirname as dirname4, isAbsolute as isAbsolute2, join as join22, parse as parse2, resolve as resolve7 } from "node:path";
async function mainRootFromGitFile(dir, dotGit) {
  const text = await readText(dotGit);
  if (text.status !== "ok") return null;
  const match = /^gitdir:\s*(.+?)\s*$/m.exec(text.text);
  if (match === null) return null;
  const gitDir = isAbsolute2(match[1]) ? match[1] : resolve7(dir, match[1]);
  const common = await readText(join22(gitDir, "commondir"));
  if (common.status !== "ok") return null;
  const commonDir = resolve7(gitDir, common.text.trim());
  return parse2(commonDir).base.toLowerCase() === ".git" ? dirname4(commonDir) : null;
}
async function gitRootFrom(start) {
  let dir = start;
  for (; ; ) {
    const dotGit = join22(dir, ".git");
    const info = await entryInfo(dotGit);
    if (info.exists && info.isDir) return dir;
    if (info.exists && info.isFile) return await mainRootFromGitFile(dir, dotGit) ?? dir;
    const parent = dirname4(dir);
    if (parent === dir) return null;
    dir = parent;
  }
}
var under = (path, base) => path === base || path.startsWith(base.endsWith("/") ? base : `${base}/`);
function isExcludedFolder(normRoot, normCwd, context) {
  const norm = (path) => normalizePath(path, context.platform);
  const specials = [context.homedir, join22(context.homedir, "Desktop"), join22(context.homedir, "Documents"), join22(context.homedir, "Downloads")].map(norm);
  const tmp = norm(context.tmpdir);
  const driveRoot = /^[a-z]:\/?$/i.test(normRoot) || normRoot === "/";
  return specials.includes(normRoot) || driveRoot || under(normRoot, tmp) || under(normCwd, tmp);
}
async function resolveProject(cwd, context) {
  const absolute = resolve7(cwd);
  const info = await entryInfo(absolute);
  const exists = info.exists && info.isDir;
  const gitRoot = exists ? await gitRootFrom(absolute) : null;
  const root = gitRoot ?? absolute;
  const normRoot = normalizePath(root, context.platform);
  const normCwd = normalizePath(absolute, context.platform);
  return { root, normRoot, kind: gitRoot === null ? "folder" : "git", exists, excluded: isExcludedFolder(normRoot, normCwd, context), cwds: [normCwd] };
}
async function groupProjects(cwds, context) {
  const byNormCwd = /* @__PURE__ */ new Map();
  for (const cwd of cwds) {
    const normCwd = normalizePath(cwd, context.platform);
    const previous = byNormCwd.get(normCwd);
    if (previous === void 0 || cwd < previous) byNormCwd.set(normCwd, cwd);
  }
  const byRoot = /* @__PURE__ */ new Map();
  for (const normCwd of [...byNormCwd.keys()].sort()) {
    const ref = await resolveProject(byNormCwd.get(normCwd), context);
    const existing = byRoot.get(ref.normRoot);
    if (existing === void 0) {
      byRoot.set(ref.normRoot, ref);
      continue;
    }
    existing.cwds.push(normCwd);
    existing.exists ||= ref.exists;
    existing.excluded ||= ref.excluded;
    if (ref.root < existing.root) existing.root = ref.root;
  }
  const out = [...byRoot.values()].sort((x, y) => x.normRoot < y.normRoot ? -1 : x.normRoot > y.normRoot ? 1 : 0);
  for (const ref of out) ref.cwds.sort();
  return out;
}

// src/scan/settings.ts
import { join as join23 } from "node:path";
var MERGE_MAX_DEPTH = 32;
function managedSettingsDir(platform) {
  if (platform === "win32") return "C:\\Program Files\\ClaudeCode";
  if (platform === "darwin") return "/Library/Application Support/ClaudeCode";
  return "/etc/claude-code";
}
async function readPart(path) {
  const read = await readJson(path);
  if (read.status !== "ok") return { part: { path, status: read.status }, value: null };
  if (!isObject5(read.value)) return { part: { path, status: "unparsable" }, value: null };
  return { part: { path, status: "ok" }, value: read.value };
}
async function readLayer(path) {
  const { part, value } = await readPart(path);
  return { parts: [part], value, hookSources: value !== null && Object.hasOwn(value, "hooks") ? [{ path, hooks: value.hooks }] : [] };
}
function unionList(before, next) {
  const seen = /* @__PURE__ */ new Set();
  const out = [];
  for (const item2 of [...before, ...next]) {
    const key = canonicalJson(item2);
    if (key === null) {
      out.push(item2);
      continue;
    }
    if (seen.has(key)) continue;
    seen.add(key);
    out.push(item2);
  }
  return out;
}
function mergeSettings(base, next, depth = 0) {
  const out = /* @__PURE__ */ Object.create(null);
  for (const key of Object.keys(base)) out[key] = base[key];
  for (const [key, value] of Object.entries(next)) {
    const before = Object.hasOwn(out, key) ? out[key] : void 0;
    if (Array.isArray(value)) {
      out[key] = unionList(Array.isArray(before) ? before : [], value);
    } else if (isObject5(value) && depth < MERGE_MAX_DEPTH) {
      out[key] = mergeSettings(isObject5(before) ? before : {}, value, depth + 1);
    } else {
      out[key] = value;
    }
  }
  return out;
}
function failClosedBoolean(value, restrictive) {
  if (typeof value === "boolean") return value;
  if (value === "true") return true;
  if (value === "false") return false;
  return restrictive;
}
var SKILL_OVERRIDE_MODES = /* @__PURE__ */ new Set(["on", "name-only", "user-invocable-only", "off"]);
var PERMISSION_LISTS = /* @__PURE__ */ new Set(["allow", "deny", "ask"]);
var PERMISSION_GRANTS = ["allow", "additionalDirectories"];
var MANAGED_LISTS = /* @__PURE__ */ new Set(["deniedMcpServers", "enabledMcpjsonServers", "disabledMcpjsonServers"]);
function sanitizeManagedPart(value) {
  const out = /* @__PURE__ */ Object.create(null);
  for (const [key, v] of Object.entries(value)) {
    if (v === null) continue;
    if (key === "disableAllHooks") {
      if (typeof v === "boolean") out[key] = v;
    } else if (key === "allowManagedHooksOnly") {
      out[key] = failClosedBoolean(v, true);
    } else if (key === "enableAllProjectMcpServers") {
      out[key] = failClosedBoolean(v, false);
    } else if (key === "permissions") {
      if (!isObject5(v)) continue;
      const permissions = /* @__PURE__ */ Object.create(null);
      for (const [field, fv] of Object.entries(v)) {
        if (fv === null) continue;
        if (field === "defaultMode") permissions[field] = typeof fv === "string" ? fv : "default";
        else if (!PERMISSION_LISTS.has(field) || Array.isArray(fv)) permissions[field] = fv;
      }
      if (["deny", "ask"].some((field) => Object.hasOwn(v, field) && v[field] !== null && !Array.isArray(v[field]))) for (const grant of PERMISSION_GRANTS) delete permissions[grant];
      out[key] = permissions;
    } else if (key === "allowedMcpServers") {
      out[key] = Array.isArray(v) ? v : [];
    } else if (MANAGED_LISTS.has(key)) {
      if (Array.isArray(v)) out[key] = v;
    } else if (key === "enabledPlugins" || key === "skillOverrides") {
      if (!isObject5(v)) continue;
      const kept = Object.entries(v).filter(([, entry]) => key === "enabledPlugins" ? typeof entry === "boolean" : typeof entry === "string" && SKILL_OVERRIDE_MODES.has(entry));
      if (kept.length > 0) out[key] = Object.fromEntries(kept);
    } else {
      out[key] = v;
    }
  }
  return out;
}
async function readManagedLayer(dir) {
  const parts = [];
  const hookSources = [];
  let merged = null;
  const take = async (path) => {
    const { part, value } = await readPart(path);
    if (part.status === "missing") return;
    parts.push(part);
    if (value !== null) merged = mergeSettings(merged ?? {}, sanitizeManagedPart(value));
    if (value !== null && Object.hasOwn(value, "hooks") && value.hooks !== null) hookSources.push({ path, hooks: value.hooks });
  };
  await take(join23(dir, "managed-settings.json"));
  const dropIns = await listDir(join23(dir, "managed-settings.d"));
  if (dropIns.status === "ok") {
    for (const name of dropIns.names) if (!name.startsWith(".") && name.toLowerCase().endsWith(".json")) await take(join23(dir, "managed-settings.d", name));
  } else if (dropIns.status === "unreadable") {
    parts.push({ path: join23(dir, "managed-settings.d"), status: "unreadable" });
  }
  return { parts, value: merged, hookSources };
}
var strings3 = (v) => Array.isArray(v) ? v.filter((x) => typeof x === "string") : [];
function matchers(v) {
  if (!Array.isArray(v)) return [];
  const out = [];
  for (const item2 of v) {
    if (!isObject5(item2)) continue;
    const m = {};
    if (typeof item2.serverName === "string") m.serverName = item2.serverName;
    if (typeof item2.serverUrl === "string") m.serverUrl = item2.serverUrl;
    if (Array.isArray(item2.serverCommand) && item2.serverCommand.every((x) => typeof x === "string")) m.serverCommand = [...item2.serverCommand];
    if (Object.keys(m).length > 0) out.push(m);
  }
  return out;
}
function viewOf(value) {
  const v = value ?? {};
  const permissions = isObject5(v.permissions) ? v.permissions : {};
  const overrides = /* @__PURE__ */ Object.create(null);
  if (isObject5(v.skillOverrides)) {
    for (const [name, mode2] of Object.entries(v.skillOverrides)) if (typeof mode2 === "string" && SKILL_OVERRIDE_MODES.has(mode2)) overrides[name] = mode2;
  }
  const plugins = /* @__PURE__ */ Object.create(null);
  if (isObject5(v.enabledPlugins)) {
    for (const [id, on] of Object.entries(v.enabledPlugins)) if (typeof on === "boolean") plugins[id] = on;
  }
  const mode = permissions.defaultMode;
  const defaultMode = typeof mode !== "string" ? null : mode === "bypassPermissions" ? "bypass" : "other";
  return {
    defaultMode,
    bypass: defaultMode === "bypass",
    allow: strings3(permissions.allow),
    deny: strings3(permissions.deny),
    skillOverrides: overrides,
    enabledPlugins: plugins,
    deniedMcpServers: matchers(v.deniedMcpServers),
    allowedMcpServers: Array.isArray(v.allowedMcpServers) ? matchers(v.allowedMcpServers) : null,
    enabledMcpjsonServers: strings3(v.enabledMcpjsonServers),
    disabledMcpjsonServers: strings3(v.disabledMcpjsonServers),
    enableAllProjectMcpServers: typeof v.enableAllProjectMcpServers === "boolean" ? v.enableAllProjectMcpServers : null,
    hooks: v.hooks,
    disableAllHooks: v.disableAllHooks === true,
    allowManagedHooksOnly: v.allowManagedHooksOnly === true
  };
}

// src/scan/skills.ts
import { createHash as createHash6 } from "node:crypto";
import { lstat as lstat6, readdir as readdir9, readFile as readFile10, realpath as realpath5 } from "node:fs/promises";
import { basename as basename6, join as join24, relative as relative2 } from "node:path";
var CONTENT_HASH_MAX_BYTES = 32 * 1024 * 1024;
var SIMPLE_ESCAPES2 = {
  "0": "\0",
  a: "\x07",
  b: "\b",
  t: "	",
  "	": "	",
  n: "\n",
  v: "\v",
  f: "\f",
  r: "\r",
  e: "\x1B",
  " ": " ",
  '"': '"',
  "/": "/",
  "\\": "\\",
  N: "\x85",
  _: "\xA0",
  L: "\u2028",
  P: "\u2029"
};
var HEX_ESCAPES = { x: 2, u: 4, U: 8 };
function readScalar(raw) {
  const s = raw.trim();
  if (s === "" || s.startsWith("#")) return "";
  const rest = (from) => {
    const tail = s.slice(from).trim();
    return tail === "" || tail.startsWith("#");
  };
  if (s[0] === '"') {
    let out = "";
    for (let i = 1; i < s.length; i++) {
      const ch = s[i];
      if (ch === "\\") {
        const next = s[i + 1];
        if (next === void 0) return null;
        if (Object.hasOwn(SIMPLE_ESCAPES2, next)) {
          out += SIMPLE_ESCAPES2[next];
          i++;
          continue;
        }
        if (!Object.hasOwn(HEX_ESCAPES, next)) return null;
        const width = HEX_ESCAPES[next];
        const hex = s.slice(i + 2, i + 2 + width);
        if (!/^[0-9A-Fa-f]+$/.test(hex)) return null;
        const code = Number.parseInt(hex, 16);
        if (code > 1114111) return null;
        out += String.fromCodePoint(code);
        i += 1 + width;
        continue;
      }
      if (ch === '"') return rest(i + 1) ? out : null;
      out += ch;
    }
    return null;
  }
  if (s[0] === "'") {
    let out = "";
    for (let i = 1; i < s.length; i++) {
      const ch = s[i];
      if (ch === "'") {
        if (s[i + 1] === "'") {
          out += "'";
          i++;
          continue;
        }
        return rest(i + 1) ? out : null;
      }
      out += ch;
    }
    return null;
  }
  if ("|>[{&*!".includes(s[0])) return null;
  const comment = s.search(/\s#/);
  return (comment === -1 ? s : s.slice(0, comment)).trim();
}
var YAML_TRUE = /* @__PURE__ */ new Set(["true", "True", "TRUE"]);
var YAML_FALSE = /* @__PURE__ */ new Set(["false", "False", "FALSE"]);
function parseFrontmatter(text) {
  const lines = text.split("\n").map((line) => line.replace(/\r$/, ""));
  const none = { present: false, fields: /* @__PURE__ */ Object.create(null), unreadable: [] };
  if (lines[0]?.trim() !== "---") return none;
  const end = lines.findIndex((line, index) => index > 0 && line.trim() === "---");
  if (end === -1) return none;
  const fields = /* @__PURE__ */ Object.create(null);
  const unreadable = [];
  const mark = (key) => {
    if (!unreadable.includes(key)) unreadable.push(key);
  };
  if (lines[end] !== lines[end].trimStart()) mark("name");
  let previous = null;
  let nameSeen = false;
  for (const line of lines.slice(1, end)) {
    if (line.trim() === "") continue;
    if (/^\s/.test(line)) {
      if (line.trimStart().startsWith("#")) continue;
      if (previous === null) mark("name");
      if (previous === "name") {
        mark("name");
        delete fields.name;
      }
      continue;
    }
    if (line.startsWith("#")) continue;
    const match = /^([A-Za-z0-9_-]+):(?:\s+(.*))?$/.exec(line);
    if (match === null) {
      mark("name");
      previous = null;
      continue;
    }
    previous = match[1];
    if (previous === "name") {
      if (nameSeen) {
        mark("name");
        delete fields.name;
        continue;
      }
      nameSeen = true;
    }
    const value = readScalar(match[2] ?? "");
    if (value === null) mark(match[1]);
    else fields[match[1]] = value;
  }
  return { present: true, fields, unreadable };
}
async function contentHash(dir, maxBytes = CONTENT_HASH_MAX_BYTES) {
  let base;
  try {
    base = await realpath5(dir);
  } catch {
    return null;
  }
  const entries = [];
  let total = 0;
  const walk = async (current) => {
    let names2;
    try {
      names2 = (await readdir9(current)).sort();
    } catch {
      return false;
    }
    for (const name of names2) {
      const path = join24(current, name);
      let info;
      try {
        info = await lstat6(path);
      } catch {
        return false;
      }
      if (info.isSymbolicLink()) return false;
      if (info.isDirectory()) {
        if (!await walk(path)) return false;
        continue;
      }
      if (!info.isFile()) return false;
      total += info.size;
      if (total > maxBytes) return false;
      let data;
      try {
        data = await readFile10(path);
      } catch {
        return false;
      }
      const rel = relative2(base, path).replace(/\\/g, "/");
      entries.push(`${rel}\0${createHash6("sha256").update(data).digest("hex")}`);
    }
    return true;
  };
  if (!await walk(base)) return null;
  return createHash6("sha256").update(entries.sort().join("\n")).digest("hex");
}
async function readSkillFolder(path, dirName) {
  const info = await entryInfo(path);
  if (!info.isDir) return null;
  const skillMd = await readText(join24(path, "SKILL.md"));
  if (skillMd.status === "missing") return null;
  const front = skillMd.status === "ok" ? parseFrontmatter(skillMd.text) : { present: false, fields: /* @__PURE__ */ Object.create(null), unreadable: [] };
  const name = front.fields.name;
  return {
    dirName,
    path,
    realPath: info.realPath,
    isLink: info.isLink,
    createdMs: info.createdMs,
    targetCreatedMs: info.targetCreatedMs,
    readable: skillMd.status === "ok",
    hasFrontmatter: front.present,
    declaredName: name !== void 0 && name !== "" ? name : null,
    nameUnreadable: front.unreadable.includes("name"),
    // 읽지 못한 값은 기본값(모델이 부를 수 있음, 사람이 부를 수 있음)으로 둔다
    disableModelInvocation: YAML_TRUE.has(front.fields["disable-model-invocation"] ?? ""),
    userInvocable: !YAML_FALSE.has(front.fields["user-invocable"] ?? ""),
    contentHash: await contentHash(path)
  };
}
async function scanSkillRoot(dir, options = {}) {
  const out = { skills: [], danglingLinks: [], unreadableDirs: [], pluginDirs: [] };
  const listing = await listDir(dir);
  if (listing.status === "unreadable") out.unreadableDirs.push(dir);
  if (listing.status !== "ok") return out;
  for (const name of listing.names) {
    const path = join24(dir, name);
    const info = await entryInfo(path);
    if (info.dangling) {
      out.danglingLinks.push(path);
      continue;
    }
    if (options.pluginDirs === true && info.isDir && (await entryInfo(join24(path, ".claude-plugin", "plugin.json"))).isFile) {
      out.pluginDirs.push(path);
      continue;
    }
    const skill = await readSkillFolder(path, name);
    if (skill !== null) out.skills.push(skill);
  }
  return out;
}
async function scanSkillPath(path) {
  if ((await entryInfo(join24(path, "SKILL.md"))).isFile) {
    const single = await readSkillFolder(path, basename6(path));
    return { skills: single === null ? [] : [single], danglingLinks: [], unreadableDirs: [], pluginDirs: [] };
  }
  return scanSkillRoot(path);
}

// src/scan/claude.ts
var SKILL_SCOPE_ORDER = { user: 0, project: 1, plugin: 2 };
var MCP_SCOPE_ORDER = { user: 0, local: 1, project: 2, plugin: 3, "claude-ai": 4 };
var OWNER_ORDER = { user: 0, managed: 1, plugin: 2, tool: 3 };
var cmp2 = (a, b) => (a ?? "") < (b ?? "") ? -1 : (a ?? "") > (b ?? "") ? 1 : 0;
var layerStatus = (layer) => layer.parts[0]?.status ?? "missing";
function mergeClaudeJsonEntries(entries) {
  if (entries.length === 0) return null;
  const union = (pick) => [...new Set(entries.flatMap(pick))].sort();
  return {
    key: entries[0].key,
    normKey: entries[0].normKey,
    mcpServers: entries.flatMap((e) => e.mcpServers),
    enabledMcpjsonServers: union((e) => e.enabledMcpjsonServers),
    disabledMcpjsonServers: union((e) => e.disabledMcpjsonServers),
    disabledMcpServers: union((e) => e.disabledMcpServers)
  };
}
function pluginEnabledIn(context, id, defaultEnabled) {
  if (Object.hasOwn(context.managed.enabledPlugins, id)) return context.managed.enabledPlugins[id];
  let value;
  for (const layer of context.ordered) if (Object.hasOwn(layer.enabledPlugins, id)) value = layer.enabledPlugins[id];
  return value ?? defaultEnabled;
}
function overrideIn(context, names2) {
  for (const name of names2) if (Object.hasOwn(context.managed.skillOverrides, name)) return context.managed.skillOverrides[name];
  let value = null;
  for (const layer of context.ordered) for (const name of names2) if (Object.hasOwn(layer.skillOverrides, name)) value = layer.skillOverrides[name];
  return value;
}
function managedHits(managed, names2, definition) {
  if (managed.allowedMcpServers !== null) return true;
  return !mcpAllowed({ layers: [managed], project: null }, names2, definition);
}
var normalizedCommand = (text) => text.replace(/\\/g, "/").toLowerCase();
function usageOf2(times) {
  let usageLastUsedMs = null;
  let usageUndated = false;
  for (const at of times) {
    if (at === void 0) continue;
    if (at === null) usageUndated = true;
    else if (usageLastUsedMs === null || at > usageLastUsedMs) usageLastUsedMs = at;
  }
  return { usageLastUsedMs, usageUndated };
}
var USER_PLACE_HEADS = ["~", "$CLAUDE_CONFIG_DIR", "$CODEX_HOME"];
function projectNamesOf(refs) {
  const sorted = [...refs].sort((x, y) => x.normRoot < y.normRoot ? -1 : x.normRoot > y.normRoot ? 1 : 0);
  const original = (ref) => basename7(ref.root) || ref.root;
  const reading = (ref) => ref.exists && !ref.excluded;
  const reserved = new Set(sorted.filter(reading).map((ref) => original(ref).toLowerCase()));
  const taken = new Set(USER_PLACE_HEADS.map((head) => head.toLowerCase()));
  const names2 = /* @__PURE__ */ new Map();
  for (const ref of sorted) {
    const name = original(ref);
    if (!reading(ref)) {
      names2.set(ref.normRoot, name);
      continue;
    }
    let label = name;
    for (let n = 2; taken.has(label.toLowerCase()) || label !== name && reserved.has(label.toLowerCase()); n++) label = `${name} (${n})`;
    taken.add(label.toLowerCase());
    names2.set(ref.normRoot, label);
  }
  return names2;
}
var slashed = (path) => path.replace(/\\/g, "/");
async function defaultCopySecrets(input) {
  const defaultHome = join25(input.homedir, ".claude");
  if (!input.env.CLAUDE_CONFIG_DIR?.trim() || normalizePath(claudeHome(input.env, input.homedir)) === normalizePath(defaultHome)) return [];
  const found = [];
  const settings = await readJson(join25(defaultHome, "settings.json"));
  if (settings.status === "ok" && typeof settings.value === "object" && settings.value !== null) {
    for (const key of envSecretKeys(settings.value.env)) found.push({ scope: "settings", server: null, projectRoot: null, field: "env", key });
  }
  const claudeJson = await readClaudeJson(join25(input.homedir, ".claude.json"));
  for (const entry of claudeJson.userMcpServers) for (const spot of secretSpots(entry.definition)) found.push({ scope: "user", server: entry.name, projectRoot: null, ...spot });
  for (const project of claudeJson.projects) for (const entry of project.mcpServers) for (const spot of secretSpots(entry.definition)) found.push({ scope: "local", server: entry.name, projectRoot: project.normKey, ...spot });
  return sortSecrets(found).map((secret) => ({ ...secret, copy: "default" }));
}
async function scanClaudeSetup(input) {
  const home = claudeHome(input.env, input.homedir);
  const claudeJsonFile = claudeJsonPath(input.env, input.homedir);
  const claudeJson = await readClaudeJson(claudeJsonFile);
  const userLayer = await readLayer(join25(home, "settings.json"));
  const managedLayer = await readManagedLayer(input.managedDir ?? managedSettingsDir(input.platform));
  const userView = viewOf(userLayer.value);
  const managedView = viewOf(managedLayer.value);
  const problems = [];
  const configPlace = (path) => `${input.env.CLAUDE_CONFIG_DIR?.trim() ? "$CLAUDE_CONFIG_DIR" : "~/.claude"}/${slashed(relative3(home, path))}`;
  const unparsable = (layer, owner) => {
    for (const part of layer.parts) if (part.status === "unparsable") problems.push({ kind: "unparsable", owner, path: part.path, place: null });
  };
  const unparsableUser = (layer, placeOf) => {
    for (const part of layer.parts) if (part.status === "unparsable") problems.push({ kind: "unparsable", owner: "user", path: part.path, place: placeOf(part.path) });
  };
  unparsableUser(userLayer, configPlace);
  unparsable(managedLayer, "managed");
  if (claudeJson.status === "unparsable") problems.push({ kind: "unparsable", owner: "tool", path: claudeJsonFile, place: null });
  const refs = await groupProjects(input.cwds, { homedir: input.homedir, tmpdir: input.tmpdir, platform: input.platform });
  const global = { ordered: [userView], managed: managedView, mcp: { layers: [userView, managedView], project: null } };
  const projectLayers = /* @__PURE__ */ new Map();
  const contexts = /* @__PURE__ */ new Map();
  const active = refs.filter((ref) => ref.exists && !ref.excluded);
  const projectNames = projectNamesOf(refs);
  const projectPlace = (ref, path) => `${projectNames.get(ref.normRoot)}/${slashed(relative3(ref.root, path))}`;
  for (const ref of active) {
    const project = await readLayer(join25(ref.root, ".claude", "settings.json"));
    const local = await readLayer(join25(ref.root, ".claude", "settings.local.json"));
    unparsableUser(project, (path) => projectPlace(ref, path));
    unparsableUser(local, (path) => projectPlace(ref, path));
    projectLayers.set(ref.normRoot, { project, local });
    const projectView = viewOf(project.value);
    const localView = viewOf(local.value);
    const entry = mergeClaudeJsonEntries(claudeJson.projects.filter((p) => p.normKey === ref.normRoot));
    contexts.set(ref.normRoot, {
      ordered: [userView, projectView, localView],
      managed: managedView,
      mcp: { layers: [userView, projectView, localView, managedView], project: entry }
    });
  }
  const everyContext = [global, ...contexts.values()];
  const globalRead = await readGlobalInstructions(home, active, { homedir: input.homedir });
  const userSkillScan = await scanSkillRoot(join25(home, "skills"), { pluginDirs: true });
  const projectSkillScans = /* @__PURE__ */ new Map();
  for (const ref of active) projectSkillScans.set(ref.normRoot, await scanSkillRoot(join25(ref.root, ".claude", "skills"), { pluginDirs: true }));
  const skillsDirRefs = [
    ...userSkillScan.pluginDirs.map((path) => ({ path, scope: "user", projectRoot: null })),
    ...active.flatMap((ref) => projectSkillScans.get(ref.normRoot).pluginDirs.map((path) => ({ path, scope: "project", projectRoot: ref.normRoot })))
  ];
  const pluginsScan = await scanPlugins(home);
  const allPlugins = [...pluginsScan.plugins, ...await readSkillsDirPlugins(skillsDirRefs)].sort(
    (a, b) => cmp2(a.id, b.id) || cmp2(normalizePath(a.installPath), normalizePath(b.installPath))
  );
  const contextsOfPaths = (paths) => {
    const out = [];
    for (const ref of active) if (paths.some((path) => ref.normRoot === path || ref.cwds.includes(path))) out.push(contexts.get(ref.normRoot));
    return out;
  };
  const userScoped = (plugin) => plugin.scopes.some((scope) => scope !== "project" && scope !== "local");
  const pluginContexts = (plugin) => userScoped(plugin) ? everyContext : contextsOfPaths(plugin.projectPaths);
  const commandTexts = [
    ...hookCommandTexts(userView.hooks),
    ...managedLayer.hookSources.flatMap(({ hooks }) => hookCommandTexts(hooks)),
    ...[...contexts.values()].flatMap((c) => c.ordered.slice(1).flatMap((view) => hookCommandTexts(view.hooks))),
    ...allPlugins.flatMap((p) => p.hookEvents.flatMap(hookCommandTexts))
  ].map(normalizedCommand);
  const mentionedByHook = (skill) => {
    const fragments = [normalizePath(skill.path), skill.realPath ?? "", `/skills/${skill.dirName}`].filter((f) => f !== "").map((f) => f.toLowerCase());
    return commandTexts.some((text) => fragments.some((fragment) => text.includes(fragment)));
  };
  const skills = [];
  const unreadableDirs = [];
  const unreadableSkillPlaces = { user: false, projects: [], plugins: [] };
  const addSkill = (folder, fields) => {
    skills.push({
      ...fields,
      path: folder.path,
      realPath: folder.realPath,
      isLink: folder.isLink,
      contentHash: folder.contentHash,
      createdMs: folder.createdMs,
      targetCreatedMs: folder.targetCreatedMs,
      readable: folder.readable,
      nameUnreadable: folder.nameUnreadable,
      ...usageOf2(fields.recordNames.map((name) => claudeJson.skillUsage[name]))
    });
  };
  const addOwnSkills = (scan, scope, projectRoot, scopeContexts, placeOf) => {
    for (const path of scan.danglingLinks) problems.push({ kind: "danglingLink", owner: "user", path, place: placeOf(path) });
    unreadableDirs.push(...scan.unreadableDirs);
    if (scan.unreadableDirs.length > 0) {
      if (projectRoot === null) unreadableSkillPlaces.user = true;
      else unreadableSkillPlaces.projects.push(projectRoot);
    }
    for (const folder of scan.skills) {
      const recordNames = skillRecordNames(folder.dirName, folder.declaredName, null);
      const modes = scopeContexts.map((context) => overrideIn(context, recordNames));
      if (folder.readable && !folder.hasFrontmatter) problems.push({ kind: "noFrontmatter", owner: "user", path: folder.path, place: placeOf(folder.path) });
      addSkill(folder, {
        scope,
        name: folder.dirName,
        recordNames,
        projectRoot,
        pluginId: null,
        enabled: modes.some((mode) => mode !== "off"),
        listed: !folder.disableModelInvocation && modes.some((mode) => mode !== "off" && mode !== "user-invocable-only"),
        managedFixed: recordNames.some((name) => Object.hasOwn(managedView.skillOverrides, name)),
        hookProvided: mentionedByHook(folder)
      });
    }
  };
  addOwnSkills(userSkillScan, "user", null, everyContext, configPlace);
  for (const ref of active) addOwnSkills(projectSkillScans.get(ref.normRoot), "project", ref.normRoot, [contexts.get(ref.normRoot)], (path) => projectPlace(ref, path));
  const plugins = [];
  const mcpServers = [];
  for (const plugin of allPlugins) {
    if (plugin.manifest === "unparsable") problems.push({ kind: "unparsable", owner: "plugin", path: join25(plugin.installPath, ".claude-plugin", "plugin.json"), place: null });
    const enabledIn = pluginContexts(plugin).filter((context) => pluginEnabledIn(context, plugin.id, plugin.defaultEnabled));
    const hasHooks = plugin.components.includes("hooks");
    const pluginNames = [.../* @__PURE__ */ new Set([plugin.name, plugin.entryName])];
    const skillNames = [];
    const seenPaths = /* @__PURE__ */ new Set();
    if (plugin.compositionKnown) {
      for (const root of plugin.skillRoots) {
        const scan = await scanSkillPath(root);
        for (const path of scan.danglingLinks) problems.push({ kind: "danglingLink", owner: "plugin", path, place: null });
        unreadableDirs.push(...scan.unreadableDirs);
        if (scan.unreadableDirs.length > 0) unreadableSkillPlaces.plugins.push(plugin.id);
        for (const folder of scan.skills) {
          const at = normalizePath(folder.path);
          if (seenPaths.has(at)) continue;
          seenPaths.add(at);
          const recordNames = [...new Set(pluginNames.flatMap((pluginName) => skillRecordNames(folder.dirName, folder.declaredName, pluginName)))].sort();
          const name = `${plugin.name}:${folder.dirName}`;
          skillNames.push(name);
          if (folder.readable && !folder.hasFrontmatter) problems.push({ kind: "noFrontmatter", owner: "plugin", path: folder.path, place: null });
          addSkill(folder, {
            scope: "plugin",
            name,
            recordNames,
            projectRoot: null,
            pluginId: plugin.id,
            enabled: enabledIn.length > 0,
            listed: enabledIn.length > 0 && !folder.disableModelInvocation,
            managedFixed: Object.hasOwn(managedView.enabledPlugins, plugin.id),
            hookProvided: hasHooks || mentionedByHook(folder)
          });
        }
      }
    }
    for (const server of plugin.mcpServers) {
      const recordNames = [...new Set(pluginNames.flatMap((pluginName) => mcpRecordNames(server.name, pluginName)))].sort();
      const denyNames = [...new Set(pluginNames.map((pluginName) => `plugin:${pluginName}:${server.name}`))].sort();
      mcpServers.push({
        scope: "plugin",
        name: server.name,
        recordNames,
        projectRoot: null,
        pluginId: plugin.id,
        definitionHash: server.definition === null ? null : definitionHash(input.salt, server.definition),
        enabled: enabledIn.some((context) => mcpAllowed(context.mcp, denyNames, server.definition, true)),
        managedFixed: managedHits(managedView, denyNames, server.definition)
      });
    }
    plugins.push({
      id: plugin.id,
      entryName: plugin.entryName,
      name: plugin.name,
      scopes: plugin.scopes,
      projectRoots: plugin.projectPaths,
      installPath: plugin.installPath,
      installRealPath: plugin.installRealPath,
      exists: plugin.exists,
      manifest: plugin.manifest,
      marketplaceEntry: plugin.marketplaceEntry,
      compositionKnown: plugin.compositionKnown,
      enabled: enabledIn.length > 0,
      managedFixed: Object.hasOwn(managedView.enabledPlugins, plugin.id),
      managedForced: managedView.enabledPlugins[plugin.id] === true,
      components: plugin.components,
      unknownEntries: plugin.unknownEntries,
      dependencies: plugin.dependencies,
      hasHooks,
      hooksUnreadable: plugin.hooksUnreadable,
      mcpUnreadable: plugin.mcpUnreadable,
      skills: skillNames.sort(),
      // 집계의 열쇠가 어느 이름인지 확인하지 못해 두 이름으로 모두 찾는다(설계 10 「~/.claude.json」)
      ...usageOf2(pluginNames.map((pluginName) => claudeJson.pluginUsage[`${pluginName}@${plugin.marketplace}`]))
    });
  }
  const installedIds = new Set(allPlugins.map((p) => p.id));
  const mentionedIds = new Set(Object.keys(managedView.enabledPlugins));
  for (const context of everyContext) for (const layer of context.ordered) for (const id of Object.keys(layer.enabledPlugins)) mentionedIds.add(id);
  const pluginsWithoutInstall = [...mentionedIds].filter((id) => !installedIds.has(id) && !id.endsWith("@builtin")).filter((id) => everyContext.some((context) => pluginEnabledIn(context, id, false))).sort();
  const userSettings = userLayer.value;
  const secrets = envSecretKeys(typeof userSettings === "object" && userSettings !== null ? userSettings.env : void 0).map((key) => ({ scope: "settings", server: null, projectRoot: null, field: "env", key }));
  const addServer = (scope, entry, projectRoot, enabled) => {
    const names2 = mcpRecordNames(entry.name, null);
    for (const spot of secretSpots(entry.definition)) secrets.push({ scope, server: entry.name, projectRoot, ...spot });
    mcpServers.push({
      scope,
      name: entry.name,
      recordNames: names2,
      projectRoot,
      pluginId: null,
      definitionHash: entry.definition === null ? null : definitionHash(input.salt, entry.definition),
      enabled,
      managedFixed: managedHits(managedView, names2, entry.definition)
    });
  };
  for (const entry of claudeJson.userMcpServers) {
    const names2 = mcpRecordNames(entry.name, null);
    addServer("user", entry, null, everyContext.some((context) => mcpAllowed(context.mcp, names2, entry.definition)));
  }
  const mcpJsonStatus = /* @__PURE__ */ new Map();
  for (const ref of active) {
    const context = contexts.get(ref.normRoot);
    const seen = /* @__PURE__ */ new Set();
    for (const entry of context.mcp.project?.mcpServers ?? []) {
      const identity = `${entry.name}\0${entry.definition === null ? "" : definitionHash(input.salt, entry.definition) ?? "deep"}`;
      if (seen.has(identity)) continue;
      seen.add(identity);
      addServer("local", entry, ref.normRoot, mcpAllowed(context.mcp, mcpRecordNames(entry.name, null), entry.definition));
    }
    const file = join25(ref.root, ".mcp.json");
    const read = await readJson(file);
    const entries = read.status === "ok" ? mcpMapOf(read.value) : null;
    const status = read.status !== "ok" ? read.status : entries === null ? "unparsable" : "ok";
    mcpJsonStatus.set(ref.normRoot, status);
    if (status === "unparsable") problems.push({ kind: "unparsable", owner: "user", path: file, place: projectPlace(ref, file) });
    for (const entry of entries ?? []) {
      const approved = projectServerApproved(context.mcp, entry.name) && mcpAllowed(context.mcp, mcpRecordNames(entry.name, null), entry.definition);
      addServer("project", entry, ref.normRoot, approved);
    }
  }
  const claudeAiNames = [.../* @__PURE__ */ new Set([...claudeJson.claudeAiEverConnected, ...input.claudeAiNames.filter((n) => n.startsWith("claude.ai "))])].sort();
  for (const name of claudeAiNames) {
    const names2 = mcpRecordNames(name, null);
    mcpServers.push({ scope: "claude-ai", name, recordNames: names2, projectRoot: null, pluginId: null, definitionHash: null, enabled: mcpAllowed(global.mcp, names2, null), managedFixed: managedHits(managedView, names2, null) });
  }
  const projects = [];
  for (const ref of refs) {
    const layers = projectLayers.get(ref.normRoot);
    const projectView = viewOf(layers?.project.value ?? null);
    const localView = viewOf(layers?.local.value ?? null);
    const settingsStatus = layers === void 0 ? null : layerStatus(layers.project);
    const localSettingsStatus = layers === void 0 ? null : layerStatus(layers.local);
    const hasSettings = settingsStatus !== null && settingsStatus !== "missing";
    const hasLocalSettings = localSettingsStatus !== null && localSettingsStatus !== "missing";
    projects.push({
      root: ref.root,
      name: projectNames.get(ref.normRoot),
      normRoot: ref.normRoot,
      kind: ref.kind,
      exists: ref.exists,
      excluded: ref.excluded,
      cwds: ref.cwds,
      settingsStatus,
      localSettingsStatus,
      mcpJsonStatus: mcpJsonStatus.get(ref.normRoot) ?? null,
      hasSettings,
      hasLocalSettings,
      instructions: layers === void 0 ? emptyInstructionSet() : await readProjectInstructions(ref.root, globalRead.set, { homedir: input.homedir }),
      bypassInProject: projectView.bypass,
      bypassInLocal: localView.bypass,
      permissionConflicts: layers === void 0 ? 0 : conflictPairs(userView, settingsStatus === "ok" ? projectView : null, localSettingsStatus === "ok" ? localView : null)
    });
  }
  const managedPluginGuards = [];
  const userPluginGuards = [];
  const unreadablePlugins = [];
  for (const plugin of allPlugins) {
    if (!userScoped(plugin)) continue;
    const forced = managedView.enabledPlugins[plugin.id] === true;
    const userEnabled = !forced && userView.enabledPlugins[plugin.id] === true && pluginEnabledIn(global, plugin.id, plugin.defaultEnabled);
    if (!forced && !userEnabled) continue;
    if (plugin.hooksUnreadable) unreadablePlugins.push(plugin.id);
    for (const events of plugin.hookEvents) (forced ? managedPluginGuards : userPluginGuards).push(...preToolUseGuards(events, forced ? "managed-plugin" : "user-plugin", plugin.id));
  }
  const unreadableSettings = [];
  const settingsGuards = (layer, source) => layer.hookSources.flatMap(({ path, hooks }) => {
    if (hookMapValid(hooks)) return preToolUseGuards(hooks, source, null);
    unreadableSettings.push(path);
    return [];
  });
  const guards = [...settingsGuards(managedLayer, "managed"), ...managedPluginGuards, ...settingsGuards(userLayer, "user"), ...userPluginGuards];
  skills.sort((a, b) => cmp2(a.name, b.name) || SKILL_SCOPE_ORDER[a.scope] - SKILL_SCOPE_ORDER[b.scope] || cmp2(normalizePath(a.path), normalizePath(b.path)) || cmp2(a.pluginId, b.pluginId));
  mcpServers.sort((a, b) => cmp2(a.name, b.name) || MCP_SCOPE_ORDER[a.scope] - MCP_SCOPE_ORDER[b.scope] || cmp2(a.projectRoot, b.projectRoot) || cmp2(a.pluginId, b.pluginId) || cmp2(a.definitionHash, b.definitionHash));
  const uniqueProblems = [];
  for (const problem of new Map(problems.map((p) => [`${p.kind}\0${p.owner}\0${p.path}`, p])).values()) {
    uniqueProblems.push({ ...problem, realPath: (await entryInfo(problem.path)).realPath });
  }
  uniqueProblems.sort((a, b) => cmp2(a.path, b.path) || cmp2(a.kind, b.kind) || OWNER_ORDER[a.owner] - OWNER_ORDER[b.owner]);
  return {
    tool: "claude-code",
    home,
    claudeJson: claudeJson.status,
    globalInstructions: globalRead.set,
    globalMentions: globalRead.mentions,
    settings: {
      user: layerStatus(userLayer),
      managedParts: managedLayer.parts.map((part) => ({ path: part.path, status: part.status })),
      defaultMode: { user: userView.defaultMode, managed: managedView.defaultMode }
    },
    hooks: {
      guards,
      userDisableAll: userView.disableAllHooks,
      managedDisableAll: managedView.disableAllHooks,
      managedAllowManagedOnly: managedView.allowManagedHooksOnly,
      unreadablePlugins: unreadablePlugins.sort(),
      unreadableSettings
    },
    pluginsFile: pluginsScan.file,
    plugins,
    pluginsWithoutInstall,
    skills: skills.map((skill) => ({ ...skill, installKey: skillInstallKey(skill) })),
    mcpServers: mcpServers.map((server) => ({ ...server, installKey: mcpInstallKey(server) })),
    projects,
    problems: uniqueProblems,
    secrets: [...sortSecrets(secrets), ...await defaultCopySecrets(input)],
    unreadableDirs: [...new Set(unreadableDirs)].sort(),
    unreadableSkillPlaces: { user: unreadableSkillPlaces.user, projects: [...new Set(unreadableSkillPlaces.projects)].sort(), plugins: [...new Set(unreadableSkillPlaces.plugins)].sort() }
  };
}

// src/scan/codex.ts
import { isAbsolute as isAbsolute3, join as join29, relative as relative5, resolve as resolve10 } from "node:path";

// node_modules/smol-toml/dist/error.js
/*!
 * Copyright (c) Squirrel Chat et al., All rights reserved.
 * SPDX-License-Identifier: BSD-3-Clause
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 *
 * 1. Redistributions of source code must retain the above copyright notice, this
 *    list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice,
 *    this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 * 3. Neither the name of the copyright holder nor the names of its contributors
 *    may be used to endorse or promote products derived from this software without
 *    specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
 * ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
 * WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
 * DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
 * FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
 * DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
 * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
 * CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
 * OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */
function getLineColFromPtr(string, ptr) {
  let lines = string.slice(0, ptr).split(/\r?\n/);
  return [lines.length, lines.pop().length + 1];
}
function makeCodeBlock(string, line, column) {
  let lines = string.split(/\r?\n/);
  let codeblock = "";
  let numberLen = (Math.log10(line + 1) | 0) + 1;
  for (let i = line - 1; i <= line + 1; i++) {
    let l = lines[i - 1];
    if (!l)
      continue;
    codeblock += i.toString().padEnd(numberLen, " ");
    codeblock += ":  ";
    codeblock += l;
    codeblock += "\n";
    if (i === line) {
      codeblock += " ".repeat(numberLen + column + 2);
      codeblock += "^\n";
    }
  }
  return codeblock;
}
var TomlError = class _TomlError extends Error {
  line;
  column;
  codeblock;
  constructor(message, options) {
    const [line, column] = getLineColFromPtr(options.toml, options.ptr);
    const codeblock = makeCodeBlock(options.toml, line, column);
    super(`Invalid TOML document: ${message}

${codeblock}`, options);
    this.line = line;
    this.column = column;
    this.codeblock = codeblock;
  }
  /** @internal */
  static x(message, ctx, ptr) {
    throw new _TomlError(message, { toml: ctx.s, ptr: ptr ?? ctx.p });
  }
};

// node_modules/smol-toml/dist/primitive.js
/*!
 * Copyright (c) Squirrel Chat et al., All rights reserved.
 * SPDX-License-Identifier: BSD-3-Clause
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 *
 * 1. Redistributions of source code must retain the above copyright notice, this
 *    list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice,
 *    this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 * 3. Neither the name of the copyright holder nor the names of its contributors
 *    may be used to endorse or promote products derived from this software without
 *    specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
 * ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
 * WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
 * DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
 * FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
 * DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
 * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
 * CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
 * OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */
function parseString(ctx) {
  let startPtr = ctx.p;
  let c = ctx.s.charCodeAt(ctx.p++);
  let first = c;
  let isLiteral = c === 39;
  let isMultiline = c === ctx.s.charCodeAt(ctx.p) && c === ctx.s.charCodeAt(ctx.p + 1);
  if (isMultiline) {
    if ((c = ctx.s.charCodeAt(ctx.p += 2)) === 10)
      ctx.p++;
    else if (c === 13 && ctx.s.charCodeAt(ctx.p + 1) === 10)
      ctx.p += 2;
  }
  let parsed = "";
  let sliceStart = ctx.p;
  let state = 0;
  for (; ctx.p < ctx.s.length; ctx.p++) {
    c = ctx.s.charCodeAt(ctx.p);
    if (isMultiline && (c === 10 || c === 13 && ctx.s.charCodeAt(ctx.p + 1) === 10)) {
      state = state && 3;
    } else if (c < 32 && c !== 9 || c === 127) {
      TomlError.x("control characters are not allowed in strings", ctx);
    } else if ((!state || state === 3) && c === first && (!isMultiline || ctx.s.charCodeAt(ctx.p + 1) === first && ctx.s.charCodeAt(ctx.p + 2) === first)) {
      if (isMultiline) {
        if (ctx.s.charCodeAt(ctx.p + 3) === first)
          ctx.p++;
        if (ctx.s.charCodeAt(ctx.p + 3) === first)
          ctx.p++;
      }
      if (!state) {
        let s = ctx.s.slice(sliceStart, ctx.p);
        parsed = parsed ? parsed + s : s;
      }
      ctx.p += isMultiline ? 3 : 1;
      return parsed;
    } else if (!state) {
      if (!isLiteral && c === 92) {
        parsed += ctx.s.slice(sliceStart, sliceStart = ctx.p);
        state = 1;
      }
    } else if (state === 1) {
      if (c === 120 || c === 117 || c === 85) {
        let errPtr = ctx.p++ - 1;
        let value = 0;
        let len = c === 120 ? 2 : c === 117 ? 4 : 8;
        for (let j = 0; j < len; j++, ctx.p++) {
          let hex = ctx.s.charCodeAt(ctx.p);
          let digit = (
            /* 0-9 */
            hex >= 48 && hex <= 57 ? hex - 48 : (
              /* A-F */
              hex >= 65 && hex <= 70 ? hex - 65 + 10 : (
                /* a-f */
                hex >= 97 && hex <= 102 ? hex - 97 + 10 : -1
              )
            )
          );
          if (digit < 0)
            TomlError.x("invalid non-hex character in unicode escape", ctx);
          value = value << 4 | digit;
        }
        if (value < 0 || value > 1114111 || value >= 55296 && value <= 57343) {
          TomlError.x("invalid unicode escape", ctx, errPtr);
        }
        parsed += String.fromCodePoint(value);
        sliceStart = ctx.p--;
        state = 0;
      } else if (isMultiline && (c === 32 || c === 9)) {
        state = 2;
      } else {
        if (c === 98)
          parsed += "\b";
        else if (c === 116)
          parsed += "	";
        else if (c === 110)
          parsed += "\n";
        else if (c === 102)
          parsed += "\f";
        else if (c === 114)
          parsed += "\r";
        else if (c === 101)
          parsed += "\x1B";
        else if (c === 34)
          parsed += '"';
        else if (c === 92)
          parsed += "\\";
        else
          TomlError.x("unrecognised escape sequence", ctx);
        sliceStart = ctx.p + 1;
        state = 0;
      }
    } else if (c !== 32 && c !== 9) {
      if (state === 2)
        TomlError.x("invalid escape: only line-ending whitespace may be escaped", ctx, sliceStart);
      state = !isLiteral && c === 92 ? 1 : 0;
      sliceStart = ctx.p;
    }
  }
  TomlError.x("unfinished string", ctx, startPtr);
}

// node_modules/smol-toml/dist/date.js
/*!
 * Copyright (c) Squirrel Chat et al., All rights reserved.
 * SPDX-License-Identifier: BSD-3-Clause
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 *
 * 1. Redistributions of source code must retain the above copyright notice, this
 *    list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice,
 *    this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 * 3. Neither the name of the copyright holder nor the names of its contributors
 *    may be used to endorse or promote products derived from this software without
 *    specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
 * ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
 * WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
 * DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
 * FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
 * DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
 * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
 * CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
 * OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */
var DATE_TIME_RE = /^(\d{4}-\d{2}-\d{2})?[Tt ]?(?:(\d{2}):\d{2}(?::\d{2}(?:\.\d+)?)?)?(Z|z|[-+]\d{2}:\d{2})?$/i;
var TomlDate = class _TomlDate extends Date {
  #hasDate = false;
  #hasTime = false;
  #offset = null;
  constructor(date, fasttype, unsafeDelim) {
    let hasDate = true;
    let hasTime = true;
    let offset = "Z";
    let c;
    if (typeof date === "string") {
      if (fasttype)
        prep: {
          if (fasttype < 3) {
            if (+date.slice(11, 13) > 23) {
              date = "";
              break prep;
            }
            if (fasttype === 2) {
              offset = null;
              date += "Z";
            } else if ((c = date.charCodeAt(date.length - 1)) !== 90 && c !== 122) {
              offset = date.slice(date.length - 6);
            }
            if (unsafeDelim)
              date = date.slice(0, 10) + "T" + date.slice(11);
          } else if (fasttype === 4) {
            date = +date.slice(0, 2) > 23 ? "" : `0000-01-01T${date}Z`;
          }
          hasDate = fasttype !== 4;
          hasTime = fasttype !== 3;
        }
      else {
        let match = date.match(DATE_TIME_RE);
        if (match) {
          if (!match[1]) {
            hasDate = false;
            date = `0000-01-01T${date}`;
          }
          hasTime = !!match[2];
          hasTime && date[10] === " " && (date = date.replace(" ", "T"));
          if (match[2] && +match[2] > 23) {
            date = "";
          } else {
            offset = match[3] || null;
            if (!offset && hasTime)
              date += "Z";
          }
        } else {
          date = "";
        }
      }
    }
    super(date);
    if (!isNaN(this.getTime())) {
      this.#hasDate = hasDate;
      this.#hasTime = hasTime;
      this.#offset = offset;
    }
  }
  isDateTime() {
    return this.#hasDate && this.#hasTime;
  }
  isLocal() {
    return !this.#hasDate || !this.#hasTime || !this.#offset;
  }
  isDate() {
    return this.#hasDate && !this.#hasTime;
  }
  isTime() {
    return this.#hasTime && !this.#hasDate;
  }
  isValid() {
    return this.#hasDate || this.#hasTime;
  }
  toISOString() {
    let iso = super.toISOString();
    if (this.isDate())
      return iso.slice(0, 10);
    if (this.isTime())
      return iso.slice(11, 23);
    if (this.#offset === null)
      return iso.slice(0, -1);
    if (this.#offset === "Z" || this.#offset === "z")
      return iso;
    let offset = +this.#offset.slice(1, 3) * 60 + +this.#offset.slice(4, 6);
    offset = this.#offset[0] === "-" ? offset : -offset;
    let offsetDate = new Date(this.getTime() - offset * 6e4);
    return offsetDate.toISOString().slice(0, -1) + this.#offset;
  }
  static wrapAsOffsetDateTime(jsDate, offset = "Z") {
    let date = new _TomlDate(jsDate);
    date.#offset = offset;
    return date;
  }
  static wrapAsLocalDateTime(jsDate) {
    let date = new _TomlDate(jsDate);
    date.#offset = null;
    return date;
  }
  static wrapAsLocalDate(jsDate) {
    let date = new _TomlDate(jsDate);
    date.#hasTime = false;
    date.#offset = null;
    return date;
  }
  static wrapAsLocalTime(jsDate) {
    let date = new _TomlDate(jsDate);
    date.#hasDate = false;
    date.#offset = null;
    return date;
  }
};

// node_modules/smol-toml/dist/extract.js
/*!
 * Copyright (c) Squirrel Chat et al., All rights reserved.
 * SPDX-License-Identifier: BSD-3-Clause
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 *
 * 1. Redistributions of source code must retain the above copyright notice, this
 *    list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice,
 *    this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 * 3. Neither the name of the copyright holder nor the names of its contributors
 *    may be used to endorse or promote products derived from this software without
 *    specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
 * ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
 * WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
 * DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
 * FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
 * DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
 * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
 * CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
 * OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */
function isDigit(char, base = 10) {
  return base === 16 ? char > 47 && char < 58 || char > 64 && char < 71 || char > 96 && char < 103 : char > 47 && char < 48 + base;
}
function isEndOfValue(char, delim) {
  return char === 32 || char === 9 || char === 10 || char === 13 || // Structure end or next value delimiter
  delim && (char === delim || char === 44) || // Comment
  char === 35;
}
function extractValue(ctx, end) {
  let errPtr = ctx.p;
  let c = ctx.s.charCodeAt(ctx.p);
  if (c === 91 || c === 123) {
    ctx.d-- || TomlError.x("document contains excessively nested structures. aborting.", ctx);
    let value = c === 91 ? parseArray(ctx) : parseInlineTable(ctx);
    ctx.d++;
    return value;
  }
  if (c === 34 || c === 39) {
    return parseString(ctx);
  }
  if (c === 116) {
    if (ctx.s.charCodeAt(++ctx.p) !== 114 || ctx.s.charCodeAt(++ctx.p) !== 117 || ctx.s.charCodeAt(++ctx.p) !== 101)
      TomlError.x("invalid value", ctx, errPtr);
    return ctx.p++, true;
  }
  if (c === 102) {
    if (ctx.s.charCodeAt(++ctx.p) !== 97 || ctx.s.charCodeAt(++ctx.p) !== 108 || ctx.s.charCodeAt(++ctx.p) !== 115 || ctx.s.charCodeAt(++ctx.p) !== 101)
      TomlError.x("invalid value", ctx, errPtr);
    return ctx.p++, false;
  }
  if (c === 43 || c === 45) {
    return parseNumber(ctx, ctx.p, ctx.s.charCodeAt(++ctx.p), 44 - c, end);
  }
  if (ctx.s.charCodeAt(ctx.p + 4) === 45 && ctx.s.charCodeAt(ctx.p + 7) === 45) {
    return parseDate(ctx, c, end);
  }
  if (ctx.s.charCodeAt(ctx.p + 2) === 58) {
    return parseTime(ctx, c, end);
  }
  return parseNumber(ctx, ctx.p, c, 0, end);
}
function parseNumber(ctx, startPtr, startChr, sign, endChr) {
  let c = startChr;
  let state = 0;
  let hasUnderscores = false;
  if (c === 105) {
    if (ctx.s.charCodeAt(++ctx.p) !== 110 || ctx.s.charCodeAt(++ctx.p) !== 102)
      TomlError.x("invalid value", ctx, startPtr);
    return ctx.p++, (sign || 1) / 0;
  }
  if (c === 110) {
    if (ctx.s.charCodeAt(++ctx.p) !== 97 || ctx.s.charCodeAt(++ctx.p) !== 110)
      TomlError.x("invalid value", ctx, startPtr);
    return ctx.p++, NaN;
  }
  if (c === 48) {
    if (++ctx.p >= ctx.s.length || isEndOfValue(c = ctx.s.charCodeAt(ctx.p), endChr))
      return ctx.bi === true ? 0n : 0;
    if (!sign) {
      if (c === 120)
        return parseIntegerBaseN(ctx, startPtr, 16, endChr);
      else if (c === 98)
        return parseIntegerBaseN(ctx, startPtr, 2, endChr);
      else if (c === 111)
        return parseIntegerBaseN(ctx, startPtr, 8, endChr);
    }
    if (c === 46)
      state = 2;
    else if (c === 101 || c === 69)
      state = 4;
    else
      TomlError.x("illegal leading zero", ctx, startPtr);
  } else if (!isDigit(c))
    TomlError.x("invalid value", ctx, startPtr);
  while (++ctx.p < ctx.s.length && (c = ctx.s.charCodeAt(ctx.p), !isEndOfValue(c, endChr))) {
    if (!state)
      state = 1;
    if (c === 95) {
      if (!(state & 1))
        TomlError.x("illegal underscore", ctx);
      state += 11;
      hasUnderscores = true;
    } else if (state === 1 && c === 46)
      state = 2;
    else if ((state === 1 || state === 3) && (c === 101 || c === 69))
      state = 4;
    else if (state === 4 && (c === 43 || c === 45)) {
      state = 6;
    } else if (!isDigit(c))
      TomlError.x(`illegal character in numeric literal`, ctx);
    else if (state > 9)
      state -= 11;
    else if (!(state & 1))
      state++;
  }
  if (!state) {
    let val = (startChr - 48) * (sign || 1);
    return ctx.bi === true ? BigInt(val) : val;
  }
  if (!(state & 1))
    TomlError.x("unfinished numeric value", ctx, startPtr);
  let str6 = ctx.s.slice(startPtr, ctx.p);
  if (hasUnderscores)
    str6 = str6.replaceAll("_", "");
  return state > 1 ? parseFloat(str6) : parseInteger(ctx, str6, 10, startPtr);
}
function parseIntegerBaseN(ctx, startPtr, base, endChr) {
  let c, underscore = 1;
  while (++ctx.p < ctx.s.length && (c = ctx.s.charCodeAt(ctx.p), !isEndOfValue(c, endChr))) {
    if (c === 95) {
      if (underscore & 1)
        TomlError.x("illegal underscore", ctx);
      underscore = 3;
    } else if (!isDigit(c, base))
      TomlError.x(`illegal character in numeric literal`, ctx);
    else if (underscore & 1)
      underscore--;
  }
  if (underscore & 1)
    TomlError.x("unfinished numeric value", ctx);
  let str6 = ctx.s.slice(startPtr + 2, ctx.p);
  if (underscore)
    str6 = str6.replaceAll("_", "");
  return parseInteger(ctx, str6, base, startPtr);
}
function parseInteger(ctx, str6, base, startPtr) {
  if (ctx.bi !== true)
    int: {
      let val = parseInt(str6, base);
      if (!Number.isSafeInteger(val)) {
        if (ctx.bi)
          break int;
        TomlError.x("integer value cannot be represented losslessly", ctx, startPtr);
      }
      return val;
    }
  return base === 10 ? BigInt(str6) : BigInt((base === 2 ? "0b" : base === 8 ? "0o" : "0x") + str6);
}
function parseDate(ctx, c, endChr) {
  let startPtr = ctx.p++, unsafeSeparator;
  if (!isDigit(c) || !isDigit(ctx.s.charCodeAt(ctx.p++)) || !isDigit(ctx.s.charCodeAt(ctx.p++)) || !isDigit(ctx.s.charCodeAt(ctx.p++))) {
    return parseNumber(ctx, ctx.p = startPtr, c, 0, endChr);
  }
  ctx.p += 5;
  if (!isDigit(ctx.s.charCodeAt(ctx.p++)))
    TomlError.x("invalid date-time: date part is malformed", ctx, startPtr);
  if (ctx.p >= ctx.s.length || ((c = ctx.s.charCodeAt(ctx.p)) !== 32 || (unsafeSeparator = true, !isDigit(ctx.s.charCodeAt(ctx.p + 1)))) && c !== 84 && c !== 116) {
    let t2 = ctx.s.slice(startPtr, ctx.p);
    return readDate(ctx, t2, 3, false, startPtr);
  }
  if (ctx.s.charCodeAt(ctx.p += 3) !== 58)
    TomlError.x("invalid date-time: time part is malformed", ctx, startPtr);
  if (ctx.s.charCodeAt(ctx.p += 3) === 58)
    ctx.p += 3;
  if (ctx.s.charCodeAt(ctx.p) === 46)
    while (isDigit(ctx.s.charCodeAt(++ctx.p)))
      ;
  if (c = ctx.s.charCodeAt(ctx.p)) {
    if (c === 90 || c === 122) {
      let t2 = ctx.s.slice(startPtr, ++ctx.p);
      return readDate(ctx, t2, 1, unsafeSeparator, startPtr, "[+00:00]");
    }
    if (c === 43 || c === 45) {
      let t2 = ctx.s.slice(startPtr, ctx.p += 6);
      return readDate(ctx, t2, 1, unsafeSeparator, startPtr, !ctx.ld && "[" + ctx.s.slice(ctx.p - 6, ctx.p) + "]");
    }
  }
  let t = ctx.s.slice(startPtr, ctx.p);
  return readDate(ctx, t, 2, unsafeSeparator, startPtr);
}
function parseTime(ctx, c, endChr) {
  let start = ctx.p;
  if (!isDigit(c) || !isDigit(ctx.s.charCodeAt(++ctx.p))) {
    return parseNumber(ctx, --ctx.p, c, 0, endChr);
  }
  if (ctx.s.charCodeAt(ctx.p += 4) === 58)
    ctx.p += 3;
  if (ctx.s.charCodeAt(ctx.p) === 46)
    while (isDigit(ctx.s.charCodeAt(++ctx.p)))
      ;
  let t = ctx.s.slice(start, ctx.p);
  return readDate(ctx, t, 4, false, start);
}
function readDate(ctx, str6, type, unsafeDelim, errPtr, temporalSuffix) {
  if (ctx.ld) {
    let date = new TomlDate(str6, type, unsafeDelim);
    if (!date.isValid())
      TomlError.x("invalid date", ctx, errPtr);
    return date;
  }
  try {
    if (temporalSuffix)
      str6 += temporalSuffix;
    switch (type) {
      case 1:
        return Temporal.ZonedDateTime.from(str6);
      case 2:
        return Temporal.PlainDateTime.from(str6);
      case 3:
        return Temporal.PlainDate.from(str6);
      case 4:
        return Temporal.PlainTime.from(str6);
    }
  } catch (e) {
    TomlError.x(e instanceof Error ? e.message : "" + e, ctx, errPtr);
  }
}

// node_modules/smol-toml/dist/util.js
/*!
 * Copyright (c) Squirrel Chat et al., All rights reserved.
 * SPDX-License-Identifier: BSD-3-Clause
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 *
 * 1. Redistributions of source code must retain the above copyright notice, this
 *    list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice,
 *    this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 * 3. Neither the name of the copyright holder nor the names of its contributors
 *    may be used to endorse or promote products derived from this software without
 *    specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
 * ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
 * WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
 * DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
 * FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
 * DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
 * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
 * CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
 * OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */
function skipComment(ctx) {
  for (; ctx.p < ctx.s.length; ctx.p++) {
    let c = ctx.s.charCodeAt(ctx.p);
    if (c === 10)
      break;
    if (c === 13 && ctx.s.charCodeAt(ctx.p + 1) === 10) {
      ctx.p++;
      break;
    }
    if (c < 32 && c !== 9 || c === 127) {
      TomlError.x("control characters are not allowed in comments", ctx);
    }
  }
}
function skipVoid(ctx, banNewLines, banComments) {
  let c;
  while (ctx.p < ctx.s.length) {
    while (ctx.p < ctx.s.length && ((c = ctx.s.charCodeAt(ctx.p)) === 32 || c === 9 || !banNewLines && (c === 10 || c === 13 && ctx.s.charCodeAt(ctx.p + 1) === 10)))
      ctx.p++;
    if (banComments || c !== 35)
      break;
    skipComment(ctx);
  }
}

// node_modules/smol-toml/dist/struct.js
/*!
 * Copyright (c) Squirrel Chat et al., All rights reserved.
 * SPDX-License-Identifier: BSD-3-Clause
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 *
 * 1. Redistributions of source code must retain the above copyright notice, this
 *    list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice,
 *    this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 * 3. Neither the name of the copyright holder nor the names of its contributors
 *    may be used to endorse or promote products derived from this software without
 *    specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
 * ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
 * WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
 * DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
 * FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
 * DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
 * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
 * CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
 * OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */
function parseKey(ctx, end = 61) {
  let startPtr;
  let state = 0;
  let parsed = [];
  let sliceStart;
  let c = ctx.s.charCodeAt(startPtr = ctx.p);
  do {
    if (c === end) {
      if (!state)
        TomlError.x("unexpected end of key", ctx);
      if (state === 1)
        parsed.push(ctx.s.slice(sliceStart, ctx.p));
      return ctx.p++, parsed;
    } else if (c === 46) {
      if (!state)
        TomlError.x("illegal empty bare key", ctx);
      if (state === 1)
        parsed.push(ctx.s.slice(sliceStart, ctx.p));
      state = 0;
    } else if (!state && (c === 34 || c === 39)) {
      if (c === ctx.s.charCodeAt(ctx.p + 1) && c === ctx.s.charCodeAt(ctx.p + 2))
        TomlError.x("illegal quoted key: multiline strings are not allowed", ctx);
      parsed.push(parseString(ctx));
      state = 2;
      ctx.p--;
    } else if (c === 32 || c === 9) {
      if (state === 1) {
        parsed.push(ctx.s.slice(sliceStart, ctx.p));
        state = 2;
      }
    } else if (state === 2 || c < 48 && c !== 45 || c > 57 && c < 65 || c > 90 && c < 97 && c !== 95 || c > 122) {
      TomlError.x("illegal character in key", ctx);
    } else if (!state) {
      state = 1;
      sliceStart = ctx.p;
    }
  } while (c = ctx.s.charCodeAt(++ctx.p));
  TomlError.x("incomplete key-value: cannot find end of key", ctx, startPtr);
}
function parseInlineTable(ctx) {
  let startPtr = ctx.p++;
  let res = /* @__PURE__ */ Object.create(null);
  let seen = /* @__PURE__ */ new Set();
  let c;
  while (ctx.p < ctx.s.length) {
    skipVoid(ctx);
    if ((c = ctx.s.charCodeAt(ctx.p)) === 125) {
      ctx.p++;
      return res;
    }
    let k;
    let t = res;
    let hasOwn = false;
    let errPtr = ctx.p;
    let key = parseKey(ctx);
    for (let i = 0; i < key.length; i++) {
      if (i)
        t = hasOwn ? t[k] : t[k] = /* @__PURE__ */ Object.create(null);
      k = key[i];
      if ((hasOwn = Object.hasOwn(t, k)) && (typeof t[k] !== "object" || seen.has(t[k]))) {
        TomlError.x("trying to redefine an already defined value", ctx, errPtr);
      }
      let unsafe = k === "__proto__";
      if (ctx.uk && (unsafe || k === "constructor")) {
        t = ctx.uk !== 1 && TomlError.x("document contains an unsafe property", ctx, errPtr);
        break;
      }
      if (!hasOwn && unsafe) {
        Object.defineProperty(t, k, { enumerable: true, configurable: true, writable: true });
      }
    }
    if (hasOwn) {
      TomlError.x("trying to redefine an already defined value", ctx, errPtr);
    }
    skipVoid(ctx, true, true);
    let value = extractValue(
      ctx,
      125
      /* } */
    );
    if (t && typeof (t[k] = value) === "object")
      seen.add(value);
    skipVoid(ctx);
    if ((c = ctx.s.charCodeAt(ctx.p++)) === 125) {
      return res;
    }
    if (c !== 44)
      TomlError.x("expected comma or end of structure", ctx, ctx.p - 1);
  }
  TomlError.x("unfinished table", ctx, startPtr);
}
function parseArray(ctx) {
  let startPtr = ctx.p++;
  let res = [];
  let c;
  while (ctx.p < ctx.s.length) {
    skipVoid(ctx);
    if ((c = ctx.s.charCodeAt(ctx.p)) === 93) {
      ctx.p++;
      return res;
    }
    res.push(extractValue(
      ctx,
      93
      /* ] */
    ));
    skipVoid(ctx);
    if ((c = ctx.s.charCodeAt(ctx.p++)) === 93) {
      return res;
    }
    if (c !== 44)
      TomlError.x("expected comma or end of structure", ctx, ctx.p - 1);
  }
  TomlError.x("unfinished array", ctx, startPtr);
}

// node_modules/smol-toml/dist/parse.js
/*!
 * Copyright (c) Squirrel Chat et al., All rights reserved.
 * SPDX-License-Identifier: BSD-3-Clause
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 *
 * 1. Redistributions of source code must retain the above copyright notice, this
 *    list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice,
 *    this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 * 3. Neither the name of the copyright holder nor the names of its contributors
 *    may be used to endorse or promote products derived from this software without
 *    specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
 * ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
 * WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
 * DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
 * FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
 * DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
 * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
 * CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
 * OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */
function peekTable(ctx, key, table, meta, type) {
  let t = table;
  let m = meta;
  let k;
  let hasOwn = false;
  let state;
  for (let i = 0; i < key.length; i++) {
    if (i) {
      t = hasOwn ? t[k] : t[k] = /* @__PURE__ */ Object.create(null);
      m = (state = m[k]).c;
      if (type === 0 && (state.t === 1 || state.t === 2)) {
        return null;
      }
      if (state.t === 2) {
        let l = t.length - 1;
        t = t[l];
        m = m[l].c;
      }
    }
    k = key[i];
    if ((hasOwn = Object.hasOwn(t, k)) && m[k]?.t === 0 && m[k]?.d) {
      return null;
    }
    if (!hasOwn) {
      let unsafe = k === "__proto__";
      if (ctx.uk && (unsafe || k === "constructor"))
        return false;
      if (unsafe) {
        Object.defineProperty(t, k, { enumerable: true, configurable: true, writable: true });
        Object.defineProperty(m, k, { enumerable: true, configurable: true, writable: true });
      }
      m[k] = {
        t: i < key.length - 1 && type === 2 ? 3 : type,
        d: false,
        i: 0,
        c: /* @__PURE__ */ Object.create(null)
      };
    }
  }
  state = m[k];
  if (state.t !== type && !(type === 1 && state.t === 3)) {
    return null;
  }
  if (type === 2) {
    if (!state.d) {
      state.d = true;
      t[k] = [];
    }
    t[k].push(t = /* @__PURE__ */ Object.create(null));
    state.c[state.i++] = state = { t: 1, d: false, i: 0, c: /* @__PURE__ */ Object.create(null) };
  }
  if (state.d) {
    return null;
  }
  state.d = true;
  if (type === 1) {
    t = hasOwn ? t[k] : t[k] = /* @__PURE__ */ Object.create(null);
  } else if (type === 0 && hasOwn) {
    return null;
  }
  return [k, t, state.c];
}
function validateTablePeek(ctx, peek, ptr) {
  if (peek === null || ctx.uk === 2)
    TomlError.x(peek === null ? "trying to redefine an already defined table or value" : "document contains an unsafe property", ctx, ptr);
}
function parse3(toml, options = {}) {
  let ctx = {
    s: toml,
    p: 0,
    d: options.maxDepth ?? 1e3,
    bi: options.integersAsBigInt ?? false,
    ld: options.useLegacyDate ?? true,
    uk: options.unsafeKeyBehaviour === "throw" ? 2 : options.unsafeKeyBehaviour === "drop" ? 1 : 0
  };
  let res = /* @__PURE__ */ Object.create(null);
  let meta = /* @__PURE__ */ Object.create(null);
  let tmp;
  let skipping = false;
  let tbl = res;
  let m = meta;
  if (toml.charCodeAt(0) === 65279)
    ctx.p++;
  skipVoid(ctx);
  while (ctx.p < toml.length) {
    if (toml.charCodeAt(ctx.p) === 91) {
      let isTableArray = toml.charCodeAt(++ctx.p) === 91;
      tmp = ctx.p += +isTableArray;
      skipping = false;
      let k = parseKey(
        ctx,
        93
        /* ] */
      );
      if (isTableArray) {
        if (toml.charCodeAt(ctx.p) !== 93) {
          TomlError.x("expected end of table array declaration", ctx);
        }
        ctx.p++;
      }
      let p = peekTable(
        ctx,
        k,
        res,
        meta,
        isTableArray ? 2 : 1
        /* Type.EXPLICIT */
      );
      if (!p) {
        validateTablePeek(ctx, p, tmp);
        skipping = true;
      } else {
        m = p[2];
        tbl = p[1];
      }
    } else {
      tmp = ctx.p;
      let k = parseKey(ctx);
      let p = peekTable(
        ctx,
        k,
        tbl,
        m,
        0
        /* Type.DOTTED */
      );
      if (!p && !skipping)
        validateTablePeek(ctx, p, tmp);
      skipVoid(ctx, true, true);
      let v = extractValue(ctx, void 0);
      if (p && !skipping)
        p[1][p[0]] = v;
    }
    skipVoid(ctx, true);
    if (ctx.p < toml.length && (tmp = toml.charCodeAt(ctx.p)) !== 10 && (tmp !== 13 || toml.charCodeAt(ctx.p + 1) !== 10)) {
      TomlError.x("each key-value declaration must be followed by an end-of-line", ctx);
    }
    skipVoid(ctx);
  }
  return res;
}

// node_modules/smol-toml/dist/stringify.js
/*!
 * Copyright (c) Squirrel Chat et al., All rights reserved.
 * SPDX-License-Identifier: BSD-3-Clause
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 *
 * 1. Redistributions of source code must retain the above copyright notice, this
 *    list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice,
 *    this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 * 3. Neither the name of the copyright holder nor the names of its contributors
 *    may be used to endorse or promote products derived from this software without
 *    specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
 * ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
 * WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
 * DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
 * FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
 * DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
 * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
 * CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
 * OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */
var HAS_WELLFORMED = !!"".isWellFormed;

// node_modules/smol-toml/dist/index.js
/*!
 * Copyright (c) Squirrel Chat et al., All rights reserved.
 * SPDX-License-Identifier: BSD-3-Clause
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 *
 * 1. Redistributions of source code must retain the above copyright notice, this
 *    list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice,
 *    this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 * 3. Neither the name of the copyright holder nor the names of its contributors
 *    may be used to endorse or promote products derived from this software without
 *    specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
 * ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
 * WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
 * DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
 * FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
 * DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
 * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
 * CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
 * OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

// src/scan/codex-config.ts
var isTable = (value) => isObject5(value) && !(value instanceof Date);
var isBool = (value) => typeof value === "boolean";
var isText = (value) => typeof value === "string";
var optional = (value, check) => value === void 0 || value === null || check(value);
var tableOf = (value, each) => isTable(value) && Object.values(value).every(each);
var isNonNegativeInteger = (value) => typeof value === "number" && Number.isInteger(value) && value >= 0 || typeof value === "bigint" && value >= 0n;
var MAX_CONFIG_DEPTH = 128;
var I64_MIN = -(2n ** 63n);
var I64_MAX = 2n ** 63n - 1n;
function exceedsLimits(value, maxDepth = MAX_CONFIG_DEPTH) {
  const stack = [[value, 0]];
  while (stack.length > 0) {
    const [item2, depth] = stack.pop();
    if (typeof item2 === "bigint") {
      if (item2 < I64_MIN || item2 > I64_MAX) return true;
      continue;
    }
    const children = Array.isArray(item2) ? item2 : isTable(item2) ? Object.values(item2) : null;
    if (children === null) continue;
    if (depth >= maxDepth) return true;
    for (const child of children) stack.push([child, depth + 1]);
  }
  return false;
}
function parseCodexConfig(text) {
  let value;
  try {
    value = parse3(text, { integersAsBigInt: "asNeeded" });
  } catch {
    return null;
  }
  return exceedsLimits(value) ? null : value;
}
var HTTP_KEYS = ["url", "bearer_token_env_var", "bearer_token", "http_headers_helper", "http_headers", "env_http_headers", "oauth", "oauth_resource", "auth"];
var STDIO_KEYS = ["args", "env", "env_vars", "cwd", "bearer_token"];
function codexServerShapeOk(server) {
  if (!isTable(server) || !optional(server.enabled, isBool)) return false;
  const has = (key) => server[key] !== void 0 && server[key] !== null;
  if (has("command")) return isText(server.command) && !HTTP_KEYS.some(has);
  if (has("url")) return isText(server.url) && !STDIO_KEYS.some(has);
  return false;
}
var approvalShapeOk = (value) => value === void 0 || isText(value) && value !== "untrusted" || isTable(value) && Object.keys(value).length === 1 && isTable(value.granular);
var pluginShapeOk = (plugin) => isTable(plugin) && optional(plugin.enabled, isBool) && optional(plugin.mcp_servers, (servers) => tableOf(servers, (server) => isTable(server) && optional(server.enabled, isBool)));
var skillsShapeOk = (skills) => optional(skills, (value) => isTable(value) && optional(value.config, (list) => Array.isArray(list) && list.every((entry) => isTable(entry) && isBool(entry.enabled) && optional(entry.path, isText) && optional(entry.name, isText))));
function codexConfigShapeOk(doc) {
  return approvalShapeOk(doc.approval_policy) && optional(doc.sandbox_mode, isText) && optional(doc.default_permissions, isText) && optional(doc.mcp_servers, (servers) => tableOf(servers, codexServerShapeOk)) && optional(doc.plugins, (plugins) => tableOf(plugins, pluginShapeOk)) && skillsShapeOk(doc.skills) && optional(doc.features, (features) => isTable(features) && optional(features.plugins, isBool)) && optional(doc.projects, (projects) => tableOf(projects, (project) => isTable(project) && optional(project.trust_level, isText))) && optional(doc.project_doc_fallback_filenames, (names2) => Array.isArray(names2) && names2.every(isText)) && optional(doc.project_doc_max_bytes, isNonNegativeInteger);
}
async function readCodexConfig(path) {
  const read = await readText(path);
  if (read.status !== "ok") return read;
  const value = parseCodexConfig(read.text);
  return value !== null && codexConfigShapeOk(value) ? { status: "ok", value } : { status: "unparsable" };
}
function mergeInto(base, top) {
  const out = /* @__PURE__ */ Object.create(null);
  for (const [key, value] of Object.entries(base)) out[key] = value;
  for (const [key, value] of Object.entries(top)) {
    const below = out[key];
    out[key] = isTable(below) && isTable(value) ? mergeInto(below, value) : value;
  }
  return out;
}
function mergeCodexLayers(layers) {
  return layers.reduce((merged, layer) => mergeInto(merged, layer), /* @__PURE__ */ Object.create(null));
}
function tomlToJson(value) {
  if (typeof value === "bigint") return { $bigint: value.toString() };
  if (typeof value === "number" && !Number.isFinite(value)) return { $float: Number.isNaN(value) ? "nan" : value > 0 ? "inf" : "-inf" };
  if (value instanceof Date) return { $datetime: value.toISOString() };
  if (Array.isArray(value)) return value.map(tomlToJson);
  if (isTable(value)) {
    const out = /* @__PURE__ */ Object.create(null);
    for (const [key, item2] of Object.entries(value)) out[key] = tomlToJson(item2);
    return out;
  }
  return value;
}

// src/scan/codex-instructions.ts
import { join as join26 } from "node:path";
var NAMES = ["AGENTS.override.md", "AGENTS.md"];
async function readCodexGlobalInstructions(codexHome2, mentionTargets) {
  const unreadable = [];
  for (const name of NAMES) {
    const path = join26(codexHome2, name);
    if (!(await entryInfo(path)).isFile) continue;
    const read = await readText(path);
    if (read.status === "unreadable") unreadable.push(path);
    if (read.status !== "ok" || !/\S/u.test(read.text)) continue;
    const found = await readInstructionSet([path], mentionTargets);
    found.set.unreadable.unshift(...unreadable);
    return found;
  }
  const set = emptyInstructionSet();
  set.unreadable.push(...unreadable);
  return { set, mentions: /* @__PURE__ */ Object.create(null) };
}
async function readCodexProjectInstructions(root, fallback) {
  for (const name of [...NAMES, ...fallback]) {
    const path = join26(root, name);
    if ((await entryInfo(path)).isFile) return (await readInstructionSet([path])).set;
  }
  return emptyInstructionSet();
}

// src/scan/codex-mcp.ts
var serversOf = (layer) => isTable(layer.mcp_servers) ? layer.mcp_servers : {};
var cmp3 = (a, b) => (a ?? "") < (b ?? "") ? -1 : (a ?? "") > (b ?? "") ? 1 : 0;
var SCOPE_ORDER5 = { user: 0, local: 1, project: 2, plugin: 3, "claude-ai": 4 };
function hashOf(salt, definition) {
  if (!isTable(definition)) return null;
  const copy2 = /* @__PURE__ */ Object.create(null);
  for (const [key, value] of Object.entries(definition)) if (key !== "enabled") copy2[key] = value;
  return definitionHash(salt, tomlToJson(copy2));
}
function pluginServerOn(context, id, name, declared) {
  const plugins = isTable(context.merged.plugins) ? context.merged.plugins : {};
  const entry = plugins[id];
  const policies = isTable(entry) && isTable(entry.mcp_servers) ? entry.mcp_servers : {};
  const policy = policies[name];
  return isTable(policy) ? policy.enabled !== false && !Object.hasOwn(policy, "ema_auth") : declared.enabled !== false;
}
function codexMcpSecrets(user, projects) {
  const secrets = [];
  const add = (scope, projectRoot, layer) => {
    for (const [name, definition] of Object.entries(serversOf(layer))) {
      if (!isTable(definition)) continue;
      for (const spot of secretSpots(tomlToJson(definition))) secrets.push({ scope, server: name, projectRoot, ...spot });
    }
  };
  add("user", null, user);
  for (const project of projects) add("project", project.normRoot, project.layer);
  return sortSecrets(secrets);
}
function codexMcpFacts(input) {
  const facts = [];
  const base = { managedFixed: false };
  for (const [name, definition] of Object.entries(serversOf(input.user))) {
    facts.push({ ...base, scope: "user", name, recordNames: [name], projectRoot: null, pluginId: null, definitionHash: hashOf(input.salt, definition), enabled: isTable(definition) && definition.enabled !== false });
  }
  for (const project of input.projects) {
    const context = input.contexts.find((c) => c.projectRoot === project.normRoot);
    const merged = context === void 0 ? {} : serversOf(context.merged);
    for (const name of Object.keys(serversOf(project.layer))) {
      const definition = merged[name];
      facts.push({ ...base, scope: "project", name, recordNames: [name], projectRoot: project.normRoot, pluginId: null, definitionHash: hashOf(input.salt, definition), enabled: isTable(definition) && definition.enabled !== false });
    }
  }
  for (const [id, servers] of input.pluginServers) {
    for (const server of servers) {
      const enabled = input.contexts.some((context) => {
        if (!context.plugins.includes(id) || Object.hasOwn(serversOf(context.merged), server.name)) return false;
        const winner = [...context.plugins].sort().find((other) => (input.pluginServers.get(other) ?? []).some((s) => s.name === server.name));
        return winner === id && pluginServerOn(context, id, server.name, server.definition);
      });
      facts.push({ ...base, scope: "plugin", name: server.name, recordNames: [server.name], projectRoot: null, pluginId: id, definitionHash: hashOf(input.salt, server.definition), enabled });
    }
  }
  return facts.sort((a, b) => cmp3(a.name, b.name) || SCOPE_ORDER5[a.scope] - SCOPE_ORDER5[b.scope] || cmp3(a.projectRoot, b.projectRoot) || cmp3(a.pluginId, b.pluginId) || cmp3(a.definitionHash, b.definitionHash));
}

// src/scan/codex-plugins.ts
import { join as join28, relative as relative4, resolve as resolve8, sep } from "node:path";
import { lstat as lstat7 } from "node:fs/promises";

// src/scan/codex-skills.ts
import { readFile as readFile11 } from "node:fs/promises";
import { basename as basename8, dirname as dirname5, join as join27 } from "node:path";
var MAX_DEPTH = 6;
var LIMITS = { maxDirectories: 2e3, maxEntries: 2e4 };
var CODEX_MANIFEST_PATHS = [".codex-plugin/plugin.json", ".claude-plugin/plugin.json", ".cursor-plugin/plugin.json"];
var MANIFEST_DIRS = CODEX_MANIFEST_PATHS.map((path) => path.split("/")[0]);
function codexFrontmatterOk(bytes) {
  if (bytes[0] === 239 && bytes[1] === 187 && bytes[2] === 191) return false;
  const front = parseFrontmatter(bytes.toString("utf8"));
  if (!front.present) return false;
  const description2 = front.fields.description;
  if (description2 !== void 0) return description2.split(/\s+/u).some((part) => part !== "");
  return front.unreadable.includes("description") || front.unreadable.includes("name");
}
async function manifestNamespace(pluginRoot) {
  for (const relative7 of CODEX_MANIFEST_PATHS) {
    const path = join27(pluginRoot, ...relative7.split("/"));
    if (!(await entryInfo(path)).isFile) continue;
    const read = await readText(path);
    if (read.status !== "ok") return null;
    try {
      const value = JSON.parse(read.text);
      const name = value?.name === void 0 ? "" : value.name;
      if (typeof name !== "string") return null;
      return name.trim() === "" ? basename8(pluginRoot) : name;
    } catch {
      return null;
    }
  }
  return null;
}
var squash = (text) => text.split(/\s+/u).filter((part) => part !== "").join(" ");
async function scanCodexSkillRoot(root, limits = LIMITS, namespace = null) {
  const out = { skills: [], danglingLinks: [], unreadableDirs: [], truncated: false };
  const rootInfo = await entryInfo(root);
  if (!rootInfo.isDir) return out;
  const visited = /* @__PURE__ */ new Set([rootInfo.realPath ?? normalizePath(root)]);
  const queue = [{ dir: root, depth: 0, viaLink: false }];
  const found = [];
  const pluginRoots = /* @__PURE__ */ new Set();
  let directories = 1;
  let entries = 0;
  walk: while (queue.length > 0) {
    const { dir, depth, viaLink } = queue.shift();
    const listing = await listDir(dir);
    if (listing.status === "unreadable") out.unreadableDirs.push(dir);
    if (listing.status !== "ok") continue;
    for (const name of listing.names) {
      if (entries === limits.maxEntries) {
        out.truncated = true;
        break walk;
      }
      entries++;
      const path = join27(dir, name);
      const info = await entryInfo(path);
      if (info.dangling) {
        out.danglingLinks.push(path);
        continue;
      }
      if (!info.exists || info.isLink && !info.isDir) continue;
      if (info.isDir) {
        if (MANIFEST_DIRS.includes(name)) pluginRoots.add(dir);
        if (depth >= MAX_DEPTH || name.startsWith(".")) continue;
        const identity = info.realPath ?? normalizePath(path);
        if (visited.has(identity)) continue;
        visited.add(identity);
        if (directories === limits.maxDirectories) {
          out.truncated = true;
          continue;
        }
        directories++;
        queue.push({ dir: path, depth: depth + 1, viaLink: viaLink || info.isLink });
        continue;
      }
      if (info.isFile && name === "SKILL.md") found.push({ dir, viaLink });
    }
  }
  const namespaces = /* @__PURE__ */ new Map();
  const namespaceOf = async (dir) => {
    for (let current = dir; ; current = dirname5(current)) {
      if (pluginRoots.has(current)) {
        if (!namespaces.has(current)) namespaces.set(current, await manifestNamespace(current));
        const namespace2 = namespaces.get(current);
        if (namespace2 !== null) return namespace2;
      }
      if (current === root || dirname5(current) === current) return null;
    }
  };
  for (const { dir, viaLink } of found) {
    const folder = await readSkillFolder(dir, basename8(dir));
    if (folder === null) continue;
    const skillFile = join27(dir, "SKILL.md");
    let bytes = null;
    try {
      bytes = await readFile11(skillFile);
    } catch {
      bytes = null;
    }
    const prefix = namespace ?? await namespaceOf(dir);
    const own = folder.declaredName === null ? "" : squash(folder.declaredName);
    const base = own === "" ? folder.dirName : own;
    out.skills.push({
      folder,
      viaLink: viaLink || folder.isLink,
      frontmatterOk: folder.readable && bytes !== null && codexFrontmatterOk(bytes),
      name: prefix === null ? base : `${prefix}:${base}`,
      skillFileRealPath: (await entryInfo(skillFile)).realPath
    });
  }
  return out;
}

// src/scan/codex-plugins.ts
var JSON_MAX_NESTING = 127;
var PLUGIN_NAME = /^[A-Za-z0-9_.-]+$/;
var MARKET_NAME = /^[A-Za-z0-9_-]+$/;
function codexPluginIdValid(id) {
  const at = id.lastIndexOf("@");
  if (at <= 0 || at === id.length - 1) return false;
  const name = id.slice(0, at);
  const market = id.slice(at + 1);
  if (!PLUGIN_NAME.test(name) || name.startsWith(".") || name.endsWith(".") || name.includes("..")) return false;
  return MARKET_NAME.test(market);
}
var VERSION_SEGMENT = /^[A-Za-z0-9_.+-]+$/;
var SEMVER = /^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*)(?:\.(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*))*))?(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$/;
var cmpText = (a, b) => a < b ? -1 : a > b ? 1 : 0;
var cmpBig = (a, b) => {
  const x = BigInt(a);
  const y = BigInt(b);
  return x < y ? -1 : x > y ? 1 : 0;
};
function cmpPre(a, b) {
  if (a === void 0 || b === void 0) return a === b ? 0 : a === void 0 ? 1 : -1;
  const xs = a.split(".");
  const ys = b.split(".");
  for (let i = 0; i < Math.min(xs.length, ys.length); i++) {
    const x = xs[i];
    const y = ys[i];
    const xn = /^\d+$/.test(x);
    const yn = /^\d+$/.test(y);
    const order = xn && yn ? cmpBig(x, y) : xn ? -1 : yn ? 1 : cmpText(x, y);
    if (order !== 0) return order;
  }
  return xs.length - ys.length;
}
function cmpBuild(a, b) {
  if (a === b) return 0;
  const xs = a.split(".");
  const ys = b.split(".");
  for (let i = 0; i < xs.length; i++) {
    if (i >= ys.length) return 1;
    const x = xs[i];
    const y = ys[i];
    const xn = /^[0-9]*$/.test(x);
    const yn = /^[0-9]*$/.test(y);
    if (xn !== yn) return xn ? -1 : 1;
    let order;
    if (xn) {
      const xv = x.replace(/^0+/, "");
      const yv = y.replace(/^0+/, "");
      order = xv.length - yv.length || cmpText(xv, yv) || x.length - y.length;
    } else order = cmpText(x, y);
    if (order !== 0) return Math.sign(order);
  }
  return ys.length > xs.length ? -1 : 0;
}
var U64_MAX = 2n ** 64n - 1n;
function semverOf(text) {
  const match = SEMVER.exec(text);
  return match !== null && [match[1], match[2], match[3]].every((part) => BigInt(part) <= U64_MAX) ? match : null;
}
function compareCodexPluginVersions(a, b) {
  const x = semverOf(a);
  const y = semverOf(b);
  if (x === null || y === null) return cmpText(a, b);
  for (let i = 1; i <= 3; i++) {
    const order = cmpBig(x[i], y[i]);
    if (order !== 0) return order;
  }
  return cmpPre(x[4], y[4]) || cmpBuild(x[5] ?? "", y[5] ?? "");
}
async function installRoot(base) {
  const listing = await listDir(base);
  if (listing.status === "unreadable") return { install: "unreadable", root: null };
  if (listing.status !== "ok") return { install: "missing", root: null };
  const versions = [];
  for (const name of listing.names) {
    if (name === "." || name === ".." || !VERSION_SEGMENT.test(name)) continue;
    const info = await entryInfo(join28(base, name));
    if (info.isDir && !info.isLink) versions.push(name);
  }
  if (versions.length === 0) return { install: "missing", root: null };
  const chosen = versions.includes("local") ? "local" : versions.reduce((best, version) => compareCodexPluginVersions(version, best) > 0 ? version : best);
  return { install: "ok", root: join28(base, chosen) };
}
async function findManifest(root) {
  const own = async (path) => {
    try {
      const info = await lstat7(path);
      return { kind: info.isSymbolicLink() ? "other" : info.isFile() ? "file" : info.isDirectory() ? "dir" : "other" };
    } catch (error) {
      return error.code === "ENOENT" ? { kind: "none" } : null;
    }
  };
  const agentPath = join28(root, "plugin.json");
  const agent = await own(agentPath);
  if (agent === null) return { status: "unreadable" };
  if (agent.kind === "dir" || agent.kind === "other") return { status: "missing" };
  if (agent.kind === "file") {
    const read = await readText(agentPath);
    if (read.status === "unreadable") return { status: "unreadable" };
    if (read.status === "ok") {
      try {
        const value = JSON.parse(read.text);
        if (isObject5(value) && !exceedsLimits(value, JSON_MAX_NESTING) && typeof value.$schema === "string" && value.$schema.startsWith("https://agent-plugins.org/schemas/")) return { status: "found", path: agentPath, agent: true };
      } catch {
      }
    }
  }
  for (const relativePath of CODEX_MANIFEST_PATHS) {
    const [dir, file] = relativePath.split("/");
    const parent = await own(join28(root, dir));
    if (parent === null) return { status: "unreadable" };
    if (parent.kind === "none") continue;
    if (parent.kind !== "dir") return { status: "missing" };
    const path = join28(root, dir, file);
    const manifest = await own(path);
    if (manifest === null) return { status: "unreadable" };
    if (manifest.kind === "none") continue;
    return manifest.kind === "file" ? { status: "found", path, agent: false } : { status: "missing" };
  }
  return { status: "missing" };
}
function manifestPath(root, raw) {
  if (typeof raw !== "string" || !raw.startsWith("./")) return null;
  const rest = raw.slice(2);
  if (rest === "" || rest.split(/[\\/]/).includes("..") || rest.startsWith("/") || rest.startsWith("\\") || /^[A-Za-z]:/.test(rest)) return null;
  const resolved = resolve8(root, rest);
  const inside2 = relative4(root, resolved);
  return inside2 !== "" && !inside2.startsWith("..") && !inside2.startsWith(sep) ? resolved : null;
}
function pluginServerOk(definition) {
  const copy2 = { ...definition };
  delete copy2.type;
  if (!isObject5(copy2.oauth) || Object.keys(copy2.oauth).length === 0) delete copy2.oauth;
  return codexServerShapeOk(copy2) && copy2.auth !== "ema_auth";
}
function serversOf2(value) {
  const map = isObject5(value.mcpServers) ? value.mcpServers : value;
  return Object.entries(map).filter((entry) => isObject5(entry[1]) && pluginServerOk(entry[1])).map(([name, definition]) => ({ name, definition })).sort((a, b) => cmpText(a.name, b.name));
}
var LEGACY_NESTED_FIELDS = ["keywords", "skills", "mcpServers", "hooks", "extensions"];
function legacyManifestOk(manifest) {
  const text = (value) => value === void 0 || typeof value === "string";
  const optionalText = (value) => value === void 0 || value === null || typeof value === "string";
  const texts = (value) => value === void 0 || Array.isArray(value) && value.every((item2) => typeof item2 === "string");
  return text(manifest.name) && optionalText(manifest.version) && optionalText(manifest.description) && optionalText(manifest.apps) && texts(manifest.keywords) && (manifest.interface === void 0 || manifest.interface === null || isObject5(manifest.interface)) && !LEGACY_NESTED_FIELDS.some((key) => exceedsLimits(manifest[key], JSON_MAX_NESTING - 1));
}
async function readCodexPlugin(codexHome2, id) {
  const out = { id, idValid: codexPluginIdValid(id), root: null, install: "missing", manifest: "missing", namespace: null, skillRoots: [], mcpServers: [], mcpUnreadable: false, compositionKnown: true };
  if (!out.idValid) return out;
  const at = id.lastIndexOf("@");
  const located = await installRoot(join28(codexHome2, "plugins", "cache", id.slice(at + 1), id.slice(0, at)));
  out.install = located.install;
  out.root = located.root;
  out.compositionKnown = located.install !== "unreadable";
  if (located.root === null) return out;
  const root = located.root;
  const found = await findManifest(root);
  if (found.status !== "found") {
    out.manifest = found.status;
    out.compositionKnown = found.status !== "unreadable";
    return out;
  }
  const read = await readText(found.path);
  if (read.status !== "ok") {
    out.manifest = read.status;
    out.compositionKnown = read.status !== "unreadable";
    return out;
  }
  let manifest;
  try {
    const value = JSON.parse(read.text);
    if (!isObject5(value)) throw new Error("\uBB36\uC74C\uC774 \uC544\uB2C8\uB2E4");
    manifest = value;
  } catch {
    out.manifest = "unparsable";
    return out;
  }
  if (found.agent ? exceedsLimits(manifest, JSON_MAX_NESTING) : !legacyManifestOk(manifest)) {
    out.manifest = "unparsable";
    return out;
  }
  const rawName = typeof manifest.name === "string" ? manifest.name : "";
  out.manifest = "ok";
  out.namespace = rawName.trim() === "" ? root.split(/[\\/]/).pop() ?? rawName : rawName;
  if (found.agent) {
    out.compositionKnown = false;
    return out;
  }
  const listed = typeof manifest.skills === "string" ? [manifest.skills] : Array.isArray(manifest.skills) && manifest.skills.every((item2) => typeof item2 === "string") ? manifest.skills : [];
  const declared = listed.map((raw) => manifestPath(root, raw)).filter((path) => path !== null);
  const roots = declared.length > 0 ? declared : (await entryInfo(join28(root, "skills"))).isDir ? [join28(root, "skills")] : [];
  if ((await entryInfo(join28(root, ".codex-plugin", "migrated-command-skills"))).isDir) roots.push(join28(root, ".codex-plugin", "migrated-command-skills"));
  out.skillRoots = [...new Set(roots)].sort();
  if (isObject5(manifest.mcpServers)) {
    out.mcpServers = serversOf2(manifest.mcpServers);
    return out;
  }
  const declaredFile = manifestPath(root, manifest.mcpServers);
  const file = declaredFile ?? ((await entryInfo(join28(root, ".mcp.json"))).isFile ? join28(root, ".mcp.json") : null);
  if (file === null) return out;
  const text = await readText(file);
  if (text.status === "missing") return out;
  if (text.status === "unreadable") {
    out.mcpUnreadable = true;
    return out;
  }
  try {
    const value = JSON.parse(text.text);
    if (!isObject5(value) || exceedsLimits(value, JSON_MAX_NESTING)) throw new Error("\uBB36\uC74C\uC774 \uC544\uB2C8\uAC70\uB098 \uB108\uBB34 \uAE4A\uB2E4");
    out.mcpServers = serversOf2(value);
  } catch {
    out.mcpUnreadable = true;
  }
  return out;
}

// src/scan/codex-settings.ts
import { resolve as resolve9 } from "node:path";
var asciiLower = (text, platform) => platform === "win32" ? text.replace(/[A-Z]/g, (letter) => letter.toLowerCase()) : text;
var trustKeyForm = (path, platform) => asciiLower(resolve9(path).replace(/\\/g, "/"), platform);
function trustOf(user, root, platform = process.platform) {
  const projects = isTable(user.projects) ? user.projects : {};
  const rootForm = trustKeyForm(root, platform);
  const exactKey = asciiLower(root, platform);
  const found = [];
  for (const [key, entry] of Object.entries(projects)) {
    if (!isTable(entry) || entry.trust_level !== "trusted" && entry.trust_level !== "untrusted") continue;
    if (key === exactKey) return entry.trust_level;
    if (trustKeyForm(key, platform) === rootForm) found.push({ key, trust: entry.trust_level });
  }
  found.sort((a, b) => a.key < b.key ? -1 : a.key > b.key ? 1 : 0);
  return found[0]?.trust ?? null;
}
function approvalOf(value) {
  if (value === void 0) return null;
  if (isTable(value)) return "granular";
  if (value === "never") return value;
  if (value === "on-request" || value === "on-failure") return "on-request";
  return "other";
}
function sandboxOf(value) {
  if (value === void 0) return null;
  return value === "danger-full-access" || value === "workspace-write" || value === "read-only" ? value : "other";
}
function safetyOf(layers) {
  const merged = mergeCodexLayers(layers);
  let syntax = null;
  for (const layer of layers) {
    if (layer.sandbox_mode !== void 0) syntax = "legacy";
    if (layer.default_permissions !== void 0) syntax = "profiles";
  }
  const permissions = merged.default_permissions;
  return {
    approval: approvalOf(merged.approval_policy),
    sandbox: sandboxOf(merged.sandbox_mode),
    permissions: permissions === void 0 ? null : permissions === ":danger-full-access" ? "danger-full-access" : "other",
    fullAccess: syntax === "legacy" ? merged.sandbox_mode === "danger-full-access" : syntax === "profiles" ? permissions === ":danger-full-access" : false
  };
}
var pluginsFeatureOn = (merged) => !(isTable(merged.features) && merged.features.plugins === false);
var DEFAULT_NAMES = ["AGENTS.override.md", "AGENTS.md"];
function fallbackNames(merged, platform = process.platform) {
  const listed = Array.isArray(merged.project_doc_fallback_filenames) ? merged.project_doc_fallback_filenames : [];
  const names2 = [];
  for (const raw of listed) {
    if (typeof raw !== "string") continue;
    const name = raw.trim();
    if (name === "" || name === "." || name === ".." || name.includes("/") || name.includes("\0")) continue;
    if (platform === "win32" && (name.includes("\\") || name.includes(":"))) continue;
    if (!DEFAULT_NAMES.includes(name) && !names2.includes(name)) names2.push(name);
  }
  return names2;
}
var projectDocDisabled = (merged) => merged.project_doc_max_bytes === 0 || merged.project_doc_max_bytes === 0n;

// src/scan/codex.ts
var slashed2 = (path) => path.replace(/\\/g, "/");
var cmp4 = (a, b) => (a ?? "") < (b ?? "") ? -1 : (a ?? "") > (b ?? "") ? 1 : 0;
var SKILL_SCOPE_ORDER2 = { user: 0, project: 1, plugin: 2 };
var OWNER_ORDER2 = { user: 0, managed: 1, plugin: 2, tool: 3 };
async function rulePath(raw, home, homedir2) {
  const expanded = raw === "~" ? homedir2 : raw.startsWith("~/") || raw.startsWith("~\\") ? join29(homedir2, raw.slice(2)) : raw;
  const absolute = isAbsolute3(expanded) ? expanded : resolve10(home, expanded);
  return (await entryInfo(absolute)).realPath ?? normalizePath(absolute);
}
async function skillRules(user, home, homedir2) {
  const skills = isTable(user.skills) ? user.skills : {};
  const list = Array.isArray(skills.config) ? skills.config : [];
  const rules = [];
  for (const entry of list) {
    if (!isTable(entry) || typeof entry.enabled !== "boolean") continue;
    const path = typeof entry.path === "string" ? entry.path : null;
    const name = typeof entry.name === "string" ? entry.name.trim() : null;
    if (path === null === (name === null) || name === "") continue;
    rules.push({ path: path === null ? null : await rulePath(path, home, homedir2), name, enabled: entry.enabled });
  }
  return rules;
}
function enabledByRules(rules, skillFile, name) {
  let enabled = true;
  for (const rule2 of rules) if (rule2.path !== null && rule2.path === skillFile || rule2.name !== null && rule2.name === name) enabled = rule2.enabled;
  return enabled;
}
function configuredIn(merged, id) {
  if (!pluginsFeatureOn(merged)) return false;
  const plugins = isTable(merged.plugins) ? merged.plugins : {};
  const entry = plugins[id];
  if (!isTable(entry) || entry.enabled === false) return false;
  const fallback = plugins._default;
  return entry.enabled !== void 0 || !isTable(fallback) || fallback.enabled !== false;
}
var loadable = (plugin) => plugin.idValid && plugin.install === "ok" && plugin.manifest === "ok";
async function codexDefaultCopySecrets(input) {
  const defaultHome = join29(input.homedir, ".codex");
  if (!input.env.CODEX_HOME?.trim() || normalizePath(codexHome(input.env, input.homedir)) === normalizePath(defaultHome)) return [];
  const read = await readCodexConfig(join29(defaultHome, "config.toml"));
  if (read.status !== "ok") return [];
  return codexMcpSecrets(read.value, []).map((secret) => ({ ...secret, copy: "default" }));
}
async function scanCodexSetup(input) {
  const home = codexHome(input.env, input.homedir);
  const userFile = join29(home, "config.toml");
  const userRead = await readCodexConfig(userFile);
  const user = userRead.status === "ok" ? userRead.value : {};
  const problems = [];
  const codexPlace = (path) => `${input.env.CODEX_HOME?.trim() ? "$CODEX_HOME" : "~/.codex"}/${slashed2(relative5(home, path))}`;
  const homePlace = (path) => `~/${slashed2(relative5(input.homedir, path))}`;
  if (userRead.status === "unparsable") problems.push({ kind: "unparsable", owner: "user", path: userFile, place: codexPlace(userFile) });
  const refs = await groupProjects(input.cwds, { homedir: input.homedir, tmpdir: input.tmpdir, platform: input.platform });
  const active = refs.filter((ref) => ref.exists && !ref.excluded);
  const projectNames = projectNamesOf(refs);
  const projectPlace = (ref, path) => `${projectNames.get(ref.normRoot)}/${slashed2(relative5(ref.root, path))}`;
  const homeReal = (await entryInfo(home)).realPath ?? normalizePath(home);
  const sameAsHome = async (dir) => normalizePath(dir) === normalizePath(home) || (await entryInfo(dir)).realPath === homeReal;
  const contexts = [{ projectRoot: null, merged: user, plugins: [] }];
  const trustedLayers = [];
  const perProject = /* @__PURE__ */ new Map();
  for (const ref of active) {
    const trust = trustOf(user, ref.root, input.platform);
    if (trust !== "trusted" || await sameAsHome(join29(ref.root, ".codex"))) {
      perProject.set(ref.normRoot, { status: null, merged: user, safety: null });
      continue;
    }
    const file = join29(ref.root, ".codex", "config.toml");
    const text = await readText(file);
    const layer = text.status === "ok" ? parseCodexConfig(text.text) : null;
    let status = text.status === "ok" ? layer === null ? "unparsable" : "ok" : text.status;
    let merged = user;
    if (layer !== null) {
      merged = mergeCodexLayers([user, layer]);
      if (!codexConfigShapeOk(merged)) {
        status = "unparsable";
        merged = user;
      }
    }
    if (status === "unparsable") problems.push({ kind: "unparsable", owner: "user", path: file, place: projectPlace(ref, file) });
    const readable = status === "ok" || status === "missing";
    perProject.set(ref.normRoot, { status, merged, safety: readable ? safetyOf(status === "ok" && layer !== null ? [user, layer] : [user]) : null });
    if (!readable) continue;
    contexts.push({ projectRoot: ref.normRoot, merged, plugins: [] });
    if (status === "ok" && layer !== null) trustedLayers.push({ normRoot: ref.normRoot, layer });
  }
  const ids = /* @__PURE__ */ new Set();
  for (const layer of [user, ...trustedLayers.map((p) => p.layer)]) if (isTable(layer.plugins)) {
    for (const id of Object.keys(layer.plugins)) if (id !== "_default") ids.add(id);
  }
  const reads = [];
  for (const id of [...ids].sort()) reads.push(await readCodexPlugin(home, id));
  for (const context of contexts) context.plugins = reads.filter((plugin) => loadable(plugin) && configuredIn(context.merged, plugin.id)).map((plugin) => plugin.id);
  const enabledIds = new Set(contexts.flatMap((context) => context.plugins));
  const rules = await skillRules(user, home, input.homedir);
  const skills = [];
  const unreadableDirs = [];
  const unreadableSkillPlaces = { user: false, projects: [], plugins: [] };
  const pluginSkillNames = /* @__PURE__ */ new Map();
  const addScan = (where2, scan, place, owner) => {
    const blocked = [...scan.unreadableDirs, ...scan.truncated ? [where2] : []];
    unreadableDirs.push(...blocked);
    if (blocked.length > 0) {
      if (owner.scope === "user") unreadableSkillPlaces.user = true;
      else if (owner.scope === "project") unreadableSkillPlaces.projects.push(owner.projectRoot);
      else unreadableSkillPlaces.plugins.push(owner.pluginId);
    }
    const problem = (kind, path) => {
      problems.push(place === null ? { kind, owner: "plugin", path, place: null } : { kind, owner: "user", path, place: place(path) });
    };
    for (const path of scan.danglingLinks) problem("danglingLink", path);
    for (const found of scan.skills) {
      if (found.folder.readable && !found.frontmatterOk) problem("noFrontmatter", found.folder.path);
      const enabled = enabledByRules(rules, found.skillFileRealPath, found.name);
      skills.push({
        scope: owner.scope,
        name: found.name,
        recordNames: [found.name],
        path: found.folder.path,
        realPath: found.folder.realPath,
        isLink: found.viaLink,
        contentHash: found.folder.contentHash,
        createdMs: found.folder.createdMs,
        targetCreatedMs: found.folder.targetCreatedMs,
        projectRoot: owner.scope === "project" ? owner.projectRoot : null,
        pluginId: owner.scope === "plugin" ? owner.pluginId : null,
        enabled,
        listed: enabled,
        readable: found.folder.readable,
        nameUnreadable: found.folder.nameUnreadable,
        managedFixed: false,
        hookProvided: false,
        usageLastUsedMs: null,
        usageUndated: false
      });
      if (owner.scope === "plugin") pluginSkillNames.set(owner.pluginId, [...pluginSkillNames.get(owner.pluginId) ?? [], found.name]);
    }
  };
  const userRoots = [
    { dir: join29(home, "skills"), place: codexPlace },
    { dir: join29(input.homedir, ".agents", "skills"), place: homePlace }
  ].filter((root, index, all) => all.findIndex((other) => normalizePath(other.dir) === normalizePath(root.dir)) === index);
  for (const root of userRoots) addScan(root.dir, await scanCodexSkillRoot(root.dir), root.place, { scope: "user" });
  for (const ref of active) {
    const dirs = [join29(ref.root, ".agents", "skills")];
    if (!await sameAsHome(join29(ref.root, ".codex"))) dirs.push(join29(ref.root, ".codex", "skills"));
    for (const dir of dirs) addScan(dir, await scanCodexSkillRoot(dir), (path) => projectPlace(ref, path), { scope: "project", projectRoot: ref.normRoot });
  }
  for (const plugin of reads) {
    if (!enabledIds.has(plugin.id)) continue;
    for (const dir of plugin.skillRoots) addScan(dir, await scanCodexSkillRoot(dir, void 0, plugin.namespace), null, { scope: "plugin", pluginId: plugin.id });
  }
  const pluginServers = new Map(reads.filter((plugin) => enabledIds.has(plugin.id) && !plugin.mcpUnreadable).map((plugin) => [plugin.id, plugin.mcpServers]));
  const mcpServers = codexMcpFacts({ user, projects: trustedLayers, contexts, pluginServers, salt: input.salt });
  const plugins = reads.map((plugin) => ({
    id: plugin.id,
    configured: contexts.some((context) => configuredIn(context.merged, plugin.id)),
    enabled: enabledIds.has(plugin.id),
    idValid: plugin.idValid,
    install: plugin.install,
    manifest: plugin.manifest,
    namespace: plugin.namespace,
    compositionKnown: plugin.compositionKnown,
    mcpUnreadable: plugin.mcpUnreadable,
    skills: (pluginSkillNames.get(plugin.id) ?? []).sort()
  }));
  const globalRead = await readCodexGlobalInstructions(home, active);
  const projects = [];
  for (const ref of refs) {
    const trust = trustOf(user, ref.root, input.platform);
    const known2 = perProject.get(ref.normRoot);
    if (known2 === void 0) {
      projects.push({ normRoot: ref.normRoot, scanned: false, trust, configStatus: null, instructions: emptyInstructionSet(), safety: null });
      continue;
    }
    const skip = trust === "untrusted" || projectDocDisabled(known2.merged);
    const instructions = skip ? emptyInstructionSet() : await readCodexProjectInstructions(ref.root, fallbackNames(known2.merged, input.platform));
    projects.push({ normRoot: ref.normRoot, scanned: true, trust, configStatus: known2.status, instructions, safety: known2.safety });
  }
  skills.sort((a, b) => cmp4(a.name, b.name) || SKILL_SCOPE_ORDER2[a.scope] - SKILL_SCOPE_ORDER2[b.scope] || cmp4(normalizePath(a.path), normalizePath(b.path)) || cmp4(a.pluginId, b.pluginId));
  const uniqueProblems = [];
  for (const problem of new Map(problems.map((p) => [`${p.kind}\0${p.owner}\0${p.path}`, p])).values()) {
    uniqueProblems.push({ ...problem, realPath: (await entryInfo(problem.path)).realPath });
  }
  uniqueProblems.sort((a, b) => cmp4(a.path, b.path) || cmp4(a.kind, b.kind) || OWNER_ORDER2[a.owner] - OWNER_ORDER2[b.owner]);
  return {
    tool: "codex",
    home,
    config: userRead.status,
    globalInstructions: globalRead.set,
    globalMentions: globalRead.mentions,
    safety: safetyOf([user]),
    skills: skills.map((skill) => ({ ...skill, installKey: codexSkillInstallKey(skill) })),
    mcpServers: mcpServers.map((server) => ({ ...server, installKey: codexMcpInstallKey(server) })),
    plugins,
    projects,
    problems: uniqueProblems,
    secrets: [...codexMcpSecrets(user, trustedLayers), ...await codexDefaultCopySecrets(input)],
    unreadableDirs: [...new Set(unreadableDirs)].sort(),
    unreadableSkillPlaces: { user: unreadableSkillPlaces.user, projects: [...new Set(unreadableSkillPlaces.projects)].sort(), plugins: [...new Set(unreadableSkillPlaces.plugins)].sort() }
  };
}

// src/scan/gemini.ts
import { lstat as lstat8 } from "node:fs/promises";
import { dirname as dirname7, isAbsolute as isAbsolute4, join as join30, relative as relative6, resolve as resolve11 } from "node:path";

// src/scan/gemini-settings.ts
import { dirname as dirname6, posix, win32 } from "node:path";
var QUOTE2 = 34;
var BACKSLASH3 = 92;
var SLASH = 47;
var STAR = 42;
var NEWLINE = 10;
function stripJsonComments(text) {
  let out = "";
  let index = 0;
  let inString = false;
  while (index < text.length) {
    const code = text.charCodeAt(index);
    if (inString) {
      out += text[index];
      if (code === BACKSLASH3 && index + 1 < text.length) {
        out += text[index + 1];
        index += 2;
        continue;
      }
      if (code === QUOTE2) inString = false;
      index++;
      continue;
    }
    if (code === QUOTE2) {
      inString = true;
      out += text[index];
      index++;
      continue;
    }
    if (code === SLASH && text.charCodeAt(index + 1) === SLASH) {
      while (index < text.length && text.charCodeAt(index) !== NEWLINE) index++;
      continue;
    }
    if (code === SLASH && text.charCodeAt(index + 1) === STAR) {
      const end = text.indexOf("*/", index + 2);
      index = end === -1 ? text.length : end + 2;
      out += " ";
      continue;
    }
    out += text[index];
    index++;
  }
  return out;
}
async function readGeminiSettings(path) {
  const read = await readText(path);
  if (read.status !== "ok") return { status: read.status, value: {} };
  try {
    const value = JSON.parse(stripJsonComments(read.text));
    return isObject5(value) ? { status: "ok", value } : { status: "unparsable", value: {} };
  } catch {
    return { status: "unparsable", value: {} };
  }
}
var section = (settings, key) => isObject5(settings[key]) ? settings[key] : {};
var strings4 = (value) => Array.isArray(value) ? value.filter((item2) => typeof item2 === "string") : [];
function contextFileNames(layers) {
  let names2 = [];
  for (const layer of layers) {
    const value = section(layer, "context").fileName;
    if (typeof value === "string" && value.trim() !== "") names2 = [value.trim()];
    else if (Array.isArray(value)) {
      const list = strings4(value).map((name) => name.trim()).filter((name) => name !== "");
      if (list.length > 0) names2 = list;
    }
  }
  return [.../* @__PURE__ */ new Set([...names2, "GEMINI.md"])];
}
function boundaryMarkersOf(layers) {
  let markers = [".git"];
  for (const layer of layers) {
    const value = section(layer, "context").memoryBoundaryMarkers;
    if (Array.isArray(value)) markers = strings4(value);
  }
  return markers;
}
function folderTrustOn(layers) {
  let on = true;
  for (const layer of layers) {
    const value = section(section(layer, "security"), "folderTrust").enabled;
    if (typeof value === "boolean") on = value;
  }
  return on;
}
var TRUST_LEVELS = /* @__PURE__ */ new Set(["TRUST_FOLDER", "TRUST_PARENT", "DO_NOT_TRUST"]);
function trustRulesValid(rules) {
  return Object.values(rules).every((value) => typeof value === "string" && TRUST_LEVELS.has(value));
}
function trustRuleBases(rules) {
  return Object.entries(rules).filter((entry) => typeof entry[1] === "string" && TRUST_LEVELS.has(entry[1])).map(([rulePath2, value]) => value === "TRUST_PARENT" ? dirname6(rulePath2) : rulePath2);
}
function geminiTrustOf(rules, root, platform = process.platform, realOf = (base) => base) {
  const norm = (path) => platform === "darwin" ? normalizePath(path, platform).toLowerCase() : normalizePath(path, platform);
  const target = norm(root);
  let longest = -1;
  let level = null;
  for (const [rulePath2, value] of Object.entries(rules)) {
    if (typeof value !== "string" || !TRUST_LEVELS.has(value)) continue;
    const base = norm(realOf(value === "TRUST_PARENT" ? dirname6(rulePath2) : rulePath2));
    const inside2 = target === base || target.startsWith(base.endsWith("/") ? base : `${base}/`);
    if (inside2 && rulePath2.length > longest) {
      longest = rulePath2.length;
      level = value;
    }
  }
  return level === null ? null : level === "DO_NOT_TRUST" ? "untrusted" : "trusted";
}
function geminiSystemPaths(env, platform) {
  const fixed2 = platform === "darwin" ? "/Library/Application Support/GeminiCli/settings.json" : platform === "win32" ? "C:\\ProgramData\\gemini-cli\\settings.json" : "/etc/gemini-cli/settings.json";
  const settings = env.GEMINI_CLI_SYSTEM_SETTINGS_PATH?.trim() || fixed2;
  const defaults = env.GEMINI_CLI_SYSTEM_DEFAULTS_PATH?.trim() || (platform === "win32" ? win32 : posix).join((platform === "win32" ? win32 : posix).dirname(settings), "system-defaults.json");
  return { settings, defaults };
}
var SHELL_NAMES = /* @__PURE__ */ new Set(["run_shell_command", "ShellTool"]);
var SANDBOX_COMMANDS = /* @__PURE__ */ new Set(["docker", "podman", "sandbox-exec", "runsc", "lxc", "windows-native"]);
function commandAllowed(command, platform) {
  if (command === "runsc") return platform === "linux";
  if (command === "windows-native") return platform === "win32";
  if (command === "sandbox-exec") return platform === "darwin";
  return true;
}
function sandboxOn(value, platform) {
  if (value === void 0 || value === null || value === false) return false;
  if (value === true) return true;
  if (typeof value === "string") {
    if (value === "" || value === "0" || value === "false") return false;
    if (value === "1" || value === "true") return true;
    return SANDBOX_COMMANDS.has(value) && commandAllowed(value, platform) ? true : null;
  }
  if (isObject5(value)) {
    if (!value.enabled) return false;
    const command = value.command;
    return command === void 0 || command === null ? true : typeof command === "string" ? sandboxOn(command, platform) : null;
  }
  return null;
}
function geminiSafetyOf(layers, platform = process.platform) {
  let approvalMode = "default";
  let box = void 0;
  let toolSandboxing = false;
  let allowed = [];
  for (const layer of layers) {
    const mode = section(layer, "general").defaultApprovalMode;
    if (typeof mode === "string" && mode !== "") approvalMode = mode;
    const tools2 = section(layer, "tools");
    if (Object.hasOwn(tools2, "sandbox")) box = isObject5(box) && isObject5(tools2.sandbox) ? { ...box, ...tools2.sandbox } : tools2.sandbox;
    if (Object.hasOwn(tools2, "allowed")) allowed = strings4(tools2.allowed);
    const toolLevel = section(layer, "security").toolSandboxing;
    if (typeof toolLevel === "boolean") toolSandboxing = toolLevel;
  }
  const shellAutoApproved = allowed.some((name) => SHELL_NAMES.has(name.trim()));
  const on = sandboxOn(box, platform);
  return { approvalMode, sandbox: on === null ? null : on || toolSandboxing, shellAutoApproved };
}
function unknownGeminiSafety() {
  return { approvalMode: null, sandbox: null, shellAutoApproved: null };
}
function mcpFilterOf(layers) {
  let allowed = null;
  let excluded = [];
  for (const layer of layers) {
    const mcp = section(layer, "mcp");
    if (Array.isArray(mcp.allowed)) allowed = strings4(mcp.allowed);
    if (Array.isArray(mcp.excluded)) excluded = strings4(mcp.excluded);
  }
  return { allowed, excluded };
}
function serversOfLayer(layer) {
  return section(layer, "mcpServers");
}

// src/scan/gemini.ts
var slashed3 = (path) => path.replace(/\\/g, "/");
var cmp5 = (a, b) => (a ?? "") < (b ?? "") ? -1 : (a ?? "") > (b ?? "") ? 1 : 0;
var SCOPE_ORDER6 = { user: 0, local: 1, project: 2, plugin: 3, "claude-ai": 4 };
var known = (status) => status === "ok" || status === "missing";
function geminiServerRecordName(name) {
  const valid = name.replace(/[^a-zA-Z0-9_\-.:]/g, "_");
  const cut = valid.indexOf("_");
  return cut === -1 ? valid : valid.slice(0, cut);
}
async function realOrSelf(path) {
  if (await reachesNetwork(path)) return path;
  return (await entryInfo(path)).realPath ?? path;
}
var LOCAL_BOUNDARY_OPS = {
  reachesNetwork: (path) => reachesNetwork(path),
  exists: async (path) => {
    try {
      await lstat8(path);
      return true;
    } catch {
      return false;
    }
  }
};
async function importBoundary(dir, markers, ops = LOCAL_BOUNDARY_OPS) {
  const start = resolve11(dir);
  if (markers.length === 0 || await ops.reachesNetwork(start)) return start;
  for (let current = start; ; ) {
    for (const marker2 of markers) {
      if (marker2 === "" || isAbsolute4(marker2) || marker2.includes("..")) continue;
      const path = join30(current, marker2);
      if (await ops.reachesNetwork(path)) continue;
      if (await ops.exists(path)) return current;
    }
    const parent = dirname7(current);
    if (parent === current) return start;
    current = parent;
  }
}
function serverOn(filter, name) {
  if (filter.allowed !== null && !filter.allowed.includes(name)) return false;
  return !filter.excluded.includes(name);
}
async function scanGeminiSetup(input) {
  const home = geminiHome(input.env, input.homedir);
  const userFile = join30(home, "settings.json");
  const userRead = await readGeminiSettings(userFile);
  const user = userRead.value;
  const problems = [];
  const geminiPlace = (path) => `${input.env.GEMINI_CLI_HOME?.trim() ? "$GEMINI_CLI_HOME/.gemini" : "~/.gemini"}/${slashed3(relative6(home, path))}`;
  if (userRead.status === "unparsable") problems.push({ kind: "unparsable", owner: "user", path: userFile, place: geminiPlace(userFile) });
  const systemPaths = geminiSystemPaths(input.env, input.platform);
  const defaultsRead = await readGeminiSettings(systemPaths.defaults);
  const systemRead = await readGeminiSettings(systemPaths.settings);
  const managedParts = [
    { path: systemPaths.defaults, status: defaultsRead.status },
    { path: systemPaths.settings, status: systemRead.status }
  ].filter((part) => part.status !== "missing");
  for (const part of managedParts) if (part.status === "unparsable") problems.push({ kind: "unparsable", owner: "managed", path: part.path, place: null });
  const outerKnown = known(userRead.status) && known(defaultsRead.status) && known(systemRead.status);
  const layersWith = (project) => [defaultsRead.value, user, ...project === null ? [] : [project], systemRead.value];
  const folderTrust = folderTrustOn(layersWith(null));
  const defaultTrustFile = join30(home, "trustedFolders.json");
  const trustFile = input.env.GEMINI_CLI_TRUSTED_FOLDERS_PATH?.trim() || defaultTrustFile;
  const trustRead = await readGeminiSettings(trustFile);
  const trustStatus = trustRead.status === "ok" && !trustRulesValid(trustRead.value) ? "unparsable" : trustRead.status;
  if (folderTrust && trustStatus === "unparsable") problems.push({ kind: "unparsable", owner: "user", path: trustFile, place: trustFile === defaultTrustFile ? geminiPlace(trustFile) : "$GEMINI_CLI_TRUSTED_FOLDERS_PATH" });
  const realBases = /* @__PURE__ */ new Map();
  if (folderTrust && trustStatus === "ok") {
    for (const base of trustRuleBases(trustRead.value)) if (!realBases.has(base)) realBases.set(base, await realOrSelf(base));
  }
  const trustedRoot = async (root) => !folderTrust || trustStatus === "ok" && geminiTrustOf(trustRead.value, await realOrSelf(root), input.platform, (base) => realBases.get(base) ?? base) === "trusted";
  const refs = await groupProjects(input.cwds, { homedir: input.homedir, tmpdir: input.tmpdir, platform: input.platform });
  const active = refs.filter((ref) => ref.exists && !ref.excluded);
  const projectNames = projectNamesOf(refs);
  const projectPlace = (ref, path) => `${projectNames.get(ref.normRoot)}/${slashed3(relative6(ref.root, path))}`;
  const homeReal = (await entryInfo(home)).realPath ?? normalizePath(home);
  const markers = boundaryMarkersOf(layersWith(null));
  const globalRead = await readInstructionSet(
    contextFileNames(layersWith(null)).map((name) => join30(home, name)),
    active,
    /* @__PURE__ */ new Set(),
    { homedir: input.homedir, within: await importBoundary(home, markers), style: "gemini" }
  );
  const projects = [];
  const projectLayers = [];
  for (const ref of refs) {
    const trusted = ref.exists && !ref.excluded && await trustedRoot(ref.root);
    if (!ref.exists || ref.excluded || !trusted) {
      projects.push({ normRoot: ref.normRoot, scanned: ref.exists && !ref.excluded, trusted, settingsStatus: null, instructions: emptyInstructionSet(), safety: null });
      continue;
    }
    const dir = join30(ref.root, ".gemini");
    const sameAsHome = normalizePath(dir) === normalizePath(home) || (await entryInfo(dir)).realPath === homeReal;
    const file = join30(dir, "settings.json");
    const read = sameAsHome ? { status: "missing", value: {} } : await readGeminiSettings(file);
    if (read.status === "unparsable") problems.push({ kind: "unparsable", owner: "user", path: file, place: projectPlace(ref, file) });
    const layers = layersWith(read.value);
    const within = await importBoundary(ref.root, boundaryMarkersOf(layers));
    const instructions = (await readInstructionSet(contextFileNames(layers).map((name) => join30(ref.root, name)), [], realPaths(globalRead.set), { homedir: input.homedir, within, style: "gemini" })).set;
    projects.push({ normRoot: ref.normRoot, scanned: true, trusted: true, settingsStatus: read.status, instructions, safety: outerKnown && known(read.status) ? geminiSafetyOf(layers, input.platform) : null });
    if (read.status === "ok") projectLayers.push({ normRoot: ref.normRoot, layer: read.value });
  }
  const mcpServers = [];
  const secrets = [];
  const addServers = (scope, projectRoot, layer, filter) => {
    for (const [name, definition] of Object.entries(serversOfLayer(layer))) {
      const shaped = isObject5(definition) ? definition : null;
      mcpServers.push({
        scope,
        name,
        recordNames: [geminiServerRecordName(name)],
        projectRoot,
        pluginId: null,
        definitionHash: shaped === null ? null : definitionHash(input.salt, shaped),
        enabled: shaped !== null && serverOn(filter, name),
        managedFixed: false,
        // 이 버전은 제미나이 서버의 안 쓰는 것을 판정하지 않아 관측 기록에 넣지 않는다
        installKey: null
      });
      for (const spot of secretSpots(shaped)) secrets.push({ scope, server: name, projectRoot, ...spot });
    }
  };
  addServers("user", null, user, mcpFilterOf(layersWith(null)));
  for (const project of projectLayers) addServers("project", project.normRoot, project.layer, mcpFilterOf(layersWith(project.layer)));
  mcpServers.sort((a, b) => cmp5(a.name, b.name) || SCOPE_ORDER6[a.scope] - SCOPE_ORDER6[b.scope] || cmp5(a.projectRoot, b.projectRoot));
  const uniqueProblems = [];
  for (const problem of new Map(problems.map((p) => [`${p.kind}|${p.owner}|${p.path}`, p])).values()) uniqueProblems.push({ ...problem, realPath: (await entryInfo(problem.path)).realPath });
  uniqueProblems.sort((a, b) => cmp5(a.path, b.path) || cmp5(a.kind, b.kind));
  return {
    tool: "gemini",
    home,
    settings: userRead.status,
    managedParts,
    folderTrust,
    trustedFolders: trustStatus,
    globalInstructions: globalRead.set,
    globalMentions: globalRead.mentions,
    safety: outerKnown ? geminiSafetyOf(layersWith(null), input.platform) : unknownGeminiSafety(),
    // 스킬 폴더는 이 버전에서 훑지 않는다. 사용자 스킬 자리를 읽지 못한 것으로 두어 스킬 규칙이 0으로 재지 않게 한다
    skills: [],
    mcpServers,
    projects,
    problems: uniqueProblems,
    secrets: sortSecrets(secrets),
    unreadableDirs: [...new Set(globalRead.set.unreadableDirs)].sort(),
    unreadableSkillPlaces: { user: true, projects: [], plugins: [] }
  };
}

// src/commands/checkup-input.ts
var CLAUDE_AI_PREFIX = "claude.ai ";
var CODEX_SKILL_OBSERVATION = { complete: false, reasons: ["not-recorded"] };
var GEMINI_SKILL_OBSERVATION = { complete: false, reasons: ["not-recorded"] };
var INHERITED_METRICS = ["responsesAndTokens", "toolCalls", "toolErrors", "shellExitCodes"];
function codexCoverage(unverifiedInheritance) {
  if (unverifiedInheritance === 0) return CODEX_COVERAGE;
  const coverage = { ...CODEX_COVERAGE };
  for (const key of INHERITED_METRICS) if (coverage[key] === "measured") coverage[key] = "proxy";
  return coverage;
}
function codexSharedRead(read) {
  return {
    files: read.files,
    listedBytes: read.listedBytes,
    bytes: read.bytes,
    inProgress: read.inProgress,
    olderThanWindow: read.olderThanWindow,
    unreadableFiles: read.unreadableFiles,
    unreadableFileBytes: read.unreadableFileBytes,
    unknownSizeFiles: read.unknownSizeFiles,
    unreadableDirs: read.unreadableDirs
  };
}
async function gatherCheckupInput(options) {
  const collectOptions = { env: options.env, homedir: options.homedir, clock: options.clock, cacheDir: options.cacheDir, rescan: options.rescan };
  const claude = await collectClaude(collectOptions);
  const codex = await collectCodex(collectOptions);
  const gemini = await collectGemini(collectOptions);
  const web = await collectWeb(options.webExports ?? [], collectOptions);
  const collectDates = new Set(makeWindows(options.clock.nowMs, options.clock.timeZone).collectDates);
  const cwds = /* @__PURE__ */ new Set();
  const normalizedCwds = /* @__PURE__ */ Object.create(null);
  for (const summary of [...claude.summaries, ...codex.summaries, ...gemini.summaries]) {
    if (summary.cwd !== null) normalizedCwds[summary.cwd] = normalizePath(summary.cwd, options.platform);
    if (summary.kind === "main" && summary.cwd !== null && Object.entries(summary.days).some(([date, day]) => collectDates.has(date) && day.responses > 0)) cwds.add(summary.cwd);
  }
  const claudeAiNames = /* @__PURE__ */ new Set();
  for (const summary of claude.summaries) {
    for (const day of Object.values(summary.days)) {
      for (const name of [...day.loadedMcpServers, ...Object.keys(day.mcpAttributions)]) if (name.startsWith(CLAUDE_AI_PREFIX)) claudeAiNames.add(name);
    }
  }
  const sortedCwds = [...cwds].sort();
  const claudeFacts = await scanClaudeSetup({
    env: options.env,
    homedir: options.homedir,
    tmpdir: options.tmpdir,
    platform: options.platform,
    cwds: sortedCwds,
    claudeAiNames: [...claudeAiNames].sort(),
    salt: options.state.salt,
    ...options.managedDir === void 0 ? {} : { managedDir: options.managedDir }
  });
  const codexFacts = await scanCodexSetup({ env: options.env, homedir: options.homedir, tmpdir: options.tmpdir, platform: options.platform, cwds: sortedCwds, salt: options.state.salt });
  const geminiFacts = await scanGeminiSetup({ env: options.env, homedir: options.homedir, tmpdir: options.tmpdir, platform: options.platform, cwds: sortedCwds, salt: options.state.salt });
  const claudeUnreadable = unreadableCount(claude.read);
  const claudeObserved = { skills: claudeObservation(claude.summaries, claudeUnreadable, "skill"), mcp: claudeObservation(claude.summaries, claudeUnreadable, "mcp") };
  const codexObserved = { skills: CODEX_SKILL_OBSERVATION, mcp: codexMcpObservation(codex.summaries, codexUnreadableCount(codex.read)) };
  const geminiObserved = { skills: GEMINI_SKILL_OBSERVATION, mcp: geminiMcpObservation(gemini.summaries, unreadableCount(gemini.read)) };
  const input = {
    clock: options.clock,
    tools: [
      {
        tool: "claude-code",
        summaries: claude.summaries,
        coverage: CLAUDE_COVERAGE,
        shellTools: [...SHELL_TOOLS].sort(),
        complete: { skills: claudeObserved.skills.complete, mcp: claudeObserved.mcp.complete },
        setup: claudeFacts
      },
      {
        tool: "codex",
        summaries: codex.summaries,
        coverage: codexCoverage(codex.unverifiedInheritance),
        shellTools: [...CODEX_SHELL_TOOLS].sort(),
        complete: { skills: codexObserved.skills.complete, mcp: codexObserved.mcp.complete },
        setup: codexFacts
      },
      {
        tool: "gemini",
        summaries: gemini.summaries,
        coverage: GEMINI_COVERAGE,
        shellTools: [...GEMINI_SHELL_TOOLS].sort(),
        complete: { skills: geminiObserved.skills.complete, mcp: geminiObserved.mcp.complete },
        setup: geminiFacts
      },
      // 웹 채팅은 셋팅이 없고 작업 폴더도 없어 프로젝트 목록에 들지 않는다(설계 「0.5.0에서 정한 것」)
      ...web.map((item2) => ({ tool: item2.tool, summaries: item2.summaries, coverage: WEB_COVERAGE, shellTools: [], complete: { skills: false, mcp: false }, setup: null }))
    ],
    // Codex와 제미나이의 프로젝트 몫은 정규화한 뿌리로 잇는다(「5단계 2부 계획 전 결정」 9번)
    projects: claudeFacts.projects,
    normalizedCwds: { ...normalizedCwds },
    installs: options.state.installs,
    self: options.self
  };
  const { fromCache: _fromCache, ...claudeRead } = claude.read;
  const { fromCache: _geminiFromCache, ...geminiRead } = gemini.read;
  const tools2 = [
    { tool: "claude-code", detected: claude.detected, visibleFrom: claude.visibleFrom, overlappingSessions: claude.overlappingSessions, read: claudeRead, observation: claudeObserved },
    // Codex는 다른 기록에서 이어받은 앞부분을 빼고 세므로 다른 세션과 겹쳐 세는 응답이 없다(설계 「5단계 계획 전 결정」 7번)
    {
      tool: "codex",
      detected: codex.detected,
      visibleFrom: codex.visibleFrom,
      overlappingSessions: 0,
      read: codexSharedRead(codex.read),
      observation: codexObserved,
      codex: {
        skippedFiles: codex.read.skippedFiles,
        skippedFileBytes: codex.read.skippedFileBytes,
        partialFiles: codex.read.partialFiles,
        skippedCopies: codex.read.skippedCopies,
        unnamedFiles: codex.read.unnamedFiles,
        parentRecordMissing: codex.parentRecordMissing,
        mergedSessions: codex.mergedSessions,
        unknownMtimeSessions: codex.unknownMtimeSessions,
        unverifiedInheritance: codex.unverifiedInheritance,
        idFallbacks: codex.idFallbacks
      }
    },
    { tool: "gemini", detected: gemini.detected, visibleFrom: gemini.visibleFrom, overlappingSessions: gemini.overlappingSessions, read: geminiRead, observation: geminiObserved },
    ...web.map((item2) => {
      const { fromCache: _webFromCache, ...read } = item2.read;
      return { tool: item2.tool, detected: item2.detected, visibleFrom: item2.visibleFrom, overlappingSessions: 0, read, observation: { skills: WEB_OBSERVATION, mcp: WEB_OBSERVATION }, web: item2.state };
    })
  ];
  return { input, collected: { claude, codex, gemini, web }, facts: { claude: claudeFacts, codex: codexFacts, gemini: geminiFacts }, tools: tools2 };
}

// src/commands/run-notices.ts
var STEP = {
  result: { en: "the result file", ko: "\uD3C9\uAC00 \uACB0\uACFC \uD30C\uC77C\uC744" },
  state: { en: "the state file", ko: "\uC0C1\uD0DC \uD30C\uC77C\uC744" },
  history: { en: "the score history", ko: "\uC810\uC218 \uC774\uB825\uC744" }
};
var PRUNED = {
  reports: { en: "old result files", ko: "\uC624\uB798\uB41C \uACB0\uACFC \uD30C\uC77C\uC744" },
  cache: { en: "cache entries whose source is gone", ko: "\uC6D0\uBCF8\uC774 \uC5C6\uC5B4\uC9C4 \uCE90\uC2DC \uD56D\uBAA9\uC744" }
};
var FOLDER = {
  state: { en: "state", ko: "\uC0C1\uD0DC" },
  reports: { en: "results", ko: "\uACB0\uACFC" },
  cache: { en: "cache", ko: "\uCE90\uC2DC" }
};
var LINES2 = {
  en: {
    save_failed: "Could not write {step} to the state folder ({code}), so the rest was not saved.",
    prune_failed: "Could not clean up {what} ({code}). Saving itself finished.",
    prune_skipped: "The {link} folder is a link, so {what} were not cleaned up.",
    not_saved: "This run does not save, so nothing was written to the state folder. It did not use the cache and is not added to the score history.",
    result_unwritten: "Could not write the result file to the OS temp folder ({code}), so only the summary is given.",
    report_failed: "Could not write the report page to the state folder ({code}).",
    report_unwritten: "Could not write the report page to the OS temp folder ({code}), so there is no report page this time.",
    report_unopened: "Could not open the report page in a browser. Open the file at the report path."
  },
  ko: {
    save_failed: "\uC0C1\uD0DC \uD3F4\uB354\uC5D0 {step} \uC4F0\uC9C0 \uBABB\uD574({code}) \uB0A8\uC740 \uC800\uC7A5\uC744 \uBA48\uCDC4\uC2B5\uB2C8\uB2E4.",
    prune_failed: "{what} \uC815\uB9AC\uD558\uC9C0 \uBABB\uD588\uC2B5\uB2C8\uB2E4({code}). \uC800\uC7A5\uC740 \uB05D\uB0AC\uC2B5\uB2C8\uB2E4.",
    prune_skipped: "{link} \uD3F4\uB354\uAC00 \uB9C1\uD06C\uB77C\uC11C {what} \uC815\uB9AC\uD558\uC9C0 \uC54A\uC558\uC2B5\uB2C8\uB2E4.",
    not_saved: "\uC800\uC7A5\uD558\uC9C0 \uC54A\uB294 \uC2E4\uD589\uC774\uB77C \uC0C1\uD0DC \uD3F4\uB354\uC5D0 \uC544\uBB34\uAC83\uB3C4 \uC4F0\uC9C0 \uC54A\uC558\uC2B5\uB2C8\uB2E4. \uC774 \uC810\uAC80\uC740 \uCE90\uC2DC\uB97C \uC4F0\uC9C0 \uC54A\uC558\uACE0 \uC810\uC218 \uC774\uB825\uC5D0\uB3C4 \uB0A8\uC9C0 \uC54A\uC2B5\uB2C8\uB2E4.",
    result_unwritten: "\uD3C9\uAC00 \uACB0\uACFC \uD30C\uC77C\uC744 \uC6B4\uC601\uCCB4\uC81C \uC784\uC2DC \uD3F4\uB354\uC5D0 \uC4F0\uC9C0 \uBABB\uD574({code}) \uC694\uC57D\uB9CC \uB0C5\uB2C8\uB2E4.",
    report_failed: "\uACB0\uACFC \uD654\uBA74\uC744 \uC0C1\uD0DC \uD3F4\uB354\uC5D0 \uC4F0\uC9C0 \uBABB\uD588\uC2B5\uB2C8\uB2E4({code}).",
    report_unwritten: "\uACB0\uACFC \uD654\uBA74\uC744 \uC6B4\uC601\uCCB4\uC81C \uC784\uC2DC \uD3F4\uB354\uC5D0 \uC4F0\uC9C0 \uBABB\uD574({code}) \uC774\uBC88\uC5D0\uB294 \uACB0\uACFC \uD654\uBA74\uC774 \uC5C6\uC2B5\uB2C8\uB2E4.",
    report_unopened: "\uACB0\uACFC \uD654\uBA74\uC744 \uBE0C\uB77C\uC6B0\uC800\uB85C \uC5F4\uC9C0 \uBABB\uD588\uC2B5\uB2C8\uB2E4. \uACB0\uACFC \uD654\uBA74\uC758 \uACBD\uB85C\uC5D0 \uC788\uB294 \uD30C\uC77C\uC744 \uC5EC\uC138\uC694."
  }
};
var RUN_NOTICE_KINDS = Object.keys(LINES2.en);
function runNoticeText(notice, lang) {
  const lines = LINES2[lang];
  switch (notice.kind) {
    case "save_failed":
      return fill(lines.save_failed, { step: STEP[notice.step][lang], code: notice.code });
    case "prune_failed":
      return fill(lines.prune_failed, { what: PRUNED[notice.what][lang], code: notice.code });
    case "prune_skipped":
      return fill(lines.prune_skipped, { link: FOLDER[notice.link][lang], what: PRUNED[notice.what][lang] });
    case "not_saved":
      return lines.not_saved;
    case "result_unwritten":
      return fill(lines.result_unwritten, { code: notice.code });
    case "report_failed":
      return fill(lines.report_failed, { code: notice.code });
    case "report_unwritten":
      return fill(lines.report_unwritten, { code: notice.code });
    case "report_unopened":
      return lines.report_unopened;
  }
}

// src/commands/self.ts
import { realpath as realpath6 } from "node:fs/promises";
import { basename as basename9, dirname as dirname8 } from "node:path";
var SELF_SKILL_NAMES = ["aq"];
var SELF_PLUGIN_NAMES = ["chunsik-garage"];
var BUNDLE_FILE = "aq.mjs";
async function selfIdentity(entryFile) {
  const skillRealPaths = [];
  if (basename9(entryFile) === BUNDLE_FILE && basename9(dirname8(entryFile)) === "scripts") {
    try {
      skillRealPaths.push(normalizePath(await realpath6(dirname8(dirname8(entryFile)))));
    } catch {
    }
  }
  return { skillNames: [...SELF_SKILL_NAMES], pluginNames: [...SELF_PLUGIN_NAMES], skillRealPaths };
}

// src/commands/checkup.ts
var codeOf = (error) => error?.code ?? "unknown";
async function runCheckup(options) {
  const now = options.now ?? Date.now;
  const started = now();
  const opened = await openState(options.stateDir);
  const webExports = await readWebExports(options.stateDir);
  const gathered = await gatherCheckupInput({
    env: options.env,
    homedir: options.homedir,
    tmpdir: options.tmpdir,
    platform: options.platform,
    clock: options.clock,
    cacheDir: options.save ? join31(options.stateDir, "cache") : null,
    rescan: options.rescan,
    state: opened.state,
    self: await selfIdentity(options.entryFile),
    ...options.managedDir === void 0 ? {} : { managedDir: options.managedDir },
    webExports: webExports.entries
  });
  const evaluation = evaluate(gathered.input);
  const result = checkupResult({ input: gathered.input, evaluation, collected: gathered.tools, appVersion: PROGRAM_VERSION, lang: options.lang, run: { stateBroken: opened.broken, webExportsBroken: webExports.status === "broken" }, ignored: opened.broken ? [] : opened.state.ignoredRules ?? [] });
  const stamp = resultStamp(options.clock.nowMs);
  const notices2 = [];
  let saved = false;
  let resultPath = null;
  if (options.save) {
    let step = "result";
    try {
      resultPath = await writeResult(options.stateDir, stamp, result);
      step = "state";
      const next = nextState(opened.state, gathered.facts, evaluation.windows.today, new Date(options.clock.nowMs).toISOString());
      await saveState(options.stateDir, await withLatestNotify(next, options.stateDir, options.env, options.homedir));
      step = "history";
      await appendHistory(options.stateDir, historyEntry(evaluation, options.clock.nowMs));
      saved = true;
    } catch (error) {
      notices2.push({ kind: "save_failed", step, code: codeOf(error) });
    }
    if (saved) {
      for (const [what, prune] of [["reports", () => pruneReports(options.stateDir, KEEP_REPORTS, stamp)], ["cache", () => pruneCache(options.stateDir)]]) {
        try {
          const report = await prune();
          if (report.skipped !== null) notices2.push({ kind: "prune_skipped", what, link: report.skipped });
        } catch (error) {
          notices2.push({ kind: "prune_failed", what, code: codeOf(error) });
        }
      }
    }
  } else {
    notices2.push({ kind: "not_saved" });
  }
  if (resultPath === null) {
    try {
      resultPath = await writeTempResult(options.tmpdir, stamp, result);
    } catch (error) {
      notices2.push({ kind: "result_unwritten", code: codeOf(error) });
    }
  }
  const round = saved ? await historyCount(options.stateDir).catch(() => null) : null;
  const history = saved ? await recentAq(options.stateDir) : [];
  const view = reportView(result, { saved, round, history });
  const repairs = view.findings.filter((finding) => finding.category === "repair").length;
  const html = reportHtml(view, await loadArt(assetsDirOf(options.entryFile), { tier: result.score.tier, unreadable: view.unreadable, repairs }));
  let reportPath = null;
  if (saved) {
    try {
      reportPath = await writeReport(options.stateDir, stamp, html);
    } catch (error) {
      notices2.push({ kind: "report_failed", code: codeOf(error) });
    }
  }
  if (reportPath === null) {
    try {
      reportPath = await writeTempReport(options.tmpdir, stamp, html);
    } catch (error) {
      notices2.push({ kind: "report_unwritten", code: codeOf(error) });
    }
  }
  if (reportPath !== null && options.open !== void 0 && !await options.open(reportPath)) notices2.push({ kind: "report_unopened" });
  const run2 = { durationMs: now() - started, cachedFiles: gathered.collected.claude.read.fromCache + gathered.collected.codex.read.fromCache + gathered.collected.gemini.read.fromCache, saved, reportPath, resultPath, notices: notices2, text: { notices: notices2.map((notice) => runNoticeText(notice, options.lang)) } };
  return { summary: checkupSummary(result, reportPath), run: run2, result };
}
async function withLatestNotify(next, stateDir2, env, homedir2) {
  const latest = await loadState(stateDir2);
  const notify = latest.status === "ok" ? latest.state.notify : next.notify;
  if (notify === null || !notify.on) return { ...next, notify };
  return { ...next, notify: { ...notify, names: nextNames(notify.names, notifyNames(env, homedir2)) } };
}

// src/commands/deep-hints.ts
import { join as join32 } from "node:path";

// src/core/copy/deep-hints.ts
var DEEP_HINT_COPY = {
  en: {
    global_mentions_project: "The global instructions of {tool} mention project paths or names several times ({projects}). Project-only content may have slipped into the global file.",
    repeated_project_lines: "{lines} lines repeat across the project instructions of {tool} ({projects}). They may belong in the global instructions.",
    large_global_instructions: "The global instructions of {tool} are about {tokens} tokens. Some of it may move into skills or project documents.",
    tools_instructions_differ: "The global instructions of Claude Code and Codex are not the same file and share only {shared} lines (Claude Code {claude}, Codex {codex}). The two tools may get different directions."
  },
  ko: {
    global_mentions_project: "{tool}\uC758 \uC804\uC5ED \uC9C0\uCE68\uC5D0 \uD504\uB85C\uC81D\uD2B8 \uACBD\uB85C\uB098 \uC774\uB984\uC774 \uC5EC\uB7EC \uBC88 \uB098\uC635\uB2C8\uB2E4({projects}). \uADF8 \uD504\uB85C\uC81D\uD2B8 \uC804\uC6A9 \uB0B4\uC6A9\uC774 \uC804\uC5ED\uC5D0 \uC11E\uC600\uC744 \uC218 \uC788\uC2B5\uB2C8\uB2E4.",
    repeated_project_lines: "{tool}\uC758 \uD504\uB85C\uC81D\uD2B8 \uC9C0\uCE68 \uC5EC\uB7EC \uACF3({projects})\uC5D0 \uAC19\uC740 \uC904\uC774 {lines}\uAC1C \uB418\uD480\uC774\uB429\uB2C8\uB2E4. \uC804\uC5ED\uC73C\uB85C \uC62C\uB9B4 \uB0B4\uC6A9\uC77C \uC218 \uC788\uC2B5\uB2C8\uB2E4.",
    large_global_instructions: "{tool}\uC758 \uC804\uC5ED \uC9C0\uCE68\uC774 \uC5B4\uB9BC\uC7A1\uC544 {tokens} \uD1A0\uD070\uC785\uB2C8\uB2E4. \uC2A4\uD0AC\uC774\uB098 \uD504\uB85C\uC81D\uD2B8 \uBB38\uC11C\uB85C \uB0B4\uB9B4 \uB0B4\uC6A9\uC774 \uC788\uC744 \uC218 \uC788\uC2B5\uB2C8\uB2E4.",
    tools_instructions_differ: "Claude Code\uC640 Codex\uC758 \uC804\uC5ED \uC9C0\uCE68\uC774 \uAC19\uC740 \uD30C\uC77C\uC774 \uC544\uB2C8\uACE0 \uACB9\uCE58\uB294 \uC904\uC774 {shared}\uC904\uBFD0\uC785\uB2C8\uB2E4(Claude Code {claude}\uC904, Codex {codex}\uC904). \uB450 \uB3C4\uAD6C\uAC00 \uB2E4\uB978 \uC9C0\uC2DC\uB97C \uBC1B\uACE0 \uC788\uC744 \uC218 \uC788\uC2B5\uB2C8\uB2E4."
  }
};
function deepHintText(hint, lang) {
  const text = DEEP_HINT_COPY[lang][hint.kind];
  switch (hint.kind) {
    case "global_mentions_project":
      return fill(text, { tool: TOOL_NAMES[hint.tool][lang], projects: hint.projects.map((project) => `${project.root} ${project.mentions}`).join(", ") });
    case "repeated_project_lines":
      return fill(text, { tool: TOOL_NAMES[hint.tool][lang], lines: hint.lines, projects: hint.projects.join(", ") });
    case "large_global_instructions":
      return fill(text, { tool: TOOL_NAMES[hint.tool][lang], tokens: Math.round(hint.tokens) });
    case "tools_instructions_differ":
      return fill(text, { shared: hint.shared, claude: hint.lines["claude-code"], codex: hint.lines.codex });
  }
}

// src/commands/deep-hints.ts
async function runDeepHints(options) {
  const now = options.now ?? Date.now;
  const started = now();
  const opened = await openState(options.stateDir);
  const gathered = await gatherCheckupInput({
    env: options.env,
    homedir: options.homedir,
    tmpdir: options.tmpdir,
    platform: options.platform,
    clock: options.clock,
    cacheDir: options.save ? join32(options.stateDir, "cache") : null,
    rescan: options.rescan,
    state: opened.state,
    self: await selfIdentity(options.entryFile),
    ...options.managedDir === void 0 ? {} : { managedDir: options.managedDir }
  });
  const hints = deepHints(gathered.input);
  return { hints, files: deepFiles(gathered.input), run: { durationMs: now() - started, text: { hints: hints.map((hint) => deepHintText(hint, options.lang)) } } };
}

// src/commands/notify.ts
var COPY3 = {
  en: {
    on: "Session start notices are on. When 7 days pass after the last checkup or something new is installed, a Claude Code session shows one line when it starts. Codex has no notices.",
    off: "Session start notices are off.",
    statusOn: "Session start notices are on.",
    statusOff: "Session start notices are off."
  },
  ko: {
    on: "\uC138\uC158 \uC2DC\uC791 \uC54C\uB9BC\uC744 \uCF30\uC2B5\uB2C8\uB2E4. \uB9C8\uC9C0\uB9C9 \uC810\uAC80 \uB4A4 7\uC77C\uC774 \uC9C0\uB098\uAC70\uB098 \uC0C8\uB85C \uAE50 \uAC83\uC774 \uC788\uC73C\uBA74 Claude Code \uC138\uC158\uC744 \uC2DC\uC791\uD560 \uB54C \uD55C \uC904\uB85C \uC54C\uB9BD\uB2C8\uB2E4. Codex\uC5D0\uB294 \uC54C\uB9BC\uC774 \uC5C6\uC2B5\uB2C8\uB2E4.",
    off: "\uC138\uC158 \uC2DC\uC791 \uC54C\uB9BC\uC744 \uAED0\uC2B5\uB2C8\uB2E4.",
    statusOn: "\uC138\uC158 \uC2DC\uC791 \uC54C\uB9BC\uC774 \uCF1C\uC838 \uC788\uC2B5\uB2C8\uB2E4.",
    statusOff: "\uC138\uC158 \uC2DC\uC791 \uC54C\uB9BC\uC774 \uAEBC\uC838 \uC788\uC2B5\uB2C8\uB2E4."
  }
};
var failure2 = (code, message) => Object.assign(new Error(message), { code });
async function runNotify(action, options) {
  const opened = await openState(options.stateDir);
  if (opened.broken && action !== "status") throw failure2("state-broken", "the state file could not be read; run a checkup first");
  const { state } = opened;
  if (action === "on") {
    state.notify = { on: true, lang: options.lang, names: nextNames(state.notify?.names ?? null, notifyNames(options.env, options.homedir)) };
    await saveState(options.stateDir, state);
  } else if (action === "off" && state.notify !== null && !opened.fresh) {
    state.notify = { ...state.notify, on: false };
    await saveState(options.stateDir, state);
  }
  const on = state.notify?.on === true;
  const text = action === "on" ? COPY3[options.lang].on : action === "off" ? COPY3[options.lang].off : on ? COPY3[options.lang].statusOn : COPY3[options.lang].statusOff;
  return { notify: { on, lang: state.notify?.lang ?? options.lang }, lastCheckupAt: state.lastCheckupAt, run: { text } };
}

// src/commands/ignore.ts
var COPY4 = {
  en: {
    added: '"{name}" is now kept as you chose. It is left out of what to fix first and the next-grade steps, and it still counts in the score.',
    removed: '"{name}" is no longer kept as you chose.',
    list: "Kept as you chose: {names}.",
    none: "Nothing is kept as you chose.",
    quote: (name) => `"${name}"`
  },
  ko: {
    added: "\u300C{name}\u300D \uD56D\uBAA9\uC740 \uC815\uD55C \uB300\uB85C \uB450\uACE0, \uBA3C\uC800 \uACE0\uCE60 \uAC83\uACFC \uB2E4\uC74C \uB4F1\uAE09 \uCC28\uB840\uC5D0\uC11C \uBE90\uC2B5\uB2C8\uB2E4. \uC810\uC218\uC5D0\uB294 \uADF8\uB300\uB85C \uB4E4\uC5B4\uAC11\uB2C8\uB2E4.",
    removed: "\u300C{name}\u300D \uD56D\uBAA9\uC758 \u300C\uADF8\uB300\uB85C \uB450\uAE30\uB85C \uD568\u300D\uC744 \uD480\uC5C8\uC2B5\uB2C8\uB2E4.",
    list: "\uADF8\uB300\uB85C \uB450\uAE30\uB85C \uD55C \uD56D\uBAA9\uC740 {names}\uC785\uB2C8\uB2E4.",
    none: "\uADF8\uB300\uB85C \uB450\uAE30\uB85C \uD55C \uD56D\uBAA9\uC774 \uC5C6\uC2B5\uB2C8\uB2E4.",
    quote: (name) => `\u300C${name}\u300D`
  }
};
var failure3 = (code, message) => Object.assign(new Error(message), { code });
function ruleIdOf(text) {
  if (text === null) return null;
  return RULES.find((spec) => spec.id === text.trim().toUpperCase())?.id ?? null;
}
async function runIgnore(action, rule2, options) {
  const copy2 = COPY4[options.lang];
  const nameOf = (id2) => RULE_COPY[id2][options.lang].name;
  const opened = await openState(options.stateDir);
  if (action === "list") {
    const ignored = opened.broken ? [] : reviveIgnoredRules(opened.state.ignoredRules);
    return { ignored, run: { text: ignored.length === 0 ? copy2.none : copy2.list.replace("{names}", ignored.map((id2) => copy2.quote(nameOf(id2))).join(", ")) } };
  }
  const id = ruleIdOf(rule2);
  if (id === null) throw failure3("unknown-rule", `not a rule id: ${rule2 ?? "(none)"}`);
  if (opened.broken) throw failure3("state-broken", "the state file could not be read; run a checkup first");
  const { state } = opened;
  const current = reviveIgnoredRules(state.ignoredRules);
  const next = reviveIgnoredRules(action === "add" ? [...current, id] : current.filter((value) => value !== id));
  if (next.join(",") !== current.join(",") || opened.fresh) {
    if (next.length > 0) state.ignoredRules = next;
    else delete state.ignoredRules;
    if (next.length > 0 || !opened.fresh) await saveState(options.stateDir, state);
  }
  return { ignored: next, run: { text: (action === "add" ? copy2.added : copy2.removed).replace("{name}", nameOf(id)) } };
}

// src/commands/import.ts
import { stat as stat9 } from "node:fs/promises";
import { join as join33, resolve as resolve12 } from "node:path";
var COPY5 = {
  en: {
    added: "Added the {tool} export: {count} {count:conversation|conversations}{range}. The next checkup counts it.",
    range: " from {first} to {last}",
    replaced: " It replaces the export added before.",
    skipped: " {count} {count:conversation|conversations} could not be read and {count:is|are} left out.",
    truncated: " The export could not be read to the end (the file ended early or the folder has too many items), so only what was read is counted.",
    listReset: " The list of added exports was broken, so it was started again. Add any other export again.",
    removedReset: "The list of added exports was broken, so it was emptied. Add the exports you want again.",
    removed: "Removed the {tool} export from the checkup. The export file itself was not touched.",
    notAdded: "No {tool} export has been added.",
    list: "Added exports: {tools}.",
    none: "No web chat export has been added."
  },
  ko: {
    added: "{tool} \uB0B4\uBCF4\uB0B4\uAE30\uB97C \uB123\uC5C8\uC2B5\uB2C8\uB2E4. \uB300\uD654 {count}\uAC1C{range}. \uB2E4\uC74C \uC810\uAC80\uBD80\uD130 \uC149\uB2C8\uB2E4.",
    range: ", {first}\uBD80\uD130 {last}\uAE4C\uC9C0\uC785\uB2C8\uB2E4",
    replaced: " \uC55E\uC11C \uB123\uC740 \uB0B4\uBCF4\uB0B4\uAE30\uB97C \uBC14\uAFE8\uC2B5\uB2C8\uB2E4.",
    skipped: " \uC77D\uC9C0 \uBABB\uD55C \uB300\uD654 {count}\uAC1C\uB294 \uBE90\uC2B5\uB2C8\uB2E4.",
    truncated: " \uB0B4\uBCF4\uB0B4\uAE30\uB97C \uB05D\uAE4C\uC9C0 \uC77D\uC9C0 \uBABB\uD574(\uD30C\uC77C\uC774 \uC911\uAC04\uC5D0 \uB04A\uACBC\uAC70\uB098 \uD3F4\uB354\uC758 \uD56D\uBAA9\uC774 \uB108\uBB34 \uB9CE\uC74C) \uC77D\uC740 \uB300\uD654\uB9CC \uC149\uB2C8\uB2E4.",
    listReset: " \uB123\uC740 \uBAA9\uB85D\uC774 \uAE68\uC838 \uC0C8\uB85C \uB9CC\uB4E4\uC5C8\uC2B5\uB2C8\uB2E4. \uB2E4\uB978 \uB0B4\uBCF4\uB0B4\uAE30\uB294 \uB2E4\uC2DC \uB123\uC5B4 \uC8FC\uC138\uC694.",
    removedReset: "\uB123\uC740 \uBAA9\uB85D\uC774 \uAE68\uC838 \uBE44\uC6E0\uC2B5\uB2C8\uB2E4. \uC140 \uB0B4\uBCF4\uB0B4\uAE30\uB97C \uB2E4\uC2DC \uB123\uC5B4 \uC8FC\uC138\uC694.",
    removed: "{tool} \uB0B4\uBCF4\uB0B4\uAE30\uB97C \uC810\uAC80\uC5D0\uC11C \uBE90\uC2B5\uB2C8\uB2E4. \uB0B4\uBCF4\uB0B4\uAE30 \uD30C\uC77C\uC740 \uADF8\uB300\uB85C \uB450\uC5C8\uC2B5\uB2C8\uB2E4.",
    notAdded: "\uB123\uC740 {tool} \uB0B4\uBCF4\uB0B4\uAE30\uAC00 \uC5C6\uC2B5\uB2C8\uB2E4.",
    list: "\uB123\uC740 \uB0B4\uBCF4\uB0B4\uAE30\uB294 {tools}\uC785\uB2C8\uB2E4.",
    none: "\uB123\uC740 \uC6F9 \uCC44\uD305 \uB0B4\uBCF4\uB0B4\uAE30\uAC00 \uC5C6\uC2B5\uB2C8\uB2E4."
  }
};
var failure4 = (code, message) => Object.assign(new Error(message), { code });
function webToolOf(text) {
  const value = text?.trim().toLowerCase() ?? "";
  if (value === "chatgpt" || value === "web-chatgpt") return "web-chatgpt";
  if (value === "claude" || value === "claude.ai" || value === "web-claude") return "web-claude";
  return null;
}
async function entriesFor(stateDir2) {
  const loaded = await readWebExports(stateDir2);
  return { entries: loaded.entries, broken: loaded.status === "broken" };
}
async function runImportAdd(path, options) {
  const copy2 = COPY5[options.lang];
  const absolute = resolve12(path);
  try {
    await stat9(absolute);
  } catch {
    throw failure4("not-found", `no file at ${absolute}`);
  }
  const { entries, broken } = await entriesFor(options.stateDir);
  const windows = makeWindows(options.clock.nowMs, options.clock.timeZone);
  const keepFrom = windows.collectDates[0];
  const before = options.cache ? await exportKey(absolute, options.clock.timeZone).catch(() => null) : null;
  let exported;
  try {
    exported = await readExport(absolute, options.clock.timeZone, keepFrom);
  } catch (error) {
    if (error instanceof ExportError) throw failure4(error.problem, `not a readable ChatGPT or Claude.ai export: ${error.problem}`);
    throw error;
  }
  const tool = exported.tool;
  const replaced = entries.find((entry) => entry.tool === tool && entry.path !== absolute)?.path ?? null;
  await writeWebExports(options.stateDir, withExport(entries, { tool, path: absolute, addedAt: new Date(options.clock.nowMs).toISOString() }));
  if (options.cache) await primeWebCache(join33(options.stateDir, "cache"), absolute, before, exported, keepFrom, options.clock.timeZone);
  const dateOf = (ms) => ms === null ? null : localDateOf(ms, options.clock.timeZone);
  const added = {
    tool,
    path: absolute,
    conversations: exported.summaries.length,
    requests: exported.totals.requests,
    responses: exported.totals.responses,
    firstDate: dateOf(exported.totals.firstMs),
    lastDate: dateOf(exported.totals.lastMs),
    skipped: exported.skipped.tooLong + exported.skipped.broken + exported.skipped.unrecognized,
    truncated: !exported.complete,
    replaced,
    listReset: broken
  };
  const name = TOOL_NAMES[tool][options.lang];
  const range = added.firstDate !== null && added.lastDate !== null ? fill(copy2.range, { first: added.firstDate, last: added.lastDate }) : "";
  let text = fill(copy2.added, { tool: name, count: added.conversations, range });
  if (replaced !== null) text += copy2.replaced;
  if (added.skipped > 0) text += fill(copy2.skipped, { count: added.skipped });
  if (added.truncated) text += copy2.truncated;
  if (broken) text += copy2.listReset;
  return { action: "add", added, run: { text } };
}
async function runImportRemove(which, options) {
  const tool = webToolOf(which);
  if (tool === null) throw failure4("unknown-tool", `not a web chat: ${which ?? "(none)"}; use chatgpt or claude`);
  const { entries, broken } = await entriesFor(options.stateDir);
  if (broken) {
    await writeWebExports(options.stateDir, []);
    return { action: "remove", removed: null, run: { text: COPY5[options.lang].removedReset } };
  }
  const removed = entries.find((entry) => entry.tool === tool) ?? null;
  if (removed !== null) await writeWebExports(options.stateDir, entries.filter((entry) => entry.tool !== tool));
  const name = TOOL_NAMES[tool][options.lang];
  return { action: "remove", removed, run: { text: fill(removed === null ? COPY5[options.lang].notAdded : COPY5[options.lang].removed, { tool: name }) } };
}
async function runImportList(options) {
  const loaded = await readWebExports(options.stateDir);
  const copy2 = COPY5[options.lang];
  const exports = loaded.entries;
  const text = exports.length === 0 ? copy2.none : fill(copy2.list, { tools: exports.map((entry) => TOOL_NAMES[entry.tool][options.lang]).join(", ") });
  return { action: "list", exports, run: { text } };
}

// src/commands/tune-plan.ts
import { randomBytes as randomBytes2 } from "node:crypto";
import { join as join37 } from "node:path";

// src/tune/items.ts
import { createHash as createHash7 } from "node:crypto";
import { lstat as lstat9, readFile as readFile12 } from "node:fs/promises";
import { dirname as dirname9, join as join34 } from "node:path";
import { isDeepStrictEqual } from "node:util";
var fingerprintOf = (bytes) => createHash7("sha256").update(bytes).digest("hex");
function targetPath(candidate, home) {
  return join34(home, candidate.unit === "A4" ? "config.toml" : "settings.json");
}
async function readTarget(path) {
  const folder = await lstat9(dirname9(path)).then(
    (info) => info.isDirectory(),
    () => false
  );
  let file;
  try {
    file = await lstat9(path);
  } catch (error) {
    const code = error?.code;
    return code === "ENOENT" || code === "ENOTDIR" ? { status: "missing", folder } : { status: "unreadable" };
  }
  try {
    return { status: "ok", bytes: await readFile12(path), regular: file.isFile() && folder };
  } catch {
    return { status: "unreadable" };
  }
}
var hasBom = (bytes) => bytes.length >= 3 && bytes[0] === 239 && bytes[1] === 187 && bytes[2] === 191;
function jsonState(bytes, key) {
  if (hasBom(bytes)) return { present: false, blocked: "byte-order-mark" };
  let doc;
  try {
    doc = JSON.parse(bytes.toString("utf8"));
  } catch {
    return { present: false, blocked: "not-json-object" };
  }
  if (!isObject5(doc)) return { present: false, blocked: "not-json-object" };
  const parent = doc[key.parent];
  if (parent === void 0) return { present: false, blocked: null };
  if (key.kind === "json-list-add") return { present: false, blocked: Array.isArray(parent) ? null : "parent-shape" };
  if (!isObject5(parent)) return { present: false, blocked: "parent-shape" };
  if (!Object.hasOwn(parent, key.name)) return { present: false, blocked: null };
  const value = parent[key.name];
  const ok = key.parent === "skillOverrides" ? typeof value === "string" && SKILL_OVERRIDE_MODES.has(value) : typeof value === "boolean";
  return ok ? { present: true, value, blocked: null } : { present: false, blocked: "value-shape" };
}
function keyPart(text) {
  const part = text.trim();
  if (/^[A-Za-z0-9_-]+$/.test(part)) return part;
  if (/^'[^']*'$/.test(part)) return part.slice(1, -1);
  if (/^"(?:[^"\\]|\\.)*"$/.test(part)) {
    const table = parseCodexConfig(`${part} = 0`);
    const names2 = table === null ? [] : Object.keys(table);
    return names2.length === 1 ? names2[0] : null;
  }
  return null;
}
function splitDotted(text) {
  const parts = [];
  let current = "";
  let quote = null;
  for (let i = 0; i < text.length; i++) {
    const char = text[i];
    if (quote !== null) {
      current += char;
      if (char === "\\" && quote === '"') current += text[++i] ?? "";
      else if (char === quote) quote = null;
    } else if (char === '"' || char === "'") {
      quote = char;
      current += char;
    } else if (char === ".") {
      parts.push(current);
      current = "";
    } else current += char;
  }
  if (quote !== null) return null;
  parts.push(current);
  const keys = parts.map(keyPart);
  return keys.every((key) => key !== null) ? keys : null;
}
function headerKey(line) {
  const start = line.search(/\S/);
  if (start < 0 || line[start] !== "[" || line[start + 1] === "[") return null;
  let i = start + 1;
  while (i < line.length) {
    const char = line[i];
    if (char === '"' || char === "'") {
      let j = i + 1;
      while (j < line.length && line[j] !== char) j += char === '"' && line[j] === "\\" ? 2 : 1;
      if (j >= line.length) return null;
      i = j + 1;
      continue;
    }
    if (char === "]") return /^\s*(?:#.*)?$/.test(line.slice(i + 1)) ? line.slice(start + 1, i) : null;
    i++;
  }
  return null;
}
function scanLine(line, start) {
  let state = start;
  let i = 0;
  while (i < line.length) {
    if (state !== null) {
      if (state === '"""' && line[i] === "\\") {
        i += 2;
        continue;
      }
      if (line.startsWith(state, i)) {
        let end = i + 3;
        while (end < line.length && end - i < 5 && line[end] === state[0]) end++;
        state = null;
        i = end;
      } else i++;
      continue;
    }
    if (line[i] === "#") return null;
    const triple = line.startsWith('"""', i) ? '"""' : line.startsWith("'''", i) ? "'''" : null;
    if (triple !== null) {
      state = triple;
      i += 3;
      continue;
    }
    if (line[i] === '"' || line[i] === "'") {
      const quote = line[i];
      let j = i + 1;
      while (j < line.length && line[j] !== quote) j += quote === '"' && line[j] === "\\" ? 2 : 1;
      if (j >= line.length) return void 0;
      i = j + 1;
      continue;
    }
    i++;
  }
  return state;
}
function tableHeaderCount(text, server) {
  let count = 0;
  let state = null;
  for (const line of text.split(/\r?\n/)) {
    if (state === null) {
      const key = headerKey(line);
      const keys = key === null ? null : splitDotted(key);
      if (keys !== null && keys.length === 2 && keys[0] === "mcp_servers" && keys[1] === server) count++;
    }
    const next = scanLine(line, state);
    if (next === void 0) return -1;
    state = next;
  }
  return state === null ? count : -1;
}
function tomlState(bytes, server) {
  if (hasBom(bytes)) return { present: false, blocked: "byte-order-mark" };
  const text = bytes.toString("utf8");
  const doc = parseCodexConfig(text);
  if (doc === null) return { present: false, blocked: "not-toml" };
  const servers = doc.mcp_servers;
  const table = isTable(servers) ? servers[server] : void 0;
  if (!isTable(table) || tableHeaderCount(text, server) !== 1) return { present: false, blocked: "table-shape" };
  if (!Object.hasOwn(table, "enabled")) return { present: false, blocked: null };
  return typeof table.enabled === "boolean" ? { present: true, value: table.enabled, blocked: null } : { present: false, blocked: "value-shape" };
}
function keyOf(candidate) {
  switch (candidate.unit) {
    case "A1":
      return { kind: "json-entry", parent: "skillOverrides", name: candidate.target };
    case "A2":
      return { kind: "json-entry", parent: "enabledPlugins", name: candidate.target };
    case "A3":
      return { kind: "json-list-add", parent: "deniedMcpServers", entry: { serverName: candidate.target } };
    case "A4":
      return { kind: "toml-table-key", table: candidate.target, key: "enabled" };
  }
}
function nextOf(candidate) {
  switch (candidate.unit) {
    case "A1":
      return "off";
    case "A2":
    case "A4":
      return false;
    case "A3":
      return { serverName: candidate.target };
  }
}
function impactOf(candidate, context) {
  const { target } = candidate;
  switch (candidate.unit) {
    case "A1": {
      const skills = { user: 0, project: 0, plugin: 0 };
      for (const bundle of context.bundles) if (bundle.positions.some((position) => position.recordNames.includes(target))) for (const position of bundle.positions) skills[position.scope]++;
      return { unit: "A1", skills };
    }
    case "A2":
      return { unit: "A2", skills: context.bundles.filter((bundle) => bundle.positions.some((position) => position.pluginId === target)).length };
    case "A3": {
      const sameName = { local: 0, project: 0, claudeAi: 0 };
      for (const { server } of context.servers) {
        if (server.name !== target || !server.enabled) continue;
        if (server.scope === "local") sameName.local++;
        else if (server.scope === "project") sameName.project++;
        else if (server.scope === "claude-ai") sameName.claudeAi++;
      }
      return { unit: "A3", sameName };
    }
    case "A4":
      return { unit: "A4", projects: context.servers.filter(({ server }) => server.name === target && server.enabled && server.scope === "project").length };
  }
}
function stateOf(read, key) {
  if (read.status === "missing") return key.kind !== "toml-table-key" && read.folder ? { present: false, blocked: null } : { present: false, blocked: "file-missing" };
  if (read.status === "unreadable") return { present: false, blocked: "file-unreadable" };
  if (!read.regular) return { present: false, blocked: "not-regular" };
  return key.kind === "toml-table-key" ? tomlState(read.bytes, key.table) : jsonState(read.bytes, key);
}
function blockOf(read, key) {
  return stateOf(read, key).blocked;
}
var sameSlot = (a, b) => a.present === b.present && isDeepStrictEqual(a.present ? a.value : void 0, b.present ? b.value : void 0);
function slotOf(read, key) {
  if (read.status === "unreadable") return null;
  if (read.status === "missing") return { present: false };
  if (hasBom(read.bytes)) return null;
  const text = read.bytes.toString("utf8");
  if (key.kind === "toml-table-key") {
    const servers = parseCodexConfig(text)?.mcp_servers;
    const table = isTable(servers) ? servers[key.table] : void 0;
    if (!isTable(table)) return null;
    return Object.hasOwn(table, "enabled") ? { present: true, value: table.enabled } : { present: false };
  }
  let doc;
  try {
    doc = JSON.parse(text);
  } catch {
    return null;
  }
  if (!isObject5(doc)) return null;
  if (!Object.hasOwn(doc, key.parent)) return { present: false };
  const parent = doc[key.parent];
  if (key.kind === "json-list-add") {
    if (!Array.isArray(parent)) return null;
    return parent.some((item2) => isDeepStrictEqual(item2, key.entry)) ? { present: true } : { present: false };
  }
  if (!isObject5(parent)) return null;
  return Object.hasOwn(parent, key.name) ? { present: true, value: parent[key.name] } : { present: false };
}
function tuneItem(candidate, context, read) {
  const key = keyOf(candidate);
  const state = context.versionOk ? stateOf(read, key) : { present: false, blocked: "unverified-version" };
  return {
    id: candidate.id,
    unit: candidate.unit,
    rule: candidate.rule,
    tool: candidate.tool,
    target: candidate.target,
    file: targetPath(candidate, context.home),
    layer: "user",
    key,
    ...state.present ? { current: state.value } : {},
    next: nextOf(candidate),
    impact: impactOf(candidate, context),
    blocked: state.blocked
  };
}

// src/tune/copy.ts
var TUNE_COPY = {
  en: {
    title: { A1: "Turn off an unused skill: {name}", A2: "Turn off an unused plugin: {name}", A3: "Block an unused MCP server: {name}", A4: "Turn off an unused Codex MCP server: {name}" },
    change: {
      A1: 'In {file}, set {key} under skillOverrides to "off" ({current}).',
      A2: "In {file}, set {key} under enabledPlugins to false ({current}).",
      A3: 'In {file}, add { "serverName": {key} } to the deniedMcpServers list.',
      A4: "In {file}, write enabled = false in the [mcp_servers.{key}] table ({current})."
    },
    current: { none: "now not set", value: "now {value}", unexpected: "now an unexpected value" },
    impact: {
      A1: "This name also turns off {user} {user:skill|skills} in user folders, {project} in projects and {plugin} in plugins. It applies to every project on this PC.",
      A2: "The plugin contains only {skills} {skills:skill|skills}.",
      A3: "Servers with the same name are blocked too: {local} local, {project} project and {claudeAi} claude.ai. It applies to every server with this name on this PC.",
      A4: "It applies to all of Codex. {projects} trusted {projects:project|projects} that {projects:redefines|redefine} this server {projects:is|are} turned off too unless {projects:it sets|they set} enabled."
    },
    undo: "After applying, you can undo this with aq tune undo.",
    blocked: {
      "unverified-version": "This {tool} version is outside the range this tool has verified, so it is not changed automatically. Change it yourself as described above.",
      "file-missing": "The settings file does not exist, so it is not changed automatically. Change it yourself as described above.",
      "file-unreadable": "The settings file could not be read, so it is not changed automatically. Change it yourself as described above.",
      "not-regular": "The settings file or its folder is a link, so it is not changed automatically. Change it yourself as described above.",
      "byte-order-mark": "The settings file starts with a byte order mark, so it is not changed automatically. Change it yourself as described above.",
      "not-json-object": "The settings file is not standard JSON (JSON with comments is not), so it is not changed automatically. Change it yourself as described above.",
      "parent-shape": "{parent} in the settings file is not in the expected shape, so it is not changed automatically. Change it yourself as described above.",
      "value-shape": "The current value is not in the expected shape, so it is not changed automatically. Change it yourself as described above.",
      "not-toml": "config.toml could not be parsed, so it is not changed automatically. Change it yourself as described above.",
      "table-shape": "The [mcp_servers.{key}] table is not written as one multi-line table (it uses an inline table or dotted keys), so it is not changed automatically. Change it yourself as described above."
    },
    notices: {
      not_saved: "This plan was not saved, so it cannot be applied. To apply it, run aq tune plan again without --no-save.",
      plan_unsaved: "The plan could not be written to the state folder ({code}), so it cannot be applied.",
      unfinished_work: "There {count:is|are} {count} unfinished tune {count:run|runs}. The next apply reconciles {count:it|them} with the files first."
    }
  },
  ko: {
    title: { A1: "\uC548 \uC4F0\uB294 \uC2A4\uD0AC \uB044\uAE30: {name}", A2: "\uC548 \uC4F0\uB294 \uD50C\uB7EC\uADF8\uC778 \uB044\uAE30: {name}", A3: "\uC548 \uC4F0\uB294 MCP \uC11C\uBC84 \uB9C9\uAE30: {name}", A4: "Codex\uC758 \uC548 \uC4F0\uB294 MCP \uC11C\uBC84 \uB044\uAE30: {name}" },
    change: {
      A1: '{file}\uC758 skillOverrides\uC5D0\uC11C \uC774\uB984 {key}\uC758 \uAC12\uC744 "off"\uB85C \uBC14\uAFC9\uB2C8\uB2E4({current}).',
      A2: "{file}\uC758 enabledPlugins\uC5D0\uC11C \uC124\uCE58 ID {key}\uC758 \uAC12\uC744 false\uB85C \uBC14\uAFC9\uB2C8\uB2E4({current}).",
      A3: '{file}\uC758 deniedMcpServers \uBAA9\uB85D\uC5D0 { "serverName": {key} } \uD56D\uBAA9\uC744 \uB354\uD569\uB2C8\uB2E4.',
      A4: "{file}\uC758 [mcp_servers.{key}] \uD45C\uC5D0 enabled = false\uB97C \uC801\uC2B5\uB2C8\uB2E4({current})."
    },
    current: { none: "\uC9C0\uAE08\uC740 \uC815\uD558\uC9C0 \uC54A\uC74C", value: "\uC9C0\uAE08\uC740 {value}", unexpected: "\uC9C0\uAE08\uC740 \uC608\uC0C1\uD558\uC9C0 \uBABB\uD55C \uAC12" },
    impact: {
      A1: "\uC774 \uC774\uB984\uC73C\uB85C \uC0AC\uC6A9\uC790 \uD3F4\uB354\uC758 \uC2A4\uD0AC {user}\uAC1C, \uD504\uB85C\uC81D\uD2B8\uC758 \uC2A4\uD0AC {project}\uAC1C, \uD50C\uB7EC\uADF8\uC778\uC758 \uC2A4\uD0AC {plugin}\uAC1C\uAC00 \uD568\uAED8 \uAEBC\uC9D1\uB2C8\uB2E4. \uC774 PC\uC758 \uBAA8\uB4E0 \uD504\uB85C\uC81D\uD2B8\uC5D0 \uB4E3\uC2B5\uB2C8\uB2E4.",
      A2: "\uC774 \uD50C\uB7EC\uADF8\uC778\uC5D0\uB294 \uC2A4\uD0AC {skills}\uAC1C\uB9CC \uB4E4\uC5B4 \uC788\uC2B5\uB2C8\uB2E4.",
      A3: "\uAC19\uC740 \uC774\uB984\uC758 \uB85C\uCEEC \uBC94\uC704 \uC11C\uBC84 {local}\uAC1C, \uD504\uB85C\uC81D\uD2B8 \uBC94\uC704 \uC11C\uBC84 {project}\uAC1C, claude.ai \uC5F0\uACB0 {claudeAi}\uAC1C\uB3C4 \uD568\uAED8 \uB9C9\uD799\uB2C8\uB2E4. \uC774 PC\uC5D0\uC11C \uC774 \uC774\uB984\uC73C\uB85C \uC815\uC758\uB41C \uC11C\uBC84 \uBAA8\uB450\uC5D0 \uB4E3\uC2B5\uB2C8\uB2E4.",
      A4: "Codex \uC804\uCCB4\uC5D0 \uB4E3\uC2B5\uB2C8\uB2E4. \uC774 \uC11C\uBC84\uB97C \uB2E4\uC2DC \uC801\uC740 \uC2E0\uB8B0\uD55C \uD504\uB85C\uC81D\uD2B8 {projects}\uACF3\uB3C4 \uADF8 \uD504\uB85C\uC81D\uD2B8\uAC00 enabled\uB97C \uC801\uC9C0 \uC54A\uC558\uC73C\uBA74 \uD568\uAED8 \uAEBC\uC9D1\uB2C8\uB2E4."
    },
    undo: "\uC801\uC6A9\uD55C \uB4A4 aq tune undo\uB85C \uB418\uB3CC\uB9B4 \uC218 \uC788\uC2B5\uB2C8\uB2E4.",
    blocked: {
      "unverified-version": "{tool}\uC758 \uBC84\uC804\uC774 \uC774 \uB3C4\uAD6C\uAC00 \uD655\uC778\uD55C \uBC94\uC704 \uBC16\uC774\uB77C \uC790\uB3D9\uC73C\uB85C \uACE0\uCE58\uC9C0 \uC54A\uC2B5\uB2C8\uB2E4. \uC704\uC5D0 \uC801\uC740 \uB300\uB85C \uC9C1\uC811 \uBC14\uAFB8\uC138\uC694.",
      "file-missing": "\uC124\uC815 \uD30C\uC77C\uC774 \uC5C6\uC5B4 \uC790\uB3D9\uC73C\uB85C \uACE0\uCE58\uC9C0 \uC54A\uC2B5\uB2C8\uB2E4. \uC704\uC5D0 \uC801\uC740 \uB300\uB85C \uC9C1\uC811 \uBC14\uAFB8\uC138\uC694.",
      "file-unreadable": "\uC124\uC815 \uD30C\uC77C\uC744 \uC77D\uC9C0 \uBABB\uD574 \uC790\uB3D9\uC73C\uB85C \uACE0\uCE58\uC9C0 \uC54A\uC2B5\uB2C8\uB2E4. \uC704\uC5D0 \uC801\uC740 \uB300\uB85C \uC9C1\uC811 \uBC14\uAFB8\uC138\uC694.",
      "not-regular": "\uC124\uC815 \uD30C\uC77C\uC774\uB098 \uADF8 \uD3F4\uB354\uAC00 \uB9C1\uD06C\uB77C \uC790\uB3D9\uC73C\uB85C \uACE0\uCE58\uC9C0 \uC54A\uC2B5\uB2C8\uB2E4. \uC704\uC5D0 \uC801\uC740 \uB300\uB85C \uC9C1\uC811 \uBC14\uAFB8\uC138\uC694.",
      "byte-order-mark": "\uC124\uC815 \uD30C\uC77C\uC774 \uBC14\uC774\uD2B8 \uC21C\uC11C \uD45C\uC2DC\uB85C \uC2DC\uC791\uD574 \uC790\uB3D9\uC73C\uB85C \uACE0\uCE58\uC9C0 \uC54A\uC2B5\uB2C8\uB2E4. \uC704\uC5D0 \uC801\uC740 \uB300\uB85C \uC9C1\uC811 \uBC14\uAFB8\uC138\uC694.",
      "not-json-object": "\uC124\uC815 \uD30C\uC77C\uC774 \uD45C\uC900 JSON\uC774 \uC544\uB2C8\uC5B4\uC11C(\uC8FC\uC11D\uC774 \uB4E0 JSON\uB3C4 \uADF8\uB807\uC2B5\uB2C8\uB2E4) \uC790\uB3D9\uC73C\uB85C \uACE0\uCE58\uC9C0 \uC54A\uC2B5\uB2C8\uB2E4. \uC704\uC5D0 \uC801\uC740 \uB300\uB85C \uC9C1\uC811 \uBC14\uAFB8\uC138\uC694.",
      "parent-shape": "\uC124\uC815 \uD30C\uC77C\uC758 {parent}\uAC00 \uC608\uC0C1\uD55C \uAF34\uC774 \uC544\uB2C8\uB77C \uC790\uB3D9\uC73C\uB85C \uACE0\uCE58\uC9C0 \uC54A\uC2B5\uB2C8\uB2E4. \uC704\uC5D0 \uC801\uC740 \uB300\uB85C \uC9C1\uC811 \uBC14\uAFB8\uC138\uC694.",
      "value-shape": "\uC9C0\uAE08 \uAC12\uC774 \uC608\uC0C1\uD55C \uAF34\uC774 \uC544\uB2C8\uB77C \uC790\uB3D9\uC73C\uB85C \uACE0\uCE58\uC9C0 \uC54A\uC2B5\uB2C8\uB2E4. \uC704\uC5D0 \uC801\uC740 \uB300\uB85C \uC9C1\uC811 \uBC14\uAFB8\uC138\uC694.",
      "not-toml": "config.toml\uC744 \uD480\uC9C0 \uBABB\uD574 \uC790\uB3D9\uC73C\uB85C \uACE0\uCE58\uC9C0 \uC54A\uC2B5\uB2C8\uB2E4. \uC704\uC5D0 \uC801\uC740 \uB300\uB85C \uC9C1\uC811 \uBC14\uAFB8\uC138\uC694.",
      "table-shape": "[mcp_servers.{key}] \uD45C\uAC00 \uBA38\uB9AC \uD558\uB098\uB85C \uC5EC\uB7EC \uC904\uC5D0 \uC801\uD600 \uC788\uC9C0 \uC54A\uC544(\uC778\uB77C\uC778 \uD45C\uB098 \uC810 \uC5F4\uC1E0\uB85C \uC801\uC740 \uAC83) \uC790\uB3D9\uC73C\uB85C \uACE0\uCE58\uC9C0 \uC54A\uC2B5\uB2C8\uB2E4. \uC704\uC5D0 \uC801\uC740 \uB300\uB85C \uC9C1\uC811 \uBC14\uAFB8\uC138\uC694."
    },
    notices: {
      not_saved: "\uC800\uC7A5\uD558\uC9C0 \uC54A\uC740 \uACC4\uD68D\uC774\uB77C \uC801\uC6A9\uD560 \uC218 \uC5C6\uC2B5\uB2C8\uB2E4. \uC801\uC6A9\uD558\uB824\uBA74 --no-save \uC5C6\uC774 \uB2E4\uC2DC \uACC4\uD68D\uD558\uC138\uC694.",
      plan_unsaved: "\uC0C1\uD0DC \uD3F4\uB354\uC5D0 \uACC4\uD68D\uC744 \uC4F0\uC9C0 \uBABB\uD574({code}) \uC801\uC6A9\uD560 \uC218 \uC5C6\uC2B5\uB2C8\uB2E4.",
      unfinished_work: "\uB05D\uB098\uC9C0 \uC54A\uC740 \uC815\uBE44 \uC791\uC5C5\uC774 {count}\uAC1C \uC788\uC2B5\uB2C8\uB2E4. \uB2E4\uC74C \uC801\uC6A9 \uB54C \uBA3C\uC800 \uC2E4\uC81C \uD30C\uC77C\uB85C \uB9DE\uCDA5\uB2C8\uB2E4."
    }
  }
};
function impactValues(item2) {
  const impact = item2.impact;
  switch (impact.unit) {
    case "A1":
      return impact.skills;
    case "A2":
      return { skills: impact.skills };
    case "A3":
      return impact.sameName;
    case "A4":
      return { projects: impact.projects };
  }
}
function tomlString(text) {
  const short = { "\\": "\\\\", '"': '\\"', "\b": "\\b", "	": "\\t", "\n": "\\n", "\f": "\\f", "\r": "\\r" };
  return `"${text.replace(/[\\"\u0000-\u001f\u007f]/g, (char) => short[char] ?? `\\u${char.charCodeAt(0).toString(16).toUpperCase().padStart(4, "0")}`)}"`;
}
function keyText(key) {
  switch (key.kind) {
    case "json-entry":
      return JSON.stringify(key.name);
    case "json-list-add":
      return JSON.stringify(key.entry.serverName);
    case "toml-table-key":
      return /^[A-Za-z0-9_-]+$/.test(key.table) ? key.table : tomlString(key.table);
  }
}
function blockedText(block, key, tool, lang) {
  const parent = key.kind === "toml-table-key" ? "mcp_servers" : key.parent;
  return fill(TUNE_COPY[lang].blocked[block], { tool: TOOL_NAMES[tool][lang], parent, key: keyText(key) });
}
function tuneItemText(item2, lang) {
  const copy2 = TUNE_COPY[lang];
  const current = item2.blocked === "value-shape" ? copy2.current.unexpected : "current" in item2 ? fill(copy2.current.value, { value: JSON.stringify(item2.current) }) : copy2.current.none;
  const key = keyText(item2.key);
  return {
    title: fill(copy2.title[item2.unit], { name: item2.target }),
    change: fill(copy2.change[item2.unit], { file: item2.file, key, current }),
    impact: fill(copy2.impact[item2.unit], impactValues(item2)),
    blocked: item2.blocked === null ? null : blockedText(item2.blocked, item2.key, item2.tool, lang),
    undo: item2.blocked === null ? copy2.undo : null
  };
}
function tuneNoticeText(notice, lang) {
  const lines = TUNE_COPY[lang].notices;
  switch (notice.kind) {
    case "not_saved":
      return lines.not_saved;
    case "plan_unsaved":
      return fill(lines.plan_unsaved, { code: notice.code });
    case "unfinished_work":
      return fill(lines.unfinished_work, { count: notice.count });
  }
}
var WORK_COPY = {
  en: {
    written: { apply: "Changed.", undo: "Undone." },
    verified: "Verified. The value is still in place and the item is off in every layer when judged again.",
    undone: "Undone later.",
    writtenOnResume: "The run was interrupted, but the file shows the change was written.",
    unknown: "The run was interrupted and the result is unknown. Check the file yourself.",
    checkFailed: "Not written because the check before the change failed. This may be a fault in this tool.",
    notApplied: {
      "no-longer-candidate": "Not changed because it is no longer a candidate when judged again. Plan again.",
      "plan-differs": "Not changed because the place or value differs from the plan now. Plan again.",
      "changed-since-plan": "Not changed because the file changed after the plan. Plan again.",
      "changed-before-write": "Not changed because the file changed just before the write. Plan again.",
      "already-set": "Not changed because it already has that value.",
      "changed-since-apply": "Not overwritten because the value changed after the apply. Look at the current value and decide yourself.",
      "not-written": "Nothing to undo because this item was not applied.",
      "interrupted": "The run was interrupted before the change, so it is recorded as not applied."
    },
    writeFailed: "The file could not be replaced ({code}).",
    notices: {
      reconciled: "Reconciled {count} unfinished tune {count:run|runs} with the files.",
      overwritten: "Another program wrote {path} again after the change. Check it with aq tune verify.",
      replan: "Some items were not changed. Plan again with aq tune plan.",
      "new-session": "Claude Code sessions that are already open may not pick this up. Check in a new session.",
      "restart-codex": "Codex needs a restart to apply this."
    },
    verify: {
      ok: "Still off.",
      changed: "The value changed after the apply. Check the current settings.",
      still: "The file still has the value, but it is still on when judged again. Another settings layer, such as a project's settings, may turn it back on."
    }
  },
  ko: {
    written: { apply: "\uBC14\uAFE8\uC2B5\uB2C8\uB2E4.", undo: "\uB418\uB3CC\uB838\uC2B5\uB2C8\uB2E4." },
    verified: "\uD655\uC778\uD588\uC2B5\uB2C8\uB2E4. \uAC12\uC774 \uADF8\uB300\uB85C\uC774\uACE0 \uB2E4\uC2DC \uD310\uC815\uD574\uB3C4 \uC5B4\uB290 \uCE35\uC5D0\uC11C\uB3C4 \uAEBC\uC838 \uC788\uC2B5\uB2C8\uB2E4.",
    undone: "\uADF8 \uB4A4\uC5D0 \uB418\uB3CC\uB838\uC2B5\uB2C8\uB2E4.",
    writtenOnResume: "\uB04A\uAE34 \uC791\uC5C5\uC774\uC9C0\uB9CC \uD30C\uC77C\uC5D0 \uC4F4 \uAC83\uC744 \uD655\uC778\uD588\uC2B5\uB2C8\uB2E4.",
    unknown: "\uB04A\uAE34 \uC791\uC5C5\uC774\uB77C \uACB0\uACFC\uB97C \uBAA8\uB985\uB2C8\uB2E4. \uD30C\uC77C\uC744 \uC9C1\uC811 \uD655\uC778\uD558\uC138\uC694.",
    checkFailed: "\uBC14\uAFB8\uAE30 \uC804 \uAC80\uC0AC\uC5D0\uC11C \uAC78\uB824 \uC4F0\uC9C0 \uC54A\uC558\uC2B5\uB2C8\uB2E4. \uC774 \uB3C4\uAD6C\uC758 \uC798\uBABB\uC77C \uC218 \uC788\uC2B5\uB2C8\uB2E4.",
    notApplied: {
      "no-longer-candidate": "\uB2E4\uC2DC \uD310\uC815\uD558\uB2C8 \uB354\uB294 \uD6C4\uBCF4\uAC00 \uC544\uB2C8\uC5B4\uC11C \uBC14\uAFB8\uC9C0 \uC54A\uC558\uC2B5\uB2C8\uB2E4. \uB2E4\uC2DC \uACC4\uD68D\uD558\uC138\uC694.",
      "plan-differs": "\uACC4\uD68D\uD55C \uB4A4 \uBC14\uAFC0 \uC790\uB9AC\uB098 \uAC12\uC774 \uB2EC\uB77C\uC838 \uBC14\uAFB8\uC9C0 \uC54A\uC558\uC2B5\uB2C8\uB2E4. \uB2E4\uC2DC \uACC4\uD68D\uD558\uC138\uC694.",
      "changed-since-plan": "\uACC4\uD68D\uD55C \uB4A4 \uD30C\uC77C\uC774 \uBC14\uB00C\uC5B4 \uBC14\uAFB8\uC9C0 \uC54A\uC558\uC2B5\uB2C8\uB2E4. \uB2E4\uC2DC \uACC4\uD68D\uD558\uC138\uC694.",
      "changed-before-write": "\uBC14\uAFB8\uAE30 \uBC14\uB85C \uC55E\uC5D0\uC11C \uD30C\uC77C\uC774 \uBC14\uB00C\uC5B4 \uBC14\uAFB8\uC9C0 \uC54A\uC558\uC2B5\uB2C8\uB2E4. \uB2E4\uC2DC \uACC4\uD68D\uD558\uC138\uC694.",
      "already-set": "\uC774\uBBF8 \uADF8 \uAC12\uC774\uB77C \uBC14\uAFB8\uC9C0 \uC54A\uC558\uC2B5\uB2C8\uB2E4.",
      "changed-since-apply": "\uC801\uC6A9\uD55C \uB4A4 \uADF8 \uAC12\uC774 \uBC14\uB00C\uC5B4 \uB36E\uC5B4\uC4F0\uC9C0 \uC54A\uC558\uC2B5\uB2C8\uB2E4. \uC9C0\uAE08 \uAC12\uC744 \uBCF4\uACE0 \uC9C1\uC811 \uC815\uD558\uC138\uC694.",
      "not-written": "\uC801\uC6A9\uB418\uC9C0 \uC54A\uC740 \uD56D\uBAA9\uC774\uB77C \uB418\uB3CC\uB9B4 \uAC83\uC774 \uC5C6\uC2B5\uB2C8\uB2E4.",
      "interrupted": "\uBC14\uAFB8\uAE30 \uC804\uC5D0 \uB04A\uAE34 \uC791\uC5C5\uC774\uB77C \uC801\uC6A9 \uC548 \uB428\uC73C\uB85C \uB9DE\uCDC4\uC2B5\uB2C8\uB2E4."
    },
    writeFailed: "\uD30C\uC77C\uC744 \uAC08\uC544 \uB07C\uC6B0\uC9C0 \uBABB\uD588\uC2B5\uB2C8\uB2E4({code}).",
    notices: {
      reconciled: "\uB05D\uB098\uC9C0 \uC54A\uC740 \uC815\uBE44 \uC791\uC5C5 {count}\uAC1C\uB97C \uC2E4\uC81C \uD30C\uC77C\uB85C \uB9DE\uCDC4\uC2B5\uB2C8\uB2E4.",
      overwritten: "{path}\uB97C \uBC14\uAFBC \uB4A4 \uB2E4\uB978 \uD504\uB85C\uADF8\uB7A8\uC774 \uB2E4\uC2DC \uC37C\uC2B5\uB2C8\uB2E4. aq tune verify\uB85C \uD655\uC778\uD558\uC138\uC694.",
      replan: "\uBC14\uAFB8\uC9C0 \uC54A\uC740 \uD56D\uBAA9\uC774 \uC788\uC2B5\uB2C8\uB2E4. aq tune plan\uC73C\uB85C \uB2E4\uC2DC \uACC4\uD68D\uD558\uC138\uC694.",
      "new-session": "Claude Code\uB294 \uC9C0\uAE08 \uB5A0 \uC788\uB294 \uC138\uC158\uC5D0\uB294 \uBC14\uB85C \uC801\uC6A9\uB418\uC9C0 \uC54A\uC744 \uC218 \uC788\uC2B5\uB2C8\uB2E4. \uC0C8 \uC138\uC158\uC5D0\uC11C \uD655\uC778\uD558\uC138\uC694.",
      "restart-codex": "Codex\uB294 \uB2E4\uC2DC \uC2DC\uC791\uD574\uC57C \uC801\uC6A9\uB429\uB2C8\uB2E4."
    },
    verify: {
      ok: "\uADF8\uB300\uB85C \uAEBC\uC838 \uC788\uC2B5\uB2C8\uB2E4.",
      changed: "\uBC14\uAFBC \uAC12\uC774 \uADF8 \uB4A4\uC5D0 \uB2EC\uB77C\uC84C\uC2B5\uB2C8\uB2E4. \uC9C0\uAE08 \uC124\uC815\uC744 \uD655\uC778\uD558\uC138\uC694.",
      still: "\uD30C\uC77C\uC5D0\uB294 \uADF8\uB300\uB85C\uC9C0\uB9CC \uB2E4\uC2DC \uD310\uC815\uD574\uB3C4 \uCF1C\uC838 \uC788\uC2B5\uB2C8\uB2E4. \uB2E4\uB978 \uC124\uC815 \uCE35(\uD504\uB85C\uC81D\uD2B8 \uC124\uC815 \uAC19\uC740 \uAC83)\uC774 \uB2E4\uC2DC \uCF1C\uACE0 \uC788\uC744 \uC218 \uC788\uC2B5\uB2C8\uB2E4."
    }
  }
};
var isNotAppliedReason = (reason) => reason !== null && Object.hasOwn(WORK_COPY.en.notApplied, reason);
var isBlock = (reason) => reason !== null && Object.hasOwn(TUNE_COPY.en.blocked, reason);
function workItemText(item2, kind, lang) {
  const copy2 = WORK_COPY[lang];
  switch (item2.state) {
    case "written":
      return item2.reason === "interrupted" ? copy2.writtenOnResume : copy2.written[kind];
    case "verified":
      return copy2.verified;
    case "undone":
      return copy2.undone;
    case "unknown":
      return copy2.unknown;
    case "rejected":
      return isBlock(item2.reason) ? blockedText(item2.reason, item2.key, item2.tool, lang) : copy2.checkFailed;
    case "not_applied":
      return isNotAppliedReason(item2.reason) ? copy2.notApplied[item2.reason] : fill(copy2.writeFailed, { code: item2.reason ?? "unknown" });
    case "planned":
    case "writing":
      return copy2.unknown;
  }
}
function workNoticeText(notice, lang) {
  const lines = WORK_COPY[lang].notices;
  if (notice.kind === "reconciled") return fill(lines.reconciled, { count: notice.count });
  if (notice.kind === "overwritten") return fill(lines.overwritten, { path: notice.path });
  return lines[notice.kind];
}
function verifyText(result, lang) {
  const copy2 = WORK_COPY[lang].verify;
  if (!result.kept) return copy2.changed;
  return result.stillOn ? copy2.still : copy2.ok;
}

// src/tune/plan.ts
import { mkdir as mkdir8 } from "node:fs/promises";
import { join as join35 } from "node:path";
var TUNE_VERIFIED = {
  "claude-code": { from: "2.1.220", to: "2.1.325" },
  codex: { from: "0.166.0", to: "0.166.0" },
  // 제미나이는 정비하지 않는다. 기록에 버전이 없어 늘 범위 밖이다(설계 「0.4.0에서 정한 것」)
  gemini: { from: "0.68.0", to: "0.68.0" },
  // 웹 채팅은 셋팅이 없어 정비하지 않는다(설계 「0.5.0에서 정한 것」)
  "web-chatgpt": null,
  "web-claude": null
};
function versionVerified(tool, version) {
  const parsed = parseVersion(version);
  if (parsed === null) return false;
  const range = TUNE_VERIFIED[tool];
  if (range === null) return false;
  return compareVersions(parsed, parseVersion(range.from)) >= 0 && compareVersions(parsed, parseVersion(range.to)) <= 0;
}
function planIdOf(nowMs, random) {
  return `${resultStamp(nowMs)}-${random}`;
}
var PLANS_DIR = join35("tune", "plans");
async function writePlan(stateDir2, plan) {
  const dir = join35(stateDir2, PLANS_DIR);
  await mkdir8(dir, { recursive: true });
  const path = join35(dir, `${plan.planId}.json`);
  await writeJson(path, plan);
  return path;
}

// src/tune/work.ts
import { chmod, mkdir as mkdir9, open as open8, readdir as readdir10, readFile as readFile13, rename as rename7, rm as rm6, unlink as unlink2 } from "node:fs/promises";
import { join as join36 } from "node:path";
var ID_PATTERN = /^\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}-\d{3}Z-[0-9a-f]{6}$/;
var TUNE_DIR = "tune";
var LOCK_FILE = join36(TUNE_DIR, "lock");
async function writeDurable(path, data, mode) {
  const temporary = `${path}.${process.pid}.tmp`;
  try {
    const handle = await open8(temporary, "w");
    try {
      await handle.writeFile(data);
      await handle.sync();
    } finally {
      await handle.close();
    }
    if (mode !== void 0 && process.platform !== "win32") await chmod(temporary, mode);
    await rename7(temporary, path);
  } catch (error) {
    await rm6(temporary, { force: true }).catch(() => void 0);
    throw error;
  }
}
var workPath = (stateDir2, workId) => join36(stateDir2, TUNE_DIR, `${workId}.json`);
async function saveWork(stateDir2, work) {
  await mkdir9(join36(stateDir2, TUNE_DIR), { recursive: true });
  await writeDurable(workPath(stateDir2, work.workId), `${JSON.stringify(work, null, 2)}
`);
}
var isWork = (value) => {
  const work = value;
  return typeof work === "object" && work !== null && typeof work.workId === "string" && Array.isArray(work.items) && Array.isArray(work.files);
};
async function loadWork(stateDir2, workId) {
  if (!ID_PATTERN.test(workId)) return null;
  try {
    const value = JSON.parse(await readFile13(workPath(stateDir2, workId), "utf8"));
    return isWork(value) && value.workId === workId ? value : null;
  } catch {
    return null;
  }
}
async function listWorks(stateDir2) {
  let names2;
  try {
    names2 = await readdir10(join36(stateDir2, TUNE_DIR));
  } catch {
    return [];
  }
  const works = [];
  for (const name of names2.sort()) {
    if (!name.endsWith(".json")) continue;
    const work = await loadWork(stateDir2, name.slice(0, -".json".length));
    if (work !== null) works.push(work);
  }
  return works;
}
var unfinished = (work) => work.items.some((item2) => item2.state === "planned" || item2.state === "writing");
function isAlive(pid) {
  try {
    process.kill(pid, 0);
    return true;
  } catch (error) {
    return error.code === "EPERM";
  }
}
async function takeLock(stateDir2, alive = isAlive) {
  const path = join36(stateDir2, LOCK_FILE);
  await mkdir9(join36(stateDir2, TUNE_DIR), { recursive: true });
  for (let attempt = 0; attempt < 2; attempt++) {
    try {
      const handle = await open8(path, "wx");
      try {
        await handle.writeFile(JSON.stringify({ pid: process.pid, at: (/* @__PURE__ */ new Date()).toISOString() }));
      } finally {
        await handle.close();
      }
      return { release: () => unlink2(path).catch(() => void 0) };
    } catch (error) {
      if (error.code !== "EEXIST") throw error;
    }
    let pid;
    try {
      pid = JSON.parse(await readFile13(path, "utf8")).pid;
    } catch {
      return null;
    }
    if (typeof pid !== "number" || alive(pid)) return null;
    await unlink2(path).catch(() => void 0);
  }
  return null;
}
async function reconcileWorks(stateDir2, read = readTarget) {
  const done = [];
  for (const work of await listWorks(stateDir2)) {
    if (!unfinished(work)) continue;
    for (const file of work.files) {
      const pending = work.items.filter((item2) => item2.file === file.path && (item2.state === "planned" || item2.state === "writing"));
      if (pending.length === 0) continue;
      let state = "not_applied";
      if (file.candidate !== null) {
        const now = await read(file.path);
        const fingerprint = now.status === "ok" ? fingerprintOf(now.bytes) : now.status === "missing" ? null : void 0;
        state = fingerprint === file.candidate ? "written" : fingerprint === file.before ? "not_applied" : "unknown";
      }
      for (const item2 of pending) {
        item2.state = state;
        item2.reason = "interrupted";
      }
    }
    for (const item2 of work.items) {
      if (item2.state !== "planned" && item2.state !== "writing") continue;
      item2.state = "not_applied";
      item2.reason = "interrupted";
    }
    await saveWork(stateDir2, work);
    done.push(work.workId);
  }
  return done;
}

// src/commands/tune-plan.ts
var codeOf2 = (error) => error?.code ?? "unknown";
async function judgeTune(options) {
  const opened = await openState(options.stateDir);
  const gathered = await gatherCheckupInput({
    env: options.env,
    homedir: options.homedir,
    tmpdir: options.tmpdir,
    platform: options.platform,
    clock: options.clock,
    cacheDir: options.cache ? join37(options.stateDir, "cache") : null,
    rescan: options.rescan,
    state: opened.state,
    self: await selfIdentity(options.entryFile),
    ...options.managedDir === void 0 ? {} : { managedDir: options.managedDir }
  });
  const evaluation = evaluate(gathered.input);
  const reads = /* @__PURE__ */ new Map();
  const items = [];
  for (const candidate of evaluation.candidates) {
    const input = setupTools(gathered.input.tools).find((tool) => tool.tool === candidate.tool);
    const judged = evaluation.tools.find((tool) => tool.tool === candidate.tool);
    const home = input.setup.home;
    const path = targetPath(candidate, home);
    if (!reads.has(path)) reads.set(path, await readTarget(path));
    const context = { home, bundles: judged.skills, servers: judged.servers, versionOk: versionVerified(candidate.tool, highestMainVersion(input.summaries)) };
    items.push(tuneItem(candidate, context, reads.get(path)));
  }
  return { items, reads, evaluation, input: gathered.input };
}
async function runTunePlan(options) {
  const now = options.now ?? Date.now;
  const started = now();
  const { items, reads } = await judgeTune({ ...options, cache: options.save });
  const files = [...reads].map(([path, read]) => ({ path, status: read.status, fingerprint: read.status === "ok" ? fingerprintOf(read.bytes) : null, items: items.filter((item2) => item2.file === path).map((item2) => item2.id) }));
  const base = { createdAt: new Date(options.clock.nowMs).toISOString(), appVersion: PROGRAM_VERSION, items, files };
  const notices2 = [];
  const pending = (await listWorks(options.stateDir)).filter(unfinished).length;
  if (pending > 0) notices2.push({ kind: "unfinished_work", count: pending });
  let plan = { planId: null, ...base };
  if (options.save) {
    const planId = planIdOf(options.clock.nowMs, options.random?.() ?? randomBytes2(3).toString("hex"));
    try {
      await writePlan(options.stateDir, { planId, ...base });
      plan = { planId, ...base };
    } catch (error) {
      notices2.push({ kind: "plan_unsaved", code: codeOf2(error) });
    }
  } else {
    notices2.push({ kind: "not_saved" });
  }
  const text = { items: Object.fromEntries(items.map((item2) => [item2.id, tuneItemText(item2, options.lang)])), notices: notices2.map((notice) => tuneNoticeText(notice, options.lang)) };
  return { plan, run: { durationMs: now() - started, saved: plan.planId !== null, notices: notices2, text } };
}

// src/commands/tune-run.ts
import { randomBytes as randomBytes3 } from "node:crypto";
import { readFile as readFile14 } from "node:fs/promises";
import { join as join38 } from "node:path";
import { isDeepStrictEqual as isDeepStrictEqual4 } from "node:util";

// src/tune/engine.ts
import { stat as stat10 } from "node:fs/promises";

// src/tune/json-edit.ts
import { isDeepStrictEqual as isDeepStrictEqual2 } from "node:util";
var SCALAR = /-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?|true|false|null/y;
function tokensOf(text) {
  const tokens = [];
  let i = 0;
  while (i < text.length) {
    const char = text[i];
    if (char === " " || char === "	" || char === "\n" || char === "\r") {
      i++;
      continue;
    }
    if (char === "{" || char === "}" || char === "[" || char === "]" || char === ":" || char === ",") {
      tokens.push({ type: char, start: i, end: i + 1 });
      i++;
      continue;
    }
    if (char === '"') {
      let j = i + 1;
      while (j < text.length && text[j] !== '"') j += text[j] === "\\" ? 2 : 1;
      if (j >= text.length) return null;
      tokens.push({ type: "string", start: i, end: j + 1 });
      i = j + 1;
      continue;
    }
    SCALAR.lastIndex = i;
    const match = SCALAR.exec(text);
    if (match === null) return null;
    tokens.push({ type: "scalar", start: i, end: i + match[0].length });
    i += match[0].length;
  }
  return tokens;
}
function treeOf(text) {
  const tokens = tokensOf(text);
  if (tokens === null) return null;
  let at = 0;
  const value = () => {
    const token = tokens[at++];
    if (token === void 0) return null;
    if (token.type === "string" || token.type === "scalar") return { type: "value", start: token.start, end: token.end };
    if (token.type !== "{" && token.type !== "[") return null;
    const close = token.type === "{" ? "}" : "]";
    const members = [];
    const items = [];
    const done = (end) => token.type === "{" ? { type: "object", start: token.start, end, members } : { type: "array", start: token.start, end, items };
    if (tokens[at]?.type === close) return done(tokens[at++].end);
    for (; ; ) {
      if (token.type === "{") {
        const key = tokens[at++];
        if (key?.type !== "string" || tokens[at++]?.type !== ":") return null;
        const inner = value();
        if (inner === null) return null;
        members.push({ key: JSON.parse(text.slice(key.start, key.end)), start: key.start, value: inner });
      } else {
        const inner = value();
        if (inner === null) return null;
        items.push(inner);
      }
      const sep2 = tokens[at++];
      if (sep2?.type === close) return done(sep2.end);
      if (sep2?.type !== ",") return null;
    }
  };
  try {
    const root = value();
    return root !== null && at === tokens.length ? root : null;
  } catch {
    return null;
  }
}
var eolOf = (text) => text.includes("\r\n") ? "\r\n" : "\n";
function unitOf(text) {
  let unit = null;
  for (const line of text.split(/\r?\n/)) {
    const indent = /^[ \t]+(?=\S)/.exec(line)?.[0];
    if (indent === void 0) continue;
    if (indent.startsWith("	")) return "	";
    if (unit === null || indent.length < unit.length) unit = indent;
  }
  return unit ?? "  ";
}
var indentAt = (text, pos) => /^[ \t]*/.exec(text.slice(text.lastIndexOf("\n", pos - 1) + 1))[0];
var containerText = (open9, close, entries, indent, style) => {
  if (indent === null) return `${open9}${entries.map((entry) => entry(null)).join(", ")}${close}`;
  const inner = indent + style.unit;
  return `${open9}${style.eol}${entries.map((entry) => inner + entry(inner)).join(`,${style.eol}`)}${style.eol}${indent}${close}`;
};
var member = (key, value) => (indent) => `${JSON.stringify(key)}: ${value(indent)}`;
var scalar = (value) => () => JSON.stringify(value);
var serverEntry = (serverName) => () => `{ "serverName": ${JSON.stringify(serverName)} }`;
var spansOf = (node) => node.type === "object" ? node.members.map((m) => ({ start: m.start, end: m.value.end })) : node.items;
var bracketsOf = (node) => node.type === "object" ? ["{", "}"] : ["[", "]"];
function insertInto(text, node, entry, style, multiline) {
  const spans = spansOf(node);
  const [open9, close] = bracketsOf(node);
  const last = spans[spans.length - 1];
  if (last === void 0) return { start: node.start, end: node.end, text: containerText(open9, close, [entry], multiline ? indentAt(text, node.start) : null, style) };
  if (text.slice(node.start, spans[0].start).includes("\n")) {
    const indent = indentAt(text, last.start);
    return { start: last.end, end: last.end, text: `,${style.eol}${indent}${entry(indent)}` };
  }
  return { start: last.end, end: last.end, text: `, ${entry(null)}` };
}
function removeAt(node, index) {
  const spans = spansOf(node);
  const [open9, close] = bracketsOf(node);
  if (spans.length === 1) return { start: node.start, end: node.end, text: open9 + close };
  if (index > 0) return { start: spans[index - 1].end, end: spans[index].end, text: "" };
  return { start: spans[0].start, end: spans[1].start, text: "" };
}
function lastIndexOf(node, key) {
  for (let i = node.members.length - 1; i >= 0; i--) if (node.members[i].key === key) return i;
  return -1;
}
function editOne(text, op) {
  const root = treeOf(text);
  if (root === null || root.type !== "object") return null;
  const style = { eol: eolOf(text), unit: unitOf(text) };
  const multiline = text.slice(root.start, root.end).includes("\n");
  const parentAt = lastIndexOf(root, op.parent);
  let edit;
  if (parentAt < 0) {
    if (op.op === "delete" || op.op === "remove") return null;
    const child = op.op === "append" ? serverEntry(op.entry.serverName) : member(op.name, scalar(op.value));
    const open9 = op.op === "append" ? "[" : "{";
    const close = op.op === "append" ? "]" : "}";
    edit = insertInto(text, root, member(op.parent, (indent) => containerText(open9, close, [child], indent, style)), style, multiline);
  } else {
    const node = root.members[parentAt].value;
    if (op.op === "append" || op.op === "remove") {
      if (node.type !== "array") return null;
      if (op.op === "append") edit = insertInto(text, node, serverEntry(op.entry.serverName), style, multiline);
      else {
        let index = -1;
        for (let i = node.items.length - 1; i >= 0 && index < 0; i--) {
          const item2 = node.items[i];
          if (isDeepStrictEqual2(JSON.parse(text.slice(item2.start, item2.end)), { serverName: op.entry.serverName })) index = i;
        }
        if (index < 0) return null;
        edit = removeAt(node, index);
      }
    } else {
      if (node.type !== "object") return null;
      const at = lastIndexOf(node, op.name);
      if (op.op === "delete") {
        if (at < 0) return null;
        edit = removeAt(node, at);
      } else if (at >= 0) {
        const value = node.members[at].value;
        edit = { start: value.start, end: value.end, text: JSON.stringify(op.value) };
      } else edit = insertInto(text, node, member(op.name, scalar(op.value)), style, multiline);
    }
  }
  return text.slice(0, edit.start) + edit.text + text.slice(edit.end);
}
function editJson(original, ops) {
  let text = original ?? "{\n}\n";
  for (const op of ops) {
    if (text === null) return null;
    text = editOne(text, op);
  }
  return text;
}
var define = (target, key, value) => {
  Object.defineProperty(target, key, { value, enumerable: true, writable: true, configurable: true });
};
function jsonMeaningOk(original, candidate, ops) {
  let expected;
  let actual;
  try {
    expected = original === null ? {} : JSON.parse(original);
    actual = JSON.parse(candidate);
  } catch {
    return false;
  }
  if (!isObject5(expected)) return false;
  for (const op of ops) {
    if (!Object.hasOwn(expected, op.parent)) {
      if (op.op === "delete" || op.op === "remove") return false;
      define(expected, op.parent, op.op === "append" ? [] : {});
    }
    const parent = expected[op.parent];
    if (op.op === "set" || op.op === "delete") {
      if (!isObject5(parent)) return false;
      if (op.op === "set") define(parent, op.name, op.value);
      else if (!Object.hasOwn(parent, op.name)) return false;
      else delete parent[op.name];
    } else {
      if (!Array.isArray(parent)) return false;
      if (op.op === "append") parent.push({ serverName: op.entry.serverName });
      else {
        let index = -1;
        for (let i = parent.length - 1; i >= 0 && index < 0; i--) if (isDeepStrictEqual2(parent[i], { serverName: op.entry.serverName })) index = i;
        if (index < 0) return false;
        parent.splice(index, 1);
      }
    }
  }
  return isDeepStrictEqual2(expected, actual);
}

// src/tune/toml-edit.ts
import { isDeepStrictEqual as isDeepStrictEqual3 } from "node:util";
var ENABLED = /^(\s*(?:enabled|"enabled"|'enabled')\s*=\s*)(true|false)(?=\s*(?:#.*)?$)/;
function linesOf(text) {
  const parts = text.split(/(\r?\n)/);
  const lines = [];
  let state = null;
  for (let i = 0; i < parts.length; i += 2) {
    const line = parts[i];
    lines.push({ text: line, eol: parts[i + 1] ?? "", inString: state !== null });
    const next = scanLine(line, state);
    if (next === void 0) return null;
    state = next;
  }
  return state === null ? lines : null;
}
var isHeader = (line) => !line.inString && headerKey(line.text) !== null;
function isHeaderOf(line, table) {
  if (line.inString) return false;
  const key = headerKey(line.text);
  const keys = key === null ? null : splitDotted(key);
  return keys !== null && keys.length === 2 && keys[0] === "mcp_servers" && keys[1] === table;
}
function editOne2(text, op) {
  const lines = linesOf(text);
  if (lines === null) return null;
  const heads = lines.flatMap((line, index) => isHeaderOf(line, op.table) ? [index] : []);
  if (heads.length !== 1) return null;
  const head = heads[0];
  let end = head + 1;
  while (end < lines.length && !isHeader(lines[end])) end++;
  const found = [];
  for (let i = head + 1; i < end; i++) if (!lines[i].inString && ENABLED.test(lines[i].text)) found.push(i);
  if (found.length > 1) return null;
  if (op.op === "delete") {
    if (found.length === 0) return null;
    lines.splice(found[0], 1);
  } else if (found.length === 1) {
    const line = lines[found[0]];
    line.text = line.text.replace(ENABLED, (_match, before) => `${before}${op.value}`);
  } else {
    const headLine = lines[head];
    let indent = "";
    for (let i = head + 1; i < end; i++) {
      const line = lines[i];
      if (!line.inString && /\S/.test(line.text) && !/^\s*#/.test(line.text)) {
        indent = /^[ \t]*/.exec(line.text)[0];
        break;
      }
    }
    const added = { text: `${indent}enabled = ${op.value}`, eol: headLine.eol, inString: false };
    if (headLine.eol === "") {
      headLine.eol = text.includes("\r\n") ? "\r\n" : "\n";
      added.eol = "";
    }
    lines.splice(head + 1, 0, added);
  }
  return lines.map((line) => line.text + line.eol).join("");
}
function editToml(original, ops) {
  let text = original;
  for (const op of ops) {
    if (text === null) return null;
    text = editOne2(text, op);
  }
  return text;
}
function tomlMeaningOk(original, candidate, ops) {
  const expected = parseCodexConfig(original);
  const actual = parseCodexConfig(candidate);
  if (expected === null || actual === null) return false;
  for (const op of ops) {
    const servers = expected.mcp_servers;
    const table = isTable(servers) ? servers[op.table] : void 0;
    if (!isTable(table)) return false;
    if (op.op === "set") table.enabled = op.value;
    else if (!Object.hasOwn(table, "enabled")) return false;
    else delete table.enabled;
  }
  return isDeepStrictEqual3(expected, actual);
}

// src/tune/engine.ts
async function replaceSetting(path, data) {
  const mode = await stat10(path).then(
    (info) => info.mode & 4095,
    () => void 0
  );
  await writeDurable(path, data, mode);
}
var fingerprintRead = (read) => read.status === "ok" ? fingerprintOf(read.bytes) : read.status === "missing" ? null : void 0;
function jsonOpOf(item2) {
  const { key, after } = item2;
  if (key.kind === "json-list-add") return { op: after.present ? "append" : "remove", parent: key.parent, entry: key.entry };
  if (key.kind === "json-entry") return after.present ? { op: "set", parent: key.parent, name: key.name, value: after.value } : { op: "delete", parent: key.parent, name: key.name };
  throw new Error("JSON \uC790\uB9AC\uAC00 \uC544\uB2C8\uB2E4");
}
function tomlOpOf(item2) {
  if (item2.key.kind !== "toml-table-key") throw new Error("TOML \uC790\uB9AC\uAC00 \uC544\uB2C8\uB2E4");
  return item2.after.present ? { op: "set", table: item2.key.table, value: item2.after.value } : { op: "delete", table: item2.key.table };
}
function candidateOf(original, items) {
  if (items[0].key.kind === "toml-table-key") {
    if (original === null) return null;
    const ops2 = items.map(tomlOpOf);
    const text2 = editToml(original, ops2);
    return text2 !== null && tomlMeaningOk(original, text2, ops2) ? text2 : null;
  }
  const ops = items.map(jsonOpOf);
  const text = editJson(original, ops);
  return text !== null && jsonMeaningOk(original, text, ops) ? text : null;
}
async function runFiles(work, io, planned) {
  const notices2 = [];
  const files = [...work.files].sort((a, b) => normalizePath(a.path) < normalizePath(b.path) ? -1 : 1);
  for (const file of files) {
    const items = work.items.filter((item2) => item2.file === file.path && item2.state === "planned");
    if (items.length === 0) continue;
    const mark = async (list, state, reason) => {
      for (const item2 of list) {
        item2.state = state;
        item2.reason = reason;
      }
      await io.save(work);
    };
    const read = await io.read(file.path);
    const fingerprint = fingerprintRead(read);
    if (fingerprint === void 0) {
      await mark(items, "rejected", "file-unreadable");
      continue;
    }
    file.before = fingerprint;
    if (planned !== null && planned.get(file.path) !== fingerprint) {
      await mark(items, "not_applied", "changed-since-plan");
      continue;
    }
    const ready = [];
    for (const item2 of items) {
      const block = blockOf(read, item2.key);
      const slot = slotOf(read, item2.key);
      if (block !== null || slot === null) {
        item2.state = "rejected";
        item2.reason = block ?? "parent-shape";
      } else if (sameSlot(slot, item2.after)) {
        item2.state = "not_applied";
        item2.reason = "already-set";
      } else if (planned === null && !sameSlot(slot, item2.before)) {
        item2.state = "not_applied";
        item2.reason = "changed-since-apply";
      } else {
        if (planned !== null) item2.before = slot;
        ready.push(item2);
      }
    }
    if (ready.length === 0) {
      await io.save(work);
      continue;
    }
    const candidate = candidateOf(read.status === "ok" ? read.bytes.toString("utf8") : null, ready);
    if (candidate === null) {
      await mark(ready, "rejected", "check-failed");
      continue;
    }
    file.candidate = fingerprintOf(Buffer.from(candidate, "utf8"));
    await mark(ready, "writing", null);
    await io.beforeRecheck?.(file.path);
    if (fingerprintRead(await io.read(file.path)) !== fingerprint) {
      await mark(ready, "not_applied", "changed-before-write");
      continue;
    }
    try {
      await io.replace(file.path, candidate);
    } catch (error) {
      await mark(ready, "not_applied", error.code ?? "write-failed");
      continue;
    }
    await mark(ready, "written", null);
    await io.afterReplace?.(file.path);
    if (fingerprintRead(await io.read(file.path)) !== file.candidate) notices2.push({ kind: "overwritten", path: file.path });
  }
  return notices2;
}

// src/commands/tune-run.ts
var failure5 = (code, message) => Object.assign(new Error(message), { code });
async function withLock(options, body) {
  const lock = await takeLock(options.stateDir, options.alive);
  if (lock === null) throw failure5("locked", `another tune run holds the lock: ${join38(options.stateDir, LOCK_FILE)}`);
  try {
    return await body();
  } finally {
    await lock.release();
  }
}
async function loadPlan(stateDir2, planId) {
  if (!ID_PATTERN.test(planId)) return null;
  try {
    const plan = JSON.parse(await readFile14(join38(stateDir2, PLANS_DIR, `${planId}.json`), "utf8"));
    return plan !== null && plan.planId === planId && Array.isArray(plan.items) && Array.isArray(plan.files) ? plan : null;
  } catch {
    return null;
  }
}
var afterOf = (item2) => item2.key.kind === "json-list-add" ? { present: true } : { present: true, value: item2.next };
var filesOf = (items) => [...new Set(items.map((item2) => item2.file))].map((path) => ({ path, items: items.filter((item2) => item2.file === path).map((item2) => item2.id), before: null, candidate: null }));
var newWork = (options, kind, planId, of) => ({
  workId: planIdOf(options.clock.nowMs, options.random?.() ?? randomBytes3(3).toString("hex")),
  kind,
  planId,
  of,
  createdAt: new Date(options.clock.nowMs).toISOString(),
  appVersion: PROGRAM_VERSION,
  items: [],
  files: []
});
var engineIo = (options) => ({ read: readTarget, replace: replaceSetting, save: (work) => saveWork(options.stateDir, work), ...options.io });
var isUndoable = (item2) => item2.state === "written" || item2.state === "verified";
var REPLAN = /* @__PURE__ */ new Set(["no-longer-candidate", "plan-differs", "changed-since-plan", "changed-before-write"]);
function noticesOf(work, engine, reconciled) {
  const notices2 = [];
  if (reconciled.length > 0) notices2.push({ kind: "reconciled", count: reconciled.length });
  notices2.push(...engine);
  if (work.kind === "apply" && work.items.some((item2) => item2.state === "not_applied" && item2.reason !== null && REPLAN.has(item2.reason))) notices2.push({ kind: "replan" });
  const written = work.items.filter((item2) => item2.state === "written");
  if (written.some((item2) => item2.tool === "claude-code")) notices2.push({ kind: "new-session" });
  if (written.some((item2) => item2.tool === "codex")) notices2.push({ kind: "restart-codex" });
  return notices2;
}
function outcomeOf(options, started, work, notices2) {
  const now = options.now ?? Date.now;
  const text = { items: Object.fromEntries(work.items.map((item2) => [item2.id, workItemText(item2, work.kind, options.lang)])), notices: notices2.map((notice) => workNoticeText(notice, options.lang)) };
  return { work, run: { durationMs: now() - started, notices: notices2, text } };
}
async function runTuneApply(options) {
  const started = (options.now ?? Date.now)();
  return withLock(options, async () => {
    const reconciled = await reconcileWorks(options.stateDir);
    const plan = await loadPlan(options.stateDir, options.planId);
    if (plan === null) throw failure5("plan-not-found", `no saved plan: ${options.planId}`);
    const unknown = options.itemIds.filter((id) => !plan.items.some((item2) => item2.id === id));
    if (unknown.length > 0) throw failure5("item-not-in-plan", `not in the plan: ${unknown.join(", ")}`);
    const { items: fresh } = await judgeTune({ ...options, cache: true });
    const work = newWork(options, "apply", plan.planId, null);
    for (const id of options.itemIds) {
      const planned = plan.items.find((item2) => item2.id === id);
      const now = fresh.find((item2) => item2.id === id);
      const base = now ?? planned;
      let state = "planned";
      let reason = null;
      if (now === void 0) [state, reason] = ["not_applied", "no-longer-candidate"];
      else if (now.blocked !== null) [state, reason] = ["rejected", now.blocked];
      else if (now.file !== planned.file || !isDeepStrictEqual4(now.key, planned.key) || !isDeepStrictEqual4(now.next, planned.next)) [state, reason] = ["not_applied", "plan-differs"];
      work.items.push({ id, unit: base.unit, tool: base.tool, target: base.target, file: base.file, key: base.key, before: "current" in base ? { present: true, value: base.current } : { present: false }, after: afterOf(base), state, reason });
    }
    work.files = filesOf(work.items);
    await saveWork(options.stateDir, work);
    const engine = await runFiles(work, engineIo(options), new Map(plan.files.map((file) => [file.path, file.fingerprint])));
    return outcomeOf(options, started, work, noticesOf(work, engine, reconciled));
  });
}
async function latestUndoable(stateDir2) {
  return (await listWorks(stateDir2)).filter((work) => work.kind === "apply" && work.items.some(isUndoable)).at(-1) ?? null;
}
async function runTuneUndo(options) {
  const started = (options.now ?? Date.now)();
  return withLock(options, async () => {
    const reconciled = await reconcileWorks(options.stateDir);
    const target = options.workId === null ? await latestUndoable(options.stateDir) : await loadWork(options.stateDir, options.workId);
    if (target === null && options.workId === null) throw failure5("nothing-to-undo", "no apply run has changes left to undo");
    if (target === null || target.kind !== "apply") throw failure5("work-not-found", `no apply run: ${options.workId}`);
    const unknown = options.itemIds.filter((id) => !target.items.some((item2) => item2.id === id));
    if (unknown.length > 0) throw failure5("item-not-in-work", `not in the run: ${unknown.join(", ")}`);
    const chosen = options.itemIds.length > 0 ? target.items.filter((item2) => options.itemIds.includes(item2.id)) : target.items.filter(isUndoable);
    const work = newWork(options, "undo", null, target.workId);
    work.items = chosen.map((item2) => ({ ...item2, before: item2.after, after: item2.before, state: isUndoable(item2) ? "planned" : "not_applied", reason: isUndoable(item2) ? null : "not-written" }));
    work.files = filesOf(work.items);
    await saveWork(options.stateDir, work);
    const engine = await runFiles(work, engineIo(options), null);
    for (const item2 of work.items) {
      if (item2.state !== "written" && item2.reason !== "already-set") continue;
      const original = target.items.find((x) => x.id === item2.id);
      original.state = "undone";
    }
    await saveWork(options.stateDir, target);
    return outcomeOf(options, started, work, noticesOf(work, engine, reconciled));
  });
}
function stillOn(item2, judged) {
  const tool = judged.evaluation.tools.find((x) => x.tool === item2.tool);
  if (tool === void 0) return false;
  switch (item2.unit) {
    case "A1":
      return tool.skills.some((bundle) => bundle.enabled && bundle.positions.some((position) => position.recordNames.includes(item2.target)));
    case "A2": {
      const input = judged.input.tools.find((x) => x.tool === "claude-code");
      return input !== void 0 && input.tool === "claude-code" && input.setup.plugins.some((plugin) => plugin.id === item2.target && plugin.enabled);
    }
    case "A3":
    case "A4":
      return tool.servers.some(({ server }) => server.name === item2.target && server.enabled);
  }
}
async function runTuneVerify(options) {
  const now = options.now ?? Date.now;
  const started = now();
  return withLock(options, async () => {
    const reconciled = await reconcileWorks(options.stateDir);
    const target = await loadWork(options.stateDir, options.workId);
    if (target === null || target.kind !== "apply") throw failure5("work-not-found", `no apply run: ${options.workId}`);
    const judged = await judgeTune({ ...options, cache: true });
    const results = [];
    for (const item2 of target.items) {
      if (!isUndoable(item2)) continue;
      const slot = slotOf(await readTarget(item2.file), item2.key);
      const result = { id: item2.id, kept: slot !== null && sameSlot(slot, item2.after), stillOn: stillOn(item2, judged) };
      if (result.kept && !result.stillOn) item2.state = "verified";
      results.push(result);
    }
    await saveWork(options.stateDir, target);
    const notices2 = reconciled.length > 0 ? [{ kind: "reconciled", count: reconciled.length }] : [];
    const text = { items: Object.fromEntries(results.map((result) => [result.id, verifyText(result, options.lang)])), notices: notices2.map((notice) => workNoticeText(notice, options.lang)) };
    return { work: target, run: { durationMs: now() - started, results, notices: notices2, text } };
  });
}

// src/commands/open.ts
import { spawn } from "node:child_process";
function openerFor(platform, path) {
  if (platform === "win32") return { command: "explorer.exe", args: [path] };
  if (platform === "darwin") return { command: "open", args: [path] };
  if (platform === "linux" || platform === "freebsd" || platform === "openbsd") return { command: "xdg-open", args: [path] };
  return null;
}
function openInBrowser(path, platform = process.platform, start = spawn) {
  const opener = openerFor(platform, path);
  if (opener === null) return Promise.resolve(false);
  return new Promise((resolve13) => {
    try {
      const child = start(opener.command, opener.args, { detached: true, stdio: "ignore", windowsHide: true, shell: false });
      child.once("error", () => resolve13(false));
      child.once("spawn", () => {
        child.unref();
        resolve13(true);
      });
    } catch {
      resolve13(false);
    }
  });
}

// src/commands/clean.ts
import { lstat as lstat10, readdir as readdir11, realpath as realpath7 } from "node:fs/promises";
import { join as join39 } from "node:path";
var isMissing7 = (error) => error?.code === "ENOENT";
async function lstatOrNull(path) {
  try {
    return await lstat10(path);
  } catch (error) {
    if (isMissing7(error)) return null;
    throw error;
  }
}
async function cleanReports(path, boundary) {
  const names2 = (await readdir11(path)).sort();
  const base = (name) => name.replace(/\.[^.]*$/, "");
  let latest = null;
  for (const name of names2) {
    const info = await lstat10(join39(path, name));
    if (info.isFile() && (latest === null || base(name) > latest)) latest = base(name);
  }
  const removed = { name: "reports", files: 0, bytes: 0 };
  const kept = { name: "reports", files: 0, bytes: 0 };
  for (const name of names2) {
    const full = join39(path, name);
    const info = await lstat10(full);
    if (info.isFile() && base(name) === latest) {
      kept.files++;
      kept.bytes += info.size;
      continue;
    }
    const size = await removeTree(full, boundary);
    removed.files += size.files;
    removed.bytes += size.bytes;
  }
  return { removed, kept };
}
async function cleanEntry(dir, boundary, spec, level, report) {
  const path = join39(dir, spec.name);
  const info = await lstatOrNull(path);
  if (info === null) return;
  if (spec.name === "reports" && level === "clean") {
    if (info.isSymbolicLink()) {
      report.skipped.push(spec.name);
    } else if (info.isDirectory()) {
      const { removed, kept } = await cleanReports(path, boundary);
      if (removed.files > 0) report.removed.push(removed);
      if (kept.files > 0) report.kept.push(kept);
    }
    return;
  }
  if (spec.removedBy === "clean" || level === "all") {
    const size2 = await removeTree(path, boundary);
    if (info.isSymbolicLink()) report.unlinked.push(spec.name);
    else report.removed.push({ name: spec.name, files: size2.files, bytes: size2.bytes });
    return;
  }
  const size = await treeSize(path);
  report.kept.push({ name: spec.name, files: size.files, bytes: size.bytes });
}
async function clean(dir, level) {
  const report = { dir, level, link: false, removed: [], kept: [], unlinked: [], skipped: [], failed: [] };
  const dirInfo = await lstatOrNull(dir);
  if (dirInfo === null) return report;
  const boundary = await expectedRealDir(dir);
  if (dirInfo.isSymbolicLink() || normalizePath(await realpath7(dir)) !== boundary) {
    report.link = true;
    return report;
  }
  for (const spec of STATE_ENTRIES) {
    try {
      await cleanEntry(dir, boundary, spec, level, report);
    } catch (error) {
      report.failed.push({ name: spec.name, code: error.code ?? "unknown" });
    }
  }
  return report;
}

// src/commands/doctor.ts
import { mkdir as mkdir10, rm as rm7, stat as stat11, writeFile as writeFile7 } from "node:fs/promises";
import { join as join40 } from "node:path";
import * as zlib3 from "node:zlib";
function hasZstd() {
  return typeof zlib3.createZstdDecompress === "function";
}
async function canWrite(dir) {
  const probe = join40(dir, `.write-probe-${process.pid}`);
  try {
    await mkdir10(dir, { recursive: true });
    await writeFile7(probe, "ok");
    await rm7(probe, { force: true });
    return true;
  } catch {
    return false;
  }
}
async function doctor(input) {
  const home = claudeHome(input.env, input.homedir);
  const list = await listClaudeFiles(home, null);
  const codex = codexHome(input.env, input.homedir);
  const records = await listCodexFiles(codex, null);
  const groups = groupCopies(records.files);
  const gemini = geminiHome(input.env, input.homedir);
  const geminiList = await listGeminiRecordFiles(geminiRecordHomes(input.env, input.homedir), null);
  const web = await readWebExports(input.stateDir);
  const exports = await Promise.all(
    web.entries.map(async (entry) => {
      try {
        const info = await stat11(entry.path);
        return { tool: entry.tool, path: entry.path, exists: info.isFile() || info.isDirectory(), bytes: info.isFile() ? info.size : null };
      } catch {
        return { tool: entry.tool, path: entry.path, exists: false, bytes: null };
      }
    })
  );
  return {
    node: { version: input.nodeVersion, ok: input.nodeOk },
    zstd: hasZstd(),
    claudeCode: { home, projectsFound: list.projectsFound, sessionFiles: list.files.length, unreadable: list.unreadableDirs.length + list.unreadableFiles.length },
    codex: {
      home: codex,
      sessionsFound: records.sessionsFound,
      recordFiles: groups.length,
      compressedOnly: groups.filter((group) => group.copies.every((copy2) => copy2.compressed)).length,
      unreadable: records.unreadableDirs.length + records.files.filter((file) => file.size === null).length
    },
    gemini: { home: gemini, tmpFound: geminiList.tmpFound, sessionFiles: geminiList.files.length, unreadable: geminiList.unreadableDirs.length + geminiList.unreadableFiles.length },
    web: { list: web.status, exports },
    state: { dir: input.stateDir, writable: await canWrite(input.stateDir) }
  };
}

// src/commands/where.ts
import { lstat as lstat11, readdir as readdir12 } from "node:fs/promises";
import { join as join41 } from "node:path";
var isMissing8 = (error) => error?.code === "ENOENT";
async function where(dir) {
  const report = { dir, exists: false, link: false, entries: [], files: 0, bytes: 0, others: [], noSaveResultsInOsTemp: true };
  let dirInfo;
  try {
    dirInfo = await lstat11(dir);
  } catch (error) {
    if (!isMissing8(error)) throw error;
  }
  report.exists = dirInfo !== void 0;
  report.link = dirInfo?.isSymbolicLink() ?? false;
  const inside2 = report.exists && !report.link;
  for (const spec of STATE_ENTRIES) {
    const entry = { name: spec.name, kind: spec.kind, exists: false, link: false, files: 0, bytes: 0, removedBy: spec.removedBy, unreadable: false };
    if (inside2) {
      try {
        const info = await lstat11(join41(dir, spec.name));
        entry.exists = true;
        entry.link = info.isSymbolicLink();
        if (!entry.link) {
          const size = await treeSize(join41(dir, spec.name));
          entry.files = size.files;
          entry.bytes = size.bytes;
        }
      } catch (error) {
        if (!isMissing8(error)) entry.unreadable = true;
      }
    }
    report.files += entry.files;
    report.bytes += entry.bytes;
    report.entries.push(entry);
  }
  if (inside2) {
    const known2 = new Set(STATE_ENTRIES.map((spec) => spec.name));
    report.others = (await readdir12(dir)).filter((name) => !known2.has(name)).sort();
  }
  return report;
}

// src/cli.ts
function nodeMajorOk(version) {
  const major = Number(version.replace(/^v/, "").split(".")[0]);
  return Number.isInteger(major) && major >= 22;
}
var CHECKUP_FLAGS = /* @__PURE__ */ new Set(["--no-open", "--no-save", "--rescan"]);
var TUNE_PLAN_FLAGS = /* @__PURE__ */ new Set(["--no-save", "--rescan"]);
function checkupArgs(rest, allowed = CHECKUP_FLAGS) {
  const flags = /* @__PURE__ */ new Set();
  let lang = null;
  for (let index = 0; index < rest.length; index++) {
    const arg = rest[index];
    if (arg === "--lang") {
      const value = rest[index + 1];
      if (value === void 0 || value.startsWith("-")) return null;
      lang = value;
      index++;
    } else if (allowed.has(arg)) {
      flags.add(arg);
    } else {
      return null;
    }
  }
  return { flags, lang };
}
var printJson = (value) => {
  process.stdout.write(`${JSON.stringify(value, null, 2)}
`);
};
function tuneRunArgs(command, rest) {
  let lang = null;
  let rescan = false;
  const positional = [];
  for (let index = 0; index < rest.length; index++) {
    const arg = rest[index];
    if (arg === "--lang") {
      const value = rest[index + 1];
      if (value === void 0 || value.startsWith("-")) return null;
      lang = value;
      index++;
    } else if (arg === "--rescan") rescan = true;
    else if (arg.startsWith("-")) return null;
    else positional.push(arg);
  }
  const [id, ...items] = positional;
  if (id === void 0) return command === "undo" ? { lang, rescan, id: null, items: [] } : null;
  if (!ID_PATTERN.test(id) || new Set(items).size !== items.length) return null;
  if (command === "apply" && items.length === 0 || command === "verify" && items.length > 0) return null;
  return { lang, rescan, id, items };
}
async function run(command, rest, context) {
  if (command === "doctor") {
    printJson(
      await doctor({
        env: context.env,
        homedir: context.homedir,
        nodeVersion: process.version,
        nodeOk: nodeMajorOk(process.version),
        stateDir: stateDir(context.homedir)
      })
    );
    return 0;
  }
  if (command === "where" && rest.length === 0) {
    printJson(await where(stateDir(context.homedir)));
    return 0;
  }
  if (command === "clean" && (rest.length === 0 || rest.length === 1 && rest[0] === "--all")) {
    printJson(await clean(stateDir(context.homedir), rest[0] === "--all" ? "all" : "clean"));
    return 0;
  }
  if (command === "badge") {
    const args2 = checkupArgs(rest, /* @__PURE__ */ new Set());
    if (args2 === null) return null;
    printJson(
      await runBadge({
        stateDir: stateDir(context.homedir),
        lang: pickLang(args2.lang, context.locale ?? Intl.DateTimeFormat().resolvedOptions().locale),
        timeZone: context.clock?.timeZone ?? Intl.DateTimeFormat().resolvedOptions().timeZone
      })
    );
    return 0;
  }
  if (command === "notify" && (rest[0] === "on" || rest[0] === "off" || rest[0] === "status")) {
    const args2 = checkupArgs(rest.slice(1), /* @__PURE__ */ new Set());
    if (args2 === null) return null;
    printJson(await runNotify(rest[0], { env: context.env, homedir: context.homedir, stateDir: stateDir(context.homedir), lang: pickLang(args2.lang, context.locale ?? Intl.DateTimeFormat().resolvedOptions().locale) }));
    return 0;
  }
  if (command === "ignore" && (rest[0] === "add" || rest[0] === "remove" || rest[0] === "list")) {
    const action = rest[0];
    const rule2 = action === "list" ? null : rest[1] ?? null;
    const args2 = checkupArgs(rest.slice(action === "list" ? 1 : 2), /* @__PURE__ */ new Set());
    if (args2 === null || action !== "list" && (rule2 === null || rule2.startsWith("--"))) return null;
    printJson(await runIgnore(action, rule2, { stateDir: stateDir(context.homedir), lang: pickLang(args2.lang, context.locale ?? Intl.DateTimeFormat().resolvedOptions().locale) }));
    return 0;
  }
  if (command === "import" && (rest[0] === "add" || rest[0] === "remove" || rest[0] === "list")) {
    const action = rest[0];
    const target = action === "list" ? null : rest[1] ?? null;
    const args2 = checkupArgs(rest.slice(action === "list" ? 1 : 2), action === "add" ? /* @__PURE__ */ new Set(["--no-save"]) : /* @__PURE__ */ new Set());
    if (args2 === null || action !== "list" && (target === null || target.startsWith("--"))) return null;
    const common = {
      stateDir: stateDir(context.homedir),
      clock: context.clock ?? { nowMs: Date.now(), timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone },
      lang: pickLang(args2.lang, context.locale ?? Intl.DateTimeFormat().resolvedOptions().locale)
    };
    if (action === "add") printJson(await runImportAdd(target, { ...common, cache: !args2.flags.has("--no-save") }));
    else if (action === "remove") printJson(await runImportRemove(target, common));
    else printJson(await runImportList(common));
    return 0;
  }
  if (command === "deep-hints") {
    const args2 = checkupArgs(rest, TUNE_PLAN_FLAGS);
    if (args2 === null) return null;
    printJson(
      await runDeepHints({
        env: context.env,
        homedir: context.homedir,
        tmpdir: context.tmpdir ?? tmpdir2(),
        platform: context.platform ?? process.platform,
        clock: context.clock ?? { nowMs: Date.now(), timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone },
        lang: pickLang(args2.lang, context.locale ?? Intl.DateTimeFormat().resolvedOptions().locale),
        stateDir: stateDir(context.homedir),
        save: !args2.flags.has("--no-save"),
        rescan: args2.flags.has("--rescan"),
        entryFile: context.entryFile ?? process.argv[1] ?? "",
        ...context.managedDir === void 0 ? {} : { managedDir: context.managedDir }
      })
    );
    return 0;
  }
  if (command === "tune" && rest[0] === "plan") {
    const args2 = checkupArgs(rest.slice(1), TUNE_PLAN_FLAGS);
    if (args2 === null) return null;
    printJson(
      await runTunePlan({
        env: context.env,
        homedir: context.homedir,
        tmpdir: context.tmpdir ?? tmpdir2(),
        platform: context.platform ?? process.platform,
        clock: context.clock ?? { nowMs: Date.now(), timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone },
        lang: pickLang(args2.lang, context.locale ?? Intl.DateTimeFormat().resolvedOptions().locale),
        stateDir: stateDir(context.homedir),
        save: !args2.flags.has("--no-save"),
        rescan: args2.flags.has("--rescan"),
        entryFile: context.entryFile ?? process.argv[1] ?? "",
        ...context.managedDir === void 0 ? {} : { managedDir: context.managedDir }
      })
    );
    return 0;
  }
  if (command === "tune" && (rest[0] === "apply" || rest[0] === "undo" || rest[0] === "verify")) {
    const which = rest[0];
    const args2 = tuneRunArgs(which, rest.slice(1));
    if (args2 === null) return null;
    const options = {
      env: context.env,
      homedir: context.homedir,
      tmpdir: context.tmpdir ?? tmpdir2(),
      platform: context.platform ?? process.platform,
      clock: context.clock ?? { nowMs: Date.now(), timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone },
      lang: pickLang(args2.lang, context.locale ?? Intl.DateTimeFormat().resolvedOptions().locale),
      stateDir: stateDir(context.homedir),
      rescan: args2.rescan,
      entryFile: context.entryFile ?? process.argv[1] ?? "",
      ...context.managedDir === void 0 ? {} : { managedDir: context.managedDir }
    };
    if (which === "undo") printJson(await runTuneUndo({ ...options, workId: args2.id, itemIds: args2.items }));
    else if (args2.id === null) return null;
    else if (which === "apply") printJson(await runTuneApply({ ...options, planId: args2.id, itemIds: args2.items }));
    else printJson(await runTuneVerify({ ...options, workId: args2.id }));
    return 0;
  }
  const args = command === "checkup" ? checkupArgs(rest) : null;
  if (args !== null) {
    const platform = context.platform ?? process.platform;
    const open9 = context.open ?? ((path) => openInBrowser(path, platform));
    const outcome = await runCheckup({
      env: context.env,
      homedir: context.homedir,
      tmpdir: context.tmpdir ?? tmpdir2(),
      platform,
      clock: context.clock ?? { nowMs: Date.now(), timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone },
      lang: pickLang(args.lang, context.locale ?? Intl.DateTimeFormat().resolvedOptions().locale),
      stateDir: stateDir(context.homedir),
      save: !args.flags.has("--no-save"),
      rescan: args.flags.has("--rescan"),
      entryFile: context.entryFile ?? process.argv[1] ?? "",
      ...context.managedDir === void 0 ? {} : { managedDir: context.managedDir },
      ...args.flags.has("--no-open") ? {} : { open: open9 }
    });
    printJson({ summary: outcome.summary, run: outcome.run });
    return 0;
  }
  return null;
}
async function main(argv, context = { env: process.env, homedir: homedir() }) {
  if (!nodeMajorOk(process.version)) {
    process.stderr.write(`Node.js 22 or later is required (found ${process.version}).
`);
    return 2;
  }
  const [command, ...rest] = argv;
  if (command === "--version" || command === "version") {
    process.stdout.write(`${PROGRAM_VERSION}
`);
    return 0;
  }
  let code;
  try {
    code = await run(command, rest, context);
  } catch (error) {
    const err = error;
    printJson({ error: { code: err.code ?? "unexpected", message: err instanceof Error ? err.message : String(error) } });
    return 1;
  }
  if (code !== null) return code;
  process.stderr.write(`Unknown command: ${[command ?? "(none)", ...rest].join(" ")}
`);
  return 64;
}

// src/entry.ts
process.exitCode = await main(process.argv.slice(2));
