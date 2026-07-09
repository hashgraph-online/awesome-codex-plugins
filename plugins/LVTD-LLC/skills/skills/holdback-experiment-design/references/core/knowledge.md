# Holdback Experiment Design Knowledge

Core concepts for long-term experiment holdbacks.

## Overview

A holdback keeps a small, defined population from receiving a feature after a
broader rollout so the team retains a counterfactual. This can reveal delayed
benefits, delayed harms, degradation, or cumulative effects that short A/B tests
miss.

## Holdback Types

### Degradation Holdback

**Definition**: A holdback designed to detect whether a launched change causes
metrics to degrade over time.

Use when the risk is delayed harm, stability loss, or long-term user behavior
change.

### Long-Term Cumulative Holdback

**Definition**: A holdback designed to measure the cumulative value of a feature
over a longer period.

Use when the change may compound across weeks or months, such as personalization,
recommendations, retention loops, or habit-forming experiences.

## Key Concepts

### Counterfactual

**Definition**: The comparison that estimates what would have happened without
the launched change.

The holdback preserves this comparison after most users receive the feature.

### Withholding Cost

**Definition**: The user, business, ethical, or trust cost of preventing a group
from receiving the launched experience.

Holdbacks are not free; the cost should be explicit.

### Readout Cadence

**Definition**: The schedule for checking long-term metrics and deciding
whether the holdback should continue.

Cadence prevents holdbacks from becoming forgotten permanent exclusions.

## Quick Reference

| Need | Holdback Type |
|------|---------------|
| Detect delayed metric harm | Degradation |
| Measure compounding value | Long-term cumulative |
| Preserve launch counterfactual | Either, depending on question |
| Manage ethical/user cost | Smallest useful population and duration |
