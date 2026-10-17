# Tracing Net Connectivity in Raw `.kicad_sch` Files

KiCad schematics don't store explicit netlists — connectivity is implicit via coordinate matching. To verify a connection between two pins:

## CRITICAL: Y-axis inversion

**This is the single most common source of errors when tracing nets programmatically.** KiCad symbol library coordinates use math convention (Y-up), but schematic placement coordinates use screen convention (Y-down). You MUST subtract pin Y from symbol Y:

```
absolute = (symbol_X + pin_X, symbol_Y - pin_Y)
```

**Getting this wrong inverts the entire pin map** — pin 1 appears where pin N should be, and vice versa. Every "missing connection" or "wrong pin" finding that comes from coordinate math should be double-checked for this error. If a script reports that a pin is unconnected but the user says the schematic is correct, the Y-axis transform is almost certainly wrong.

## Step 1: Find pin positions in the symbol library definition

Each symbol has pins defined with relative offsets in the `lib_symbols` section:
```
(symbol "BSS84_1_1"
  (pin input line (at -5.08 0 0) ... (number "1"))      ; Gate
  (pin passive line (at 2.54 5.08 270) ... (number "3")) ; Drain
  (pin passive line (at 2.54 -5.08 90) ... (number "2")) ; Source
)
```

## Step 2: Calculate absolute pin positions

Apply the symbol's placement transform: `(at X Y ANGLE)`.

**No rotation (0 deg):**
- Pin at relative (px, py) -> absolute **(X + px, Y - py)**
- The Y subtraction is mandatory — symbol pin coordinates use math convention (up = positive Y), while schematic coordinates use screen convention (down = positive Y).

**With rotation:** Apply rotation matrix to pin offset BEFORE the Y inversion, then add to symbol position.
- 90 deg CW: (px, py) -> (py, -px) -> absolute (X + py, Y - (-px)) = (X + py, Y + px)
- 180 deg: (px, py) -> (-px, -py) -> absolute (X + (-px), Y - (-py)) = (X - px, Y + py)
- 270 deg CW: (px, py) -> (-py, px) -> absolute (X + (-py), Y - px) = (X - py, Y - px)

Example: Symbol at (161.29, 176.53), pin at relative (-5.08, 0), no rotation:
- Absolute: (161.29 + (-5.08), 176.53 - 0) = (156.21, 176.53)

Example: Resistor at (152.4, 176.53) rotated 90 deg, pin 1 at relative (0, 3.81):
- Rotated offset: (3.81, 0) -> absolute: (152.4 + 3.81, 176.53 - 0) = (156.21, 176.53)
- Same point as the gate pin above -> directly connected!

## Important: Multi-sided IC symbols have pins on different sides at the same Y-coordinate

Large IC symbols (e.g., ESP32 modules) have pins on the left **and** right sides. Two different pins can share the same Y-coordinate but have very different X-coordinates. A `no_connect` or wire at `(91.44, 77.47)` is NOT the same pin as a wire endpoint at `(60.96, 77.47)` — they are on opposite sides of the symbol.

**Always verify BOTH X and Y** when matching coordinates. Use exact floating-point comparison — KiCad stores coordinates with nanometer precision internally, and properly connected elements share the exact same coordinate values. If you see any difference (even 0.001mm), the coordinates are NOT the same point; they indicate a wiring error or coordinate transform bug. To determine which side a pin exits from:
1. Find the pin's relative offset in the `lib_symbols` definition — negative X = left side, positive X = right side
2. Apply the symbol's placement transform to get the absolute position
3. Match against wires/labels/no_connects using the **exact** (X, Y) pair

Do not assume a pin exits on a particular side based on the pin name or number alone.

## Step 3: Trace wires from pin positions

Search for `(wire (pts (xy X1 Y1) (xy X2 Y2)))` where one endpoint matches the pin position. Follow the wire chain endpoint-to-endpoint.

**KiCad 9 wire format note:** The `(wire` keyword, `(pts` keyword, and coordinate data may be on separate lines:
```
(wire
    (pts
        (xy 41.91 77.47) (xy 60.96 77.47)
    )
```
When extracting wires programmatically, search up to 4-5 lines ahead from `(wire` to find the `(xy ...)` coordinates.

## Step 4: Identify net names at wire endpoints

Look for:
- **Power symbols**: `(lib_id "power:GND")` or `(lib_id "power:+BATT")` placed at a wire endpoint — the symbol's Value property is the net name
- **Labels**: `(label "NET_NAME" (at X Y ...))` at a wire endpoint
- **Global labels**: `(global_label "NET_NAME" (at X Y ...))` for cross-sheet nets
- **Junctions**: `(junction (at X Y))` marks where crossing wires connect
- **Other component pins**: Another symbol's pin at the same coordinate

**Global label parsing note (KiCad 9):** The `(at ...)` is NOT on the line immediately after `(global_label "...")`. There is a `(shape ...)` line in between:
```
(global_label "EN_5V"
    (shape input)
    (at 43.18 128.27 180)
```
When extracting labels, search 2-3 lines ahead for the `(at ...)` coordinates, not just the next line.

**Labels connect via wires, not just at pin endpoints.** A global label is typically placed at the far end of a short wire stub extending from the pin. To find which label connects to which pin, you must trace the wire chain from the pin endpoint to the label position — checking only the exact pin coordinate will miss most connections.

## Step 5: Verify with junctions

If a wire passes through a point where another wire starts, they only connect if there's a `(junction ...)` at that point, OR if the wire endpoint exactly matches.

## Common False Positive Patterns

### Reference designator reuse
When a component is removed from a schematic (e.g., R13 was a GPIO pullup), its reference designator may be reused for a completely different component (e.g., R13 becomes a gate pulldown for a FET). Do not assume a reference designator has the same function across schematic revisions. Always check what the component actually connects to in the current schematic.

### Connector naming conventions
Not all "programming" connectors are JTAG. A 2x3 header (J2) with TX, RX, GND, 3V3, EN, and BOOT pins is a **serial programming header** (UART), not a JTAG header. JTAG requires TCK, TMS, TDI, TDO signals. Check the actual pin assignments before labeling a connector.

## Multi-Unit Symbols

Components like LM324 (4 opamps), CD4066 (4 switches), or STM32 (multi-bank pin assignments) contain multiple units in one package. Each unit is a separate `_U_1` / `_U_2` / etc. sub-symbol in the `lib_symbols` section. When tracing nets:

1. **Identify which unit is placed** — the placed symbol's `lib_id` suffix (e.g., `LM324_1_1` = unit 1) tells you which sub-symbol provides the pin offsets
2. **Each unit has its own pin set** — unit 1 of an LM324 has pins 1/2/3 (IN+/IN-/OUT), unit 2 has pins 5/6/7, etc. Power pins (VCC/GND) are typically in a shared sub-symbol `_0_1`
3. **Power pins may not be placed** — the `_0_1` sub-symbol with VCC/GND is often placed on only one instance (or a dedicated power sheet). Don't flag missing power connections on other units — check if any unit of the same component has them connected
4. **Reference designator is shared** — all units share the same reference (e.g., U1A, U1B, U1C, U1D are all U1). The analyzer reports them as separate symbol instances with the same `reference` field

To find all units of a component: search for placed symbols where the `lib_id` base name matches (ignoring the `_U_V` suffix) and the `reference` property is the same.

## Hierarchical buses

Bus connectivity (GH #25) is resolved by a dedicated per-sheet bus graph,
separate from the point-to-point tracing above.

- **Expansion.** Vectors (`D[0..7]` -> D0..D7) and groups (`{TX RX}` -> TX,
  RX) expand to an ordered member list; group members may themselves be
  project bus aliases, expanded recursively. `~{...}`/`_{...}`/`^{...}`
  markup around a bus distributes over each member; markup around a
  non-bus name (`~{OE}`) is not a bus.
- **Member attachment.** A member net joins its bus via an unlabelled
  bus-entry tap, or a same-sheet member label matching the bus's own
  member naming.
- **Sheet pins.** A parent bus reaching a child sheet's pin maps onto the
  child's hierarchical-label bus positionally, per instance — never by
  matching bare bus names across instances.
- **Hier/local join.** A genuine (non-sheet-pin) hierarchical label joins
  same-name local labels on its own sheet into one net; a sheet-pin label
  does not — its bare name belongs to the child and repeats per instance.
- **Naming.** A resolved member net is named from the parent (lowest sheet) label.
- **Qualified keys.** Bare-name collisions across sheet scopes use the
  `/<sheet>/<name>` key (KH-359), same as any other net.
- **Unresolved.** `bus_topology.unresolved` (`[{reason, name}]`) lists
  every bus construct the resolver could not confidently resolve — those
  connections are not asserted. `reason` is one of a fixed snake_case
  vocabulary (`name` carries the associated label/alias/sheet-pin name, or
  for `ambiguous_bus_width` the ambiguous width as a string; identical
  `{reason, name}` pairs are deduplicated within the bus-graph resolution
  notes; port-matching notes may repeat for genuinely distinct occurrences):
  - `entry_both_ends_on_bus` — a bus-entry tap lands on a bus wire at
    both ends (neither end is the wire side).
  - `entry_off_bus` — a bus-entry tap touches no bus wire at either end.
  - `label_not_on_bus_wire` — a bus-name label (local/hier/pin) isn't
    positioned on any bus wire segment.
  - `unlabeled_entry_tap` — a bus-entry tap's net carries no label at all.
  - `entry_tap_name_not_in_bus` — a bus-entry tap's net carries a label,
    but its name doesn't match any member of the tapped bus (distinct
    from `unlabeled_entry_tap`: the tap has a label, just not a member one).
  - `ambiguous_bus_width` — a cluster carries two different same-width
    bus-label expansions, so there's no single canonical member ordering.
  - `duplicate_hier_port` — two hierarchical-label ports share the same
    (namespace, name) key on one sheet (malformed sheet).
  - `no_hier_counterpart_for_pin` — a sheet-pin bus port has no matching
    hierarchical-label port on the child sheet.
  - `no_pin_counterpart_for_hier` — a hierarchical-label bus port has no
    matching sheet-pin port on the parent sheet.
  - `bus_width_mismatch` — a matched sheet-pin/hier-label port pair
    expand to different member counts.

## Complete Example

To verify Q4 (P-FET) gate connects to R13 -> GND:
1. Q4 at (161.29, 176.53), BSS84 Gate pin at (-5.08, 0) -> absolute **(156.21, 176.53)**
2. R13 at (152.4, 176.53) rotated 90 deg, Pin 1 at (0, 3.81) -> rotated (3.81, 0) -> absolute **(156.21, 176.53)** — same point, direct connection
3. R13 Pin 2 at (0, -3.81) -> rotated (-3.81, 0) -> absolute **(148.59, 176.53)**
4. Wire from (147.32, 176.53) to (148.59, 176.53) connects to R13 Pin 2
5. Junction at (147.32, 176.53), wire to (147.32, 177.8)
6. `power:GND` symbol at (147.32, 177.8) -> **GND net**
