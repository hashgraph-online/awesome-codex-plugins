---
name: interface-matrix
type: reference
parent_skill: dfmea-design
author: RBraga01
version: "1.0"
status: approved
created: "2026-06-01"
last_updated: "2026-06-03"
updated_by: RBraga01
reviewed_by: RBraga01
license: MIT
---

# Interface Matrix — DFMEA Reference

Guide for constructing an interface matrix and boundary diagram for Design FMEA.
Use alongside the [dfmea-design](../SKILL.md) skill.

> **Scope:** This document covers interface analysis reference logic — boundary diagrams, matrix construction, failure patterns, tolerance stack-up, and validation methods.
> For the step-by-step DFMEA execution workflow, see [dfmea-design SKILL.md](../SKILL.md).

---

## Required Execution Checklist

☐ Define system boundary (inside vs outside scope)
☐ Identify all external elements (components, environment, user, process, maintenance)
☐ Build interface matrix — assign interaction type for every element pair
☐ Identify at least one failure mode for every interface cell with an interaction type
☐ All interfaces have at least one validated failure mode (no silent/empty interactions)
☐ Assign system-level effects for each interface failure
☐ Include misuse and abuse scenarios in user interface analysis
☐ Analyse tolerance stack-up for all critical mechanical interfaces
☐ Validate critical interfaces using analysis (FEA, simulation) or testing (DVP)
☐ Prioritise interfaces by severity and likelihood — focus resources on high-risk interactions
☐ Transfer interface failure modes to DFMEA Step 4
☐ Confirm DVP includes validation tests for all critical interfaces

---

## Why Interfaces Matter

Most design failures occur at **interfaces**, not within a single component.

A component may perform its individual function perfectly, but fail when it interacts with:
- Adjacent components (mechanical contact, electrical connection)
- The environment (temperature, vibration, humidity, corrosion)
- The assembly process (handling forces, fixture contact, torque application)
- The user (loading, misuse scenarios, maintenance access)

An interface matrix maps all these interactions systematically so no failure path is overlooked.

---

## Boundary Diagram

The boundary diagram defines what is **inside** and **outside** the DFMEA scope,
and shows the interfaces at the boundary.

### Elements

**System under analysis (inside scope)**
The component, subsystem, or system being designed.

**External elements (outside scope)**
- Other components in the assembly (customer-supplied or other design teams)
- Environment: thermal, vibration, humidity, electromagnetic, chemical
- User / operator (including misuse and abuse scenarios — over-torque, incorrect installation, off-label use)
- Assembly process (fixtures, torques, handling)
- Maintenance / service (access, tools, replacement cycles)

**Interface arrows**
Draw an arrow for each interaction across the boundary. Label each arrow with:
- The type of interaction (force, signal, thermal, fluid, chemical)
- The direction: input to system, output from system, or bidirectional
- The nominal condition and operating range (if known)

All interface arrows must include direction (input/output) and operating range.

### Example — ECU boundary diagram

```
Environment (Temp -40°C to +125°C, vibration 10-2000 Hz) → input
        ↕
Wiring harness ←→ [ECU] ←→ CAN bus (bidirectional, 500 kbit/s)
                    ↕
              Mounting bracket (vibration load transfer → input)
                    ↕
           Vehicle ground (electrical reference → input)
```

---

## Interface Matrix — Construction

### Step 1: List all elements

Column and row headers: the component under analysis + all external elements.

### Step 2: Identify interaction type at each intersection

For each pair of elements, identify whether they interact and how.

| Interaction type | Symbol | Examples |
|----------------|--------|---------|
| Force / mechanical | F | Clamping, contact, vibration, thermal expansion |
| Electrical / signal | E | Voltage, current, ground reference, signal |
| Thermal | T | Heat conduction, thermal resistance, temperature delta |
| Fluid / chemical | C | Hydraulic pressure, corrosion medium, lubrication |
| Optical / radiation | O | EMC, light, UV |
| No interaction | — | |

When multiple interaction types exist at the same interface, list all of them explicitly (e.g., F + T + C). Do not collapse multiple types into a single symbol.

### Example — Connector interface matrix

|  | PCB | Backshell | Wire | Environment | User |
|--|-----|-----------|------|-------------|------|
| **Connector body** | F, E | F | E | T, C | F |
| **Contacts (pins)** | E | — | E | C | — |
| **Sealing** | — | F | F | C | — |

### Step 3: For each interaction, identify failure mode candidates

For each "F", "E", "T", or "C" cell, ask:
- What can go wrong at this interface?
- What is the consequence to the system function?

**Example — Connector body × Environment (T, C):**
- Thermal failure mode: housing deforms under sustained high temperature, contact force lost → intermittent connection
- Chemical failure mode: connector body corrodes in salt spray environment → housing fracture under vibration

These become Failure Modes in Step 4 of the DFMEA.

### Step 4: Prioritise interfaces

Not all interfaces carry equal risk. Prioritise based on:
- **Severity** of the worst system effect if the interface fails
- **Likelihood** of failure given the operating environment
- **Detectability** — interfaces that fail silently are highest priority

Focus DFMEA depth and DVP effort on high-severity, hard-to-detect interfaces first.

---

## Interface Failure Mode Patterns

### Mechanical interfaces
| Failure mode | Typical cause |
|-------------|--------------|
| Fretting / wear | Micro-motion under vibration, insufficient clamping force |
| Stress concentration | Geometry (notch, sharp radius), improper tolerance stack-up |
| Thermal expansion mismatch | Dissimilar materials with different CTE |
| Loosening under vibration | Insufficient preload, no locking feature |
| Assembly damage | Handling force exceeds component strength |

### Electrical interfaces
| Failure mode | Typical cause |
|-------------|--------------|
| High contact resistance | Contamination, oxidation, insufficient contact force |
| Signal crosstalk | Insufficient isolation, grounding design |
| Short circuit | Creepage distance insufficient for operating voltage + contamination |
| EMC susceptibility | Shielding gap, ground loop |
| Ground reference drift | High-resistance ground path, shared ground with power |

### Thermal interfaces
| Failure mode | Typical cause |
|-------------|--------------|
| Thermal resistance too high | Poor thermal interface material, insufficient contact area |
| Thermal runaway | Positive feedback loop between power dissipation and junction temperature |
| Condensation | Temperature gradient causes dew point at interface |

### Chemical / environmental interfaces
| Failure mode | Typical cause |
|-------------|--------------|
| Galvanic corrosion | Dissimilar metals in electrolytic environment |
| Seal degradation | Material incompatibility with fluid media |
| Surface finish attack | Wrong coating for environment (salt, humidity, UV) |

---

## Tolerance Stack-Up at Interfaces

When two components interface mechanically, their dimensional tolerances combine.
The worst-case gap or interference is:

```
Worst-case gap     = nominal gap + sum of all tolerance contributions (+ direction)
Worst-case overlap = nominal gap − sum of all tolerance contributions (− direction)
```

**Check for:**
- Minimum clearance at worst-case (prevents binding / assembly interference)
- Maximum clearance at worst-case (prevents slop / rattling / loss of function)
- Special Characteristics on dimensions that directly control an interface

When process capability data is available, use statistical tolerance stack-up (RSS method) instead of worst-case arithmetic. Statistical analysis reflects real production variation and avoids over-constraining tolerances.

Document the tolerance stack-up analysis in Step 1 (Planning) and reference it in Step 4
when assigning failure modes to interface dimensions.

---

## Interface Validation

Critical interface failure modes must be validated — documentation alone is not sufficient.

| Validation method | When to use |
|-------------------|-------------|
| FEA / simulation | Mechanical stress, thermal, fluid — early in design phase |
| Bench test | Single interface, controlled conditions — pre-prototype |
| DVP system test | Full interface under production-representative conditions |
| HALT / HASS | Accelerated stress to find hidden interface weaknesses |

Link each critical interface failure mode to a DVP test entry. If no test exists, this is an open risk that must be documented with a management acceptance or an action to add the test.

---

## Interface Matrix → DFMEA Connection

| Interface matrix output | DFMEA field |
|------------------------|------------|
| Element pair with interaction type | Structure Analysis — component and interface level |
| Interface function statement | Function Analysis (Step 3) |
| Failure mode at interface | Failure Mode (Step 4) |
| System consequence of interface failure | Failure Effect (Step 4) |
| Design control that ensures interface performance | Detection control (Step 5) |
| DVP test for interface behaviour | Detection control → DVP entry (Step 6) |

---

## Checklist — Interface Matrix Complete?

- [ ] Boundary diagram drawn — inside and outside scope are clear
- [ ] All external elements identified (adjacent components, environment, user, process, maintenance)
- [ ] Interface type identified for every element pair that interacts
- [ ] Multiple interaction types listed explicitly where applicable (not collapsed)
- [ ] All interface arrows include direction and operating range
- [ ] Misuse and abuse scenarios included in user interface analysis
- [ ] At least one failure mode candidate for every interface cell with an interaction type
- [ ] All interfaces have at least one validated failure mode (no silent/empty interactions)
- [ ] Interfaces prioritised by severity and likelihood
- [ ] Tolerance stack-up analysed for all critical mechanical interfaces (statistical method if Cpk data available)
- [ ] Critical interfaces validated by analysis or test (DVP entry exists)
- [ ] Interface failure modes transferred to DFMEA Step 4
- [ ] DVP entries exist for all Detection controls at interfaces
