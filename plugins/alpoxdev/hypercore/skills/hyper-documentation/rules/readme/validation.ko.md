# README Validation

**Purpose**: README 완료 선언 전에 통과해야 하는 품질 게이트.

## Evidence 검사

- [ ] 모든 install 명령이 저장소의 매니페스트, 락파일, 또는 기존 문서에 존재한다.
- [ ] 모든 스크립트 호출(`npm run build`, `cargo test`, `pnpm dev` 등)이 실제 scripts/tasks 파일에 존재한다.
- [ ] CLI 섹션의 모든 명령이 소스의 실제 명령 핸들러에 매핑된다.
- [ ] usage 섹션의 모든 API/익스포트 심볼이 진입점에서 export 되어 있다.
- [ ] 언급된 모든 파일 경로가 저장소에 존재한다.
- [ ] 모든 링크가 실제 로컬 파일 또는 문서화된 외부 자원을 가리킨다.

## Shape 검사

- [ ] 프로젝트 형태가 디스커버리 프로필에 기록되어 있다.
- [ ] 섹션 선택이 `rules/readme/section-design.md`의 형태별 정책과 일치한다.
- [ ] 프로젝트가 명시적으로 다른 순서를 쓰지 않는 한 기본 순서를 따른다.
- [ ] 일반적인 화면 크기에서 quickstart가 첫 화면 안에 도달 가능하다.
- [ ] Project structure 섹션은 자명하지 않은 경우에만 포함된다.

## Language 검사

- [ ] README 산문이 기본적으로 한국어이거나, 사용자가 요청했거나 기존 대상 README 보존이 필요해서만 다른 언어를 사용했다.
- [ ] 용어가 코드베이스와 일치한다 (폴더, 명령, 설정 키 이름이 정확).
- [ ] 마케팅 부풀림 없음. 능력은 진술하되 과장하지 않음.
- [ ] sentence-case 또는 Title-case 헤딩이 일관되게 사용된다.

## Anti-fabrication 검사

- [ ] 지어낸 명령, 스크립트, env var, API 없음.
- [ ] 출처가 실제 존재하지 않는 배지 없음.
- [ ] 실제 파일이 없는 스크린샷 참조 없음.
- [ ] 모르는 부분은 `<!-- TODO -->` 또는 명시적인 "메인테이너 확인 필요" 노트로 표시되어 있음.

## Refactor 모드 검사

- [ ] 기존의 정확한 섹션은 보존됨.
- [ ] 오래된 명령과 죽은 링크는 제거되거나 교체됨.
- [ ] 이전 README와의 diff가 리뷰 가능한 크기.

## Update 모드 검사

- [ ] 요청되거나 암시된 섹션만 만져짐.
- [ ] 주변 섹션은 그대로 유지됨.
- [ ] 변경 이력 섹션이 이미 존재하면 날짜가 있는 항목이 추가됨.

## 완료 요약

마지막에 다음을 보고한다:

```text
Mode: [create | refactor | update]
Project type: [cli | library | web-app | monorepo | plugin | framework | docs-site | service]
Files inspected: [실제로 읽은 경로 목록]
Sections changed: [생성 또는 다시 쓴 헤딩 목록]
Unknowns flagged: [<!-- TODO --> 마커의 개수와 위치]
```

검사가 실패하면 검사를 완화하지 말고 README를 고친다.

## Sources

> 외부 출처 없음. 내용 확인 2026-09-21.

이 규칙은 README 작성을 위한 저장소 로컬 검증 게이트를 서술한다. 외부 주장이 없으므로 외부 출처를 인용하지 않는다.
