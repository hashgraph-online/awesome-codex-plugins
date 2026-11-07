# 기획 패키지 Flow Schema

> 복잡 기획 패키지에서만 사용하는 `.hyper/prd/[slug]/flow.json`용 JSON schema.

## 목차

- Schema
- Status values
- Rules
- Example: initial state

## Schema

```json
{
  "id": "package-{slug}-{YYYYMMDD-HHmmss}",
  "skill": "prd-maker",
  "mode": "create | update",
  "status": "in_progress | completed | blocked",
  "complexity": "complex",
  "created_at": "ISO8601",
  "updated_at": "ISO8601",
  "slug": "kebab-case-slug",
  "request": {
    "summary": "initiative에 대한 짧은 설명",
    "requester": "알고 있다면 요청자",
    "context": "추가 context"
  },
  "current_phase": "brief | research | prd | diagram | feature_spec | user_flow | wireframe | sources | preview | validate",
  "outputs": {
    "prd": "prd.md",
    "diagram": "diagram.md",
    "diagram_data": "diagram.data.json",
    "diagram_svg": "diagram.svg",
    "preview": "preview.html",
    "feature_spec": "feature-spec.md",
    "user_flow": "user-flow.md",
    "wireframe": "wireframe.md",
    "sources": "sources.md"
  },
  "phases": {
    "brief": {
      "status": "pending | in_progress | completed",
      "product_name": "feature 또는 product 이름",
      "problem": "해결할 문제",
      "target_users": ["혜택을 받는 사용자"],
      "desired_outcome": "business goal",
      "constraints": ["알려진 제약"],
      "unknowns": ["알려진 unknown"]
    },
    "research": {
      "status": "pending | in_progress | completed | skipped",
      "queries": ["사용한 distinct search query"],
      "sources_found": 0,
      "skip_reason": "건너뛰었다면 그 이유"
    },
    "prd": {
      "status": "pending | in_progress | completed",
      "sections_written": ["summary", "problem", "scope", "requirements", "metrics"],
      "open_questions_count": 0
    },
    "diagram": {
      "status": "pending | in_progress | completed",
      "branches_written": ["prd", "feature_spec", "user_flow", "wireframe", "open_questions"],
      "rendered": false,
      "renderer": "scripts/render-planning-map.sh"
    },
    "feature_spec": {
      "status": "pending | in_progress | completed",
      "requirements_mapped": ["R1", "R2"],
      "edge_cases_count": 0
    },
    "user_flow": {
      "status": "pending | in_progress | completed",
      "flows_written": ["happy_path", "alternate_paths", "error_paths"]
    },
    "wireframe": {
      "status": "pending | in_progress | completed",
      "screens_written": ["screen name"],
      "states_covered": ["empty", "loading", "error"]
    },
    "sources": {
      "status": "pending | in_progress | completed",
      "entries_logged": 0
    },
    "preview": {
      "status": "pending | in_progress | completed",
      "built": false,
      "builder": "scripts/build-preview.sh"
    },
    "validate": {
      "status": "pending | in_progress | completed | failed",
      "checks_passed": ["scope_clarity", "cross_artifact_alignment", "sources", "open_questions", "change_history"],
      "checks_failed": [],
      "notes": "검증 세부 사항"
    }
  }
}
```

## Status values

| Status | Meaning |
|--------|---------|
| `pending` | 아직 시작하지 않은 phase |
| `in_progress` | 현재 진행 중인 phase |
| `completed` | 성공적으로 완료된 phase |
| `skipped` | 의도적으로 건너뛴 phase (`research` 전용) |
| `failed` | validation에 실패한 phase (`validate` 전용) |
| `blocked` | 외부 입력을 기다리는 중 (전체 status 전용) |

## Rules

- `current_phase`는 status가 `in_progress` 또는 `pending`인 첫 phase로 설정한다.
- 쓸 때마다 `updated_at`을 갱신한다.
- 모든 phase가 `completed`이거나 의도적으로 `skipped`이면 최상위 `status`를 `completed`로 설정한다.
- `validate`가 실패하면 status를 `failed`로 설정하고 문제를 수정한 뒤 validation을 다시 실행한다.
- `id`는 slug와 생성 timestamp를 결합한다: `package-billing-retry-20260430-100000`.
- `mode`는 package workflow의 `create` 또는 `update`를 반영한다.

## Example: initial state

```json
{
  "id": "package-billing-retry-20260430-100000",
  "skill": "prd-maker",
  "mode": "create",
  "status": "in_progress",
  "complexity": "complex",
  "created_at": "2026-04-30T10:00:00Z",
  "updated_at": "2026-04-30T10:00:00Z",
  "slug": "billing-retry",
  "request": {
    "summary": "Create planning package for automatic billing retry flow",
    "requester": "PM",
    "context": "Current failed payments require manual retry"
  },
  "current_phase": "brief",
  "outputs": {
    "prd": "prd.md",
    "diagram": "diagram.md",
    "diagram_data": "diagram.data.json",
    "diagram_svg": "diagram.svg",
    "preview": "preview.html",
    "feature_spec": "feature-spec.md",
    "user_flow": "user-flow.md",
    "wireframe": "wireframe.md",
    "sources": "sources.md"
  },
  "phases": {
    "brief": { "status": "in_progress" },
    "research": { "status": "pending" },
    "prd": { "status": "pending" },
    "diagram": { "status": "pending" },
    "feature_spec": { "status": "pending" },
    "user_flow": { "status": "pending" },
    "wireframe": { "status": "pending" },
    "sources": { "status": "pending" },
    "preview": { "status": "pending" },
    "validate": { "status": "pending" }
  }
}
```

## Sources

> 외부 출처 없음. 내용 확인 2026-09-21.

이 파일은 이 패키지 자체의 `flow.json` 스키마, 상태 어휘, 단계 규칙을 담습니다. 외부 URL을 인용하지 않고 외부 사실을 주장하지 않으므로 외부 출처를 기록하지 않습니다.
