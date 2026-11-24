---
case: worktree-B4
description: Use when you work in a worktree and another worktree of the same repository may change the same files, so a merge would clash.
---

# Two worktrees, one file

Shapes: chat.

```sh
stickypane diff list                       # each worktree's files, and those two changed
stickypane chat add chat --as chart "chart and table both change render/axis.go; one of us should wait"
```

`diff list` compares every worktree's changes from its base and names
the files two of them changed. When yours shares a file, say so in the
chat, naming the file and both worktrees, and let the user decide the
order. Do not change the other branch.

Done when: every shared file is named in the chat, and you changed
nothing outside your worktree.
