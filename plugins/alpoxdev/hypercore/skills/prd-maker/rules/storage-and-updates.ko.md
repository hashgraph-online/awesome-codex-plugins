# 저장 및 갱신

스킬이 패키지 파일을 생성하거나 갱신할 때 이 규칙 파일을 사용합니다.

## 1. 폴더 위치

각 기획 패키지는 여기에 저장합니다.

`.hyper/prd/[slug]/`

새 패키지의 기본 파일은 기획 체인 순서로 다음과 같습니다.

- `prd.md`
- `feature-spec.md`
- `user-flow.md`
- `wireframe.md`
- `diagram.md`
- `diagram.data.json`
- `diagram.svg`
- `preview.html`
- `sources.md`

복잡 패키지는 다음도 포함합니다.

- `flow.json`

## 2. Slug 규칙

- 짧은 ASCII kebab-case slug를 우선합니다.
- 전체 요청 문장이 아니라 이니셔티브 또는 기능명을 기준으로 slug를 만듭니다.
- 사용자가 같은 주제를 명확히 갱신하는 경우 기존 slug를 재사용합니다.

좋은 예:

- `billing-retry-flow`
- `team-inbox-assignment`
- `ai-planning-assistant`

피할 예:

- 전체 문장 slug
- 날짜가 제품 개념의 일부가 아닌데 날짜를 넣은 slug
- 같은 이니셔티브에 여러 폴더 생성

## 3. 파일 책임

- `prd.md`: 제품 결정 기록과 요구사항 source of truth
- `feature-spec.md`: 기능 동작, 수락 기준, 상태, 권한, 분석, 출시 메모
- `user-flow.md`: 사용자 여정, 분기, 결정 지점, 빈/오류 상태, 진입/종료 지점
- `wireframe.md`: 저충실도 화면 목록, 상태 변형, 레이아웃 블록, 컴포넌트 메모
- `diagram.md`: 시각 기획 맵 설명과 Mermaid/text 원본
- `diagram.data.json`: 결정적 SVG 렌더링을 위한 노드 데이터
- `diagram.svg`: `bash scripts/render-planning-map.sh`가 생성하는 카드/커넥터형 시각 맵
- `preview.html`: `assets/preview.template.html`에서 `bash scripts/build-preview.sh`로 생성하는 로컬 브라우저 뷰어
- `sources.md`: 제공 맥락, 조사 쿼리, 출처 메모, 근거 공백
- `flow.json`: 복잡 패키지만 사용하는 단계 상태

사용자가 명시하지 않았으면 README, notes, changelog 같은 추가 파일을 만들지 않습니다.

## 4. 생성 흐름

폴더가 없을 때는:

- 폴더를 만듭니다.
- 각 마크다운 파일은 대응하는 template asset에서 만들고, `diagram.data.json`은 JSON 템플릿에서 만듭니다.
- 미지수는 조용히 생략하지 말고 명시적 가정 또는 오픈 질문으로 채웁니다.
- PRD → 기능명세서 → 유저플로우 → 와이어프레임 → 다이어그램/미리보기 체인 순서로 작성합니다.
- `bash scripts/render-planning-map.sh`로 `diagram.data.json`에서 `diagram.svg`를 렌더링합니다.
- 패키지 콘텐츠 작성 후 `bash scripts/build-preview.sh`로 `preview.html`을 빌드합니다.
- 복잡 패키지라면 `references/flow-schema.md`에서 `flow.json`을 초기화합니다.

## 5. 갱신 흐름

폴더가 이미 있을 때는:

- 현재 패키지 파일을 먼저 읽습니다.
- 의존 콘텐츠 갱신 전에 누락된 기본 파일을 템플릿에서 추가합니다.
- 바뀐 섹션만 patch합니다.
- 기존 링크, 이전 결정, 유용한 맥락을 보존합니다.
- `prd.md`의 변경 이력 섹션에 날짜 있는 항목을 추가합니다.
- 명백히 낡은 경우가 아니면 이전 근거를 삭제하지 말고 새 조사/맥락을 `sources.md`에 추가합니다.
- PRD의 상위 변경을 기능명세서, 유저플로우, 와이어프레임 순으로 전파합니다.
- 패키지 콘텐츠, 다이어그램 데이터, 출처 로그가 바뀌면 `diagram.svg`와 `preview.html`을 다시 생성합니다.

## 6. 누락 폴더 복구

사용자가 패키지 갱신을 요청했지만 일치하는 폴더가 없으면:

- 새 폴더를 만듭니다.
- 누락된 기준선을 `prd.md` 변경 이력의 가정으로 남깁니다.
- `create` 모드로 계속합니다.

## Sources

> 외부 출처 없음. 내용 확인 2026-09-21.

이 파일은 이 패키지 자체의 저장 위치, 슬러그 규칙, 생성·갱신 절차를 담습니다. 외부 URL을 인용하지 않고 외부 사실을 주장하지 않으므로 외부 출처를 기록하지 않습니다.
