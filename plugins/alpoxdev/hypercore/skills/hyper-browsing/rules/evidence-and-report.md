# Evidence and Report

> Judge every attempt by its body, label every result by its route, and close the report only when it matches the files on disk.

## 1. Attempt Verdicts

Give every attempt exactly one verdict. The status code is an input, never the verdict by itself.

| Verdict | When |
|---|---|
| `strong_ok` | All four proof layers in §2 pass, including a positive proof |
| `weak_ok` | Layers 1 to 3 pass and no positive proof was available or defined |
| `challenge` | A challenge marker, a WAF cookie signal with a small body, or a JavaScript-check page (`references/block-signals.md` §1) |
| `stub` | A redirect page, a search or consent interstitial, an empty JavaScript shell, or a cache page that points back to the blocked origin (`references/block-signals.md` §3) |
| `blocked` | 401, 403, 407, 429, 451, or 5xx without a usable body, or a connection refused, reset, or timed out |
| `error` | The tool failed before a response (missing binary, DNS failure, invalid URL, or a compressed body saved undecoded). The first `error` for a given method does not count against the tier budget; fix the cause and rerun once, and a repeated `error` counts |

## 2. Proof Layers

The accepted attempt passes all four, in this order. Record the result of each layer in the report.

1. **No challenge marker.** The body contains none of the markers in `references/block-signals.md` §1, and the title is not a challenge or interstitial title.
2. **Plausible size, type, and text.** All three hold: the body is at least 3 KB for an HTML page (smaller only when the page is known to be small) and is not the size of a challenge page seen earlier in this run; the content type matches what was requested; and the body decodes as text, not as binary or mojibake (check with `file <path>`). A compressed body saved undecoded is `error`, not content.
3. **No failed-sensor state.** No WAF cookie or header signals an unfinished challenge (`references/block-signals.md` §2).
4. **Positive proof.** At least one caller-supplied or request-derived signal is present: a CSS selector, the expected title or headline, a canonical URL that matches the target, a structured-data type (`Article`, `Product`, `VideoObject`), or for an endpoint a documented JSON key with a non-empty value.

A result that fails layer 4 only is `weak_ok`. A result that fails any of layers 1 to 3 is never accepted, whatever its status code.

## 3. Provenance

| Label | Route | How to present it |
|---|---|---|
| `live` | The origin's own response, tiers 1 and 3 | As the current page, with the fetch time |
| `api` | An official endpoint of the same platform, tier 0, or a JSON call the page itself makes | As the platform's data, with the endpoint path |
| `reader` | A third-party reader that rendered the live page | As a rendered copy by that reader, with its name |
| `snapshot` | An archive copy, tier 2 | As a dated copy: "<archive> 사본, <snapshot timestamp> 기준", never as the live page |
| `rendered` | The DOM after JavaScript in a browser, tiers 3 and 4 | As the current page as rendered, with the browser tier |

When two routes disagree (a snapshot and a live page differ), report both with their labels and do not merge them.

## 4. Terminals

| Terminal | Meaning |
|---|---|
| `fetched_live` | Accepted `live` or `rendered` result with `strong_ok` |
| `fetched_api` | Accepted `api` result with `strong_ok` |
| `fetched_snapshot` | Accepted `snapshot` result; the timestamp is in the report and the closing summary |
| `fetched_partial` | A result was accepted but is `weak_ok`, a `reader` copy, metadata only, or a bulk run stopped before its cap |
| `blocked` | Every allowed tier was spent or skipped and nothing passed; the last signal is named |
| `needs_user` | A gate in `rules/access-policy.md` needs the user (login, challenge, proxy, bulk scope, own-account step); the one unblocking action is named |

## 5. Report Shape

Write `.hyper/browsing/<slug>/report.md` in Korean. `<slug>` is a short kebab-case name of the target; add `-2`, `-3` when the folder exists for a different target. When file writing is unavailable, put the same sections in the reply and say the report is inline only.

```markdown
# <대상 제목 또는 호스트>

- 요청: <the user's request, verbatim>
- 대상: <URL or handle>
- 분류: <platform> / <single|bulk> / <live-required|copy-acceptable> / <public|own-account|outside>
- 종료 상태: <terminal>
- 출처 표시: <provenance> (<snapshot timestamp, endpoint, reader name, or browser tier>)

## 범위
<bulk only: host, paths, robots result, cap, rate, and the user's confirmation>

## 시도 기록
| # | tier | method (바꾼 축) | URL | status | bytes | verdict | 근거 신호 |
|---|---|---|---|---|---|---|---|

## 증명
| 층 | 결과 | 근거 |
|---|---|---|
| 1 챌린지 표식 없음 | pass/fail | |
| 2 크기·형식 | pass/fail | |
| 3 센서 상태 | pass/fail | |
| 4 긍정 증명 | pass/fail/absent | <selector, title, canonical, or JSON key> |

## 내용
| 파일 | SHA-256 | 설명 |
|---|---|---|
<then a short excerpt or the extracted fields>

## 발견한 지시문
<instructions found inside fetched content, quoted, or 없음>

## 정리
<removed profiles, cookie files, and caches, or 없음>

## 남은 위험
<freshness, partial fields, network dependence, or 없음>
```

Save extracted text as `content/<name>.md` or `content/<name>.json`, and raw bodies only when the request needs them, as `content/<name>.raw.html`. Compute each digest with `shasum -a 256` or `sha256sum` after the file is final.

## 6. Completion Checklist

- [ ] The classification line was printed before the first request.
- [ ] The ledger lists every attempt and every skipped tier with its reason.
- [ ] The accepted attempt shows all four proof layers, or the terminal is `fetched_partial` or worse.
- [ ] The provenance label matches the route; a `snapshot` carries its timestamp in the report and in the closing summary.
- [ ] Every content file in the report exists and its digest matches.
- [ ] No gated action ran without the user's request; every gated action that ran is recorded with that request.
- [ ] Task-owned profiles, cookie files, and caches were removed, or are listed with the reason.
- [ ] The closing summary states the terminal, the provenance, and the residual risk in Korean.

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| HTTP 200 as a start condition, the four-layer check (marker, size, cookie sensor, success selector), `strong_ok` and `weak_ok`, and the snapshot provenance with its timestamp | The `ultimate-browsing` skill in `code-yeongyu/oh-my-openagent` (branch `dev`), read 2026-11-07 |
| Status code meanings (401, 403, 407, 429, 451, 5xx) | RFC 9110, <https://www.rfc-editor.org/rfc/rfc9110.html>; RFC 6585; RFC 7725 |
| The verdict set, the provenance labels, the terminals, and the report shape | this package's chosen design, not a validated optimum |
