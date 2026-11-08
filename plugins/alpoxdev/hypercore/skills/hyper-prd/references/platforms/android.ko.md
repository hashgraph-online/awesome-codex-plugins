# Android Platform Checklist

PRD에서 판정한 플랫폼에 `android`가 있을 때만 이 파일을 읽고 플랫폼 요구사항 블록과 그 출시 게이트 표를 채운다. 항목마다 ID, 등급, PRD에 써야 할 문장이나 표, 출처, 확인 날짜가 붙는다. 저장소나 대화에 답이 없는 항목은 PRD에서 `[확인 필요: ...]`가 되고 추측이 되지 않는다.

## Contents

- Grades
- Target API level
- Data safety
- Permissions
- Billing
- Publishing format
- Performance and usability
- Shared data-collection matrix
- Filling the release gate table
- Sources

## Grades

| 등급 | 뜻 | PRD가 져야 할 몫 |
|---|---|---|
| `[M]` | Google Play 정책이나 법이 강제한다. 답이 틀리거나 없으면 출시가 막힌다 | 출시 게이트 표에 결론 하나 |
| `[M-조건]` | 정해진 조건이 성립할 때만 강제된다 | 결론 하나. 해당, 또는 조건을 밝힌 비해당 |
| `[G]` | 권장. 빠져도 스토어가 앱을 거절하지 않는다 | 이 제품에 의미가 있을 때만 적는다 |

이 파일의 `[M]`·`[M-조건]` 항목은 모두 PRD 출시 게이트 표에서 행 하나를 갖는다. 항목의 값은 정책을 옮겨 적은 문장이 아니라 결론이다. `해당`, 이유를 붙인 `비해당`, `[확인 필요]` 중 하나다. "Play 정책을 준수한다" 같은 문장은 결론이 아니며 검토에서 거절된다.

## Target API level

| ID | 등급 | PRD에 적는 내용 | 출처 | 확인 |
|---|---|---|---|---|
| A1 | `[M]` | 빌드가 선언하는 대상 API 레벨(`targetSdk` 값). 첫 출시와 이후 모든 업데이트에 대해 적고, 그 판단을 다시 확인하는 날짜를 붙인다. 2026-08-31부터 새 앱과 앱 업데이트는 Android 16(API 레벨 36) 이상을 대상으로 해야 한다. 그날 전에 내보내는 릴리스는 더 낮은 레벨을 대상으로 할 수 있지만, 어느 경우든 PRD는 레벨을 적는다. | [Target API level](https://support.google.com/googleplay/android-developer/answer/11926878) | 2026-11-07 |

## Data safety

| ID | 등급 | PRD에 적는 내용 | 출처 | 확인 |
|---|---|---|---|---|
| A2 | `[M]` | 작성한 Data safety 신고 내용. 수집이 없는 경우도 포함한다. 앱이 사용자 데이터를 하나도 수집하지 않아도 이 양식은 필수이므로, PRD는 이 항목을 비워 두지 않고 "수집하는 데이터 없음"이라는 신고로 적는다. | [Provide information for Google Play's Data safety section](https://support.google.com/googleplay/android-developer/answer/10787469) | 2026-11-07 |
| A3 | `[M]` | 신고가 이름으로 적은 데이터 유형마다 수집 여부, 제3자 공유 여부, 목적, 선택 여부, 일시 처리 여부. 신고한 집합은 릴리스가 실제로 다루는 집합과 같다. | [Provide information for Google Play's Data safety section](https://support.google.com/googleplay/android-developer/answer/10787469) | 2026-11-07 |

## Permissions

| ID | 등급 | PRD에 적는 내용 | 출처 | 확인 |
|---|---|---|---|---|
| A4 | `[M]` | 권한 목록을 판정하는 규칙. 스토어 등록정보에서 홍보하는 현재 기능이나 서비스를 구현하는 데 필요한 권한만 요청할 수 있다. 계획만 했거나 숨긴 기능을 위한 권한은 정책 위반이므로, PRD는 나중을 위해 권한을 미리 잡아 두지 않는다. | [Permissions and APIs that Access Sensitive Information](https://support.google.com/googleplay/android-developer/answer/9888170) | 2026-11-07 |
| A5 | `[M]` | 런타임 권한마다 행 하나인 대응 표. 권한, 그 권한이 필요한 현재 기능, 그 기능을 홍보하는 등록정보 문구나 스크린샷, 권한 요청이 나오는 화면을 적는다. 같은 행에서 홍보하는 기능이 없는 권한은 범위에서 빼거나 그 기능을 등록정보 계획에 넣는다. | [Permissions and APIs that Access Sensitive Information](https://support.google.com/googleplay/android-developer/answer/9888170) | 2026-11-07 |
| A6 | `[M-조건]` | 조건: 앱이 Play가 민감하거나 제한된 것으로 다루는 권한을 요청한다. 이때 PRD는 선언할 사용 사례와 그 검토 증거를 적는다. 릴리스가 승인되기 전에 선언 내용을 검토하기 때문이다. 그런 권한이 없으면 이 행은 "비해당"으로 적는다. | [Permissions and APIs that Access Sensitive Information](https://support.google.com/googleplay/android-developer/answer/9888170) | 2026-11-07 |

## Billing

| ID | 등급 | PRD에 적는 내용 | 출처 | 확인 |
|---|---|---|---|---|
| A7 | `[M-조건]` | 조건: 앱이 앱 안에서 디지털 재화나 디지털 서비스를 판매한다. 이때 PRD는 구매가 Play 결제 시스템을 거친다고 적고, 유료 항목마다 가격, 결제 주기, 구매자가 받는 것을 나열한다. 실물 상품, 실물 서비스, 앱 밖에서 소비하는 콘텐츠는 이 행의 범위 밖이며 그렇다고 적는다. | [Payments policy](https://support.google.com/googleplay/android-developer/answer/10281818), [Play Billing integration](https://developer.android.com/google/play/billing/integrate) | 2026-11-07 |
| A8 | `[M-조건]` | 조건: 앱이 Play Billing을 쓴다. 이때 Billing Library 버전은 8 이상이다. 2026-08-31까지 새 앱과 기존 앱의 업데이트가 모두 버전 8 이상을 써야 하기 때문이다. PRD는 고른 버전과 그 판단을 다시 확인하는 날짜를 적는다. | [Play Billing integration](https://developer.android.com/google/play/billing/integrate) | 2026-11-07 |

## Publishing format

| ID | 등급 | PRD에 적는 내용 | 출처 | 확인 |
|---|---|---|---|---|
| A9 | `[M]` | 배포 산출물 형식. APK가 아니라 Android App Bundle(AAB, `.aab`)을 Play에 올린다. 크기나 기능 목표 때문에 앱이 기대는 배포 분할이 있으면 함께 적는다. | [Android App Bundles](https://developer.android.com/guide/app-bundle) | 2026-11-07 |

## Performance and usability

| ID | 등급 | PRD에 적는 내용 | 출처 | 확인 |
|---|---|---|---|---|
| A10 | `[G]` | 안정성 하한과 그 읽는 방법. 사용자 체감 크래시 비율 1.09% 이하, ANR 비율 0.47% 이하. Play가 앱 버전에 대해 보여 주는 나쁜 동작 임계값이다. 측정 방법: Play Console > Android vitals에서 앱 버전별로, 콘솔이 보여 주는 보고 기간 동안 읽는다. PRD는 분모를 기억으로 다시 쓰지 않고 콘솔의 지표 이름을 그대로 옮긴다. | [Android vitals](https://developer.android.com/topic/performance/vitals) | 2026-11-07 |
| A11 | `[G]` | 모든 상호작용 컨트롤의 터치 타깃이 48 dp 이상이라는 문장. 측정 방법: 기기나 레이아웃 검사기에서 컨트롤마다 dp 단위 레이아웃 경계를 읽고, 작은 화면 크기 하나와 큰 화면 크기 하나에서 확인한다. 48 dp보다 작은 타깃은 컨트롤 이름과 계획한 크기와 함께 적는다. | [Core app quality](https://developer.android.com/docs/quality-guidelines/core-app-quality) | 2026-11-07 |

수치 항목은 세 가지를 적는다. 단위가 붙은 임계값, 그 수치를 만드는 측정 방법, 그 수치가 덮는 모집단이나 기간. 분위수 기반 지표는 분위수를 적는다(`@p75`). 여기 있는 vitals 임계값 둘은 콘솔 보고 기간에 대한 비율이라 분위수가 아니므로 기간을 적는다. 세 가지 없이 "안정적"이나 "충분히 큼"으로 쓴 항목은 요구사항이 아니다.

수집한 출처에는 이 Play 페이지들의 조항 번호가 기록되지 않았으므로 각 행은 페이지 제목과 URL로 근거를 밝히고 구속하는 문장을 함께 인용한다. 페이지 제목만으로는 규칙이 무엇인지 말해 주지 않는다.

## Shared data-collection matrix

판정한 플랫폼에 iOS와 Android가 함께 있으면 매트릭스를 한 번만 쓰고 두 방향에서 읽는다. 두 번 쓰면 두 서술이 어긋나고, 같은 동작에 대해 두 스토어가 다른 설명을 받게 된다.

| 데이터 유형 | 수집 | 제3자 공유 | 사용자 신원 연결 | 추적 사용 | 목적 | 선택 여부 | 일시 처리 |
|---|---|---|---|---|---|---|---|

- iOS 프라이버시 라벨 행과 Play Data safety 행이 모두 이 표에서 나온다. 어느 쪽도 데이터 유형을 기억으로 다시 쓰지 않는다.
- 한 플랫폼은 수집하고 다른 플랫폼은 수집하지 않는 데이터 유형은 신고 세부가 아니라 제품 판단이다. 그 차이와 이유를 PRD에 적는다.
- 릴리스가 다루는데 표에 없는 유형은 표의 결함이다. 두 스토어 양식을 채우기 전에 표를 고친다.

## Filling the release gate table

| 열 | 내용 |
|---|---|
| ID | 이 파일의 항목 ID. 예: `A1` |
| 등급 | 이 파일의 등급을 바꾸지 않고 옮긴다 |
| 항목 | 의무를 짧은 문장 하나로 쓴다. 수치 항목이면 임계값, 측정 방법, 분위수를 함께 쓴다 |
| 결론 | `해당`, 조건이나 이유를 붙인 `비해당`, `[확인 필요: <질문>]` 중 하나 |
| 근거 | 결론을 확정하는 문서, 콘솔 화면, 측정 |
| 재확인 | 날짜가 붙은 값을 다시 확인하는 날짜. 날짜가 없는 항목은 `none` |

결론이 `[확인 필요]`인 `[M]` 행이 있으면 PRD는 `status: draft`를 유지한다. 이 파일의 날짜가 붙은 값은 스토어 정책 값이다. Google Play가 정책을 고치면 함께 바뀌므로, 날짜가 붙은 행은 분기마다 그리고 스토어 공지가 있을 때마다 다시 확인한다.

## Sources

> 확인 2026-11-07.

| 출처 | 확정하는 항목 | 인용 |
|---|---|---|
| [Target API level](https://support.google.com/googleplay/android-developer/answer/11926878) | A1 | "Starting August 31, 2026: New apps and app updates must target Android 16 (API level 36) or higher" |
| [Data safety](https://support.google.com/googleplay/android-developer/answer/10787469) | A2, A3 | "Even developers with apps that do not collect any user data must complete this form" |
| [Permissions and APIs that Access Sensitive Information](https://support.google.com/googleplay/android-developer/answer/9888170) | A4, A5, A6 | "You may only request permissions ... that are necessary to implement current features or services in your app that are promoted in your Google Play listing." |
| [Payments policy](https://support.google.com/googleplay/android-developer/answer/10281818) | A7 | 앱 안 디지털 재화 정책 페이지. 조사 파일은 인용 없이 URL만 기록했다. |
| [Play Billing integration](https://developer.android.com/google/play/billing/integrate) | A7, A8 | "By Aug 31, 2026, all new apps and app updates to existing apps must use Billing Library version 8 or later." |
| [Android App Bundles](https://developer.android.com/guide/app-bundle) | A9 | 배포 형식 페이지. 조사 파일은 인용 없이 URL만 기록했다. |
| [Android vitals](https://developer.android.com/topic/performance/vitals) | A10 | 나쁜 동작 임계값: 사용자 체감 크래시 비율 1.09%, ANR 비율 0.47%. |
| [Core app quality](https://developer.android.com/docs/quality-guidelines/core-app-quality) | A11 | "Touch targets are at least 48 dp." |

### Evidence grade

`QUOTED` - 위 항목과 인용은 수집한 출처에서 가져왔고, 각 출처는 2026-11-07에 열었다. 인용 없이 URL만 기록된 페이지 둘은 그렇게 표시했고 인용문으로 바꿔 쓰지 않았다. ID 체계, 등급 정의, 출시 게이트 열, 공유 매트릭스 열은 그 출처들을 조합한 이 패키지의 설계다.

날짜가 붙은 값(`A1`, `A8`)은 고정된 사실이 아니라 스토어 정책 값이다. Google Play가 정책을 고치면 함께 바뀌므로 확인 날짜가 항목의 일부이고 재확인 행이 게이트 표의 일부다.
