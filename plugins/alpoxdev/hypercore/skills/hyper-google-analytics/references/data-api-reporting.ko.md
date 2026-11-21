# Data API Reporting

`analyze` 실행에서 리포트 데이터로 질문에 답할 때 이 참조를 읽습니다. 메서드 선택, 요청 전에 도는 이름 점검, 흔한 질문의 요청 레시피, 행 상한, 할당량 예산, 모든 결과가 달아야 할 데이터 품질 표시를 소유합니다.

> 영어판: [`data-api-reporting.md`](data-api-reporting.md)

## Contents

- Method choice
- Names before tokens
- Request recipes
- Row limit and response shape
- Quota budget
- Data-quality flags
- Reporting rule

## Method choice

| 질문 형태 | 메서드 | 버전 |
|---|---|---|
| 날짜 범위 하나에 리포트 하나 | `properties.runReport` | v1beta |
| HTTP 호출 하나에 리포트 다섯 개까지 | `properties.batchRunReports` | v1beta |
| 피벗 표 하나, 또는 한 호출의 피벗 여러 개 | `properties.runPivotReport`, `properties.batchRunPivotReports` | v1beta |
| 지난 몇 분 | `properties.runRealtimeReport` | v1beta |
| 속성이 받는 측정기준·측정항목 이름 | `properties.getMetadata` | v1beta |
| 두 개 이상의 측정기준과 측정항목을 함께 물을 수 있는지 | `properties.checkCompatibility` | v1beta |
| 단계를 명시한 퍼널 | `properties.runFunnelReport` | v1alpha 전용 |

- `runFunnelReport`는 "베타에 들어가기 전에 문법과 기능에 대한 피드백을 모으려고 알파 안정성으로 도입한" 메서드입니다. v1beta 표면과 별개의 결정으로 다룹니다. 리포트를 반복 재현해야 하는 운영 속성에서는 `eventName` 위의 `runReport`로 퍼널을 만들고, 알파 메서드를 왜 버렸는지 보고서에 적습니다.
- `batchRunReports`가 아끼는 것은 왕복 횟수이지 할당량이 아닙니다. "배치의 각 리포트는 토큰과 `concurrentRequests` 할당량에 개별로 계상되므로", 다섯 개 배치는 리포트 다섯 개만큼의 토큰을 씁니다.
- 두 축 교차표에는 `runPivotReport`가 맞는 표면입니다. `runReport`에 `orderBys`를 거는 방식은 피벗을 할 수 없으므로 대체물이 아닙니다.

## Names before tokens

모든 요청은 할당량 토큰을 쓰고, 거부된 측정기준 이름도 토큰을 씁니다. 이름을 먼저 확정합니다.

1. 속성마다 실행마다 `getMetadata`를 한 번 호출합니다. `GET https://analyticsdata.googleapis.com/v1beta/properties/<property_id>/metadata`입니다. 돌려받은 측정기준·측정항목 이름을 실행 내내 보관하고 다시 묻지 않습니다.
2. 이번 실행에서 쓰지 않은 측정기준·측정항목 조합이면 `checkCompatibility`를 먼저 호출합니다. 리포트가 보낼 것과 같은 `dimensions`, `metrics` 배열로 `POST https://analyticsdata.googleapis.com/v1beta/properties/<property_id>:checkCompatibility`를 보냅니다. 맞지 않는 조합은 리포트 요청을 만들기 전에 정리됩니다.
3. GA4 UI의 표시 이름은 API 이름이 아닙니다. UI의 `Session default channel group`은 요청에서 `sessionDefaultChannelGroup`이고, 어느 표기를 그 속성이 받는지는 metadata 응답이 정합니다.
4. 맞춤 정의는 UI에서 입력한 이름이 아니라 접두사 문법을 씁니다.

| 정의 | 요청에서의 이름 |
|---|---|
| 이벤트 범위 맞춤 측정기준 | `customEvent:<parameter>` |
| 사용자 범위 맞춤 측정기준 | `customUser:<parameter>` |
| 이벤트 범위 맞춤 측정항목 | `customEvent:<metric>` |
| 평균으로 보고하는 이벤트 범위 맞춤 측정항목 | `averageCustomEvent:<metric>` |
| 이벤트 하나의 핵심 이벤트 비율 | `sessionKeyEventRate:<eventName>` |
| 맞춤 채널 그룹 | `customChannelGroup:<id>` |

5. `getMetadata`가 오류로 돌려준 이름은 물어본 이름 그대로 정의 누락으로 보고하고, 짐작한 표기로 다시 시도하지 않습니다.

## Request recipes

모든 본문은 ADC 베어러 토큰과 함께 `https://analyticsdata.googleapis.com/v1beta/properties/<property_id>:<method>`로 갑니다. 아래 본문은 모두 `returnPropertyQuota`를 켜서 응답이 요청 비용을 돌려주게 합니다.

### Traffic by channel

"이번 달 세션이 어디서 왔나"에 답합니다.

```json
{
  "dateRanges": [{"startDate": "2026-10-01", "endDate": "2026-10-31"}],
  "dimensions": [{"name": "sessionDefaultChannelGroup"}],
  "metrics": [
    {"name": "sessions"},
    {"name": "totalUsers"},
    {"name": "engagedSessions"},
    {"name": "keyEvents"}
  ],
  "orderBys": [{"metric": {"metricName": "sessions"}, "desc": true}],
  "limit": 25,
  "returnPropertyQuota": true
}
```

채널 질문에는 `sessionDefaultChannelGroup`이 답합니다. "그 채널 안의 어느 소스인가"는 `sessionSource`와 `sessionMedium`이 답하며, 첫 요청을 넓히는 것이 아니라 두 번째 요청입니다.

### Landing pages

"어느 진입 페이지가 참여 세션과 핵심 이벤트를 만들었나"에 답합니다.

```json
{
  "dateRanges": [{"startDate": "2026-10-01", "endDate": "2026-10-31"}],
  "dimensions": [{"name": "landingPage"}],
  "metrics": [
    {"name": "sessions"},
    {"name": "engagementRate"},
    {"name": "keyEvents"},
    {"name": "sessionKeyEventRate"}
  ],
  "orderBys": [{"metric": {"metricName": "sessions"}, "desc": true}],
  "limit": 50,
  "returnPropertyQuota": true
}
```

진입 페이지 질문에는 `pagePath`가 아니라 `landingPage`를 씁니다. `pagePath`는 세션 중간 조회를 포함해 페이지를 볼 때마다 세므로 다른 질문에 답하고 더 큰 수를 냅니다.

### Key event rates

"어느 이벤트가 전환되고 비율은 얼마인가"에 답합니다.

```json
{
  "dateRanges": [{"startDate": "2026-10-01", "endDate": "2026-10-31"}],
  "dimensions": [{"name": "eventName"}],
  "metrics": [
    {"name": "eventCount"},
    {"name": "keyEvents"},
    {"name": "sessionKeyEventRate"}
  ],
  "orderBys": [{"metric": {"metricName": "keyEvents"}, "desc": true}],
  "limit": 100,
  "returnPropertyQuota": true
}
```

이벤트 하나의 비율이 질문이면 `sessionKeyEventRate`에 이벤트 이름을 접미사로 붙입니다. `sessionKeyEventRate:purchase`입니다. 접미사 없는 측정항목은 속성 전체 비율을 돌려주므로 다른 수입니다.

### Ecommerce funnel

"구매 경로가 어디서 끊기나"에 답합니다.

```json
{
  "dateRanges": [{"startDate": "2026-10-01", "endDate": "2026-10-31"}],
  "dimensions": [{"name": "eventName"}],
  "metrics": [
    {"name": "eventCount"},
    {"name": "addToCarts"},
    {"name": "checkouts"},
    {"name": "ecommercePurchases"},
    {"name": "purchaseRevenue"}
  ],
  "dimensionFilter": {
    "filter": {
      "fieldName": "eventName",
      "inListFilter": {
        "values": ["view_item", "add_to_cart", "begin_checkout", "purchase"]
      }
    }
  },
  "limit": 10,
  "returnPropertyQuota": true
}
```

- 퍼널 단계는 필터에 넣은 이벤트 이름 네 개(`view_item`, `add_to_cart`, `begin_checkout`, `purchase`)입니다. 이벤트 범위 측정항목 `addToCarts`, `checkouts`, `ecommercePurchases`는 같은 이벤트의 속성 전체 집계라 모든 행에서 같은 값이 반복되므로 단계마다 읽지 않고 한 번만 읽습니다. 단계별 볼륨은 `eventCount`이며, "측정항목이 비었다"와 "이벤트가 아예 안 왔다"를 가르는 값입니다.
- `purchaseRevenue`와 `transactions`는 구매 이벤트가 `transaction_id`와 통화를 실을 때만 채워집니다. 마지막 단계에 `eventCount`는 있는데 `purchaseRevenue`가 0이면 퍼널 발견 사항이 아니라 매개변수 발견 사항입니다.
- `runFunnelReport` 위에 세운 퍼널은 v1alpha입니다. 위의 v1beta 등가물은 반복 재현이 되고, 단계마다 이벤트를 세며 사용자를 단계 사이에서 중복 제거하지 않는다는 것이 그 한계입니다.

### Realtime

"지금 도착하고 있나"에 답합니다.

```json
{
  "dimensions": [{"name": "eventName"}],
  "metrics": [{"name": "eventCount"}, {"name": "activeUsers"}],
  "limit": 20,
  "returnPropertyQuota": true
}
```

- 본문은 `:runRealtimeReport`로 가고 `dateRanges`를 받지 않습니다. 창은 지난 30분입니다.
- 실시간은 존재 확인입니다. 여기서 나온 수는 일간 합계가 아니고 카드의 행 수도 작게 제한되므로, 개수로 인용하지 않습니다.
- 실시간 데이터는 최종값이 아닙니다. 여기 보인 이벤트도 표준 보고서에서는 다르게 처리될 수 있습니다.

## Row limit and response shape

- "API는 얼마나 요청하든 요청당 최대 250,000행을 돌려줍니다." 기본 `limit`은 10,000입니다.
- `keepEmptyRows`는 기본값이 false이므로 모든 측정항목이 0인 행은 응답에서 빠집니다. 하루 볼륨이 0인 이벤트의 존재를 증명할 때처럼 0행 자체가 답일 때만 `"keepEmptyRows": true`를 켜고, 그 밖에는 기본값이 정직한 형태입니다.
- `rowCount`를 돌려받은 행 수와 대조합니다. `rowCount`가 행 목록보다 크면 답이 잘린 것이고, 보고서는 잘린 수를 밝힙니다.
- 응답은 `dimensionHeaders`, `metricHeaders`, `rows`, `rowCount`, `metadata`, `propertyQuota`를 담습니다. 행 값을 옮겨 적을 때는 헤더 순서를 인용합니다. 위치로 열을 잘못 읽는 것이 가장 흔한 전사 오류입니다.

## Quota budget

표준 속성의 코어 토큰 할당량입니다.

| 버킷 | 표준 속성 |
|---|---|
| 속성당 하루 토큰 | 200,000 |
| 속성당 시간당 토큰 | 40,000 |
| 프로젝트·속성당 시간당 토큰 | 14,000 |
| 동시 요청 | 10 |

- "API 요청 하나의 토큰 청구는 `tokensPerDay`, `tokensPerHour`, `tokensPerProjectPerHour`에서 동시에 차감되므로", 실행이 만들 수 있는 요청 수를 정하는 것은 일간 합계가 아니라 가장 작은 버킷입니다.
- 어느 버킷이든 고갈되면 `429 RESOURCE_EXHAUSTED`가 돌아옵니다. 오류는 그 버킷을 밝히므로 버킷을 보고하고 그 버킷에 쓰기를 멈춥니다. 재시도는 토큰을 만들지 않습니다.
- 일간 버킷은 PST 자정에, 시간당 버킷은 "한 시간 안에, 반드시 정시 경계는 아니게" 갱신됩니다. 시간당 버킷에 걸린 실행은 언제 재개할 수 있는지 기록합니다.
- `returnPropertyQuota: true`는 응답에 `propertyQuota`를 더해 `tokensPerDay`, `tokensPerHour`, `tokensPerProjectPerHour`, `concurrentRequests`, `serverErrorsPerProjectPerHour`, `potentiallyThresholdedRequestsPerHour`의 남은 값을 돌려줍니다. `analyze` 실행의 모든 요청에 켜고, `429`를 받은 뒤가 아니라 시간당 버킷이 떨어지기 전에 멈춥니다.
- 임계값 적용에는 자체 예산이 있습니다. 시간당 임계값 적용 가능 요청이 120건입니다. 인구통계나 잠재고객 측정기준을 쓰는 리포트가 여기서 씁니다.
- `GOOGLE_CLOUD_PROJECT`가 요청을 클라우드 프로젝트에 귀속시키므로, 두 프로젝트가 속성은 공유하면서 프로젝트별 버킷은 공유하지 않을 수 있습니다.

## Data-quality flags

| 표시 | 나타나는 곳 | 뜻 | 보고서가 쓰는 문장 |
|---|---|---|---|
| 샘플링 | `metadata.samplingMetadatas` | 응답이 전체 데이터가 아니라 표본으로 계산한 추정값 | "샘플링됨 - 정확한 수가 아닌 추정값" |
| `(other)` 합산 | `metadata.dataLossFromOtherRow` | 하루 고유값 500개를 넘는 카디널리티가 `(other)` 한 행으로 묶임 | "`(other)` 행 포함. 이름 붙은 값의 합이 총계와 다름" |
| 임계값 적용 | 임계값 적용 가능 요청, 그리고 인구통계·잠재고객 측정기준 `userAgeBracket`, `userGender`, `brandingInterest`, `audienceId`, `audienceName` | 신원 보호를 위해 행을 감추거나 합산하므로 작은 세그먼트가 0으로 보일 수 있음 | "임계값 적용됨 - 빠진 행은 트래픽 0의 증거가 아님" |
| 추정 고유 수 | `activeUsers` 같은 고유 수 측정항목 | API가 "HyperLogLog++(HLL++) 알고리즘으로 고유 수를 추정" | "추정 고유 수. 두 리포트가 조금 다를 수 있음" |

- 필터는 `(other)` 합산 뒤에 적용되므로 `dimensionFilter`는 `(other)` 안을 보지 못합니다. `dataLossFromOtherRow`가 참일 때 필터를 건 리포트 합계가 필터 없는 합계보다 작은 것은 정상이고, 필터가 깨진 것이 아닙니다.
- 읽을 필드는 `dataLossFromOtherRow`입니다. 눈에 보이는 증상은 측정기준 값이 문자 그대로 `(other)`인 행입니다.
- 임계값 적용 결과와 실제로 빈 세그먼트는 행에서 똑같이 보입니다. 하나를 고르지 말고 응답이 뒷받침하는 쪽을 밝힙니다.

## Reporting rule

보고서의 모든 수는 다음 네 가지를 달고, 못 달면 보고하지 않습니다.

1. 두 날짜와, 범위가 날짜 경계를 넘을 때는 속성의 시간대를 포함한 날짜 범위
2. 요청이 간 속성 ID
3. 메서드, 측정기준, 측정항목, 필터, 상한을 포함한 요청 형태
4. 위 표에서 이름을 가져온, 응답에 있는 모든 데이터 품질 표시

임계값이 적용됐거나 샘플링됐거나 `(other)`의 영향을 받은 결과는 그렇게 표시하고 정확한 값으로 제시하지 않습니다. 질문이 이벤트 단위 행을 필요로 하거나 임계값·샘플링에 반복해서 걸리면, 모든 줄에 단서를 다는 대신 BigQuery 내보내기 경로를 정직한 답으로 제시합니다.

## Sources

> Checked 2026-11-08.

| Claim | Source |
|---|---|
| v1beta 메서드 표면: `runReport`, `batchRunReports`, `runPivotReport`, `batchRunPivotReports`, `runRealtimeReport`, `getMetadata`, `checkCompatibility` | <https://developers.google.com/analytics/devguides/reporting/data/v1/rest> |
| `runFunnelReport`는 v1alpha 전용이며 알파 안정성으로 도입됨 | <https://developers.google.com/analytics/devguides/reporting/data/v1/rest/v1alpha/properties/runFunnelReport> |
| 요청당 최대 250,000행, 기본 10,000행, `keepEmptyRows` 기본값 false | <https://developers.google.com/analytics/devguides/reporting/data/v1/rest/v1beta/properties/runReport> |
| 속성당 하루 200,000토큰, 시간당 40,000, 프로젝트·속성당 시간당 14,000, 동시 요청 10, `429 RESOURCE_EXHAUSTED`, PST 자정 일간 갱신, 한 시간 안의 시간당 갱신 | <https://developers.google.com/analytics/devguides/reporting/data/v1/quotas> |
| 요청 하나의 토큰 청구가 세 버킷에서 동시에 차감되고, 배치 리포트도 토큰과 동시 요청 할당량에 개별로 계상됨 | <https://developers.google.com/analytics/devguides/reporting/data/v1/quotas> |
| `returnPropertyQuota`가 남은 토큰, 동시 요청, 서버 오류, 임계값 적용 가능 요청을 보고함 | <https://developers.google.com/analytics/devguides/reporting/data/v1/quotas> |
| 시간당 임계값 적용 가능 요청 120건과 임계값이 적용되는 측정기준 다섯 개 | <https://developers.google.com/analytics/devguides/reporting/data/v1/quotas> |
| `samplingMetadatas`, `dataLossFromOtherRow`, 하루 고유값 500개 초과 시 `(other)` 합산, 합산 뒤 필터 적용, 고유 수 HLL++ 추정 | <https://developers.google.com/analytics/devguides/reporting/data/v1/reporting-data-expectations> |
| `customEvent:<param>`, `customUser:<param>`, `averageCustomEvent:<metric>`, `sessionKeyEventRate:<eventName>`, `customChannelGroup:<id>` 표기 | <https://developers.google.com/analytics/devguides/reporting/data/v1/api-schema> |
| `sessionDefaultChannelGroup`, `landingPage`, `sessionKeyEventRate`를 포함한 측정기준·측정항목 API 이름 | <https://developers.google.com/analytics/devguides/reporting/data/v1/api-schema> |

### Evidence grade

메서드 목록과 버전, 250,000행 상한과 10,000행 기본값, 모든 할당량 수치, 할당량 필드 이름, 데이터 품질 표시 네 가지와 그 응답 필드, 맞춤 정의 표기 문법은 위 페이지를 2026-11-08에 읽은 `MEASURED`입니다. 요청 레시피 다섯 개, 알파 메서드 대신 `eventName` 위의 v1beta로 퍼널을 만드는 선택, 진입 페이지 질문에 `pagePath`가 아니라 `landingPage`가 답한다는 규칙, 네 항목 보고 규칙은 이 패키지가 측정 사실을 조합한 `LOCAL`입니다. 요청 하나의 토큰 비용은 읽은 출처에 공개된 수치가 없으므로, 이 참조는 비용을 예측하지 않고 `propertyQuota`의 남은 값으로 예산을 잡습니다.
