# Design Intent Interpretation Guide

When presenting schematic or PCB analysis results, check the `design_intent`
object in the analysis JSON to understand the design context and calibrate
your review accordingly.

## Reading Auto-Detected Intent

The `design_intent` object contains:

- `product_class`: "prototype" or "production"
- `ipc_class`: 1, 2, or 3
- `target_market`: "hobby", "consumer", "industrial", "medical", "automotive", "aerospace"
- `confidence`: 0.0-1.0 (how confident the auto-detection is)
- `detection_signals`: list of strings explaining what was detected
- `source`: per-field dict showing where each value came from ("config", "pcb_fab_notes", "schematic_title", "auto")

**When confidence < 0.5**, ask the user to confirm before applying professional-grade
criteria:

> "Based on [detection_signals], this appears to be a [target_market] [product_class]
> design. Should I apply [target_market]-grade review criteria, or is this a prototype /
> hobby project?"

**When confidence >= 0.5**, apply the detected intent silently but mention it in your
review summary: "Reviewing as a [target_market] [product_class] design (IPC Class [N])."

## LLM Refinement Signals

Beyond what the heuristics detect, look for these contextual patterns when reviewing
analysis output. If you spot them, adjust your review priorities accordingly -- you do
not need to re-run the analyzers.

### Application domain indicators
- Silkscreen text: "MEDICAL DEVICE", "FOR AUTOMOTIVE USE", "MIL-SPEC", "CLASS III"
- Regulatory markings: CE, FCC, UL, CSA logos or text references
- Safety agency file numbers in title blocks or fab notes

### Component-level indicators
- AEC-Q100/Q200 prefixes in MPNs -> automotive
- MIL-PRF, MIL-STD, QPL references -> aerospace/defense
- All components from same temp grade (-40 to +85 or wider) -> production-grade
- Conformal coating callouts -> harsh environment
- Hi-rel screening levels (Class B, Class S) -> space-grade

### Design pattern indicators
- Redundant power paths, OR-ing diodes -> high-reliability
- Voting circuits (2-of-3, TMR) -> safety-critical
- Watchdog timers with external reset -> production embedded
- Isolation barriers (optocouplers, isolated DC-DC) -> medical or industrial
- Board revision detection circuitry (GPIO strapping, ADC divider) -> production
- All MPNs populated, consistent manufacturer choices -> BOM-locked production

### BOM maturity indicators
- Every component has an MPN field -> production-ready
- Multiple components from same manufacturer family -> intentional sourcing
- Second-source alternates listed -> supply-chain-aware production
- Lifecycle status fields populated -> active management

## Market-Specific Review Priorities

Adjust what you emphasize based on `target_market`:

### hobby
- Focus on: basic correctness, learning opportunities, cost optimization
- De-emphasize: DFM details, documentation completeness, test coverage
- Tone: educational, suggest improvements as learning points

### consumer
- Focus on: cost optimization, ESD on external I/O, package consolidation, EMC
- Flag: missing ESD protection on user-accessible connectors
- De-emphasize: test point coverage, fab notes completeness

### industrial
- Focus on: temperature range adequacy, long-lifetime components, test coverage, EMC
- Flag: electrolytic caps in designs with >10yr expected lifetime
- Flag: components with commercial temp range (-10 to +70) in industrial application
- Require: test point coverage >= 90%

### medical
- Focus on: safety components, isolation barriers, IPC Class 3 DFM, redundancy
- Flag: missing isolation between patient-connected and mains-connected sections
- Flag: single points of failure in safety-critical paths
- Require: test point coverage >= 95%, all safety components identified
- Recommend: formal FMEA if not referenced

### automotive
- Focus on: AEC-Q qualification, wide temp range (-40 to +125), vibration-sensitive footprints, EMC
- Flag: non-AEC-Q components in critical paths
- Flag: stress-sensitive MLCC placement near board edges or flex points
- Require: test point coverage >= 95%

### aerospace
- Focus on: IPC Class 3 DFM, derating (50% voltage, 60% power), full traceability
- Flag: any single-source components without documented alternatives
- Flag: components without radiation tolerance data (if applicable)
- Require: test point coverage >= 98%, full lifecycle documentation

## Severity Adjustment Table

Adjust finding severity based on `product_class` and `target_market`:

| Finding | prototype/hobby | production/consumer | production/industrial+ |
|---------|----------------|--------------------|-----------------------|
| Missing MPN | info | medium | high |
| No test points | info | medium | high |
| Missing fab notes | info | medium | high |
| Mixed passive sizes | -- | info | medium |
| Single-source IC | -- | info | medium |
| No ESD on external I/O | medium | high | critical |
| No hardware version detect | -- | info | medium |
| Electrolytic in long-life design | -- | info | high |
| Commercial temp in industrial | -- | -- | high |
| Missing isolation (medical) | -- | -- | critical |

"--" means suppress or skip this finding entirely for this context.

## User Confirmation Prompt

When the auto-detected intent changes the review substantially (e.g., from hobby
defaults to medical Class 3), confirm with the user before the first detailed
analysis presentation. After confirmation, apply consistently for the rest of the
session without re-asking.
