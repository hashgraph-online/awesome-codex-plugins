# 리포트 템플릿

저장할 조사 리포트를 초안할 때 이 참고 파일을 사용합니다.

## 목차

- 파일 경로
- 템플릿
- `--quick` 변형
- 작성 규칙

## 파일 경로

기본, deep, parallel 실행에서는 `.hyper/research/[NN].slug.md`에 저장하고 저널은 `.hyper/research/[NN].slug/`에 둡니다.

예: `.hyper/research/03.websocket-vs-sse.md`와 `.hyper/research/03.websocket-vs-sse/`.

## 템플릿

```markdown
# [주제] 조사 리포트

> As of: YYYY-MM-DD 또는 버전 | Depth: quick/default/deep (+parallel) | Run state: converged/exhausted/blocked
> Sources reviewed: N | Sources cited: M | Domains: D | Waves: W | Excursions: X | Execution checks: V

## Executive Summary
[핵심 질문에 먼저 2-4문장으로 답합니다. 검증된 주장만 여기에 넣습니다.]

## Scope And Fidelity
- 핵심 질문:
- 축:
- 기간과 as of 기준점:
- source floor와 derived number 정책:
- 사용한 증거 채널:

## Key Findings
### 1. [발견]
- 주장: [진술] [S1][S4] (C1)
- 수치: [값] MEASURED [S1] | [값] DERIVED = [입력에 대한 계산식]
- 중요한 이유:

## Comparison
| 기준 | 옵션 A | 옵션 B | 출처 |
|------|------|------|------|

## Expected Truths
| 예상 진실 | 결과 | 근거 |
|---|---|---|
| E1 | true / violated / unknown | |

## Verified Claims
| 주장 | 종류 | 판정 | 근거 |
|---|---|---|---|
| C3 | code | CONFIRMED | `[NN].slug/verify-<slug>.md` |
| C1 | non-code | supported (도메인 2개, 1차 S1, 반대 검색 Q7) | [S1][S4] |

## Contradictions
- [출처 A와 출처 B: 해소 방식과 근거, 또는 열린 채로 두는 이유]

## Debate record
| 주장 | 판정 | claim에 대한 변경 |
|---|---|---|
| C1 | holds | |
| C5 | unverified (debate 공격 한 번) | Unresolved으로 이동 |

- 전체 debate 행은 journal 파일 `debate.md`에 있고, 이 부록은 고위험 claim마다 판정을 나열합니다.

## Unresolved And Refuted
- 미해결: [주장 - 빠진 내용]
- 반박됨: [주장 - 반대 근거]

## Risks And Caveats
- [한계, 약한 소스 caveat, 가정과 그 민감도 문장]

## Known Gaps
- [이번 실행이 답하지 못한 것. exhausted 실행이면 열린 lead와 확장 시 조사할 내용]

## Recommendation
- [의사결정이나 다음 행동. 검증된 주장에서만 끌어냅니다]

## Source Ledger
| # | Source | URL/path | Publisher | Published/updated | Accessed | Channel | Grade | Role | Used? |
|---:|---|---|---|---|---|---|---|---|---|

## Query Log
- [서로 다른 질의, 채널, 사용한 이유. 저널을 쓰는 실행이면 `queries.md`를 가리키는 포인터]

## Expansion Trace
- Wave 1: [검색이나 lane] -> [얻은 lead]; Wave 2: ...; stop reason: [규칙]

## Validation Notes
- Gates: structure, citation, claim gate, lineage, recency, read-back 항목별 통과나 남은 결함
- Source floor: [충족 또는 미달, 검토 수 대비 인용 수]
- Dedupe: [질의와 중복 소스 처리]

## Report gates
| 게이트 | 상태 (pass / fail / not_run) | 열려 있는 결함 심각도 (blocker / major / minor) | 이유 |
|---|---|---|---|
| structure | | | |
| citation | | | |
| claim gate | | | |
| number lineage | | | |
| recency | | | |
| read-back | | | |

## References
- [S1] [제목](https://example.com/source), 접근 YYYY-MM-DD
```

## `--quick` 변형

`--quick` 리포트는 머리말, Executive Summary, Scope And Fidelity, Key Findings, Risks And Caveats, Source Ledger, Query Log, Validation Notes, References를 유지합니다. 한 번의 수집으로 채울 수 없는 절은 빼고, claim-source matrix는 Key Findings 안에 둡니다.

## 작성 규칙

- 배경보다 답을 먼저 둡니다.
- 비자명한 주장에는 모두 ledger의 `[S<n>]` id로 인용을 붙입니다.
- 위험도가 높은 주장은 `verified-claims`에서만 단정합니다. 부속 항목은 Unresolved And Refuted 아래에만 둡니다.
- `## Debate record` 부록은 고위험 claim마다 판정을 나열하고, 전체 debate 행은 journal 파일 `debate.md`에 둡니다.
- 모든 수치에 `MEASURED`, `ASSUMED`, `DERIVED` 중 하나를 표시합니다.
- 최신성이 중요하면 정확한 날짜를 쓰고, 머리말에 as of 기준점을 밝힙니다.
- 여러 lane이 찾았더라도 중복 소스는 한 번만 셉니다.
- 인용은 원어 그대로 20단어 미만으로 하고, 리포트 언어가 다르면 인용 옆에 번역을 붙입니다.

## Sources

> 확인 2026-11-09.

| Claim | Source |
|---|---|
| 노력 머리말, verified-claims와 contradiction 절, 미해결·반박 부속 절, 확장 추적, 짧은 출처 표기 인용은 `ulw-research` 스킬의 종합 구성을 각색한 것 | <https://github.com/code-yeongyu/oh-my-openagent/tree/0d80470e4201925727e88afbafcdf24d7801a588> |
| source ledger 열과 검토 수 대비 인용 수 구분 | `instructions/sourcing/references/source-ledger.md` |
| 고위험 claim마다 판정을 나열하는 `## Debate record` 부록 | `dbc-hbin/omp-ulw`의 커밋 `74df40f` (2026-11-09). 소스 저장소에 license가 없어 메커니즘을 이 패키지의 문장으로 다시 썼고 텍스트나 코드를 복사하지 않았다 |

### 근거 등급

`LOCAL` - 이 파일은 이 패키지 자체의 템플릿을 담습니다. `https://example.com/source` 대상은 자리표시자 호스트이며 출처가 아닙니다.
