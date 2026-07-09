# Experiment Verification Monitoring Knowledge

Core concepts for operational experiment quality.

## Overview

Experiment verification and monitoring protect the quality of evidence before
and during an experiment. The work is operational: confirm the test is
configured correctly, detect issues early, and validate that the platform itself
can be trusted.

## Key Concepts

### Prelaunch Verification

**Definition**: Checks performed before launch to confirm targeting,
assignment, treatment, exposure logging, metrics, and user experience.

Prelaunch verification prevents avoidable configuration errors from reaching
users.

### QA Tool

**Definition**: Internal tooling that lets teams spot-check control and
treatment experiences before or during launch.

Good QA tooling reduces manual guesswork and makes test setup reproducible.

### Experiment Canary

**Definition**: A small early launch or health check that catches configuration
or instrumentation issues before full experiment exposure.

Canaries are useful when launch mistakes are costly but can be detected quickly.

### A/A Test

**Definition**: An experiment where both groups receive the same experience, used
to test assignment, measurement, and analysis infrastructure.

A/A tests help detect hidden platform issues and build confidence in the
experiment system.

### Leakage And Interference

**Definition**: Problems where users, treatments, or effects cross boundaries in
ways that violate the experiment design.

Leakage and interference can come from shared accounts, social effects,
overlapping tests, or implementation mistakes.

## Terminology

| Term | Definition |
|------|------------|
| Assignment | Variant allocation for eligible units |
| Exposure | Event showing a user encountered the tested experience |
| Spillover | Effect from one user or group influencing another |
| Canary | Small launch or health signal before broad exposure |
| Gold standard | Required quality bar for correctly configured experiments |

## How It Relates To

- **A/B test design brief**: The brief defines what verification must check.
- **Experimentation throughput strategy**: Overlapping tests need conflict and
  interference monitoring.
- **Trustworthy experiment insights**: Operational health is a prerequisite for
  credible statistical interpretation.

## Common Misconceptions

- **Myth**: If the final dashboard runs, the experiment is healthy.
  **Reality**: The setup may be wrong even if metrics compute.
- **Myth**: Manual QA is enough.
  **Reality**: Recurring platform use needs repeatable tools and checks.
- **Myth**: A/A tests are only for new platforms.
  **Reality**: Mature systems can drift and need periodic health checks.

## Quick Reference

| Concept | One-Line Summary |
|---------|------------------|
| Prelaunch verification | Confirm setup before user exposure |
| QA tool | Spot-check treatment and control experiences |
| Canary | Catch early launch issues quickly |
| A/A test | Validate platform health with identical treatments |
| Leakage/interference | Detect boundary violations and cross-test effects |
