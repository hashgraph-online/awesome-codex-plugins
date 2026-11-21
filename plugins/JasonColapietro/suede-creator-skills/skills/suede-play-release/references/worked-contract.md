# Suede AI Google Play Release Skills: Worked Contract

Synthetic release evidence example; the values are not a live package or an executed rollout.

## Input

The requester authorizes promotion of versionCode 42 from internal testing to a 10% production rollout. They provide the package id, AAB hash, locale release notes, and an existing publishing configuration. No credential rotation or new account grant is authorized.

## Expected output

Run the configured preflight, confirm the selected artifact versionCode and hash, pull current release state, and promote the existing versionCode rather than uploading a rebuilt bundle. Preserve the locale changelogs. Return the Play API readback showing the track, versionCode, status and userFraction, together with command exit status and timestamp. Claim a 10% staged rollout only if the API actually returns userFraction 0.1 for the intended release.

## Missing input and recovery

A preflight 403 means release access is missing, not that a new key should be created automatically. Report the exact failing action and required Play Console grant, with the existing completed artifact checks. Do not claim upload or promotion. If fastlane reports success but readback is unavailable, record the mutation as uncertain and inspect current track state before retrying; a second upload is not a verification step.

## Validation

Compare the artifact's versionCode against both source testing and target production track. Check all expected locales, the rollout fraction, and release status. A mismatch between fastlane output and API state remains an unresolved delivery result. Preserve the production halt decision in Step 7 and never broaden the requested 10% rollout to completion.

## Detailed scope and routing

Suede AI Google Play delivery skill: ship an Android release from the agent interface and prove what is live. Preflight the publishing credential with a real Play API call, upload an AAB to a testing track, promote that exact versionCode, stage or complete a rollout, write per-locale release notes, and read back versionCode, status, and userFraction from the Play Developer API. One step stays a Play Console action the user takes: the first release-access grant for the service account. Use when uploading or promoting an Android build, wiring a Play service account and fastlane supply lanes, fixing per-versionCode changelogs, raising or halting a staged rollout, or answering what production is really serving. NOT FOR: planning, building, or policy-checking the app (use android-app-factory); Play listing, keyword, and screenshot work (use suede-aso); CI required checks (use suede-ci-gate).
