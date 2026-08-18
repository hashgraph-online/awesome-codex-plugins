# A/B Test Results Readout Knowledge

Core concepts for interpreting and communicating experiment results.

## Overview

An experiment readout explains what happened, why it may have happened, what the
data can and cannot support, and what decision should follow. Good readouts
combine metric comparisons with context about data quality, population,
segments, and tradeoffs.

## Key Concepts

### Readout

**Definition**: A structured explanation of experiment results and the
recommended decision.

It should be understandable to product, engineering, analytics, and business
stakeholders.

### Ad Hoc Analysis

**Definition**: Follow-up analysis beyond the preconfigured result dashboard.

Use it when the initial metric movement is surprising, flat, mixed, or likely
to differ across user groups.

### Subgroup Analysis

**Definition**: Splitting test and control users into meaningful groups to
understand whether effects differ across user types.

Subgroup analysis can explain averages, but it should be handled carefully to
avoid cherry-picking.

### Outlier Check

**Definition**: Looking for extreme observations that distort averages.

Outlier checks are important when metrics aggregate user behavior and a small
set of users can dominate the mean.

### Analyst-Friendly Data

**Definition**: Data that can be queried at the granularity needed for the
experiment question, such as user, device, variant, exposure, or event level.

Analyst-friendly data makes deeper readouts possible.

## Visualization Principles

| Need | Useful View |
|------|-------------|
| Compare control and test | Bar chart or interval plot |
| Show trend over time | Line chart |
| Show segment differences | Small multiples or grouped bars |
| Show distribution or outliers | Histogram, box plot, or percentile table |
| Explain decision | Summary table with metric roles |

## Common Misconceptions

- **Myth**: A dashboard result is the full analysis.
  **Reality**: Dashboards can start the readout, but surprising results often
  need ad hoc investigation.
- **Myth**: Averages represent every user.
  **Reality**: Averages can hide subgroup differences and outliers.
- **Myth**: More charts mean a better readout.
  **Reality**: Each chart should answer a stakeholder question.
