# Worked delivery contract

This synthetic scenario demonstrates the expected artifact shape; its numbers and outcomes are example inputs, not measured customer results.

## Input

Convert an owned recipe PWA into an iOS app. It has responsive recipe pages and saved favorites; the requested native value is offline saved recipes and share-sheet import. No submission is authorized.

## Expected output

Write SITE_TO_IOS_AUDIT.md with dated inspected routes, auth/payment/privacy behavior and the 4.2 risk. Write SITE_TO_IOS_PLAN.md choosing a bundled or native-shell route from those observations, naming offline storage, share import, error/retry states, build command, simulator target and QA matrix. Keep bundle/signing ownership unresolved until evidence supplies it.

## Failure case

The URL requires a login the agent cannot use. Audit accessible routes and supplied source, list the blocked authenticated flows and request an authorized test path. Do not invent login, account deletion or purchase behavior.

## Validation

Run the chosen build command on the named target; test cold-start deep link, airplane-mode favorites, share import and cancellation. Distinguish a built shell from a reviewed submission package, and retain the 4.2 decision with evidence.

## Coverage and routing

Suede AI workflow for turning a live website, PWA, dashboard, or marketplace into an iOS app. Use when the user has a site or web app and asks to put it on the App Store, wrap it in an app, ship an iOS version, or convert a PWA to native. Produces SITE_TO_IOS_AUDIT.md and SITE_TO_IOS_PLAN.md: URL audit, shell-vs-native strategy, App Store Guideline 4.2 wrapper risk and the native value that mitigates it, current SDK, privacy manifest, age rating, login and payment checks, kids-app rules, QA matrix, and a release gate. NOT FOR: Android builds or conversions (use android-app-factory); Google Play uploads and rollouts (use suede-play-release); App Store listing, keyword, and screenshot strategy (use suede-aso).
