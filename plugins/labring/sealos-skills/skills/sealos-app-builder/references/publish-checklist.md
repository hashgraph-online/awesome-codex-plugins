# Publish Checklist

Use this reference when preparing a Sealos app for handoff, preview, or production launch.

## Functional checks

1. The app loads correctly when opened by Sealos Desktop.
2. The app handles direct browser access gracefully.
3. `getSession()` succeeds inside Desktop.
4. Business data writes are tied to the correct Sealos user.
5. Business data reads render correctly for real records.

## Configuration checks

1. Environment variables are documented and present.
2. Database migrations or schema setup are complete.
3. The package name and SDK imports match the target workspace.
4. Any required Desktop-side event names are confirmed.

## Release checks

1. The app has a stable URL or deployment target.
2. A Sealos Desktop test app is already verified against that URL.
3. Manual registration or platform configuration steps are written down.
4. Beginner-facing docs explain the Desktop runtime requirement.

## Recommended final summary

When handing off the work, summarize:

1. what was implemented
2. how to run it
3. how to validate it inside Sealos Desktop
4. which steps remain manual
