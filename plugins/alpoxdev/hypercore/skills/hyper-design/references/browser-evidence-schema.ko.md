# Browser Evidence Handoff Schema

이미 사용 가능한 browser capability가 수집한 evidence를 제공할 때만 이 schema를 사용한다. collector는 input을 검증하며 browser를 열지 않는다.

```json
{
  "version": 1,
  "surface": "http://localhost:3000/settings",
  "captures": [
    {
      "viewport": { "width": 375, "height": 800 },
      "state": "default",
      "capturedAt": "2026-08-29T12:00:00Z",
      "stressString": "supercalifragilisticexpialidocious",
      "observations": [
        {
          "locator": "button[type=submit]",
          "rect": { "x": 16, "y": 600, "width": 343, "height": 44 },
          "textRect": { "x": 32, "y": 612, "width": 200, "height": 20 },
          "role": "control",
          "fontSizePx": 16,
          "gapAbovePx": 24,
          "overflowX": false,
          "contrastPairs": [
            { "label": "label-on-surface", "foreground": "#000000", "background": "#ffffff" }
          ],
          "focusVisible": true,
          "computed": { "fontSize": "16px", "color": "#000000", "backgroundColor": "#ffffff" }
        }
      ]
    }
  ]
}
```

`state`는 `default`, `hover`, `focus`, `active`, `disabled`, `loading`, `empty`, `error` 중 하나다. `computed`에는 string primitive value만 넣는다. `screenshot`은 optional metadata이며 accessibility나 behavior의 증거가 아니다.

## Measurement fields

measurement-capable renderer가 만드는 field이며, `collect-rendered-evidence.sh`가 사용한다:

- `computed.foreground`(또는 `color`)와 `computed.background`(또는 `backgroundColor`): 칠해진 텍스트·배경 pair이며 `#rgb` 또는 `#rrggbb` hex로 기록한다. collector는 WCAG ratio를 계산하며 4.5 미만이면 failing 처리한다.
- `contrastPairs`: 추가 pair이며 `{label, foreground, background}` object로 기록하고 같은 방식으로 측정한다.
- `fontSizePx`(또는 `measuredFontSize`): observation role의 computed font size를 CSS px로 기록한다.
- `gapAbovePx`: element 위쪽 vertical gap을 CSS px로 기록한다.
- `textRect`: text box rectangle이다. collector는 같은 capture 안의 서로 다른 observation에 속한 `textRect`끼리 비교하며 4px 초과 overlap을 failing으로 처리한다. 자기 container 안에 있는 text box는 overlap이 아니다.
- `overflowX`: `false`(overflow 없음) 또는 viewport edge를 넘은 CSS px 수 중 하나이며, number가 2를 초과하면 capture width에서 failing 처리한다.
- `stressString`(capture): overflow 측정 시 함께 놓인 끊기지 않은 string이다.

어떤 measurement field도 없는 observation은 `measurements.status: "not_run"`으로 보고되며, 이는 절대 pass가 되지 않는다. 전체 정의와 threshold는 `rendered-measurements.md`를 참조한다.

## Sources

> 자체 검토 확인 2026-09-21. 외부 출처는 사용하지 않았다.

handoff schema는 이 패키지 자체 JSON 계약이며 collector와 fixture가 이를 강제한다. measurement field는 이 패키지 계약을 `dbc-hbin/omp-ulw @ 74df40f`의 텍스트나 코드를 복사하지 않고 재작성한 field로 확장한 것이며, threshold는 `rendered-measurements.md`를 따른다. 예시 값은 외부 서비스에서 가져온 데이터가 아니라 설명용이다.
