# Agent Support

hyper-handoff 메모를 실제 헤드리스 실행으로 끝까지 옮긴 에이전트와 그렇지 않은 에이전트를 적는다. 이 기기에서 2026-11-10에 끝까지 돌린 것은 omp와 Horon 둘뿐이다. 나머지 줄은 모두 `not_run`이며, 그 칸에는 벤더 문서나 설치 확인만 들어간다. 통과를 적지 않는다. 하네스가 `skip`을 기록한 것은 그 에이전트 이름이 해소된다는 것만 증명한다.

> 영어판: [`agent-support.md`](agent-support.md)

## Contents

- Measured support
- Hook support, documented and unmeasured
- How to reproduce
- Sources

## 1. Measured support

`Status`가 `measured`인 것은 기록된 실행의 `result.json`에서 `fail`이 0이고 각 시나리오가 `pass`이거나 이유가 붙은 `skip`일 때뿐이다. 바이너리가 없거나 설치·로그인을 미룬 에이전트는 `not_run`이고, 그 줄에 이유를 적어 지원 여부를 읽는 쪽이 짐작하지 않게 한다.

| Agent | Install command | Skill loading | Scenarios measured | Compaction hook (documented, not measured) | Status | Measured |
|---|---|---|---|---|---|---|
| omp | 프로젝트에서 `npx skills add alpoxdev/hypercore --skill hyper-handoff -a codex` | `.agents/skills/hyper-handoff`의 프로젝트 사본을 읽는다. `~/.omp/agent/skills/hyper-handoff`의 사용자 수준 사본이 가릴 수 있어, `install` 시나리오는 프로젝트 사본에만 심은 토큰을 읽는다 | `write` pass, `resume` pass, `drift` pass, `authority` pass, `install` pass. `write` 실행이 저장한 메모를 `cross`에서 Horon이 이어받았다 | `session.compacting`이 압축 프롬프트를 바꿀 수 있고 앞뒤에 `session_before_compact`와 `session_compact`가 있다 | measured: 5개 중 5개 pass | 2026-11-10, omp/18.18.6 |
| Horon | 프로젝트에서 `npx skills add alpoxdev/hypercore --skill hyper-handoff -a codex` | `.agents/skills/hyper-handoff`의 프로젝트 사본을 읽는다 | `write` pass, `resume` pass, `drift` pass, `authority` pass, `install` pass. omp가 쓴 메모를 이어받은 `cross` pass | 훅 이벤트 목록에 문서화된 압축 이벤트가 없다 | measured: 5개 중 5개 pass, `cross` 포함 | 2026-11-10, horon-agent v0.1.5 (c4816f4) |
| Claude Code | `npx skills add alpoxdev/hypercore -a claude-code -g`, 또는 마켓플레이스 플러그인 | 프로젝트 `.claude/skills`, 또는 `skills/`를 읽는 플러그인 | 이 기기에 기록된 실행이 없어 없음 | `PreCompact`가 stdout으로 압축 프롬프트 앞에 글을 넣을 수 있고, `SessionStart`가 `source: compact`로 실행된다 | not_run: 이 기기에 설치돼 있지 않고, 설치·로그인은 소유자 결정으로 남겼다(D5) | not_run |
| Codex | `npx skills add alpoxdev/hypercore --skill hyper-handoff -a codex` | 프로젝트 `.agents/skills` | 이 기기에 기록된 실행이 없어 없음 | `PreCompact`와 `PostCompact`가 있고 정의 해시별 신뢰 검토를 거쳐야 실행된다. `PreCompact` stdout은 버려지며 `continue: false`나 `compact_prompt` 설정만 압축에 닿는다 | not_run: 이 기기에 설치돼 있지 않고, 설치·로그인은 소유자 결정으로 남겼다(D5) | not_run |
| pi | 프로젝트에서 `npx skills add alpoxdev/hypercore --skill hyper-handoff -a pi` | 프로젝트 `.agents/skills` | 없음. 하네스는 다섯 시나리오 모두 `not_installed` 이유의 `skip`으로 기록했다 | `session_before_compact`가 요약을 대체할 수 있고 `session_compact`가 뒤따른다 | not_run: 바이너리가 없어 시나리오를 돌릴 수 없었다. 버려도 되는 저장소에서 `-a pi` 설치를 한 번 실행해 `./.agents/skills/hyper-handoff`로 복사되는 것을 확인했지만(exit 0), 그 사본을 읽은 pi 에이전트는 없었다 | not_run |
| jcode | 프로젝트에서 `npx skills add alpoxdev/hypercore --skill hyper-handoff -a codex` | 프로젝트 `.agents/skills`. 이 기기에서 확인하지 않았다 | 이 기기에 기록된 실행이 없어 없음 | 훅 이벤트 목록에 문서화된 압축 이벤트가 없다. `session_start`는 있다 | not_run: 설치돼 있지 않고, 프로젝트 사본을 읽는지도 이 기기에서 확인하지 않았다 | not_run |

측정한 줄을 읽는 법:

- omp는 모든 시나리오를 첫 시도에 통과했다. 주목할 것은 `install` 시나리오다. 이 기기에는 이 스킬의 사용자 수준 사본도 있고, 프로젝트 사본에만 심은 토큰이 돌아왔다는 것이 프로젝트 사본 로딩과 가림을 구분한다.
- Horon도 모든 시나리오를 통과했지만 첫 `write` 시도는 스트림 오류로, 첫 `drift` 시도는 답을 쓴 뒤 전송 오류로 죽었다. 둘 다 한 번 다시 돌려 통과했고, `result.json`이 시나리오마다 `attempts`와 `first_attempt_reason`을 남기므로 재시도가 드러난다.
- `cross` 실행은 omp의 `write`가 저장한 저장소를 되살리고, 그 메모를 `handoff-memo.sh check`로 검사해 `Format: hyper-handoff/1`을 읽은 뒤 이어받았다. 한 에이전트의 메모가 다른 에이전트에서 이어졌고, 이것이 이 패키지가 존재하는 이유인 속성이다.

## 2. Hook support, documented and unmeasured

이번 배포에는 훅 어댑터가 들어가지 않는다. 계획이 다음 웨이브로 미뤘다(결정 D1). 위 훅 칸은 조사 보고서의 출처로 2026-11-10에 읽은 각 벤더 문서를 옮긴 것이며, 실제 압축을 일으켜 잰 값이 아니다.

코어 스킬에는 이 훅이 하나도 필요 없다. 메모 쓰기, 검사, 이어받기는 번들 스크립트와 스킬 본문만으로 돌아간다. 압축 이벤트가 아예 없는 Horon이 omp와 같은 시나리오를 통과한 이유가 그것이다.

## 3. How to reproduce

```bash
bash scripts/handoff-agent-smoke.sh --agent omp --out .hyper/qa/handoff-universal/5-omp
bash scripts/handoff-agent-smoke.sh --agent horon --out .hyper/qa/handoff-universal/5-horon
bash scripts/handoff-agent-smoke.sh --agent horon --scenario cross \
  --memo-from .hyper/qa/handoff-universal/5-omp --out .hyper/qa/handoff-universal/5-cross
```

- `--agent <name>`은 `omp`, `horon`, `pi`와 하네스가 아는 다른 이름을 받고, `--scenario <name>`은 `write`, `resume`, `drift`, `authority`, `install`, `cross` 중 하나를 돈다.
- 하네스는 모델을 실제로 호출하므로 `scripts/verify.sh`나 CI에 들어가지 않는다. 에이전트 바이너리, 그 모델 엔드포인트의 자격증명, `install` 시나리오의 `npx skills` 내려받기를 위한 네트워크가 필요하다. 네트워크가 없어 실패한 설치는 `skip`으로 기록하고 통과로 세지 않는다.
- 시나리오마다 임시 git 저장소를 만들고 파일로만 판정한다. 메모나 답의 토큰, 없어야 하는 표지 파일, 스크립트 종료 코드가 그것이다. `--out`에 `result.json`과 시도마다의 로그 하나를 쓴다.
- 바이너리가 없으면 모든 시나리오가 `not_installed` 이유의 `skip`이 된다. 위 pi 줄이 그렇게 나왔고, 그래서 지원이 아니라 `not_run`이다.

## Sources

> 확인 2026-11-10. 로컬 실행 기록과, 조사 보고서가 인용한 벤더 훅 문서를 대조했다.

| Claim | Source |
|---|---|
| omp가 2026-11-10에 `write`, `resume`, `drift`, `authority`, `install`에 `pass`를 기록했고 에이전트 버전은 `omp/18.18.6`, 요약은 `pass` 5, `fail` 0, `skip` 0이다 | 로컬 스모크 실행, `.hyper/qa/handoff-universal/5-omp/result.json`(git 무시 대상이라 커밋하지 않는다) |
| Horon이 2026-11-10에 같은 다섯 `pass`를 기록했고 에이전트 버전은 `horon-agent v0.1.5 (c4816f4)`이다. `write`는 2회(`transport error`), `drift`는 2회(`answer then stream error`) 시도했다 | 로컬 스모크 실행, `.hyper/qa/handoff-universal/5-horon/result.json` |
| Horon이 omp의 `write`가 남긴 메모를 이어받았고, 번들 스크립트가 그 메모에 `Format: hyper-handoff/1`을 출력했으며 시나리오가 통과했다 | 로컬 스모크 실행, `.hyper/qa/handoff-universal/5-cross/result.json`과 `cross-check.log` |
| 이 기기에 pi가 없어 모든 시나리오가 `not_installed` 이유의 `skip`을 기록했고 요약은 `pass` 0, `fail` 0, `skip` 5다 | 로컬 스모크 실행, `.hyper/qa/handoff-universal/5-pi/result.json`. 명령 추적은 `5-failure.txt` |
| `npx skills`는 `-a omp`를 `Invalid agents: omp`로 거부하고, `-a codex`는 `./.agents/skills/hyper-handoff`에 쓴다. 그래서 omp, Horon, jcode는 `codex` 대상을 통해 설치한다 | `.hyper/research/22.handoff-universal/verify-install-target.md`; `README.md` 설치 표 |
| 버려도 되는 저장소에서 `npx -y skills@latest add <worktree> --skill hyper-handoff -a pi -y`가 exit 0으로 끝나고 `./.agents/skills/hyper-handoff (copied)`를 출력했다. `-a pi` 대상이 `codex` 대상과 같은 프로젝트 경로에 쓴다는 뜻이며, 그 사본을 읽은 pi 에이전트는 없었다 | 로컬 설치 확인, `.hyper/qa/handoff-universal/3-failure.txt:20-21` |
| 에이전트별 스킬 로딩 경로: Claude Code는 프로젝트 `.claude/skills`를, omp·Horon·Codex·pi·jcode는 프로젝트 `.agents/skills`를 읽는다 | 조사 보고서 `.hyper/research/22.handoff-universal.md`의 Comparison 표와 C1. 근거는 [Claude Code skills](https://code.claude.com/docs/en/skills.md), [Codex build skills](https://learn.chatgpt.com/docs/build-skills.md), [oh-my-pi docs/skills.md](https://raw.githubusercontent.com/can1357/oh-my-pi/main/docs/skills.md), [Horon docs/runtime/PROMPT.md](https://github.com/horon-ai/agent/tree/5b83dc3), [pi docs/skills.md](https://github.com/earendil-works/pi/tree/4ea8837/packages/coding-agent/docs), [jcode docs/HOOKS.md](https://raw.githubusercontent.com/1jehuang/jcode/c664f8a/docs/HOOKS.md) |
| 압축 훅 이벤트: Claude Code는 `PreCompact`와 `SessionStart`, Codex는 `PreCompact`와 `PostCompact`에 신뢰 검토, omp는 `session.compacting`과 `session_before_compact`, `session_compact`, pi는 `session_before_compact`와 `session_compact`이며 Horon과 jcode의 훅 목록에는 압축 이벤트가 없다 | [Claude Code hooks](https://code.claude.com/docs/en/hooks.md), [Codex hooks](https://learn.chatgpt.com/docs/hooks.md), [oh-my-pi docs/hooks.md](https://raw.githubusercontent.com/can1357/oh-my-pi/main/docs/hooks.md), [pi docs/extensions.md](https://raw.githubusercontent.com/earendil-works/pi/4ea8837/packages/coding-agent/docs/extensions.md), [Horon docs/runtime/HOOKS.md](https://raw.githubusercontent.com/horon-ai/agent/5b83dc3/docs/runtime/HOOKS.md), [jcode docs/HOOKS.md](https://raw.githubusercontent.com/1jehuang/jcode/c664f8a/docs/HOOKS.md) |
| Comparison 표와 주장 C1-C11, 훅 어댑터를 첫 배포에서 빼기로 한 결정(D1), omp와 Horon만 시험하고 Claude Code·Codex 설치는 소유자에게 남긴 선택(D5) | 조사 보고서 `.hyper/research/22.handoff-universal.md`; 계획 `.hyper/plans/handoff-universal.md` |
| 스모크 시나리오, 그 파일만 보는 판정, 재시도 한계, `not_installed` 건너뛰기 규칙 | `scripts/handoff-agent-smoke.sh` 헤더 주석; 기록된 `result.json`을 이 표가 읽은 결과 |

### Evidence grade

omp와 Horon 줄은 `LOCAL`이다. 이 기기의 헤드리스 실행에서 나왔고 모델의 글 대신 파일로 판정했으며, 그 `result.json` 기록은 커밋하지 않는다. 여섯 에이전트의 훅 이벤트와 로딩 경로는 `EXTERNAL-VENDOR-DOC`이다. 2026-11-10에 읽은 벤더 문서이며 이 기기에서 측정하지 않았다. `not_run` 줄은 에이전트의 능력이 아니라 이 기기의 상태를 적은 것이다.
