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

## 프로젝트 설정

`--config <file.json>`은 프로젝트 설정 문서 하나를 detector에 지정하며, 이 문서는 `assets/detector-config.schema.json`으로 검증한다. 파일은 선택이며, 없으면 detector는 이전과 똑같이 동작한다.

```json
{
  "version": 1,
  "rules": { "surface.radial-glow": "off", "copy.cliche": "P1" },
  "allowFonts": ["BrandMono"],
  "allowEasings": ["cubic-bezier(0.2, 0.6, 0.2, 1)"],
  "designTokens": { "--brand-mono": "BrandMono" }
}
```

- `rules`는 rule id를 `off`, `P1`, `P2`, `P3` 중 하나로 대응한다. `off`는 그 rule을 검사에서 빼고, severity 값은 report에서 registry 기본값을 대체한다.
- `--rules <id,id>`는 한 번의 실행을 지정한 rule id로 좁히고 모르는 id에서는 exit 2로 끝난다. 이 flag는 선택만 하며, 설정이 `off`로 끈 rule을 되살리지는 않는다. 어떤 id가 존재하는지는 catalog의 Static 열이 정한다. 등록되는 것은 `yes`와 `partial` 행뿐이다(`references/anti-pattern-catalog.md`).
- `motion.missing-reduced-motion`은 파일별이 아니라 스캔 전체를 보는 프로젝트 단위 rule이다. 다른 id와 똑같이 선택, 비활성화, severity override가 된다.
- `allowFonts`, `allowEasings`, `designTokens`는 허용 목록이다. 일치한 evidence 조각에 허용 값이 들어 있으면 그 finding은 findings 목록 대신 skipped 개수로 옮긴다.
- markup 요소의 `data-detect-ignore="<rule-id>"`(또는 `*`)는 그 요소 구간을 지정한 rule에서 제외한다. 해당 hit은 skipped 개수로 옮겨 예외가 드러나게 한다.
- JSON report는 `--config`를 쓴 경우에만 최상위 `skipped` 개수를 담는다.
- 잘못된 설정은 schema 오류와 함께 exit 2로 끝나며 rule을 하나도 실행하지 않는다. 파일이 없거나 JSON이 깨져도 같은 방식으로 exit 2다.

설정은 waiver가 아니다. 설정은 프로젝트가 요청한 범위를 바꾸고, waiver는 출처와 이유를 붙여 승인된 예외 하나를 기록한다. 설정 파일은 P0를 숨기거나 protected-contract failure을 가리거나 사용자 결정을 대체하지 않는다.

## Sources

> 확인 2026-11-09.

| 주장 | 출처 |
|---|---|
| slop detector의 rule별 severity override, font·easing 허용 목록, design token 허용 목록, 요소별 ignore 속성 | `dbc-hbin/omp-ulw @ 74df40f` (2026-11-09), 이 패키지 자체 문장으로 재작성했다. 원본 저장소에는 라이선스가 없으며 텍스트나 코드를 복사하지 않았다. |
| baseline과 waiver 규칙, `off\|P1\|P2\|P3` 값 집합, `skipped` report field | 이 패키지 번들 detector와 waiver validator를 위한 자체 계약 |

### Evidence grade

메커니즘 아이디어는 라이선스가 없는 참조에서 가져와 이 패키지에서 다시 구현했으며 텍스트나 코드를 재사용하지 않았다. schema, 값 집합, `skipped` field는 이 패키지 자체 계약이며 `assets/evals/detector-cases.jsonl`에서 검증한다.
