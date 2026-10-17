# Notification & Attention Design

Notifications are a cross-cutting concern that affects every product. This reference covers notification types, delivery channels, attention management, and permission patterns for responsible notification design.

---

## Notification Types

### By Purpose

| Type | Description | Priority | Example |
|------|-------------|----------|---------|
| **Transactional** | Result of a user action | High | "Order confirmed", "Payment received" |
| **Informational** | System updates or status | Medium | "Maintenance scheduled", "Export ready" |
| **Social** | Activity from other users | Medium | "Alex commented on your post" |
| **Promotional** | Marketing or upsell | Low | "Try our new feature", "Upgrade plan" |
| **Alert** | Urgent system or security | Critical | "Unusual sign-in detected", "Server down" |

### By Urgency

```
Critical   ████████████  Requires immediate action (security, data loss)
High       █████████░░░  Important, time-sensitive (mentions, assignments)
Medium     ██████░░░░░░  Relevant but not urgent (comments, updates)
Low        ███░░░░░░░░░  Nice to know (tips, promotions)
Info       █░░░░░░░░░░░  Background context (changelog, analytics)
```

---

## Severity & Visual Hierarchy

### Standard Severity Levels

```css
/* Critical — Blocking issue, requires immediate attention */
.alert-critical {
  background: #fef2f2;
  border-left: 4px solid #dc2626;
  color: #991b1b;
}

/* Warning — Potential issue, user should be aware */
.alert-warning {
  background: #fffbeb;
  border-left: 4px solid #f59e0b;
  color: #92400e;
}

/* Success — Positive confirmation */
.alert-success {
  background: #f0fdf4;
  border-left: 4px solid #16a34a;
  color: #166534;
}

/* Info — Neutral information */
.alert-info {
  background: #eff6ff;
  border-left: 4px solid #3b82f6;
  color: #1e40af;
}
```

### Visual Priority

| Element | Critical | Warning | Info | Success |
|---------|----------|---------|------|---------|
| Icon | ⛔ / 🔴 | ⚠️ / 🟡 | ℹ️ / 🔵 | ✅ / 🟢 |
| Color | Red | Yellow/Amber | Blue | Green |
| Position | Modal/top banner | Top banner | Inline/toast | Toast |
| Sound | Optional alert | None | None | None |
| Persistence | Until resolved | Until dismissed | Auto-dismiss | Auto-dismiss |

---

## Delivery Channels

### Channel Selection Guide

```
                   Urgency
                High ──────────── Low
              │                        │
  Sync        │  Modal      Banner     │
  (blocking)  │  Alert      Inline     │
              │                        │
              │  Push        Email     │
  Async       │  Toast       Badge    │
  (non-block) │  SMS      In-app feed │
              │                        │
```

### In-App Notifications

#### Banners (Persistent)

```
┌───────────────────────────────────────────────────┐
│ ⚠️ Your trial expires in 3 days. [Upgrade now] [✕] │
└───────────────────────────────────────────────────┘
┌─────────────────── Page Content ──────────────────┐
```

- Fixed at top or bottom of viewport
- Persist until dismissed or condition resolved
- Use for: system-wide announcements, degraded service, account alerts
- Include clear action button and dismiss option
- Maximum 1-2 banners visible at a time

#### Toasts / Snackbars

```
                              ┌──────────────────────────┐
                              │ ✅ Document saved         │
                              │            [Undo] [✕]    │
                              └──────────────────────────┘
```

**Duration guidelines:**
- Short messages (no action): 4 seconds
- Messages with action button: 6-8 seconds
- Error messages: 8-10 seconds or until dismissed
- Never auto-dismiss critical errors

**Placement:**
- Bottom-center or bottom-right (most common)
- Top-center for important alerts
- Consistent position throughout the app
- Away from primary interaction areas

**Stacking:**
```
┌──────────────────────────────┐
│ ✅ File uploaded              │  ← newest
└──────────────────────────────┘
┌──────────────────────────────┐
│ ℹ️ 2 team members online     │  ← older
└──────────────────────────────┘

Max stack: 3 toasts visible
Older toasts slide out or collapse
```

- Stack newest on top
- Maximum 3 visible at once
- Older toasts auto-dismiss to make room
- All toasts dismissible with close button or swipe

#### Badges

```
┌────────────────────────────────────────┐
│  [🔔 3]  [📨 12]  [👤]                │
└────────────────────────────────────────┘
```

**Design rules:**
- Numeric badge: 1-99, then "99+" for overflow
- Dot badge: for "something new" without specific count
- Position: top-right of the icon
- Color: red for requiring attention, blue/gray for informational
- Clear on interaction (opening the relevant section)
- Animate on increment (subtle scale pulse)

#### Modals / Dialogs

Reserve for critical interruptions that require immediate user decision.

```
┌─────────────────────────────────────────┐
│  ⚠️ Unsaved Changes                     │
│                                          │
│  You have unsaved changes that will be   │
│  lost if you leave this page.            │
│                                          │
│  [Discard Changes]  [Save & Continue]    │
└──────────────────────────────────────────┘
```

- Only for actions that require a decision
- Never for informational messages (use toast/banner instead)
- Always provide a clear way to dismiss (Esc, close button, outside click)
- Maximum 1 modal at a time (never stack modals)
- Include a clear primary action

#### Inline Notifications

```
┌─────────────────────────────────────────┐
│  Email: [user@example.com          ]    │
│  ⚠️ This email is already in use.       │
│     [Sign in instead?]                  │
└─────────────────────────────────────────┘
```

- Placed directly next to the relevant content
- Contextual and specific to the user's action
- Best for: form validation, field-level errors, contextual tips
- Don't require dismissal (disappear when issue is resolved)

### External Channels

#### Push Notifications

```
┌─────────────────────────────────────────┐
│ 🔔 AppName                     now      │
│ Alex commented on "Q4 Report"           │
│ "Great analysis! Can we discuss the..." │
└─────────────────────────────────────────┘
```

- Ask permission contextually (not on first visit)
- Group related notifications (3+ from same thread → summary)
- Deep-link to the relevant content
- Rich notifications: image previews, action buttons
- Respect quiet hours (system settings or app-level)

#### Email Notifications

- Batch non-urgent notifications (daily/weekly digest)
- Include unsubscribe link in every email (CAN-SPAM, GDPR)
- One-click unsubscribe header (RFC 8058)
- Clear sender name and subject line
- Deep-link to specific content in the app

---

## Notification Center

### Inbox Pattern

```
┌─ Notifications ─────────────────────────┐
│  [All] [Unread (5)] [Mentions]          │
│                                          │
│  Today                                   │
│  ┌────────────────────────────────────┐  │
│  │ 🔵 Alex commented on "Q4 Report"  │  │
│  │    "Looks great! One question..."  │  │
│  │    2 hours ago            [···]    │  │
│  ├────────────────────────────────────┤  │
│  │ 🔵 Build #142 passed              │  │
│  │    main branch — all tests green   │  │
│  │    3 hours ago            [···]    │  │
│  ├────────────────────────────────────┤  │
│  │    Sarah shared "Design Brief"     │  │
│  │    5 hours ago            [···]    │  │
│  └────────────────────────────────────┘  │
│                                          │
│  Yesterday                               │
│  ┌────────────────────────────────────┐  │
│  │    Invoice #1234 paid              │  │
│  │    Yesterday at 4:32 PM   [···]    │  │
│  └────────────────────────────────────┘  │
│                                          │
│  [Mark all as read]                      │
└──────────────────────────────────────────┘
```

**Features:**
- Read/unread visual distinction (dot, bold, background color)
- Grouping by time (Today, Yesterday, This week, Older)
- Filter tabs (All, Unread, Mentions, specific categories)
- Bulk actions: mark all as read, clear all
- Individual actions: mark read/unread, mute thread, delete
- Clicking notification navigates to relevant content
- Infinite scroll with loading states
- "You're all caught up" message when empty

---

## Attention Management

### Interruption Budget

Not all notifications deserve equal interruption.

```
Daily interruption budget (suggested maximums):
├── Critical alerts: No limit (safety/security)
├── High-priority (mentions, assignments): 10-15
├── Medium (comments, updates): Batched 2-3x/day
├── Low (tips, promotions): 1/day maximum
└── Passive (badges, feed): Zero interruption
```

### Do Not Disturb

```
┌─ Focus Mode ────────────────────────────┐
│                                          │
│  [🔕 Do Not Disturb]  Until: [1 hour ▾] │
│                                          │
│  Allow through:                          │
│  [✓] Direct mentions                    │
│  [✓] Critical system alerts             │
│  [ ] Comments on my items               │
│  [ ] Team updates                        │
│                                          │
│  Schedule:                               │
│  [ ] Auto-enable outside work hours      │
│      Work hours: [9:00] - [17:00]        │
│                                          │
│  [Save]                                  │
└──────────────────────────────────────────┘
```

### Notification Preferences

```
┌─ Notification Settings ─────────────────┐
│                                          │
│  Channel          In-app  Push   Email   │
│  ─────────────────────────────────────── │
│  Mentions          ✓      ✓      ✓      │
│  Comments          ✓      ✓      ○      │
│  Updates           ✓      ○      ○      │
│  Marketing         ○      ○      ○      │
│                                          │
│  ✓ = enabled  ○ = disabled               │
│                                          │
│  Email digest: [Weekly ▾]                │
│                                          │
│  [Save preferences]                      │
└──────────────────────────────────────────┘
```

- Per-category, per-channel control
- Sensible defaults (not everything on)
- Email digest option for batching
- Quick "mute all" toggle
- Accessible from notification center and settings

### Batching & Grouping

```
Instead of 5 separate notifications:
  "Alex commented on Project X"
  "Alex commented on Project X"
  "Sarah commented on Project X"
  "Alex commented on Project X"
  "Jordan commented on Project X"

Send 1 grouped notification:
  "4 new comments on Project X from Alex, Sarah, and Jordan"
```

- Group by thread/topic, not by user
- Show count and participant summary
- Batch non-urgent notifications (5-15 minute window)
- Expand to individual items on click

---

## Permission Requests

### Just-in-Time Permissions

```
❌ On first visit:
"AppName wants to send you notifications"
[Don't Allow]  [Allow]

✅ In context, when relevant:
┌─────────────────────────────────────────┐
│  Want to know when someone replies?     │
│                                         │
│  Get notified when team members         │
│  respond to your comments.              │
│                                         │
│  [Enable Notifications]  [Not now]      │
└─────────────────────────────────────────┘
→ Then triggers the browser permission prompt
```

### Pre-Permission Pattern

Before triggering the system permission dialog:

1. **Explain value**: Why the user benefits from this permission
2. **Show in context**: When the permission is relevant to what they're doing
3. **Custom prompt first**: Your own UI before the system dialog
4. **Respect "not now"**: Don't ask again for at least 30 days
5. **Never on first visit**: Wait until user has experienced product value

### Permission Denied Recovery

```
When user denied permission:
┌─────────────────────────────────────────┐
│  ℹ️ Notifications are disabled           │
│                                          │
│  To enable notifications:               │
│  1. Click the lock icon in your browser │
│  2. Find "Notifications"               │
│  3. Change to "Allow"                   │
│                                          │
│  [Show me how]                           │
└─────────────────────────────────────────┘
```

- Provide clear instructions to re-enable in browser/OS settings
- Don't repeatedly nag about denied permissions
- Offer email as a fallback channel
- Show relevant instructions per browser/platform

---

## Key Metrics

| Metric | Target | Context |
|--------|--------|---------|
| Push opt-in rate | > 50% | Permission acceptance |
| Notification open rate | > 15% | Push engagement |
| Email unsubscribe rate | < 0.5%/email | List health |
| Toast dismissal rate | Track | Too many = too noisy |
| Notification → action | > 25% | Relevance indicator |
| Permission ask timing | After activation | Not on first visit |
| DND usage | Monitor | High = too noisy overall |

---

## Anti-Patterns

1. **Permission on first visit** — Asking for push permission before user sees value
2. **Notification carpet bombing** — Sending every event as a push notification
3. **No notification preferences** — All-or-nothing notification control
4. **Stacking modals** — Multiple dialogs requiring sequential dismissal
5. **Auto-dismissing errors** — Critical errors that disappear before user reads them
6. **Same urgency for everything** — Treating promotions like security alerts
7. **No grouping** — 10 individual notifications for 10 comments on the same thread
8. **Notification-only features** — Actions only accessible through notification center
9. **Dark pattern nudging** — "You have 0 notifications" as a growth hack
10. **Ignoring quiet hours** — Sending push notifications at 3 AM

---

## Sources

- [Material Design: Notifications](https://m3.material.io/foundations/content-design/notifications) — Component patterns
- [Apple HIG: Notifications](https://developer.apple.com/design/human-interface-guidelines/notifications) — Platform guidelines
- [Nielsen Norman Group: Notification UX](https://www.nngroup.com/articles/push-notification/) — Research
- [Intercom: Notification Design](https://www.intercom.com/blog/) — SaaS patterns
- [Web Push Protocol](https://web.dev/articles/push-notifications-overview) — Technical implementation
- [RFC 8058](https://datatracker.ietf.org/doc/html/rfc8058) — One-click unsubscribe
