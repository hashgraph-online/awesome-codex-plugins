# MCP and Auth

자격 증명 질문, API 활성화 질문, 공식 Google Analytics MCP 서버에 대한 결정에서 이 참조를 읽습니다. 애플리케이션 기본 자격 증명 설정, 속성 접근 부여, 켜야 할 두 API, 서버 설치, 읽기 전용 기본값, 전체 도구 목록, 서버가 연결되지 않았을 때의 REST 대체 경로를 소유합니다.

> 영어판: [`mcp-and-auth.md`](mcp-and-auth.md)

## Contents

- Credential setup
- Property access
- Enable both APIs
- The MCP server
- Tool list
- Read-only default and write tools
- REST fallback
- Stop conditions

## Credential setup

두 범위를 한 번에 받는 애플리케이션 기본 자격 증명 명령입니다.

```sh
gcloud auth application-default login \
  --scopes="https://www.googleapis.com/auth/cloud-platform,https://www.googleapis.com/auth/analytics.readonly"
```

- `cloud-platform`은 클라이언트 라이브러리와 할당량 귀속 경로에 필요하고, `analytics.readonly`는 Data API와 Admin API 모두의 읽기 범위입니다.
- `analytics.edit`은 실행이 쓸 때만 범위 목록에 더합니다. 쓰기가 없는 실행이 edit 범위를 가진 자격 증명은 실행이 필요한 것보다 넓습니다.
- 서비스 계정은 가장(impersonation)으로 동작합니다. `gcloud auth application-default login --impersonate-service-account=SERVICE_ACCOUNT_EMAIL --scopes=...`입니다.
- 요청이 클라우드 프로젝트에 할당량으로 귀속되도록 `GOOGLE_CLOUD_PROJECT`를 설정합니다. 프로젝트가 없는 것은 인증 실패가 아니라 할당량 귀속의 공백이며 그렇게 보고합니다.
- 아무것도 출력하지 않고 존재를 확인합니다. `[ -n "${GOOGLE_APPLICATION_CREDENTIALS:-}" ]`입니다. 자격 증명 존재를 증명하려고 `echo`, `env`, 설정 덤프, `gcloud auth print-access-token`을 쓰지 않습니다. 토큰 명령은 베어러 토큰을 셸 기록과 대화 기록에 남깁니다.

## Property access

- 자격 증명의 신원은 Google Analytics UI에서 속성 접근도 부여받아야 합니다. "In the Google Analytics UI, grant your user account access to a Google Analytics property."
- 서비스 계정은 기본적으로 속성 사용자가 아닙니다. 인증은 되는데 속성이 하나도 안 보이는 신원은 자격 증명이 깨진 것이 아니라 접근 부여가 빠진 것입니다.
- 부여와 범위는 별개 게이트입니다. `analytics.readonly`는 있고 속성 역할이 없는 실행은 아무것도 읽지 못하고, 속성 역할은 있고 범위가 없는 실행은 속성을 조회하기 전에 거부됩니다. 어느 쪽이 실패했는지 보고합니다.
- 속성 역할은 쓰기를 따로 정합니다. 맞춤 측정기준은 Editor, 핵심 이벤트는 Marketer 또는 Editor입니다.

## Enable both APIs

자격 증명을 소유한 클라우드 프로젝트에서 두 API를 모두 켜야 합니다.

```sh
gcloud services enable analyticsdata.googleapis.com analyticsadmin.googleapis.com
```

- 요구 사항은 두 서비스 이름 `analyticsdata.googleapis.com`과 `analyticsadmin.googleapis.com`입니다. `gcloud services enable` 줄은 그것을 켜는 일반적인 방법이며, 문서 인용이 아니라 호출 예로 적습니다.
- `analyticsdata.googleapis.com`이 `runReport`와 나머지 Data API를, `analyticsadmin.googleapis.com`이 `accountSummaries.list`와 Admin API를 서비스합니다.
- Admin API 읽기는 되는데 리포트가 실패하면 data API만 꺼진 것이고, 그 반대면 그 반대입니다. 호출을 재시도하지 말고 꺼진 API와 그것이 막는 단계를 밝힙니다.
- API 활성화 오류는 프로젝트 수준 설정입니다. 새 로그인, 새 범위, 다른 속성으로 고쳐지지 않습니다.

## The MCP server

Google이 이 표면에 공식으로 내는 에이전트 도구는 하나입니다. `googleanalytics/google-analytics-mcp`이고 PyPI 이름은 `analytics-mcp`입니다.

```sh
pipx run analytics-mcp
```

- `pipx run`으로 설치합니다. 이 서버에 문서화된 `uvx` 호출은 없습니다.
- 고정에 의미 있는 버전 이력은 이렇습니다. 1.0.0은 실험 단계를 졸업한 2026-11-03에, 1.1.0은 Admin 쓰기 도구와 실시간용 `minute_ranges`를 더한 2026-11-06에 나왔습니다. 쓰기 도구가 필요한 레시피는 1.1.0 이상을 요구합니다.
- 서버는 Apache-2.0, Python 3.10 이상이고, Google이 내는 별도 `analytics` CLI는 없습니다. MCP 서버가 CLI에 해당하는 표면입니다.
- 클라이언트 등록은 자격 증명을 환경으로 넘깁니다. 예를 들어 `-e GOOGLE_APPLICATION_CREDENTIALS=... -e GOOGLE_CLOUD_PROJECT=... -- pipx run analytics-mcp`입니다. 값은 환경 참조이고 커밋된 설정에 리터럴로 넣지 않습니다.
- 멀티테넌트 배포는 `--transport http --stateless-http`를 쓰거나, `--oauth`와 `GOOGLE_OAUTH_CLIENT_ID` / `GOOGLE_OAUTH_CLIENT_SECRET`을 쓰는 내장 OAuth 2.1 경로를 씁니다. OAuth 상태가 메모리에 있으므로 그 경로는 단일 인스턴스를 전제합니다.

## Tool list

도구 열세 개 전부, 읽기 열 개와 쓰기 세 개입니다. 쓰기 열은 읽기 너머로 그 도구가 무엇을 더 요구하는지 적습니다.

| Tool | Access | What it returns or changes | Extra requirement for a write |
|---|---|---|---|
| `get_account_summaries` | 읽기 | 자격 증명이 볼 수 있는 모든 계정과 속성 | - |
| `get_property_details` | 읽기 | 속성 하나의 설정 | - |
| `list_google_ads_links` | 읽기 | 속성의 Google Ads 연결 | - |
| `list_property_annotations` | 읽기 | 속성의 데이터 주석 | - |
| `list_key_events` | 읽기 | 속성의 핵심 이벤트 | - |
| `run_report` | 읽기 | Data API 리포트 | - |
| `run_funnel_report` | 읽기 | 뒤에 v1alpha 표면이 있는 퍼널 리포트 | - |
| `run_conversions_report` | 읽기 | 연결된 경우 Google Ads 비용·기여 행을 포함한 전환 리포트 | - |
| `get_custom_dimensions_and_metrics` | 읽기 | 속성의 맞춤 정의 | - |
| `run_realtime_report` | 읽기 | 지난 30분의 실시간 리포트 | - |
| `create_property_annotation` | 쓰기 | 데이터 주석을 만듭니다 | `--allow-write`와 `analytics.edit` |
| `create_custom_dimension` | 쓰기 | 맞춤 측정기준을 만듭니다 | `--allow-write`와 `analytics.edit`, 그리고 Editor 역할 |
| `create_key_event` | 쓰기 | 이벤트를 핵심 이벤트로 표시합니다 | `--allow-write`와 `analytics.edit`, 그리고 Marketer 또는 Editor 역할 |

- 쓰기 도구 세 개만 속성을 바꿉니다. 그 존재가 게이트를 낮추지 않습니다. 맞춤 측정기준 만들기는 여전히 요청에서 이름을 지어야 하고, `rules/safety-gates.md`의 명시적 승인 등급에 있는 동작은 MCP 도구가 아예 없어서 승인 뒤의 REST 호출로 남습니다.
- `run_funnel_report`는 감싼 메서드의 알파 단서를 그대로 집니다. 리포트를 반복 재현해야 하는 속성에서는 `eventName` 위의 `run_report`를 씁니다.
- `run_conversions_report`는 연결된 계정에만 Google Ads 비용·기여 행을 돌려줍니다. 연결되지 않은 속성의 빈 결과는 전환 발견 사항이 아닙니다.

## Read-only default and write tools

- 서버는 기본이 읽기 전용입니다. `ANALYTICS_MCP_ALLOW_WRITE` / `--allow-write`의 기본값은 `false`이고, 플래그는 "Enable tools that create or modify Google Analytics resources."로 설명됩니다.
- 연결된 서버의 도구 목록에 쓰기 도구가 없는 것은 기본 상태이지 설치가 깨진 것이 아닙니다. 도구가 없는 이유는 쓰기 모드가 꺼져 있다는 것이고, 서버에 그 도구가 없다는 것이 아닙니다.
- 쓰기 모드를 켜는 것은 그것이 필요한 실행의 결정입니다. 그것만으로는 쓰기가 승인되지 않습니다. 승인 등급이 동작마다 그대로 적용됩니다.
- 쓰기 모드가 켜진 상태에서 쓰기 도구를 부르면 자격 증명이 `analytics.edit`을 추가로 필요로 합니다. 쓰기 모드가 켜진 쓰기 도구의 `PERMISSION_DENIED`는 범위 또는 역할 발견 사항이고, 이 참조가 어느 쪽인지 밝힙니다.

## REST fallback

MCP 서버가 연결되지 않았을 때 같은 작업은 ADC 베어러 토큰으로 REST API를 씁니다.

```sh
curl -sS -H "Authorization: Bearer $(gcloud auth application-default print-access-token)" \
  "https://analyticsdata.googleapis.com/v1beta/properties/<property_id>:runReport" \
  -H "Content-Type: application/json" \
  -d '{"dateRanges":[{"startDate":"2026-10-01","endDate":"2026-10-31"}],"dimensions":[{"name":"sessionDefaultChannelGroup"}],"metrics":[{"name":"sessions"}],"limit":10,"returnPropertyQuota":true}'
```

- 대체 경로는 같은 메서드 표면과 같은 할당량입니다. MCP 서버는 두 번째 API가 아니라 감싸는 층입니다. 할당량 오류는 두 경로에서 같습니다.
- 토큰을 출력하지 않습니다. 위의 `$(gcloud auth application-default print-access-token)` 치환은 요청 안에서 평가되고 절대 되비추지 않습니다. 무언가를 보여야 하는 실행은 토큰을 썼다는 사실을 보여 주고 그 글자는 보여 주지 않습니다.
- 서버가 연결돼 있으면 MCP 읽기 도구를 먼저 씁니다. 속성과 계정 맥락을 함께 싣기 때문입니다. REST는 서버가 노출하지 않는 메서드가 필요할 때 씁니다. `checkCompatibility`, `getMetadata`, 쓰기 도구 세 개 밖의 쓰기가 그렇습니다.
- REST 경로도 같은 속성 접근 부여와 같은 API 활성화를 필요로 합니다. 대체 경로가 둘 중 하나를 우회하지 않습니다.

## Stop conditions

다음을 우회하지 말고 그 단계를 멈추고 보고합니다.

- 자격 증명이 없습니다. `GOOGLE_APPLICATION_CREDENTIALS`이 비어 있고 ADC 파일도 없습니다. 범위를 포함한 `gcloud auth application-default login` 명령을 그대로 밝히고 멈춥니다.
- 자격 증명은 있는데 속성이 보이지 않습니다. 빠진 속성 부여를 보고하고 실행이 기대한 속성 ID를 밝히고 멈춥니다. 계속하려고 속성이나 부여를 만들지 않습니다.
- 범위나 API가 없습니다. 범위 또는 `*.googleapis.com` 서비스와 그것이 막는 단계를 밝히고 멈춥니다. 오류가 풀리기를 바라며 같은 호출을 다시 돌리지 않습니다.
- MCP 쓰기 도구가 없습니다. 쓰기 모드가 꺼져 있고 그 동작에 `--allow-write`와 승인이 필요하다고 보고한 뒤 그 동작을 멈춥니다.
- 신원이 속성 역할 없는 서비스 계정입니다. 역할 공백을 이름으로 보고하고 멈춥니다.

액세스 토큰, 리프레시 토큰, 서비스 계정 키, Measurement Protocol 비밀값을 대화, 보고서, 커밋에 출력하지 않습니다. 값을 식별해야 하면 앞 4글자까지만 보여 주고 나머지는 가렸다고 밝힙니다.

## Sources

> Checked 2026-11-08.

| Claim | Source |
|---|---|
| `cloud-platform`과 `analytics.readonly`를 한 명령으로 받는 ADC 로그인과 GA UI의 속성 접근 부여 | <https://developers.google.com/analytics/devguides/reporting/data/v1/quickstart> |
| `analyticsdata.googleapis.com`과 `analyticsadmin.googleapis.com`을 모두 켜야 함 | <https://github.com/googleanalytics/google-analytics-mcp> |
| MCP 서버는 `pipx run analytics-mcp`로 설치하고 Apache-2.0, Python 3.10 이상이며 `GOOGLE_APPLICATION_CREDENTIALS`로 ADC를 받음 | <https://github.com/googleanalytics/google-analytics-mcp> |
| `analytics-mcp` 1.0.0은 2026-11-03, 1.1.0은 2026-11-06에 공개됐고 후자가 Admin 쓰기 도구와 `minute_ranges`를 더함 | <https://pypi.org/project/analytics-mcp/>, <https://api.github.com/repos/googleanalytics/google-analytics-mcp/releases> |
| 도구 열세 개: 읽기 열 개와 쓰기 `create_property_annotation`, `create_custom_dimension`, `create_key_event` | <https://github.com/googleanalytics/google-analytics-mcp> |
| 쓰기 모드는 `ANALYTICS_MCP_ALLOW_WRITE` / `--allow-write`로 기본 꺼져 있고 "Enable tools that create or modify Google Analytics resources"로 설명됨 | <https://github.com/googleanalytics/google-analytics-mcp> |
| 쓰기는 `analytics.edit`이 필요하고 맞춤 측정기준은 Editor, 핵심 이벤트는 Marketer 또는 Editor | <https://github.com/googleanalytics/google-analytics-mcp> |
| ADC 로그인의 서비스 계정 가장 변형 | <https://github.com/googleanalytics/google-analytics-mcp> |
| `GOOGLE_CLOUD_PROJECT`가 요청을 클라우드 프로젝트에 할당량으로 귀속 | <https://developers.google.com/analytics/devguides/reporting/data/v1/quotas> |
| `--transport http --stateless-http`와 메모리 상태를 쓰는 OAuth 2.1 경로의 멀티테넌트 전송 | <https://github.com/googleanalytics/google-analytics-mcp> |

### Evidence grade

ADC 명령과 그 범위, 두 API 서비스 이름, 설치 명령, 버전 날짜, 도구 열세 개의 이름과 읽기·쓰기 구분, 읽기 전용 기본값과 플래그, 속성 역할 요구, 가장과 멀티테넌트 옵션은 위 페이지를 2026-11-08에 읽은 `MEASURED`입니다. REST 대체 경로의 모양, 쓰기 도구의 존재가 승인 게이트를 낮추지 않는다는 규칙, 정지 조건은 이 패키지가 측정한 표면 위에 세운 `LOCAL` 정책입니다. MCP 호출의 토큰 비용과 할당량 동작은 별도 한도가 아니라 Data API 자체의 것이고, 읽은 출처 어디에도 도구별 비용은 없습니다.
