---
case: form-F4
description: Use when several changes each need a yes (eight dependency upgrades, five files to delete), and asking one by one would tire the user.
---

# Several at once

Shapes: form.

```sh
stickypane note write upgrades-1 --open <<'EOF'
---
type: form
title: Which upgrades?
---
## Upgrade
- [ ] lodash 4.17.20 → 4.17.21 (patch)
- [ ] react 18 → 19 (major: 12 files change)
- [ ] vite 5 → 6 (major: config changes)

[ Apply selected ] [ Cancel ]
EOF
stickypane wait upgrades-1 --timeout 15m --json
```

One box per change, none ticked in advance, each with what it costs.
Apply exactly the boxes in `answers`, and nothing that was left unticked.

Done when: the changes made are exactly the ticked ones.
