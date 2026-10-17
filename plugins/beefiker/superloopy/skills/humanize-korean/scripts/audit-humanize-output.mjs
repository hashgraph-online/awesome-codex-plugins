#!/usr/bin/env node
import { readFile, writeFile } from "node:fs/promises";
import {
  CALQUE_ADVISORY_PATTERNS,
  CALQUE_GATING_PATTERNS,
  CALQUE_PATTERN_IDS,
  CALQUE_REPAIR_HINTS,
  P3_TRANSPARENT_PATTERN,
  PROTECTED_PROSE_SPAN_PATTERN,
  countP1bOnly,
  koreanRatio,
  removeProtectedProseSpans,
  stripAlphaContextSentences
} from "./calque-patterns.mjs";

const PATTERNS = [
  ["A-2", /를 통해|을 통해|통하여/gu],
  ["A-3", /에 있어서|에 있어/gu],
  ["A-7", /가지고 있다|가지고 있습니다|가졌다/gu],
  ["A-8", /되어진다|되어집니다|되어졌다/gu],
  ["A-10", /할 수 있다|할 수 있을|할 수 있습니다/gu],
  ["C-11", /(고|며|지만|아서|어서),/gu],
  ["D-1", /결론적으로|따라서|요약하면|정리하면/gu],
  ["D-2", /시사하는 바가 크다|시사하는 바가 큽니다|주목할 만하다|주목할 만합니다/gu],
  ["H-1", /(^|\n|[.!?]\s)\s*(또한|따라서|즉|나아가|아울러|게다가|더욱이)/gu],
  ["I-1", /인 것이다|인 것입니다|한 것이다|한 것입니다|는 것입니다/gu],
  ["J-2", /"[^"]{1,40}"/gu],
  ["K-1", /멱등(?:성)?/gu],
  ["M-1", /[—–]/gu],
  // Upstream v2.5–v2.7 adoptions (im-not-ai, 2026-09-10 drift pass). Human-near-zero forms count toward
  // S2; density- or threshold-conditioned forms (A-20, A-22, A-24) are advisory below.
  ["A-20", /(?:되|지)고\s?있(?:다|습니다|는|었|어)/gu],
  ["A-21", /단순한\s[^.!?\n]{1,20}?(?:을|를)\s?넘어(?:서)?/gu],
  ["A-22", /(?:은|는|이|가)\s*(?:명확|분명)(?:하다|합니다|하며|하고|해졌|하지만|해\s?보인다)/gu],
  ["A-24", /더\s?이상(?!의)[^.!?\n]{0,25}(?:않|아니|없|못하|불가)/gu],
  ["D-8", /(?:필요한|중요한|핵심적인|시급한|절실한|더\s?심각한|뼈아픈)\s?것은(?=\s|$)|(?<![가-힣])관건은(?=\s)/gu],
  ["D-9", /(?:으)?로\s?이어(?:진다|집니다|졌다|질\s)|에\s?직결(?:된다|됩니다)/gu],
  ["D-10", /[가-힣]는\s?이유(?:다|입니다|였다|이다)(?=[.!?\s"”』]|$)/gu],
  ["D-12", /(?:^|[.!?]\s+)(?:그러나\s|하지만\s|다만\s|물론\s)?(?:과제|한계|숙제|아쉬운\s?점)(?:도|는)\s?(?:남아\s?있다|분명하다|있다|적지\s?않다)(?=[.!?]|\s*$)/gmu],
  // Q-1 (local): chatbot frame sentences pasted along with the body — greeting header, closing offer,
  // knowledge-cutoff disclaimer. Zero meaning loss on removal; quoted mentions are filtered. 물론입니다
  // counts only at the start of the text or a line: as a predicate (계약 연장은 물론입니다) it is prose.
  // D-9b (injection watch): logical-settlement 결국 is human-used in narrative, so it is never graded
  // and never a "remains" warning; it is counted so the injection guard sees a rewrite that adds one.
  ["D-9b", /(?<![가-힣])결국(?![가-힣])/gu],
  ["Q-1", /(?:^|\n)\s*물론(?:입니다|이죠|이에요)[!.]?|다음은\s[^\n:]{0,30}입니다:|요청하신\s[^\n]{0,20}?(?:정리하면|정리해\s?드리)|도움이\s?되(?:셨|었)(?:길|으면)\s?(?:바랍니다|좋겠습니다)|추가\s?질문이\s?있(?:으시)?(?:면|다면)|제\s?지식은\s[^\n]{0,20}?까지/gu]
];
const REQUIRED_S1_PATTERN_IDS = ["A-2", "A-3", "A-7", "A-8", "C-11", "D-1", "D-2", "H-1", "I-1", "K-1", "M-1", "P-1a", "P-2", "P-4", "Q-1"];
// Quoted spans are protected byte-for-byte, so the rewriter cannot repair J-2;
// it stays informational and is excluded from grading.
const GRADE_EXEMPT_IDS = ["J-2"];
// Calque warn tier (P family): reported with a repair hint, never graded. Developer prose uses
// 투명하게 for alpha and disclosure far more than for the calque, 정본 keeps its legal sense, and
// the open-class 조용히 heuristic (P-1b) is a heuristic; none of them may cost a grade.
// A-20 (passive progressive), A-22 (evaluative predicate) and A-24 (더 이상) are advisory too: upstream
// fires them only at paragraph density or a document threshold, which a whole-text count cannot see.
const ADVISORY_PATTERN_IDS = [...CALQUE_ADVISORY_PATTERNS.map(([id]) => id), "A-20", "A-22", "A-24", "D-9b"];
const PROSE_SPAN_FILTERED_IDS = new Set(["K-1", "M-1", "Q-1", ...CALQUE_PATTERN_IDS]);
const UPSTREAM_ADVISORY_HINTS = {
  "A-20": "~되고 있다/~지고 있다 is the English progressive passive; act only when three or more cluster in one paragraph, and then turn some into a plain trend (심화되고 있다 → 심해졌다), keeping isolated uses.",
  "A-22": "~은 명확하다/분명하다 is `it is clear that`; drop the evaluative predicate and assert the proposition, keeping certainty as an adverb (분명히) if the source is certain. A conclusion the text actually argued for stays.",
  "A-24": "더 이상 ~ 않다 is `no longer`; use 이제 or a change verb (~로 옮겨 갔다) when it repeats or closes a redefinition. Never turn the negation into a positive claim, and never write a new 더 이상 A가 아니라 B."
};
// Upstream v2.4 서법 보존: a decrease in deontic or hedge markers means a
// demand or reservation may have become a plain assertion. Repositioning
// (the D-6 repair) keeps the counts identical; only substitution loses one.
// A decrease warns rather than fails: A-10/G-2 repairs may legitimately drop
// a hedge when the source itself is certain.
const DEONTIC_MARKER_PATTERN = /[가-힣]야(?:만)?\s*(?:한다|합니다|했다|할|하며|하고|겠다|겠습니다|된다|됩니다)|필요가\s?있(?:다|습니다|을)|요구(?:된다|됩니다)/gu;
// `수도` needs the trailing 있 so the nouns 수도 (capital, water supply) do
// not count; `~로 보인다` is matched through any preceding syllable because
// the hedge is the ending, not the 것으로 nominalizer.
const HEDGE_MARKER_PATTERN = /수\s?(?:있다|있습니다|있을)|[가-힣]로\s?보(?:인다|입니다)|가능성이\s?(?:있|높)(?:다|습니다)|[가-힣]\s?수도\s?있|듯하(?:다|습니다)/gu;
// Upstream v2.4 C-8: paired antithesis rhetoric is absent from the human
// corpus, so two or more remaining pairs are a safe repetition signal.
// The 인가 branch requires both halves of the pair; a lone rhetorical
// question or the noun 인가 (approval) is not antithesis.
const ANTITHESIS_PATTERN = /[가-힣](?:가|이)\s?아니라|인가[,，][^\n.!?]*인가\?/gu;
const KOREAN_NAME_STOPLIST = new Set([
  "광고",
  "계획",
  "고객",
  "공지",
  "과정",
  "기능",
  "기록",
  "검증",
  "댓글",
  "도구",
  "메일",
  "문구",
  "문서",
  "문장",
  "방해",
  "사용자",
  "사람",
  "서비스",
  "성능",
  "소개글",
  "안내문",
  "업데이트",
  "요소",
  "이메일",
  "작업",
  "제품",
  "증거",
  "파일"
]);

const args = parseArgs(process.argv.slice(2));
if (!args.source || !args.final || !args.report) {
  fail("Usage: audit-humanize-output.mjs --source SOURCE --final FINAL --report REPORT");
}

let report;
try {
  report = await audit(args);
} catch (error) {
  const message = error instanceof Error ? error.message : String(error);
  await writeFailureReport(args.report, message);
  fail(message);
}

await writeFile(args.report, `${JSON.stringify(report, null, 2)}\n`);
if (!report.ok) fail(report.problems.join("; "));

async function audit(args) {
  const source = await readInputFile("source", args.source);
  const final = await readInputFile("final", args.final);
  const genre = args.genre ?? null;
  const sourceRatio = koreanRatio(source);
  const finalRatio = koreanRatio(final);
  const protectedTokens = collectProtectedTokens(source);
  const missing = [...protectedTokens].filter((token) => !final.includes(token));
  const before = countPatterns(source);
  const after = countPatterns(final);
  const changeRate = levenshtein(source, final) / Math.max(source.length, final.length, 1);
  const problems = [];
  if (sourceRatio < 0.2) problems.push("Korean source text required");
  if (missing.length > 0) problems.push("Protected tokens changed");
  if (finalRatio < 0.2) problems.push("Final text is not Korean enough");
  if (changeRate > 0.5) problems.push("Change rate exceeds 50%");
  if (requiredS1Count(before) > 0 && requiredS1Count(after) >= requiredS1Count(before)) {
    problems.push("S1 AI-tell count not reduced");
  }
  if ((after["K-1"] ?? 0) > 0) problems.push("Unnecessary technical jargon remains");
  if ((after["M-1"] ?? 0) > 0) problems.push("Em dash remains in Korean prose");

  const warnings = [];
  if (changeRate > 0.3 && changeRate <= 0.5) warnings.push("Change rate exceeds 30%");
  const modality = {
    deontic: { before: countMatches(source, DEONTIC_MARKER_PATTERN), after: countMatches(final, DEONTIC_MARKER_PATTERN) },
    hedge: { before: countMatches(source, HEDGE_MARKER_PATTERN), after: countMatches(final, HEDGE_MARKER_PATTERN) }
  };
  if (modality.deontic.after < modality.deontic.before || modality.hedge.after < modality.hedge.before) {
    warnings.push("Modality markers decreased; a demand or hedge may have become a plain assertion — reposition instead of substituting (D-6), and drop a hedge only when the source is certain");
  }
  const antithesis = { before: countMatches(source, ANTITHESIS_PATTERN), after: countMatches(final, ANTITHESIS_PATTERN) };
  if (antithesis.after >= 2) {
    warnings.push("Paired antithesis rhetoric repeats; keep the strongest pair and flatten the rest into direct statements, and do not create a new pair elsewhere (C-8)");
  }
  // Injection guard (upstream v2.6 finding): a rewrite that fixes one tell must not create another
  // — 결국, ~하는 이유다, 더 이상 A가 아니라 B, and connective commas were all measured appearing in
  // rewritten text that lacked them. Any counted id that rose is named; quoted spans (J-2) are
  // protected byte-for-byte, so a rise there is the source's, not the rewrite's.
  for (const id of Object.keys(after)) {
    if (GRADE_EXEMPT_IDS.includes(id)) continue;
    if ((after[id] ?? 0) > (before[id] ?? 0)) warnings.push(`${id} injected by the rewrite (${before[id] ?? 0} → ${after[id]}); a repair must not create a tell in another sentence`);
  }
  if (antithesis.after > antithesis.before) warnings.push(`C-8 injected by the rewrite (${antithesis.before} → ${antithesis.after}); flatten the pair you added`);
  // A remaining calque always explains its ladder step. Gating ids also hold the grade below A/B
  // through REQUIRED_S1_PATTERN_IDS; advisory ids stop here.
  for (const id of CALQUE_PATTERN_IDS) {
    if ((after[id] ?? 0) > 0) warnings.push(`${id} remains (${after[id]}): ${CALQUE_REPAIR_HINTS[id]}`);
  }
  for (const [id, hint] of Object.entries(UPSTREAM_ADVISORY_HINTS)) {
    if ((after[id] ?? 0) > 0) warnings.push(`${id} remains (${after[id]}): ${hint}`);
  }
  return {
    ok: problems.length === 0,
    grade: grade({ after, changeRate, missing, problems }),
    genre,
    sourceChars: source.length,
    finalChars: final.length,
    changeRate: Number(changeRate.toFixed(4)),
    koreanRatio: {
      source: Number(sourceRatio.toFixed(4)),
      final: Number(finalRatio.toFixed(4))
    },
    protectedTokens: { total: protectedTokens.size, missing },
    patterns: { before, after },
    modality,
    antithesis,
    warnings,
    problems
  };
}

function countMatches(text, pattern) {
  return [...text.matchAll(pattern)].length;
}

async function readInputFile(label, path) {
  try {
    return await readFile(path, "utf8");
  } catch (error) {
    const reason = error instanceof Error && "code" in error ? error.code : error instanceof Error ? error.message : String(error);
    throw new Error(`Unable to read ${label} file: ${path} (${reason})`);
  }
}

async function writeFailureReport(path, message) {
  const report = {
    ok: false,
    grade: "D",
    genre: null,
    sourceChars: 0,
    finalChars: 0,
    changeRate: 0,
    koreanRatio: { source: 0, final: 0 },
    protectedTokens: { total: 0, missing: [] },
    patterns: { before: {}, after: {} },
    modality: { deontic: { before: 0, after: 0 }, hedge: { before: 0, after: 0 } },
    antithesis: { before: 0, after: 0 },
    warnings: [],
    problems: [message]
  };
  await writeFile(path, `${JSON.stringify(report, null, 2)}\n`);
}

function parseArgs(values) {
  const parsed = {};
  for (let index = 0; index < values.length; index += 2) {
    parsed[values[index].replace(/^--/u, "")] = values[index + 1];
  }
  return parsed;
}

function collectProtectedTokens(text) {
  const patterns = [
    /https?:\/\/\S+/gu,
    /`[^`]+`/gu,
    PROTECTED_PROSE_SPAN_PATTERN,
    /\b[A-Z][A-Za-z0-9.-]*\b/gu,
    /\b[A-Z]{2,}\b/gu,
    /\b\d+(?:\.\d+){1,}\b/gu,
    /\d{4}년\s*\d{1,2}월\s*\d{1,2}일/gu,
    /\d+(?:\.\d+)?\s?(?:%|MB|GB|KB|ms|초|분|시간|원|달러)/gu
  ];
  return new Set([
    ...patterns.flatMap((pattern) => text.match(pattern) ?? []).filter(Boolean),
    ...collectKoreanProductNameCandidates(text)
  ]);
}

function countPatterns(text) {
  const counts = Object.fromEntries(PATTERNS.map(([id, pattern]) => {
    const input = PROSE_SPAN_FILTERED_IDS.has(id) ? removeProtectedProseSpans(text) : text;
    return [id, [...input.matchAll(pattern)].length];
  }));
  return { ...counts, ...countCalquePatterns(removeProtectedProseSpans(text)) };
}

// Every P id is span-filtered: a bug report quotes the offending text, and the quote must not
// count against the rewrite. P-1b counts only what P-1a did not claim; P-3 is counted after
// rendering sentences (alpha transparency) are dropped.
function countCalquePatterns(prose) {
  const counts = {};
  for (const [id, pattern] of [...CALQUE_GATING_PATTERNS, ...CALQUE_ADVISORY_PATTERNS]) {
    if (id === "P-1b") counts[id] = countP1bOnly(prose);
    else if (id === "P-3") counts[id] = countMatches(stripAlphaContextSentences(prose), P3_TRANSPARENT_PATTERN);
    else counts[id] = countMatches(prose, pattern);
  }
  return counts;
}

function collectKoreanProductNameCandidates(text) {
  const patterns = [
    /(?:^|[\n.!?]\s*)([\uAC00-\uD7A3][\uAC00-\uD7A3A-Za-z0-9.+-]{1,30})(?=은|는|이|가)/gu,
    /([\uAC00-\uD7A3][\uAC00-\uD7A3A-Za-z0-9.+-]{1,30})(?=\s*(?:앱|서비스|플랫폼|도구|브라우저|메신저|뷰어|에디터))/gu
  ];
  return patterns
    .flatMap((pattern) => [...text.matchAll(pattern)].map((match) => match[1]))
    .filter((token) => token.length >= 3 && !KOREAN_NAME_STOPLIST.has(token));
}

function requiredS1Count(counts, requiredIds = REQUIRED_S1_PATTERN_IDS) {
  return requiredIds.reduce((total, id) => total + (counts[id] ?? 0), 0);
}

function levenshtein(left, right) {
  let start = 0;
  while (start < left.length && start < right.length && left[start] === right[start]) start += 1;

  let leftEnd = left.length;
  let rightEnd = right.length;
  while (leftEnd > start && rightEnd > start && left[leftEnd - 1] === right[rightEnd - 1]) {
    leftEnd -= 1;
    rightEnd -= 1;
  }

  left = left.slice(start, leftEnd);
  right = right.slice(start, rightEnd);
  if (left.length === 0) return right.length;
  if (right.length === 0) return left.length;
  if (right.length > left.length) [left, right] = [right, left];

  let previous = Array.from({ length: right.length + 1 }, (_, index) => index);
  let current = Array.from({ length: right.length + 1 }, () => 0);
  for (let i = 1; i <= left.length; i += 1) {
    current[0] = i;
    for (let j = 1; j <= right.length; j += 1) {
      const cost = left[i - 1] === right[j - 1] ? 0 : 1;
      current[j] = Math.min(current[j - 1] + 1, previous[j] + 1, previous[j - 1] + cost);
    }
    [previous, current] = [current, previous];
  }
  return previous[right.length];
}

function grade({ after, changeRate, missing, problems }) {
  if (problems.length > 0 || missing.length > 0 || changeRate > 0.5) return "D";
  const s1After = requiredS1Count(after);
  const s2After = Object.entries(after)
    .filter(([id]) => ![...REQUIRED_S1_PATTERN_IDS, ...GRADE_EXEMPT_IDS, ...ADVISORY_PATTERN_IDS].includes(id))
    .reduce((total, [, count]) => total + count, 0);
  if (s1After === 0 && changeRate >= 0.1 && changeRate <= 0.3) return "A";
  if (s1After === 0 && s2After <= 4) return "B";
  return "C";
}

function fail(message) {
  console.error(message);
  process.exit(1);
}
