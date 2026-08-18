# Build Terminal Dashboard Workflow

Build a full-screen interface while retaining a noninteractive command contract.

## Steps

1. [ ] Define model, messages/events, update transitions, and view rendering.
2. [ ] Keep domain and I/O services independent of the terminal UI framework.
3. [ ] Route all long-running work through cancellable commands or goroutines.
4. [ ] Bound event rates and coalesce redundant refreshes.
   - The renderer owns and stops its ticker.
   - Input, render, and worker goroutines share a cancellation tree.
5. [ ] Provide keyboard help, focus state, textual status, and a quit path.
6. [ ] Restore the alternate screen and cursor on all exits.
   - Stop producers, apply the documented drain/discard policy, and join owned
     goroutines before restoring terminal state.
7. [ ] Provide a plain or structured equivalent for agents and CI.
8. [ ] Test update logic without a terminal, then smoke-test supported terminals.

## Exit Criteria

- [ ] The dashboard cannot strand the terminal in a modified state.
- [ ] Every essential action remains accessible without the dashboard.
