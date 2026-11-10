# 영수증

첫 발송 전과 반환된 영수증을 검증할 때 이 파일을 읽는다. 모든 영수증, 원장, 승인 기록의 정확한 형식을 맡는다.

모든 영수증은 `.hyper/debate/<slug>/` 아래 JSON 파일이고, 라운드마다 관점마다 하나다. 할당에 그 라운드의 스키마를 그대로 넣어 관점이 추측하지 않게 한다.

## Contents

1. Common rules
2. Round 1 receipt
3. Round 2 receipt
4. Round 3 receipt
5. Ledger
6. Approval record
7. Validation checklist

## 1. 공통 규칙

- 관점마다 라운드마다 파일 하나다. `round1/<perspective>.json`, `round2/<perspective>.json`, `round3/<perspective>.json`.
- 관점 id는 정확히 `skeptic`, `validator`, `researcher`, `architect`, `creative`다.
- 모든 영수증은 `perspective`와 `round`를 적는다. 신원이 할당과 맞지 않는 영수증은 내용이 좋아도 무효다.
- 모든 중첩 객체는 추가 속성을 금지한다. 여분 키는 관점이 필드를 지어냈다는 뜻이므로 영수증을 거절한다.
- 인용은 `path:line`, 공식 URL, `user: <인용문>`, `no evidence found` 중 하나다. 지어낸 인용은 발견을 무효로 만든다.
- 영수증 안의 산문은 한국어가 기본이다. id, 판정, 필드 이름은 영어로 둔다.

## 2. 1라운드 영수증

```json
{
  "type": "object",
  "properties": {
    "perspective": {"type": "string", "enum": ["skeptic", "validator", "researcher", "architect", "creative"]},
    "round": {"type": "integer", "enum": [1]},
    "findings": {
      "type": "array", "minItems": 3, "maxItems": 7,
      "items": {
        "type": "object",
        "properties": {
          "id": {"type": "string"},
          "claim": {"type": "string"},
          "evidence": {"type": "array", "minItems": 1, "items": {"type": "string"}}
        },
        "required": ["id", "claim", "evidence"], "additionalProperties": false
      }
    }
  },
  "required": ["perspective", "round", "findings"], "additionalProperties": false
}
```

반환 시 확인: 발견 3~7개, 관점 접두사가 붙은 id, 발견마다 인용 문자열 하나 이상, 실행 전체에서 중복 id 없음.

## 3. 2라운드 영수증

```json
{
  "type": "object",
  "properties": {
    "perspective": {"type": "string", "enum": ["skeptic", "validator", "researcher", "architect", "creative"]},
    "round": {"type": "integer", "enum": [2]},
    "critiques": {
      "type": "array", "minItems": 1,
      "items": {
        "type": "object",
        "properties": {
          "targetFindingId": {"type": "string"},
          "verdict": {"type": "string", "enum": ["ATTACK", "STANDS"]},
          "reason": {"type": "string"},
          "evidence": {"type": "array", "minItems": 1, "items": {"type": "string"}}
        },
        "required": ["targetFindingId", "verdict", "reason", "evidence"], "additionalProperties": false
      }
    }
  },
  "required": ["perspective", "round", "critiques"], "additionalProperties": false
}
```

반환 시 확인. 영수증마다 나머지 네 관점의 발견 전부에 판정이 정확히 하나씩 있고, 알 수 없는 대상 id가 없고, 자기 판정이 없고, 모든 `STANDS`에 이유가 비어 있지 않다.

## 4. 3라운드 영수증

```json
{
  "type": "object",
  "properties": {
    "perspective": {"type": "string", "enum": ["skeptic", "validator", "researcher", "architect", "creative"]},
    "round": {"type": "integer", "enum": [3]},
    "responses": {
      "type": "array", "minItems": 3, "maxItems": 7,
      "items": {
        "type": "object",
        "properties": {
          "findingId": {"type": "string"},
          "verdict": {"type": "string", "enum": ["DEFEND", "REFINE", "CONCEDE"]},
          "survivingClaim": {"type": ["string", "null"]},
          "reason": {"type": "string"},
          "evidence": {"type": "array", "items": {"type": "string"}}
        },
        "required": ["findingId", "verdict", "survivingClaim", "reason", "evidence"], "additionalProperties": false
      }
    }
  },
  "required": ["perspective", "round", "responses"], "additionalProperties": false
}
```

반환 시 확인: 자기 발견마다 응답 하나, `DEFEND`와 `REFINE`은 비어 있지 않은 `survivingClaim`과 비어 있지 않은 `evidence`, `CONCEDE`는 null `survivingClaim`. `reason`은 그 발견에 기록된 모든 공격을 다룬다.

## 5. 원장

`.hyper/debate/<slug>/ledger.json`은 JSON 객체 하나다. 마지막에 한 번이 아니라 점진적으로 쓴다.

```json
{
  "request": {"verbatim": "", "optIn": "", "scope": [], "outcome": ""},
  "slug": "",
  "mode": "full | bundle-only | review",
  "execution": "parallel | sequential",
  "reduced": false,
  "reducedReason": null,
  "grounding": [{"path": "", "note": ""}],
  "waves": [
    {"round": 1, "perspectives": [{"id": "skeptic", "job": "", "attempt": 1, "receipt": "round1/skeptic.json"}]}
  ],
  "findings": [
    {
      "id": "skeptic-1",
      "perspective": "skeptic",
      "claim": "",
      "evidence": [""],
      "critiques": [{"by": "validator", "verdict": "ATTACK", "reason": ""}],
      "response": {"verdict": "REFINE", "survivingClaim": "", "reason": ""},
      "decision": "keep | refine | open-question | drop",
      "decisionReason": ""
    }
  ],
  "surviving": {"skeptic": 0, "validator": 0, "researcher": 0, "architect": 0, "creative": 0},
  "dropped": {"skeptic": 0, "validator": 0, "researcher": 0, "architect": 0, "creative": 0},
  "openQuestions": [{"question": "", "why": "", "gates": []}],
  "approval": {"requestedAt": "", "request": "", "decidedAt": null, "decision": null},
  "terminal": "planned | awaiting-approval | reduced-planned | declined | blocked",
  "notes": []
}
```

## 6. 승인 기록

승인 요청과 응답은 원장의 `approval`에 있고, 제시한 본문은 `.hyper/debate/<slug>/approval.md`에 저장해 읽는 사람이 무엇이 승인됐는지 정확히 볼 수 있게 한다.

```markdown
# <slug> - Approval

## Decisions presented
- <decision>

## Risks and mitigations
- <risk> -> <mitigation>

## Open questions
- <question> -> <who must decide>

## Asked
<the exact question put to the user>

## Decision
<the user's answer, verbatim, or `no answer`>
```

`## Decision` 본문이 비었거나 없으면 승인이 아니다.

## 7. 검증 체크리스트

어떤 라운드를 넘어가기 전:

- [ ] 그 라운드의 영수증 다섯 개가 있고 관점마다 하나다.
- [ ] 각 영수증의 `perspective`와 `round`가 파일 이름 및 할당과 맞는다.
- [ ] 스키마 밖 키를 가진 영수증이 없다.
- [ ] 1라운드: 각 3~7개 발견, 모든 발견에 인용, 실행 전체에서 id 고유.
- [ ] 2라운드: 다른 관점 발견 전체 커버리지, 자기 판정 없음, 알 수 없는 id 없음, 모든 `STANDS`에 이유.
- [ ] 3라운드: 자기 발견마다 응답 하나, 모든 `DEFEND`/`REFINE`에 근거, 모든 `CONCEDE`에 null 주장, 모든 공격 처리.
- [ ] 원장에 웨이브 식별자, 시도 번호, 영수증 경로가 있다.

## Sources

> Checked 2026-11-10.

| Claim | Source |
|---|---|
| 1~3라운드 영수증 스키마 | `dbc-hbin/omp-ulw@74df40f hyperplan/references/rounds.md` (메커니즘 참조, 재작성) |
| 2라운드는 스키마보다 커버리지를 보고, 3라운드는 자기 발견을 검사한다 | `dbc-hbin/omp-ulw@74df40f hyperplan/references/rounds.md` (메커니즘 참조, 재작성) |
| 원장 필드, 승인 기록, 검증 체크리스트 | 이 패키지의 설계, 2026-11-10 (issue #26) |

### Evidence grade

`LOCAL` - 스키마는 라이선스가 없는 저장소에서 재작성했고 텍스트나 코드를 복사하지 않았다. 원장, 승인 기록, 체크리스트는 이 패키지의 설계다.
