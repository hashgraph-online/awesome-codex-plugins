# BigQuery Export

질문이 이벤트 단위 행을 필요로 하거나, 리포트 행·할당량 한도를 넘거나, 임계값 적용·샘플링에 반복해서 걸릴 때 이 참조를 읽습니다. 내보내기 한도, 일시 중지된 내보내기가 하는 일, 데이터셋과 표 이름, 지연 도착 데이터 창, 내보내기를 설정하지 않고 권고하는 규칙을 소유합니다.

> 영어판: [`bigquery-export.md`](bigquery-export.md)

## Contents

- When to recommend it
- The daily limit
- Dataset and table names
- The late-data window
- What the export does not give
- Recommending, not setting up

## When to recommend it

질문이 다음 세 형태 중 하나에 들면 BigQuery 내보내기를 권고하고, 설정하지는 않습니다.

1. **이벤트 단위 행.** 개별 이벤트의 매개변수, 한 세션 안 이벤트 사이의 조인, 집계가 아닌 사용자 경로가 답에 필요합니다. Data API 리포트는 집계를 돌려주고, 어떤 요청 형태도 그것을 행으로 바꾸지 않습니다.
2. **행 또는 할당량 한도.** 결과가 요청 하나가 돌려줄 수 있는 250,000행을 넘거나, 분석이 속성의 Data API 버킷을 다 쓸 상황입니다. 가장 작은 버킷은 프로젝트·속성당 시간당 14,000토큰입니다.
3. **반복되는 임계값 적용이나 샘플링.** 같은 질문이 시도할 때마다 `dataLossFromOtherRow`나 `samplingMetadatas` 항목을 돌려주거나, 인구통계 질문이 필요로 하는 행이 감춰집니다. 모든 줄에 단서를 다는 것은 답이 아닙니다.

권고마다 내보내기, 그 한도, 켜는 데 필요한 것을 밝힙니다. 켜는 일은 이 실행 범위 밖의 속성 수준 변경입니다. 이유가 붙은 권고이지, 내보내기가 이미 있다는 주장이 아닙니다.

## The daily limit

- "Standard properties have a daily BigQuery Export limit of 1 million events." 한도는 표나 쿼리가 아니라 속성별·일별입니다.
- 넘으면 내보내기가 일시 중지됩니다. "the daily BigQuery export will be paused and previous days' exports will not be reprocessed." 중지된 날은 나중에 채워지는 지연이 아니라 내보내기의 영구한 구멍입니다.
- 내보내기는 볼륨 급증의 안전망이 아닙니다. 실행이 한도에 가까운 날을 보면 중지되기 전에 말합니다. 중지된 뒤에는 되메울 것이 없습니다.
- Analytics 360은 자체의 훨씬 높은 상한을 갖고 Fresh Daily는 360 전용 옵션입니다. 둘 다 표준 속성에 해당하지 않으므로 100만 이벤트 한도를 없애는 것처럼 인용하지 않습니다.
- 스트리밍 내보내기는 최선 노력이고 "may contain data gaps"이며 신규 사용자 트래픽 소스 필드를 뺍니다. 당일 내부만 보는 질문은 그 구멍을 물려받습니다.

## Dataset and table names

| 항목 | 이름 |
|---|---|
| 데이터셋 | `analytics_<property_id>` |
| 일간 내보내기 표 | `events_YYYYMMDD` |
| 스트리밍(당일) 표 | `events_intraday_YYYYMMDD` |

- `<property_id>`는 숫자 속성 ID, 즉 `properties/<number>`의 숫자이고 `G-` 측정 ID가 아닙니다. 측정 ID로 지은 데이터셋은 잘못된 데이터셋 발견 사항입니다.
- `events_20261001` 일간 표는 UTC가 아니라 속성 시간대 기준 10월 1일 이벤트를 담습니다.
- 당일 표는 교체됩니다. 어떤 날짜의 일간 표가 완성되면 그 날짜의 당일 표는 삭제됩니다. `events_intraday_20261001`에 고정한 쿼리는 다음 날 동작을 멈추고, 당일 표가 아직 있는 동안 같은 날짜로 두 표를 합치면 이중 계상됩니다.
- 두 표는 담는 필드의 스키마를 공유하고, `traffic_source`와 `user_ltv`는 당일 표에 없습니다.
- `event_params`, `item_params`, `user_properties`는 `key`와 `value.string_value` / `value.int_value` / `value.double_value`를 가진 반복 RECORD이므로, 매개변수를 읽는 일은 열 참조가 아니라 unnest입니다.

## The late-data window

공식 페이지 둘이 어긋나고, 이 참조는 조용히 하나를 고르지 않고 둘 다 기록합니다.

| 페이지 | 적힌 창 |
|---|---|
| BigQuery Export 스키마 페이지 | 일간 표가 이벤트 날짜 뒤 "up to 3 days"까지 갱신됨 |
| BigQuery Export 지원 페이지 | "up to 2 calendar days, plus today" |

- 이 패키지가 기록하는 값은 보수적 해석인 **72시간**입니다. 72시간 안의 날짜에 대한 질문은 그 불확실성을 밝히고 답합니다. 두 정책이 셋째 날 포함 여부에서 다르기 때문입니다.
- 창이 닫히기 전에 읽은 일간 수는 잠정값입니다. 표가 아직 지연 이벤트를 받을 수 있고 최종 수가 오를 수 있다고 밝힙니다.
- 창이 지난 뒤 도착한 이벤트는 내보내기에 아예 없으므로, 내보내기 합계가 같은 날짜의 Data API 합계보다 낮을 수 있습니다. 그 차이는 처리 차이이지 한쪽 표면이 틀렸다는 증거가 아닙니다.
- 이 수치에 기대기 전에 두 페이지를 다시 읽습니다. 어느 한쪽이 바뀌면 보수적 값이 움직입니다.

## What the export does not give

- 이 패키지는 SQL을 쓰지 않습니다. 내보내기는 질문의 표면으로 권고되고, 쿼리를 쓰는 일은 쓰기를 요청받은 실행의 몫입니다.
- 링크 켜기, 데이터셋 위치 선택, BigQuery 역할 부여는 속성과 클라우드 프로젝트 변경입니다. 정확한 단계와 함께 제안하고 `analyze`의 일부로 실행하지 않습니다.
- 내보내기가 수집 점검을 대체하지 않습니다. 행이 있는 표는 이벤트가 내보내기에 도달했다는 것을 증명하고, 실제 페이지의 태그가 오늘 맞다는 것을 증명하지 않습니다.
- 내보내기는 수집된 것을 담습니다. 사이트가 보낸 적 없는 매개변수는 리포트에서 빠진 것과 똑같이 `event_params`에서도 빠집니다. 내보내기가 수집 격차를 메우지 않습니다.

## Recommending, not setting up

| 상황 | 실행이 하는 일 |
|---|---|
| 이벤트 단위 행이 필요함 | 내보내기, 데이터셋과 표 이름, 답에 이벤트 단위 쿼리가 필요하다는 점을 밝히고 아무것도 켜지 않음 |
| 리포트가 행 상한이나 할당량 버킷에 걸림 | 내보내기를 권고하고 측정한 한도나 고갈된 버킷을 밝힘 |
| 임계값 적용이나 샘플링이 반복됨 | 내보내기를 권고하고 반복된 표시를 밝히며 내보내기에 임계값 적용이 없다는 점을 밝힘 |
| 요청이 "BigQuery 연결해줘"라고 함 | 속성의 `configure` 동작에 클라우드 프로젝트 변경이 더해진 일. 필요한 승인을 밝히고 멈춤 |

보고서의 권고는 한도, 표 이름, 72시간 단서, 위 표의 이유를 담습니다. 쿼리, 데이터셋 위치, 내보내기가 이미 켜져 있다는 주장은 담지 않습니다.

## Sources

> Checked 2026-11-08.

| Claim | Source |
|---|---|
| 표준 속성의 하루 BigQuery 내보내기 한도는 100만 이벤트이고, 360은 훨씬 높은 상한을 가지며 Fresh Daily는 360 전용 | <https://support.google.com/analytics/answer/9358801> |
| 하루 한도를 넘으면 내보내기가 일시 중지되고 이전 날짜의 내보내기는 다시 처리되지 않음 | <https://support.google.com/analytics/answer/9823238> |
| 데이터셋 `analytics_<property_id>`, 일간 표 `events_YYYYMMDD`, 당일 표 `events_intraday_YYYYMMDD`는 일간 표 완성 뒤 삭제됨 | <https://support.google.com/analytics/answer/7029846> |
| 스키마 페이지는 일간 표가 이벤트 날짜 뒤 최대 3일까지 갱신된다고 적음 | <https://support.google.com/analytics/answer/7029846> |
| 지원 페이지는 "up to 2 calendar days, plus today"라고 적음 | <https://support.google.com/analytics/answer/9358801> |
| 스트리밍 내보내기는 최선 노력이고 데이터 구멍이 있을 수 있으며 신규 사용자 트래픽 소스 필드를 뺌 | <https://support.google.com/analytics/answer/9358801> |
| `event_params`, `item_params`, `user_properties`는 `key`로 묶인 반복 RECORD이고 문자열·정수·실수 값을 가짐 | <https://support.google.com/analytics/answer/7029846> |
| Data API 요청은 최대 250,000행을 돌려주고, 표준 할당량의 가장 작은 버킷은 프로젝트·속성당 시간당 14,000토큰 | <https://developers.google.com/analytics/devguides/reporting/data/v1/rest/v1beta/properties/runReport>, <https://developers.google.com/analytics/devguides/reporting/data/v1/quotas> |

### Evidence grade

하루 100만 이벤트 한도, 일시 중지와 재처리 없음, 데이터셋·표 이름, 당일 표의 수명, 반복 RECORD 스키마, 스트리밍 단서, 두 페이지가 각각 적은 지연 데이터 창은 위 페이지를 2026-11-08에 읽은 `MEASURED`입니다. 두 페이지가 어긋나서 고른 72시간 보수적 값, 세 형태 권고 규칙, 내보내기를 설정하지 않고 권고한다는 규칙은 `LOCAL`입니다. 어긋남 자체는 선호로 해소하지 않고 불일치로 보고하며, 보수적 값은 두 페이지가 합치할 때까지 이 패키지가 기록하는 값입니다.
