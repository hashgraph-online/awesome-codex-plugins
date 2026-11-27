# Choreography, character, timing

Candidates come from here. Pick two to four that genuinely differ for the moment; add
the current motion as `A 지금` when there is one.

## Purpose sets the range (step 1)

| purpose | example | range |
|---|---|---|
| 어디서 왔는지 보여 주기 | a panel growing out of the row that opened it | a handed-over path; 250 to 450ms |
| 바뀌었음을 알리기 | a saved badge, a count changing | one element, small travel; 150 to 300ms |
| 주의 끌기 | a new notification | one element, may overshoot; seen rarely |
| 표현 | a landing hero, onboarding | several elements, longer, expressive curves |

How often the moment is seen decides productive or expressive. A screen opened many times
a day is productive: short, no bounce, little travel. Larger travel takes longer; small
elements move faster than large ones.

## Choreography (step 3)

| pattern | gains | costs |
|---|---|---|
| 한꺼번에 | shortest; nothing waits | no order; the eye has no first place to go |
| 차례로 (stagger) | reading order made visible | long lists take long; cap the total, not the gap |
| 제목 먼저, 나머지 겹쳐 | a lead, then everything at once | the overlap must be enough to read as one motion |
| 중요한 것 먼저 | the key number or action lands first | needs a clear first element |
| 이어받기 (handed over: GSAP Flip, Motion `layout`/`layoutId`) | shows where something came from | only when an element really moves between places |
| 가운데에서 바깥으로 | a burst from the trigger | reads as expressive |

Conditions to draw: the real number of elements (5 cards and 40 rows choreograph
differently), and the narrowest real width when the layout reflows.

## Character (step 4)

| family | GSAP | Motion |
|---|---|---|
| 부드럽게 감속 | `power2.out` | `easeOut` |
| 강하게 감속 | `expo.out`, `power4.out` | `[0.16, 1, 0.3, 1]` |
| 넘쳤다 돌아옴 | `back.out(1.7)` | spring `bounce: 0.3` |
| 탄성 | `elastic.out(1, 0.5)` | spring `bounce: 0.5` |
| 튕김 | `bounce.out` | keyframes, rarely right in a product |
| 직선 | `none` | `linear`; only for scroll-linked progress |

Enter decelerates, exit accelerates (`.in`), and a moving element that stays on screen
uses `inOut`. A spring has no set length: its time is measured, not chosen. Step 4 decides
the exit with the enter: the same curve, or an accelerating one, drawn as a pair; the
spec gets a row per direction (`열 때`, `닫을 때`).

## Timing (step 5)

A ladder of total length with the curve and order fixed: for a productive moment 200 ·
300 · 400 · 500ms, for an expressive one 400 · 600 · 800 · 1000ms. A stagger gap ladder:
30 · 60 · 90ms, with the total shown on each caption (`전체 640ms`). For a spring, ladder
`visualDuration` (Motion) or `duration` with the spring ease (GSAP).

## Trigger and interruption (step 6)

| trigger | when |
|---|---|
| 한 번 재생 | the content arrives once |
| 스크롤에 붙임 (scrub) | progress belongs to the scroll position |
| 스크롤로 한 번 재생 | a section enters the view; plays forward once |
| 되감기 | the same control opens and closes |

Interruption, drawn by triggering twice: continue from where it is (reverse), jump to the
end, restart. A panel opened and closed fast must never jump. For a scroll moment the
interruption is scrolling back up and down again: whether it reverses, stays, or plays
again (`replays`).

## Reduced motion (step 7)

| option | what moves |
|---|---|
| 투명도만 | opacity, short (about 150ms), no travel |
| 즉시 | nothing; the end state appears |
| 거리 줄임 | the same motion with travel under 4px |

The reduced version keeps the meaning (what changed is still visible) and drops travel.
`motion.cjs` measures its travel: the caption shows it.

## Held constant

Until their step is picked: everything together (choreography), `power2.out` or Motion's
default `easeOut` (character), 400ms per element (for a spring, `visualDuration` 0.4) and
a 60ms gap where a candidate needs one (timing), the code's travel or 16px when there is none, play once (trigger), and the
full version (reduced motion is its own step).
