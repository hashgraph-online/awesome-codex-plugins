# Waiver와 Baseline

detector baseline 결과를 사용하거나 waiver를 해석하거나 report-only CI를 문서화할 때 이 규칙을 읽는다.

## Baseline

- baseline은 알려진 정적 finding과 이후 scan을 비교하는 저장된 `detect-slop.sh` v2 JSON 결과다.
- 명시적인 `--baseline <result.json>` 없이 `--only-new`을 사용하지 않는다. 손상되었거나 호환되지 않는 baseline은 비교를 block한다.
- baseline은 debt를 보이게 하는 도구이지 승인 기록이 아니다. 기존 finding을 visual, accessibility, remediation pass로 바꾸지 않는다.
- detector는 baseline을 생성·수정·확장하지 않는다. consumer project가 local baseline file을 소유한다.

예시 report-only 명령이며 이 skill 폴더에서 실행한다.

```bash
bash scripts/detect-slop.sh \
  --target <project>/src --baseline <project>/.ai-slop-remover-baseline.json --only-new --json
```

사용자 또는 프로젝트 authority가 명시하지 않는 한 이 명령으로 CI를 차단하거나 dependency를 설치하거나 project configuration을 수정하지 않는다.

## 좁은 waiver

optional `.ai-slop-remover.json`은 승인된 값 하나 또는 파일 하나의 rule을 기록할 수 있다. 의존하기 전에 `scripts/validate-waivers.sh`로 검증한다.

모든 waiver에는 알려진 `ruleId`, `value` 또는 `file` 중 정확히 하나, 비어 있지 않은 reason, 그리고 `user-confirmed`, `documented-brand`, `fixture`, `generated-output` 중 source가 필요하다. `reviewAfter`가 있으면 absolute `YYYY-MM-DD` 날짜를 쓴다.

waiver는 다음을 절대 하지 않는다.

- configuration을 자동 생성하거나 수정
- 프로젝트 전체의 모든 rule suppress
- P0, protected-contract failure, 미해결 source/behavior defect 숨김
- 예외가 문서화되지 않았을 때 user decision 대체

명시 brand font/gradient에는 value waiver를, generated/exported/deliberate demonstration file에는 file waiver만 우선한다. source-local `ai-slop-disable-next-line <rule> -- <reason>` marker는 portable generated output을 위한 문서화 guidance일 뿐이며, 이 skill은 marker를 자동으로 쓰지 않는다.

## Sources

> 자체 검토 확인 2026-09-21. 외부 출처는 사용하지 않았다.

baseline과 waiver 규칙은 이 패키지 번들 detector와 waiver validator를 위한 자체 계약이다. `ai-slop-disable-next-line` marker 형식은 외부 표준이 아니라 이 패키지가 문서화한 guidance다.
