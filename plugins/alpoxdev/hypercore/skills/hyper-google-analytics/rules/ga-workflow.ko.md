# GA 워크플로

이 규칙으로 모드를 고르고 그 단계를 실행합니다. 모드 선택, 모드별 단계, `diagnose`가 걷는 고정 순서를 소유합니다.

## 1. Pick The Mode

모드는 요청에 쓰인 단어가 아니라 요청한 결과물을 따릅니다.

| 요청한 결과물 | 모드 |
|---|---|
| 지금 무엇이 설정돼 있는지에 대한 발견 사항 목록이며 변경 없음 | `audit` |
| 저장소에 GA4를 추가하거나 고치고 태그를 실제로 띄움 | `install` |
| 속성 설정 하나를 바꾸고 다시 읽어 확인함 | `configure` |
| 보고 데이터로 답하는 숫자나 비교 | `analyze` |
| 빠지거나 중복되거나 잘못된 데이터의 원인 | `diagnose` |

한 요청이 모드 둘을 가질 수 있습니다. "점검하고 빠진 것도 넣어줘"는 `audit` 다음 `install`입니다. 그 순서로 실행하고 각각에 자기 완료 근거를 붙입니다.

## 2. Identify Before Writing

속성이나 라이브 사이트에 처음 쓰기 전에 다음을 모두 밝힙니다.

- 계정, 속성 ID(`properties/<숫자>`), 스트림 ID 또는 측정 ID(`G-`)
- 환경: 운영 사이트, 미리보기, 로컬
- 쓰기가 보낼 정확한 메서드와 본문

`accountSummaries.list` 다음 `dataStreams.list`로 얻습니다. 측정 ID만으로 속성 ID를 추측하지 않습니다.

## 3. Mode Phases

### `audit`

1. 저장소에서 태그, 측정 ID, 태그 관리자, 프레임워크 통합, 서버 측 호출을 스캔합니다. 각각의 파일과 줄을 기록합니다.
2. 실제 페이지를 열어 `/g/collect` 요청을 캡처합니다. 쿼리의 `tid`와 `en`, 응답 상태를 기록합니다.
3. 속성을 읽기 전용으로 읽습니다. 스트림과 그 측정 ID, 향상된 측정 토글, 핵심 이벤트, 커스텀 디멘션과 지표, 데이터 보존 기간, 데이터 필터, 원치 않는 추천, 교차 도메인 설정입니다.
4. 셋을 비교합니다. 실행되지 않는 코드, 속성 스트림과 측정 ID가 다른 태그, 두 번 보내는 페이지뷰, 수집을 막는 동의 기본값, 공개된 한도를 넘는 이벤트, 실제 트래픽을 가리는 필터입니다.
5. 모든 발견 사항을 심각도(데이터 전체 차단, 지표 왜곡, 리포트 오도, 표시 문제)로 채점하고 수정 담당(코드, 속성, 태그 관리자, 동의 배너)을 붙입니다.

### `install`

1. 프레임워크와 사이트 제약으로 방식을 고릅니다. 태그 관리자 컨테이너, `gtag.js` 스니펫, 프레임워크 패키지, 서버 측 호출 중 하나입니다. 고른 방식이 왜 맞는지와 버린 방식이 무엇을 치렀을지 밝힙니다.
2. 모든 페이지에서, 모든 측정 명령보다 앞에, 태그 호출 전에 동의 기본값을 씁니다. 동의 플랫폼이 없으면 기본값이 사용자가 행동할 때까지 저장을 막는다는 점을 분명히 적습니다.
3. 페이지뷰 출처를 정확히 하나만 고릅니다. 태그 관리자를 쓰면 자동 기록 추적을 함께 켜지 않습니다. 쓰지 않으면 `send_page_view`를 켜 두고 기록 이벤트가 이끌게 하거나, 둘 다 끄고 라우트 변경 때 `page_view`를 직접 보냅니다. 둘 다 켜 두지 않습니다.
4. 태그가 필요로 하는 CSP 항목을 넣습니다. `script-src-elem https://www.googletagmanager.com`, `https://*.google-analytics.com`에 대한 `connect-src`와 `img-src`, 인라인 컨테이너 코드용 nonce입니다.
5. 수집을 증명합니다. 페이지를 새로 열어 기대한 `tid`와 `en=page_view`를 가진 `/g/collect` 요청을 캡처하고 상태를 기록하거나, `debug_mode`가 있을 때만 동작하는 DebugView에 이벤트를 보여 줍니다. 디버그를 끄는 방법은 매개변수를 빼는 것뿐입니다.

### `configure`

1. 현재 값을 먼저 읽고 필드와 그 경로를 인용합니다.
2. 계정, 속성, 스트림을 밝힌 뒤 정확한 변경을 적습니다. 메서드, 바뀌는 필드, 전후 값입니다.
3. 승인 등급에 있는 변경이면 여기서 멈추고 `rules/safety-gates.md` §5를 따릅니다.
4. 한 번 쓰고 나서 `get`으로 리소스를 다시 읽어 바뀐 필드를 인용합니다.
5. 처리 뒤에야 효력이 생기는 설정(데이터 필터, 핵심 이벤트, 변경한 이벤트)이면 얼마나 걸리는지와 read-back만으로는 무엇을 증명할 수 없는지 밝힙니다.

### `analyze`

1. 질문을 디멘션, 지표, 날짜 범위, 필터나 비교로 옮깁니다.
2. 보내기 전에 `getMetadata`로 이름을 확인하고, 새 조합이면 `checkCompatibility`로 짝을 확인합니다.
3. `limit`을 명시해 요청 하나를 보내고, 응답이 할당량을 돌려주면 읽습니다. 요청당 250,000행 상한과 10,000행 기본값이 모두 적용됩니다.
4. 응답이 돌려준 데이터 품질 표시를 모두 보고서로 옮깁니다. 임계값 적용, 샘플링 메타데이터, `(other)` 통합과 `dataLossFromOtherRow`, 고유 수가 HLL++ 추정이라는 사실입니다.
5. 결론을 한 문장으로 적고, 그다음 숫자를 요청, 날짜 범위, 주의와 함께 적습니다.

### `diagnose`

이 순서를 걷고 증상을 설명하는 첫 원인에서 멈춥니다. 시험하기 쉽다는 이유로 뒤 원인으로 건너뛰지 않습니다.

1. **요청 자체가 없음.** 태그가 아예 로드되지 않습니다. 빠진 스니펫, 번들러가 막은 스크립트, 실어야 할 이벤트 뒤에 놓인 태그, 빌드가 지운 코드입니다.
2. **잘못된 측정 ID.** 페이지가 이 속성 스트림이 아닌 `tid`를 보냅니다. 옛 설치에서 남은 중복 태그, 운영에 남은 테스트 ID입니다.
3. **동의 거부.** 동의 기본값이 측정 명령보다 앞에서 저장을 막거나, 동의 업데이트가 실행되지 않거나, 코드 순서가 기본값을 태그 뒤에 둡니다.
4. **CSP나 네트워크 차단.** 빠진 `connect-src`나 `script-src-elem`, 시험 브라우저의 광고 차단기, 요청을 버리는 프록시입니다.
5. **중복.** 페이지뷰 출처 둘(자동 기록 추적과 수동 호출), 두 번 로드한 태그, `transaction_id` 없는 `purchase`, 클라이언트 이벤트를 반복하는 Measurement Protocol 이벤트입니다.
6. **필터와 추천.** 내부 트래픽이나 개발자 트래픽 필터, 빈 호스트 이름을 막는 호스트 이름 필터, 자기 추천, 2분이 지나 만료된 교차 도메인 `_gl` 값입니다.
7. **처리 지연.** 요청이 맞고 도착합니다. 숫자가 아직 표준 보고서에 없을 뿐이고 표준 보고서는 24시간에서 48시간 지연됩니다. 결함이 아니며 지연으로 보고하고 고쳤다고 말하지 않습니다.

루프 규칙:

- 원인마다 최대 세 번 시도하고 재개를 거쳐 셉니다. 한 원인에서 세 번째 실패하면 그 원인에 대해 `exhausted`로 끝내고 다음에 모을 근거를 적습니다.
- 검사자는 새 네트워크 요청, DebugView, 실시간입니다. 표준 보고서는 검사자가 아닙니다.
- 증상이 아니라 원인을 고칩니다. 중복을 멈추려고 이벤트를 빼지 않고, 빈틈을 가리려고 필터를 넓히지 않고, 신호를 띄우려고 점검을 끄지 않습니다.

## 4. Report Path

`references/report-template.md`를 따라 `.hyper/google-analytics/<slug>/report.md`를 씁니다. 한 저장소에 속성이 여럿이면 slug는 사이트나 속성 이름에 모드를 붙입니다.

## Sources

> Checked 2026-11-08.

| Claim | Source |
|---|---|
| 표준 보고서는 24시간에서 48시간 지연되고 실시간은 수 분 안에 나타나며, `/g/collect` 요청은 성공하면 `200`이나 `204`로 답합니다 | <https://developers.google.com/analytics/devguides/collection/ga4/troubleshoot> |
| 디버그 모드는 `debug_mode`를 더해 켜고, `false`로 두어도 꺼지지 않으므로 매개변수를 빼야 합니다 | <https://support.google.com/analytics/answer/7201382> |
| 동의 기본값은 모든 페이지에서 모든 측정 명령보다 먼저 실행해야 하고, 순서가 틀리면 동작하지 않습니다 | <https://developers.google.com/tag-platform/security/guides/consent> |
| 태그 관리자를 쓰면서 Analytics의 자동 기록 추적을 켜면 페이지뷰가 두 번 집계됩니다 | <https://developers.google.com/analytics/devguides/collection/ga4/single-page-applications> |
| 태그의 최소 CSP 항목은 스크립트에 `googletagmanager.com`, connect와 image에 `google-analytics.com`을 적고 인라인 컨테이너 코드에 nonce를 씁니다 | <https://developers.google.com/tag-platform/security/guides/csp> |
| 데이터 필터는 24시간에서 36시간 안에 적용되고 효과는 영구적입니다 | <https://support.google.com/analytics/answer/10104470> |
| 교차 도메인 링커 매개변수는 2분 뒤 만료됩니다 | <https://developers.google.com/tag-platform/devguides/cross-domain> |
| `runReport`는 요청당 최대 250,000행을 돌려주고 기본값은 10,000행입니다 | <https://developers.google.com/analytics/devguides/reporting/data/v1/rest/v1beta/properties/runReport> |
| 임계값 적용, 샘플링 메타데이터, `(other)` 행, HLL++ 추정이 리포트가 담아야 하는 데이터 품질 표시입니다 | <https://developers.google.com/analytics/devguides/reporting/data/v1/reporting-data-expectations> |
| `checkCompatibility`와 `getMetadata`는 할당량을 쓰기 전에 디멘션과 지표 짝을 검증하려고 있습니다 | <https://developers.google.com/analytics/devguides/reporting/data/v1/rest> |

### Evidence grade

`LOCAL` - 모드 단계와 일곱 단계 원인 순서는 인용한 페이지 위에서 이 패키지가 고른 설계입니다. 지연, 필터, CSP, 할당량 값은 2026-11-08에 읽은 공식 페이지에서 `MEASURED`입니다. 순서는 싸고 자주 나오는 원인을 앞에 두므로 게시된 순위가 아니라 관찰된 실패를 반영합니다.
