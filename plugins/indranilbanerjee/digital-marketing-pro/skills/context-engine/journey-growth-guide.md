# Journey & Growth Intelligence Guide

Reference knowledge for customer journey orchestration, growth loop modeling, dark funnel analysis, and journey simulation. Use this to design multi-stage customer journeys grounded in state machine methodology rather than linear funnel assumptions.

---

## 1. Journey State Machine Methodology

### Why State Machines Over Funnels
Traditional funnels assume linear progression: awareness to consideration to purchase. Real customer behavior is non-linear. People skip stages, regress, stall, re-enter, and follow paths the funnel model cannot represent. A state machine models the journey as a set of defined states with probabilistic transitions between them, capturing the actual complexity of buyer behavior.

### Core Journey States

| State | Definition | Entry Signals | Exit Signals |
|---|---|---|---|
| **Awareness** | Knows the problem exists, may know solutions exist | First website visit, ad impression, social discovery, content consumption | Returns to site, engages with content, follows social |
| **Consideration** | Actively researching solutions, comparing options | Multiple site visits, content downloads, comparison page views, newsletter signup | Visits pricing page, starts free trial, requests demo |
| **Evaluation** | Narrowing to a shortlist, testing or comparing finalists | Pricing page visit, demo request, free trial start, sales conversation | Verbal or written intent to purchase, trial conversion |
| **Decision** | Ready to buy, finalizing terms and logistics | Cart creation, proposal request, contract review, procurement process | Purchase completed, contract signed |
| **Onboarding** | First experience with the product or service post-purchase | Purchase confirmation, account creation, first login | Completes onboarding steps, reaches activation milestone |
| **Active** | Regular, engaged customer deriving value | Consistent product usage, repeat purchases, support interactions | Usage decline, purchase frequency drop, complaint escalation |
| **Advocacy** | Actively promotes and refers the brand | NPS 9-10, public review, social share, referral submission, case study participation | Engagement decline, NPS drop, stops referring |
| **At-Risk** | Showing disengagement signals but not yet lost | Usage decline >30%, support ticket escalation, NPS drop, payment failure | Responds to retention intervention OR cancels/goes silent |
| **Churned** | No longer a customer | Cancellation, subscription lapse, 90+ days no purchase, account deletion | Win-back response, re-purchase, re-subscription |

### Transition Events
Events that move customers between states. Each transition has a trigger event, a probability, and an average time-to-transition:

- **Awareness to Consideration**: Trigger — return visit within 14 days, content download, email signup. Typical probability: 15-25% of aware contacts. Average time: 3-21 days
- **Consideration to Evaluation**: Trigger — pricing page view, demo request, trial start, sales inquiry. Typical probability: 20-40% of considering contacts. Average time: 7-30 days
- **Evaluation to Decision**: Trigger — proposal acceptance, trial conversion, verbal commitment. Typical probability: 30-60% of evaluating contacts. Average time: 7-60 days (B2B can be 90+ days)
- **Decision to Onboarding**: Trigger — purchase completion. Typical probability: 85-95% (cart abandonment and contract fall-through account for the gap). Average time: 1-7 days
- **Onboarding to Active**: Trigger — activation milestone reached (defined per product). Typical probability: 60-80%. Average time: 7-30 days. This is the most critical transition — failure here drives early churn
- **Active to Advocacy**: Trigger — NPS 9-10 response, unprompted review, referral submission. Typical probability: 10-25% of active customers. Average time: 60-180 days
- **Active to At-Risk**: Trigger — usage decline >30%, support escalation, NPS drop below 7. Typical probability: 15-30% annually. Average time: 30-90 days of declining signals
- **At-Risk to Churned**: Trigger — cancellation, non-renewal, 90 days inactivity. Typical probability: 40-70% of at-risk customers without intervention, 20-40% with intervention. Average time: 30-90 days

### Regression Transitions (Non-Linear Movement)
- **Evaluation back to Consideration**: Sticker shock on pricing, internal champion lost, competitor introduced late. Probability: 15-30%
- **Active back to Onboarding**: Major product update requiring re-learning, account migration, team turnover losing institutional knowledge. Handle with proactive re-onboarding campaigns
- **Churned to Awareness**: Win-back campaigns, market changes that renew the need, competitor failure. Probability: 5-15% within 12 months of churn

---

## 2. Cross-Channel Coordination Patterns

### Sequential Messaging (Progressive Narrative)
Each channel and touchpoint should add NEW information, not repeat the same message. Repetitive cross-channel messaging accelerates fatigue and signals poor orchestration.

**Awareness Stage Messaging**:
- **Social ads**: Problem/solution fit — establish the pain point and introduce the category. Format: short video, carousel, or static image. Tone: educational, curiosity-driven
- **Display/programmatic**: Brand awareness — logo, tagline, category association. Format: banner, native. Tone: minimal, memorable
- **Content/SEO**: Educational — how-to guides, industry reports, benchmarks. Format: long-form articles, infographics. Tone: authoritative, helpful

**Consideration Stage Messaging**:
- **Email nurture**: Social proof and differentiation — case studies, comparison guides, customer testimonials. Format: 3-5 email sequence over 2-3 weeks. Tone: consultative, evidence-based
- **Retargeting ads**: Specific value propositions — feature highlights, ROI claims, competitive advantages. Format: carousel of proof points, video testimonials. Tone: persuasive, specific
- **SMS/push**: Not appropriate for consideration stage. Reserve for later stages

**Decision Stage Messaging**:
- **Email**: Offer and urgency — limited time pricing, free implementation, bonus features. Format: single clear CTA. Tone: direct, confident
- **SMS**: Time-sensitive offers — "Your trial expires in 48 hours, lock in annual pricing." Format: 160 characters max. Tone: urgent, action-oriented
- **Sales outreach**: Personalized — address specific objections surfaced during evaluation, custom ROI projection, tailored proposal. Format: 1:1 communication. Tone: consultative, closing

### Medium-Appropriate Content Rules
- **Social**: Snackable, visual, scroll-stopping. Under 15 seconds for video. One idea per post. Optimized for the feed environment
- **Email**: Detailed, personal, scannable. 200-500 words for nurture. One primary CTA. Mobile-optimized layout
- **SMS**: Urgent, action-oriented. Under 160 characters. Only for time-sensitive communications. Requires explicit opt-in
- **Ads (display/programmatic)**: Awareness and retargeting. Minimal copy. Strong visual. Clear brand. Landing page does the heavy lifting
- **Content (blog/resource)**: Comprehensive, authoritative. 1,500-3,000 words for SEO. Structured for skimming (headers, bullets, tables). Optimized for both human readers and AI citation

---

## 3. Branching Logic Design

### Engagement-Based Branching
- **Email opened, link clicked**: Path A — continue nurture at current cadence with progressively deeper content
- **Email opened, no click**: Path B — resend with different subject line after 48 hours, then try different content angle
- **Email not opened (2 consecutive)**: Path C — switch channel (social retargeting, SMS if opted in), then re-engage via email with different sender name and time-of-day
- **Email not opened (4 consecutive)**: Path D — move to re-engagement sequence. If no engagement after re-engagement, suppress from email to protect deliverability

### Behavioral Branching
- **Visited pricing page**: High intent signal. Branch to sales-ready path — trigger sales notification, send pricing comparison content, offer demo/consultation
- **Visited blog only**: Lower intent. Branch to nurture path — continue educational content, build trust before commercial messaging
- **Started free trial**: Activation path — onboarding email sequence focused on reaching activation milestone, in-app guidance, check-in from success team
- **Downloaded gated content**: Middle-of-funnel signal. Branch to topic-specific nurture path aligned with the content topic they downloaded
- **Visited careers page**: Non-buyer signal. Suppress from sales sequences. Optionally add to employer brand audience

### Time-Based Branching
- **No action in 7 days**: Trigger re-engagement — different channel, different message angle, or value-add content (not another sales pitch)
- **No action in 21 days**: Move to low-frequency nurture (monthly rather than weekly). Reduce investment but maintain presence
- **No action in 60 days**: Move to dormant list. Quarterly re-engagement attempt only. Focus budget on active contacts
- **Sudden re-engagement after dormancy**: Flag for immediate attention. Re-score lead. Route to appropriate stage based on re-engagement behavior

### Predictive Branching
- **High lead score (80+)**: Fast-track to sales. Skip middle nurture stages. Direct human outreach within 24 hours
- **Medium lead score (50-79)**: Continue nurture but accelerate cadence. Include more commercial content (case studies, ROI calculators, comparison guides)
- **Low lead score (<50)**: Standard nurture pace. Focus on education and trust-building. Do not waste sales team time
- **Score trending up rapidly**: Alert sales even if absolute score is medium. Momentum matters — a contact going from 30 to 65 in a week is more valuable than a stable 70

---

## 4. Journey Simulation (Monte Carlo Method)

### Setup
1. Define all journey states and transitions (from the state machine above)
2. Assign transition probabilities based on historical data (or industry benchmarks if no historical data exists)
3. Assign time-to-transition distributions (not point estimates — use distributions: normal, lognormal, or empirical)
4. Define entry rate (how many new contacts enter the Awareness state per day/week)
5. Define simulation parameters: number of simulated customers (minimum 10,000 for stable results), time horizon (6-12 months)

### Execution
For each simulated customer:
1. Start in the Awareness state
2. At each time step, draw a random number against the transition probability to determine if the customer moves to the next state, regresses, or stays
3. If transitioning, draw a time-to-transition from the distribution to determine when the transition occurs
4. Continue until the customer reaches a terminal state (Churned, Advocacy) or the simulation time horizon is reached
5. Record the full path: states visited, time spent in each state, final state

### Output Analysis
- **Expected conversion rate**: Percentage of simulated customers who reach Decision/Purchase state. Report mean and 90% confidence interval
- **Average time-to-convert**: Mean time from Awareness to Decision. Segment by path type (direct vs. regression-included paths)
- **Bottleneck identification**: The state with the highest exit-to-churn rate is the primary bottleneck. The state with the longest average dwell time is the primary friction point. These are often different states requiring different interventions
- **Revenue projection**: Multiply conversion rate by average deal value. Report as a range: 10th percentile (pessimistic), 50th (expected), 90th (optimistic)
- **Path analysis**: Identify the most common paths to conversion. Identify the most common paths to churn. Understand which regressions are recoverable and which are terminal

### Sensitivity Analysis
Run the simulation while varying one parameter at a time:
- What happens if we improve Consideration-to-Evaluation transition probability by 10%? (Impact of better mid-funnel content)
- What happens if we reduce Onboarding-to-Active time by 20%? (Impact of better onboarding)
- What happens if we reduce At-Risk-to-Churned probability by 15%? (Impact of better retention program)
- Rank interventions by their simulated revenue impact to prioritize investment

---

## 5. Growth Loop Taxonomy

### Viral Loops
- **Mechanism**: User invites other users, who become users, who invite more users
- **Key metric**: Viral coefficient (K) = invites per user x conversion rate per invite. Sustainable organic growth requires K > 1. Most products achieve K = 0.2-0.6, which amplifies paid acquisition but does not replace it
- **Cycle time**: Days to weeks. Faster cycle time = faster compounding
- **Optimization levers**: Reduce friction in invite flow, increase incentive for inviter and invitee, make sharing a natural part of the product experience (not a bolt-on)
- **Examples**: Dropbox referral program, Slack team invites, Calendly meeting links (product-led viral loop)

### Content Loops
- **Mechanism**: Content attracts users, users create content (reviews, UGC, community posts), more content attracts more users
- **Key metric**: Content creation rate per active user, organic traffic per piece of user-generated content
- **Cycle time**: Weeks to months (SEO indexing and ranking takes time)
- **Optimization levers**: Lower barriers to content creation, improve content discoverability (SEO, internal search), incentivize quality contributions
- **Examples**: TripAdvisor reviews, Reddit posts, Stack Overflow answers, Amazon product reviews

### Data Network Effects (Data Loops)
- **Mechanism**: More users generate more data, better data improves the product, better product attracts more users
- **Key metric**: Product quality improvement rate per unit of data, user growth rate correlated with data volume
- **Cycle time**: Months (model retraining, product improvement cycles)
- **Examples**: Google Search (more queries = better results), Waze (more drivers = better traffic data), recommendation engines

### Paid Reinvestment Loops
- **Mechanism**: Revenue from customers funds acquisition spend, which generates more customers, which generates more revenue
- **Key metric**: Payback period (how long until a customer's revenue covers their acquisition cost). Sustainable if payback period < available capital runway
- **Cycle time**: Payback period length. Shorter payback = faster compounding
- **Optimization levers**: Reduce CAC (better targeting, better conversion rates), increase early-stage revenue (faster onboarding, quicker first purchase), optimize LTV (retention, upsell)

### Ecosystem/Marketplace Loops
- **Mechanism**: Supply attracts demand, demand attracts supply. Two-sided network effect
- **Key metric**: Liquidity — the probability that a participant on one side finds a match on the other side in a reasonable time
- **Cycle time**: Varies. Initial loop is hardest to start (chicken-and-egg problem). Once spinning, cycle time shortens as the marketplace grows
- **Examples**: Uber (drivers attract riders attract drivers), Airbnb (hosts attract guests attract hosts), app stores

---

## 6. Growth Loop Modeling

### For Each Loop, Define
1. **Input metric**: What feeds the loop? (New signups, content published, revenue generated, invites sent)
2. **Amplification factor**: How many new inputs does each cycle generate? (Each user invites 2.3 friends on average, each $1 of revenue reinvested generates $1.40 in new revenue)
3. **Cycle time**: How long for one complete loop iteration? (Viral loop: 5 days. Paid loop: 45 days. Content loop: 90 days)
4. **Compounding rate**: Amplification factor per cycle time. This is the true growth rate of the loop
5. **Decay factor**: What percentage of the loop output is lost each cycle? (Churn, invite fatigue, content aging, market saturation). Sustainable growth requires amplification factor > decay factor
6. **Bottleneck**: Which step in the loop is the constraint? (Invite acceptance rate? Content creation rate? Payback period length?) Optimizing the bottleneck has the highest leverage

### Multi-Loop Strategy
Most successful companies run multiple loops simultaneously:
- **Primary loop**: The dominant growth driver. Usually paid reinvestment for early-stage companies, viral or content for mature companies
- **Amplifier loop**: A secondary loop that accelerates the primary. Content loop amplifies paid loop by reducing CAC through organic traffic. Viral loop amplifies everything by adding zero-CAC users
- **Defensive loop**: A loop that creates switching costs or moats. Data loops and ecosystem loops are the strongest defensive loops — competitors cannot replicate the data or network without the users

---

## 7. Dark Funnel Intelligence

### What the Dark Funnel Is
The dark funnel encompasses all buyer journey activities invisible to traditional analytics and attribution: private Slack conversations about your product, AI chatbot recommendations, podcast mentions, word-of-mouth referrals, dark social sharing (links shared via private messaging apps), community discussions in closed groups, and offline conversations. Studies estimate 60-80% of the B2B buyer journey happens in the dark funnel before any trackable interaction.

### Signal Detection Methods
- **Reddit and community monitoring**: Track brand name, product name, and category terms in relevant subreddits and forums. Use Reddit API or social listening tools with Boolean queries. Monitor r/[your-industry] and competitor communities
- **AI chatbot citation tracking**: Use GEO (Generative Engine Optimization) tools to monitor whether AI assistants (ChatGPT, Perplexity, Google AI Overview, Copilot) cite your content when answering relevant queries. Track citation frequency over time
- **Podcast attribution**: Create vanity URLs for podcast sponsorships and guest appearances (yoursite.com/podcastname). Track branded search volume lift in the 48 hours following episode publication. Compare to baseline branded search volume
- **Self-reported attribution**: Add "How did you hear about us?" as a required field on demo request and signup forms. Offer both structured options (dropdown) and freeform text. Analyze freeform responses monthly for emerging dark funnel channels
- **Direct traffic analysis**: Unexplained spikes in direct traffic or branded search volume that do not correlate with any tracked campaign activity indicate dark funnel influence. Cross-reference with podcast episodes, community discussions, or PR activity timing
- **Referral path analysis**: Monitor referral traffic from messaging-adjacent sources (t.co shortened links from Twitter DMs, l.messenger.com from Facebook Messenger, various link shorteners used in Slack and Discord)

### Dark Funnel Illumination Strategies
- **Post-purchase surveys**: Standardized attribution survey sent within 24 hours of purchase. Include specific dark funnel options: "recommendation from a colleague," "heard about us in a podcast," "saw a community discussion," "an AI assistant recommended us"
- **Branded search as proxy**: Treat branded search volume as a composite metric for all brand awareness activity, including dark funnel. Track weekly and correlate with known marketing activities — the unexplained portion approximates dark funnel impact
- **Community seeding**: Actively participate in the communities where your audience discusses solutions (Reddit, Slack groups, Discord servers, industry forums). Provide genuine value, not promotional content. Build presence so that when recommendations happen organically, your brand is top of mind
- **Influencer and creator partnerships**: Creators operate primarily in the dark funnel. Their recommendations travel via word-of-mouth, private shares, and conversation. Measure impact through branded search lift, self-reported attribution, and vanity URL tracking rather than last-click attribution
- **Content designed for sharing**: Create content specifically optimized for private sharing — tools, calculators, templates, checklists, and frameworks that people naturally share with colleagues via Slack or email. These assets travel through the dark funnel and bring people back to your site
