# A/B Testing Platform Strategy Knowledge

Core concepts for experimentation platform planning.

## Overview

An A/B testing platform is not only a UI for toggling variants. It is a system
for assignment, targeting, exposure logging, data collection, metric
calculation, result access, governance, and operational safety.

## Core Components

### Targeting and Eligibility

Defines which users can enter an experiment based on product, account, region,
device, permission, or other criteria.

### Assignment

Assigns eligible users to control or test variants. Assignment must be stable
enough for the product experience and randomized enough for valid comparison.

### Exposure Logging

Records when a user actually encounters the experimental experience. Exposure
events connect assignment to analysis.

### Feature Delivery

Serves the correct experience to the correct user. This may use feature flags,
configuration, server-side logic, client-side logic, or a third-party SDK.

### Metric Pipeline

Transforms product events into experiment metrics. This includes data quality,
granularity, definitions, and repeatable computation.

### Results Access

Makes experiment results available through dashboards, notebooks, reports, or
self-service tools.

### Governance

Controls ownership, approvals, naming, documentation, guardrails, and rollout
rules.

## Build, Buy, Hybrid

| Option | Best Fit |
|--------|----------|
| Build | Unique product constraints, deep internal data needs, strong platform team |
| Buy | Need speed, common web/app use cases, limited internal platform capacity |
| Hybrid | Third-party delivery plus internal metrics, or internal assignment plus external reporting |
| Manual/simple | Early proof of value, low experiment volume, limited budget |

## Maturity Levels

| Level | Description |
|-------|-------------|
| Manual | Engineers and analysts coordinate tests with scripts or simple flags |
| Basic | Assignment, exposure logging, and repeatable metric queries exist |
| Managed | Dashboards, templates, approvals, and quality checks exist |
| Self-service | Product teams can safely configure and read experiments |
| Platform | Experimentation is integrated into product and engineering workflows |
