# Section Design

**Purpose**: 프로젝트 프로필에서 README 섹션, 순서, 깊이, 언어를 결정한다.

## 1. 프로젝트 형태별 섹션 정책

| 형태 | 필수 | 권장 | 요청 없으면 생략 |
|---|---|---|---|
| **CLI** | Title, install, quickstart, commands, examples, license | Configuration, environment variables, exit codes | 아키텍처 다이어그램, 내부 API |
| **Library** | Title, install, usage, API surface, examples, license | TypeScript types, peer deps, 지원 런타임 | 내부 모듈 맵 |
| **Web app** | Title, dev quickstart, environment, build/deploy, license | 기술 스택, 프로젝트 구조, contributing | 마케팅 카피 |
| **Monorepo** | Title, repo overview, package list, dev quickstart, license | 패키지별 README, 공통 스크립트 | 긴 아키텍처 에세이 |
| **Plugin** | Title, install (호스트 플랫폼), usage, configuration, license | 호환성 매트릭스, 호스트별 예시 | 내부 확장 지점 |
| **Framework** | Title, install (`create-*`), quickstart, core concepts (링크), license | 템플릿, 생태계 | 전체 문서 사이트 내용 |
| **Docs site** | Title, 무엇을 문서화하는지, local dev, contribution flow, license | Build/deploy, content structure | 자동 생성된 콘텐츠 트리 |
| **Service / API** | Title, run locally, environment, endpoints summary, license | Deployment, observability | 내부 요청 핸들러 |

여러 형태가 적용될 때는 주된 형태를 고르고, 보조 형태가 진짜 필요로 하는 추가 섹션만 더한다.

## 2. 순서 관습

기본 순서, 위에서 아래:

1. 제목 + 한 줄 설명
2. 배지 (검증 가능한 경우에만)
3. 기능 (3-7개 불릿, 한 줄씩)
4. Install
5. Quickstart / Usage
6. Configuration / Environment
7. Commands / API surface
8. Examples (길면 `<details>`로 접기)
9. Development (scripts, test, lint)
10. Project structure (자명하지 않을 때만)
11. Contributing (프로세스가 문서화된 경우에만)
12. License

Install을 묻어두지 않는다. 새 독자가 긴 컨텍스트를 지나치지 않고 install 명령에 도달해야 한다.

## 3. 헤딩과 코드 스타일

- 프로젝트 문서가 이미 Title Case를 일관되게 쓰지 않는 한 헤딩은 sentence case로 한다.
- 펜스 코드 블록에 올바른 언어 태그를 단다 (`bash`, `ts`, `py`, `rs`, `json`, `yaml`).
- 셸 프롬프트는 트랜스크립트를 옮길 때만 보여준다 (`$` 사용자, `#` 루트). 그 외엔 생략.
- 예시 코드는 블록당 약 12줄 이내로 유지하고, 더 길면 예시 파일을 링크한다.
- 명령 이름, 폴더 이름, 설정 키는 코드베이스가 쓰는 케이싱을 그대로 사용한다.

## 4. 언어와 톤

- README 산문은 기본적으로 한국어로 쓴다. 사용자가 다른 언어를 명시적으로 요청했거나 기존 대상 README의 현재 언어를 일관성 때문에 보존해야 할 때만 다른 언어를 사용한다.
- 코드베이스가 쓰는 용어를 그대로 쓴다 (폴더, 명령, 설정 키 이름은 정확히 인용).
- 마케팅보다 능력을 진술한다: "Mermaid 다이어그램을 의존성 없이 SVG로 렌더링" 이 "초고속 다이어그램 엔진" 보다 낫다.
- README 전체에서 한 개념에는 한 용어를 쓴다.
- 문장은 짧게 유지한다. 열거 가능한 내용은 단락 대신 리스트와 표를 선호한다.

## 5. 배지

다음 모두를 만족할 때만 배지를 추가한다:

- 배지 출처가 실제로 존재한다 (배포된 npm 버전, 구성된 CI 워크플로, 등록된 SPDX 라이선스).
- 프로젝트가 이미 그 배지를 발행하고 있거나 사용자가 명시적으로 요청했다.

링크 가능한 출처가 없는 커버리지/다운로드/빌드 상태 배지는 추가하지 않는다. 배지가 없는 편이 깨진 배지보다 낫다.

## 6. Quickstart 계약

Quickstart는 다음을 만족해야 한다:

- 설치 직후 끝까지 실행 가능,
- 가장 작은 현실적인 예시 사용,
- 기본값이 동작할 때 자리 표시자(`YOUR_TOKEN`, `<replace-me>`)는 피함,
- 긴 워크스루 대신 명령 한 줄 또는 3-5줄 코드를 선호.

진짜로 셋업이 필요한 경우(env vars, 계정, 외부 서비스)에는 짧은 한 단락으로 적고 깊은 가이드를 링크한다.

## 7. 섹션 정리

내용이 없는 섹션은 버린다:

- 테스트 미구성 → "Testing" 생략.
- 배포된 패키지 없음 → "Install from registry" 생략, "From source"만 유지.
- 기여 프로세스가 문서화되어 있지 않음 → 가짜 프로세스를 만들지 말고 이슈 트래커 링크로 대체.
- 배포 파이프라인이 문서화되어 있지 않음 → "Deployment" 추측하지 말고 생략.

짧고 정확한 README가 길고 부풀려진 README보다 낫다.

## 8. Monorepo 관련 가이드

모노레포에서 루트 README는 패키지 사이의 안내자, 패키지별 README는 한 패키지를 깊이 다룬다.

- 루트 README: 패키지 목록을 한 줄 목적과 폴더 경로로 나열하고, 워크스페이스 인식 install/dev 명령을 루트에서 보여준다.
- 패키지 README: 그 패키지를 자체 프로젝트로 보고 위 표의 형태별 정책을 적용한다.
- 루트 README에 패키지별 install 지시를 중복하지 않는다. 대신 링크한다.

## Sources

> 외부 출처 없음. 내용 확인 2026-09-21.

이 규칙은 README 작성을 위한 저장소 로컬 섹션 설계 정책을 서술한다. 외부 주장이 없으므로 외부 출처를 인용하지 않는다.
