# 읽기·쓰기 도구

> 각 도구가 `.xlsx`를 건드릴 때 실제로 무엇을 지키는지. 스킬 자체 도구 행은 2026-11-13 이 기기에서 실행한 결과입니다. `LOCAL`로 표시한 라이브러리 행도 여기서 실행했고, 나머지는 그 라이브러리 문서를 근거로 적었음을 표시했습니다.

## 목차

1. 패키지 구조, 손실이 이해되는 이유
2. 측정: openpyxl 3.1.5 왕복
3. 측정: 번들 도구
4. 그 밖의 작성기, 메커니즘별
5. 선택 기준
6. 여기서 하지 않는 것

## 패키지 구조, 손실이 이해되는 이유

`.xlsx`는 XML 파트를 담은 zip입니다. 차트·이미지·표·메모·정의된 이름·인쇄 영역이 있는 워크북의 파트는 이렇습니다.

```
[Content_Types].xml          _rels/.rels
xl/workbook.xml              xl/_rels/workbook.xml.rels
xl/styles.xml                xl/theme/theme1.xml
xl/worksheets/sheet1.xml     xl/worksheets/_rels/sheet1.xml.rels
xl/drawings/drawing1.xml     xl/drawings/_rels/drawing1.xml.rels
xl/charts/chart1.xml         xl/media/image1.png
xl/tables/table1.xml         xl/comments/comment1.xml
docProps/app.xml             docProps/core.xml
```

워크시트만 이해하는 작성기는 `sheet1.xml`, `workbook.xml`, `[Content_Types].xml`, 관계 파일을 다시 쓰고, 자기 스타일 모델에서 `styles.xml`을 재생성합니다. 모델에 없는 것은 존재하지 않게 됩니다. "차트가 사라졌다"의 메커니즘 전체가 이것입니다.

## 측정: openpyxl 3.1.5 왕복

조건: `uv run --with openpyxl --python 3.13`, macOS arm64, 2026-11-13. 편집 없이 로드 후 저장.

**단순 파일** (`build_workbook.py`가 만든 파일, 열 차트 하나, 매크로 없음):

| 관찰 | 결과 |
|---|---|
| 전/후 파트 수 | 11 / 14 |
| 사라진 파트 | 없음 |
| 추가된 파트 | `docProps/app.xml`, `docProps/core.xml`, `xl/theme/theme1.xml` |
| 바뀐 파트 | 11개 중 11개. `chart1.xml`과 `styles.xml`까지 전부 재작성 |

이 형태에서는 내용을 지키지만 패키지 전체를 다시 씁니다. 차트는 살아남았고 바이트는 그대로가 아닙니다.

**풍부한 파일** (차트, 이미지, 표, 데이터 유효성, 메모, 병합 셀, 인쇄 영역, 정의된 이름, 틀 고정):

| 산출물 | 왕복 후 |
|---|---|
| 차트 | 유지 (`_charts` = 1) |
| 이미지 | 유지 (`_images` = 1) |
| 표 | 유지 (`tables` = 1) |
| 데이터 유효성 | 유지 |
| 셀 메모 | 유지 |
| 병합 셀, 인쇄 영역, 틀 고정, 정의된 이름 | 유지 |

openpyxl의 모델이 이들을 포함하므로 살아남습니다. "openpyxl이 내 차트를 잃나"에 단일 답이 없는 이유가 이것입니다.

**피벗 파트**, 풍부한 파일에 `xl/pivotCache/pivotCacheDefinition1.xml`과 `xl/pivotTables/pivotTable1.xml`을 넣은 뒤 로드/저장: 두 파트가 **사라졌습니다**. openpyxl 3.1.5에 `openpyxl.pivot.table.TableDefinition`과 `openpyxl.pivot.cache.CacheDefinition`이 있는데도 이렇게 된 것은, 넣은 스텁이 그 리더가 받아들이는 모양이 아니어서 버려졌기 때문입니다. openpyxl을 거치는 피벗은 위험으로 보고 왕복 뒤 파트를 확인한다. 항상 보존된다거나 항상 사라진다고 단정하지 않는다.

**매크로**:

| 호출 | 저장 후 `xl/vbaProject.bin` |
|---|---|
| `load_workbook(path)` | 사라짐 |
| `load_workbook(path, keep_vba=True)` | 유지, 바이트 동일(`sha256` 같음), `macroEnabled` 콘텐츠 타입 유지 |

기본 호출은 VBA를 조용히 지웁니다. `.xlsm`에는 `keep_vba=True`가 필수이고, 그래도 보장되는 것은 VBA 파트뿐입니다. openpyxl이 모델링하지 않는 모양의 파트, 예컨대 인식되지 않는 피벗 스텁은 여전히 사라집니다.

## 측정: 번들 도구

| 작업 | 건드린 파트 | 검증 방법 |
|---|---|---|
| `inspect` | 없음(읽기 전용) | — |
| 피벗 파트가 있는 파일에 `patch --set-value` | `xl/worksheets/sheet1.xml` 하나 | `untouchedPartsPreserved: true`, 19개 중 18개 다이제스트 동일 |
| `.xlsm`에 `patch` | 워크시트 파트 하나 | `vbaProject.bin` sha256 불변 |
| `recalc` | 워크시트 파트 + `xl/workbook.xml`(`fullCalcOnLoad`) | 수식 유지, `data_only` 읽기에서 값 반환 |
| `build` | 새 파일 | 19파트, openpyxl에서 열림 |

파트 하나만 건드린다는 점이, 차트·피벗·매크로가 있는 기존 파일을 수정할 때 `patch`를 먼저 고르는 이유입니다.

## 그 밖의 작성기, 메커니즘별

| 작성기 | 모델 | 잃거나 다시 쓰는 것 |
|---|---|---|
| pandas `to_excel`(openpyxl 엔진) | 값과 기본 서식만 | 차트, 이미지, 메모, 피벗, 매크로, 조건부 서식. 새 파일을 쓰므로 질문은 "원본에서 무엇을 잃었나"다 |
| xlsxwriter | 쓰기 전용 | 기존 파일을 아예 읽지 못한다. 생성에는 좋고 편집에는 쓸 수 없다 |
| LibreOffice 헤드리스 변환 | 전체 엔진 | 패키지 전체를 다시 쓴다. 대부분 지키지만 아이디·서식·차트 직렬화가 바뀐다 |
| Numbers / 엑셀(GUI) | 전체 엔진 | 권위 있지만 GUI 세션 없이는 스크립트로 쓸 수 없다 |
| 로 zip 직접 편집(이 스킬) | 바이트 | 고친 파트가 스키마에 맞는 한 아무것도 잃지 않는다 |

`uv run --with openpyxl`이 여기서 가장 싼 독립 읽기 확인입니다. 기록용 편집기가 아닙니다.

## 선택 기준

- 차트·피벗·매크로·출처 불명 파일을 편집한다 → `patch`
- 새 파일을 만든다 → `build`(차트와 조건부 서식 포함) 후 `recalc`
- 피벗이 필요하다 → 집계 행을 계산해 쓰고, 네이티브 피벗을 약속하지 않는다. `large-data-and-pivots.md`를 본다
- 독립 확인이 필요하다 → openpyxl 읽기 확인, 그리고 확인이 엑셀이 아니라 openpyxl이었다고 밝힌다

## 여기서 하지 않는 것

- 엑셀 엔진으로 계산하지 않는다. 평가기는 문서화된 함수 집합을 덮고 나머지는 미검증으로 보고한다. 범위는 `ROWS`·`COLUMNS`·`INDEX`·`VLOOKUP`·`HLOOKUP`을 위해 행·열 모양을 유지하고, `ISERROR`/`ISERR`/`ISNA`는 오류를 전파하지 않고 검사하며, 실패한 `MATCH`나 조회는 `IFNA`·`ISNA`가 검사하는 `#N/A`를 돌려주고, `POWER`/`^`는 음수 밑에 분수 지수를 주면 복소수가 아니라 `#NUM!`을 돌려준다.
- 렌더링·인쇄하지 않는다. 레이아웃, 페이지 나눔, 인쇄 정확도는 실제 엔진이 필요하다.
- VBA를 실행하지 않는다.
- `.xls`나 `.xlsb`를 읽지 않는다.

## Sources

> 확인 2026-11-13.

| 주장 | 출처 |
|---|---|
| 위에 적은 openpyxl 파트 수, 사라진 파트, 유지된 산출물 전부 | 2026-11-13 이 기기에서 `uv run --with openpyxl`로 openpyxl 3.1.5 측정. 스크립트와 결과는 세션에서 재현 |
| 번들 도구가 건드린 파트 수 | `patch_workbook.py` / `recalc_cached.py` 출력, 2026-11-13 확인 |
| OOXML 파트 배치 | <https://learn.microsoft.com/en-us/office/open-xml/spreadsheet/structure-of-a-spreadsheetml-document> |
| pandas `to_excel`이 `.xlsx` 엔진으로 openpyxl을 쓴다 | <https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_excel.html> |
| xlsxwriter는 설계상 쓰기 전용이다 | <https://xlsxwriter.readthedocs.io/working_with_memory.html> |

### Evidence grade

이 스킬 도구가 만든 행과, 여기서 실행한 openpyxl 3.1.5 행이 `LOCAL`입니다. pandas, xlsxwriter, LibreOffice, Numbers 행은 그 문서의 동작에서 추론한 것이고, 이 기기에 LibreOffice가 없으므로 측정이 아니라 `DOC` 등급 근거입니다. 버전과 날짜를 적었으니 모든 주장을 다시 확인할 수 있습니다.
