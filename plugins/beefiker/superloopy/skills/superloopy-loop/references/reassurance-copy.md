# Reassurance-copy reference

Apply this reference only when an affected artifact creates or changes Korean product-behavior copy that a user sees. Do not infer it from prompt keywords. Internal logs, diagnostics, developer documentation, comments, test narration, quotations, general prose, marketing prose, and non-Korean copy are out of scope.

## RC-1: Empty reassurance

Reject unsupported assurances such as `안전하게 처리합니다`, `안심하고 사용하세요`, `정확하게 계산합니다`, and `정확하고 안전하게 진행됩니다`. Replace them with a supplied behavior, measurement, or observable state.

## RC-2: Incomplete failure outcome

A failure message must name at least one supplied reader-relevant fact: the observable outcome, retained state, active fallback, recovery result, or next action. For example, `저장에 실패해도 이전 버전은 안전하게 남습니다` is insufficient without at least one supplied fact from that list. If the fact is unavailable, record it as a blocker or question; never invent a recovery result.

## RC-3: Negative-capability wording

Prefer an affirmative state or next action when the meaning remains intact. Preserve verified privacy or legal commitments, such as `검색어를 서버로 전송하지 않습니다`, and route them to manual review rather than deleting them.

## RC-4: Unsupported reinvention

Every recovery, retention, encryption, privacy, correctness, or safety clause must map to supplied behavior. Plausibility is not support.

## Korean naturalness

Use `humanize-korean` semantic review for misplaced modifiers and collocations. For phrases such as `정확한 컴퓨터`, `정확한 MSI 보드 확인됨`, or `정확한 펌웨어 이미지`, name the supplied target, model identity, specification, measurement, or match. Preserve legitimate phrases such as `정확한 시간`, `정확한 수치`, `정확한 사양`, and `정확한 정보`. Do not reduce this semantic judgment to a keyword or phrase classifier.
