# 동의

사이트가 동의가 필요한 사용자에게 서비스하거나, 컨테이너에 동의 설정이 있거나, 발견 사항이 동의에 관한 것이면 이 파일을 읽습니다. `volatile` 표시가 붙은 사실은 Google의 동의 제품과 개인정보 법과 함께 바뀝니다. 법률 행은 구현이 무엇을 공개해야 하는지 확인하는 점검표이며 법률 자문이 아닙니다.

## Contents

- 1. Consent Mode v2
- 2. Defaults before measurement
- 3. Consent in the container
- 4. CMP wiring
- 5. Verification
- 6. Korean privacy-policy items
- Sources

## 1. Consent Mode v2

| Type | Controls |
|---|---|
| `ad_storage` | 광고 쿠키와 저장소 |
| `analytics_storage` | 분석 쿠키와 저장소 |
| `ad_user_data` | 광고를 위해 Google로 사용자 데이터 전송(2023년 11월 추가) |
| `ad_personalization` | 맞춤 광고(2023년 11월 추가) |
| `functionality_storage`, `personalization_storage`, `security_storage` | CMP나 템플릿이 매핑할 수 있는 Google 외 저장소 목적 |

- 기본 모드: Google 태그는 사용자가 동의하기 전까지 로드하거나 아무것도 보내지 않습니다.
- 고급 모드: 태그가 `denied` 기본값으로 로드되고 쿠키 없는 핑을 보냅니다. GA4는 속성에 거부된 트래픽이 충분히 쌓이면 이 핑을 행동 모델링에 씁니다(`volatile`, 7일 동안 하루 약 1,000거부 이벤트).
- 모드는 사용자와 함께 고릅니다. 동의 전에 수집하는 것을 바꾸므로 실서비스 사이트에서의 변경은 승인 등급입니다(`rules/safety-gates.md` §1).

## 2. Defaults Before Measurement

"If your consent code is called out of order, consent defaults won't work." 기본값은 모든 페이지에서 측정 명령보다 먼저 실행되어야 합니다.

```html
<script>
window.dataLayer = window.dataLayer || [];
function gtag(){dataLayer.push(arguments);}
gtag('consent', 'default', {
  ad_storage: 'denied',
  ad_user_data: 'denied',
  ad_personalization: 'denied',
  analytics_storage: 'denied',
  wait_for_update: 500
});
</script>
<!-- then the container snippet -->
```

- GTM 설치에서 권장되는 경로는 **Consent Initialization - All Pages**에 붙인 동의 템플릿(CMP의 Community Template Gallery 템플릿이나 사용자 템플릿)입니다. 이 트리거는 "will always fire before all other tags, including any Initialization triggers"이며 `setDefaultConsentState`를 호출하고 나중에 `updateConsentState`를 호출합니다. "Don't create templates that use the `gtag consent` command." 위의 페이지 코드 블록은 템플릿을 쓸 수 없을 때의 대체 수단이고, 그때는 컨테이너 스니펫 위에 있어야 합니다.
- 기본값은 항상 설정합니다. 설정하지 않은 동의는 허용으로 동작하므로 `update`만 보내는 페이지는 선택 전에 측정합니다. `'granted'`가 아닌 값은 모두 `'denied'`로 취급됩니다.
- 지역별 기본값: 지역 목록마다 기본값 하나입니다(`region: ['KR']`). 가장 구체적인 지역이 이기고 `region` 없는 기본값이 나머지 모두를 덮습니다.
- `wait_for_update`(밀리초)는 태그가 발화 전에 CMP의 업데이트를 기다리게 합니다.
- 사용자의 선택 뒤 업데이트: 템플릿에서는 `updateConsentState`, 페이지 코드 대체 수단에서는 `gtag('consent', 'update', {...})`입니다.
- `ad_user_data`는 광고 측정 용도(향상된 전환, 전환 추적)에 필요하고, 맞춤 광고에는 `ad_user_data`와 `ad_personalization`이 모두 허용되어야 합니다.
- `url_passthrough: true`(`gtag('set', 'url_passthrough', true)`)는 저장소가 거부됐을 때 광고 클릭 식별자를 URL에 유지합니다. `ads_data_redaction: true`는 `ad_storage`가 거부됐을 때만 효과가 있습니다.
- Google 태그의 **Set consent mode override** 설정(`volatile`, 2024-08-28 이후)은 코드 순서를 고칠 수 없을 때 고른 지역에 `denied` 기본값을 강제합니다.
- Custom HTML 태그로 동의를 절대 설정하지 않습니다. gtag 명령이 대기 중인 dataLayer 메시지 뒤에 줄을 서므로, 같은 이벤트로 발화한 태그들이 서로 다른 동의 상태를 볼 수 있습니다.

## 3. Consent in the Container

- Admin > Container Settings > **Enable consent overview**를 켜면 모든 태그의 동의 상태를 한곳에서 봅니다.
- 태그마다 **Consent Settings**가 있습니다. 내장 동의 검사(Google 태그는 동의 유형을 직접 읽습니다), **No additional consent required**(`notNeeded`), **Require additional consent for tag to fire**(`needed`)와 나열한 동의 유형입니다. `notSet`은 아무도 정하지 않았다는 뜻입니다.
- 내장 검사가 있는 Google 태그에는 **Require additional consent**를 더하지 않습니다. "If you have implemented consent mode and use additional consent checks at the same time, they won't work properly"인데, 차단된 태그는 나중에 동의가 허용돼도 다시 발화하지 않기 때문입니다.
- Google 외 태그(Meta, TikTok, Hotjar, Custom HTML)에는 내장 검사가 없습니다. 맞는 유형으로 `needed`를 설정하지 않으면 동의 전에 발화합니다.
- 사용자 템플릿은 `setDefaultConsentState`, `updateConsentState`, `isConsentGranted`, `addConsentListener`로 동의를 설정하고 읽으며, 템플릿은 `access_consent` 권한을 선언합니다.
- `scripts/gtm-container-audit.sh`는 태그마다 `CONSENT_NOT_SET`을, Consent Initialization에서 발화하는 것이 없으면 `NO_CONSENT_INIT`을 보고합니다.

## 4. CMP Wiring

- 동의 배너는 GTM 안의 태그가 아니라 페이지 코드나 CMP 벤더 자체 스크립트로 불러옵니다. "some users block tag managers"이고, GTM으로 전달한 배너는 그때 사라집니다.
- Google 광고 제품으로 맞춤 광고를 내보내는 게시자는 EEA와 영국(2024-01-16 이후), 스위스(2024-07-31 이후) 사용자에게 IAB TCF와 연동된 Google 인증 CMP를 써야 합니다. 광고주는 Google의 EU 사용자 동의 정책에 따라 동의를 받아야 합니다. Google의 CMP Partner 배지는 연동 벤더를 나열하지만 "adopting any of these partners"가 규정 준수를 보장하지는 않습니다(`volatile`).
- CMP 하나를 권하고 벤더를 고르기 전에 한 번 묻습니다. 벤더 추가는 승인 등급입니다.
- Community Template Gallery 템플릿이 있는 CMP는 그것을 Consent Initialization 트리거에 붙여 씁니다.

## 5. Verification

- Tag Assistant **Consent** 탭: **On-page Default**과 **On-page Update** 열을 읽습니다. 가장 이른 동의 이벤트가 기본값이고 가장 늦은 것이 업데이트입니다. 배너를 누르기 전과 뒤에 둘 다 확인합니다. 이 탭은 동의 모드의 네 유형만 보여 줍니다.
- `/g/collect` 요청은 `gcs`(`ad_storage`와 `analytics_storage`)와 `gcd`로 동의 상태를 담습니다. 동의 전 `analytics_storage`가 거부된 요청은 고급 모드의 쿠키 없는 핑이거나 기본 모드에서는 없어야 합니다.
- `scripts/gtm-site-check.sh`는 서버가 보낸 HTML에서 기본값이 로더 뒤에 나타나면 `CONSENT_AFTER_LOADER`를 보고합니다.
- DebugView는 분석 동의가 없었으면 이벤트를 보여 주지 않습니다. CMP가 켜진 상태의 빈 DebugView는 설치가 깨졌다는 뜻이 아닙니다.
- Tag Diagnostics는 "Consent mode installation out of order"와 "0% consent rate detected"를 표시합니다.

## 6. Korean Privacy-Policy Items

한국 사용자에게 서비스하는 사이트의 개인정보 처리방침에는 다음이 있어야 합니다(개인정보 보호법 제30조 제1항).

- 쿠키 같은 자동 수집 장치의 설치, 운영, 거부(제7호, "인터넷 접속정보파일 등 개인정보를 자동으로 수집하는 장치의 설치ㆍ운영 및 그 거부에 관한 사항")
- 제3자 제공(제3호)과 위탁 처리(제4호). 분석 처리자로서의 Google이 여기에 해당합니다.
- 데이터가 해외의 Google 서버로 가면 국외 이전 항목(제28조의8)

빠진 항목은 정책 담당자를 위한 발견 사항으로 보고합니다. 이 스킬은 법률 문구를 쓰지 않습니다. 개인정보보호위원회의 개인정보 처리방침 작성 지침(2026-04)은 해당하는 경우 제3자의 행태정보 공개를 권장 사항으로 다루고, 방침을 공개하지 않으면 최대 1천만 원의 과징금이 있음을 밝힙니다(`volatile`).

## Sources

> Checked 2026-11-08.

| Claim | Source |
|---|---|
| 동의 유형, 측정 전 기본값, 순서 규칙, `wait_for_update`, `region` | <https://developers.google.com/tag-platform/security/guides/consent> |
| 기본 모드와 고급 모드 | <https://developers.google.com/tag-platform/security/concepts/consent-mode> |
| 행동 모델링 임계값 | <https://support.google.com/analytics/answer/11161109> |
| Tag Assistant의 동의 디버깅 | <https://developers.google.com/tag-platform/security/guides/consent-debugging> |
| 동의 설정, 동의 개요, Consent Initialization 순서, 광고 동의 유형 | <https://support.google.com/tagmanager/answer/10718549>, <https://support.google.com/tagmanager/answer/13802165> |
| 템플릿 동의 API와 템플릿의 `gtag consent` 금지 | <https://developers.google.com/tag-platform/tag-manager/templates/consent-apis>, <https://developers.google.com/tag-platform/tag-manager/templates/api> |
| Google 태그의 추가 동의 검사 | <https://support.google.com/tagmanager/answer/12962079> |
| 게시자용 인증 TCF CMP, EU 사용자 동의 정책 | <https://support.google.com/adsense/answer/13554116>, <https://www.google.com/about/company/user-consent-policy/> |
| Custom HTML로 동의를 설정하지 않음 | <https://developers.google.com/tag-platform/devguides/datalayer> |
| Consent mode override 설정 | <https://support.google.com/tagmanager/answer/4620708> |
| 사용자가 태그 관리자를 차단함 | <https://web.dev/articles/tag-best-practices> |
| 한국 개인정보 처리방침 항목 | <https://www.law.go.kr/법령/개인정보보호법/제30조>, <https://www.law.go.kr/LSW/lsSideInfoP.do?lsiSeq=283839&joNo=0028&joBrNo=08&docCls=jo> |

### Evidence grade

2026-11-08에 읽은 Google 공식 문서, 한국 법령 원문(시행 2026-09-11), 개인정보보호위원회 지침 PDF(9, 14-15쪽)입니다. Google 자체 문서는 기본값이 없을 때 고급 모드가 무엇을 하는지 서로 다르게 적고 있으며, 이 파일은 템플릿 API 규칙(설정하지 않으면 허용)을 따릅니다. CMP 요구 사항과 override 설정은 Google 정책과 함께 바뀌므로 의존하기 전에 다시 확인합니다.
