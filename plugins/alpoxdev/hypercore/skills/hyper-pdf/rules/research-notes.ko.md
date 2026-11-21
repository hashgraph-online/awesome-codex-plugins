# 선행 사례 조사

> 이 패키지를 쓰기 전에 기존 PDF 스킬과 플러그인 스물한 개를 읽었습니다. 조사의 목적은 그들이 잘하는 것과 이 패키지가 메우는 틈을 구체적으로 밝히는 것입니다.

## 1. 방법

각 후보를 2026-11-13에 공개 소스에서 읽었습니다. `SKILL.md`(또는 플러그인 매니페스트), 참조 파일, 스크립트가 있으면 그것까지 읽었습니다. 별 수·마지막 푸시·라이선스는 같은 날짜의 GitHub API 값입니다. 라이선스 파일이 없는 저장소는 `none`으로 적었고 그 코드는 아이디어로만 다룹니다.

## 2. 표

| 저장소 | 별 | 마지막 푸시 | 라이선스 | 방식 | 기여하는 것 | 없는 것 |
|---|---|---|---|---|---|---|
| `anthropics` PDF 스킬 모음 | 193971 | 2026-11-06 | none | pypdf + pdfplumber + JS 필드 스크립팅 | 후보 중 가장 완성도 높은 양식 채우기: 필드 탐색·읽기·채우기·검증 | 파이썬 런타임. 한국어 조판 없음. 구조 트리·언어 태그 검사 없음 |
| `openai/skills` (.curated/pdf) | 28722 | 2026-10-28 | none | 한 파일의 도구 라우팅 | 간결한 트리거와 라우팅 규율 | 구현 없음. 검증 단계 없음 |
| `anthropics/knowledge-work-plugins` (pdf-viewer) | 35630 | 2026-11-13 | Apache-2.0 | 뷰어 플러그인 | 보기를 저작과 별개 역량으로 분리 | 읽기 전용. 생성 없음 |
| `github/awesome-copilot` (pdftk-server) | 41117 | 2026-11-13 | MIT | pdftk 래퍼 | 병합·분할·회전에 필요한 pdftk 연산을 정확히 지목 | pdftk 설치 필요. 얇은 래퍼이고 품질 검사 없음 |
| `nexu-io/open-design` (pdf) | 107474 | 2026-11-13 | Apache-2.0 | 디자인 중심 내보내기 | PDF를 시각 검토가 붙는 디자인 산출물로 다룸 | 추출 없음. 접근성 없음 |
| `tw93/Kami` | 12534 | 2026-11-10 | MIT | 문서 템플릿 체계 | 템플릿 기반 비브라우저 경로가 보고서에 통한다는 증거 | 라틴 우선. 한국어 줄바꿈 규칙 없음 |
| `0xcjl/md-pdf-report` | 1 | 2026-07-29 | MIT | CJK 글꼴 md → PDF | 한국어 선례: CJK 글꼴 등록과 `word-break` 지정 | 마크다운만. 추출·접근성 없음 |
| `Straits-AI/pdf-skill` | 0 | 2026-07-17 | MIT | 추출 중심 | 추출 한계를 분명히 적음 | 생성 없음 |
| `claude-office-skills/skills` | 574 | 2026-01-31 | MIT | 좁은 스킬 셋(추출/양식/병합) | 동작별 분리가 각 계약을 작게 유지 | 공유 런타임 없음. 설정이 겹침 |
| `ComPDFKit/compdf-skills` | 110 | 2026-08-12 | none | 상용 SDK 래퍼 | SDK 수준 연산(OCR·변환·서명)을 지목 | 유료 SDK 의존. 여기서 실행 불가 |
| `Nebutra/MinerU-Skill` | 133 | 2026-09-24 | MIT | MinerU 문서 파서 | 복잡한 PDF의 레이아웃 인식 추출이 강함 | 무거운 모델 의존. 생성 없음 |
| `ndpvt-web/latex-document-skill` | 828 | 2026-11-13 | none | LaTeX 소스 생성 | TeX가 있으면 가장 충실한 조판 경로 | TeX 툴체인 필요. 이 기기에 없음 |
| `SidneyLYZhang/pdf-generation` | 1 | 2026-11-09 | MIT | 생성만 | 최소 생성 계약 | 검증·추출 없음 |
| `yejinlei/pdf-ocr-skill` | 13 | 2026-04-20 | MIT | OCR 파이프라인 | OCR을 재작성이 아니라 쪽 위 레이어로 다룸 | OCR만 |
| `vlebert/markdown-to-pdf-agent-skill` | 4 | 2026-07-17 | MIT | md → PDF | 단순한 단일 목적 계약 | 품질 검사 없음 |
| `hamzaabduljabbar/claude-pdf-markup-skill` | 16 | 2026-08-02 | NOASSERTION | 주석과 마크업 | 주석 좌표를 핵심 기본 요소로 둠 | 주석만. 라이선스 불명 |
| `aliceisjustplaying/claude-skill-pdf-to-markdown` | 55 | 2025-11-29 | none | PDF → 마크다운 | 출력 마크다운 순서 규칙이 구체적 | 한국어·표 처리 없음 |
| `carboneio/carbone-agent-plugin` | 6 | 2026-11-12 | Apache-2.0 | 템플릿 엔진 플러그인 | 템플릿과 데이터 분리를 생성 모델로 | Carbone 서비스 필요. 라틴 중심 |
| `two4mamba/claude-skill-pdf-smart-ocr` | 2 | 2026-05-12 | MIT | OCR + 라우팅 | 쪽이 필요할 때만 OCR로 라우팅 | 결과 검증 없음 |
| `molefrog/skills` | 170 | 2026-02-12 | MIT | 다중 스킬 모음 | 스킬 경계를 출력 형태로 서술 | PDF가 중심이 아님 |
| `formify-e-sign/formify-skills` | 5 | 2026-11-12 | MIT | 전자서명 흐름 | 서명 필드를 일급으로 | 서비스 의존. 로컬 생성 없음 |

## 3. 이 패키지가 메우는 틈

조사한 후보 중 다섯을 모두 갖춘 것은 없습니다.

1. **한국어 조판 규칙**을 명시적 계약으로 둠: 줄 머리 금지 문자, 조사 붙임, `keep-all` 동작, 1.6 이상 줄 높이. CJK 선례는 글꼴을 지목하지만 줄바꿈 규칙은 말하지 않습니다.
2. **만들어진 바이트에서 글꼴 임베딩을 검증**. 대부분 글꼴을 지정하고 끝내며, `FontFile2`/`FontFile3`가 들어갔는지 되읽지 않습니다.
3. **구조 트리와 `/Lang`을 검사되는 속성으로** 두고 빠진 항목마다 구체적 손실을 지목. 접근성이 대부분 한 절이지만 여기서는 스캔되는 불변식입니다.
4. **생성 경로 둘과 명시적 라우팅 규칙**. 데이터 기반 계약서가 브라우저에 의존하지 않고, CSS가 많은 디자인이 스펙 조판기로 재현된다고 거짓말하지 않습니다.
5. **의존성 없는 런타임**을 macOS 프레임워크로. 다른 후보는 파이썬, 유료 SDK, TeX, 모델, 외부 서비스 중 하나가 필요하고 아무것도 설치하지 않은 기본 기기에서 도는 것은 없습니다.

## 4. 가져온 아이디어와 새로 쓴 것

| 아이디어 | 출처 | 쓴 방식 |
|---|---|---|
| 필드를 먼저 탐색하고 채운 뒤 검증 | `anthropics/skills` | `form`이 `--fill` 없이 `fields[]`를 출력하고, `--fill`은 `applied`/`missing`을 보고 |
| 그려진 규칙선 교차로 표 복구 | `jsvine/pdfplumber`(라이브러리) | CoreGraphics 텍스트·선 조회로 재구현. 경계는 추론으로 보고 |
| 쪽 검사 후에만 OCR로 라우팅 | `two4mamba/claude-skill-pdf-smart-ocr` | `check`가 쪽 목록과 함께 `PAGE_NEEDS_OCR`을 냄 |
| 쪽 이미지를 검토 면으로 | `nexu-io/open-design` | `render`를 선택 미리보기가 아니라 필수 관문으로 |
| 동작별 분리 | `claude-office-skills/skills` | 스킬을 나누지 않고 하위 명령 하나로. 런타임을 공유하기 위해 |

소스 파일은 복사하지 않았습니다. 라이선스가 없는 저장소(`anthropics/skills`, `openai/skills`, `ComPDFKit/compdf-skills`, `aliceisjustplaying/claude-skill-pdf-to-markdown`, `ndpvt-web/latex-document-skill`)는 서술된 동작만 읽었고 구현은 독립입니다.

## 5. 의도적으로 만들지 않은 것

| 만들지 않음 | 이유 |
|---|---|
| 파이썬 추출 스택 | 이 기기의 기본 환경에 파이썬 PDF 라이브러리가 없고, 요구하면 실행 가능한 사람이 줄어듦 |
| PDF/A·PDF/UA 인증 | 적합성 인증에는 검증기와 사람 검토가 필요하고 둘 없이 주장하면 거짓 |
| 내장 자바스크립트 실행 | PDF 액션은 신뢰할 수 없는 입력. 스캔이 보고하고 실행하지 않음 |
| AES-256 암호화 | PDFKit이 RC4 128비트만 노출. 더 있는 것처럼 암시하지 않고 명령이 밝힘 |
| 제3자 PDF 구조 트리 복구 | 잘못된 콘텐츠 스트림 위에 다시 세운 트리는 콘텐츠에 없는 구조를 주장 |

## Sources

> Checked 2026-11-13.

| Claim | Source |
|---|---|
| 저장소 지표·푸시 날짜·라이선스 | GitHub REST API `GET /repos/{owner}/{repo}`, 2026-11-13 조회 |
| `anthropics` PDF 스킬 구조 | <https://github.com/anthropics/skills> |
| 표 복구 접근 | <https://github.com/jsvine/pdfplumber> |
| 태그 PDF와 구조 트리 요구 | <https://pdfa.org/resource/pdfa-2/> |
| 한국어 줄바꿈 표준 | <https://www.w3.org/TR/klreq/> |

### Evidence grade

§2의 별 수·푸시 날짜·라이선스는 2026-11-13 GitHub API에서 받은 `MEASURED`입니다. 틈 분석과 재사용 표는 같은 날짜에 각 `SKILL.md`를 읽어 도출한 `LOCAL`입니다. 지표는 움직이므로 현재 값으로 인용하기 전에 다시 조회하세요.