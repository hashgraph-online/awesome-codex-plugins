# Inclusive Experiment Analysis Rules

Rules for designing and interpreting inclusive experiment analysis.

## Core Rules

### 1. Start With Plausible Difference In Experience

Choose dimensions because the product change could affect those users
differently, not because the data happens to be available.

### 2. Check Representation Before Interpreting Safety

If a subgroup is absent or too small, say the experiment cannot verify impact
for that subgroup.

### 3. Check Balance When Dimensions Matter

When test and control differ materially on a relevant dimension, avoid treating
the subgroup result as clean causal evidence.

### 4. Treat Accessibility As More Than A Metric

Some accessibility issues will not show up clearly in engagement metrics. Pair
experiment readouts with accessibility review when the change touches content,
navigation, media, contrast, motion, or input mode.

### 5. Do Not Average Away Harm

A positive aggregate result can still be unacceptable if a meaningful group is
harmed.

### 6. Label Exploratory Segments

If subgroup analysis was not planned before the test, label it exploratory and
use it to guide follow-up rather than overclaiming proof.

## Quick Reference

| Check | Good Question |
|-------|---------------|
| Relevance | Could this group experience the change differently? |
| Ethics | Should we use this dimension, and under what governance? |
| Data | Is the dimension available and trustworthy? |
| Balance | Are test and control comparable? |
| Impact | Did outcomes differ meaningfully? |
| Decision | Does subgroup harm change launch or mitigation? |
