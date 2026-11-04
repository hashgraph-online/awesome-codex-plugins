# Activation Experiment Ideas

Candidate tests from signup through first value. Design, sizing, and stopping rules belong to `suede-ab-testing`; this file only supplies the candidates.

## Contents
- Signup Experiments (form design, identity options, copy and trust, trial and commitment, post-submit)
- Flow Simplification Experiments (reduce friction, step sequencing, progress & motivation)
- Guided Experience Experiments (product tours, CTA optimization, UI guidance)
- Personalization Experiments (user segmentation, dynamic content)
- Quick Wins & Engagement Experiments (time-to-value, motivation mechanics, support & help)
- Email & Multi-Channel Experiments (onboarding emails, email content, feedback loops)
- Re-engagement Experiments (stalled user recovery, return experience)
- Technical & UX Experiments (performance, mobile onboarding, accessibility)
- Metrics to Track

## Signup Experiments

### Form design
- Single-step vs. multi-step; multi-step with and without a progress bar
- Minimum fields (email plus password or identity provider) vs. current set
- Add or remove phone, company, and role fields
- One "Full name" field vs. first/last split
- Form embedded on the landing page vs. a separate signup page

### Identity options
- Add passkeys alongside password
- Social or SSO buttons above vs. below the email form
- Which providers to show for this audience (Google, Apple, Microsoft, GitHub)
- Magic link or one-time code vs. password

### Copy and trust
- Headline and button text ("Create account" vs. "Start free trial" vs. "Get started")
- Trial length stated in the button
- Social proof or security note beside the form
- Password requirements shown up front vs. on error

### Trial and commitment
- Card required vs. not required for trial (with renewal terms disclosed either way)
- Trial length (7 vs. 14 vs. 30 days)
- Full-access trial vs. feature-limited trial; freemium vs. trial
- Email verification required up front vs. delayed vs. gated to specific actions
- Invisible bot checks vs. puzzle CAPTCHA

### Post-submit
- Instant product access vs. confirm-email-first
- Auto-login vs. separate login
- Personalized welcome based on the use-case answer

## Flow Simplification Experiments

### Reduce Friction

| Test | Hypothesis |
|------|------------|
| Email verification timing | During vs. after onboarding |
| Empty states vs. dummy data | Pre-populated examples |
| Pre-filled templates | Accelerate setup with templates |
| OAuth options | Faster account linking |
| Required step count | Fewer required steps |
| Optional vs. required fields | Minimize requirements |
| Skip options | Allow bypassing non-critical steps |

### Step Sequencing

| Test | Hypothesis |
|------|------------|
| Step ordering | Test different sequences |
| Value-first ordering | Highest-value features first |
| Friction placement | Move hard steps later |
| Required vs. optional balance | Ratio of required steps |
| Single vs. branching paths | One path vs. personalized |
| Quick start vs. full setup | Minimal path to value |

### Progress & Motivation

| Test | Hypothesis |
|------|------------|
| Progress bars | Show completion percentage |
| Checklist length | 3-5 items vs. 5-7 items |
| Gamification | Badges, rewards, achievements |
| Completion messaging | "X% complete" visibility |
| Starting point | Begin at 20% vs. 0% |
| Celebration moments | Acknowledge completions |

---

## Guided Experience Experiments

### Product Tours

| Test | Hypothesis |
|------|------------|
| Interactive tours | Tools like Navattic, Storylane |
| Tooltip vs. modal guidance | Subtle vs. attention-grabbing |
| Video tutorials | For complex workflows |
| Self-paced vs. guided | User control vs. structured |
| Tour length | Shorter vs. comprehensive |
| Tour triggering | Automatic vs. user-initiated |

### CTA Optimization

| Test | Hypothesis |
|------|------------|
| CTA text variations | Action-oriented copy testing |
| CTA placement | Position within screens |
| In-app tooltips | Feature discovery prompts |
| Sticky CTAs | Persist during onboarding |
| CTA contrast | Visual prominence |
| Secondary CTAs | "Learn more" vs. primary only |

### UI Guidance

| Test | Hypothesis |
|------|------------|
| Hotspot highlights | Draw attention to key features |
| Coachmarks | Contextual tips |
| Feature announcements | New feature discovery |
| Contextual help | Help where users need it |
| Search vs. guided | Self-service vs. directed |

---

## Personalization Experiments

### User Segmentation

| Test | Hypothesis |
|------|------------|
| Role-based onboarding | Different paths by role |
| Goal-based paths | Customize by stated goal |
| Role-specific dashboards | Relevant default views |
| Use-case question | Personalize based on answer |
| Industry-specific paths | Vertical customization |
| Experience-based | Beginner vs. expert paths |

### Dynamic Content

| Test | Hypothesis |
|------|------------|
| Personalized welcome | Name, company, role |
| Industry examples | Relevant use cases |
| Dynamic recommendations | Based on user answers |
| Template suggestions | Pre-filled for segment |
| Feature highlighting | Relevant to stated goals |
| Benchmark data | Industry-specific metrics |

---

## Quick Wins & Engagement Experiments

### Time-to-Value

| Test | Hypothesis |
|------|------------|
| First quick win | "Complete your first X" |
| Success messages | After key actions |
| Progress celebrations | Milestone moments |
| Next step suggestions | After each completion |
| Value demonstration | Show what they achieved |
| Outcome preview | What success looks like |

### Motivation Mechanics

| Test | Hypothesis |
|------|------------|
| Achievement badges | Gamification elements |
| Streaks | Consecutive day engagement |
| Leaderboards | Social comparison (if appropriate) |
| Rewards | Incentives for completion |
| Unlock mechanics | Features revealed progressively |

### Support & Help

| Test | Hypothesis |
|------|------------|
| Free onboarding calls | For complex products |
| Contextual help | Throughout onboarding |
| Chat support | Availability during onboarding |
| Proactive outreach | For stuck users |
| Self-service resources | Help docs, videos |
| Community access | Peer support early |

---

## Email & Multi-Channel Experiments

### Onboarding Emails

| Test | Hypothesis |
|------|------------|
| Founder welcome email | Personal vs. generic |
| Behavior-based triggers | Action/inaction based |
| Email timing | Immediate vs. delayed |
| Email frequency | More vs. fewer touches |
| Quick tips format | Short actionable content |
| Video in email | More engaging format |

### Email Content

| Test | Hypothesis |
|------|------------|
| Subject lines | Open rate optimization |
| Personalization depth | Name vs. behavior-based |
| CTA prominence | Single clear action |
| Social proof inclusion | Testimonials in email |
| Urgency messaging | Trial reminders |
| Plain text vs. designed | Format testing |

### Feedback Loops

| Test | Hypothesis |
|------|------------|
| NPS during onboarding | When to ask |
| Blocking question | "What's stopping you?" |
| NPS follow-up | Actions based on score |
| In-app feedback | Thumbs up/down on features |
| Survey timing | When to request feedback |
| Feedback incentives | Reward for completing |

---

## Re-engagement Experiments

### Stalled User Recovery

| Test | Hypothesis |
|------|------------|
| Re-engagement email timing | When to send |
| Personal outreach | Human vs. automated |
| Simplified path | Reduced steps for returners |
| Incentive offers | Discount or extended trial |
| Problem identification | Ask what's blocking |
| Demo offer | Live walkthrough |

### Return Experience

| Test | Hypothesis |
|------|------------|
| Welcome back message | Acknowledge return |
| Progress resume | Pick up where left off |
| Changed state | What happened while away |
| Re-onboarding | Fresh start option |
| Urgency messaging | Trial time remaining |

---

## Technical & UX Experiments

### Performance

| Test | Hypothesis |
|------|------------|
| Load time optimization | Faster = higher completion |
| Progressive loading | Perceived performance |
| Offline capability | Mobile experience |
| Error handling | Graceful failure recovery |

### Mobile Onboarding

| Test | Hypothesis |
|------|------------|
| Touch targets | Size and spacing |
| Swipe navigation | Mobile-native patterns |
| Screen count | Fewer screens needed |
| Input optimization | Mobile-friendly forms |
| Permission timing | When to ask |

### Accessibility

| Test | Hypothesis |
|------|------------|
| Screen reader support | Accessibility impact |
| Keyboard navigation | Non-mouse users |
| Color contrast | Visibility |
| Font sizing | Readability |

---

## Metrics to Track

For all experiments, measure:

| Metric | Description |
|--------|-------------|
| Activation rate | % reaching activation event |
| Time to activation | Hours/days to first value |
| Step completion rate | % completing each step |
| Drop-off points | Where users abandon |
| Return rate | Users who come back |
| Day 1/7/30 retention | Engagement over time |
| Feature adoption | Which features get used |
| Support requests | Volume during onboarding |
