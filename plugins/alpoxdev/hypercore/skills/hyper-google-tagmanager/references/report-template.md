# Report Template

Read this file when writing `.hyper/gtm/<slug>/report.md`. The report is written in Korean; IDs, code, event and parameter names, and quoted documentation stay in English. `<slug>` is a short kebab-case name of the site and the job (`shop-purchase-event`); add `-2` when the folder exists for a different run.

## Files

```text
.hyper/gtm/<slug>/
├── report.md              # this report
├── detect.json            # gtm-detect.sh output, when run
├── site-<n>.json          # gtm-site-check.sh output per URL, when run
├── container-audit.json   # gtm-container-audit.sh output, when run
└── import.json            # container import draft, when configure wrote one
```

Never save credentials, tokens, `api_secret` values, full `gtm_auth` values, or dataLayer dumps containing customer data here.

## Template

```markdown
# <site> GTM <mode> 보고서

> 날짜: YYYY-MM-DD | 모드: audit|install|configure|verify|diagnose|analyze | 컨테이너: GTM-XXXX | 환경: Preview|<env>|Live
> 결과: verified | partial | proposed | exhausted | blocked

## 요약
[무엇을 확인했고 무엇이 바뀌었는지, 남은 위험 하나를 2-4문장으로 씁니다.]

## 현재 상태 (근거)
| 항목 | 값 | 근거 |
|---|---|---|
| 컨테이너 ID와 로더 수 | | gtm-site-check.sh `containers` |
| 직접 단 Google 태그 | | `googleTagIds` |
| 동의 기본값 순서 | | `order` |
| 프레임워크 | | gtm-detect.sh `frameworks` |

## 발견 사항
| 등급 | 코드 | 대상 | 근거 | 제안 |
|---|---|---|---|---|

## 이벤트 계획
| 이벤트 | 트리거 | 매개변수 | 대상 | 동의 유형 |
|---|---|---|---|---|

## 변경 내용
- 파일: <path>:<line> - <무엇을 바꿨는지>
- 컨테이너: <workspace/version, 추가·변경·삭제 항목>

## 검증
| 태그 | 트리거 이벤트 | 발화 | 요청 | 주요 매개변수 | 동의 상태 | 결과 |
|---|---|---|---|---|---|---|

## 승인과 게시
- 승인 받은 동작: <동작, 사용자 승인 문장 인용, 결과와 버전 ID> 또는 없음
- 제안만 한 동작: <정확한 동작, 바뀌는 것, 롤백 대상 버전 ID>

## 남은 위험
- [not verified 행, 열린 발견 사항, 데이터 지연·표본·임계값 주의]

## 출처
- [참고한 references 파일과 외부 문서, 확인 날짜]
```

## Writing Rules

- Lead with the result; every finding names its evidence.
- Use the `verified`, `failed`, `not verified` words from `rules/validation.md` §2 exactly.
- The `결과:` line names exactly one value from `rules/validation.md` §5, chosen by what this run's evidence supports.
- Absolute dates only.
- A proposed publish or deletion lists its exact action, not a summary.

## Sources

> Checked 2026-11-08.

| Claim | Source |
|---|---|
| The report shape and the file layout | this package's design |

### Evidence grade

`LOCAL` - template only; no external claim.
