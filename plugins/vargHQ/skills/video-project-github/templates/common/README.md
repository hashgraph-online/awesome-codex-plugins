# {{name}}

Private project. Text is saved in this repo. Media is listed in `media.lock.jsonl` by hash and stored in this
repo's Releases, so nothing is lost and nothing is too big.

## Get it back on another computer

Tell your agent: "Clone {{name}} from my GitHub and run `python3 tools/repo.py restore`."

By hand: `gh repo clone {{name}} && cd {{name}} && python3 tools/repo.py restore`

Keys are not in GitHub on purpose. Copy `.env.example` to `.env` and fill it from your password manager.
