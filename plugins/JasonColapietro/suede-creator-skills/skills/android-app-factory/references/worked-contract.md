# Worked delivery contract

This synthetic scenario demonstrates the expected artifact shape; its numbers and outcomes are example inputs, not measured customer results.

## Input

Build an offline habit tracker for adults, with no account, ads, purchases, or sync. The repository has a Gradle wrapper and one Compose screen. Delivery is a local reviewable build, not a Play upload.

## Expected output

Return a Delivery Contract naming the offline core loop (create habit, mark today, reopen and retain state), package-ID placeholder, architecture choice and device/API matrix. Implement loading, empty and persisted states. Attach the actual Gradle test/lint/build command output and device evidence to the release gate. Mark billing, account deletion and child-directed rules not applicable with the stated scope as the reason; still inventory SDK data behavior.

## Failure case

The Gradle build passes but no emulator is available. Return the build artifact and passing commands, mark the core-loop runtime checks unverified and name the emulator/device action needed. A debug APK alone does not prove a signed AAB or release readiness.

## Validation

Reopen the installed app after process death and verify the saved habit remains. Match screenshots to the same build. A build failure retains the first actionable error and exact command; fix that cause before reporting a passing build.

## Coverage and routing

Suede AI Android app factory: plan, build, test, and prepare a production native Android app from product idea to a Play-ready signed bundle. Use for requests to create, ship, monetize, or modernize an Android app. Covers Kotlin and Jetpack Compose architecture, live target-API and Play policy checks, 16 KB page sizes, accessibility, privacy and Data Safety, Play Billing Library 8+, Play Integrity, account deletion, kids and Families rules, testing, performance, store assets, signing, and a release evidence gate. NOT FOR: uploading, promoting, or rolling out a build on Play (use suede-play-release); turning a website into an iOS app (use site-to-ios-app); a review-only pass on an existing app (use suede-code --findings-only); Play listing, keyword, and screenshot strategy (use suede-aso).
