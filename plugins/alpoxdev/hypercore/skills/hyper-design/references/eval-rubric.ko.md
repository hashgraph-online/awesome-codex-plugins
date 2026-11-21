# 평가 루브릭

`assets/evals/` case를 추가·검토·해석할 때 이 참고 문서를 읽는다.

## Detector oracle

각 detector rule에는 최소 positive fixture와 false-positive guard fixture가 필요하다. 관찰 가능한 기계 출력만 검증한다.

- rule ID, 소스 위치, severity, engine, evidence kind
- 명시적 로컬 맥락이 뒷받침할 때의 candidate exception status
- guard fixture가 증명해야 하는 finding의 부재
- 관련 없는 rule 추가가 count를 바꾸지 않을 때만 stable summary count

소스 match만으로 visual quality, accessibility conformance, 제품 적합성, AI 저작 여부를 판정하지 않는다.

## Workflow oracle

workflow JSONL case는 trigger, mode, 보호 계약, browser capability fallback, unsafe request를 다룬다. 각 case는 필요한 행동과 금지 결과를 명시한다. 기존 case는 유지하고 실제 실패가 발견되면 regression을 추가한다.

## Human sampling

정적 rule을 `P1` 또는 immediate tier로 올리기 전 relevant example 5개와 exception-like example 5개 이상을 확인한다. confirmed, false-positive, ambiguous 결과를 기록한다. 검토 표본의 false positive가 10%를 넘으면 rule은 review-only로 유지하거나 제거한다.

## 결과 경계

- 정적 detector 출력은 source signature만 증명한다.
- rendered evidence에는 유효한 browser handoff capture가 필요하다.
- screenshot evidence는 keyboard, semantic, accessibility, task completion을 증명하지 않는다.
- `generic-output risk`는 우선순위 label일 뿐 AI 저작 주장에 쓰지 않는다.

## Sources

> 자체 검토 확인 2026-09-21. 외부 출처는 사용하지 않았다.

detector, workflow, human sampling 기준은 이 패키지 자체 것이다. 10% false-positive 임계값과 5개 표본 크기는 외부 지침이 아니라 이 패키지가 정한 값이다.
