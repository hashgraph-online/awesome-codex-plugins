# Inclusive Experiment Analysis Knowledge

Core concepts for evaluating product experiments across user groups.

## Overview

Inclusive experiment analysis asks whether a product change works for the range
of users affected by it, not only for the average or majority user. It uses
relevant dimensions and subgroup analysis to identify uneven benefit or harm.

## Key Concepts

### User Dimension

**Definition**: An attribute or context that may affect how a user experiences
the change.

Examples include device type, bandwidth, accessibility needs, geography,
language, tenure, usage level, privacy settings, plan type, or content
preferences.

### Representation

**Definition**: Whether the users in the experiment include enough of a group
to support a meaningful conclusion.

Without representation, absence of measured harm is not evidence of safety.

### Test/Control Balance

**Definition**: Whether important dimensions are similarly distributed across
variants.

Imbalance can make subgroup interpretation unreliable.

### Subgroup Harm

**Definition**: A negative effect concentrated in a specific group even when the
overall result is neutral or positive.

Subgroup harm should influence launch decisions, mitigations, and follow-up
research.

### Ethical Dimension Use

**Definition**: Using user attributes only when relevant, lawful, respectful,
and necessary for product safety or inclusion.

Do not collect or analyze sensitive attributes without a clear reason and proper
governance.

## Dimension Prompts

| Dimension | Ask |
|-----------|-----|
| Accessibility | Does the change affect screen readers, alt text, keyboard access, color, motion, or comprehension? |
| Device | Does the experience differ across mobile, web, TV, OS, or browser? |
| Bandwidth | Does media, image weight, or latency create unequal performance? |
| Privacy | Could privacy choices affect recommendation quality or data availability? |
| Usage level | Do high- and low-activity users respond differently? |
| Geography/language | Does context or localization affect meaning or access? |
