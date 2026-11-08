# GTM 워크플로

**Purpose**: 모드 하나를 골라 단계를 순서대로 실행하고 검증으로 이어 붙여, 설치나 컨테이너 변경이 증명 없이 끝나지 않게 합니다.

## 1. Mode Selection

요청한 결과물로 모드를 고르고, 1단계 스크립트 출력으로 확인합니다.

| Mode | Requested output | Ends with |
|---|---|---|
| `audit` | 사이트, 저장소, 컨테이너 내보내기가 무엇을 불러오고 무엇이 잘못됐는지에 대한 발견 사항 | 보고서만. 편집 없음 |
| `install` | dataLayer, 동의 기본값, SPA 페이지 뷰, CSP를 처리한 GTM이 사이트에서 로드됨 | `verify` |
| `configure` | 작업공간 초안이나 가져오기 JSON으로 만들거나 바꾼 컨테이너 항목 | `verify`, 그다음 게시 게이트 |
| `verify` | 지정한 태그가 올바른 데이터와 동의 상태로 발화한다는 증명 | 검증 표 |
| `diagnose` | 빠지거나 중복되거나 잘못된 신호를 찾아 고치고 다시 검증함 | 전후 근거 |
| `analyze` | 컨테이너 상태 지표나 목적지 데이터를 이벤트 계획과 대조함 | 보고서만. 편집 없음 |

- 결과물을 여럿 지정한 요청은 `audit` -> `install` -> `configure` -> `verify` 순서로 모드를 실행합니다. 검사가 실패하면 `diagnose`가 `verify`를 대신합니다.
- "점검만", "audit only", "고치지 말고", "do not change"는 고칠 수 있는 발견 사항이 있어도 실행을 `audit`이나 `analyze`에 붙잡아 둡니다. 수정은 제안으로 적습니다.
- 이미 GTM을 불러오는 사이트에서의 `install`은 먼저 `audit`이 됩니다. 기존 컨테이너를 보고하고, 유지할지, 교체할지, 요청한 태그를 거기에 더할지 한 번 묻습니다. 기존 컨테이너 유지를 권합니다.

## 2. Phases Per Mode

### `audit`

1. 저장소가 범위에 있으면 `scripts/gtm-detect.sh --root <repo>`를 실행합니다.
2. 지정한 URL마다 `scripts/gtm-site-check.sh --url <url> --check-loader`를 실행합니다. 최소한 홈 페이지와 깊은 페이지 하나에서 실행합니다.
3. 사용자가 내보내기를 제공했거나 API가 컨테이너 버전을 반환했으면 `scripts/gtm-container-audit.sh --file <export.json>`을 실행합니다.
4. 렌더링된 브라우저를 쓸 수 있으면 페이지를 열고 `googletagmanager.com`과 `/g/collect` 요청을 기록하며 `window.dataLayer`와 `window.google_tag_manager` 키를 읽습니다(`references/verification.md`).
5. 발견 사항마다 `error`, `warn`, `info`로 등급을 매기고 근거를 붙이며, 적용할 모드와 함께 수정을 제안합니다.

### `install`

1. `references/install-recipes.md` §1로 태그 전략을 정합니다. GTM을 쓸지, 제품 하나에 변경이 드물어 직접 Google 태그를 쓸지입니다. 한 ID에 둘 다 설치하지 않습니다.
2. 코드를 쓰기 전에 이벤트 계획 표(`references/container-design.md` §1)를 작성합니다.
3. 컨테이너의 설치 대화상자나 API `snippet` 메서드에서 스니펫을 가져옵니다. 아니면 `references/install-recipes.md` §2의 현재 형태를 쓰고 어느 형태를 썼는지 기록합니다.
4. 동의 기본값(`references/consent.md` §2)과 페이지 수준 dataLayer 푸시를 스니펫 위에 둡니다.
5. 프레임워크 레시피(`references/install-recipes.md` §3), SPA 규칙(§4), CSP 규칙(§5)을 적용합니다.
6. `gtm-detect.sh`를 다시 실행해 컨테이너 하나, 로더 하나, 같은 ID의 직접 Google 태그 없음을 확인합니다.
7. `verify`로 이어 갑니다.

### `configure`

1. 현재 컨테이너를 읽습니다. 내보내기 또는 API의 `accounts.containers.versions.live`와 작업공간을 씁니다(`references/api-and-analysis.md` §1).
2. 그 컨테이너에 `gtm-container-audit.sh`를 실행해 알려진 부채에서 변경을 시작합니다.
3. 변경마다 이벤트 계획 행으로 쓰고, `references/container-design.md` §7의 이름 규칙에 따라 작업공간 항목이나 가져오기 JSON으로 만듭니다.
4. 새 태그마다 동의 설정을 지정합니다(`references/consent.md` §3).
5. Preview(Tag Assistant)나 `quick_preview`를 열고 `verify`로 이어 갑니다.
6. `rules/safety-gates.md` §1의 게시 게이트에서 멈춥니다.

### `verify`

1. 먼저 비운영 환경이나 Preview를 씁니다(`references/verification.md` §1-§2).
2. 계획의 태그마다 트리거 이벤트, 태그 발화 여부, 보낸 요청, 주요 매개변수, 동의 상태를 기록합니다.
3. 변경을 실은 페이지에 `gtm-site-check.sh`를 실행합니다.
4. 태그마다 `verified`, `failed`, `not verified`로 이유와 함께 보고합니다. 표준 보고서는 증명이 아닙니다. 요청이나 디버그 이벤트가 증명입니다.

### `diagnose`

이 순서로 좁히고 증상을 설명하는 첫 계층에서 멈춥니다.

1. 로딩: 컨테이너가 서버가 보낸 페이지나 렌더링된 페이지에 한 번, 올바른 ID로 있고 `gtm.js`가 비어 있지 않은 컨테이너를 반환하는가(`references/verification.md` §4)?
2. 차단: CSP 위반, 광고 차단기, 전부 거부하는 `gtag('policy')`, `gtm.blocklist`, 방화벽.
3. 순서: 동의 기본값과 dataLayer 푸시가 스니펫보다 앞서는가, 로드 뒤에 `dataLayer = []`를 두지 않았는가.
4. 트리거: 이벤트가 dataLayer에 도달했는가, 트리거 조건이 그것과 맞았는가?
5. 동의: 태그가 설정대로 동의를 기다렸는가 건너뛰었는가?
6. 목적지: 요청이 브라우저를 떠났는가, 도착했는가(DebugView, 실시간, 벤더 디버거)?

시도마다 한 가지만 바꾸고 같은 검사를 다시 돌리며 전후를 기록합니다. 한 근본 원인에 세 번 실패하면 `exhausted`로 끝냅니다.

### `analyze`

1. `gtm-container-audit.sh`를 실행하고 개수, 태그 유형, 발견 사항을 보고합니다.
2. 컨테이너의 태그를 이벤트 계획이나 사용자 목록과 비교합니다. 계획에 있지만 빠진 것, 있지만 계획에 없는 것입니다.
3. 사용자가 데이터 확인을 원하고 읽기 자격 증명이 있으면 실시간이나 최근 며칠 보고서에서 관측한 이벤트를 계획과 비교합니다(`references/api-and-analysis.md` §5). 데이터 지연과 표본 추출이나 임계값 적용 여부를 밝힙니다.

## 3. Target Line

2단계 전에 한국어 줄 하나를 출력합니다.

```text
대상: <site or repo> / 컨테이너: <GTM-ID or 없음> / 환경: <Preview|<env name>|Live> / 근거: <script and finding that showed the current state>
```

## Sources

> Checked 2026-11-08.

| Claim | Source |
|---|---|
| 게시 전 확인 수단으로서의 Preview와 Tag Assistant | <https://support.google.com/tagmanager/answer/6107056> |
| 표준 보고서는 지연되고 요청과 DebugView가 즉시 확인 수단이라는 점 | <https://developers.google.com/analytics/devguides/collection/ga4/troubleshoot> |
| 진단 계층(로딩, 차단, 순서, 트리거, 동의, 목적지) | this package's design over `references/verification.md` |

### Evidence grade

`LOCAL` - 모드 순서와 진단 순서는 검증된 최적값이 아니라 이 패키지의 설계입니다.
