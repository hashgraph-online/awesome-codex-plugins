# deja for Codex

The plugin bundle Codex installs from this repository's marketplace:

```sh
codex plugin marketplace add vshulcz/deja-vu && codex plugin add deja-vu@deja-vu
```

It carries deja's MCP server, the `deja-history` skill and three hooks:
recall at session start and on each prompt, and what a compaction threw away
served again once.

[deja](https://github.com/vshulcz/deja-vu) indexes the session transcripts
twenty-four coding agents already write to disk, including sessions from before it
was installed, and answers from them locally: BM25 over the transcripts, no
model and no embeddings, credentials redacted as the index is built.

The binary is not in the bundle — plugins carry files, not native binaries:

```sh
brew install deja-vu
```

or

```sh
curl -fsSL https://raw.githubusercontent.com/vshulcz/deja-vu/main/install.sh | sh
```

`deja install codex` writes the same MCP server and hooks into `~/.codex`
from the CLI. Either path works, and having both does not wire anything twice.

Details, the harness matrix and the benchmarks are in the
[repository README](../README.md). Security policy: [SECURITY.md](../SECURITY.md).

MIT, same as deja.
