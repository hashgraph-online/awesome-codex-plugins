# Intake and Questions

첫 질문 전에 이 규칙을 사용한다. 플랫폼·규모 판정, 탐색 우선 순서, 질문 예산과 형식, 물을 가치가 없는 기본값을 소유한다.

## 1. 플랫폼을 먼저 정한다

대상 플랫폼은 `web`, `ios`, `android`, `desktop`이다. 여러 개인 것이 보통이다. 템플릿 기본값이 아니라 요청과 증거로 정한다.

| 신호 | 플랫폼 |
|---|---|
| 브라우저, URL, 반응형 레이아웃, 검색 노출, 탭 안 세션 | `web` |
| App Store, TestFlight, 아이폰·아이패드 빌드 | `ios` |
| Play Store, APK·AAB, 안드로이드 태블릿 빌드 | `android` |
| 설치형 애플리케이션, 트레이 아이콘, 설치 관리자, 자동 업데이트, 공증, 코드 서명 | `desktop` |

판정을 메타 블록에 한 줄 근거와 함께 적는다. 예: `platforms: web, ios - the request names a browser product and an App Store release`. 요청이 두 플랫폼 사이에서 정말 모호하고 답이 범위를 크게 바꾸면 그것은 질문 하나이지, 문서에 몰래 박아 둘 추측이 아니다.

플랫폼 결정은 체크리스트가 아니다. `prd.md`의 플랫폼 블록은 결정된 플랫폼과 남은 의무를 기록하고, 체크리스트가 생기면 그 블록을 채운다.

## 2. 규모를 정한다

| 규모 | 쓰는 때 | 문서에 미치는 영향 |
|---|---|---|
| `S` | 기존 제품 안의 기능 하나나 동작 변경 하나. 사용자에게 보이는 결과가 하나이고 새 표면이 없음 | 목표 하나, 스토리 하나나 둘, 짧은 요구사항 목록. 실제 범위를 담지 않으면 P2/P3 절을 두지 않음 |
| `M` | 새 제품 표면이나 여러 단계 흐름. 순서대로 출시할 수 있는 스토리 여럿 | 전체 절 집합, P1/P2/P3 스토리, 요구사항 여럿, 결정된 플랫폼마다 블록 |
| `L` | 새 제품, 여러 플랫폼, 제품 모델을 바꾸는 변경 | 전체 절 집합에 위험, 의존성, 바뀌면 안 되는 동작을 명시 |

규모를 한 줄 근거와 함께 적는다. 예: `size: S - one settings screen changes an existing flow`. 두 규모가 다 맞으면 작은 쪽을 택한다. 과대한 문서는 결함이다. 이 스킬이 피하려는 실패가 모든 아이디어를 제품 출시처럼 다루는 흐름이다.

## 3. 묻기 전에 탐색한다

질문이 답해질 때까지 다음 순서로 읽는다.

1. 저장소: 기존 제품 문서, README, 플랫폼이나 제약을 적은 설정
2. `.hyper/prd/` 아래 같은 제품의 기존 문서. 이미 결정된 PRD와 모순되지 않게 한다
3. 사용자가 붙여 준 맥락. 링크, 텍스트로 설명된 화면, 앞선 대화 포함

이 출처가 답하는 것을 묻지 않는다. 출처가 질문의 일부를 답하면 나머지만 묻는다. 두 출처가 어긋나면 그 불일치는 문서의 열린 질문에 넣을 발견이지, 범위를 막지 않는 한 사용자에게 할 질문이 아니다.

## 4. 질문 예산과 형식

| 규모 | 질문 |
|---|---|
| `S` | `S 1` |
| `M` | `M 3` |
| `L` | `L 5` |

모든 질문의 규칙:

- 한 번에 하나. 한 메시지에 번호 붙은 질문 목록을 내지 않는다.
- 선택지 2~5개. 각 선택지가 되묻지 않고 고를 수 있을 만큼 구체적이어야 한다.
- 권장안은 정확히 하나이고 한 문장 이유를 붙인다.
- 사용자만 결정할 수 있는 것만 묻는다. 사업 우선순위, 대상 사용자, 가격 의도, 법적 태도, 출시 범위, 둘 다 받아들일 수 있는 결과 사이의 맞바꿈이 해당한다.
- 문서가 가정으로 적을 수 있는 것을 묻지 않는다. 관례로 답이 나오면 관례를 택하고 표시한다.
- 무응답, "알아서", "적당히", 선택지를 고르지 않는 답은 권장안을 택해 `[가정: …]`으로 기록하고 계속한다. 다시 묻지 않는다. 표시는 그 값을 쓰는 문장에 붙인다. 침묵으로 정한 값을 질문에서 먼 절이라도 사실처럼 쓰지 않는다.
- 답이 없고 막히는 질문(그것 없이는 문서 범위를 정할 수 없음)은 `status: draft`를 유지하고, 답할 사람을 적어 열린 질문 절에 넣는다.

## 5. 물을 가치가 없는 기본값

요청이 반대하지 않으면 다음을 택한다. 범위를 바꿀 때만 그 선택을 가정으로 기록한다.

- 문서 본문 언어: 사용자 언어, 없으면 한국어
- 슬러그: 제품이나 기능 이름에서 만든 케밥 케이스
- 파일 위치: `.hyper/prd/<slug>/prd.md`
- 절 순서: 템플릿 순서
- 상태: 막힘 질문 없이 체크리스트가 통과할 때까지 `draft`
- 우선순위 척도: 목표 달성에 없으면 안 되는 요구사항이 `P0`, 첫 출시 범위가 `P1`, 이후 요구사항이 `P2`
- 지표 측정 시점: 제품이 현실적으로 관측할 수 있는 첫 측정 창. 비워 두지 않고 명시한다
- 플랫폼 체크리스트 내용: 남은 의무로 기록하고 지어내지 않는다

## 6. 인테이크를 보고한다

절을 쓰기 전에 짧은 블록 하나로 밝힌다. 근거가 붙은 플랫폼, 근거가 붙은 규모, 예산이 허용하는 질문 수, 읽은 출처다. 이 블록은 `prd.md`의 메타 영역에 들어가고 별도 파일이 되지 않는다.

## Sources

> 확인 2026-11-07.

| Claim | Source |
|---|---|
| 열린 인터뷰 대신 상한이 있는 질문 수 | [snarktank/ai-dev-tasks create-prd](https://raw.githubusercontent.com/snarktank/ai-dev-tasks/main/create-prd.md) - "Limit questions to 3-5 critical gaps in understanding." |
| 한 번에 질문 하나와 세션 전체 상한 | [spec-kit clarify](https://raw.githubusercontent.com/github/spec-kit/main/templates/commands/clarify.md) - "Maximum of 5 total questions across the whole session." / "Present EXACTLY ONE question at a time." |
| 묻지 않아도 되는 합리적 기본값 목록 | [spec-kit specify](https://raw.githubusercontent.com/github/spec-kit/main/templates/commands/specify.md) - "Examples of reasonable defaults (don't ask about these)" |
| 묻는 대신 사실을 찾음 | [OpenAI Codex plan template](https://raw.githubusercontent.com/openai/codex/main/codex-rs/collaboration-mode-templates/templates/plan.md) - "Eliminate unknowns in the prompt by discovering facts, not by asking the user." |
| 구조나 결정을 바꾸는 것만 물음 | [Citadel prd](https://github.com/SethGammon/Citadel) - "Ask up to 3 questions — only those that would change the architecture." |
| 플랫폼별 의무를 처음부터 PRD에 넣음 | [strvcom flutter-template prd](https://github.com/strvcom/flutter-template) |
| 문제 크기에 비례하는 문서 | [Martin Fowler, SDD 도구 비교](https://martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html) - "it quickly became clear that the workflow was like using a sledgehammer to crack a nut" |

### 근거 등급

`LOCAL` - 플랫폼 표, 규모 표, 기본값 목록은 이 패키지의 설계다. `S 1, M 3, L 5` 예산은 인용한 상한을 조합해 고른 값이지 측정된 최적값이 아니다.
