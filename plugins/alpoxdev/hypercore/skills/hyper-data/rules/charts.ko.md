# 차트

사용자가 차트를 요청했을 때만 이 규칙을 읽습니다. 차트는 기본이 아니며 숫자와 짧은 표가 대부분의 질문에 답하고 장식은 답을 희미하게 만듭니다. 차트를 요청받았을 때 이 규칙이 타입, 시간 처리, 전달 전 검사를 정합니다.

## 1. 차트를 그릴 때

- 사용자가 요청했을 때 차트를 그립니다. 기본은 차트 없음입니다. 숫자와 다섯 행짜리 표가 대부분의 질문에 답합니다.
- 시간에 따른 추이, 분포, 여러 범주 간 비교, 변수 사이 관계는 문장으로 담기 어려운 형태입니다. 이 경우 차트가 답에 동행할 수 있으며, 본문은 발견을 적습니다.
- 차트 하나는 질문 하나에 답합니다. 패널 세 개짜리 차트는 두 질문에 모두 대충 답합니다.

## 2. 타입은 질문을 따릅니다

| 질문 형태 | 차트 |
|---|---|
| 시간이 지나며 어떻게 달라졌나 | 선 그래프, 날짜 시간 x축 |
| 어느 범주가 가장 큰가 | 값으로 정렬한 가로 막대 |
| 어떻게 분포하나 | 빈 개수를 조정한 히스토그램, 그룹별 상자 그림 |
| X와 Y가 관계되나 | 산점도. 눈이 편할 때만 추세선을 얹습니다 |
| 전체 구성이 어떻게 되나 | 쌓은 막대나 100% 막대. 파이 차트는 네 조각 이하일 때만 |
| 시간에 걸친 많은 계열 | 얽힌 선 하나가 아니라 작은 배수 그림 |

- 범주 막대는 알파벳이 아니라 값으로 정렬합니다.
- 제목은 발견을 적고("서울이 3월에 부산을 앞섰다") 데이터셋 이름을 적지 않습니다. 축 라벨은 단위를 담습니다.
- 잘못된 타입으로 억지 그림을 그리면 숫자로만 둔 설명보다 빨리 오해를 만듭니다.

## 3. 시간대와 부분 버킷

- 일·주·월 버킷은 실행 기계의 시간대가 아니라 읽는 사람의 시간대로 자릅니다. UTC로 조용히 바꾸지 않습니다. 그 시간대를 축 라벨이나 캡션에 적습니다. 모르는 시간대는 버킷팅 전에 먼저 정합니다.
- 끝나지 않은 버킷(오늘, 이번 주, 이번 달)은 밝은 채움새나 해치로 표시하고 라벨을 붙여 그 버킷 자체에 부분 표시를 합니다. 부분 버킷이 평소처럼 그려지면 데이터가 떨어진 것으로 읽힙니다.
- 경계가 하루 중간에 있으면(읽는 사람 자정에 시작하는 일 버킷) 자정 경계가 로컬 시간 기준이라고 적습니다.

## 4. 품질과 렌더링

- 매체에 맞게 크기를 정합니다. 단독 그래프는 기본 dpi에서 `figsize=(10, 6)`가 잘 읽히고, 문서는 내보낼 때 `dpi=150` 이상이 필요합니다. 저장 전에 `tight_layout()`(또는 `constrained_layout=True`)를 부릅니다. 잘린 라벨이 차트 결함 중 가장 흔합니다.
- 기본 색상 순환은 그대로 씁니다. 무지개 색상, 3차원 막대, 뜻 없는 장식은 피합니다.
- 계열이 적으면 선에 직접 라벨을 붙이거나 범례를 빈 공간 안에 둡니다. 계열이 많으면 맥락은 회색으로 하고 질문에 답하는 계열만 색을 줍니다.
- matplotlib으로 보고서 옆에 단독 PNG를 저장합니다(`plt.savefig(path, dpi=150, bbox_inches="tight")`). HTML 산출은 다른 산출물 형태이며, 이 스킬의 차트는 렌더된 파일 자체입니다.

## 5. CJK 폰트

matplotlib의 기본 폰트는 CJK를 빈 상자(tofu)로 그립니다. 라벨이나 제목에 CJK가 하나라도 있으면 플로팅 전에 폴백을 정합니다.

```python
import platform
import matplotlib
cjk = {"Darwin": "AppleGothic", "Windows": "Malgun Gothic"}.get(platform.system(), "Noto Sans CJK KR")
matplotlib.rcParams["font.family"] = [cjk, "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False   # 마이너스 부호가 렌더링되게 유지
```

플로팅 전에 폰트와 엔진을 확인하고, 폰트나 라이브러리를 자동으로 설치하지 않습니다.

## 6. 교차 검증과 확인

- 숫자 하나를 교차 검증합니다. 핵심 숫자를 두 번째 출처(다른 테이블, 시스템 자체 합계, 원시 개수)에서 다시 구합니다. 그 출처를 차트 옆에 이름 붙이고 일치 여부를 적고 차이만큼 수량으로 적습니다. 두 번째 출처가 없으면 교차 검증을 미검증으로 밝히고, 일치한다고 지어내지 않습니다.
- 전달 전에 렌더된 파일을 엽니다. 스크립트가 실제로 쓴 이미지를 열어 네 가지를 확인합니다. 라벨이 잘리거나 읽을 수 없는 곳이 없는지, tofu나 깨진 글자가 없는지, 겹침이 없는지, 차트가 제목이 주장하는 발견을 보여 주는지입니다. 검사가 실패하면 단서를 붙여 내놓지 않고 고쳐 다시 렌더링합니다. 아무도 확인하지 않은 차트는 근거가 아닙니다.

## Sources

> Checked 2026-11-09.

| Claim | Source |
|---|---|
| 요청받았을 때나 답이 문장으로 담기 어려운 형태일 때만 차트를 그리는 규칙과 타입 표 | `dbc-hbin/omp-ulw@74df40f mechanisms/data-analyst/references/visualization.md` (mechanism reference, re-authored) |
| 읽는 사람의 시간대로 버킷을 자르고 부분 버킷을 막대 자체에 표시하는 규칙 | `dbc-hbin/omp-ulw@74df40f mechanisms/data-analyst/references/visualization.md` (mechanism reference, re-authored) |
| 두 번째 출처로 핵심 숫자 하나를 교차 검증하고, 없을 때는 미검증으로 밝히는 규칙 | `dbc-hbin/omp-ulw@74df40f mechanisms/data-analyst/references/visualization.md` (mechanism reference, re-authored) |
| CJK 폴백과 `axes.unicode_minus = False` | `dbc-hbin/omp-ulw@74df40f mechanisms/data-analyst/references/visualization.md` (mechanism reference, re-authored) |
| 전달 전에 렌더된 차트를 여는 규칙 | `dbc-hbin/omp-ulw@74df40f mechanisms/data-analyst/references/visualization.md` (mechanism reference, re-authored) |

### Evidence grade

`LOCAL` - 타입 표, CJK 폴백 줄, 확인 점검표는 라이선스가 없는 공개 저장소의 고정 커밋에서 우리말로 다시 쓴 메커니즘 행입니다. 살펴본 경로는 matplotlib만 남겼고, 브라우저 산출물 경로는 다른 산출물 형태라 여기서 이름 붙이지 않습니다.
