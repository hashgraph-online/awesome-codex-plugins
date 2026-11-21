# {{name}}

The person is not technical. Say "saved", "version" and "go back", never commit, branch or push.

## Every session

1. Read `STATUS.md`. 2. Run `python3 tools/repo.py status`. 3. If media is missing, run `python3 tools/repo.py restore`.

## Rules

- Save after each finished piece of work and before anything risky: `python3 tools/repo.py save "what changed"`. Rewrite `STATUS.md` first.
- Use `tools/repo.py` for all saving, going back and sharing (`--help` lists it). Never run `git reset --hard`, `git clean`, `git push --force` or `git rebase`.
- Keys live only in `.env`, read from the environment. Never write a key in any other file or in a commit message.
- Media never goes in git. `save` lists it by hash and stores it in Releases.
- `python3 tools/repo.py back <version>` undoes anything. It adds a new version and loses nothing.
- When this file and the actual files disagree, follow the actual files and tell the person what you found.
