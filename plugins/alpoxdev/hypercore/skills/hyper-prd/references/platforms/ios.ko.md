# iOS Platform Checklist

PRD에서 판정한 플랫폼에 iOS(`ios`)가 포함될 때만 이 파일을 불러오고, 플랫폼 요구사항 블록과 그 출시 게이트 표를 채운다. 항목마다 ID, 등급, PRD에 들어가야 할 문장이나 표, 근거, 확인 날짜를 적는다. 저장소나 대화에 답이 없는 항목은 추측으로 채우지 않고 PRD에서 `[확인 필요: ...]`가 된다.

## Grades

| 등급 | 뜻 | PRD가 해야 할 일 |
|---|---|---|
| `[M]` | App Store 심사 지침이나 법이 강제한다. 답이 틀리거나 없으면 출시가 막힌다 | 출시 게이트 표에 결론 하나 |
| `[M-조건]` | 정해진 조건이 성립할 때만 강제한다 | 결론 하나: 해당, 또는 조건을 밝힌 비해당 |
| `[G]` | 권장. 빠져도 심사에서 거절하지 않는다 | 이 제품에 관련 있을 때만 적는다 |

이 파일의 `[M]`·`[M-조건]` 항목은 모두 PRD 출시 게이트 표에 자기 행을 갖는다. 항목의 값은 정책을 다시 옮겨 적은 것이 아니라 결론이다. `해당`, 이유를 붙인 `비해당`, `[확인 필요]` 중 하나다. "App Store 심사 지침을 준수한다" 같은 문장은 결론이 아니며 검토에서 거절한다.

## Account deletion

| Id | 등급 | PRD에 적을 것 | 근거 | 확인 |
|---|---|---|---|---|
| I1 | `[M-조건]` | 조건: 앱이 계정 생성을 지원한다. 그러면 앱 안 어디에서 계정을 삭제하는지, 삭제가 무엇을 지우는지, 실행 전에 사용자에게 무엇을 알리는지를 적는다. 지침 5.1.1(v): "If your app supports account creation, you must also offer account deletion within the app". 계정 생성이 없는 앱은 "비해당"과 그 조건을 적는다. | [App Store Review Guidelines](https://developer.apple.com/app-store/review/guidelines/) 5.1.1(v) | 2026-11-07 |

## In-app purchase

| Id | 등급 | PRD에 적을 것 | 근거 | 확인 |
|---|---|---|---|---|
| I2 | `[M-조건]` | 조건: 앱이 앱 안에서 쓰는 디지털 재화나 디지털 서비스를 판다. 그러면 구매가 지침 3.1.1에 따라 앱 내 구매로 이뤄진다고 적고, 유료 항목마다 가격, 주기, 구매자가 받는 것을 나열한다. 실물 상품과 앱 밖에서 소비하는 서비스는 이 행의 범위 밖이라고 밝힌다. | [App Store Review Guidelines](https://developer.apple.com/app-store/review/guidelines/) 3.1.1 | 2026-11-07 |
| I3 | `[M-조건]` | 조건: 앱이 유료 구독을 판다. 그러면 구독이 끝난 뒤 구독자가 무엇을 유지하는지, 구매 화면에서 가격·주기·갱신 조건을 어떻게 보여 주는지 적는다. | [App Store Review Guidelines](https://developer.apple.com/app-store/review/guidelines/) 3.1.2 | 2026-11-07 |

## Privacy declaration

| Id | 등급 | PRD에 적을 것 | 근거 | 확인 |
|---|---|---|---|---|
| I4 | `[M]` | 출시가 다루는 데이터 유형마다 App Privacy 라벨 내용: 수집 여부, 사용자 신원과 연결되는지, 추적에 쓰는지, 목적. 새 앱 제출과 모든 앱 업데이트에 이 정보가 필요하다. | [App Privacy Details](https://developer.apple.com/app-store/app-privacy-details/) | 2026-11-07 |
| I5 | `[M]` | 프라이버시 매니페스트(`PrivacyInfo.xcprivacy`) 내용: 수집 데이터 유형, 앱이나 서드파티 SDK가 호출하는 required-reason API, 추적 도메인. 매니페스트 소유자와 그것이 포괄하는 SDK 목록을 PRD에 적는다. | [Privacy manifest files](https://developer.apple.com/documentation/bundleresources/privacy-manifest-files) | 2026-11-07 |

## App review access

| Id | 등급 | PRD에 적을 것 | 근거 | 확인 |
|---|---|---|---|---|
| I6 | `[M-조건]` | 조건: 앱의 일부라도 로그인을 요구한다. 그러면 전체 접근 권한이 있는 데모 계정을 App Store Connect에 제공한다고 적고, 계정 소유자와 로그인 뒤 심사자가 보는 것을 밝힌다. 지침 2.1 App Completeness가 심사 경로를 다룬다. 조사 파일이 인용문 없이 조항 번호만 기록했으므로 이 행은 인용이 아니라 조항을 근거로 든다. | [App Store Review Guidelines](https://developer.apple.com/app-store/review/guidelines/) 2.1 | 2026-11-07 |
| I7 | `[M]` | 최소 기능 답을 두 문장으로 적는다. 지침 4.2: 앱은 웹사이트를 다시 포장한 것을 넘어서는 자체 기능·콘텐츠·UI를 갖추므로, PRD가 그 콘텐츠나 상호작용을 밝힌다. 지침 4.2.2: 앱은 주로 마케팅 자료, 광고, 웹 스크랩, 콘텐츠 수집물, 링크 모음이 아니므로, PRD가 그것만으로 남을 부분이 무엇인지 밝힌다. | [App Store Review Guidelines](https://developer.apple.com/app-store/review/guidelines/) 4.2, 4.2.2 | 2026-11-07 |

## Permission requests

| Id | 등급 | PRD에 적을 것 | 근거 | 확인 |
|---|---|---|---|---|
| I8 | `[G]` | 앱이 요청하는 권한마다: 요청이 나타나는 화면, 시스템 창 앞에 보여 주는 문장, 권한을 거부했을 때 동작하지 않는 기능. 요청은 앱 시작 시가 아니라 문맥 안에서 한다: "Make the request in a context that helps people understand why your app needs authorization." | [Asking permission to use notifications](https://developer.apple.com/documentation/usernotifications/asking-permission-to-use-notifications) | 2026-11-07 |

## Shared data-collection matrix

판정한 플랫폼에 iOS와 Android가 함께 있으면 매트릭스를 한 번만 쓰고 두 방향에서 읽는다. 두 번 쓰면 두 서술이 어긋나고, 두 스토어가 같은 동작을 다르게 설명받는다.

| 데이터 유형 | 수집 | 제3자 공유 | 사용자 신원 연결 | 추적 사용 | 목적 | 선택 여부 | 일시 처리 |
|---|---|---|---|---|---|---|---|

- App Privacy 라벨 행(`I4`)과 Play Data safety 행이 모두 이 표에서 풀린다. 어느 쪽도 데이터 유형을 기억으로 다시 적지 않는다.
- 한 플랫폼은 수집하고 다른 플랫폼은 수집하지 않는 유형은 신고 세부가 아니라 제품 결정이다. 차이와 이유를 PRD에 적는다.
- 출시가 다루는데 표가 빠뜨린 유형은 표의 결함이다. 어느 스토어 양식을 채우기 전에 표를 고친다.

## Filling the release gate table

| 열 | 내용 |
|---|---|
| ID | 이 파일의 항목 ID. 예: `I1` |
| 등급 | 이 파일의 등급을 그대로 옮긴다 |
| 항목 | 의무를 짧은 문장 하나로 쓴다. 수치 항목이면 임계값, 측정 방법, 분위수를 함께 쓴다 |
| 결론 | `해당`, 조건이나 이유를 붙인 `비해당`, `[확인 필요: <질문>]` |
| 근거 | 결론을 확정하는 문서, App Store Connect 화면, 측정 |
| 재확인 | 날짜가 붙은 값을 다시 확인하는 날. 날짜가 없는 항목은 `none` |

결론이 `[확인 필요]`인 `[M]` 행이 있으면 PRD는 `status: draft`로 남는다. 스토어 정책 값은 Apple이 지침을 고치면 함께 바뀐다. 분기마다, 그리고 App Store 공지를 받을 때마다 모든 행을 현재 지침 원문과 대조하고, 이 파일을 믿지 말고 날짜를 갱신한다.

## Sources

> 확인 2026-11-07.

| 근거 | 확정하는 항목 | 인용 |
|---|---|---|
| [App Store Review Guidelines](https://developer.apple.com/app-store/review/guidelines/) 5.1.1(v) | I1 | "If your app supports account creation, you must also offer account deletion within the app" |
| [App Store Review Guidelines](https://developer.apple.com/app-store/review/guidelines/) 3.1.1 | I2 | 디지털 재화의 앱 내 구매 조항. 조사 파일이 인용문 없이 조항 번호만 기록했다. |
| [App Store Review Guidelines](https://developer.apple.com/app-store/review/guidelines/) 3.1.2 | I3 | 구독 조항. 조사 파일이 인용문 없이 범위만 기록했다. |
| [App Privacy Details](https://developer.apple.com/app-store/app-privacy-details/) | I4 | "This information is required to submit new apps and app updates to the App Store." |
| [Privacy manifest files](https://developer.apple.com/documentation/bundleresources/privacy-manifest-files) | I5 | 매니페스트 문서. 조사 파일이 인용문 없이 URL만 기록했다. |
| [App Store Review Guidelines](https://developer.apple.com/app-store/review/guidelines/) 2.1 | I6 | 심사 경로를 다루는 App Completeness 조항. 인용문 없이 기록했다. |
| [App Store Review Guidelines](https://developer.apple.com/app-store/review/guidelines/) 4.2 | I7 | Minimum Functionality 본문 조항: 앱은 웹사이트를 다시 포장한 것을 넘어선다. |
| [App Store Review Guidelines](https://developer.apple.com/app-store/review/guidelines/) 4.2.2 | I7 | 마케팅 자료, 광고, 웹 스크랩, 콘텐츠 수집물, 링크 모음이 주가 되는 앱에 대한 최소 기능 조항. 인용문 없이 기록했다. |
| [Asking permission to use notifications](https://developer.apple.com/documentation/usernotifications/asking-permission-to-use-notifications) | I8 | "Make the request in a context that helps people understand why your app needs authorization." |

### Evidence grade

`QUOTED` - 위 항목과 인용은 수집한 출처에서 가져왔고, 각 출처는 2026-11-07에 열었다. 조항 다섯은 인용문 없이 조항 번호로만 기록되어 있어, 바꿔 말해 인용으로 만들지 않고 그대로 표시했다. 계정 삭제 인용은 지침에서 그 문장을 담고 있는 조항으로 적었다. ID 체계, 등급 정의, 출시 게이트 열, 공유 매트릭스 열은 그 출처를 조합한 이 패키지의 설계다.

날짜가 붙은 값(`I1`-`I8`)은 고정된 사실이 아니라 스토어 정책 값이다. Apple이 지침을 고치면 바뀌므로 확인 날짜가 항목의 일부이고, 재확인 행이 게이트 표의 일부다.
