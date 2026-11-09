# Fix And Proof

원인을 확정이라고 부르기 전에, 그리고 최소 수정 모드에서 무엇이든 고치기 전에 이 파일을 읽는다. 토글 증명, red-to-green 순서, 관측 공백, 계측 제거를 맡는다.

## 1. Confirmed Means Toggle-Provable

원인은 다음 세 가지가 모두 성립할 때만 확정이고, 그중 셋째가 토글 증명이다. 토글이 없으면 확정도 없다.

1. **잡은 값이 예측과 정확히 맞는다.** "일관돼 보인다"가 아니라, 실패가 일어나는 순간에 읽은 관찰이 가설이 말한 그 값이다.
2. **재현이 안정적이다.** 다시 돌려도 같은 관찰이 나온다. 증상이 가끔만 나타나는 사안은 증상을 격리한 것이지 원인을 격리한 것이 아니다. 가설 루프로 돌아간다.
3. **원인을 토글하면 실패가 토글된다.** 원인을 바꾸면 실패가 사라지고, 되돌리면 실패가 다시 재현된다. 두 방향을 모두 관찰해야 한다. 이것이 메커니즘과 상관관계를 가르는 증명이다.

그 밖의 모든 증거 수준은 상관관계다. 상관관계로 만든 수정은 버그를 출시한다.

| 의심 원인 | 유효한 토글 |
|---|---|
| 환경 변수가 라이브러리 기본값을 덮는데 그 값이 틀렸다 | 해제 → 실패 사라짐, 복원 → 실패 재발 |
| 작업에 await가 없다 | await 추가 → 통과, 제거 → 다시 실패 |
| 클라이언트가 하드코딩 URL을 쓴다 | 설정된 URL로 바꿈 → 통과, 되돌림 → 다시 실패 |
| 공유 상태 경쟁 | 접근 직렬화 → 부하에서 통과, 가드 제거 → 부하에서 실패 |
| 값을 쓰기 전에 읽는다 | 읽기를 쓰기 뒤로 옮김 → 통과, 되돌림 → 실패 |

토글을 만들 수 없으면 원인은 확정이 아니다. 수정을 쓰지 말고 라운드를 하나 더 돈다.

## 2. Record The Confirmation

```markdown
## Root cause (confirmed <ISO timestamp>)
- Mechanism: <the causal chain from cause to observable symptom, one paragraph>
- Evidence: <file:line of the captured value | path to the saved reproduction | command and output>
- Toggle proof: "With <change X>, the repro produces <good>. Reverting <change X>, the repro produces <bad>."
- Fix scope: <files and approximate size>
```

메커니즘 문단이 핵심 시험이다. 원인에서 증상까지의 사슬을 인과 문단 하나로 쓰지 못하면, 고칠 만큼 버그를 이해하지 못한 것이다.

토글 증명에 이르지 못한 원인은 `Assumption:`과 그것을 확정할 정확한 점검을 붙여 보고하고 실행은 `unconfirmed`로 끝난다. 확정된 것처럼 편집하지 않는다.

## 3. Red To Green

최소 수정 모드에서는 이 순서를 지킨다.

1. **소유 테스트를 찾는다.** 이 계약을 가장 강한 경계에서 이미 덮는 테스트를 찾아 고치지 않은 코드에서 실행한다.
   - 이 버그 때문에 이미 실패 → red 증거다. 기록한다.
   - 통과하지만 경로를 덮음 → 병렬 테스트를 더하지 말고 실패 case로 확장한다.
   - 소유 테스트가 없음 → 저장소가 이 동작의 테스트를 두는 곳에서만 좁은 재현을 더한다. 그렇지 않으면 잡아 둔 실행 재현이 증거다.
2. **Red.** 실패 실행을 잡아 출력을 일지에 붙인다. 테스트 이름은 버그 보고처럼 읽혀야 하고, 실패 출력만 읽어도 무엇이 깨졌는지 알 수 있어야 한다.
3. **Green.** 관찰한 메커니즘을 완전히 없애는 가장 작은 변경을 한다. 과잉 수정의 신호: "혹시 몰라서" 붙이는 null 검사, 옆 함수 리팩터, 버그가 요구하지 않은 새 설정 옵션, 코드를 깔끔하게 만들려는 새 추상화.
4. **green 이후에만 리팩터.** 수정에 직접 속한 정리는 허용한다. 나머지는 일지의 후속 항목이지 이번 변경이 아니다.
5. **영역 검사.** 손댄 영역에 저장소가 요구하는 검사를 실행한다. 새 실패가 나오면 "수정"이 무언가를 떠받치던 부분을 바꾼 것이다. 새 실패를 증거로 §1로 돌아간다.

수정 뒤에 쓴 테스트는 수정을 되돌려도 통과할 수 있다. 수정 없이 실패하고 수정과 함께 통과하는지 확인하고, 두 출력을 일지에 남긴다.

## 4. Close The Observability Gap

상태가 보이지 않아서 진단이 라운드를 더 썼다면(어느 분기가 돌았는지, 값이 무엇이었는지, 폴백이 걸렸는지 알려 주는 로그가 없었다면) 그 불가시성은 버그 옆의 결함이다. 로그 줄을 더하는 것이 "혹시 몰라서"가 아닌 유일한 순간이다. 이번 실행이 그 줄이 자리를 얻는다는 증거다.

- 프로젝트가 지정한 로거로, 소비자가 필요로 하는 수준에서, 결정 지점에, 보간 문자열이 아니라 필드에 데이터를 담아 쓴다.
- 그 줄의 상시 소비자를 이름으로 댄다. 이번 세션만을 위해 존재한 줄은 계측이고 §5가 제거한다.
- 프로젝트가 의도적으로 로그를 남기지 않으면 그 결정을 존중하고 이 단계를 건너뛰며 일지에 적는다.

## 5. Remove Every Instrumentation Hunk

- 이번 실행이 더한 `console.log`, `print`, `dbg!`, `fmt.Println`, 임시 플래그, 비활성 단언, sleep, 디버그 포트, 로컬 패치를 모두 제거한다.
- 일지의 Instrumentation 표 행을 하나씩, 아직 돌고 있는 것이 있으면 Resources 표 행도 하나씩 지운다.
- diff에 의도한 변경만 남았는지 확인한다. `git diff`(또는 저장소의 동등한 명령)에 남은 probe가 없어야 한다. 커밋하지 않는다.
- probe가 이제 수정의 일부라서 남아야 하면 §4로 옮기고 거기서 이름을 밝힌다.

## 6. Handoff Shape

확정된 원인의 수정이 여러 파일, 새 모듈 경계, 스키마 변경을 요구하면 산출물은 편집이 아니라 일지 안의 수정 브리프다. 일지의 `Result:` 줄은 `handoff`다.

```markdown
## Fix brief

- 원인: <the confirmed mechanism, one paragraph>
- 증거: `path:line` | `<command and output>`, toggle proof: "<change X → good; revert → bad>"
- 재현: `<exact command>` in `<working directory>` — <expected failure>
- 수정 범위 초안: <the surfaces that must change, with the known location of each>
- 순서: <which file or migration must land first, and why>
- 검증 계획: <the red run, the green run, and the area checks a worker must produce>
- 가정·미확인: <open points>
```

브리프는 이번 실행의 조사를 다시 읽지 않고도 실행할 수 있어야 한다. 새 기능 계획이 아니라 계획 형태의 산출물이다. 원인, 재현, 증명은 이미 존재한다.

## Sources

> Checked 2026-11-09.

| Claim | Source |
|---|---|
| 원인은 실패를 재현하고 없애는 토글로만 확정 | `dbc-hbin/omp-ulw@74df40f debugging/references/methodology/06-fix.md` (mechanism reference, re-authored) |
| 세 가지 확정 조건과 토글 예시 | `dbc-hbin/omp-ulw@74df40f debugging/references/methodology/06-fix.md` (mechanism reference, re-authored) |
| green 전 red, 소유 테스트 우선, 가장 작은 변경, green 이후에만 리팩터 | `dbc-hbin/omp-ulw@74df40f debugging/references/methodology/06-fix.md` (mechanism reference, re-authored) |
| 관측 공백 해소와 임시 계측 hunk 전부 제거 | `dbc-hbin/omp-ulw@74df40f debugging/references/methodology/06-fix.md` (mechanism reference, re-authored) |
| `handoff` 종료 상태와 계획 형태의 수정 브리프 | integrator contract, 2026-11-09 |

### Evidence grade

`LOCAL` - 수정 브리프 필드와 §3의 순서는 이 패키지의 설계다. 메커니즘 행은 라이선스가 없는 저장소에서 자기 말로 다시 쓴 것이며 텍스트나 코드를 복사하지 않았다. 토글 증명 요건은 상관관계로 만든 수정이 이 패키지가 막으려는 실패 모드라서 단단하게 둔다.
