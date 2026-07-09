#!/usr/bin/env node
import { readFile, writeFile } from "node:fs/promises";

const PATTERNS = [
  ["A-2", /를 통해|을 통해|통하여/gu],
  ["A-3", /에 있어서|에 있어/gu],
  ["A-7", /가지고 있다|가졌다/gu],
  ["A-8", /되어진다|되어졌다/gu],
  ["A-10", /할 수 있다|할 수 있을/gu],
  ["C-11", /(고|며|지만|아서|어서),/gu],
  ["D-1", /결론적으로|따라서|요약하면|정리하면/gu],
  ["D-2", /시사하는 바가 크다|주목할 만하다/gu],
  ["H-1", /(^|\n)\s*(또한|따라서|즉|나아가|아울러|게다가|더욱이)/gu],
  ["I-1", /인 것이다|한 것이다/gu],
  ["J-2", /"[^"]{1,40}"/gu]
];
const REQUIRED_S1_PATTERN_IDS = ["A-2", "A-3", "A-7", "A-8", "C-11", "D-1", "D-2", "H-1", "I-1"];
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
  const sourceRatio = koreanRatio(source);
  const finalRatio = koreanRatio(final);
  const protectedTokens = collectProtectedTokens(source);
  const missing = [...protectedTokens].filter((token) => !final.includes(token));
  const before = countPatterns(source);
  const after = countPatterns(final);
  const changeRate = levenshtein(source, final) / Math.max(source.length, 1);
  const problems = [];
  if (sourceRatio < 0.2) problems.push("Korean source text required");
  if (missing.length > 0) problems.push("Protected tokens changed");
  if (finalRatio < 0.2) problems.push("Final text is not Korean enough");
  if (changeRate > 0.5) problems.push("Change rate exceeds 50%");
  if (requiredS1Count(before) > 0 && requiredS1Count(after) >= requiredS1Count(before)) {
    problems.push("S1 AI-tell count not reduced");
  }

  const warnings = changeRate > 0.3 && changeRate <= 0.5 ? ["Change rate exceeds 30%"] : [];
  return {
    ok: problems.length === 0,
    grade: grade({ after, changeRate, missing, problems }),
    sourceChars: source.length,
    finalChars: final.length,
    changeRate: Number(changeRate.toFixed(4)),
    koreanRatio: {
      source: Number(sourceRatio.toFixed(4)),
      final: Number(finalRatio.toFixed(4))
    },
    protectedTokens: { total: protectedTokens.size, missing },
    patterns: { before, after },
    warnings,
    problems
  };
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
    sourceChars: 0,
    finalChars: 0,
    changeRate: 0,
    koreanRatio: { source: 0, final: 0 },
    protectedTokens: { total: 0, missing: [] },
    patterns: { before: {}, after: {} },
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

function koreanRatio(text) {
  const hangul = text.match(/[\u3131-\u318E\uAC00-\uD7A3]/gu)?.length ?? 0;
  const letters = text.match(/[\p{L}]/gu)?.length ?? 0;
  return letters === 0 ? 0 : hangul / letters;
}

function collectProtectedTokens(text) {
  const patterns = [
    /https?:\/\/\S+/gu,
    /`[^`]+`/gu,
    /"[^"]+"/gu,
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
  return Object.fromEntries(PATTERNS.map(([id, pattern]) => [id, [...text.matchAll(pattern)].length]));
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

function requiredS1Count(counts) {
  return REQUIRED_S1_PATTERN_IDS.reduce((total, id) => total + (counts[id] ?? 0), 0);
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
  const s1After = requiredS1Count(after) + (after["J-2"] ?? 0);
  const s2After = Object.entries(after)
    .filter(([id]) => ![...REQUIRED_S1_PATTERN_IDS, "J-2"].includes(id))
    .reduce((total, [, count]) => total + count, 0);
  if (s1After === 0 && changeRate >= 0.1 && changeRate <= 0.3) return "A";
  if (s1After === 0 && s2After <= 4) return "B";
  return "C";
}

function fail(message) {
  console.error(message);
  process.exit(1);
}
