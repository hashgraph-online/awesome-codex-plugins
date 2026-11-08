# 동의와 개인정보

동의 질문, PII 질문, 보존 기간 질문, 한국 개인정보 처리방침 고지 점검에서 이 참조를 읽습니다. Consent Mode v2 스니펫과 그 순서, 기본 모드와 고급 모드, Tag Assistant 확인, PII 규칙, 보존 기간, 고지 점검표를 소유합니다.

한국어 절은 구현을 위한 고지 점검표입니다. 법률 자문이 아니며, 특정 사이트에 적법한 근거가 있는지 판단하지 않습니다.

> 영어판: [`consent-and-privacy.md`](consent-and-privacy.md)

## Contents

- The consent default must precede the tag
- Parameters
- Region defaults
- Basic and advanced mode
- Verifying consent
- Personal data
- Retention
- Korean disclosure checklist

## The consent default must precede the tag

`gtag('consent', 'default', ...)`를 모든 페이지에서, 측정 데이터를 보내는 어떤 명령보다도 먼저 호출합니다. Google은 실패 방식을 분명히 적습니다. "If your consent code is called out of order, consent defaults won't work."

태그가 이미 페이지뷰를 보낸 뒤에 도착한 기본값은 그 페이지뷰를 소급해 거부하지 않습니다. 사이트에 동의 플랫폼이 없으면 기본값은 사용자가 행동할 때까지 저장을 막고, 보고서는 배너를 한 번도 건드리지 않은 사용자에게서 이제 아무것도 수집하지 않는다고 적어야 합니다.

## Parameters

```html
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}

  gtag('consent', 'default', {
    ad_storage: 'denied',
    ad_user_data: 'denied',
    ad_personalization: 'denied',
    analytics_storage: 'denied',
    wait_for_update: 500,
    region: ['ES', 'DE', 'FR', 'IT', 'NL', 'BE', 'AT', 'PL', 'SE', 'IE', 'DK', 'FI', 'PT', 'GR', 'CZ', 'RO', 'HU', 'SK', 'BG', 'HR', 'SI', 'LT', 'LV', 'EE', 'LU', 'MT', 'CY', 'IS', 'LI', 'NO', 'GB', 'CH'],
  });
  gtag('set', 'url_passthrough', true);
  gtag('set', 'ads_data_redaction', true);

  gtag('js', new Date());
</script>
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
```

위 스니펫에 Consent Mode v2 매개변수 네 개가 모두 있습니다. 광고 매개변수 둘은 2023년 11월에 추가됐으므로, `ad_storage`와 `analytics_storage`만 든 스니펫은 v2 이전이며 발견 사항입니다.

| Parameter | What it controls |
|---|---|
| `ad_storage` | 광고용 쿠키나 로컬 저장소 |
| `analytics_storage` | 분석용 쿠키나 로컬 저장소 |
| `ad_user_data` | 광고 관련 사용자 데이터를 Google로 보내는 일 |
| `ad_personalization` | 개인화 광고 |

## Region defaults

- `region`은 ISO 3166-2 코드를 받습니다. 지역을 담은 호출과 담지 않은 호출이 함께 있을 수 있고, "더 구체적인 지역을 담은 쪽이 적용됩니다".
- 요청이 범위를 말하지 않으면 EEA, 영국, 스위스에 `denied` 기본값을 쓰고 그 선택을 보고서에 밝힙니다. 위 목록은 구체적인 인코딩 한 가지입니다. EU 회원국 27개에 EEA 구성국인 아이슬란드, 리히트슈타인, 노르웨이를 더하고, 그 뒤에 영국과 스위스를 둡니다. 사이트의 실제 시장 목록과 맞춥니다.
- 올바른 형태는 전역 기본값 하나에 더 엄격한 지역 기본값을 더한 것이지, 추측한 기본값 하나가 아닙니다.

## Basic and advanced mode

| Mode | What is sent before consent | Consequence |
|---|---|---|
| Basic | 아무것도 보내지 않습니다. "동의 상태조차" 보내지 않습니다 | 모델링이 없고 거부한 사용자는 그냥 빠집니다 |
| Advanced | 쿠키 없는 핑 | 행태 모델링과 전환 모델링이 빈자리의 일부를 채울 수 있습니다 |

- 모드는 요청에서 고릅니다. 요청이 말하지 않으면 기본 모드 기본값을 쓰고 그 선택을 밝힙니다. 고급 모드로 바꾸는 것은 브라우저 밖으로 나가는 내용을 바꾸므로 사이트 소유자의 결정입니다.
- 고급 모드 모델링에는 물량이 필요합니다. `analytics_storage='denied'` 상태로 하루 1,000개 이상 이벤트가 7일 이상, 그리고 28일 가운데 7일에 하루 허용 사용자 1,000명 이상입니다. 트래픽이 적은 사이트에 모델링을 약속하지 않습니다.
- 모델링된 데이터는 잠재고객, 보존, BigQuery 내보내기, 예측 지표에 닿지 않습니다.
- `url_passthrough`는 쿠키가 거부된 상태에서 `gclid`, `dclid`, `gclsrc`, `_gl`, `wbraid`를 페이지 사이로 이어 줍니다.
- `ads_data_redaction`은 `ad_storage`가 허용이거나 동의 명령이 아예 돌지 않으면 효과가 없으므로, 허용 기본값과 함께 두는 것은 제어가 아니라 장식입니다.

## Verifying consent

확인 수단은 배너 자체의 상태가 아니라 Tag Assistant입니다.

1. Tag Assistant를 붙여 페이지를 열고 디버그 세션을 시작합니다.
2. Consent 이벤트를 찾습니다. 가장 이른 것이 페이지의 기본값이고 가장 늦은 것이 업데이트입니다.
3. 기본 이벤트에서 매개변수 네 개를 모두 확인합니다. `ad_storage`, `ad_personalization`, `ad_user_data`, `analytics_storage`입니다.
4. 기본값이 첫 수집 요청보다 앞서는지, 업데이트가 사용자 행동 뒤에 오는지 확인합니다.

`gcs`는 수집 요청에 저장 동의를 인코딩하고, `gcd`는 동의 모드가 꺼져 있어도 항상 전송됩니다. `gcs`가 저장 거부를 보이는데도 페이지뷰가 집계되면 기본값이 너무 늦게 도착했다는 증거입니다.

## Personal data

- "Google prohibits customers from sending Personally Identifiable Information to Google Analytics."
- "Both the URL path and parameters must be free of PII." 여기에는 `page_location`, `page_title`, 쿼리 문자열, 해시 조각이 포함됩니다.
- PII에는 이메일 주소, 실명과 사용자 이름, 우편 주소, 전화번호, 정밀 위치가 들어갑니다. 1제곱마일보다 작은 영역은 위도·경도 쌍을 포함해 금지됩니다. 가명 쿠키 ID와 IP 주소는 Google의 정의에서 빠지며, GA4는 IP 주소를 기록하거나 저장하지 않으므로 IP 마스킹은 GA4 작업이 아닙니다.
- `user_id`는 최대 256자여야 하고, 제3자가 신원을 알아낼 수 없어야 하며, Analytics 쿠키에 저장해서는 안 되고, 커스텀 디멘션으로 등록하지 않는 것이 좋습니다.
- 인터페이스의 데이터 가림은 웹 전용이고 최선 노력이며 클라이언트 측입니다. Measurement Protocol이나 데이터 가져오기는 덮지 않습니다.
- `api_secret`은 비공개이며 클라이언트 코드에 나타나서는 안 됩니다.
- 기존 코드가 PII 값을 보낼 수 있으면 파일과 줄이 붙은 발견 사항으로 보고하고, 그 값을 보고서에 복사하지 않으며, 가림이나 제거를 제안합니다.

## Retention

- 표준 속성은 사용자 수준 보존 2개월 또는 14개월, 이벤트 수준 보존 2·14·26개월을 제공합니다. 38개월과 50개월은 360 전용입니다. Large와 XL 속성은 이벤트 데이터가 2개월로 강제됩니다.
- 2개월 기간은 나이, 성별, 관심사 데이터에 항상 적용됩니다.
- 삭제는 월 단위로 돌고, 나중에 보존을 늘리면 아직 남아 있는 데이터를 채울 수 있습니다.
- 회수된 데이터는 탐색과 퍼널에 쓰이고 집계 리포트는 영향을 받지 않습니다.
- 보존 기간을 줄이는 일은 승인 등급 행동입니다. 무엇이 영구 삭제되고 복구할 수 없는지 밝힌 뒤 기다립니다.

## Korean disclosure checklist

이것은 구현을 위한 고지 점검표이며 법률 자문이 아닙니다. 각 행을 사이트의 실제 처리와 대조해 있음, 빠짐, 해당 없음으로 표시하고 사유를 적습니다.

| Item | Provision | What the policy must state | GA4 hook |
|---|---|---|---|
| 3호 | 개인정보 보호법 제30조 제1항 제3호 | 제3자 제공: 제공받는 자, 목적, 항목, 보유 기간, 거부할 권리 | 식별자가 사이트를 떠날 때 제공받는 자로서의 Google LLC |
| 4호 | 개인정보 보호법 제30조 제1항 제4호 | 처리 위탁: 수탁자와 위탁 업무의 범위 | 사이트 소유자를 대신해 태그를 운영하는 대행사나 업체 |
| 7호 | 개인정보 보호법 제30조 제1항 7호 | "인터넷 접속정보파일 등 개인정보를 자동으로 수집하는 장치의 설치ㆍ운영 및 그 거부에 관한 사항" | `_ga`와 `_ga_<container-id>` 쿠키, 그것이 수집하는 것, 방문자가 거부하는 방법 |
| Overseas transfer | 개인정보 보호법 제28조의8 | 이전되는 항목, 국가, 시기와 방법, 이전받는 자의 성명과 연락처, 목적, 보유 기간, 거부 방법 | Google의 국외 인프라에서의 수집 |

이 절의 규칙입니다.

- 보고서에 위 조항과 호 번호를 그대로 쓰고, 7호 문장은 법이 쓴 그대로 인용합니다.
- 쿠키를 언급하지만 거부 방법이 없는 처리방침은 법이 쓴 7호를 충족하지 못합니다.
- Google을 분석 도구로만 적고 제공받는 자, 목적, 항목, 보유 기간을 빼면 국외 이전 행을 충족하지 못합니다.
- 각 행의 상태와 그 근거를 보고합니다. 처리방침 본문을 대신 써 주지 않고, 동의가 법적으로 유효한지에 답하지 않습니다.

## Sources

> Checked 2026-11-08.

| Claim | Source |
|---|---|
| 동의 기본값은 모든 페이지에서 측정 명령보다 먼저 돌고, 순서가 틀리면 동작하지 않으며, Consent Mode v2가 2023년 11월 `ad_user_data`와 `ad_personalization`을 더했습니다 | <https://developers.google.com/tag-platform/security/guides/consent> |
| 기본 모드는 동의 전 아무것도 보내지 않고, 고급 모드는 쿠키 없는 핑을 보내며, `gcd`는 항상 전송되고 `gcs`는 저장 동의를 인코딩합니다 | <https://developers.google.com/tag-platform/security/concepts/consent-mode> |
| 더 구체적인 지역이 적용되고, `url_passthrough`는 `gclid`, `dclid`, `gclsrc`, `_gl`, `wbraid`를 이어 주며, `ads_data_redaction`은 `ad_storage` 거부가 필요합니다 | <https://developers.google.com/tag-platform/security/guides/consent> |
| 가장 이른 Consent 이벤트가 페이지 기본값이고 가장 늦은 것이 업데이트이며, 그곳에서 매개변수 네 개를 확인합니다 | <https://developers.google.com/tag-platform/security/guides/consent-debugging> |
| 모델링에는 7일간 하루 거부 이벤트 1,000개와 28일 중 7일의 하루 허용 사용자 1,000명이 필요하고, 모델링 데이터는 잠재고객·보존·BigQuery 내보내기·예측 지표에 없습니다 | <https://support.google.com/analytics/answer/11161109> |
| Google은 PII 전송을 금지하고 URL 경로와 매개변수 모두 PII가 없어야 합니다 | <https://support.google.com/analytics/answer/6004245>, <https://support.google.com/analytics/answer/6366371> |
| 1제곱마일 미만의 정밀 위치는 금지되고, IP 주소와 가명 ID는 PII 정의에서 빠집니다 | <https://support.google.com/analytics/answer/7686480> |
| 데이터 가림은 웹 전용이며 Measurement Protocol과 데이터 가져오기를 덮지 않습니다 | <https://support.google.com/analytics/answer/13544947> |
| `user_id`는 최대 256자이고 제3자가 신원을 알 수 없어야 하며 커스텀 디멘션으로 쓰지 않는 것이 좋습니다 | <https://support.google.com/analytics/answer/9213390>, <https://support.google.com/analytics/answer/12675187> |
| 보존 옵션, Large·XL 속성의 강제 2개월, 월 단위 삭제 | <https://support.google.com/analytics/answer/7667196> |
| 제30조 제1항 3호·4호·7호, 시행 2026-09-11, 법률 제21445호 | <https://www.law.go.kr/법령/개인정보보호법/제30조> |
| 국외 이전 고지는 제28조의8 | <https://www.law.go.kr/LSW/lsSideInfoP.do?lsiSeq=283839&joNo=0028&joBrNo=08&docCls=jo> |
| `api_secret`은 비공개이며 클라이언트 코드에 노출해서는 안 됩니다 | <https://developers.google.com/analytics/devguides/collection/protocol/ga4/sending-events> |

### Evidence grade

인용 문장, 매개변수 이름, 임계값, 보존 옵션, 조항 번호는 위 페이지를 2026-11-08에 읽은 `MEASURED`입니다. 점검표 행, 지역 목록 인코딩, 요청이 침묵할 때 `denied` 기본값을 쓰라는 지시는 이 패키지의 `LOCAL` 설계입니다. 법령은 시행 판(2026-09-11)에서 읽었고 이 절은 의도적으로 고지 내용에서 멈추므로 법률 자문이 되지 않습니다.
