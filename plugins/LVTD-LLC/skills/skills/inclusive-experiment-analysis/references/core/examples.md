# Inclusive Experiment Analysis Examples

## Bandwidth And Accessibility Scenario

**Change**: Add images to a content discovery surface.

**Dimensions to consider**:
- Bandwidth or connection quality.
- Device type.
- Screen reader or alt text support.
- Page or app performance.

**Potential concern**: Images may improve engagement for many users while
slowing the experience for users with lower bandwidth or creating accessibility
gaps without useful alternative text.

## Privacy Behavior Scenario

**Change**: Use additional behavioral data for personalized recommendations.

**Dimensions to consider**:
- Privacy settings.
- Device or operating system.
- Data-sharing consent.
- Recommendation quality by segment.

**Potential concern**: Users who share less data may receive worse
recommendations and show lower engagement, even if the aggregate metric rises.

## Usage-Level Scenario

**Change**: Add a personalized homepage.

**Dimensions to consider**:
- High-consumption users.
- Low-consumption users.
- New versus returning users.

**Potential concern**: Aggregate lift may be small because one subgroup benefits
while another is unchanged.

## Weak Inclusive Claim

```markdown
The test improved the primary metric, so it improves the product for users.
```

**Problems**:
- Does not identify which users are represented.
- Does not check subgroup harm.
- Does not consider accessibility or context-specific constraints.
