# API와 분석

Tag Manager API를 호출하기 전, `analyze`에서, 컨테이너 내보내기를 읽을 때 이 파일을 읽습니다. `volatile` 표시가 붙은 사실은 API와 함께 바뀌므로 살아 있는 검색 문서(`https://tagmanager.googleapis.com/$discovery/rest?version=v2`)가 이 스냅숏보다 우선합니다.

## Contents

- 1. Tag Manager API v2
- 2. Write pipeline
- 3. Export format and enum casing
- 4. Tools and MCP servers
- 5. Analysis
- Sources

## 1. Tag Manager API v2

기준 URL은 `https://tagmanager.googleapis.com/tagmanager/v2/`입니다. 리소스 트리(폴더, 템플릿, 기본 변수는 작업공간 범위(scope)이고 사용자 권한은 계정 범위(scope)입니다):

```text
accounts                                   list, get, update
accounts.user_permissions                  list, get, create, update, delete
accounts.containers                        list, get, create, update, delete, lookup, snippet, move_tag_id, combine (deprecated)
accounts.containers.destinations           list, get, link
accounts.containers.environments           list, get, create, update, delete, reauthorize
accounts.containers.versions               get, live, update, delete, publish, set_latest, undelete
accounts.containers.version_headers        list, latest
accounts.containers.workspaces             list, get, create, update, delete, bulk_update, getStatus, quick_preview, sync, resolve_conflict, create_version
accounts.containers.workspaces.{tags,triggers,variables,folders,templates,built_in_variables,clients,zones,transformations,gtag_config}
```

유용한 호출: `GET .../containers/{c}:snippet`(설치 스니펫), `GET .../versions:live`(게시된 버전), `GET .../version_headers:latest`, `GET /tagmanager/v2/accounts/containers:lookup?tagId=GTM-XXXXXXX`.

OAuth 범위(scope)는 정확히 일곱 개이며 `https://www.googleapis.com/auth/` 접두사를 붙입니다.

| Scope | Allows | Use for |
|---|---|---|
| `tagmanager.readonly` | 컨테이너와 그 항목 보기 | `audit`, `analyze`, `verify` |
| `tagmanager.edit.containers` | 컨테이너와 항목 관리, 버전과 게시는 불가 | `configure` 초안, `versions.set_latest` |
| `tagmanager.edit.containerversions` | 버전 관리, `create_version`, `quick_preview` | 버전 생성(요청에 있을 때) |
| `tagmanager.publish` | 게시, `environments.reauthorize` | 승인 등급 전용 |
| `tagmanager.delete.containers` | 컨테이너와 작업공간 삭제 | 승인 등급 전용 |
| `tagmanager.manage.users` | 사용자 권한 | 승인 등급 전용 |
| `tagmanager.manage.accounts` | 계정 설정 | 승인 등급 전용 |

단계에 필요한 가장 좁은 조합을 요청합니다. 일부 제3자 서버는 기본으로 일곱 개를 모두 요청하므로, 사용자가 그런 서버를 고르면 그 사실을 밝힙니다.

할당량(`volatile`): 프로젝트당 하루 10,000 요청, 프로젝트당 초당 0.25 쿼리이며 100초에 25 요청으로 적용됩니다. 초과하면 HTTP 403을 응답합니다. 요청을 4초 이상 간격으로 보내고, `userRateLimitExceeded`나 `quotaExceeded`에서는 n = 0..5에 따라 `(2^n) + random(0..1000) ms`만큼 물러납니다. API로 큰 컨테이너를 점검하면 느리므로 항목을 하나씩 나열하기보다 `versions.live`나 내보내기를 한 번 읽는 편이 좋습니다.

서비스 계정은 컨테이너 권한(`read`, `edit`, `approve`, `publish`)을 가진 Tag Manager 사용자로 추가해야 합니다. 키만 만들면 아무 권한도 없습니다. 클라이언트 라이브러리: Python은 `googleapiclient.discovery.build('tagmanager', 'v2', credentials=...)`, Node는 `@googleapis/tagmanager`입니다. 둘 다 snake_case 메서드 이름(`create_version`, `bulk_update`, `quick_preview`)을 씁니다. 공식 CLI는 없습니다.

## 2. Write Pipeline

```text
GET   .../workspaces                         find or create a dedicated workspace (standard accounts allow 3 at once)
POST  .../workspaces/{w}/bulk_update         atomic multi-item change; new IDs "new_1", "new_2"
GET   .../workspaces/{w}/status              workspaceChange[] and mergeConflict[]
POST  .../workspaces/{w}:quick_preview       compile check; empty body; read compilerError
POST  .../workspaces/{w}:create_version      {name, notes}; deletes the workspace
POST  .../versions/{v}:publish?fingerprint=  approval tier
```

- `update`는 전체 교체입니다. `get`으로 읽은 항목 전체를 보내고 `?fingerprint=<value>`를 쿼리 매개변수로 붙입니다. fingerprint는 API에서 선택 사항이고, 빼면 마지막 작성자가 조용히 이깁니다. 오래된 fingerprint는 실패하므로 다시 읽고 변경을 다시 하며, 같은 본문을 다시 보내지 않습니다.
- `compilerError: true`는 `quick_preview`, `create_version`, `publish`에서 HTTP 200과 함께 돌아옵니다. 그러면 멈춥니다.
- `bulk_update` 응답에는 삭제된 항목과 시스템이 갱신한 항목이 빠집니다. 결과를 알려면 작업공간을 다시 읽습니다.
- `create_version`은 원본 작업공간을 삭제합니다. 다른 사람의 편집이 있는 Default Workspace에서는 절대 실행하지 않습니다.
- API에는 확인 절차도 되돌리기도 없습니다. 롤백은 이전 버전을 게시하는 것입니다.
- API에 접근할 수 없으면 `.hyper/gtm/<slug>/import.json`에 가져오기 JSON(§3 형태)을 쓰고, 새 작업공간에 **Merge**로 가져오라고 사용자에게 알립니다.

## 3. Export Format and Enum Casing

Admin > Export Container는 다음을 만듭니다.

```json
{"exportFormatVersion": 2,
 "containerVersion": {
   "container": {"publicId": "GTM-XXXXXXX", "usageContext": ["WEB"]},
   "tag": [{"tagId": "101", "name": "GA4 - Event - purchase", "type": "gaawe",
            "parameter": [{"type": "TEMPLATE", "key": "eventName", "value": "purchase"}],
            "firingTriggerId": ["201"], "tagFiringOption": "ONCE_PER_EVENT",
            "consentSettings": {"consentStatus": "NEEDED",
              "consentType": {"type": "LIST", "list": [{"type": "TEMPLATE", "value": "analytics_storage"}]}}}],
   "trigger": [{"triggerId": "201", "name": "CE - purchase", "type": "CUSTOM_EVENT",
                "customEventFilter": [{"type": "EQUALS", "parameter": [
                  {"type": "TEMPLATE", "key": "arg0", "value": "{{_event}}"},
                  {"type": "TEMPLATE", "key": "arg1", "value": "purchase"}]}]}],
   "variable": [], "folder": [], "customTemplate": [], "builtInVariable": []
 }}
```

- enum은 두 가지 표기로 나타납니다. 내보내기와 실제 페이로드는 `CUSTOM_EVENT`, `HISTORY_CHANGE`, `CONSENT_INIT`, `NOT_SET`, `TEMPLATE`, `EQUALS`를 쓰고 검색 문서는 `customEvent`, `historyChange`, `consentInit`, `notSet`을 보여 줍니다. 밑줄을 빼고 대소문자를 무시해 비교합니다. `scripts/gtm-container-audit.sh`가 그렇게 합니다.
- 태그 유형은 양쪽 모두 소문자입니다. `googtag`(Google 태그), `gaawe`(GA4 이벤트), `html`(Custom HTML), `ua`(Universal Analytics, 폐기), `awct`(Ads 전환), `awud`(Ads 사용자 제공 데이터), `gclidw`(Conversion Linker), `sp`(Ads 리마케팅), `flc`(Floodlight), `cvt_<id>`(사용자 템플릿)입니다. `gaawc`(옛 GA4 구성 태그)는 2023-09-05에 `googtag`가 되었으므로 만들지 않습니다.
- 변수 유형: `v`(Data Layer 변수), `c`(상수), `jsm`(Custom JavaScript), `u`(URL), `k`(자사 쿠키), `smm`(조회 테이블), `remm`(정규식 테이블).
- 기본 트리거 ID: `2147479553` All Pages, `2147479572` Consent Initialization - All Pages, `2147479573` Initialization - All Pages.
- 변수 참조는 문자열 안에 `{{Name}}` 형태로 나타납니다.
- 내보내기에는 Custom HTML 안에 고객 ID나 토큰이 있을 수 있습니다. 발견 사항에 필요한 것만 인용합니다.

## 4. Tools and MCP Servers

- 2026-11-08 기준 Google은 Tag Manager MCP 서버도 Tag Manager 에이전트 스킬도 공개하지 않았습니다(`volatile`). 공식 `googleanalytics/google-analytics-mcp` 서버는 GA4만 다루며(읽기 도구와 제한된 쓰기 세 개) `analyze`에서 GA4 데이터를 읽는 공식 수단입니다.
- `stape-io/google-tag-manager-mcp-server`(Apache-2.0)는 가장 많이 쓰이는 커뮤니티 서버입니다. 리소스마다 `action` 필드가 있는 도구 하나를 제공하고 `bulkUpdate`, `quickPreview`, `createVersion`, fingerprint가 필요한 업데이트를 지원합니다. 호스팅 엔드포인트는 컨테이너 구성을 제3자를 거쳐 전달하고 로컬 CLI는 그렇지 않습니다. 이 서버는 일곱 범위(scope)를 모두 요청합니다. 로컬 CLI와 최소 권한을 권하고, 그 쓰기 도구는 `rules/safety-gates.md` 아래에서 다룹니다.
- MCP 서버나 API 자격 증명이 있으면 먼저 읽기에 쓰고, 둘 다 없으면 사용자에게 컨테이너 내보내기(Admin > Export Container)를 요청해 파일로 작업합니다.

## 5. Analysis

### Container health

`scripts/gtm-container-audit.sh --file <export.json>`을 실행합니다. 개수, 태그 유형, 다음 발견 사항을 보고합니다.

| Code | Rule |
|---|---|
| `UA_TAG` (error) | 태그 유형 `ua` |
| `NO_FIRING_TRIGGER` (warn) | `firingTriggerId`가 없고 시퀀싱 설정이나 정리 태그도 아님 |
| `DUPLICATE_GOOGLE_TAG` (warn) | 같은 `tagId`를 가진 `googtag` 태그 둘 |
| `CUSTOM_HTML_DOCUMENT_WRITE` (warn) | `document.write`를 호출하는 Custom HTML |
| `HISTORY_CHANGE_PAGEVIEW` (warn) | Google 태그 옆에 사용 중인 History Change 트리거 |
| `CUSTOM_HTML`, `PAUSED_TAG`, `CONSENT_NOT_SET`, `UNUSED_TRIGGER`, `UNUSED_VARIABLE`, `NO_CONSENT_INIT` (info) | 이름 그대로 |

해당할 때 직접 더합니다. 상수 변수 대신 하드코딩한 `G-`, `AW-`, `GTM-` ID, All Pages에 붙은 전환 태그, Custom JavaScript 변수 개수(CSP 위험), 이름과 폴더 정리 상태(`references/container-design.md` §7), 작업공간 3개 제한 대비 사용량, 비어 있는 버전 이름입니다. 컨테이너 크기는 API가 없으므로 Versions 페이지의 Size 표시를 읽습니다(300 KB의 70%를 넘으면 조치).

### Plan versus container

이벤트 계획의 행마다 있음, 없음, 다름(트리거, 매개변수, 동의)으로 적고, 컨테이너 태그마다 계획에 있음 또는 계획에 없음으로 적습니다.

### Destination data

- GA4 실시간: `POST https://analyticsdata.googleapis.com/v1beta/properties/{id}:runRealtimeReport`에 차원 `eventName`, 지표 `eventCount`를 보내고 범위(scope)는 `analytics.readonly`입니다. 창은 최근 30분(GA4 360은 60분)입니다. 할당량(`volatile`): 속성당 하루 실시간 토큰 200,000개, 동시 요청 10개입니다. 실시간은 이벤트 이름을 보여 주며 등록하지 않은 매개변수는 보여 주지 않습니다.
- GA4 기록: 계획의 이벤트를 `date`별 `eventName`으로 `runReport`에서 조회합니다. 표준 데이터는 24~48시간 늦고, `samplingMetadatas`, 임계값 적용, `(other)` 행을 수치와 함께 보고합니다.
- Tag coverage(Google tag > Admin > Tools > Tag coverage)에는 API가 없습니다. 최대 10,000페이지, 30일 활동, 24시간 지연, 리디렉트·후행 슬래시·URL 대소문자·낮은 트래픽으로 인한 잘못된 "not tagged"가 있습니다. 사용자가 제공하면 그 CSV를 씁니다.
- 모든 수치 옆에 날짜 범위, 속성, 데이터 지연을 밝힙니다.

## Sources

> Checked 2026-11-08.

| Claim | Source |
|---|---|
| 리소스 트리, 메서드, `compilerError`, `newWorkspacePath` | <https://developers.google.com/tag-platform/tag-manager/api/reference/rest>, <https://tagmanager.googleapis.com/$discovery/rest?version=v2> |
| OAuth 범위 | <https://developers.google.com/tag-platform/tag-manager/api/v2/authorization> |
| 할당량과 백오프 | <https://developers.google.com/tag-platform/tag-manager/api/v2/limits-quotas>, <https://developers.google.com/tag-platform/tag-manager/api/v2/errors> |
| `bulk_update`, `quick_preview`, `create_version`, `publish`의 fingerprint | <https://developers.google.com/tag-platform/tag-manager/api/reference/rest/v2/accounts.containers.workspaces/bulk_update>, <https://developers.google.com/tag-platform/tag-manager/api/reference/rest/v2/accounts.containers.versions/publish> |
| `combine` 폐기 | <https://developers.google.com/tag-platform/tag-manager/api/reference/rest/v2/accounts.containers/combine> |
| 클라이언트 라이브러리 | <https://developers.google.com/tag-platform/tag-manager/api/v2/libraries> |
| 내보내기 형태와 대문자 enum | <https://developers.google.com/tag-platform/tag-manager/api/reference/rest/v2/accounts.containers.versions>의 `ContainerVersion` 스키마. 대문자 enum은 2026-11-08 GitHub에 공개된 컨테이너 내보내기 2개에서 관찰 |
| GA4 구성 태그가 Google 태그가 된 변경 | <https://support.google.com/tagmanager/answer/4620708> |
| 작업공간 제한, 가져오기와 내보내기 | <https://support.google.com/tagmanager/answer/7059647>, <https://support.google.com/tagmanager/answer/6106997> |
| GA4 MCP 서버 도구 목록 | <https://github.com/googleanalytics/google-analytics-mcp> |
| 커뮤니티 GTM MCP 서버 | <https://github.com/stape-io/google-tag-manager-mcp-server> |
| GA4 실시간 보고서와 할당량 | <https://developers.google.com/analytics/devguides/reporting/data/v1/realtime-basics>, <https://developers.google.com/analytics/devguides/reporting/data/v1/quotas> |
| Tag coverage | <https://support.google.com/tagmanager/answer/12270036> |

### Evidence grade

2026-11-08에 읽은 Google 공식 API 문서와 살아 있는 검색 문서이며, 내보내기 예와 커뮤니티 서버는 같은 날 공개 저장소에서 읽었습니다. 태그와 변수 유형 코드는 실제 내보내기에서 얻었고 Google의 산문 문서에는 없습니다.
