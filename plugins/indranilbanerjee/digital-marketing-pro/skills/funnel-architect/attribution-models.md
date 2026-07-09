# Attribution Models — Comparison & Implementation Guide

## Model Comparison

| Model | How It Works | Best For | Limitation |
|-------|-------------|----------|-----------|
| **Last-Click** | 100% credit to last touchpoint | Short sales cycles, direct response | Ignores awareness/consideration |
| **First-Click** | 100% credit to first touchpoint | Brand awareness campaigns | Ignores nurture/conversion steps |
| **Linear** | Equal credit to all touchpoints | Balanced overview | Over-credits low-impact touches |
| **Time-Decay** | More credit to touches closer to conversion | Long sales cycles, B2B | Under-credits awareness |
| **Position-Based (U-shape)** | 40% first, 40% last, 20% split among middle | Balanced with emphasis on intro/close | Somewhat arbitrary splits |
| **Data-Driven** | ML model allocates based on actual impact | Large datasets (300+ conversions/month) | Requires significant data volume |
| **Marketing Mix Modeling** | Econometric model using aggregate data | Budget allocation across channels | Slow, requires historical data |

---

## Model Selection Decision Tree

```
START: How many conversions per month?
├── < 300 → Use Position-Based or Time-Decay
│   ├── Short sales cycle (< 7 days)? → Last-Click or Linear
│   └── Long sales cycle (> 30 days)? → Time-Decay
├── 300-1000 → Consider Data-Driven
│   └── Is your analytics platform capable? → Use Data-Driven
└── > 1000 → Use Data-Driven + MMM for budget planning

BUSINESS MODEL OVERRIDES:
- eCommerce / DTC → Last-Click baseline, upgrade to Data-Driven when possible
- B2B SaaS → Position-Based or Time-Decay (long cycles, many touches)
- Local Business → Last-Click (simple journeys)
- Marketplace → Separate attribution for supply and demand sides
```

---

## Platform Implementation Guides

### Google Analytics 4 (GA4)

- **Default**: Data-driven attribution (cross-channel)
- **Setup**: Admin → Attribution Settings → Choose model and lookback window
- **Lookback windows**: 30 days for acquisition, 90 days for other conversions
- **Reports**: Advertising → Attribution → Model comparison
- **Limitation**: Only tracks Google-visible touchpoints, cannot see all walled garden data

### Meta (Facebook) Attribution

- **Default**: 7-day click, 1-day view attribution
- **Conversions API (CAPI)**: Server-side event tracking for better match rates
- **Aggregated Event Measurement**: For iOS 14+ tracking limitations
- **Recommended**: Configure CAPI + browser pixel for maximum data coverage
- **Compare**: Meta's self-reported conversions vs GA4's cross-channel view

### Google Ads

- **Default**: Last-click within Google Ads
- **Data-driven**: Available in conversion settings when sufficient data
- **Cross-campaign**: Attribution applies across Search, Display, YouTube, Shopping
- **Recommendation**: Enable data-driven attribution, set appropriate conversion windows

---

## Cross-Device Attribution

### Challenges
- Same user, different devices appears as multiple users
- Cookie-based tracking breaks across devices
- Privacy regulations limit cross-device linking

### Solutions
1. **Deterministic matching**: Logged-in user IDs across devices (most accurate, requires auth)
2. **Probabilistic matching**: Statistical models linking device patterns (less accurate)
3. **Google Signals**: Cross-device data from logged-in Google users in GA4
4. **CRM integration**: Match conversions to known contacts across touchpoints

---

## Custom Model Design Framework

When standard models don't fit:

1. **Define touchpoint categories**: Awareness, Engagement, Conversion Assist, Conversion
2. **Assign category weights** based on business model:
   - B2B SaaS: Awareness 20%, Engagement 30%, Assist 20%, Conversion 30%
   - eCommerce: Awareness 15%, Engagement 15%, Assist 20%, Conversion 50%
3. **Test against actual outcomes**: Compare model predictions to observed patterns
4. **Iterate quarterly**: Adjust weights based on incrementality test results

---

## Attribution Validation

### How to Verify Your Model Is Accurate

1. **Holdout tests**: Pause a channel, measure true impact vs model-predicted impact
2. **Incrementality tests**: Geo-split or user-split experiments per channel
3. **Cross-model comparison**: Run 2-3 models in parallel, compare conclusions
4. **Sanity checks**: Does the attribution match what you intuitively know about channel performance?
5. **Revenue reconciliation**: Do attributed conversions sum to actual revenue?

### Red Flags

- A single channel claims >80% of conversions (likely measurement bias)
- Model suddenly changes attribution dramatically (check for tracking issues)
- Branded search gets majority credit (it's capturing demand, not creating it)
- Model ignores channels you know drive awareness (review touchpoint capture)
