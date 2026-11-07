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
      "observations": [
        {
          "locator": "button[type=submit]",
          "rect": { "x": 16, "y": 600, "width": 343, "height": 44 },
          "overflowX": false,
          "focusVisible": true,
          "computed": { "fontSize": "16px", "color": "rgb(0, 0, 0)" }
        }
      ]
    }
  ]
}
```

`state`는 `default`, `hover`, `focus`, `active`, `disabled`, `loading`, `empty`, `error` 중 하나다. `computed`에는 string primitive value만 넣는다. `screenshot`은 optional metadata이며 accessibility나 behavior의 증거가 아니다.

## Sources

> 자체 검토 확인 2026-09-21. 외부 출처는 사용하지 않았다.

handoff schema는 이 패키지 자체 JSON 계약이며 collector와 fixture가 이를 강제한다. 예시 값은 외부 서비스에서 가져온 데이터가 아니라 설명용이다.
