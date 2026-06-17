# Crank Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| "No ready issues found for this epic" | Epic has no child issues or all blocked | Run `$plan <epic-id>` first to decompose epic into issues. Check dependencies with `bd show <id>`. |
| "Global wave limit (50) reached" | Excessive retries or circular dependencies | Review failed waves in `.agents/crank/wave-N-checkpoint.json`. Fix blocking issues manually or break circular deps with `br dep remove`. |
| Wave vibe gate fails repeatedly | Workers producing non-conforming code | Check `.agents/council/YYYY-MM-DD-vibe-wave-N.md` for specific findings. Add cross-cutting constraints to task metadata or refine worker prompts. |
| Workers report completion but files missing | Permission errors or workers writing to wrong paths | Check `.agents/swarm/<team>/worker-N-output.json` for file paths. Verify write permissions with `ls -ld`. |
| RED Gate passes (tests don't fail) | Test wave workers wrote implementation code | Re-run TEST WAVE with explicit "no implementation code access" in worker prompts. Tests must fail before GREEN waves start. |
