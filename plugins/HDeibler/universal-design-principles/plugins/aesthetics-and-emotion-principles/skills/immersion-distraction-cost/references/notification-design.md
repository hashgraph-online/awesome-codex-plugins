# Notification design — patterns

Practical patterns for designing notification systems that respect user attention.

## The notification taxonomy

Categorize notifications by urgency and required action:

**Critical / immediate.** True emergencies. Security alerts. Real-time conversations the user is actively in. Warrant immediate interruption.

**Important / soon.** Things the user wants to know within hours. Direct messages from collaborators. Significant updates to active work. Can be deferred briefly; should be batched.

**Useful / eventually.** Updates the user might want. Non-urgent activity from connections. Suggestions. Should be delivered in digest form.

**Engagement / not actually urgent.** "Come back!" messages. Daily reminders. "Don't miss out!" Often serve the product more than the user; question necessity.

Different categories warrant different delivery patterns.

## Pattern: real-time only for the critical category

Reserve real-time push notifications for genuinely critical or important matters. Default users to not receiving real-time notifications for the eventually-or-engagement categories.

## Pattern: batched delivery

For the important and useful categories, batch notifications:

- **Hourly digest.** For users who want frequent updates.
- **Daily digest.** Default for most users.
- **Weekly digest.** For low-frequency products or users who prefer minimal contact.

The batched delivery dramatically reduces interruption count without losing the information.

## Pattern: configurable preferences

Let users choose what they receive and when:

- **Per-category controls.** Different notifications for different categories.
- **Quiet hours.** No notifications during user-specified periods (typically nights and weekends).
- **Channel selection.** Push vs. email vs. in-app, by category.
- **Frequency control.** Real-time vs. batched, with batch size configurable.

Conservative defaults; comprehensive controls.

## Pattern: in-app indicators for non-urgent updates

For updates that don't warrant interruption but the user might want to see, use in-app indicators (a badge on a navigation item, a "new" indicator on a panel) rather than push notifications. The user discovers the update when they next visit the app.

This pattern works for products users return to regularly. It doesn't work for products users only visit when notified.

## Pattern: smart timing

When notifications must be delivered, time them well:

- **Avoid late nights and early mornings.** Even non-urgent notifications during sleep hours feel intrusive.
- **Match user time zone.** A 9am notification means very different things in different time zones.
- **Detect and respect user activity.** Some products can detect when users are in deep work and suppress non-urgent notifications.
- **Batch by natural break points.** Deliver at the end of a focus session, not during one.

## Pattern: notification content that respects user time

For each notification, ask: does the user need to know this in this much detail right now?

- **Brief, scannable.** Notifications should communicate the essential in a glance.
- **Don't demand action.** Informational notifications are preferable to action-demanding ones. Let the user choose to act.
- **Provide context.** Why is this notification appearing? Users who understand notifications trust them more.
- **Avoid clickbait.** Notifications that overstate urgency or relevance damage trust.

## Pattern: respecting system focus modes

Modern operating systems have focus modes (iOS Focus, Android Do Not Disturb, macOS Focus). Honor them in your product.

- When the user is in a focus mode, suppress all but explicitly-marked-urgent notifications.
- Provide a way to mark notifications as urgent (so users can configure focus modes to allow them).
- Don't override focus modes for marketing or engagement notifications.

## Pattern: notification fatigue prevention

Watch for signs of fatigue:

- Users disabling notifications in settings.
- Click-through rate dropping over time.
- App uninstalls correlating with notification volume.
- Survey feedback about notifications.

When fatigue signs appear, reduce notification volume, not increase it. The instinct to "send better notifications more often" usually backfires.

## Pattern: opt-in for new notification types

When introducing a new kind of notification, default to off. Let users opt in. This:

- Respects users who have already calibrated their notification preferences.
- Limits backlash from a new noise source.
- Provides cleaner data on whether the notification type is wanted.

The alternative (default-on, with opt-out) generates short-term engagement gains and long-term trust damage.

## Pattern: end-of-session opportunities

Some prompts that aren't notifications can still wait for between-session moments:

- Onboarding tips after the user completes a task.
- Feature suggestions when the user returns from being away.
- Survey requests at moments of obvious value delivery.

These prompts are less intrusive than notifications because they appear in the product's natural flow.

## Anti-patterns

**Notification flooding.** Many notifications per day. Users habituate, then disable, then leave.

**Notifications that don't match content.** "Important update!" with trivial content. Trust erodes.

**Notifications that demand engagement.** "Tap to claim your reward!" Effectively forced interactions.

**Notifications without preferences.** No way for users to control what they receive.

**Override of focus modes.** Notifications during user-declared focus periods. Maximum trust damage.

**Sound and vibration on routine notifications.** Audio reinforcement for non-urgent matters; teaches users to ignore.

**Marketing pretending to be useful.** "Your weekly summary" that's actually a sales pitch. Discovered, never trusted again.

**Engagement notifications dressed as user-serving.** Notifications crafted to look like the user's friend or product activity but really driven by engagement metrics.

## Measurement

Track notification-related metrics:

- **Click-through rate.** Are users engaging with notifications? Declining CTR signals fatigue.
- **Disable rate.** What % of users disable notifications after the first day? First week?
- **Attribution.** What percentage of returning users are notification-driven vs. organic?
- **User-reported satisfaction.** Surveys can reveal whether users feel notifications are valuable or annoying.

Optimize for sustainable engagement rather than peak engagement. A higher CTR achieved by sending fewer better notifications beats a lower CTR from sending more.

## A simple test

Look at your own notifications from your own product. Would you, as a user, want to receive these? Are they timed appropriately? Are they valuable? Or do they feel like noise?

The dogfooding test catches a lot of issues before users do.

## Cross-reference

For the parent principle, see `immersion`. For flow design, see `immersion-flow`.
