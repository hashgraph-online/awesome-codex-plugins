# Quality Gates

Run gates before moving between phases:

```bash
python3 {plugin_root}/scripts/zagrosi_skills.py lint-interview --phase plan --planning-dir "{planning_dir}" --strict
python3 {plugin_root}/scripts/zagrosi_skills.py lint-plan --planning-dir "{planning_dir}" --depth standard --strict
python3 {plugin_root}/scripts/zagrosi_skills.py lint-sections --planning-dir "{planning_dir}" --depth standard --strict
python3 {plugin_root}/scripts/zagrosi_skills.py traceability --planning-dir "{planning_dir}" --strict
python3 {plugin_root}/scripts/zagrosi_skills.py status --path "{planning_dir}"
```

Gate response:

- `success`: no critical or high findings
- `score`: 0-100 quality score
- `findings`: severity-coded issues with recommendations

Fix high and critical findings before continuing. In standard and deep planning,
use `--strict` so medium findings also block until addressed or explicitly
accepted by the user.

Depth modes:

- `fast`: fewer questions, local review, compact but still self-contained sections
- `standard`: multi-thousand-word plan, reviewed TDD plan, 1,000+ word sections
- `deep`: review-board passes, 5,000+ word plan, stronger traceability, risk and decision rigor
