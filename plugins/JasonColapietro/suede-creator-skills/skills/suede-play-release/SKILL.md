---
name: suede-play-release
description: "Suede AI Google Play Release Skills. Google Play release delivery with AAB preflight, test-track upload, exact versionCode promotion, staged rollout, locale notes, and API readback. Use when asked \"promote this Android build\" or to diagnose Play publishing access and prove the served release. NOT FOR: app building or policy review (android-app-factory), listing assets (suede-aso), or CI gates (suede-ci-gate)."
metadata:
  display-name: "Suede AI Google Play Release Skills"
---

# Suede AI Google Play Release Skills

## Compatibility

Requires Android release artifacts and authorized Google Play publishing access. Bundled preflight uses Python with pyjwt/cryptography and macOS Keychain; delivery examples use fastlane supply. Linux CI uses its secret store.

Use [the worked contract](references/worked-contract.md) for a staged rollout
example, access-failure recovery, and API readback validation.

```text
Iron Law: the Play API decides what shipped, not a green fastlane summary.
Every claim about a live release is a readback or it is a guess.
```

## Gate policy: advisory, not blocking

Run every check and report results honestly. Verdicts are advice attached to the
work, never a control that changes it. A failed check changes what you report,
never what you do. The one exception is the production halt in Step 7: a public
release is irreversible for the users who get it, so present the options and let
the user pick.

## Step 0: Preflight the credential before anything else

Never assume publishing works. Prove it with a real API call that changes
nothing: open an edit and delete it. The script reads the key from the macOS
login Keychain and needs `pyjwt` and `cryptography`; on Linux CI, load the same
base64 JSON from the CI secret store and run the equivalent token exchange.

```bash
python3 scripts/play-preflight.py <package.name> [--service NAME] [--account NAME]
```

Three outcomes, three different actions:

| Result | Meaning | Do |
| --- | --- | --- |
| token fails | key is wrong or revoked | rotate, see Step 1 |
| HTTP 401/403 on the edit | Play Console has not granted the account | Step 1's grant |
| edit opens and deletes | publishing is wired | continue |

A 403 here is the normal state of a brand-new service account, not a bug.

## Step 1: Credentials

Use a **dedicated publishing service account**, separate from any billing or
purchase-verification account. A credential that can push releases should not
also be able to void purchases. Give it no cloud IAM roles: all of its authority
comes from the Play Console grant, so before that grant the key is inert.

Store the JSON in the login Keychain **base64-encoded**:

```bash
security add-generic-password -U -s GOOGLE_PLAY_SERVICE_ACCOUNT_JSON -a <account> -w
```

Run it with `-w` last and no value so it prompts and the key never enters shell
history. Paste the base64, not the raw JSON.

Base64 is load-bearing. `security` hex-encodes any multi-line secret on read, so
raw JSON comes back in one of two shapes depending on content. Base64 gives one
shape and one decode path.

Granting access is a **Play Console UI action** and cannot be done from the API:
invite the service-account email under Users and permissions with release
permissions on the app. Report this to the user as a step only they can take,
with the exact email and permissions, then re-run Step 0.

## Step 2: Pull before every command

`fastlane` reads the working tree, not the remote. A stale checkout produces a
run that succeeds and does nothing, because a missing changelog is a skip rather
than an error.

```bash
git -C <repo> pull --ff-only && git -C <repo> log --oneline -1
```

If fastlane offers to set itself up, the Fastfile is not on disk. Answer no and
pull; accepting scaffolds an empty config over the real one.

## Step 3: Write the changelog first

Release notes live at
`fastlane/metadata/android/<locale>/changelogs/<versionCode>.txt`, one file per
locale per versionCode.

A missing file is **not** an error. Play silently serves the previous version's
notes, so users read stale text against a new build and nothing tells you. Write
one for every locale that has listing copy, before uploading.

```bash
for l in $(ls fastlane/metadata/android); do
  [ -f "fastlane/metadata/android/$l/changelogs/$VC.txt" ] || echo "MISSING: $l"
done
```

Match each locale's existing register rather than translating the English word
for word. Check the limit: 500 characters.

## Step 4: Verify the artifact, never the source tree

A source read is not evidence that a change reached the binary.

```bash
jarsigner -verify app/build/outputs/bundle/release/app-release.aab | head -1
grep -oE 'android:version(Code|Name)="[^"]*"' \
  app/build/intermediates/merged_manifests/release/*/AndroidManifest.xml
```

When the release changes an asset, hash it on both sides and require a match:

```bash
unzip -p <aab> 'base/res/*xxxhdpi*ic_launcher.png' | shasum -a 256
shasum -a 256 app/src/main/res/mipmap-xxxhdpi/ic_launcher.png
```

`jarsigner` reporting a self-signed certificate is correct under Play App
Signing, which re-signs with the real release key.

## Step 5: Upload to a testing track first

```bash
fastlane android internal
```

Build uploads carry the binary and its changelogs only. Listing text, icon,
feature graphic and screenshots move through a separate lane, so a routine
upload cannot rewrite what the store says about the app.

## Step 6: Promote, never re-upload

Play rejects a second bundle carrying a versionCode it already has. Re-uploading
is not a slower path to the same place, it is an error.

Promote the versionCode already on the testing track, which is also the only
thing that makes testing-first mean anything: the artifact reaching production is
the one that was validated, bit for bit.

```ruby
upload_to_play_store(
  version_code: <code>, track: "internal", track_promote_to: "production",
  skip_upload_aab: true, skip_upload_apk: true,
  release_status: "inProgress", rollout: "0.1"
)
```

## Step 7: Production halt

A production rollout is irreversible for the users who receive it. Stop and
present:

```text
Ready to promote versionCode <n> (<name>) to production at <pct>% of users.
Currently live: versionCode <m>. <one line on what users will notice>.
  1. Promote at <pct>%
  2. Promote at a different fraction
  3. Upload to a testing track only
  4. Hold
```

Then wait. Proceed on an explicit answer, and treat a standing instruction to
ship as that answer.

## Step 8: Read back what is actually live

The fastlane summary reports that the request succeeded, not what the release
became. Parameters like `track_promote_release_status` can differ from the
`release_status` you set, so read the track:

```
GET /androidpublisher/v3/applications/<pkg>/edits/<id>/tracks/production
```

Check three fields and say them plainly:

- `versionCodes`: the build users get.
- `status`: `inProgress` is a staged rollout; `completed` is everyone.
- `userFraction`: absent when `completed`.

A 100% rollout should land as `status: completed` with **no** `userFraction`. A
release sitting at `inProgress` with `userFraction: 1.0` is a different state
that reads the same in a success message. Confirm which one you got.

Also confirm every locale you wrote appears in that release's `releaseNotes`.

## Done means

Every line proven by a command in this run:

- Preflight opened and deleted a real Play edit.
- The AAB verified: signature, versionCode in the merged manifest, and a hash
  match for any changed asset.
- The track readback shows the expected versionCode, status, and fraction.
- Every locale with listing copy appears in the live release's notes.

## Boundaries

1. Do not promote to production, raise a rollout, or halt one without an
   explicit instruction covering that action.
2. Do not create the Play Console grant yourself; it is a UI action. Name the
   email and permissions and hand it to the user.
3. Do not print, commit, or copy the service-account JSON, the upload keystore,
   or `keystore.properties` into a repo.
4. Do not push listing text, images, or screenshots as part of a build upload.
   Store copy moves in its own deliberate step.
5. Do not report a release state from a fastlane summary. Read the track.
6. Do not reuse a billing or purchase-verification service account for
   publishing.
7. Do not edit a changelog for a versionCode already serving users to fix a
   typo silently; that changes live store copy and belongs in the same
   confirmation as a rollout change.

## Routing

- Need to plan, build, test, or policy-check the app itself -> use
  `android-app-factory`, then return here for delivery.
- Need listing text, keywords, screenshots, or ratings work -> use
  `suede-aso`. Listing changes travel in their own deliberate step (Boundary 4),
  so plan them there and ship them separately from the binary.
- Need CI wiring, required checks, or merge gates around the release -> use
  `suede-ci-gate`.
- Need branch, worktree, or stale-mirror handling for the release branch, or
  the iOS half of the same release -> private Suede AI companions, not in this
  pack.
- Need constants to match across the Android, iOS and web surfaces -> use
  `suede-parity-contract`.
- From `android-app-factory`: route Play credential setup, upload,
  track promotion, staged rollout, and live-state verification back here.
