# 보고서 템플릿

`.hyper/gtm/<slug>/report.md`를 쓸 때 이 파일을 읽습니다. 보고서는 한국어로 쓰고 ID, 코드, 이벤트와 매개변수 이름, 인용한 문서는 영어로 유지합니다. `<slug>`는 사이트와 작업을 나타내는 짧은 케밥 표기 이름이며(`shop-purchase-event`), 다른 실행 때문에 폴더가 이미 있으면 `-2`를 붙입니다.

## Files

```text
.hyper/gtm/<slug>/
├── report.md              # this report
├── detect.json            # gtm-detect.sh output, when run
├── site-<n>.json          # gtm-site-check.sh output per URL, when run
├── container-audit.json   # gtm-container-audit.sh output, when run
└── import.json            # container import draft, when configure wrote one
```

자격 증명, 토큰, `api_secret` 값, 전체 `gtm_auth` 값, 고객 데이터가 담긴 dataLayer 덤프를 여기에 저장하지 않습니다.

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

- 결론을 먼저 씁니다. 모든 발견 사항은 근거를 밝힙니다.
- `rules/validation.md` §2의 `verified`, `failed`, `not verified` 단어를 그대로 씁니다.
- 날짜는 절대 날짜만 씁니다.
- 제안한 게시나 삭제는 요약이 아니라 정확한 동작을 적습니다.

## Sources

> Checked 2026-11-08.

| Claim | Source |
|---|---|
| 보고서 형태와 파일 배치 | this package's design |

### Evidence grade

`LOCAL` - 템플릿만 있으며 외부 주장이 없습니다.
