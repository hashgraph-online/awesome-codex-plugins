# AGENTS.md

本文件约束 `thoth/init/` 子树内的 `audit`、`preview`、`migration`、`render`、`generator`、`service` 实现。

## 1. 子树使命

- 维护 `/thoth:init` 与 `sync` 的 canonical repo-local 实现。
- 坚持 `audit-first adopt/init`，禁止把目标仓库默认为空白脚手架。
- 保证所有受管写入都能落到 `.thoth/migrations/*` 与 `.thoth/objects/*` 的证据链中。
- 保证 Claude / Codex 两个宿主面的投影来自同一 canonical authority，而不是分叉模板。

## 2. 恢复顺序

1. 先读仓库根 [AGENTS.md](/mnt/cfs/5vr0p6/yzy/thoth/AGENTS.md)。
2. 再读 [service.py](/mnt/cfs/5vr0p6/yzy/thoth/thoth/init/service.py) 与 [preview.py](/mnt/cfs/5vr0p6/yzy/thoth/thoth/init/preview.py)。
3. 然后读 [audit.py](/mnt/cfs/5vr0p6/yzy/thoth/thoth/init/audit.py)、[migration.py](/mnt/cfs/5vr0p6/yzy/thoth/thoth/init/migration.py)、[generators.py](/mnt/cfs/5vr0p6/yzy/thoth/thoth/init/generators.py)。
4. 若涉及 public command 文案或宿主约束，再读 [commands/init.md](/mnt/cfs/5vr0p6/yzy/thoth/commands/init.md) 与相关测试。

## 3. 非协商规则

1. 不允许把 `init` 实现成 blind scaffold；必须先审查现状，再决定 `init` / `adopt` / `resume` 模式。
2. 不允许静默删除用户已有仓库信息；任何受管位移、备份、删除都必须有 migration 证据。
3. repo-root `.codex` 仍然是宿主自有目录，不得把它升级为 Thoth authority 的受管根。
4. `AGENTS.md` / `CLAUDE.md`、Codex hooks、dashboard、tests、scripts 的生成必须服从同一 canonical source，不允许手工分叉两套逻辑。
5. 仅在当前请求直接要求时才扩大 managed roots、legacy remove 列表或 host projection 内容。
6. 修改 preview / apply / sync 逻辑时，必须同时检查“无源文件误删”“resume/adopt 语义不漂移”“双宿主投影不分叉”。

## 4. 行为准则整合

### 4.1 Think Before Coding

- 先确认这是 `audit`、`preview`、`apply`、`migration`、`projection` 中哪一层的问题，不要先改生成器再猜测症状来源。
- 若同一现象可能来自宿主桥接、repo 审查、managed path 判定或迁移位移，必须先缩小归因范围。

### 4.2 Simplicity First

- 优先在已有 `service.py`、`preview.py`、`migration.py` 的责任边界内修正问题。
- 不为一次性兼容场景新增抽象层、额外配置开关或平行 renderer。
- 若一个列表、一个 helper、一次顺序调整就能解决问题，不要重写整个 init pipeline。

### 4.3 Surgical Changes

- 不顺手重排整个生成物布局、dashboard 模板或 `.agent-os` 模板，除非本次目标明确要求。
- 只删除因当前 init 语义变更而确认为陈旧的 managed path，不清理无关历史内容。
- 若发现 `commands/init.md`、tests、host projections 与实现不一致，应最小范围对齐，不扩大成全面 prompt 重写。

### 4.4 Goal-Driven Execution

- 对本子树的修改，成功条件至少应包含：模式判定正确、migration 证据存在、host projections 一致、无 silent destructive write。
- 若改动涉及 `init` 输出合同或 managed files，优先用现有单测/集成测试边界证明没有回归。

建议计划格式：

```text
1. Narrow the failing authority or renderer layer -> verify: exact file/ledger contract
2. Apply the smallest init-surface change -> verify: preview/apply/projection behavior
3. Re-run the targeted test slice -> verify: no semantic drift
```

## 5. 本子树的具体边界

- `initialize_project()` 是 audit-first apply orchestration，不是“新建项目向导”。
- `sync_project_layer()` 只重建 canonical 投影与派生层，不得偷偷接管新的 repo surface。
- `build_init_preview()` 的 `create/update/preserve/remove` 是 init 语义的核心 authority；新增规则时先想清楚是否会误伤已有仓库。
- `generate_host_projections()` 输出的是宿主投影，不是宿主私有策略分叉点。
