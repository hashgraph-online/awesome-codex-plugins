# SSH Key Recovery on a Fresh Host

## Contents

- [Diagnostic Signature](#diagnostic-signature)
- [Step 1 — Confirm the keys are actually missing](#step-1--confirm-the-keys-are-actually-missing)
- [Step 2 — Search exhaustively before giving up](#step-2--search-exhaustively-before-giving-up)
- [Step 3 — Recover from a sibling host (if reachable)](#step-3--recover-from-a-sibling-host-if-reachable)
- [Step 4 — If recovery isn't possible, disable the affected workers and continue](#step-4--if-recovery-isnt-possible-disable-the-affected-workers-and-continue)
- [Step 5 — Avoid the recurrence](#step-5--avoid-the-recurrence)
- [What NOT to Do](#what-not-to-do)

This is the single most common cause of "all workers unhealthy" in the wild: a `workers.toml` checked in (or copied) from another machine references SSH identity files that don't exist on the host you're on right now. Every probe returns `RCH-E100`/`RCH-E101`. Agents historically stall here and ask the human.

**Don't ask. Recover.** Here's the playbook.

---

## Diagnostic Signature

```
Probing 9 worker(s)...
  vmi1149989 ubuntu@212.90.121.76... ✗ Connection failed:
    RCH-E100
      × SSH connection failed for ubuntu@212.90.121.76
      help: SSH Troubleshooting:
            1. Verify host/user/key in workers.toml.
            2. Try a manual connection with verbose logs:
            ssh -vvv -i "/home/ubuntu/.ssh/contabo_vps_ed25519"
                       ubuntu@212.90.121.76
            Run 'rch doctor' for comprehensive SSH diagnostics.
```

…repeated for every worker, and `ls -la ~/.ssh/` shows the referenced key file is missing.

---

## Step 1 — Confirm the keys are actually missing

```bash
# Pull every identity_file referenced by workers.toml
grep -h '^[[:space:]]*identity_file' ~/.config/rch/workers.toml \
  | sed 's/.*=[[:space:]]*"\(.*\)"/\1/' | sort -u | while read -r p; do
      r="${p/#~/$HOME}"
      printf '%s -> %s\n' "$p" "$([[ -r "$r" ]] && echo OK || echo MISSING)"
    done
```

Anything tagged `MISSING` is a candidate.

---

## Step 2 — Search exhaustively before giving up

The key may exist on this host under a different path:

```bash
# Common locations
for k in $(grep -h identity_file ~/.config/rch/workers.toml | sed 's/.*"\([^"]*\)"/\1/' | xargs -n1 basename | sort -u); do
  echo "## $k"
  find ~/.ssh /root/.ssh 2>/dev/null -name "$k*"
  # Then broader (only if needed; this is slower):
  # sudo find / -xdev -name "$k*" -not -path '*/proc/*' -not -path '*/sys/*' 2>/dev/null
done
```

Also check ssh-agent for in-memory keys (their fingerprints compared to authorized_keys on the worker can confirm a working key exists even if the file does not):

```bash
ssh-add -l
ssh-add -L           # the actual public keys
```

If a key is in the agent, you don't strictly need the file — `rch` will still fail because it expects a file path, but you can use this to:
- copy the matching private key from another host you can reach
- or, with explicit user authorization, generate a new key and add it to the workers' authorized_keys

---

## Step 3 — Recover from a sibling host (if reachable)

If you have any host that **does** have the keys (typically the original developer machine or another worker), grab them via SSH:

```bash
# Replace <SOURCE> with the host name and adjust paths
SOURCE=trj
for k in contabo_vps_ed25519 thinkstation2_ed25519; do
  if ssh "$SOURCE" "test -r ~/.ssh/$k"; then
    scp "$SOURCE:~/.ssh/$k" "~/.ssh/$k"
    scp "$SOURCE:~/.ssh/${k}.pub" "~/.ssh/${k}.pub" 2>/dev/null || true
    chmod 600 "~/.ssh/$k"
    chmod 644 "~/.ssh/${k}.pub" 2>/dev/null || true
  else
    echo "$k not on $SOURCE either"
  fi
done
rch workers probe --all
```

---

## Step 4 — If recovery isn't possible, disable the affected workers and continue

Don't let one missing key block all work. Disable just the unreachable workers and proceed with whatever's left:

```bash
# Disable any worker whose probe surfaces a key/auth error.
# Probe response shape: .data is a flat array of {id, host, status, latency_ms?, error?}
rch --json workers probe --all \
  | jq -r '.data[] | select(.status != "ok" and (.error // "" | test("Permission denied \\(publickey|no such identity|identity_file"))) | .id' \
  | while read -r id; do
      [[ -z "$id" ]] && continue
      echo "disabling $id (missing key)"
      rch workers disable "$id" --reason "missing ssh key on host" --drain -y
    done

# Now re-check
rch workers probe --all
rch check
```

When the keys are recovered later, re-enable:

```bash
rch workers enable <id>
```

---

## Step 5 — Avoid the recurrence

Bake a check into the host's provisioning. Two ergonomic options:

### Option A — pre-flight in the shell rc

In `~/.bashrc` (or equivalent), after any rch-related work:

```bash
rch_keys_check() {
  local missing=0
  while read -r p; do
    p="${p/#~/$HOME}"
    [[ -r "$p" ]] || { echo "missing rch key: $p"; missing=1; }
  done < <(grep -h '^[[:space:]]*identity_file' ~/.config/rch/workers.toml 2>/dev/null \
             | sed 's/.*=[[:space:]]*"\(.*\)"/\1/')
  return $missing
}
```

Then `rch_keys_check && rch check`.

### Option B — `rch config doctor` upstream

`rch config validate` doesn't currently check identity_file existence. This is filed as upstream UX feedback (see "Upstream Bugs to File" in `RECOVERY_PLAYBOOKS.md`). When that lands, `rch config doctor` will surface missing keys directly.

---

## What NOT to Do

- **Do not delete `~/.config/rch/workers.toml`** to "start over". You'll lose every host/priority/tag that was carefully configured. If you must reset, copy it first: `cp ~/.config/rch/workers.toml{,.bak}`.
- **Do not run `rch workers discover --add --yes` blindly** to "rediscover" — it will add freshly-discovered hosts but won't remove the broken ones, leaving a doubly-confused config.
- **Do not pause and ask the human** unless you've tried Steps 1–4 and the keys are genuinely lost. The first three steps are seconds; only Step 3 might be slow if SCP transfer is large.
- **Do not generate a brand-new key and try to push it to authorized_keys on every worker** without explicit user authorization. That's a privilege change, not a recovery.
