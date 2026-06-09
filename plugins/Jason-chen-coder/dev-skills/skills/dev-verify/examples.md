# dev-verify · Examples

## 例 1 — skill 仓库变更

Claims:
1. 新 skill 目录齐全 — `bash scripts/validate-repo.sh`
2. plugin manifest JSON 有效 — 同一脚本中的 Python JSON parse
3. README 技能数同步 — 同一脚本 grep `9 个 skill` / `skills-9`

合格输出:

```
Verified:
- bash scripts/validate-repo.sh: PASS (Validation OK)
- git diff --check: PASS (no whitespace errors)

Status: ready for dev-code-review
```

## 例 2 — bug 修复

Claims:
1. 原 bug 修复 — regression test passes
2. regression test 有效 — 临时反转 fix 后 test fails,恢复后 passes
3. 相关模块未回归 — module test passes

反模式:
- “我改了空值判断,应该修好了。”
- “单测过了,所以构建也没问题。”但没有跑 build。
