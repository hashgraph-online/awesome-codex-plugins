# Humanize Korean Golden Set

Calibration pairs for the humanize-korean skill. Each `before` is intentionally AI-flavored; each `after` shows the target repair shape at the intended edit size. Every pair must pass `scripts/audit-humanize-output.mjs` — rewrite pairs at grade `A` or `B`, must-not-change pairs accepted with their vocabulary intact; `test/humanize-korean-golden.test.js` enforces this, so keep the format below intact when adding pairs. G-29 is the semantic N-1 calibration: it uses `audit: none` because the audit must not classify Korean noun-phrase relations.

Entry format:

- Heading: `### G-NN · rule IDs · genre`. The genre is passed to the audit script as `--genre` and recorded in its report.
- `audit:` line: comma-separated pattern IDs the audit script must detect in `before` and clear in `after`; `none` for rules without a deterministic pattern.
- One `before` fence and one `after` fence.

Do not copy the product claims in these pairs into unrelated text; use them only as rewrite-shape references.

## Translationese (A Rules)

### G-01 · A-2 · 리포트
audit: A-2

```before
팀은 자동화 스크립트를 통해 배포 시간을 절반으로 줄였습니다.
```

```after
팀은 자동화 스크립트로 배포 시간을 절반으로 줄였습니다.
```

### G-02 · A-2 · 블로그
audit: A-2

```before
우리는 사용자 인터뷰를 통해 온보딩 문제를 찾았고 로그 분석을 통해 이탈 구간을 좁혔습니다.
```

```after
우리는 사용자 인터뷰로 온보딩 문제를 찾았고 로그 분석으로 이탈 구간을 좁혔습니다.
```

### G-03 · A-3 · 공적
audit: A-3

```before
심사 과정에 있어서 가장 중요한 기준은 재현 가능성입니다.
```

```after
심사 과정에서 가장 중요한 기준은 재현 가능성입니다.
```

### G-04 · A-7 · 리포트
audit: A-7

```before
이 라이브러리는 자체 캐시 계층을 가지고 있습니다.
```

```after
이 라이브러리에는 자체 캐시 계층이 있습니다.
```

### G-05 · A-8 · 공적
audit: A-8

```before
개정된 약관은 다음 달부터 적용되어집니다.
```

```after
개정된 약관은 다음 달부터 적용됩니다.
```

### G-06 · A-10 · 블로그
audit: A-10

```before
새 대시보드에서는 지표 변화를 실시간으로 확인할 수 있습니다.
```

```after
새 대시보드에서는 지표 변화가 실시간으로 보입니다.
```

### G-07 · A-1 · 리포트
audit: none

```before
이번 회의에서는 남은 예산에 대해 논의했습니다.
```

```after
이번 회의에서는 남은 예산을 논의했습니다.
```

### G-08 · A-4 · 칼럼
audit: none

```before
이 방식은 별도 설정이 필요 없다는 점에서 도입 부담이 적습니다.
```

```after
이 방식은 별도 설정이 필요 없어서 도입 부담이 적습니다.
```

### G-09 · A-5 · 리포트
audit: none

```before
결제 오류와 관련하여 접수된 문의가 지난주보다 늘었습니다.
```

```after
결제 오류로 접수된 문의가 지난주보다 늘었습니다.
```

### G-10 · A-6 · 블로그
audit: none

```before
사용 로그를 바탕으로 기본 설정값을 다시 조정했습니다.
```

```after
사용 로그를 보고 기본 설정값을 다시 조정했습니다.
```

### G-11 · A-9 · 리포트
audit: none

```before
장애 원인은 모니터링 담당자에 의해 이미 확인됐습니다.
```

```after
장애 원인은 모니터링 담당자가 이미 확인했습니다.
```

### G-12 · A-11 · 대화체
audit: none

```before
응답 속도를 높이기 위해 캐시를 새로 넣었어요.
```

```after
응답 속도를 높이려고 캐시를 새로 넣었어요.
```

## Sentence Endings (I, E Rules)

### G-13 · I-1 · 블로그
audit: I-1

```before
이번 분기 성장은 결국 신규 추천 기능 덕분인 것입니다.
```

```after
이번 분기 성장은 결국 신규 추천 기능 덕분입니다.
```

### G-14 · I-2 · 리포트
audit: none

```before
이 요금제의 장점은 초기 비용이 없다는 점에 있습니다.
```

```after
이 요금제는 초기 비용이 없다는 게 장점입니다.
```

### G-15 · I-3 · 칼럼
audit: none

```before
문의가 줄었다는 것은 새 문서가 효과를 냈다는 의미입니다.
```

```after
문의가 준 만큼 새 문서가 효과를 낸 셈입니다.
```

### G-16 · E-2 · 리포트
audit: none

```before
가입 전환율이 올랐습니다. 결제 실패율은 내렸습니다. 문의량은 줄었습니다. 응답 시간은 짧아졌습니다.
```

```after
가입 전환율이 오르고 결제 실패율은 내렸습니다. 문의량이 줄면서 응답 시간도 짧아졌습니다.
```

## Transitions And Significance (D, H Rules)

### G-17 · D-1, H-1 · 리포트
audit: D-1, H-1

```before
따라서 이번 분기에는 온보딩 개선을 최우선으로 진행합니다.
```

```after
이번 분기에는 온보딩 개선을 최우선으로 진행합니다.
```

### G-18 · D-1, H-1 · 공적
audit: D-1, H-1

```before
검토 결과 요건을 모두 충족했습니다. 따라서 신청을 승인합니다.
```

```after
검토 결과 요건을 모두 충족해 신청을 승인합니다.
```

### G-19 · D-2 · 리포트
audit: D-2

```before
지난 분기 재구매율이 40%에서 62%로 올랐고 신규 유입도 함께 늘었습니다. 이는 주목할 만합니다.
```

```after
지난 분기 재구매율이 40%에서 62%로 올랐고 신규 유입도 함께 늘었습니다.
```

### G-20 · H-1 · 블로그
audit: H-1

```before
이번 업데이트로 시작 화면이 가벼워졌습니다. 또한 알림 설정 화면도 새로 정리했습니다.
```

```after
이번 업데이트로 시작 화면이 가벼워졌습니다. 알림 설정 화면도 새로 정리했습니다.
```

### G-21 · D-3 · 칼럼
audit: none

```before
본질적으로 이 문제는 캐시 만료 정책이 문서와 달랐던 데서 시작됐습니다.
```

```after
이 문제는 캐시 만료 정책이 문서와 달랐던 데서 시작됐습니다.
```

### G-22 · D-4 · 블로그
audit: none

```before
매우 강력한 자동 분류 기능으로 받은편지함을 정리해 보세요.
```

```after
자동 분류 기능으로 받은편지함을 정리해 보세요.
```

## Structure And Jargon (B, C, F, K Rules)

### G-23 · B-1 · 리포트
audit: none

```before
우리 팀은 검색 증강 생성(RAG) 파이프라인을 도입했습니다. 검색 증강 생성(RAG)은 답변 품질을 높였고 검색 증강 생성(RAG) 운영 비용은 예상보다 낮았습니다.
```

```after
우리 팀은 검색 증강 생성(RAG) 파이프라인을 도입했습니다. RAG는 답변 품질을 높였고 운영 비용은 예상보다 낮았습니다.
```

### G-24 · C-11 · 공적
audit: C-11

```before
신청 절차는 간단하지만, 제출 서류는 꼼꼼히 확인해야 합니다.
```

```after
신청 절차는 간단하지만 제출 서류는 꼼꼼히 확인해야 합니다.
```

### G-25 · F-4 · 공적
audit: none

```before
접수 지연의 재발 방지를 위한 처리 절차의 단순화가 필요합니다. 관련 서식은 다음 주에 공지합니다.
```

```after
접수 지연이 되풀이되지 않도록 처리 절차를 단순하게 바꿔야 합니다. 관련 서식은 다음 주에 공지합니다.
```

### G-26 · F-5 · 칼럼
audit: none

```before
장기적 관점에서 지속적 개선을 추진해야 합니다. 우선순위는 분기마다 다시 정합니다.
```

```after
길게 보고 꾸준히 개선해야 합니다. 우선순위는 분기마다 다시 정합니다.
```

### G-27 · K-1 · 리포트
audit: K-1

```before
이 엔드포인트는 멱등이라 같은 요청을 여러 번 보내도 결과가 달라지지 않습니다.
```

```after
이 엔드포인트는 같은 요청을 여러 번 보내도 결과가 달라지지 않습니다.
```

## Combined Repair

### G-28 · D-1, A-2, I-1, D-2, H-1 · 블로그
audit: D-1, A-2, I-1, D-2, H-1

```before
결론적으로 이번 개편은 성능 개선을 통해 사용자 경험을 크게 높인 것입니다. 초기 로딩 시간이 3.2초에서 1.4초로 줄었고 이는 매우 주목할 만합니다. 또한 새 캐시 계층은 백그라운드에서 동작합니다. 설정 화면 구성은 예전 그대로입니다.
```

```after
이번 개편은 성능 개선으로 사용자 경험을 크게 높였습니다. 초기 로딩 시간이 3.2초에서 1.4초로 줄었습니다. 새 캐시 계층은 백그라운드에서 동작합니다. 설정 화면 구성은 예전 그대로입니다.
```

## Modifier Targets (N Rule)

### G-29 · N-1 · 리포트
audit: none

```before
정확한 컴퓨터를 확인했습니다. 정확한 MSI 보드를 확인했습니다. 정확한 펌웨어 이미지를 적용했습니다.
```

```after
대상 컴퓨터를 확인했습니다. MSI 보드 모델을 확인했습니다. 보드와 일치하는 펌웨어 이미지를 적용했습니다.
```
