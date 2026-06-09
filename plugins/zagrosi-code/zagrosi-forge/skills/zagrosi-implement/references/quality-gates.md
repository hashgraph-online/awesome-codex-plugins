# Implementation Quality Gates

Before starting:

```bash
python3 {plugin_root}/scripts/zagrosi_skills.py lint-sections --planning-dir "{planning_dir}"
```

After each section:

```bash
python3 {plugin_root}/scripts/zagrosi_skills.py implement-record-section \
  --sections-dir "{sections_dir}" \
  --section "{section}" \
  --commit "{commit_hash_or_none}"
```

Before finishing:

```bash
python3 {plugin_root}/scripts/zagrosi_skills.py lint-implementation-state --sections-dir "{sections_dir}"
python3 {plugin_root}/scripts/zagrosi_skills.py traceability --planning-dir "{planning_dir}"
python3 {plugin_root}/scripts/zagrosi_skills.py status --path "{planning_dir}"
```

Fix high and critical findings. Medium findings are acceptable only when noted
in the final residual-risk summary.
