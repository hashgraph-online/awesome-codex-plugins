// Korean adverb and compound-term calques (English carried across word-for-word) that mark
// LLM-written technical prose. Measured on GitHub issues 2026-09-10: 조용히 grew 381x from
// pre-ChatGPT to 2026 against 4x for control vocabulary, with a third of hits carrying an
// AI-authorship footer. See docs/specs/2026-09-10-korean-calque-rules-design.md.
//
// Single source for the P family. The audit imports it; any Stop-time nudge or doctor check
// must import it too rather than copying a regex, so the tiers cannot drift apart.

// Program actions a system performs "silently". Verb stems (잘리, 멈추, 죽) match any inflection;
// Sino-Korean nouns (실패, 무시, 누락, 중단, 종료, 삭제) must carry verbal morphology (실패한다,
// 무시됨, 종료된) so the bare noun in 실패 원인 or 무시 사례 is not a program action. Up to two
// intervening tokens absorb an object or adverb (조용히 H2로 기동된다).
const PROGRAM_ACTION = "실패(?:한|했|합|해|하|다|로|함)|무시(?:한|했|합|해|하|된|됐|됩|되|당|함)|누락(?:된|됐|됩|되|한|했|시|됨)|중단(?:된|됐|됩|되|한|했|시|됨)|종료(?:된|됐|됩|되|한|했|시|됨)|삭제(?:된|됐|됩|되|한|했|됨)|사라|잘리|잘린|잘림|잘라|건너뛰|죽|깨지|깨진|멈추|멈춘|멈춤|비어|빠지|빠진|넘어가|덮어|no-?op|skip";

// Human actions and settings that 조용히 legitimately modifies. Anything else after 조용히 is
// the calque: programs do not act 조용히, people do.
const HUMAN_ACTION = "앉|말|얘기|이야기|대화|속삭|물러|떠나|지내|기다리|듣|들었|웃|울|걷|살|잠|쉬|지켜|바라|생각|읊|읽|되짚|돌아보|살펴|회고|분석|검토|정리|기록|관찰|고민|준비|공부|연습|하세요|하자|해라|밤|아침|분위기|공간|마을|동네|사람|성격|목소리";

export const P1A_SILENCE_PATTERN = new RegExp(`조용(?:히|한)\\s*(?:[가-힣A-Za-z0-9_.%]+\\s+){0,2}(?:${PROGRAM_ACTION})`, "gu");
export const P1B_SILENCE_PATTERN = new RegExp(`조용(?:히|한)(?!\\s*(?:[가-힣]+\\s+){0,2}(?:${HUMAN_ACTION}))`, "gu");
export const P2_GRACEFUL_PATTERN = /우아(?:하게|한)\s*(?:[가-힣]+\s+)?(?:종료|실패|축소|처리|중단|저하|대응|폴백|재시도)/gu;
export const P3_TRANSPARENT_PATTERN = /투명(?:하게|한)\s*(?:[가-힣]+\s+)?(?:처리|동작|작동|지원|전달|연결|통합|전환|교체|대체|적용|마이그레이션|프록시|캐시|재시도|폴백|위임|포워딩|라우팅)/gu;
// 투명 in a sentence about rendering is alpha transparency, not the "invisible to the caller"
// calque. Sentences carrying these words are dropped before P-3 is counted.
export const P3_ALPHA_CONTEXT_PATTERN = /배경|색|알파|투명도|이미지|레이어|opacity|png/iu;
export const P4_SSOT_PATTERN = /단일\s*진실\s*(?:공급원|소스|원천|의\s*원천)/gu;
// No trailing boundary: particles attach directly (정본을, 정본으로). The leading boundary
// already excludes 수정본 and 개정본.
export const P5_CANONICAL_PATTERN = /(?<![가-힣])정본/gu;
export const P6_FAILSAFE_PATTERN = /안전하게\s*실패|(?<![가-힣])첫날부터/gu;

// Quoted spans, inline code, and fenced code blocks are protected byte-for-byte, so a calque inside
// them is the source's, not the writer's. Every consumer strips these before counting; shared here so the audit and the
// write-time nudge cannot disagree about what a quote is.
export const PROTECTED_PROSE_SPAN_PATTERN = /```[\s\S]*?```|`[^`\r\n]+`|"[^"\r\n]+"|“[^”\r\n]+”|‘[^’\r\n]+’|「[^」\r\n]+」|『[^』\r\n]+』/gu;

export function removeProtectedProseSpans(text) {
  return text.replace(PROTECTED_PROSE_SPAN_PATTERN, "");
}

// Hangul share of all letters; the audit's Korean-text threshold is 0.2.
export function koreanRatio(text) {
  const hangul = text.match(/[\u3131-\u318E\uAC00-\uD7A3]/gu)?.length ?? 0;
  const letters = text.match(/[\p{L}]/gu)?.length ?? 0;
  return letters === 0 ? 0 : hangul / letters;
}

// Fail tier: grade A/B requires these at zero in the rewrite.
export const CALQUE_GATING_PATTERNS = [
  ["P-1a", P1A_SILENCE_PATTERN],
  ["P-2", P2_GRACEFUL_PATTERN],
  ["P-4", P4_SSOT_PATTERN]
];

// Warn tier: reported, never graded. P-3 is advisory because developer prose uses 투명하게 for
// alpha and disclosure far more often than for the calque; P-5 keeps its legal sense; P-6 has
// unproven AI attribution (its footer share sits below baseline) and 첫날부터 can be literal.
export const CALQUE_ADVISORY_PATTERNS = [
  ["P-1b", P1B_SILENCE_PATTERN],
  ["P-3", P3_TRANSPARENT_PATTERN],
  ["P-5", P5_CANONICAL_PATTERN],
  ["P-6", P6_FAILSAFE_PATTERN]
];

export const CALQUE_PATTERN_IDS = [...CALQUE_GATING_PATTERNS, ...CALQUE_ADVISORY_PATTERNS].map(([id]) => id);

// One ladder step per id, quoted in audit warnings. Deletion first; a symptom stated from
// supplied facts second; never a stock replacement phrase (정본, 페일세이프, 그레이스풀 and the
// ~없이 family measure as AI tells themselves).
export const CALQUE_REPAIR_HINTS = {
  "P-1a": "조용히 is for people. Delete it when the verb already implies unnoticed behavior (조용히 무시된다 → 무시된다), or state the observed symptom from supplied facts.",
  "P-1b": "조용히 modifies a program action here. Say what the program did and which signal it did not give; do not swap in 아무 표시 없이 or 티 안 나게.",
  "P-2": "우아하게 is a calque of gracefully. Delete it and keep the plain verb (종료한다) unless the source states what happens to in-flight work; never assert on your own that requests finish, drain, or are cancelled. A developer genre may keep `graceful shutdown` in backticks.",
  "P-3": "투명하게 means disclosed in Korean, not unnoticed by the caller. If the source means the latter, say 사용자가 손댈 것 없이 or 코드 변경 없이; if it means alpha or disclosure, keep it.",
  "P-4": "단일 진실 공급원 is a calque of single source of truth. Use 기준 데이터 or state the fact (설정은 이 파일 하나만 본다); developer genres may keep `SSOT` in backticks.",
  "P-5": "정본 in the canonical-data sense is itself an AI tell (4,631x since 2022). Prefer 기준 데이터 or name the file; keep the legal sense.",
  "P-6": "안전하게 실패 reads as a contradiction in Korean; say what state the failure leaves (실패하면 기본값으로 되돌린다). 첫날부터 is filler unless a real date replaces it."
};

// Count tier-B silence hits that tier-A did not already claim, so one 조용히 is never
// reported twice. Both patterns anchor on the same 조용 token, so a shared start index is
// the whole overlap test.
export function countP1bOnly(text) {
  const claimed = new Set([...text.matchAll(P1A_SILENCE_PATTERN)].map((match) => match.index));
  return [...text.matchAll(P1B_SILENCE_PATTERN)].filter((match) => !claimed.has(match.index)).length;
}

// Drop sentences that talk about rendering before counting P-3. Sentence boundaries are
// terminal punctuation or a line break; Korean prose rarely needs more than that here.
export function stripAlphaContextSentences(text) {
  return text
    .split(/(?<=[.!?。])\s+|\n/u)
    .filter((sentence) => !P3_ALPHA_CONTEXT_PATTERN.test(sentence))
    .join("\n");
}
