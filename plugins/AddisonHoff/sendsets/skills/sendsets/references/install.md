# CLI installation

Install the CLI with `brew install addisonhoff/tap/sendsets` (macOS, Linux) or `scoop bucket add sendsets https://github.com/AddisonHoff/homebrew-tap` then `scoop install sendsets` (Windows). Without a package manager, download the archive for your platform and `checksums.txt` from https://github.com/AddisonHoff/sendsets-releases/releases/latest, check the archive against `checksums.txt`, and unpack the `sendsets` binary onto PATH.

Confirm with `sendsets version`. The Unix binary defaults to `~/.local/bin/sendsets`; use that path if the current shell has not loaded the new PATH. A hosted workspace uses the default host. For self-hosted use `SENDSETS_HOST` or `--host`.

Run `scripts/doctor.sh` after authentication. It checks auth and calls `sendsets doctor --json`. A fresh workspace can report missing mailboxes or app connections. These are next actions, not evidence that the CLI install failed.

`assets/campaign.example.yaml` is an editable example for `sendsets run`. Check the current CLI help before adapting it to a customer campaign.
