# [이니셔티브 이름] 기획 다이어그램

> 시각 기획 맵의 canonical source입니다. `diagram.data.json`과 동기화하고 `bash scripts/render-planning-map.sh`로 `diagram.svg`를 렌더링합니다.

## 패키지 링크

- PRD: `./prd.md`
- 기능 명세: `./feature-spec.md`
- 유저 플로우: `./user-flow.md`
- 와이어프레임: `./wireframe.md`
- 출처: `./sources.md`

## 다이어그램

```mermaid
mindmap
  root(([이니셔티브 이름]))
    PRD
      문제
      목표
      범위
      메트릭
    기능 명세
      요구사항
      상태
      수락 기준
    유저 플로우
      진입점
      정상 경로
      예외 케이스
    와이어프레임
      화면
      컴포넌트
      빈/오류 상태
    오픈 질문
      제품
      디자인
      기술
```

## 노드 목록

| Node | Type | Linked artifact | Notes |
|------|------|-----------------|-------|
| [이니셔티브 이름] | root | `prd.md` | 중앙 아이디어 |
| PRD | branch | `prd.md` | 제품 결정 기록 |
| 기능 명세 | branch | `feature-spec.md` | 기능 동작 |
| 유저 플로우 | branch | `user-flow.md` | 여정과 상태 |
| 와이어프레임 | branch | `wireframe.md` | 저충실도 구조 |
| 오픈 질문 | branch | `prd.md` | 미해결 공백 |

## 렌더 메모

- 사용 렌더러: [none / mermaid-cli / other]
- 렌더 파일: [none / `diagram.svg`]
- 마지막 확인: YYYY-MM-DD
