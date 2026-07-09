# Conversational Commerce — Chat, SMS & Messaging

> Conversational commerce is the intersection of messaging and buying. Customers increasingly expect to discover, evaluate, and purchase products within chat interfaces. This guide covers every major messaging channel, compliance requirements, and measurement frameworks.

---

## Channel Landscape

| Channel | Monthly Active Users | Commerce Maturity | Best For |
|---------|---------------------|-------------------|----------|
| **WhatsApp Business** | 2B+ | High (especially outside US) | International commerce, support, notifications |
| **SMS / MMS** | Universal | High | Promotions, alerts, re-engagement, transactional |
| **Facebook Messenger** | 1B+ | Medium-High | Lead gen, customer support, automated flows |
| **Instagram DMs** | 2B+ (Instagram total) | Medium | Product inquiries, influencer commerce |
| **RCS (Rich Communication Services)** | Growing (Android default) | Emerging | Rich media messaging, branded sender |
| **Live Chat (Website)** | N/A | High | Real-time support, sales conversion |
| **Chatbots (AI)** | N/A | Medium-High | Automated support, qualification, FAQ |
| **Apple Business Messages** | iOS users | Medium | Premium support, appointment booking |

---

## WhatsApp Business — Setup & Marketing

### Account Tiers

| Tier | WhatsApp Business App | WhatsApp Business Platform (API) |
|------|----------------------|--------------------------------|
| Best for | Small businesses (<5 agents) | Mid-market and enterprise |
| Cost | Free | Per-message pricing since 1 July 2025 (varies by country and template type — India marketing template ≈ USD 0.0118; service messages in the 24-hr customer-care window and 72-hr free window from CTWA/Page CTAs are free) |
| Automation | Basic quick replies, labels | Full chatbot, CRM integration, workflows |
| Broadcasting | Broadcast lists (256 contacts) | Unlimited template messages (pre-approved) |
| Commerce | Product catalog in-app | Full catalog + cart + payment integration |
| Verification | Green checkmark available | Green checkmark available |

### WhatsApp Message Types

| Type | Use Case | Requires Opt-In? | Template Approval? |
|------|---------|-------------------|-------------------|
| **Utility** | Order confirmations, shipping updates, receipts | Yes | Yes |
| **Authentication** | OTP, login verification | Yes | Yes |
| **Marketing** | Promotions, product launches, re-engagement | Yes (explicit) | Yes |
| **Service** | Customer-initiated support conversations | No (customer initiated) | No (free-form within 24hr window) |

### WhatsApp Marketing Best Practices
1. Obtain explicit opt-in before sending any marketing messages
2. Segment audiences — do not blast entire contact list
3. Personalize messages with customer name and relevant product data
4. Include clear CTA (shop now, book appointment, reply to order)
5. Respect frequency: 2-4 marketing messages per month maximum
6. Always provide easy opt-out mechanism
7. Use rich media: images, videos, product carousels, interactive buttons

---

## Chatbot Design Framework

### Conversation Architecture

```
Entry Point → Greeting → Intent Detection → Flow Routing
                                               │
                    ┌──────────┬────────────────┼────────────────┐
                    ▼          ▼                ▼                ▼
               Product     Support         Appointment       Lead
               Browse      Issue           Booking           Qualification
                    │          │                │                │
                    ▼          ▼                ▼                ▼
               Add to      Resolve /       Confirm /        Capture /
               Cart        Escalate        Remind           Route to Sales
                    │          │                │                │
                    └──────────┴────────────────┴────────────────┘
                                               │
                                          Close / Survey
```

### Chatbot Design Principles

| Principle | Implementation |
|-----------|---------------|
| **Identify the bot** | Always disclose that the user is chatting with a bot, not a human |
| **Limit scope** | Define 5-10 core intents the bot handles well; escalate everything else |
| **Provide human escalation** | "Talk to a human" option available at every step |
| **Use quick replies** | Offer button options to guide the conversation (reduce free-text friction) |
| **Handle dead ends** | Every unrecognized input gets a graceful fallback ("I didn't quite get that. Here are some things I can help with:") |
| **Personalize** | Use customer name, order history, browsing context when available |
| **Keep it short** | Messages under 60 words; break long responses into multiple messages |
| **Confirm actions** | Always confirm before processing orders, bookings, or account changes |

### Chatbot Platform Comparison

| Platform | Best For | AI Capability | Channels Supported | Pricing |
|----------|---------|---------------|-------------------|---------|
| **ManyChat** | SMBs, e-commerce | Rule-based + AI | Messenger, Instagram, WhatsApp, SMS | Free tier + $15+/mo |
| **Intercom** | SaaS, support | AI (Fin) + rules | Web chat, email, Messenger, WhatsApp | $74+/mo |
| **Drift** | B2B lead gen | AI + playbooks | Web chat, email | Custom pricing |
| **Zendesk Chat** | Support teams | AI + agent routing | Web chat, Messenger, WhatsApp | $49+/agent/mo |
| **Tidio** | Small e-commerce | AI + templates | Web chat, Messenger, email | Free tier + $29+/mo |
| **Custom (GPT/Claude API)** | Enterprise, custom needs | Full LLM capability | Any (via integration) | API usage costs |

---

## SMS Compliance Guide

### TCPA (Telephone Consumer Protection Act) — United States

| Requirement | Details |
|------------|---------|
| **Express written consent** | Required before sending any marketing SMS |
| **Consent must be clear** | Cannot be buried in terms; must be conspicuous |
| **Opt-out** | Must honor STOP/UNSUBSCRIBE immediately |
| **Identification** | Every message must identify the sender |
| **Quiet hours** | Do not send before 8AM or after 9PM (recipient's time zone) |
| **Record keeping** | Maintain consent records for at least 4 years |
| **Penalties** | $500-$1,500 per unsolicited message (class action risk) |

### 10DLC (10-Digit Long Code) Registration

Since 2023, all businesses sending SMS via standard phone numbers must register with The Campaign Registry (TCR).

| Step | Action | Details |
|------|--------|---------|
| 1 | Register your brand | Company name, EIN, website, vertical |
| 2 | Register your campaign | Use case, sample messages, opt-in flow description |
| 3 | Receive trust score | Score determines throughput limits (messages per second) |
| 4 | Carrier approval | AT&T, T-Mobile, Verizon review and approve |
| 5 | Begin sending | Stay within approved use case and throughput |

### Opt-In Best Practices

| Method | Example | Compliance Level |
|--------|---------|-----------------|
| Web form with checkbox | "[ ] I agree to receive text messages from {{brand}}. Msg & data rates may apply. Reply STOP to unsubscribe." | Strong |
| Keyword opt-in | "Text JOIN to 55555" (with terms displayed) | Strong |
| Point-of-sale | Paper or tablet consent form at checkout | Strong (if documented) |
| Pre-checked box | Any pre-checked consent box | **Non-compliant** (do not use) |
| Implied consent | Purchasing = consent to marketing | **Non-compliant** (do not use) |

### Required SMS Disclosures (First Message)

```
Welcome to {{brand}} alerts! You'll receive up to {{frequency}} msgs/mo.
Msg & data rates may apply. Reply HELP for help, STOP to cancel.
Terms: {{URL}} Privacy: {{URL}}
```

---

## Conversation Flow Templates

### E-Commerce — Product Recommendation Flow

```
Bot: Hey {{name}}! 👋 Looking for something specific today?
     [Browse New Arrivals] [Get a Recommendation] [Check Order Status]

User: [Get a Recommendation]

Bot: Great! What are you shopping for?
     [Clothing] [Accessories] [Home] [Gifts]

User: [Clothing]

Bot: What's the occasion?
     [Casual / Everyday] [Work / Professional] [Special Event]

User: [Casual / Everyday]

Bot: Here are 3 picks I think you'll love:
     [Product Card 1 — image, name, price, "View" button]
     [Product Card 2 — image, name, price, "View" button]
     [Product Card 3 — image, name, price, "View" button]

     [Show More] [Talk to a Stylist]
```

### B2B — Lead Qualification Flow

```
Bot: Hi there! I'm {{bot_name}} from {{company}}.
     How can I help you today?
     [Learn about pricing] [Book a demo] [Talk to sales] [Support]

User: [Learn about pricing]

Bot: Happy to help! A couple of quick questions so I can point you
     to the right plan. How many team members would use {{product}}?
     [1-10] [11-50] [51-200] [200+]

User: [11-50]

Bot: And what's your primary use case?
     [{{Use case A}}] [{{Use case B}}] [{{Use case C}}]

User: [{{Use case B}}]

Bot: Based on your team size and needs, our {{Plan Name}} at
     ${{price}}/mo would be the best fit. Here's what's included:
     {{key features}}

     [Start Free Trial] [Book a Demo] [Talk to Sales]
```

---

## Live Chat Best Practices

| Best Practice | Details |
|--------------|---------|
| Response time | First response within 30 seconds; aim for <15 seconds |
| Availability | Display chat only during staffed hours; use bot for off-hours |
| Proactive triggers | Fire chat invite after 30+ seconds on pricing page, cart page, or high-intent pages |
| Canned responses | Pre-write responses for top 20 FAQs; personalize before sending |
| Routing | Route by page (pricing → sales, support → CS, product → specialist) |
| Context | Pass page URL, customer history, and cart contents to agent |
| Multitasking | Agents handle max 3 simultaneous chats for quality |
| Handoff | Seamless bot-to-human handoff with full conversation history |
| Post-chat | Send transcript via email; trigger CSAT survey |
| Mobile optimization | Chat widget must work on mobile without obscuring content |

---

## Facebook Messenger Marketing

### Messenger Entry Points

| Entry Point | Setup | Best For |
|-------------|-------|----------|
| "Send Message" button on Page | Automatic | General inquiries |
| Click-to-Messenger ads | Facebook Ads Manager | Lead gen, promotions |
| m.me links | m.me/YourPageName | Email, website, QR codes |
| Messenger Ref URL | m.me/YourPageName?ref=campaign | Campaign-specific flows |
| Customer Chat Plugin | Website embed | Website → Messenger handoff |
| Checkbox Plugin | On web forms | Opt-in during checkout/registration |

### Messenger Policy Essentials
- **24-hour rule:** Free-form messages only within 24 hours of user's last message
- **Outside 24 hours:** Must use approved message tags (confirmed event, post-purchase update, account update) or sponsored messages (paid)
- **No promotional content** in message tags — this will get your page restricted
- **Subscription messaging** requires approval for news bots only

---

## RCS (Rich Communication Services) Overview

| Attribute | SMS | RCS |
|-----------|-----|-----|
| Media support | MMS (limited) | High-res images, video, audio, files |
| Branding | No sender branding | Verified sender name, logo, color |
| Interactivity | None | Buttons, carousels, quick replies |
| Read receipts | No | Yes |
| Typing indicators | No | Yes |
| Fallback | N/A | Falls back to SMS if RCS unavailable |
| Availability | Universal | Android (default in Google Messages); Apple adopted in iOS 18 |
| Cost | Per-message | Per-message (similar to SMS) |

### RCS Marketing Checklist
- [ ] Register as verified RCS sender through Google or aggregator
- [ ] Design branded sender profile (logo, colors, description)
- [ ] Create rich media message templates (carousels, buttons)
- [ ] Set up SMS fallback for non-RCS devices
- [ ] Test across multiple Android devices and carriers
- [ ] Track RCS-specific metrics (read rates, button clicks)

---

## Measurement Framework

| Metric | Definition | Benchmark |
|--------|-----------|-----------|
| **Response Rate** | % of messages that receive a reply | SMS: 45%+, Chat: 70%+ |
| **First Response Time** | Time to first agent/bot response | <30 seconds (live chat), instant (bot) |
| **Resolution Rate** | % of conversations resolved without escalation | Bot: 60-80%, Live chat: 85%+ |
| **CSAT (Customer Satisfaction)** | Post-conversation survey score | 4.2+ / 5.0 |
| **Conversion Rate** | % of conversations resulting in purchase/lead | 5-15% (varies by channel) |
| **Revenue per Conversation** | Total revenue / total conversations | Track and improve over time |
| **Opt-Out Rate** | % of subscribers who unsubscribe | SMS: <2% per campaign |
| **Cost per Conversation** | Total channel cost / conversations | Lower than phone support |
| **Bot Containment Rate** | % handled by bot without human | Target: 60-70% |
| **Click-Through Rate** | % who click links/buttons in messages | SMS: 15-30%, RCS: 25-40% |

---

## Channel Selection Matrix

| If your goal is... | Best Channel(s) |
|--------------------|----------------|
| Promotional campaigns (US market) | SMS + RCS |
| International commerce | WhatsApp Business |
| Real-time sales support | Live chat on website |
| Automated lead qualification | Chatbot (Messenger, website, WhatsApp) |
| Post-purchase engagement | SMS + WhatsApp + Email |
| High-touch B2B sales | Live chat + Drift/Intercom |
| Gen Z / millennial engagement | Instagram DMs + SMS |
| Rich media promotions | RCS (Android) + Messenger |

---

> **Conversational commerce collapses the funnel.** Discovery, consideration, and purchase happen in a single thread. The brands that master messaging will outperform those still forcing customers through traditional funnels.
