---
name: outbound-sequence-playbook
description: Every outbound sequence step by step, with the exact Zevari campaigns_v2_create program for each. Use when the user asks which sequence to run, how to route leads by ICP score and LinkedIn activity, how to build a LinkedIn or email campaign, or how to set up follow-ups, InMail or multichannel sequences.
---

> Synced copy of https://zevari.ai/guides/outbound-sequence-playbook.md. When Zevari is connected, `skills_get` with slug `outbound-sequence-playbook` returns the latest version: prefer it.

<!-- guide below: scripts/sync.sh replaces everything after this line -->

# Appendix: every sequence, written for an AI agent

This appendix lists every sequence in this playbook, step by step, in a form an AI agent can read and run in Zevari. A plain-text copy lives at https://zevari.ai/guides/outbound-sequence-playbook.md.

## How to build a sequence in Zevari

1. Call `zevari_context_get` and confirm with the user which workspace and LinkedIn account this campaign sends from, then call `zevari_context_confirm`. For a sequence with email steps, confirm the mailbox it sends from too.
2. Replace every `<write: …>` placeholder with finished copy. Zevari sends copy exactly as written. Never send the angle brackets.
3. Create the campaign with `campaigns_v2_create`: pass a `name`, the `sequence` array given under each campaign below, and `draft: true`.
4. Add leads with `campaigns_v2_add_leads`, passing each lead's identity unchanged. LinkedIn steps need the lead's LinkedIn profile ID saved. If a lead comes back unresolved, or found only through Sales Navigator, run `linkedin_get_profile` for it, then add it again.
5. Under manual approval, `campaigns_v2_add_leads` returns `approval.confirmation_id` and `approval.approval_url`. Show the user the URL. Once they approve, call `campaigns_v2_schedule` with the campaign id and that confirmation id, or nothing sends. On Autopilot, adding leads schedules the first steps straight away.

## Step types

| Step in this playbook | action_type | Config fields | Notes |
|---|---|---|---|
| View profile | view_profile | none | They see you looked. |
| Like a recent post | like_post | reaction (optional: like, celebrate, support, love, insightful, funny) | Uses their most recent post. Skipped if they have none. |
| Comment on a post | comment_on_post | comment_text (required) | Uses their most recent post. Zevari does not write comments: the same comment_text goes on every lead's post, so write one that fits any post, or leave the step out. |
| Connection request | connect | message (optional note, max 200 characters) | Leave message out for a blank invite. |
| LinkedIn message | message | body (required), generation_mode (optional) | With generation_mode "llm", body is a brief and Zevari drafts each lead's message from it. The programs below use it where a message has to mention the lead's own post or business. |
| InMail | inmail | body (required), subject (optional) | Needs a Premium or Sales Navigator sender. |
| Email | email_send | subject and body (both required) | Sends only to leads with a usable email. |

## Rules

- **Variables.** Copy may use {{first_name}}, {{last_name}}, {{full_name}} and {{company_name}}, with a fallback for an empty value: {{first_name|there}}. Any other {{…}} is rejected.
- **Timing.** delay_hours is the time after the previous step. Without branches, every step after the first needs at least 3 hours.
- **Branches.** Once one step has config.routing, every step needs it: {version: 1, id, next}. next is a later step's id, null (end), or a condition. Zevari has two conditions: connection_accepted (with invite, the connect step's id, and wait_hours, at most 720) and usable_email. The step right after a condition is timed from the decision: from the accept for yes, from the end of the wait for no.
- **Unanswered invites.** An invite that isn't accepted in time takes the "no" path or ends the sequence. Zevari withdraws pending invites separately, by the campaign's withdraw setting (by default 10 days after the invite was sent).
- **Replies.** A reply on any channel stops the lead: every remaining step in the sequence is skipped, and the conversation moves to the Inbox.
- **One sequence per campaign.** Campaigns are sequence-locked by default, so every lead runs exactly this sequence. Copy and delays stay editable later; the shape does not.

## Campaign sequences

### 1. Connect and say hi

- **Group:** Simple
- **Best for:** Your first campaign, or a free LinkedIn account.
- **Why it works:** One invite and one question. Most replies come from the first message after they accept, so prove this works by hand on 10 people before adding steps.

**Steps**

- **Lead enters**: Anyone on your list
- **Connection request**: No note
- **Accepted within 7 days?**: Waits for them to accept
  - If **Yes**:
    - wait 1 day, then **Message 1**: Thanks + one question
    - End.
  - If **No** (decided after 7 days):
    - End: not accepted in time.

**Zevari program** (the `sequence` for `campaigns_v2_create`)

```json
[
  {"action_type":"connect","delay_hours":0,"config":{"routing":{"version":1,"id":"invite","next":{"id":"accepted","kind":"connection_accepted","invite":"invite","wait_hours":168,"yes":"dm","no":null}}}},
  {"action_type":"message","delay_hours":24,"config":{"body":"<write: Thanks + one question>","routing":{"version":1,"id":"dm","next":null}}}
]
```

### 2. Three cold emails

- **Group:** Simple
- **Best for:** No LinkedIn profile, local businesses, smaller deals, ICP score 3 (Moderate fit).
- **Why it works:** Plain text, a short lowercase subject, no links. Every email gives a new reason to reply instead of “just checking in”.

**Steps**

- **Lead enters**: Has a work email
- **Email 1**: Trigger, question, proof, ask
- wait 3.5 days, then **Email 2**: A new angle
- wait 4 days, then **Email 3**: Short and personal
- End.

**Zevari program** (the `sequence` for `campaigns_v2_create`)

```json
[
  {"action_type":"email_send","delay_hours":0,"config":{"subject":"<write: subject, under 8 words>","body":"<write: Trigger, question, proof, ask>"}},
  {"action_type":"email_send","delay_hours":84,"config":{"subject":"<write: subject, under 8 words>","body":"<write: A new angle>"}},
  {"action_type":"email_send","delay_hours":96,"config":{"subject":"<write: subject, under 8 words>","body":"<write: Short and personal>"}}
]
```

### 3. Fit check: three emails (ICP score 3, Moderate fit)

- **Group:** Simple
- **Best for:** ICP score 3 (Moderate fit) leads: a maybe, not a priority.
- **Why it works:** ICP score 3 (Moderate fit) leads don't get your LinkedIn limits. A short, honest fit check by email lets the right ones raise their hand: just seeing if there's a fit, then the problem they may have, then one last fit check.

**Steps**

- **Lead enters**: ICP score 3 (Moderate fit), has email
- **Email 1**: Just seeing if there's a fit
- wait 3 days, then **Email 2**: The problem they may have
- wait 4 days, then **Email 3**: Still seeing if there's a fit
- End.

**Zevari program** (the `sequence` for `campaigns_v2_create`)

```json
[
  {"action_type":"email_send","delay_hours":0,"config":{"subject":"<write: subject, under 8 words>","body":"<write: Just seeing if there's a fit>"}},
  {"action_type":"email_send","delay_hours":72,"config":{"subject":"<write: subject, under 8 words>","body":"<write: The problem they may have>"}},
  {"action_type":"email_send","delay_hours":96,"config":{"subject":"<write: subject, under 8 words>","body":"<write: Still seeing if there's a fit>"}}
]
```

### 4. InMail, then email

- **Group:** Simple
- **Best for:** The 50 accounts you want most. Sales Navigator senders.
- **Why it works:** InMail credits are scarce, so spend them on your best fits and back each one up with an email.

**Steps**

- **Lead enters**: Your top named accounts
- **InMail**: No connection needed
- **Has email?**: checked as soon as the step before it finishes
  - If **Yes**:
    - wait 5 days, then **Email 1**: Follows up on the InMail
    - End.
  - If **No**:
    - End: No email, so it stops.

**Zevari program** (the `sequence` for `campaigns_v2_create`)

```json
[
  {"action_type":"inmail","delay_hours":0,"config":{"subject":"<write: subject>","body":"<write: No connection needed>","routing":{"version":1,"id":"inmail","next":{"id":"has_email","kind":"usable_email","yes":"email","no":null}}}},
  {"action_type":"email_send","delay_hours":120,"config":{"subject":"<write: subject, under 8 words>","body":"<write: Follows up on the InMail>","routing":{"version":1,"id":"email","next":null}}}
]
```

### 5. Already connected: three messages

- **Group:** Simple
- **Best for:** People you're already connected with. Waking up your network.
- **Why it works:** No invite to wait on, so the first message goes out on day one.

**Steps**

- **Lead enters**: Already connected with you
- **Message 1**: Ask about their business
- wait 3 days, then **Message 2**: A new angle on the problem
- wait 4 days, then **Message 3**: A low-friction offer
- End.

**Zevari program** (the `sequence` for `campaigns_v2_create`)

```json
[
  {"action_type":"message","delay_hours":0,"config":{"body":"Brief: Ask about their business. Draft it for this lead.","generation_mode":"llm"}},
  {"action_type":"message","delay_hours":72,"config":{"body":"<write: A new angle on the problem>"}},
  {"action_type":"message","delay_hours":96,"config":{"body":"<write: A low-friction offer>"}}
]
```

### 6. Connect, InMail if they don't accept

- **Group:** Standard
- **Best for:** Premium and Sales Navigator senders with InMail credits.
- **Why it works:** Not accepting isn't a no. Most people never saw the invite, and the InMail reaches them anyway.

**Steps**

- **Lead enters**: Anyone on your list
- **Connection request**: No note
- **Accepted within 7 days?**: Waits for them to accept
  - If **Yes**:
    - wait 1 day, then **Message 1**: Thanks + one question
    - wait 3 days, then **Message 2**: A new angle
    - End.
  - If **No** (decided after 7 days):
    - **InMail**: Same offer, no connection
    - End.

**Zevari program** (the `sequence` for `campaigns_v2_create`)

```json
[
  {"action_type":"connect","delay_hours":0,"config":{"routing":{"version":1,"id":"invite","next":{"id":"accepted","kind":"connection_accepted","invite":"invite","wait_hours":168,"yes":"dm1","no":"inmail"}}}},
  {"action_type":"message","delay_hours":24,"config":{"body":"<write: Thanks + one question>","routing":{"version":1,"id":"dm1","next":"dm2"}}},
  {"action_type":"message","delay_hours":72,"config":{"body":"<write: A new angle>","routing":{"version":1,"id":"dm2","next":null}}},
  {"action_type":"inmail","delay_hours":0,"config":{"subject":"<write: subject>","body":"<write: Same offer, no connection>","routing":{"version":1,"id":"inmail","next":null}}}
]
```

### 7. Connect, email if they don't accept

- **Group:** Standard
- **Best for:** Any list where you found emails for most leads.
- **Why it works:** LinkedIn first because it's warmer. Email catches everyone who didn't accept, so nobody falls through.

**Steps**

- **Lead enters**: Anyone on your list
- **Connection request**: No note
- **Accepted within 7 days?**: Waits for them to accept
  - If **Yes**:
    - wait 1 day, then **Message 1**: Thanks + one question
    - wait 3 days, then **Message 2**: A new angle
    - End.
  - If **No** (decided after 7 days):
    - **Has email?**: checked as soon as the step before it finishes
      - If **Yes**:
        - **Email 1**: Same offer, new channel
        - wait 3.5 days, then **Email 2**: A new angle
        - End.
      - If **No**:
        - End: No email, so it stops.

**Zevari program** (the `sequence` for `campaigns_v2_create`)

```json
[
  {"action_type":"connect","delay_hours":0,"config":{"routing":{"version":1,"id":"invite","next":{"id":"accepted","kind":"connection_accepted","invite":"invite","wait_hours":168,"yes":"dm1","no":{"id":"has_email","kind":"usable_email","yes":"email1","no":null}}}}},
  {"action_type":"message","delay_hours":24,"config":{"body":"<write: Thanks + one question>","routing":{"version":1,"id":"dm1","next":"dm2"}}},
  {"action_type":"message","delay_hours":72,"config":{"body":"<write: A new angle>","routing":{"version":1,"id":"dm2","next":null}}},
  {"action_type":"email_send","delay_hours":0,"config":{"subject":"<write: subject, under 8 words>","body":"<write: Same offer, new channel>","routing":{"version":1,"id":"email1","next":"email2"}}},
  {"action_type":"email_send","delay_hours":84,"config":{"subject":"<write: subject, under 8 words>","body":"<write: A new angle>","routing":{"version":1,"id":"email2","next":null}}}
]
```

### 8. Connect and four follow-ups

- **Group:** Standard
- **Best for:** The done-for-you default for most B2B lists.
- **Why it works:** Four messages over two weeks, each with a new reason to reply. The last one is personal, not a breakup message.

**Steps**

- **Lead enters**: Anyone on your list
- **Connection request**: No note
- **Accepted within 7 days?**: Waits for them to accept
  - If **Yes**:
    - wait 1 day, then **Message 1**: Icebreaker question
    - wait 3 days, then **Message 2**: Reframe the pain
    - wait 3 days, then **Message 3**: A low-friction offer
    - wait 4 days, then **Message 4**: A personal last note
    - End.
  - If **No** (decided after 7 days):
    - End: not accepted in time.

**Zevari program** (the `sequence` for `campaigns_v2_create`)

```json
[
  {"action_type":"connect","delay_hours":0,"config":{"routing":{"version":1,"id":"invite","next":{"id":"accepted","kind":"connection_accepted","invite":"invite","wait_hours":168,"yes":"dm1","no":null}}}},
  {"action_type":"message","delay_hours":24,"config":{"body":"<write: Icebreaker question>","routing":{"version":1,"id":"dm1","next":"dm2"}}},
  {"action_type":"message","delay_hours":72,"config":{"body":"<write: Reframe the pain>","routing":{"version":1,"id":"dm2","next":"dm3"}}},
  {"action_type":"message","delay_hours":72,"config":{"body":"<write: A low-friction offer>","routing":{"version":1,"id":"dm3","next":"dm4"}}},
  {"action_type":"message","delay_hours":96,"config":{"body":"<write: A personal last note>","routing":{"version":1,"id":"dm4","next":null}}}
]
```

### 9. Quiet on LinkedIn: email-led

- **Group:** Standard
- **Best for:** Good fits who haven't posted, liked or commented in 30 days.
- **Why it works:** If they aren't on LinkedIn, a message sits unread. Email does the work, and the invite is a bonus.

**Steps**

- **Lead enters**: Inactive on LinkedIn, has email
- **View profile**: They see you looked
- wait 1 day, then **Connection request**: With a note
- wait 1 day, then **Email 1**: Goes out either way
- wait 3.5 days, then **Email 2**: A new angle
- wait 4 days, then **Email 3**: Short and personal
- End.

**Zevari program** (the `sequence` for `campaigns_v2_create`)

```json
[
  {"action_type":"view_profile","delay_hours":0,"config":{}},
  {"action_type":"connect","delay_hours":24,"config":{"message":"<write: With a note, max 200 characters>"}},
  {"action_type":"email_send","delay_hours":24,"config":{"subject":"<write: subject, under 8 words>","body":"<write: Goes out either way>"}},
  {"action_type":"email_send","delay_hours":84,"config":{"subject":"<write: subject, under 8 words>","body":"<write: A new angle>"}},
  {"action_type":"email_send","delay_hours":96,"config":{"subject":"<write: subject, under 8 words>","body":"<write: Short and personal>"}}
]
```

### 10. Warm up, then connect

- **Group:** Standard
- **Best for:** Leads who post regularly.
- **Why it works:** By the time the invite lands, your name has already shown up twice in their notifications.

**Steps**

- **Lead enters**: Active on LinkedIn
- **View profile**: They see you looked
- wait 1 day, then **Like a recent post**
- wait 1 day, then **Connection request**: No note
- **Accepted within 7 days?**: Waits for them to accept
  - If **Yes**:
    - wait 1 day, then **Message 1**: Mention their post
    - wait 3 days, then **Message 2**: A low-friction offer
    - End.
  - If **No** (decided after 7 days):
    - End: not accepted in time.

**Zevari program** (the `sequence` for `campaigns_v2_create`)

```json
[
  {"action_type":"view_profile","delay_hours":0,"config":{"routing":{"version":1,"id":"view","next":"like"}}},
  {"action_type":"like_post","delay_hours":24,"config":{"reaction":"like","routing":{"version":1,"id":"like","next":"invite"}}},
  {"action_type":"connect","delay_hours":24,"config":{"routing":{"version":1,"id":"invite","next":{"id":"accepted","kind":"connection_accepted","invite":"invite","wait_hours":168,"yes":"dm1","no":null}}}},
  {"action_type":"message","delay_hours":24,"config":{"body":"Brief: Mention their post. Draft it for this lead.","generation_mode":"llm","routing":{"version":1,"id":"dm1","next":"dm2"}}},
  {"action_type":"message","delay_hours":72,"config":{"body":"<write: A low-friction offer>","routing":{"version":1,"id":"dm2","next":null}}}
]
```

### 11. LinkedIn-active core

- **Group:** Advanced
- **Best for:** ICP score 4 (Strong fit) leads active on LinkedIn in the last 30 days.
- **Why it works:** Three warm touches before the invite, four messages if they accept, and three emails if they don't. Every lead gets a full try on the channel that suits them.

**Steps**

- **Lead enters**: ICP score 4 (Strong fit), active on LinkedIn
- **View profile**: They see you looked
- wait 1 day, then **Like a recent post**
- wait 1 day, then **Comment on a post**: Specific, not generic
- wait 1 day, then **Connection request**: No note, or A/B test one
- **Accepted within 7 days?**: Waits for them to accept
  - If **Yes**:
    - wait 1 day, then **Message 1**: Icebreaker question
    - wait 3 days, then **Message 2**: Reframe the pain
    - wait 3 days, then **Message 3**: A low-friction offer
    - wait 4 days, then **Message 4**: A personal last note
    - End.
  - If **No** (decided after 7 days):
    - **Has email?**: checked as soon as the step before it finishes
      - If **Yes**:
        - **Email 1**: Same offer, new channel
        - wait 3.5 days, then **Email 2**: A new angle
        - wait 4 days, then **Email 3**: Short and personal
        - End.
      - If **No**:
        - End: not accepted in time.

**Before you build:** Zevari posts the same comment_text on every lead's most recent post, so it can't be specific to each lead. Write one short comment that fits any post, or leave the comment step out and comment by hand.

**Zevari program** (the `sequence` for `campaigns_v2_create`)

```json
[
  {"action_type":"view_profile","delay_hours":0,"config":{"routing":{"version":1,"id":"view","next":"like"}}},
  {"action_type":"like_post","delay_hours":24,"config":{"reaction":"like","routing":{"version":1,"id":"like","next":"comment"}}},
  {"action_type":"comment_on_post","delay_hours":24,"config":{"comment_text":"<write: a short comment that fits any post; the same text goes on every lead's latest post>","routing":{"version":1,"id":"comment","next":"invite"}}},
  {"action_type":"connect","delay_hours":24,"config":{"routing":{"version":1,"id":"invite","next":{"id":"accepted","kind":"connection_accepted","invite":"invite","wait_hours":168,"yes":"dm1","no":{"id":"has_email","kind":"usable_email","yes":"email1","no":null}}}}},
  {"action_type":"message","delay_hours":24,"config":{"body":"<write: Icebreaker question>","routing":{"version":1,"id":"dm1","next":"dm2"}}},
  {"action_type":"message","delay_hours":72,"config":{"body":"<write: Reframe the pain>","routing":{"version":1,"id":"dm2","next":"dm3"}}},
  {"action_type":"message","delay_hours":72,"config":{"body":"<write: A low-friction offer>","routing":{"version":1,"id":"dm3","next":"dm4"}}},
  {"action_type":"message","delay_hours":96,"config":{"body":"<write: A personal last note>","routing":{"version":1,"id":"dm4","next":null}}},
  {"action_type":"email_send","delay_hours":0,"config":{"subject":"<write: subject, under 8 words>","body":"<write: Same offer, new channel>","routing":{"version":1,"id":"email1","next":"email2"}}},
  {"action_type":"email_send","delay_hours":84,"config":{"subject":"<write: subject, under 8 words>","body":"<write: A new angle>","routing":{"version":1,"id":"email2","next":"email3"}}},
  {"action_type":"email_send","delay_hours":96,"config":{"subject":"<write: subject, under 8 words>","body":"<write: Short and personal>","routing":{"version":1,"id":"email3","next":null}}}
]
```

### 12. 5/5 MVP

- **Group:** Advanced
- **Best for:** Your 1–2 best-fit leads a day (ICP score 5, Strong fit, active, Sales Navigator sender).
- **Why it works:** The full warm-up, a shorter accept wait, then InMail and email so your best leads hear from you on every channel.

**Steps**

- **Lead enters**: ICP score 5 (Strong fit), active on LinkedIn
- **View profile**: They see you looked
- wait 1 day, then **Like a recent post**
- wait 1 day, then **Comment on a post**: Specific, not generic
- wait 1 day, then **Connection request**: A personal note
- **Accepted within 5 days?**: Waits for them to accept
  - If **Yes**:
    - wait 1 day, then **Message 1**: Icebreaker question
    - wait 3 days, then **Message 2**: Their objection, answered
    - wait 3 days, then **Message 3**: A low-friction offer
    - End.
  - If **No** (decided after 5 days):
    - **InMail**: A personal InMail
    - **Has email?**: checked as soon as the step before it finishes
      - If **Yes**:
        - wait 5 days, then **Email 1**: Same offer, new channel
        - wait 3.5 days, then **Email 2**: Short and personal
        - End.
      - If **No**:
        - End: No email, so it stops.

**Before you build:** Zevari posts the same comment_text on every lead's most recent post, so it can't be specific to each lead. Write one short comment that fits any post, or leave the comment step out and comment by hand.

**Zevari program** (the `sequence` for `campaigns_v2_create`)

```json
[
  {"action_type":"view_profile","delay_hours":0,"config":{"routing":{"version":1,"id":"view","next":"like"}}},
  {"action_type":"like_post","delay_hours":24,"config":{"reaction":"like","routing":{"version":1,"id":"like","next":"comment"}}},
  {"action_type":"comment_on_post","delay_hours":24,"config":{"comment_text":"<write: a short comment that fits any post; the same text goes on every lead's latest post>","routing":{"version":1,"id":"comment","next":"invite"}}},
  {"action_type":"connect","delay_hours":24,"config":{"message":"<write: A personal note, max 200 characters>","routing":{"version":1,"id":"invite","next":{"id":"accepted","kind":"connection_accepted","invite":"invite","wait_hours":120,"yes":"dm1","no":"inmail"}}}},
  {"action_type":"message","delay_hours":24,"config":{"body":"<write: Icebreaker question>","routing":{"version":1,"id":"dm1","next":"dm2"}}},
  {"action_type":"message","delay_hours":72,"config":{"body":"<write: Their objection, answered>","routing":{"version":1,"id":"dm2","next":"dm3"}}},
  {"action_type":"message","delay_hours":72,"config":{"body":"<write: A low-friction offer>","routing":{"version":1,"id":"dm3","next":null}}},
  {"action_type":"inmail","delay_hours":0,"config":{"subject":"<write: subject>","body":"<write: A personal InMail>","routing":{"version":1,"id":"inmail","next":{"id":"has_email","kind":"usable_email","yes":"email1","no":null}}}},
  {"action_type":"email_send","delay_hours":120,"config":{"subject":"<write: subject, under 8 words>","body":"<write: Same offer, new channel>","routing":{"version":1,"id":"email1","next":"email2"}}},
  {"action_type":"email_send","delay_hours":84,"config":{"subject":"<write: subject, under 8 words>","body":"<write: Short and personal>","routing":{"version":1,"id":"email2","next":null}}}
]
```

### 13. 5/5 quiet: InMail + email

- **Group:** Advanced
- **Best for:** ICP score 5 (Strong fit) leads who haven't been active on LinkedIn in 30 days.
- **Why it works:** Your best fits still get every channel, led by the ones they'll actually see: InMail lands in their inbox without a connection, email carries the follow-ups, and the invite is a bonus.

**Steps**

- **Lead enters**: ICP score 5 (Strong fit), quiet on LinkedIn
- **View profile**: They see you looked
- wait 1 day, then **InMail**: A personal InMail
- wait 2 days, then **Email 1**: Same idea, by email
- wait 3 days, then **Email 2**: Their objection, answered
- wait 1 day, then **Connection request**: With a note
- wait 4 days, then **Email 3**: A personal last note
- End.

**Zevari program** (the `sequence` for `campaigns_v2_create`)

```json
[
  {"action_type":"view_profile","delay_hours":0,"config":{}},
  {"action_type":"inmail","delay_hours":24,"config":{"subject":"<write: subject>","body":"<write: A personal InMail>"}},
  {"action_type":"email_send","delay_hours":48,"config":{"subject":"<write: subject, under 8 words>","body":"<write: Same idea, by email>"}},
  {"action_type":"email_send","delay_hours":72,"config":{"subject":"<write: subject, under 8 words>","body":"<write: Their objection, answered>"}},
  {"action_type":"connect","delay_hours":24,"config":{"message":"<write: With a note, max 200 characters>"}},
  {"action_type":"email_send","delay_hours":96,"config":{"subject":"<write: subject, under 8 words>","body":"<write: A personal last note>"}}
]
```

### 14. Engage first, high-trust buyers

- **Group:** Advanced
- **Best for:** Enterprise, security and financial-services buyers.
- **Why it works:** These buyers ignore cold InMail and email. Show up in their comments first, then ask to swap notes, not for a sales call.

**Steps**

- **Lead enters**: Enterprise and security buyers
- **View profile**: They see you looked
- wait 1 day, then **React to a relevant post**
- wait 3 days, then **Comment on post 1**: Add a real point of view
- wait 3 days, then **Comment on post 2**: Keep the thread going
- wait 2 days, then **Connection request**: A personal note
- **Accepted within 7 days?**: Waits for them to accept
  - If **Yes**:
    - wait 1 day, then **Message 1**: Offer a knowledge exchange
    - wait 4 days, then **Message 2**: Share something useful
    - End.
  - If **No** (decided after 7 days):
    - End: not accepted in time.

**Before you build:** Zevari posts the same comment_text on every lead's most recent post, so it can't be specific to each lead. Write one short comment that fits any post, or leave the comment step out and comment by hand. Both comment steps use their most recent post. Unless they post again in between, the second comment lands on the same post, so drop it or swap it for a like.

**Zevari program** (the `sequence` for `campaigns_v2_create`)

```json
[
  {"action_type":"view_profile","delay_hours":0,"config":{"routing":{"version":1,"id":"view","next":"like"}}},
  {"action_type":"like_post","delay_hours":24,"config":{"reaction":"like","routing":{"version":1,"id":"like","next":"comment1"}}},
  {"action_type":"comment_on_post","delay_hours":72,"config":{"comment_text":"<write: a short comment that fits any post; the same text goes on every lead's latest post>","routing":{"version":1,"id":"comment1","next":"comment2"}}},
  {"action_type":"comment_on_post","delay_hours":72,"config":{"comment_text":"<write: a short comment that fits any post; the same text goes on every lead's latest post>","routing":{"version":1,"id":"comment2","next":"invite"}}},
  {"action_type":"connect","delay_hours":48,"config":{"message":"<write: A personal note, max 200 characters>","routing":{"version":1,"id":"invite","next":{"id":"accepted","kind":"connection_accepted","invite":"invite","wait_hours":168,"yes":"dm1","no":null}}}},
  {"action_type":"message","delay_hours":24,"config":{"body":"<write: Offer a knowledge exchange>","routing":{"version":1,"id":"dm1","next":"dm2"}}},
  {"action_type":"message","delay_hours":96,"config":{"body":"<write: Share something useful>","routing":{"version":1,"id":"dm2","next":null}}}
]
```

### 15. The full stack: every channel

- **Group:** The full stack
- **Best for:** High-value deals where every lead is worth a 9-touch effort.
- **Why it works:** Every channel Zevari has, in order of warmth: profile view, like, comment, invite, messages, then email. If they don't accept, InMail and three emails take over. A reply at any point stops it.

**Steps**

- **Lead enters**: Your best-fit leads
- **View profile**: Day 0: they see you looked
- wait 1 day, then **Like a recent post**
- wait 1 day, then **Comment on a post**: Specific, not generic
- wait 1 day, then **Connection request**: A/B test the note
- **Accepted within 7 days?**: Waits for them to accept
  - If **Yes**:
    - wait 1 day, then **Message 1**: Icebreaker question
    - wait 3 days, then **Message 2**: Their objection, answered
    - wait 3 days, then **Message 3**: A low-friction offer
    - **Has email?**: checked as soon as the step before it finishes
      - If **Yes**:
        - wait 2 days, then **Email 1**: Recap + a useful resource
        - wait 4 days, then **Email 2**: A personal last note
        - End.
      - If **No**:
        - wait 4 days, then **Message 4**: A personal last note
        - End.
  - If **No** (decided after 7 days):
    - **InMail**: No connection needed
    - **Has email?**: checked as soon as the step before it finishes
      - If **Yes**:
        - wait 5 days, then **Email 1**: Same offer, new channel
        - wait 3.5 days, then **Email 2**: A new angle
        - wait 4 days, then **Email 3**: Short and personal
        - End.
      - If **No**:
        - End: No email, so it stops.

**Before you build:** Zevari posts the same comment_text on every lead's most recent post, so it can't be specific to each lead. Write one short comment that fits any post, or leave the comment step out and comment by hand.

**Zevari program** (the `sequence` for `campaigns_v2_create`)

```json
[
  {"action_type":"view_profile","delay_hours":0,"config":{"routing":{"version":1,"id":"view","next":"like"}}},
  {"action_type":"like_post","delay_hours":24,"config":{"reaction":"like","routing":{"version":1,"id":"like","next":"comment"}}},
  {"action_type":"comment_on_post","delay_hours":24,"config":{"comment_text":"<write: a short comment that fits any post; the same text goes on every lead's latest post>","routing":{"version":1,"id":"comment","next":"invite"}}},
  {"action_type":"connect","delay_hours":24,"config":{"message":"<write: A/B test the note, max 200 characters>","routing":{"version":1,"id":"invite","next":{"id":"accepted","kind":"connection_accepted","invite":"invite","wait_hours":168,"yes":"dm1","no":"inmail"}}}},
  {"action_type":"message","delay_hours":24,"config":{"body":"<write: Icebreaker question>","routing":{"version":1,"id":"dm1","next":"dm2"}}},
  {"action_type":"message","delay_hours":72,"config":{"body":"<write: Their objection, answered>","routing":{"version":1,"id":"dm2","next":"dm3"}}},
  {"action_type":"message","delay_hours":72,"config":{"body":"<write: A low-friction offer>","routing":{"version":1,"id":"dm3","next":{"id":"has_email","kind":"usable_email","yes":"email1","no":"dm4"}}}},
  {"action_type":"email_send","delay_hours":48,"config":{"subject":"<write: subject, under 8 words>","body":"<write: Recap + a useful resource>","routing":{"version":1,"id":"email1","next":"email2"}}},
  {"action_type":"email_send","delay_hours":96,"config":{"subject":"<write: subject, under 8 words>","body":"<write: A personal last note>","routing":{"version":1,"id":"email2","next":null}}},
  {"action_type":"message","delay_hours":96,"config":{"body":"<write: A personal last note>","routing":{"version":1,"id":"dm4","next":null}}},
  {"action_type":"inmail","delay_hours":0,"config":{"subject":"<write: subject>","body":"<write: No connection needed>","routing":{"version":1,"id":"inmail","next":{"id":"has_email2","kind":"usable_email","yes":"email3","no":null}}}},
  {"action_type":"email_send","delay_hours":120,"config":{"subject":"<write: subject, under 8 words>","body":"<write: Same offer, new channel>","routing":{"version":1,"id":"email3","next":"email4"}}},
  {"action_type":"email_send","delay_hours":84,"config":{"subject":"<write: subject, under 8 words>","body":"<write: A new angle>","routing":{"version":1,"id":"email4","next":"email5"}}},
  {"action_type":"email_send","delay_hours":96,"config":{"subject":"<write: subject, under 8 words>","body":"<write: Short and personal>","routing":{"version":1,"id":"email5","next":null}}}
]
```

### 16. Kara's icebreaker sequence

- **Group:** Playbooks
- **Best for:** Cold LinkedIn outreach where the goal is a reply, not a call.
- **Why it works:** Kara McMaster's rule: optimize for the reply. Engage a day before a blank invite, wait a day or two after they accept, then four messages with one idea each. The last one is the most human, because it's the inbox preview.

**Steps**

- **Lead enters**: Anyone on your list
- **Like a recent post**: The day before the invite
- wait 1 day, then **Connection request**: Blank, no note
- **Accepted within 14 days?**: Waits for them to accept
  - If **Yes**:
    - wait 2 days, then **Message 1**: An observation + one question
    - wait 3 days, then **Message 2**: Something new, never a bump
    - wait 3 days, then **Message 3**: Proof: a client's result
    - wait 3 days, then **Message 4**: Personal, zero business
    - End.
  - If **No** (decided after 14 days):
    - End: not accepted in time.

**Zevari program** (the `sequence` for `campaigns_v2_create`)

```json
[
  {"action_type":"like_post","delay_hours":0,"config":{"reaction":"like","routing":{"version":1,"id":"like","next":"invite"}}},
  {"action_type":"connect","delay_hours":24,"config":{"routing":{"version":1,"id":"invite","next":{"id":"accepted","kind":"connection_accepted","invite":"invite","wait_hours":336,"yes":"dm1","no":null}}}},
  {"action_type":"message","delay_hours":48,"config":{"body":"Brief: An observation + one question. Draft it for this lead.","generation_mode":"llm","routing":{"version":1,"id":"dm1","next":"dm2"}}},
  {"action_type":"message","delay_hours":72,"config":{"body":"<write: Something new, never a bump>","routing":{"version":1,"id":"dm2","next":"dm3"}}},
  {"action_type":"message","delay_hours":72,"config":{"body":"<write: Proof: a client's result>","routing":{"version":1,"id":"dm3","next":"dm4"}}},
  {"action_type":"message","delay_hours":72,"config":{"body":"<write: Personal, zero business>","routing":{"version":1,"id":"dm4","next":null}}}
]
```

### 17. Permission to send (Kellen Casebeer)

- **Group:** Playbooks
- **Best for:** Cold email where a meeting ask is too heavy.
- **Why it works:** Name their situation in line one, then ask permission to send something specific, like a checklist or the angle you'd test. A yes is a reply, and the follow-ups bring a new jolt each time instead of a bump.

**Steps**

- **Lead enters**: Has a work email
- **Email 1**: Name it, then “Can I send it?”
- wait 3 days, then **Email 2**: A one-line agitational bump
- wait 4 days, then **Email 3**: Why you reached out, last note
- End.

**Zevari program** (the `sequence` for `campaigns_v2_create`)

```json
[
  {"action_type":"email_send","delay_hours":0,"config":{"subject":"<write: subject, under 8 words>","body":"<write: Name it, then “Can I send it?”>"}},
  {"action_type":"email_send","delay_hours":72,"config":{"subject":"<write: subject, under 8 words>","body":"<write: A one-line agitational bump>"}},
  {"action_type":"email_send","delay_hours":96,"config":{"subject":"<write: subject, under 8 words>","body":"<write: Why you reached out, last note>"}}
]
```

### 18. Value-bump ladder (after Josh Braun)

- **Group:** Playbooks
- **Best for:** Cold email to mid-market buyers.
- **Why it works:** Every bump gives something, and each one is shorter than the last. Never more than one content-free nudge. The last two ask about timing instead of pushing.

**Steps**

- **Lead enters**: Has a work email
- **Email 1**: Trigger, question, proof, ask
- wait 4 days, then **Email 2**: A resource, no reply needed
- wait 6 days, then **Email 3**: A new trigger + interest check
- wait 11 days, then **Email 4**: Timing not right? Am I off?
- wait 9 days, then **Email 5**: Given up on the project?
- End.

**Zevari program** (the `sequence` for `campaigns_v2_create`)

```json
[
  {"action_type":"email_send","delay_hours":0,"config":{"subject":"<write: subject, under 8 words>","body":"<write: Trigger, question, proof, ask>"}},
  {"action_type":"email_send","delay_hours":96,"config":{"subject":"<write: subject, under 8 words>","body":"<write: A resource, no reply needed>"}},
  {"action_type":"email_send","delay_hours":144,"config":{"subject":"<write: subject, under 8 words>","body":"<write: A new trigger + interest check>"}},
  {"action_type":"email_send","delay_hours":264,"config":{"subject":"<write: subject, under 8 words>","body":"<write: Timing not right? Am I off?>"}},
  {"action_type":"email_send","delay_hours":216,"config":{"subject":"<write: subject, under 8 words>","body":"<write: Given up on the project?>"}}
]
```

### 19. Status-quo ladder (after Jen Allen-Knuth)

- **Group:** Playbooks
- **Best for:** Buyers who aren't looking yet.
- **Why it works:** Each email under 40 words, each moving them one step off the status quo: the problem, what peers are hitting, the cost of doing nothing, then what would have to be true. Then a clean release.

**Steps**

- **Lead enters**: Has a work email
- **Email 1**: The problem, under 50 words
- wait 3.5 days, then **Email 2**: What peer teams are hitting
- wait 5 days, then **Email 3**: The cost of doing nothing
- wait 8 days, then **Email 4**: What would have to be true?
- wait 7 days, then **Email 5**: A clean release
- End.

**Zevari program** (the `sequence` for `campaigns_v2_create`)

```json
[
  {"action_type":"email_send","delay_hours":0,"config":{"subject":"<write: subject, under 8 words>","body":"<write: The problem, under 50 words>"}},
  {"action_type":"email_send","delay_hours":84,"config":{"subject":"<write: subject, under 8 words>","body":"<write: What peer teams are hitting>"}},
  {"action_type":"email_send","delay_hours":120,"config":{"subject":"<write: subject, under 8 words>","body":"<write: The cost of doing nothing>"}},
  {"action_type":"email_send","delay_hours":192,"config":{"subject":"<write: subject, under 8 words>","body":"<write: What would have to be true?>"}},
  {"action_type":"email_send","delay_hours":168,"config":{"subject":"<write: subject, under 8 words>","body":"<write: A clean release>"}}
]
```

### 20. One-line nudge, then switch channel (after Morgan J Ingram)

- **Group:** Playbooks
- **Best for:** LinkedIn-first outreach that stalls after the first message.
- **Why it works:** A blank invite, one reason for reaching out, then “any feedback on my message?”. The second follow-up changes the channel, not the wording.

**Steps**

- **Lead enters**: Anyone on your list
- **Connection request**: Blank, no note
- **Accepted within 7 days?**: Waits for them to accept
  - If **Yes**:
    - wait 1 day, then **Message 1**: Why you reached out
    - wait 3 days, then **Message 2**: Any feedback on my message?
    - **Has email?**: checked as soon as the step before it finishes
      - If **Yes**:
        - wait 3 days, then **Email**: Same reason, new channel
        - End.
      - If **No**:
        - wait 3 days, then **Message 3**: One exit question
        - End.
  - If **No** (decided after 7 days):
    - End: not accepted in time.

**Zevari program** (the `sequence` for `campaigns_v2_create`)

```json
[
  {"action_type":"connect","delay_hours":0,"config":{"routing":{"version":1,"id":"invite","next":{"id":"accepted","kind":"connection_accepted","invite":"invite","wait_hours":168,"yes":"dm1","no":null}}}},
  {"action_type":"message","delay_hours":24,"config":{"body":"<write: Why you reached out>","routing":{"version":1,"id":"dm1","next":"dm2"}}},
  {"action_type":"message","delay_hours":72,"config":{"body":"<write: Any feedback on my message?>","routing":{"version":1,"id":"dm2","next":{"id":"has_email","kind":"usable_email","yes":"email","no":"dm3"}}}},
  {"action_type":"email_send","delay_hours":72,"config":{"subject":"<write: subject, under 8 words>","body":"<write: Same reason, new channel>","routing":{"version":1,"id":"email","next":null}}},
  {"action_type":"message","delay_hours":72,"config":{"body":"<write: One exit question>","routing":{"version":1,"id":"dm3","next":null}}}
]
```

### 21. Warm network: fit or intro

- **Group:** Playbooks
- **Best for:** Your existing connections, when you're testing a new offer.
- **Why it works:** No pitch: is this something your team is dealing with, or do you know someone who is? Either answer helps, so people reply.

**Steps**

- **Lead enters**: Already connected with you
- **Message 1**: Facing this, or know who is?
- wait 4 days, then **Message 2**: One useful thing, no ask
- End.

**Zevari program** (the `sequence` for `campaigns_v2_create`)

```json
[
  {"action_type":"message","delay_hours":0,"config":{"body":"<write: Facing this, or know who is?>"}},
  {"action_type":"message","delay_hours":96,"config":{"body":"<write: One useful thing, no ask>"}}
]
```

## Automation sequences

Automations run in the Automations area of the Zevari app, which is in early access. Each one starts from a trigger, filters the lead, then takes actions or enrolls the lead in a campaign. Build them in the app; there is no MCP tool for them yet. If your workspace doesn't have Automations, run the campaign part on its own.

### 22. Screening question, then “why not?”

- **Group:** Playbooks
- **Best for:** Service businesses: “Are you running X for {company}?”
- **Why it works:** Even a no opens the conversation. Every reply lands as a draft for you, and the ones who don't answer get one new idea, then a personal last note.

**Steps**

- **Added by you or your AI**: Connected leads
- **Message 1**: Are you running X for them?
- **Replied within 4 days?**: Waits for a reply
  - If **Yes**:
    - **Draft a reply for me**: A no gets “why not?”
    - End.
  - If **No** (decided after 4 days):
    - **Message 2**: Something new, never a bump
    - **Replied within 4 days?**: Waits for a reply
      - If **Yes**:
        - Continue at **Draft a reply for me** (above).
      - If **No** (decided after 4 days):
        - **Message 3**: Personal, zero business
        - End.

### 23. Interested, then ghosted

- **Group:** Playbooks
- **Best for:** Leads who said they were interested and went quiet after you asked for a call.
- **Why it works:** Up to three follow-ups, each on a different channel, each offering two specific times instead of a calendar link. The last one future-paces: is this a later problem?

**Steps**

- **Added to list**: Your “Asked for a call” list
- **Replied within 3 days?**: Waits for a reply
  - If **Yes**:
    - End: Back in the conversation.
  - If **No** (decided after 3 days):
    - **Message**: Two specific times
    - **Replied within 4 days?**: Waits for a reply
      - If **Yes**:
        - End: Back in the conversation.
      - If **No** (decided after 4 days):
        - **Email**: Same two times, by email
        - wait 4 days, then **Message**: Is this a later problem?
        - End.

### 24. A/B test three angles

- **Group:** Playbooks
- **Best for:** Finding the message that works before you scale a list.
- **Why it works:** One source split three ways, one variable per campaign so the results compare. Run about 150 leads a week, keep the best angle and rerun.

**Steps**

- **New leads from a source**: Your Sales Navigator search
- **Qualify**: ICP score 4 or higher (Strong fit)
  - If **Qualified**:
    - **A/B split**: A third down each path
      - If **Angle A**:
        - **Enroll in campaign**: Status quo pain
        - End.
      - If **Angle B**:
        - **Enroll in campaign**: Hidden cost
        - End.
      - If **Angle C**:
        - **Enroll in campaign**: Compare to their path
        - End.
  - If **Not qualified**:
    - End: Left early.

### 25. Signal strength: comment before you DM

- **Group:** Playbooks
- **Best for:** Signal-led outreach on keyword posts.
- **Why it works:** The strongest fits get a message about their post, or an invite if you're not connected. Weaker fits get a helpful comment first, because a cold DM to a stranger is the fastest way to be ignored.

**Steps**

- **New leads from a source**: Posted about a buying signal
- **Qualify**: ICP score 3 or higher (Moderate or Strong fit)
  - If **Qualified**:
    - **Segment by ICP score**: First group that's true
      - If **ICP score 4–5 (Strong fit)**:
        - **Already connected?**: On LinkedIn
          - If **Yes**:
            - **Message**: About their post
            - End.
          - If **No**:
            - **Connection request**: A note about their post
            - End.
      - If **ICP score 3 (Moderate fit)**:
        - **Comment on their post**: Genuinely helpful
        - wait 1 day, then **Connection request**: Blank, no note
        - **Accepted within 7 days?**: Waits for them to accept
          - If **Yes**:
            - wait 1 day, then **Message**: Pick up the thread
            - End.
          - If **No** (decided after 7 days):
            - End: not accepted in time.
  - If **Not qualified**:
    - End: Left early.

### 26. Switching window: they're asking for a tool

- **Group:** Playbooks
- **Best for:** Posts asking for recommendations or venting about a competitor.
- **Why it works:** The hottest signal there is. You get told right away, and the first touch is a genuinely useful answer in their comments, not a pitch in their inbox.

**Steps**

- **New leads from a source**: “Any alternatives to X?”
- **Qualify**: ICP score 3 or higher (Moderate or Strong fit)
  - If **Qualified**:
    - **Notify me**: Hot: switching tools
    - **Comment on their post**: A useful answer, no pitch
    - wait 1 day, then **Connection request**: A note about the thread
    - **Accepted within 5 days?**: Waits for them to accept
      - If **Yes**:
        - wait 1 day, then **Message**: Offer to compare options
        - End.
      - If **No** (decided after 5 days):
        - End: not accepted in time.
  - If **Not qualified**:
    - End: Left early.

### 27. Deliver the guide, then check they used it

- **Group:** Playbooks
- **Best for:** People who comment your keyword on a lead-magnet post.
- **Why it works:** Deliver the asset before asking for anything. A few days later ask if they used it and what they're working on, and hand every reply to you.

**Steps**

- **Comments on my post**: Your lead-magnet post
- **Already connected?**: On LinkedIn
  - If **Yes**:
    - **Message: the guide**: Here it is, with the link
    - wait 3 days, then **Message: check in**: Did you use it? What's next?
    - **Replied within 4 days?**: Waits for a reply
      - If **Yes**:
        - **Notify me**: A warm conversation
        - **Draft a reply for me**: Lands in your inbox
        - End.
      - If **No** (decided after 4 days):
        - End.
  - If **No**:
    - **Connection request**: “Sending the guide”
    - **Accepted within 7 days?**: Waits for them to accept
      - If **Yes**:
        - Continue at **Message: the guide** (above).
      - If **No** (decided after 7 days):
        - End: not accepted in time.

### 28. Re-open parked leads on a new signal

- **Group:** Playbooks
- **Best for:** Leads who finished a sequence without replying.
- **Why it works:** Don't revive everyone on a timer. Park the silent ones, and when one of them posts a new buying signal, come back with a message about that post.

**Steps**

- **New leads from a source**: Posted about a buying signal
- **On your Parked list?**: Finished a sequence, no reply
  - If **Yes**:
    - **Remove from list**: Parked
    - **Enroll in campaign**: Message about their post
    - End.
  - If **No**:
    - End: Not parked.

### 29. Post commenters → intro message

- **Group:** Automations
- **Best for:** Turning people who comment on your posts into conversations.
- **Why it works:** They already raised their hand. Qualify them, then message the connected ones and invite the rest, with email as the last fallback.

**Steps**

- **Comments on my post**: Someone comments on a post
- **Qualify**: ICP score 3 or higher (Moderate or Strong fit)
  - If **Qualified**:
    - **Already connected?**: On LinkedIn
      - If **Yes**:
        - **Message: intro**: A personal introduction
        - **Replied within 3 days?**: Waits for a reply
          - If **Yes**:
            - **Draft a reply for me**: Lands in your inbox
            - End.
          - If **No** (decided after 3 days):
            - **Follow-up**: A friendly reminder
            - End.
      - If **No**:
        - **Connection request**: A personal invite
        - **Accepted within 7 days?**: Waits for them to accept
          - If **Yes**:
            - Continue at **Message: intro** (above).
          - If **No** (decided after 7 days):
            - **Find email**: Uses credits to look one up
              - If **Found**:
                - **Email: intro**: The intro, by email
                - End.
              - If **Not found**:
                - End.
  - If **Not qualified**:
    - End: Left early.

### 30. Lead router: right campaign for every score

- **Group:** Automations
- **Best for:** A Sales Navigator search that feeds you new leads every week.
- **Why it works:** One search, scored once, then each lead goes to the campaign that fits it: score-5 (Strong fit) leads get the MVP treatment and a call, score-4 (Strong fit) leads the LinkedIn core, score-3 (Moderate fit) leads email only.

**Steps**

- **New leads from a source**: Your Sales Navigator search
- **Qualify**: Your Qualified line: 3+
  - If **Qualified**:
    - **Segment by ICP score**: First group that's true
      - If **ICP score 5 (Strong fit)**:
        - **Notify me**: Add them to my call list
        - **Enroll in campaign**: 5/5 MVP
        - End.
      - If **ICP score 4 (Strong fit)**:
        - **Enroll in campaign**: LinkedIn-active core
        - End.
      - If **Else: ICP score 3 (Moderate fit)**:
        - **Find email**: Uses credits to look one up
          - If **Found**:
            - **Enroll in campaign**: Three cold emails
            - End.
          - If **Not found**:
            - End.
  - If **Not qualified**:
    - End: Left early.

### 31. Buying signal → message about their post

- **Group:** Automations
- **Best for:** Keyword-post and hiring signals.
- **Why it works:** The message quotes what they just posted, so it reads as a reply, not a pitch. Connected leads get a DM, the rest get email, and an invite if there's no email.

**Steps**

- **New leads from a source**: Posted about a buying signal
- **Qualify**: ICP score 3 or higher (Moderate or Strong fit)
  - If **Qualified**:
    - **Route by channel**: Connected, email or neither
      - If **Connected**:
        - **Message**: Quotes their post
        - End.
      - If **Has email**:
        - **Email**: Quotes their post
        - End.
      - If **Neither**:
        - **Find email**: Uses credits to look one up
          - If **Found**:
            - Continue at **Email** (above).
          - If **Not found**:
            - **Connection request**: A note about their post
            - End.
  - If **Not qualified**:
    - End: Left early.

### 32. Revive after 45 days of silence

- **Group:** Automations
- **Best for:** Strong fits who got every step and never replied.
- **Why it works:** Silence isn't a no. Wait 45 days, then come back with a new reason to talk, without adding anyone again by hand.

**Steps**

- **Added to list**: Your strong-fit list
- **Enroll in campaign**: Connect and four follow-ups
  - If **Replied**:
    - **Draft a reply for me**: Lands in your inbox
    - End.
  - If **Finished, no reply**:
    - **Wait 45 days**
    - **Enroll in campaign**: A new reason to talk
    - End.
  - If **Didn't accept**:
    - **Find email**: Uses credits to look one up
      - If **Found**:
        - **Enroll in campaign**: Three cold emails
        - End.
      - If **Not found**:
        - End.
