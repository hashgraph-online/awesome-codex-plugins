# Test prompts for `incident-response`

Run these manually with the plugin loaded (`claude --plugin-dir ./npmscan-mcp-plugin`)
before publishing a change to this skill. Each case names the exact tool calls and fields the response
should surface — not just "did a tool get called," but "did the right
playbook steps survive into the answer."

1. **A maintainer change, chained into remediation** — ask:
   > "A package's maintainer list shows a new account added shortly before
   > the latest release shipped — what should I actually do about that?"
   Expect `get_remediation_playbook({ rules: ["new-maintainer-published-quickly"] })`
   (chained from a `check_maintainer_changes` finding with that exact
   `rule` value — a synthetic-fixture pattern, same caveat as cases 11-14
   below: real packages age out of the tool's 180-day lookback window over
   time, e.g. the real Sept 2025 chalk/debug "qix" compromise this pattern
   is modeled on no longer shows any live finding on chalk today since
   it's now well past 180 days old — so don't rely on a specific real
   package still exhibiting this live when re-running this case). The
   response should quote the matched playbook's real steps — for
   `maintainer-change-flagged`: freeze to the last known-good version, check
   repo activity/communication for transparency, require two-person review
   for the first re-adopted versions — not a generic "be careful" answer.
   It should also lead with that match's `situationNote` ("A maintainer
   added to this package published a new version shortly afterward — the
   exact shape of the September 2025 chalk/debug 'qix' compromise...") and
   name the `severity` ("high"), not just the step list on its own.

2. **A provenance mismatch, chained into remediation** — ask:
   > "check_package_provenance flagged install-script-added on
   > @npmcli/arborist — what's the incident response?"
   Expect `get_remediation_playbook({ rules: ["install-script-added"] })` to
   return the new `provenance-mismatch` playbook. The response should name
   its actual steps: freeze to the last clean version, diff the flagged
   version's install scripts/dependencies against source at the attested
   commit, rotate the npm publish token and CI secrets for that package,
   require `--provenance` plus a second maintainer's review going forward —
   specifically the token-rotation step, since that's what distinguishes
   this from a generic "audit the code" answer.

3. **A clean result — no forced playbook** — ask:
   > "lodash came back with riskTier none on check_package_provenance. What
   > should I do?"
   Expect the response to say plainly that no remediation/incident response
   is needed — NOT a `get_remediation_playbook` call made just to have
   something to show, and not an invented "clean" playbook.

4. **Direct lookup by named scenario, no live finding** — ask:
   > "What's the standard playbook for a postinstall script that downloads
   > a binary?"
   Expect `get_remediation_playbook({ id: "postinstall-binary" })` (no
   package-specific finding tool call first, since no package was named) —
   response names the real steps: block the PR/update, verify the binary
   host is a trusted GitHub Releases/CDN, check for obfuscation/
   child_process launches, rotate tokens if the payload ran.

5. **Non-triggering — a plain trust question with no remediation ask** — ask:
   > "Is chalk 5.3.1 safe to use?"
   Expect `package-trust-check` to activate instead — no
   `get_remediation_playbook` call, since the user asked a trust/investigation
   question, not "what do I do about this."

6. **Two different findings collapsing to one playbook, without repeating
   boilerplate** — ask:
   > "analyze_install_script flagged both obfuscation and exfil-hosts on
   > this package. What's the incident response?"
   Expect one `get_remediation_playbook({ rules: ["obfuscation", "exfil-hosts"] })`
   call (not two separate calls) returning a single
   `supply-chain-compromise` playbook entry in `playbooks`, but two entries
   in `matches` — one per rule, each with its own distinct `situationNote`.
   The response should present the playbook's steps once, not twice, while
   still naming both specific things that were found (the obfuscated code
   and the exfil-host contact) rather than only mentioning one or merging
   them into a single generic sentence.

7. **Vague, non-technical symptom, no package name and no exact rule id** —
   ask:
   > "npm install did something weird just now — it looked like it grabbed
   > a file from some random website and then ran it. What do we do?"
   The user never says "postinstall," "binary," or any tool/rule vocabulary.
   Expect the model to still recognize this as the postinstall-binary
   scenario per the symptom table and call
   `get_remediation_playbook({ id: "postinstall-binary" })` directly (no
   package name given, so no finding tool to run first) — NOT a refusal, and
   NOT a request that the user "be more specific" or name a `rule`/id
   themselves first. The response should flag that this is a best-read
   guess from the description, not a confirmed diagnosis, then give the
   real steps (block the PR/update, verify the binary host, check for
   obfuscation/child_process, rotate tokens if it ran).

8. **A named package with a vague symptom, but enough to pick one finding
   tool** — ask:
   > "Is glob-utils-pro safe? A teammate said it does something sketchy
   > during npm install."
   "Sketchy during npm install" names a package AND a specific-enough
   symptom (install-time behavior) to skip the full package-trust-check
   sweep and go straight to `analyze_install_script({ name: "glob-utils-pro" })`
   per the symptom table, then chain into `get_remediation_playbook` with
   whatever `rule`s it actually returns (or say plainly that nothing was
   flagged if the scan comes back clean).

9. **Totally generic — the one case that should still ask a question** —
   ask:
   > "We got a security alert about one of our dependencies. What do I do?"
   No package name, no symptom, nothing to ground a guess in. Expect the
   model to ask one clarifying question (which package, or what the alert
   actually said) rather than guessing a random playbook id or refusing to
   engage — this is the single row in the symptom table where asking is the
   right move, not the default.

10. **The `suspected-typosquat` playbook (previously untested)** — ask:
    > "I almost installed `expres` instead of `express` — what's the
    > standard response for this?"
    Expect `get_remediation_playbook({ id: "suspected-typosquat" })` (or
    `{ rules: ["typosquat"] }` if chained from a live `possibleTyposquatOf`
    finding). The response should quote the real playbook: `severity:
    "high"`, its three steps (check maintainers/repo lineage, inspect
    README/code size for a suspiciously thin repo, replace with the
    intended package and add allow-lists), and cite the
    `GHSA-c2m4-w5hm-vqjw` incident reference (crossenv, which impersonated
    cross-env to steal environment variables) — not a generic "double-check
    the name" answer.

11. **The `child-process-in-install` playbook (previously untested)** —
    ask:
    > "A package's postinstall script spawns a child process —
    > `exec('chmod +x ./agent.exe && ./agent.exe')` — right after
    > downloading a binary. How bad is this and what do I do?"
    Expect `get_remediation_playbook({ rules: ["child-process"] })` (or the
    fuller rule set `analyze_install_script` would actually return for this
    content) to surface `child-process-in-install`: `severity: "high"`,
    steps escalating straight to "assume high risk, identify the exact
    command," isolating/whitelisting only if it's a verified trusted build
    step — otherwise remove/replace and report it — plus the
    `GHSA-f7jv-2wj8-grw7` incident reference.

12. **The `unexpected-network-install` playbook — the one moderate-severity
    case (previously untested)** — ask:
    > "A dependency's install script makes an outbound network call to a
    > host I don't recognize, but nothing else about it looks off. What
    > should I do?"
    Expect `get_remediation_playbook({ rules: ["network-io"] })` to return
    `unexpected-network-install`, `severity: "moderate"` — distinctly lower
    than cases 10-11 — with steps to capture logs and identify the source,
    re-run with `--network=none` to confirm it's actually required, then
    allowlist the specific domain and verify checksums if so, plus the
    `GHSA-fw7f-xj7r-p9v6` incident reference. Expect the response's tone to
    reflect the lower severity, not treat every network call the same as a
    child-process finding.

13. **A maintainer added on npm with no release carrying it yet — the
    "access changed, nothing shipped" urgency case** — ask:
    > "A co-maintainer was just added to a package's npm maintainer list,
    > but no new version has been published since. Is this already
    > something to act on?"
    Expect the model to recognize this as more urgent than a completed
    turnover, chaining to
    `get_remediation_playbook({ rules: ["maintainer-added-recently"] })` →
    the `maintainer-change-flagged` playbook, `severity: "high"`: freeze to
    the last known-good version, check repo activity for transparency,
    require two-person review for the first release the new maintainer
    actually publishes. The response should explicitly say the risk here
    is that access already changed even though nothing has shipped with it
    yet — not wait for a release before treating it as worth acting on.

14. **The dormant-package negative counterpart — same pattern, correctly
    zero findings** — ask the same question as case 13, but about a
    package whose last release was years ago (well outside a ~180-day
    lookback). Expect `check_maintainer_changes` to report no findings and
    a `note` explaining the change falls outside its lookback window given
    the package's dormancy — and the response to say plainly that no
    incident-response action is currently indicated (while still noting
    the maintainer list did change, for the record) rather than
    manufacturing a playbook just to have something to show.

15. **Unmatched rule and unmatched id in the same batch, exact note text**
    — ask:
    > "The scan flagged rule `not-a-real-rule` and I also tried playbook id
    > `not-a-real-playbook-id` directly, plus the baseline
    > `lifecycle-present` finding — what do these actually mean?"
    Expect `get_remediation_playbook({ rules: ["lifecycle-present",
    "not-a-real-rule"], id: "not-a-real-playbook-id" })` in one call, all
    three results `matched: false`, and the response to use the tool's own
    exact note text for each — `'No dedicated playbook for rule
    "not-a-real-rule" — likely a baseline/informational finding, not
    evidence of risk on its own.'` and `'No playbook found with id
    "not-a-real-playbook-id".'` — rather than inventing generic advice for
    the two that came back unmatched.

16. **We are the compromised publisher** — say:
    > "Our npm token got stolen and someone published new versions of our
    > packages with a worm in them. What do we do?"
    Expect `get_remediation_playbook({ id: "compromised-publisher" })`
    (no package-specific finding tool first — there's no package named) and
    the response to lead with revoking npm/GitHub tokens and rotating every
    credential, then deprecating/unpublishing the bad versions and telling
    users — not only the consumer-side `supply-chain-compromise` steps
    (pinning, auditing), which don't stop a stolen token from publishing
    again.

To confirm the skill loaded and is namespaced correctly, run `/help` and
check the **Custom commands** tab for `/npmscan:incident-response`, or just
invoke it directly with that name.
