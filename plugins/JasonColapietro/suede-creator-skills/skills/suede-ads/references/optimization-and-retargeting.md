# Campaign Optimization


For hard kill/keep/scale thresholds, use the platform playbooks (see Reference Routing): the kill rules and breakeven CPL/CPC math live in [b2b-paid-playbook.md](b2b-paid-playbook.md), and Meta's full decision tree lives in [meta-decision-system.md](meta-decision-system.md).

### Key Metrics by Objective

| Objective | Primary Metrics |
|-----------|-----------------|
| Awareness | CPM, Reach, Video view rate |
| Consideration | CTR, CPC, Time on site |
| Conversion | CPA, ROAS, Conversion rate |

### Optimization Levers

"Too high" and "low" below are not opinions. **Too high** means above the break-even CPA / ROAS ceiling computed in Scaling discipline, and **low** means below the funnel benchmark in the platform playbook for that channel. Compute the ceiling before you pull any lever, and for hard kill/scale thresholds, use the playbooks routed at the top of Campaign Optimization.

**If CPA is too high:**
1. Check landing page (is the problem post-click?)
2. Tighten audience targeting
3. Test new creative angles
4. Improve ad relevance/quality score
5. Adjust bid strategy

**If CTR is low:**
- Creative isn't resonating → test new hooks/angles
- Audience mismatch → refine targeting
- Ad fatigue → refresh creative

**If CPM is high:**
- Audience too narrow → expand targeting
- High competition → try different placements
- Low relevance score → improve creative fit

### Bid Strategy Progression
1. Start with maximize-conversions (no target) or cost caps while data is thin
2. Gather conversion data: roughly 30 per month per campaign on Google, about
   50 per week per ad set to leave Meta's learning phase
3. Set targets (tCPA, tROAS, cost cap) at or slightly above trailing actuals
4. Move targets in 10 to 15% steps and wait one to two weeks between moves

---

## Retargeting Strategies

### Funnel-Based Approach

| Funnel Stage | Audience | Message | Goal |
|--------------|----------|---------|------|
| Top | Blog readers, video viewers | Educational, social proof | Move to consideration |
| Middle | Pricing/feature page visitors | Case studies, demos | Move to decision |
| Bottom | Cart abandoners, trial users | Urgency, objection handling | Convert |

### Retargeting Windows

| Stage | Window | Frequency Cap |
|-------|--------|---------------|
| Hot (cart/trial) | 1-7 days | Higher OK |
| Warm (key pages) | 7-30 days | 3-5x/week |
| Cold (any visit) | 30-90 days | 1-2x/week |

### Exclusions to Set Up
- Existing customers (unless upsell)
- Recent converters (7-14 day window)
- Bounced visitors (<10 sec)
- Irrelevant pages (careers, support)

### Retarget with a different offer

The conventional retargeting playbook re-shows the same product/offer to people who didn't buy. Working premise: **the most common reason someone didn't buy is that the offer wasn't right for them.** Re-showing the same thing harder doesn't help.

Instead, retarget with **different** products, services, or offers from your catalog:
- Visitor clicked on protein powder, didn't buy → retarget with creatine (totally different category)
- Visitor downloaded a lead magnet, didn't book a call → retarget with a different lead magnet on a related topic
- Visitor viewed pricing, didn't sign up → retarget with a free audit or assessment instead

Measure it as its own ad set against same-offer retargeting; the lift varies by catalog depth and margin.

### The four-ad retargeting layer

Build out your retargeting layer with these 4 ad types running simultaneously:

1. **Objection-handling ad**: directly addresses the most common reasons people didn't buy. To find these, **outbound call every lead** who didn't convert and ask why. The verbatim objections become the headline of this ad.
2. **Proof testimonial carousel**: multi-image/multi-slide carousel of testimonials and proof that supports the claims of your original ad
3. **Other-offers CBO**: your other best-performing ads for other products/services in one CBO, retargeted to the same audience
4. **Value-first audit/assessment ad**: wraps your call in a free piece of value. Whether they buy or not, they leave with something useful. Lowers the friction to engage.

Run the four together against the audience that did not convert, and judge the layer on blended CPA, not each ad alone.

---
