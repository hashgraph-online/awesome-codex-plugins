# {{name}}

Code project. The person is not technical: say "saved", "version" and "go back", never commit, branch or push.

## Every session

1. Read `STATUS.md` and `features.json`. 2. Run `python3 tools/repo.py status`. 3. Run the tests below before changing anything.

## Commands

- Run: (fill in the one command)
- Test: (fill in the one command)

## Rules

- Work on one feature from `features.json` at a time. Mark it done only after its test passes. Never delete a feature or a test to make a check pass.
- Save after each finished feature: `python3 tools/repo.py save "what changed"`. Rewrite `STATUS.md` first.
- A risky idea or a second agent: `python3 tools/repo.py try <name>`, then `keep` or `drop`. Each gets its own folder.
- Use `tools/repo.py` for all saving, going back and sharing (`--help` lists it). Never run `git reset --hard`, `git clean`, `git push --force` or `git rebase`.
- Keys live only in `.env`, read from the environment. Never write a key in any other file or in a commit message.
- `python3 tools/repo.py back <version>` undoes anything. It adds a new version and loses nothing.
- When this file and the actual files disagree, follow the actual files and tell the person what you found.
