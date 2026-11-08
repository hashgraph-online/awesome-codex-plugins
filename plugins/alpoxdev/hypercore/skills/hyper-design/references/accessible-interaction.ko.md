# 접근 가능한 상호작용

쓰기 모드가 컨트롤, 폼, 대화상자, 탭, 동적 콘텐츠를 만들거나 고칠 때, 그리고 감사 발견 사항이 컨트롤의 역할, 이름, 상태, 키보드 사용에 관한 것일 때 읽는다. 각 항목은 단서, 이유, 수정이다. 코드는 프로젝트 스택에 맞게 고쳐 쓰는 시작 형태이지 붙여 넣는 라이브러리가 아니다.

## 목차

- 1. 조작 단서
- 2. 키보드와 포커스
- 3. 폼과 오류
- 4. 동적 콘텐츠
- 5. 문서 전체
- 6. 코드 형태

## 1. 조작 단서

| 단서 | 이유 | 수정 |
|---|---|---|
| 버튼, `summary`, 체크박스 레이블, `[role="button"]`이 화살표 커서를 유지한다(흔히 CSS 초기화가 `button { cursor: default }`를 설정한 뒤) | 화살표는 "이것은 텍스트"라고 말한다. 사람은 망설이거나 아예 누르지 않는다 | 초기화 뒤 기본 규칙 하나로 켜진 모든 컨트롤에 `cursor: pointer`, 비활성 컨트롤에 `cursor: not-allowed`를 준다(§6.1). 아무것도 하지 않는 요소에는 절대 주지 않는다 |
| `<div onClick>`, `<span onClick>`, `href` 없는 `<a>`, 동작에 쓴 `<a href="#" onClick>` | 역할이 없어 스크린 리더가 컨트롤로 알리지 않고 키보드가 건너뛴다 | 동작은 `<button type="button">`, 이동은 실제 목적지로 가는 `<a href>`다. 네이티브로 만들 수 없는 직접 만든 컨트롤에는 역할, 상태 속성, 완전한 키보드 지원을 준다 |
| 글자 없는 아이콘 전용 닫기, 메뉴, 검색, 소셜 버튼 | 스크린 리더가 "버튼"만 읽고 음성 제어가 이름을 부를 수 없다 | 보이는 의미와 일치하는 `aria-label`이나 시각적으로 숨긴 텍스트를 주고 아이콘에 `aria-hidden="true"`를 준다 |
| 컨트롤이 정지, hover, 눌림, 비활성에서 똑같이 보이고 회색으로 죽인 버튼도 여전히 동작한다 | 동작이 접수됐다는 피드백이 없고 비활성 컨트롤은 고장 난 것처럼 보인다 | 서로 다른 `:hover`, `:active`, `:focus-visible`, 비활성 스타일을 3:1까지 맞춰 준다. `disabled` 속성을 우선하고 포커스를 유지해야 할 때는 `aria-disabled="true"`와 코드 수준 차단을 쓴다 |
| 상태를 색으로만 표시한다. 빨간 테두리, 초록 칩 | 색각 이상 사용자를 배제하고 강제 색상 모드에서 사라진다 | 모든 색 신호에 텍스트나 아이콘을 함께 준다. 오류 텍스트가 먼저다 |
| 끌기만으로 순서를 바꾸거나 크기를 조정하거나 값을 고른다 | 끌 수 없는 사람에게는 실패한다(WCAG 2.5.7) | 클릭, 탭, 키보드 경로를 준다. 위로·아래로 이동 버튼, 슬라이더 옆 숫자 입력 |

## 2. 키보드와 포커스

| 단서 | 이유 | 수정 |
|---|---|---|
| 대체 없이 `outline: none` | 키보드 사용자가 자기 위치를 잃는다 | 모든 테마에서 이웃 색 대비 3:1의 `:focus-visible` 스타일 |
| 메뉴가 hover로만 열리고, 드롭다운이 클릭으로는 열리지만 키보드로는 열리지 않는다 | 키보드와 터치 사용자에게 그 컨트롤은 없는 것이다 | 모든 상호작용 요소가 Tab, Shift+Tab, Enter, Space로 동작한다. 대화상자는 Escape로 닫힌다 |
| DOM 순서와 시각 순서가 달라 포커스가 튄다 | 이동이 예측 불가능하다 | 소스 순서를 시각 순서와 같게 유지한다. 긴 페이지에는 건너뛰기 링크를 넣고(§6.2), 실제 콘텐츠에 `tabindex="-1"`은 통제된 포커스 대상 안에서만 준다 |
| 직접 만든 모달에서 Tab이 뒤로 빠져나간다 | 키보드 사용자가 숨은 페이지로 간다 | 포커스를 가두고 Escape로 닫는 네이티브 `<dialog>`와 `showModal()`을 우선한다. 닫을 때 포커스를 연 요소로 돌려준다 |
| 역할 없는 평범한 버튼으로 만든 탭 | 스크린 리더가 어느 패널이 보이는지 알 수 없다 | `role="tablist"`, `aria-selected`와 `aria-controls`가 있는 `role="tab"`, `role="tabpanel"`. 화살표 키로 탭 사이를 옮기고 활성 탭은 `tabindex="0"`, 나머지는 `-1`이다 |

## 3. 폼과 오류

- 모든 필드에 보이는 `<label for>`(또는 감싸는 레이블)가 있다. placeholder는 힌트이지 레이블이 아니다. 개인 정보에는 `autocomplete` 토큰을 쓴다.
- 입력 전에 적용되는 안내는 필드 위나 옆에 두고 `aria-describedby`로 연결한다.
- 검증은 제출할 때나 사용자가 바꾼 필드를 벗어날 때 하고 포커스를 받을 때는 하지 않는다. 필드에 `aria-invalid="true"`를 표시하고 메시지를 옆에 보여 주며 입력을 보존하고 고치는 방법을 평이한 말로 쓴다.
- 필드가 여럿인 폼은 제출할 때 위쪽에 오류 요약을 보여 주고 포커스를 옮기며 각 줄을 해당 필드로 연결한다. 문구는 인라인 메시지와 같게 쓴다.
- 휴대폰에서 포커스를 받은 필드는 화면 키보드 위로 스크롤되어 보인다. 키보드가 필드를 가리지 않도록 아래 여백을 충분히 둔다.

## 4. 동적 콘텐츠

- 페이지를 다시 불러오지 않고 바뀌는 내용(저장 토스트, 결과 개수, 업로드 완료)은 변화 전에 존재하는 라이브 영역으로 알린다. 상태에는 `aria-live="polite"`, 긴급 오류에만 `role="alert"`를 쓴다.
- 라이브 영역을 비운 뒤 다음 프레임에 새 텍스트를 써야 같은 메시지를 반복해도 다시 알린다.
- 로딩 텍스트는 무엇을 불러오는지 말한다("청구서를 불러오는 중"). 스피너만 두지 않는다.

## 5. 문서 전체

작업이 전체 페이지나 앱 셸을 만들 때만 적용하고 단일 컴포넌트에는 적용하지 않는다.

- `<html lang>`을 콘텐츠 언어로 설정하고 고유한 `<title>`과 랜드마크(`header`, `nav`, `main`, `footer`)를 둔다.
- `h1`은 하나이고 제목 수준을 건너뛰지 않는다.
- viewport meta가 확대를 막지 않는다.

## 6. 코드 형태

### 6.1 포인터 커서 기본 계층

```css
@layer base {
  :where(a[href], button, summary, select, label[for],
         input:is([type="checkbox"], [type="radio"], [type="file"], [type="range"],
                  [type="color"], [type="submit"], [type="button"], [type="reset"]),
         [role="button"], [role="link"], [role="tab"], [role="switch"],
         [role="menuitem"], [role="option"]) {
    cursor: pointer;
  }
  :where(label:has(> input:is([type="checkbox"], [type="radio"]))) { cursor: pointer; }
  :where(:disabled, [aria-disabled="true"]) { cursor: not-allowed; }
}
```

텍스트 입력은 `cursor: text`를 유지하고 끌기 손잡이는 `grab`과 `grabbing`을 쓴다. Tailwind에서는 preflight 계층 뒤에 둔다.

### 6.2 건너뛰기 링크

```html
<a class="skip-link" href="#main">Skip to content</a>
<main id="main" tabindex="-1">…</main>
```

```css
.skip-link { position: absolute; inset-inline-start: 0.5rem; translate: 0 -200%; }
.skip-link:focus-visible { translate: 0 0.5rem; }
```

### 6.3 네이티브 대화상자

```html
<button type="button" aria-haspopup="dialog" aria-controls="rename">Rename</button>
<dialog id="rename" aria-labelledby="rename-title">
  <h2 id="rename-title">Rename project</h2>
  <form method="dialog">
    <label for="rename-name">Name</label>
    <input id="rename-name" name="name" required>
    <button value="cancel" formnovalidate>Cancel</button>
    <button value="save">Save</button>
  </form>
</dialog>
```

`dialog.showModal()`로 열면 포커스가 갇히고 Escape로 닫힌다. `close` 이벤트에서 포커스를 연 요소로 돌려놓는다.

## Sources

> 확인 2026-11-07.

| 주장 | 출처 |
|---|---|
| 조작 단서 항목(포인터 커서 기본 계층, 네이티브 요소, 접근 가능한 이름, 서로 다른 상태, 색만 쓰는 피드백, 문서 전체에만 적용하는 페이지 의미 구조)과 패턴 목록(포커스 가둠, 건너뛰기 링크, 오류 처리, 레이블, 끌기 대안, 탭, 라이브 영역) | <https://github.com/miqdadbadjuber/anti-slop> (commit `9504989`, `antislop-human/SKILL.md` and its `references/A11Y-PATTERNS.md`; MIT, Copyright 2026 Miqdad Badjuber; the patterns file is adapted from <https://github.com/addyosmani/web-quality-skills>, MIT, Copyright 2026 Addy Osmani). §6의 코드는 원본에서 복사하지 않고 이 패키지용으로 작성했다. |
| 이름, 역할, 값; 키보드 조작성; 포커스 표시; 끌기 동작; 상태 메시지 | <https://www.w3.org/TR/2024/REC-WCAG22-20241212/> (SC 4.1.2, 2.1.1, 2.4.7, 2.5.7, 4.1.3) |
| 네이티브 `dialog` 요소는 `showModal()`에서 포커스를 가두고 Escape로 닫힌다 | <https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/dialog> |

### Evidence grade

WCAG 기준은 규범이다. 포인터 커서 규칙은 널리 쓰는 관례이지 WCAG 요구 사항이 아니며 기본값으로 둔다.
