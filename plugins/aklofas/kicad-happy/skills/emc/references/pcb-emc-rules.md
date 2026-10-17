# PCB Design Rules for EMC

Quantitative design rules used by the EMC analyzer. Each rule has a threshold, rationale, and authoritative source. All formulas and values verified against external references (April 2026).

## Ground Plane Integrity

### GP-001: Signal crossing ground plane void
- **Severity:** CRITICAL (high-speed) or HIGH (general)
- **Threshold:** Reference plane coverage <95% for any signal net
- **Rationale:** Return current must detour around the gap, creating a large loop antenna. Even "slow" signals have fast edge rates (SPI at 10 MHz has ~10 ns edges = 35 MHz bandwidth).
- **Source:** Hubing, T.H. "Common PCB Layout Mistakes that Cause EMC Compliance Failures." AltiumLive 2022 Keynote. Identified as the #1 PCB layout cause of EMC failures.
- **Fix:** Route signal around the gap, or fill the void. If a split is intentional, bridge it with a capacitor.
- **Touch pad exception:** Nets belonging to capacitive-touch pads (identified from CP-003 findings in the PCB analyzer) are reported at INFO severity with `is_touch_net: true`. Pour clearance under a touch pad is intentional for capacitive coupling; the recommendation is to preserve the void rather than fill it.

### GP-002: No ground plane zones
- **Severity:** CRITICAL
- **Threshold:** Board has ≥4 copper layers but no ground zone
- **Source:** Ott, H.W. *EMC Engineering*, Ch. 16 — "A ground plane is the single most important factor in achieving electromagnetic compatibility."

### GP-003: Fragmented ground plane
- **Severity:** HIGH
- **Threshold:** Ground zone has >3 disconnected islands
- **Rationale:** Isolated copper islands create slot antennas and force return currents through longer paths.

### GP-004: Low ground plane fill ratio
- **Severity:** MEDIUM
- **Threshold:** Ground zone fill ratio <60%

### GP-005: Multiple ground domains
- **Severity:** MEDIUM
- **Threshold:** More than one ground domain detected
- **Rationale:** Multiple ground domains require careful single-point connection to avoid ground loops. Unintentional splits create return current detours and loop antennas.
- **Fix:** Verify domains connect at a single intentional point (e.g., near the ADC for analog/digital split). Ensure no signal traces cross the domain boundary.

## Decoupling

### DC-001: Decoupling cap distance
- **Severity:** HIGH (>8mm), MEDIUM (>5mm)
- **Threshold:** 5mm warning, 8mm critical
- **Rationale:** Connection inductance increases with trace length. For microstrip over ground, loop inductance is approximately 0.3–0.8 nH/mm (Bogatin Rule of Thumb #6: 50Ω FR4 ≈ 8.3 nH/inch ≈ 0.33 nH/mm). However, connection inductance is dominated by via transitions rather than plane distribution — see LearnEMC note below.
- **Source:** Bogatin, E. "Total Loop Inductance per Length in 50-Ohm Transmission Lines." EDN Rule of Thumb #6. Hubing, T.H. ["Estimating the Connection Inductance of Decoupling Capacitors."](https://learnemc.com/estimating-connection-inductance) LearnEMC — notes that via placement matters more than cap-to-IC distance when planes are used for distribution.
- **Note:** The common "~1 nH/mm" rule of thumb applies to wire loops, not microstrip. For traces over a solid ground plane, 0.3–0.8 nH/mm is more accurate.

### DC-002: Missing decoupling
- **Severity:** HIGH
- **Threshold:** IC (U/IC prefix) with no capacitor within 10mm
- **Source:** Every major IC manufacturer's application notes recommend decoupling on all power pins. TI SLUA383, Analog Devices MT-101.

### DC-003: Decoupling cap far from via
- **Severity:** MEDIUM
- **Threshold:** Decoupling cap pad >3mm from nearest via to power/ground plane
- **Rationale:** Connection inductance is dominated by via transitions rather than cap-to-IC distance. Long traces between cap pad and via add ~0.5–0.8 nH/mm, degrading high-frequency decoupling.
- **Source:** LearnEMC, "Estimating the Connection Inductance of Decoupling Capacitors."
- **Fix:** Minimize trace between cap pad and its via. Use short fat traces or co-planar via layout.

## I/O Interface Filtering

### IO-001: No EMC filtering near connector
- **Severity:** HIGH (external connectors like USB, Ethernet), LOW (internal headers)
- **Threshold:** No ferrite bead, CM choke, or ESD/TVS device within 25mm
- **Rationale:** Common-mode currents on cables dominate radiated emissions at 30–300 MHz. Even microamps of CM current can exceed emission limits (5 µA on a 1m cable at 100 MHz = 46.4 dBµV/m, exceeding FCC Class B by ~3 dB).
- **Source:** Ott, *EMC Engineering*, Ch. 19 — common-mode cable radiation is the dominant emission mechanism. The 25mm threshold is a heuristic for geometric proximity checking. TI ESD layout guides (SLVA680, SLVAEX9) recommend placement "as close to the connector as PCB design rules allow" but do not specify a numeric distance.

### IO-002: Insufficient ground pins on connector
- **Severity:** MEDIUM (high-speed: USB, HDMI, Ethernet, PCIe), LOW (general)
- **Threshold:** Ground pins < max(2, signal_pins / 4) for connectors with >2 signal pins
- **Rationale:** High-speed connectors need adequate ground pins for return current paths and cable shielding to maintain signal integrity and reduce emissions.
- **Fix:** Add ground pins or use a connector variant with integrated shielding.

## Switching Regulator EMC

### SW-001: Harmonic overlap with emission bands
- **Severity:** HIGH (low-order harmonics in band), MEDIUM (many harmonics), INFO (high-order only)
- **Threshold:** Any switching frequency harmonic falling in 30–960 MHz test range
- **Rationale:** SMPS harmonics in the 30–300 MHz range are the #1 cause of radiated emissions failures. The harmonic amplitude envelope follows a trapezoidal spectrum:
  - Flat to f₁ = 1/(πτ) where τ = pulse width
  - −20 dB/decade from f₁ to f₂
  - f₂ = 1/(πt_r) where t_r = rise time
  - −40 dB/decade above f₂
- **Source:** Paul, C.R. *Introduction to EMC*, Ch. 3, §3.2 — trapezoidal waveform spectral envelope derivation.
- **Fix:** Minimize hot loop area. Consider spread-spectrum clocking if the regulator supports it.

### SW-002: Large switching node copper area
- **Severity:** HIGH (>100 mm²), MEDIUM (25–100 mm²)
- **Threshold:** Total copper area on SW/PH/LX net >25 mm² (zones + traces combined)
- **Rationale:** Large copper on the switching node acts as an antenna for switching noise. Only minimal copper should connect IC pin to inductor pad.
- **Source:** TI SLVA477, "Layout Tips for Switching Regulators."
- **Fix:** Remove unnecessary zones or copper pours on SW node. Use minimal-area traces from IC to inductor only.

### SW-003: Large input capacitor hot loop
- **Severity:** HIGH (>100 mm²), MEDIUM (25–100 mm²)
- **Threshold:** Triangle area (input cap → IC → inductor) >25 mm²
- **Rationale:** Hot loops radiate switching noise proportional to loop area × current × frequency. The input capacitor loop is the dominant emission source in most switching regulators.
- **Source:** Paul, *Introduction to EMC*, Ch. 10; Ridley, *Power Supply Design Vol. 2*.
- **Fix:** Place input cap, IC, and inductor in a tight triangle. Minimize trace length between them.

## Clock Routing

### CK-001: Clock on outer layer
- **Severity:** MEDIUM
- **Threshold:** >50% of clock routing on F.Cu/B.Cu when inner layers are available
- **Rationale:** Outer-layer microstrip radiates more than inner-layer stripline. Stripline is shielded by reference planes above and below.
- **Source:** Armstrong, K. "PCB Design Techniques for Lowest-Cost EMC Compliance." Part 5 — routing discipline and stripline preference for clocks.

### CK-002: Long clock trace
- **Severity:** MEDIUM
- **Threshold:** Clock net >100mm
- **Source:** Johnson, H. *High-Speed Digital Design*, Ch. 1 — longer traces are more effective antennas.

### CK-003: Clock routed near connector
- **Severity:** MEDIUM
- **Threshold:** Clock net trace segment within 10mm of an external connector
- **Rationale:** Clock harmonics can couple to attached cables via proximity, increasing radiated emissions. Clock traces near connector apertures create efficient radiators.
- **Fix:** Route clock traces away from connectors. Use ground guard traces if routing is constrained.

## Via Stitching

### VS-001: Insufficient via stitching
- **Severity:** MEDIUM
- **Threshold:** Average via spacing > 2× required λ/20 spacing
- **Rationale:** Ground via stitching prevents parallel-plate waveguide modes from propagating between planes. λ/20 is the conservative recommendation for high-isolation applications.
- **Source:** [Altium — "Everything You Need to Know About Stitching Vias"](https://resources.altium.com/p/everything-you-need-know-about-stitching-vias) — λ/20 for >120 dB isolation, λ/10 for general use.

### Via stitching spacing requirements (FR4, εr = 4.4)

| Frequency | λ (in FR4) | λ/20 spacing |
|-----------|-----------|--------------|
| 100 MHz   | 1430 mm   | 71 mm        |
| 500 MHz   | 286 mm    | 14 mm        |
| 1 GHz     | 143 mm    | 7.1 mm       |
| 2.4 GHz   | 60 mm     | 3.0 mm       |

## Stackup

### SU-001: Adjacent signal layers
- **Severity:** HIGH
- **Threshold:** Two signal-type layers adjacent without ground/power plane between them
- **Source:** Ott, H.W. ["PCB Stack-Up."](http://www.hottconsultants.com/techtips/pcb-stack-up-2.html) hottconsultants.com — recommended 4-layer stackup is SIG/GND/PWR/SIG with tight coupling (0.1–0.2mm) between signal and adjacent reference plane.

### SU-002: Signal layer far from reference
- **Severity:** LOW
- **Threshold:** Signal layer >0.3mm from nearest reference plane
- **Source:** Ott, PCB Stack-Up series — tight coupling reduces loop area. Every halving of signal-to-reference spacing reduces emissions by ~6 dB (from E ∝ loop area ∝ dielectric height).

### SU-003: Power/ground plane pair spacing
- **Severity:** LOW
- **Threshold:** Power/ground dielectric >0.2mm
- **Rationale:** Thin dielectric between power/ground pairs provides interplane capacitance for high-frequency decoupling.
- **Value:** C = ε₀ × εr / d. For 0.15mm FR4 (εr=4.4): **~26 pF/cm²** (~168 pF/in²).
- **Source:** [LearnEMC — "Decoupling for Boards with Closely-Spaced Power Planes"](https://learnemc.com/decoupling-for-boards-with-closely-spaces-power-planes). Armstrong, K. PCB EMC Design Part 4 — recommends thin prepreg between power/ground pairs.

## Emission Estimates

### EE-001: Board cavity resonance
- **Severity:** INFO
- **Formula:** f_mn = (c / 2√εr) × √((m/L)² + (n/W)²)
- **Source:** Standard TM_mn cavity resonance for rectangular parallel-plate resonator with open (magnetic) sidewalls. Pozar, D.M. *Microwave Engineering*; also Paul, *Introduction to EMC*, Ch. 10.
- **Verified:** 100mm × 80mm FR4 board → f₁₀ = 714.5 MHz ✓

### EE-002: Switching harmonic envelope
- **Severity:** INFO
- **Formula:** Trapezoidal spectrum with corners at f₁ = 1/(πτ) and f₂ = 1/(πt_r)
- **Source:** Paul, *Introduction to EMC*, Ch. 3, §3.2.

## Key Physics (Verified)

All formulas below verified by derivation from first principles and cross-checked against LearnEMC.com calculators (April 2026).

### Differential-mode loop radiation

```
E = K × f² × A × I / r
  K = 1.316×10⁻¹⁴ (free space)
  K = 2.632×10⁻¹⁴ (with ground plane image, ×2)
```

Derivation: E = η₀β²IA/(4πr), where η₀ = 377Ω, β = 2πf/c. Substituting and simplifying yields K = η₀π/c² = 1.3167×10⁻¹⁴.

Source: Ott, *EMC Engineering*, Ch. 6; Paul, *Introduction to EMC*, Ch. 10; [LearnEMC DM Radiation Calculator](https://learnemc.com/ext/calculators/mremc/dmode.php).

### Common-mode cable radiation

```
E = µ₀ × f × L × I_CM / r = 1.257×10⁻⁶ × f × L × I_CM / r
```

The coefficient 1.257×10⁻⁶ = µ₀ = 4π×10⁻⁷. This is the monopole-above-ground form (includes ×2 image factor; base short-dipole coefficient is 6.283×10⁻⁷).

Source: Ott, *EMC Engineering*, Ch. 6; Paul, *Introduction to EMC*, Ch. 10; [LearnEMC CM EMI Calculator](https://learnemc.com/ext/calculators/mremc/cmode.php).

### Bandwidth and knee frequency

```
BW_3dB = 0.35 / t_r         (single-pole RC, exact: ln(9)/2π ≈ 0.3497)
f_knee = 0.5 / t_r          (Johnson convention — practical EMC boundary)
f₂     = 1/(π × t_r)        (Paul convention — trapezoidal envelope corner)
```

The two "knee" conventions serve different purposes. Johnson's 0.5/t_r is more conservative (higher frequency) and is the standard in EMC/SI practice. Paul's 1/(πt_r) ≈ 0.318/t_r is the mathematical envelope corner.

Source: Johnson, H. *High-Speed Digital Design*, Ch. 1 (0.35/t_r and 0.5/t_r). Paul, *Introduction to EMC*, Ch. 3 (1/πt_r).

### Scaling rules (from E ∝ f²AI/r)

| Change | Effect | dB |
|--------|--------|-----|
| Double loop area (A) | ×2 | +6 dB |
| Double frequency (f) | ×4 (f²) | +12 dB |
| Double current (I) | ×2 | +6 dB |
| Double distance (r) | ×0.5 | −6 dB |

### Via inductance

```
L = 0.2 × h × [ln(4h/d) + 1] nH    (h, d in mm)
L = 5.08 × h × [ln(4h/d) + 1] nH   (h, d in inches)
```

Source: Goldfarb, E. & Pucha, R. "Modeling Via Grounds in Microstrip." IEEE Microwave and Guided Wave Letters, Vol. 1, No. 6, June 1991. Also Johnson, H. *High-Speed Signal Propagation* (2003); Bogatin, E. *Signal and Power Integrity — Simplified* (2010).

## Differential Pair EMC

### DP-001: Intra-pair skew
- **Severity:** HIGH (exceeds protocol limit), MEDIUM (>50% of limit)
- **Threshold:** Protocol-specific — USB HS: 25 ps, USB SS: 5 ps, Ethernet: 50 ps, HDMI: 20 ps, PCIe: 5 ps
- **Formula:** `skew_ps = ΔL_mm × propagation_delay_ps_per_mm(εr)`. For FR4 microstrip (εr=4.4): ~5.5 ps/mm.
- **Source:** USB 2.0 spec §7.1.2; IEEE 802.3 §40.6.1; PCI Express Base Spec §4.3.3; HDMI 2.1 spec §4.2.1.1.

### DP-002: Skew-induced CM radiation
- **Severity:** HIGH (estimated emission exceeds limit), MEDIUM (within 6 dB of limit)
- **Formula:** `V_CM = V_diff × Δt / (2 × T_rise)`. CM current: `I_CM = V_CM / Z_cable`. Radiation from `cm_radiation_dbuv_m()`.
- **Source:** Ott, *EMC Engineering*, Ch. 19; Johnson, *High-Speed Signal Propagation*, Ch. 11; Altium, "Guide to Mode Conversion."

### DP-003: Reference plane change under diff pair
- **Severity:** HIGH
- **Threshold:** Any layer transition on a differential pair net
- **Rationale:** Each layer transition forces the return current to change planes. Without a nearby stitching via or decoupling cap, the return current takes a long path, converting DM to CM.
- **Source:** Armstrong, "PCB Design Techniques for Lowest-Cost EMC Compliance," Part 5.

### DP-004: Diff pair on outer layer
- **Severity:** MEDIUM
- **Threshold:** >50% of diff pair routing on F.Cu/B.Cu when inner layers available
- **Rationale:** Same as CK-001. Outer-layer microstrip radiates more than inner-layer stripline.

## Board Edge Analysis

### BE-001: Signal trace near board edge
- **Severity:** HIGH (clock/high-speed), MEDIUM (general signal)
- **Threshold:** Signal trace on outer layer within 1× dielectric height of board edge
- **Rationale:** Traces near the edge lack full ground plane reference. The discontinuity creates a slot antenna effect.
- **Source:** Hubing, "Common PCB Layout Mistakes," AltiumLive 2022; In Compliance Magazine, "Avoid Critical Signals in Edges of the PCB."

### BE-002: Ground pour ring coverage
- **Severity:** MEDIUM
- **Threshold:** <90% of board perimeter has ground zone within 2mm
- **Rationale:** A continuous ground guard ring around the board perimeter reduces edge radiation from the parallel-plate waveguide formed by power/ground planes.
- **Source:** Signal Integrity Journal, "Controlling Electromagnetic Emissions from PCB Edges in Backplanes."

### BE-003: Connector area via stitching
- **Severity:** HIGH (external connectors), MEDIUM (general)
- **Threshold:** Via spacing in 10mm radius exceeds 2× λ/20 for the connector's highest-frequency signal
- **Source:** [Altium — "Everything You Need to Know About Stitching Vias"](https://resources.altium.com/p/everything-you-need-know-about-stitching-vias); Ott, *EMC Engineering*, Ch. 16.

## PDN Impedance

### PD-001: PDN anti-resonance exceeds target
- **Severity:** HIGH when an anti-resonance peak exceeding the target impedance occurs at or below 200 MHz (`PDN_RELEVANT_FMAX_HZ`); INFO when all exceeding peaks lie above that frequency band (listed under `out_of_band_peaks`)
- **Threshold:** Parallel capacitor network impedance exceeds Z_target = V × 5% / (0.5 × I_transient) at any anti-resonance peak, where I_transient defaults to 2× the regulator's estimated output current (capped at 5 A), or 0.5 A if regulator current is unavailable. When set in `.kicad-happy.json`, `project.pdn_transient_current_a` overrides the default. Capacitances are reported in engineering units (µF, nF, pF).
- **Rationale:** Anti-resonance peaks between capacitors of different values create impedance spikes that can cause voltage ripple exceeding spec.
- **Source:** Bogatin, *Signal and Power Integrity — Simplified*, Ch. 10.

### PD-002: PDN anti-resonances within target
- **Severity:** INFO
- **Threshold:** Anti-resonance peaks exist but all within target impedance
- **Source:** Same as PD-001.

### PD-003: Distributed rail impedance at IC load point
- **Severity:** HIGH
- **Threshold:** Z(f) at worst-case IC exceeds Z_target, accounting for trace R+L between regulator and IC
- **Rationale:** Target impedance at the regulator output does not guarantee impedance at the IC power pins. Trace resistance and inductance create a series impedance that elevates the PDN impedance seen by ICs far from the regulator. Local decoupling caps partially mitigate but may introduce new anti-resonances.
- **Formula:** Z_at_IC(f) = Z_local(f) || (Z_reg(f) + R_trace + j×2πf×L_trace)
- **Source:** Bogatin, *Signal and Power Integrity — Simplified*, Ch. 10-12; Smith, "Decoupling Capacitor Calculations for ASICs."

### PD-004: Cross-rail PDN coupling
- **Severity:** MEDIUM
- **Threshold:** Upstream rail impedance exceeds adjusted target at downstream switching frequency
- **Rationale:** A downstream switching regulator draws pulsed current from its input rail at its switching frequency. If the upstream PDN impedance is high at that frequency, it creates voltage ripple on the upstream rail that affects all other loads sharing that rail.
- **Formula:** I_in_transient = V_out × I_out / (V_in × η × D) at f_sw
- **Source:** Basso, *Switch-Mode Power Supplies* (McGraw-Hill); Ridley, *Power Supply Design Vol. 2*.

## Return Path Continuity

### RP-001: Missing stitching via at layer transition
- **Severity:** HIGH (differential pair or high-speed net), MEDIUM (all transitions unstitched), LOW (partial)
- **Threshold:** Signal via transitions layers without a ground stitching via within max(2 × dielectric_height, 1.0 mm)
- **Rationale:** When a signal changes layers, return current must also change planes. Without a nearby ground via, return current takes a long detour, creating a large loop antenna.
- **Source:** Ott, "PCB Stack-Up Part 6"; Sierra Circuits return path design guide.
- **Fix:** Add ground stitching via adjacent to each signal via. Use multiple ground vias for differential pairs.

## Crosstalk

### XT-001: Trace spacing violation (3H rule)
- **Severity:** HIGH (aggressor-victim pair: clock/switching near analog/ADC), MEDIUM (at least one aggressor), LOW (general)
- **Threshold:** Parallel trace coupling length ≥5mm with spacing < 3 × dielectric height on outer layers
- **Rationale:** 3× dielectric height spacing gives <3% near-end crosstalk. Closer spacing creates coupling that adds to emissions and can cause false signal transitions.
- **Source:** Bogatin, *Signal and Power Integrity*, Ch. 13; Johnson, *High-Speed Digital Design*, Ch. 5.
- **Fix:** Increase spacing to ≥3H or insert ground guard trace between aggressor and victim.

## EMI Filter Verification

### EF-001: Filter cutoff too close to switching frequency
- **Severity:** MEDIUM
- **Threshold:** f_sw / f_cutoff < 5
- **Rationale:** EMI input filters on switching regulators must provide adequate attenuation at the switching frequency. A ratio ≥5 between switching frequency and filter cutoff ensures sufficient margin for the -40 dB/decade rolloff.
- **Source:** Paul, *Introduction to EMC*, Ch. 9; Analog Devices, "Speed Up the Design of EMI Filters for SMPS."
- **Fix:** Increase filter inductance or capacitance to lower cutoff to ≤f_sw/5.

### EF-002: Filter cutoff verified (passing check)
- **Severity:** INFO
- **Threshold:** f_sw / f_cutoff ≥ 5
- **Rationale:** Informational confirmation that the EMI filter design meets the 5× cutoff ratio criterion for adequate attenuation.

## ESD Protection Path

### ES-001: ESD device far from connector
- **Severity:** MEDIUM
- **Threshold:** TVS/ESD protection device >15mm from protected connector
- **Rationale:** During 8kV IEC 61000-4-2 ESD strike (dI/dt = 37.5 GA/s), each nH of inductance in the path creates ~37.5V of overshoot. Trace inductance is ~0.5–0.8 nH/mm, so every extra mm degrades clamping performance.
- **Source:** TI SLVA680 "ESD Protection Layout Guide"; ST AN5686 "PCB Layout Tips for ESD Protection."
- **Fix:** Move TVS within 10mm of connector. Keep ESD current path as short as possible.

### ES-002: Insufficient ground vias near ESD device
- **Severity:** HIGH (no ground via within 3mm), LOW (single ground via)
- **Threshold:** <2 ground stitching vias within 3mm of TVS ground pad
- **Rationale:** TVS ground path inductance is the most critical parasitic in ESD protection. Two parallel vias halve the inductance (~0.5 nH → ~0.25 nH), improving clamping by ~9V at 37.5 GA/s.
- **Fix:** Add ≥2 ground vias directly adjacent to TVS ground pad. Use short, wide traces to ground plane.

## Thermal-EMC Interaction

### TH-001: MLCC DC bias derating
- **Severity:** MEDIUM
- **Threshold:** Effective capacitance <50% of nominal due to DC bias
- **Rationale:** Ceramic capacitors lose capacitance under DC bias. Severe derating (>50%) shifts the self-resonant frequency (SRF) and may leave gaps in decoupling coverage, affecting PDN impedance.
- **Source:** Murata "DC Bias Characteristics of MLCCs"; Analog Devices, "Temperature and Voltage Variation of Ceramic Capacitors."
- **Fix:** Use larger package (lower derating), higher voltage rating, or C0G/NP0 dielectric for critical decoupling.

### TH-002: Ferrite bead near heat source
- **Severity:** LOW
- **Threshold:** Ferrite bead within 10mm of a switching regulator
- **Rationale:** Ferrite permeability (µ) decreases significantly with temperature. If a regulator runs hot (>85°C), ferrite impedance may drop 30–50%, reducing filtering effectiveness.
- **Fix:** Verify ferrite's thermal rating. Consider relocating away from heat source or using higher-temperature-rated material.

## Shielding

### SH-001: Connector aperture slot resonance
- **Severity:** MEDIUM (resonance coincides with emission source), INFO (general)
- **Threshold:** Slot resonance frequency (f = c / 2L) within ±20% of a board emission source (crystal harmonics, switching harmonics)
- **Rationale:** A connector aperture acts as a resonant slot antenna. When slot resonance overlaps with on-board emission sources, the connector becomes an efficient radiator.
- **Source:** Ott, *EMC Engineering*, Ch. 6 — aperture theory and slot antenna radiation.
- **Fix:** Use shielded connector variants. Add absorber material inside enclosure near aperture.

## References

- Ott, H.W. *Electromagnetic Compatibility Engineering.* Wiley, 2009.
- Paul, C.R. *Introduction to Electromagnetic Compatibility.* 2nd ed., Wiley, 2006.
- Johnson, H.W. *High-Speed Digital Design: A Handbook of Black Magic.* Prentice Hall, 1993.
- Johnson, H.W. *High-Speed Signal Propagation: Advanced Black Magic.* Prentice Hall, 2003.
- Bogatin, E. *Signal and Power Integrity — Simplified.* 3rd ed., Prentice Hall, 2018.
- Bogatin, E. ["Rules of Thumb."](https://www.colorado.edu/faculty/bogatin/publications/rules-thumb) University of Colorado.
- Hubing, T.H. [LearnEMC.com](https://learnemc.com/) — EMC education, calculators, design guidelines.
- Armstrong, K. "PCB Design Techniques for Lowest-Cost EMC Compliance." 8-part series, Cherry Clough Consultants.
- Goldfarb, E. & Pucha, R. IEEE Microwave and Guided Wave Letters, Vol. 1, No. 6, 1991.
- [47 CFR Part 15](https://www.law.cornell.edu/cfr/text/47/part-15) — FCC regulations for unintentional radiators.
- USB 2.0 Specification, §7.1.2 — Signaling, differential driver requirements.
- IEEE 802.3 §40.6.1 — Ethernet PHY differential output requirements.
- PCI Express Base Specification, §4.3.3 — Differential pair skew requirements.
- HDMI 2.1 Specification, §4.2.1.1 — TMDS signaling requirements.
- [Cadence — "Differential Pair Length Matching Guidelines"](https://resources.cadence.com/)
- [Altium — "Guide to Mode Conversion, Its Causes, and Solutions"](https://resources.altium.com/)
- In Compliance Magazine — "Avoid Critical Signals in Edges of the PCB."
- Signal Integrity Journal — "Controlling Electromagnetic Emissions from PCB Edges in Backplanes."
