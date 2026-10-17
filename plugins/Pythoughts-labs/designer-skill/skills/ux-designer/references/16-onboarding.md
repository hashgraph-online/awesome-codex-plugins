# Onboarding & User Activation

Onboarding is the critical bridge between sign-up and engaged usage. This reference covers patterns for first-run experiences, progressive disclosure, activation metrics, and re-engagement.

---

## Onboarding Patterns

### Product Tours

```
┌─────────────────────────────────────────┐
│  ┌──────────────────────────────┐       │
│  │  Step 2 of 4                 │       │
│  │  ─────────────               │       │
│  │  Create your first project   │       │
│  │                              │       │
│  │  Click the + button to get   │       │
│  │  started with a new project. │       │
│  │                              │       │
│  │  [Back]  [Next]  [Skip tour] │       │
│  └──────────────────────────────┘       │
│              ▼                           │
│         [ + New Project ]                │
└─────────────────────────────────────────┘
```

**Best practices:**
- Keep tours to 3-5 steps maximum
- Highlight one feature per step with a spotlight/overlay
- Always allow skipping ("Skip tour" visible on every step)
- Point to the actual UI element being described
- Show progress indicator (step N of M)
- Trigger contextually, not on every login

### Tooltip Walkthroughs

```
                    ┌──────────────────────┐
                    │ 💡 Quick tip          │
                    │ Use / to search       │
                    │ commands quickly.     │
                    │                       │
                    │ [Got it] [Show more]  │
                    └───────┬──────────────┘
                            ▼
┌────────────────────────────────────────┐
│ [Search commands... /]                 │
└────────────────────────────────────────┘
```

- Appear in context when user first encounters a feature
- One tooltip at a time (never stack)
- Dismissible and don't block interaction with the feature
- "Got it" dismisses permanently; "Show more" opens full docs
- Respect dismissals (don't re-show on next session)

### Onboarding Checklists

```
┌─ Getting Started ───────────────────────┐
│                                          │
│  ✅ Create your account                  │
│  ✅ Set up your profile                  │
│  🔲 Invite a team member                 │
│  🔲 Create your first project            │
│  🔲 Connect an integration               │
│                                          │
│  ████████████░░░░░░░░  60% complete      │
│                                          │
│  [Dismiss checklist]                     │
└──────────────────────────────────────────┘
```

**Best practices:**
- 4-6 items (not overwhelming)
- Pre-check completed items (account creation counts!)
- Progress bar/percentage for motivation
- Link each item directly to the relevant action
- Dismissible but recoverable from settings
- Celebrate completion (confetti, congratulations message)
- Order items by value delivered, not complexity

### Empty States as Onboarding

```
┌─────────────────────────────────────────┐
│                                          │
│          📁                              │
│     No projects yet                      │
│                                          │
│  Create your first project to start      │
│  collaborating with your team.           │
│                                          │
│  [+ Create Project]                      │
│                                          │
│  Or try a template:                      │
│  [Marketing Plan] [Sprint Board] [Wiki]  │
│                                          │
└─────────────────────────────────────────┘
```

- Show helpful illustration (not just "no data")
- Clear call-to-action for the logical next step
- Offer templates or sample data to reduce blank-page anxiety
- Brief explanation of what this area is for
- Never show a completely empty screen with no guidance

### Sample Data / Sandbox

- Pre-populated example data that demonstrates product value
- Clearly labeled as sample/demo data ("This is example data — delete anytime")
- Easy one-click removal when user is ready
- Shows real functionality, not just screenshots
- Avoids cluttering the user's actual workspace

---

## Progressive Disclosure

### Layered Complexity

```
Level 1 — Basic (default view):
┌────────────────────────────────┐
│  Name: [                    ]  │
│  Email: [                   ]  │
│                                │
│  [Save]                        │
└────────────────────────────────┘

Level 2 — Show more:
┌────────────────────────────────┐
│  Name: [                    ]  │
│  Email: [                   ]  │
│                                │
│  ▾ Advanced settings           │
│  ┌──────────────────────────┐  │
│  │ Role: [Admin ▾]          │  │
│  │ Team: [Engineering ▾]    │  │
│  │ Timezone: [Auto ▾]       │  │
│  └──────────────────────────┘  │
│                                │
│  [Save]                        │
└────────────────────────────────┘
```

**Principles:**
- Show the most common options by default
- Hide advanced options behind expandable sections
- Use sensible defaults so advanced options are rarely needed
- Label advanced sections clearly ("Advanced settings", "More options")
- Persist user's disclosure preference per section

### Feature Revelation Strategies

- **Usage-based**: Unlock features as users demonstrate readiness
- **Time-based**: Introduce features over first week of usage
- **Role-based**: Show features relevant to user's selected role
- **Need-based**: Surface features when context suggests need
- Avoid gating features artificially — if a user seeks them out, show them

---

## User Activation

### Defining Activation Metrics

```
Activation = user reached the "aha moment"

Examples:
- Slack: Sent first message in a channel
- Dropbox: Uploaded first file
- GitHub: Made first commit
- Figma: Created first design frame
- Notion: Created and shared first page
```

### Time-to-Value (TTV)

The time between sign-up and the user experiencing core product value.

**Optimization strategies:**
- Remove unnecessary sign-up steps (defer profile completion)
- Auto-configure based on sign-up context (role, company size)
- Pre-populate with relevant templates or data
- Guide users to the core action immediately
- Measure TTV and optimize for reduction

### The "Aha Moment"

```
Identify by analyzing:
1. What do retained users have in common?
2. What action separates retained from churned users?
3. How quickly do successful users reach this action?

Design toward it:
- Make the path to the aha moment as short as possible
- Remove friction between sign-up and first value
- Celebrate when users reach it
```

---

## Personalization

### Role-Based Onboarding

```
┌─────────────────────────────────────────┐
│  Welcome! What's your role?             │
│                                         │
│  ┌───────────┐  ┌──────────────┐        │
│  │ 🎨        │  │ 💻           │        │
│  │ Designer  │  │ Developer    │        │
│  └───────────┘  └──────────────┘        │
│  ┌───────────┐  ┌──────────────┐        │
│  │ 📊        │  │ 👤           │        │
│  │ Manager   │  │ Other        │        │
│  └───────────┘  └──────────────┘        │
│                                         │
│  This helps us customize your setup.    │
└─────────────────────────────────────────┘
```

- Ask 1-2 personalization questions max during sign-up
- Customize dashboard, default views, and feature highlights based on role
- Allow changing selection later without losing work
- Make it clear how this choice affects their experience
- Skip if irrelevant (single-purpose tools don't need role selection)

### Skill-Level Adaptation

- Detect usage patterns to infer expertise level
- Offer "beginner" vs. "experienced" onboarding paths
- Show keyboard shortcuts to power users, guided tours to beginners
- Progressively reduce hand-holding as usage increases
- Allow manual skill-level toggle in settings

---

## Sign-Up Flow

### Reducing Friction

```
Minimal sign-up (3 fields max):
┌────────────────────────────────┐
│  Get started                   │
│                                │
│  Email: [                   ]  │
│  Password: [                ]  │
│                                │
│  [Create Account]              │
│                                │
│  ── or continue with ──        │
│  [Google]  [GitHub]  [SSO]     │
│                                │
│  Already have an account?      │
│  Sign in                       │
└────────────────────────────────┘
```

**Best practices:**
- Social login / SSO options reduce friction significantly
- Defer non-essential fields (name, company) to post-sign-up
- Email-first flow: collect email, then ask for password on next step
- Magic link option for password-free sign-up
- Show password requirements inline, not after failed submission
- Single-field entry: email only, then decide sign-in vs. sign-up

### Progressive Profiling

Collect user information over time, not all at once.

```
Sign-up:    Email + password only
First use:  "What's your name?" (in-context)
Day 3:      "What's your team size?" (when relevant)
Day 7:      "Connect your calendar?" (when value is clear)
```

- Each request provides clear value to the user
- Ask in context (team size when inviting first member)
- Never block core features behind profile completion
- Show profile completion percentage (optional, gamification)

### Deferred Registration

- Let users try the product before requiring sign-up
- Save anonymous work and transfer to account on registration
- Show value before asking for commitment
- "Continue as guest" option where applicable

---

## First-Run Experience

### Blank Slate Design

Every empty screen is an opportunity to onboard:

| Screen | Instead of "No data" | Show |
|--------|---------------------|------|
| Dashboard | Empty widgets | Pre-configured widgets with sample data |
| Project list | "No projects" | Templates + "Create first project" CTA |
| Inbox | "No messages" | "Invite your team to start conversations" |
| Analytics | "No data yet" | "Connect a data source" + preview |

### Starter Templates

- Offer 3-5 templates relevant to user's role/industry
- Preview template before selecting
- "Start from scratch" always available
- Templates should be fully functional, not just layouts
- Allow customization immediately after selection

### Guided Setup Wizards

```
Step 1        Step 2         Step 3        Done!
[Profile] ──→ [Team] ──→ [Integrations] ──→ [🎉]
  ●             ○              ○              ○
```

- Maximum 3-5 steps
- Show progress and allow skipping each step
- Save progress if user abandons mid-wizard
- Offer "Do this later" for optional steps
- Each step should deliver immediate value

---

## Re-Engagement

### Return User Flows

```
┌─────────────────────────────────────────┐
│  Welcome back, Alex!                    │
│                                         │
│  Since you were last here:              │
│  • 3 new comments on "Q4 Report"        │
│  • Sarah shared "Design Brief" with you │
│  • Your trial ends in 5 days            │
│                                         │
│  [Go to Q4 Report]  [View all updates]  │
└─────────────────────────────────────────┘
```

- Show relevant updates since last visit
- Deep-link to unfinished work or pending actions
- Don't re-show completed onboarding steps
- Feature announcements for major changes only

### What's New Patterns

- Changelog accessible from a "What's new" menu item or badge
- Brief inline announcements for features relevant to user's workflow
- "New" badges on navigation items (auto-dismiss after first visit)
- Major updates: one-time modal with clear benefit statement
- Never block user workflow for feature announcements

---

## Measuring Success

### Key Metrics

| Metric | Target | How to measure |
|--------|--------|---------------|
| Sign-up completion | > 85% | Users who complete sign-up / started |
| Onboarding completion | > 65% | Users who finish checklist / total |
| Time to first value | < 5 min | Time from sign-up to activation event |
| Day 1 retention | > 40% | Users who return the day after sign-up |
| Day 7 retention | > 25% | Users who return within first week |
| Activation rate | > 30% | Users who reach aha moment / total sign-ups |
| Tour skip rate | Monitor | High skip may indicate poor tour design |
| Checklist item completion | Track per item | Identifies friction points |

### Drop-Off Analysis

- Funnel visualization for each onboarding step
- Identify where users abandon (highest drop-off = biggest opportunity)
- Segment by user source, role, and device
- A/B test onboarding variations against activation rate
- Qualitative: user session recordings of first-run experience

---

## Anti-Patterns

1. **Mandatory lengthy tours** — Forcing users through 10+ steps before they can use the product
2. **Information overload** — Teaching everything at once instead of progressively
3. **No skip option** — Trapping users in onboarding flows
4. **Ignoring return users** — Showing the same onboarding to returning users
5. **Empty states with no guidance** — "No data" with no next step
6. **Asking too much at sign-up** — 10-field registration forms
7. **Irrelevant personalization questions** — Asking role when it doesn't affect the experience
8. **Celebrating too early** — Confetti when user hasn't done anything meaningful yet
9. **Feature dumping** — Showing every feature in tooltips before user needs them
10. **No measurement** — Not tracking where users drop off in onboarding

---

## Sources

- [UserOnboard](https://www.useronboard.com/) — Real product onboarding teardowns
- [ProductLed: User Activation](https://productled.com/) — Activation frameworks
- [Appcues: State of User Onboarding](https://www.appcues.com/) — Onboarding benchmarks
- [Nielsen Norman Group: Onboarding](https://www.nngroup.com/articles/onboarding/) — UX research
- [Intercom: Onboarding](https://www.intercom.com/blog/onboarding/) — SaaS onboarding best practices
- [Reforge: Activation](https://www.reforge.com/) — Growth frameworks
