# Admin API Audit

속성을 Admin API로 읽는 `audit`·`configure` 실행, 또는 설정 하나를 바꾸는 실행에서 이 참조를 읽습니다. 고정된 읽기 순서, 각 읽기가 만드는 필드, 범위와 승인 등급이 붙은 쓰기 레시피, Admin API 안의 버전 경계를 소유합니다.

> 영어판: [`admin-api-audit.md`](admin-api-audit.md)

## Contents

- Scope split
- The fixed read order
- Write recipes
- Version boundaries
- Reading a write back

## Scope split

- 읽기는 `analytics.readonly` 또는 `analytics.edit`을 받습니다. 실수로 쓰지 못하도록 `analytics.readonly`를 씁니다.
- 쓰기는 `analytics.edit`만 받습니다. 메서드 페이지가 쓰기마다 밝힙니다. "Requires the following OAuth scope: `https://www.googleapis.com/auth/analytics.edit`."
- 속성 역할도 범위와 별개로 쓰기를 막습니다. 자격 증명이 가진 범위가 속성의 Editor를 주지는 않습니다. 역할 거부는 역할 거부로 보고하고 범위 누락으로 보고하지 않습니다.
- 아래 경로는 모두 `https://analyticsadmin.googleapis.com` 기준이고, 모든 호출이 목록의 첫 항목에 기대지 않고 속성 리소스 이름을 명시적으로 싣습니다.

## The fixed read order

이 순서로 읽고 요청이 앞 몇 단계만 필요로 하면 거기서 읽기를 멈춥니다. 순서가 가장 싸고 가장 넓은 것부터라, 점검은 불완전한 계정 그림 없이 일찍 끝날 수 있습니다.

| 단계 | 메서드 | 얻는 것 | 뒷받침하는 발견 사항 |
|---|---|---|---|
| 1 | `accountSummaries.list` | 자격 증명이 볼 수 있는 모든 계정과 속성, 속성 표시 이름과 `property` 리소스 이름 | 요청이 있다고 전제한 속성이 없음, 또는 두 속성이 같은 사이트를 서비스함 |
| 2 | `properties.get` | 업종, 시간대, 통화, `createTime`, 상위 계정(`parent`), 서비스 등급 | 모든 일간 경계를 옮기는 시간대, 또는 사이트 가격과 맞지 않는 통화 |
| 3 | `dataStreams.list` | 스트림마다 `type`, 웹 스트림이면 `webStreamData.measurementId`와 `defaultUri` | 페이지의 측정 ID가 다른 스트림 것이거나 `defaultUri`가 없음 |
| 4 | `dataStreams.getEnhancedMeasurementSettings`(v1alpha) | 스트림의 향상된 측정 스위치: `streamEnabled`, `pageChangesEnabled`, `scrollsEnabled`, `outboundClicksEnabled`, `siteSearchEnabled`, `videoEngagementEnabled`, `fileDownloadsEnabled`, `formInteractionsEnabled` | 자체 `page_view`도 보내는 SPA에서 기록 기반 페이지뷰(`pageChangesEnabled`)가 켜져 있음 |
| 5 | `customDimensions.list`, `customMetrics.list` | 정의마다 `parameterName`, 범위, `displayName`, `archived` 상태 | 정의 없이 수집되는 이벤트 매개변수, 또는 사이트가 보내지 않는 `customEvent:` 정의 |
| 6 | `keyEvents.list` | 핵심 이벤트마다 `eventName`과 `countingMethod` | 볼륨 없는 표시 이벤트, 또는 표시하지 않은 중요한 전환 |
| 7 | `getDataRetentionSettings` | `eventDataRetention`과 `resetUserDataOnNewActivity` | 1년 범위 질문인데 보존 기간이 2개월 기본값 |
| 8 | `getGoogleSignalsSettings`(v1alpha) | Google signals의 `state` | 인구통계·리마케팅 질문이 의존하는데 signals가 켜져 있거나 꺼져 있음 |
| 9 | 없음 - GA UI의 Admin > Data settings > Data filters에서 읽음 | 필터마다 이름, 유형, 상태(`Testing`, `Active`, `Inactive`)를 UI에서 읽은 그대로 옮겨 적음 | 실제 트래픽을 가리는 활성 내부 트래픽 필터, 또는 부분적 격차를 설명하는 테스트 필터 |
| 10 | `measurementProtocolSecrets.list` | 비밀값의 **이름과 표시 이름만** | 비밀값 없는 서버 측 전송, 또는 표시 이름이 보낸 쪽과 어긋난 비밀값 |

읽기 규칙:

- 10단계는 응답 모양이 아니라 정책입니다. `MeasurementProtocolSecret`에는 "Output only. The measurement protocol secret value."로 표시된 `secretValue` 필드가 실제로 있습니다. 그래서 각 비밀값에서 `name`과 `displayName`만 읽고, `secretValue`는 되비추거나 로그에 남기거나 출력하거나 저장하지 않습니다. 보고서에도, 대화에도, 커밋에도, 복사한 응답 발췌에도 넣지 않습니다. 값을 식별해야 하면 앞 4글자까지만 보여 주고 나머지는 가렸다고 밝힙니다.
- 한 단계에서 읽기가 실패하면 그 단계에서 정확한 오류와 함께 보고합니다. 단계를 건너뛰고 그 설정이 없는 것처럼 계속하지 않습니다. "읽지 못함"과 "설정되지 않음"은 다른 발견 사항입니다.
- 발견 사항마다 그것을 만든 필드를 인용합니다. 1단계는 `property` 리소스 이름, 3단계는 `webStreamData.measurementId`, 4단계는 v1alpha 향상된 측정 설정의 `pageChangesEnabled`, 5단계는 `archived` 식입니다. 9단계는 API 메서드가 없으므로 API 필드도 없습니다. UI 경로와 읽은 필터 행을 인용합니다. 필드가 없는 발견 사항은 짐작입니다.
- 4단계는 v1alpha 전용입니다. v1beta `dataStreams` 메서드 집합은 `create`, `get`, `list`, `patch`, `delete`이고 향상된 측정 메서드가 없으므로, v1beta로 부르면 404가 돌아옵니다. 그 404는 그 호출의 예상된 모양이지 스트림이 깨진 것이 아닙니다.

## Write recipes

아래 모든 행은 `analytics.edit` 범위를 달고 `rules/safety-gates.md` §1의 승인 등급 하나에 대응합니다. 등급은 모드가 아니라 동작에 속하므로, 이 중 하나를 원하는 읽기 전용 `audit`은 그 동작에 대해 `configure` 실행이 됩니다.

| 레시피 | 메서드와 본문 | 범위 | 승인 등급 |
|---|---|---|---|
| 속성 만들기 | `POST /v1beta/properties` | `analytics.edit` | 요청에서 이름 지음 |
| 웹 스트림 만들고 측정 ID 받기 | `POST /v1beta/properties/<property_id>/dataStreams` | `analytics.edit` | 요청에서 이름 지음 |
| 맞춤 측정기준·측정항목 만들기 | `POST /v1beta/properties/<property_id>/customDimensions`(또는 `customMetrics`) | `analytics.edit` | 요청에서 이름 지음 |
| 맞춤 측정기준·측정항목 보관 처리 | `POST /v1beta/properties/<property_id>/customDimensions/<id>:archive`(또는 `customMetrics`) | `analytics.edit` | 명시적 승인 |
| 핵심 이벤트 만들기 | `POST /v1beta/properties/<property_id>/keyEvents` | `analytics.edit` | 요청에서 이름 지음 |
| 핵심 이벤트 삭제 | `DELETE /v1beta/properties/<property_id>/keyEvents/<id>` | `analytics.edit` | 명시적 승인 |
| 보존 기간 낮추기 | `PATCH /v1beta/properties/<property_id>/dataRetentionSettings` | `analytics.edit` | 명시적 승인 |
| Measurement Protocol 비밀값 만들기 | `POST /v1beta/properties/<property_id>/dataStreams/<stream_id>/measurementProtocolSecrets` | `analytics.edit` | 요청에서 이름 지음 |
| Measurement Protocol 비밀값 삭제 | `DELETE /v1beta/properties/<property_id>/dataStreams/<stream_id>/measurementProtocolSecrets/<id>` | `analytics.edit` | 명시적 승인 |

레시피별 전문:

**속성.** `displayName`, `timeZone`, `currencyCode`, `parent`를 최소로 담은 `Property` 본문으로 `POST /v1beta/properties`를 보냅니다. 응답이 새 속성 리소스 이름입니다. 속성 만들기는 요청에서 이름을 지으므로 "새 상점용 속성 하나 추가해줘"는 덮고, "우리 분석이 엉망이야"는 덮지 않습니다.

**웹 스트림.** `type: WEB_DATA_STREAM`과 `webStreamData.defaultUri`로 `POST /v1beta/properties/<property_id>/dataStreams`를 보냅니다. 응답의 `webStreamData.measurementId`는 "Output only. Analytics Measurement ID. Example: `G-1A2BCD345E`"입니다. ID는 요청이 아니라 응답에서 받습니다. 호출 전에는 존재하지 않습니다.

**맞춤 측정기준·측정항목.** `parameterName`, `displayName`, `scope`(`EVENT` 또는 `USER`)로 `POST /v1beta/properties/<property_id>/customDimensions`를 보냅니다. `scope`는 만든 뒤 바꿀 수 없으므로, 잘못된 범위는 patch가 아니라 보관 처리 후 다시 만들어 고칩니다. 자리 한도도 그대로입니다. 사용자 범위 25개, 이벤트 범위 50개, 아이템 범위 10개이고, 삭제한 자리는 48시간 뒤에야 다시 씁니다.

**보관 처리.** `POST .../customDimensions/<id>:archive`는 정의를 은퇴시키고, 자리를 곧바로 비우지 않고, 과거 기록도 바꾸지 않습니다. 그 정의를 참조하던 리포트의 모양이 바뀌고 API에서 되돌릴 수 없으므로 명시적 승인입니다.

**핵심 이벤트.** `eventName`과 `countingMethod`(`ONCE_PER_EVENT` 또는 `ONCE_PER_SESSION`)로 `POST /v1beta/properties/<property_id>/keyEvents`를 보냅니다. `conversionEvents`는 폐기됐습니다. Admin API 색인이 "Deprecated: Use `CreateKeyEvent` instead."라고 적습니다. 새 레시피를 폐기된 표면 위에 만들지 않습니다.

**핵심 이벤트 삭제.** `DELETE .../keyEvents/<id>`는 명시적 승인입니다. 그 이벤트를 전환으로 세던 리포트가 그 시점부터 바뀌고, 다시 만들어도 표시는 복구되지 않습니다.

**보존 기간.** `eventDataRetention`(`TWO_MONTHS`, `FOURTEEN_MONTHS`, `TWENTY_SIX_MONTHS`, `THIRTY_EIGHT_MONTHS`, `FIFTY_MONTHS`)과, 14개월 이상 옵션에서는 `resetUserDataOnNewActivity`로 `PATCH /v1beta/properties/<property_id>/dataRetentionSettings`를 보냅니다. 보존 기간을 낮추는 것은 명시적 승인입니다. 삭제된 사용자 단위 데이터는 월 단위 주기로 사라지고, 나중에 값을 올려도 복구되지 않습니다.

**Measurement Protocol 비밀값.** `displayName`으로 `POST .../dataStreams/<stream_id>/measurementProtocolSecrets`를 보냅니다. 응답은 비밀값을 한 번 담고, 그 값은 서버 측 전용입니다. 표시 이름과 앞 4글자만 기록하고 값은 기록하지 않습니다. 삭제는 그 값을 쓰던 보낸 쪽이 멈추므로 명시적 승인입니다.

등급 표가 그대로 적지 않은 두 레시피의 처리:

- 비밀값 만들기는 `rules/safety-gates.md`의 진행 등급에도, 금지 등급에도 없습니다. 다른 만들기와 같은 요청-이름 규율을 따르고, 그 값은 절대 출력하지 않습니다.
- 비밀값 삭제는 같은 파일의 명시적 승인 등급에 이름으로 들어 있으므로, 깨지는 보낸 쪽과 함께 한 번 묻습니다.

## Version boundaries

| 표면 | 버전 | 비고 |
|---|---|---|
| `accountSummaries`, `properties`, `dataStreams`, `customDimensions`, `customMetrics`, `keyEvents`, `dataRetentionSettings`, `measurementProtocolSecrets` | v1beta | 이 참조가 딛는 표면. 여기서 `dataStreams`는 스트림 리소스만 뜻하며 `create`, `get`, `list`, `patch`, `delete`입니다 |
| `dataStreams.getEnhancedMeasurementSettings`, `updateEnhancedMeasurementSettings` | v1alpha 전용 | v1beta 등가물이 없고, v1beta 메서드 집합에 향상된 측정 멤버가 없어 v1beta 호출은 404 |
| `googleSignalsSettings`(`getGoogleSignalsSettings`, `updateGoogleSignalsSettings`) | v1alpha 전용 | v1beta 등가물이 없고, v1beta 호출은 실패 |
| `conversionEvents` | 폐기 | `keyEvents`가 대체. 새 레시피에 쓰지 않음 |
| `bigQueryLinks`, `audiences`, `calculatedMetrics`, `channelGroups`, `accessBindings`, `reportingDataAnnotations`, `submitUserDeletion` | v1alpha | 이 참조 범위 밖. 버전 오류를 제대로 진단하도록 이름만 적음 |

Google signals가 v1alpha라는 것은 8단계 읽기가 알파 경로를 쓰고 그 단서와 함께 보고된다는 뜻입니다. v1beta 경로의 404는 그 호출의 예상된 모양이지 속성이 깨진 것이 아닙니다. 4단계의 향상된 측정 읽기도 같습니다.

## Reading a write back

- 쓰기 뒤에 짝이 맞는 `get`을 호출하고 쓰기가 바꾼 필드를 인용합니다. 쓰기 메서드의 응답 본문은 read-back이 아닙니다.
- read-back의 `name`을 쓰기 전에 이름 지은 속성과 리소스에 대조합니다. 다른 사용자의 동시 변경은 이번 실행의 결과가 아닙니다.
- read-back은 설정을 증명하고 효과를 증명하지 않습니다. 새 핵심 이벤트, 보관 처리한 정의, 낮춘 보존 기간은 모두 변경 이후 처리되는 데이터에만 적용되고, read-back은 과거에 대해 아무것도 증명하지 않습니다.
- 배포된 데이터 필터는 적용에 24~36시간이 걸립니다. 필터에는 API 메서드가 없으므로, 변경 뒤 상태는 GA UI의 Admin > Data settings > Data filters에서 다시 읽고, UI가 `Active`를 보여도 데이터는 아직 이전 상태를 반영할 수 있습니다. 그 점을 명시적으로 적습니다.

## Sources

> Checked 2026-11-08.

| Claim | Source |
|---|---|
| 모든 Admin API 쓰기는 `analytics.edit`을 요구하고 읽기는 `analytics.readonly`를 받음 | <https://developers.google.com/analytics/devguides/config/admin/v1/rest/v1beta/properties.dataStreams/create> |
| `accountSummaries.list`가 호출자가 접근할 수 있는 모든 계정의 요약을 돌려줌 | <https://developers.google.com/analytics/devguides/config/admin/v1/rest> |
| 속성 만들기는 `POST /v1beta/properties` | <https://developers.google.com/analytics/devguides/config/admin/v1/rest/v1beta/properties/create> |
| 웹 데이터 스트림이 "Output only. Analytics Measurement ID"인 `webStreamData.measurementId`를 돌려줌 | <https://developers.google.com/analytics/devguides/config/admin/v1/rest/v1beta/properties.dataStreams> |
| `customDimensions`, `customMetrics`, `keyEvents`, `dataRetentionSettings`, `measurementProtocolSecrets`가 v1beta 표면이고 create·get·list·patch·archive·delete 동사를 가짐 | <https://developers.google.com/analytics/devguides/config/admin/v1/rest> |
| `dataStreams.getEnhancedMeasurementSettings`가 v1alpha 전용이고 `pageChangesEnabled`를 포함한 향상된 측정 스위치를 돌려줌 | <https://developers.google.com/analytics/devguides/config/admin/v1/rest/v1alpha/properties.dataStreams/getEnhancedMeasurementSettings> |
| `MeasurementProtocolSecret`이 "Output only. The measurement protocol secret value"인 `secretValue`를 가지며 `get`·`list`가 그 리소스를 돌려줌 | <https://developers.google.com/analytics/devguides/config/admin/v1/rest/v1beta/properties.dataStreams.measurementProtocolSecrets> |
| v1beta·v1alpha `properties` 리소스 색인에 `dataFilters` 리소스가 없으므로 데이터 필터는 GA UI의 Admin > Data settings > Data filters에서 읽음 | <https://developers.google.com/analytics/devguides/config/admin/v1/rest>, <https://analyticsadmin.googleapis.com/$discovery/rest?version=v1beta> |
| Google signals 설정은 v1alpha 전용 | <https://developers.google.com/analytics/devguides/config/admin/v1/rest> |
| `conversionEvents`는 `keyEvents`로 폐기됨("Deprecated: Use `CreateKeyEvent` instead") | <https://developers.google.com/analytics/devguides/config/admin/v1/rest> |
| 맞춤 측정기준 자리는 사용자 25개, 이벤트 50개, 아이템 10개이고 삭제 48시간 뒤에 풀림 | <https://support.google.com/analytics/answer/14240153> |
| 보존 기간을 낮추면 오래된 사용자 단위 데이터가 월 단위로 삭제되고 복구되지 않음 | <https://support.google.com/analytics/answer/7667196> |
| 데이터 필터 효과는 영구적이고 활성화에 24~36시간이 걸림 | <https://support.google.com/analytics/answer/10104470> |
| 속성 역할이 쓰기를 막음: 맞춤 측정기준은 Editor, 핵심 이벤트는 Marketer 또는 Editor | <https://github.com/googleanalytics/google-analytics-mcp> |

### Evidence grade

범위 구분, 메서드 경로, `webStreamData.measurementId` 필드, 버전 경계(향상된 측정 읽기가 v1alpha 전용이고 `dataFilters` 리소스가 없다는 점 포함), `MeasurementProtocolSecret`의 `secretValue` 필드, 폐기된 `conversionEvents` 표면, 자리 한도, 보존 기간 동작, 필터 적용 시간은 위 페이지를 2026-11-08에 읽은 `MEASURED`입니다. 열 단계 읽기 순서와 각 읽기를 발견 사항에 연결하는 표는 `LOCAL`입니다. 순서는 점검이 일찍 끝나도록 가장 넓은 것에서 가장 좁은 것으로 걷는 이 패키지의 설계입니다. 모든 쓰기의 승인 등급은 `rules/safety-gates.md`에서 가져왔고, 그 파일이 그대로 이름 짓지 않은 두 행(비밀값 만들기와 삭제)은 조용히 배정하지 않고 쓰는 자리에서 밝힙니다. 비밀값에서 `name`과 `displayName`만 읽는다는 규칙은 API가 실제로 돌려주는 필드 위에 세운 이 패키지의 정책이지 응답 모양에 대한 주장이 아닙니다.
