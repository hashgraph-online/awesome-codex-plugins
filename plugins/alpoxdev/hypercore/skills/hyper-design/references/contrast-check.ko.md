# 대비 검사

텍스트, 아이콘, 테두리, 포커스 색 쌍을 판정할 때와 어디에든 "AA를 통과한다"를 쓰기 전에 읽는다. 눈은 회색 쌍의 대비를 과대평가하므로 계산 없이 통과를 주장하지 않는다.

## 1. 공식 (WCAG 2.x)

1. 각 채널을 0-1로 바꾼다: `c = value / 255`.
2. 선형화한다: `c <= 0.03928`이면 `c / 12.92`, 아니면 `((c + 0.055) / 1.055) ^ 2.4`.
3. 상대 휘도: `L = 0.2126 R + 0.7152 G + 0.0722 B`.
4. 비율: `(L1 + 0.05) / (L2 + 0.05)`, `L1`은 밝은 쪽 색이다. 범위는 1에서 21이다.
5. 반올림하지 않은 비율을 4.5(일반 텍스트)와 3.0(큰 텍스트, 아이콘, 컨트롤 경계, 포커스 표시)에 비교한다. 반올림은 표시할 때만 한다. 4.4983은 4.50으로 출력되지만 여전히 4.5에 미달한다.

## 2. 명령

이 함수를 POSIX 셸(bash, zsh)에 붙여 넣고 불투명한 헥스 색 두 개로 호출한다. 텍스트 색이 먼저다. `awk`만 필요하고 파일을 쓰지 않는다.

```bash
contrast() {
  awk -v fg="$1" -v bg="$2" '
    function hexval(h,  i, c, v) { h = tolower(h); v = 0
      for (i = 1; i <= length(h); i++) { c = index("0123456789abcdef", substr(h, i, 1)) - 1
        if (c < 0) return -1; v = v * 16 + c } return v }
    function lum(hex,  r, g, b) { sub(/^#/, "", hex)
      if (length(hex) == 3) hex = substr(hex,1,1) substr(hex,1,1) substr(hex,2,1) substr(hex,2,1) substr(hex,3,1) substr(hex,3,1)
      if (length(hex) != 6) { bad = 1; return 0 }
      r = lin(hexval(substr(hex,1,2))); g = lin(hexval(substr(hex,3,2))); b = lin(hexval(substr(hex,5,2)))
      return 0.2126 * r + 0.7152 * g + 0.0722 * b }
    function lin(v,  c) { if (v < 0) { bad = 1; return 0 } c = v / 255
      return (c <= 0.03928) ? c / 12.92 : ((c + 0.055) / 1.055) ^ 2.4 }
    BEGIN { a = lum(fg); b = lum(bg)
      if (bad) { print "error: colors must be #rgb or #rrggbb" > "/dev/stderr"; exit 2 }
      hi = (a > b) ? a : b; lo = (a > b) ? b : a; ratio = (hi + 0.05) / (lo + 0.05)
      printf "ratio %.2f (%.4f)\n", ratio, ratio
      printf "normal text: %s (needs 4.5)\n", (ratio >= 4.5) ? "PASS" : "FAIL"
      printf "large text and non-text UI: %s (needs 3.0)\n", (ratio >= 3.0) ? "PASS" : "FAIL"
      exit (ratio >= 4.5) ? 0 : 1 }'
}
contrast "#777777" "#ffffff"
# ratio 4.48 (4.4781)
# normal text: FAIL (needs 4.5)
# large text and non-text UI: PASS (needs 3.0)
```

이 함수는 쌍이 4.5를 통과하면 0, 아니면 1, 형식이 잘못되면(`#rgb`나 `#rrggbb`가 아님) 2를 반환한다.

- 투명도가 있는 색은 실제 배경 위에 먼저 합성한다. 채널마다 `channel = alpha * fg + (1 - alpha) * bg`를 계산하고 불투명해진 결과를 명령에 넣는다.
- 이미지나 그라디언트 위 텍스트는 최악 지점에서 확인한다. 텍스트 아래에서 밝은 텍스트면 가장 밝은 픽셀, 어두운 텍스트면 가장 어두운 픽셀을 스크림까지 포함해 고른다.
- 쌍과 비율, 판정을 보고서의 게이트 표에 기록한다.

## 3. 참조 표

위 공식으로 계산한 값이다. 목록에 없는 쌍을 계산하는 대신 쓰지 말고 온전성 확인용으로만 쓴다.

| 배경 위 텍스트 | 비율 | 일반 텍스트(4.5) | 큰 텍스트(3.0) |
|---|---|---|---|
| `#ffffff` 위 `#000000` | 21.00 | pass | pass |
| `#333333` 위 `#ffffff` | 12.63 | pass | pass |
| `#666666` 위 `#ffffff` | 5.74 | pass | pass |
| `#ffffff` 위 `#777777` | 4.48 | fail | pass |
| `#070707` 위 `#777777` | 4.50 (4.4983) | fail | pass |
| `#888888` 위 `#ffffff` | 3.54 | fail | pass |
| `#999999` 위 `#ffffff` | 2.85 | fail | fail |
| `#000000` 위 `#555555` | 2.82 | fail | fail |

## Sources

> 확인 2026-11-07.

| 주장 | 출처 |
|---|---|
| 상대 휘도, 0.03928 선형화 임계값, 대비 비율, 4.5:1과 3:1 임계값 | <https://www.w3.org/TR/2024/REC-WCAG22-20241212/> (상대 휘도와 대비 비율의 정의) |
| "회색 쌍을 주장하지 않는다" 규칙, 참조 표, 임계값 근접 예시 | <https://github.com/miqdadbadjuber/anti-slop> (commit `9504989`, `antislop-human/SKILL.md`, The Contrast Checker; MIT, Copyright 2026 Miqdad Badjuber). 원본의 Python 검사기는 복사하지 않았고 위 명령은 이 패키지의 awk 구현이다. |
| 명령이 참조 표의 모든 행을 재현하고 형식이 잘못된 입력을 거부한다 | 이 패키지의 실행 확인, 2026-11-07, macOS awk |

### Evidence grade

공식은 규범 WCAG 2.2다. 명령은 표의 여덟 행과 대조해 확인했다. 알파 합성은 구현하지 않고 설명만 했으므로 먼저 합성해야 한다.
