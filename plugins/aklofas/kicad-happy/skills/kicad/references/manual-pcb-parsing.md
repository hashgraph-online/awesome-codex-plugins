# Manual PCB Parsing (Script Fallback)

When `analyze_pcb.py` fails (unsupported format, newer KiCad version, corrupted file), fall back to direct file parsing. This is more expensive (reading raw S-expressions) but always works as long as the file is valid KiCad.

## Table of Contents

1. [When to Use Manual Parsing](#when-to-use-manual-parsing)
2. [Performance: Line-by-Line Parsing](#performance-line-by-line-parsing)
3. [Net Extraction](#net-extraction)
4. [Footprint Extraction](#footprint-extraction)
5. [Track and Via Extraction](#track-and-via-extraction)
6. [Zone Extraction](#zone-extraction)
7. [Board Outline](#board-outline)
8. [Connectivity Analysis](#connectivity-analysis)
9. [KiCad 5 Legacy Format](#kicad-5-legacy-format)
10. [Validation Methodology](#validation-methodology)

---

## When to Use Manual Parsing

Use manual parsing when:
- `analyze_pcb.py` crashes or returns unexpected results on a file you know is valid
- The PCB is from a KiCad version newer than the script supports
- You need to validate script output against raw file data
- You need to extract data the script doesn't provide (e.g., specific filled_polygon vertices)
- The file is partially corrupt but still readable

Always try the script first — it handles coordinate transforms, via classification, connectivity analysis, and 25+ analysis stages automatically.

---

## Performance: Line-by-Line Parsing

KiCad PCB files can be 20K-70K+ lines, with zones containing thousands of polygon vertices. **Never use full-content regex with `re.DOTALL` on the entire file** — it causes catastrophic backtracking on large files. Use line-by-line state-machine parsing instead for top-level extraction. `re.DOTALL` is acceptable on small, pre-extracted blocks (e.g., a single footprint or pad block) where the input size is bounded.

### Buffer Accumulation Pattern

For simple blocks (segments, vias):

```python
import re

with open(pcb_file) as f:
    lines = f.readlines()

segments = []
buf = None
for line in lines:
    if '\t(segment' in line:
        buf = line
    elif buf:
        buf += line
        if line.strip() == ')':
            m_s = re.search(r'\(start\s+([\d.-]+)\s+([\d.-]+)\)', buf)
            m_e = re.search(r'\(end\s+([\d.-]+)\s+([\d.-]+)\)', buf)
            m_w = re.search(r'\(width\s+([\d.]+)\)', buf)
            m_l = re.search(r'\(layer\s+"([^"]+)"\)', buf)
            # KiCad ≤9: (net 7), KiCad 10: (net "NetName")
            m_n = re.search(r'\(net\s+(\d+)\)', buf) or re.search(r'\(net\s+"([^"]+)"\)', buf)
            if all([m_s, m_e, m_w, m_l, m_n]):
                net_val = m_n.group(1)
                segments.append({
                    'sx': float(m_s.group(1)), 'sy': float(m_s.group(2)),
                    'ex': float(m_e.group(1)), 'ey': float(m_e.group(2)),
                    'w': float(m_w.group(1)), 'layer': m_l.group(1),
                    'net': int(net_val) if net_val.isdigit() else net_val
                })
            buf = None
```

### Depth-Tracked Parsing

For nested blocks (footprints, zones), track parenthesis depth:

```python
footprints = {}
current_fp = None
fp_text = []
depth = 0

for line in lines:
    if line.startswith('\t(footprint '):
        current_fp = True
        fp_text = [line]
        depth = line.count('(') - line.count(')')
    elif current_fp:
        fp_text.append(line)
        depth += line.count('(') - line.count(')')
        if depth <= 0:
            block = ''.join(fp_text)
            # Extract data from the bounded block (regex is safe here)
            m_ref = re.search(r'\(property\s+"Reference"\s+"([^"]+)"', block)
            m_at = re.search(r'\n\t\t\(at\s+([\d.-]+)\s+([\d.-]+)(?:\s+([\d.-]+))?\)', block)
            if m_ref and m_at:
                ref = m_ref.group(1)
                footprints[ref] = {
                    'x': float(m_at.group(1)),
                    'y': float(m_at.group(2)),
                    'angle': float(m_at.group(3)) if m_at.group(3) else 0,
                    'block': block
                }
            current_fp = None
```

---

## Net Extraction

**KiCad ≤9:** Net declarations are single-line entries near the top of the file:

```python
nets = {}
for line in lines:
    m = re.match(r'\s*\(net\s+(\d+)\s+"([^"]*)"\)', line)
    if m:
        nets[int(m.group(1))] = m.group(2)
```

Net 0 is always the unconnected net (empty name).

**KiCad 10:** No net declarations section. Nets are referenced by name string directly in pads, tracks, vias, and zones. Collect unique net names from those elements instead.

Power nets typically have names like `GND`, `+3V3`, `+5V`, `VBUS`.

---

## Footprint Extraction

After extracting footprint blocks with depth-tracking (see above), extract pads from each block:

```python
for ref, fp in footprints.items():
    # KiCad ≤9: (net 5 "+3V3"), KiCad 10: (net "+3V3")
    pads = re.findall(
        r'\(pad\s+"([^"]+)"\s+(\w+)\s+\w+\s+'
        r'\(at\s+([\d.-]+)\s+([\d.-]+).*?\)'
        r'\s+\(size\s+([\d.-]+)\s+([\d.-]+)\).*?'
        r'\(net\s+(?:(\d+)\s+)?"([^"]*)"',
        fp['block'], re.DOTALL)
    # pads: list of (pad_num, type, rel_x, rel_y, size_w, size_h, net_id_or_empty, net_name)
```

### Absolute Pad Positions

Pad coordinates are relative to footprint origin. Transform to board coordinates:

```python
import math

def pad_to_absolute(fp_x, fp_y, fp_angle_deg, pad_rx, pad_ry):
    rad = math.radians(-fp_angle_deg)  # KiCad: CW positive in layout
    abs_x = fp_x + pad_rx * math.cos(rad) - pad_ry * math.sin(rad)
    abs_y = fp_y + pad_rx * math.sin(rad) + pad_ry * math.cos(rad)
    return abs_x, abs_y
```

### Key Footprint Fields

| Field | Where | Purpose |
|-------|-------|---------|
| `(property "Reference" "U1")` | Footprint block | Component designator |
| `(property "Value" "STM32F407")` | Footprint block | Component value |
| `(at X Y ANGLE)` | 2nd-level child | Position and rotation |
| `(layer "F.Cu")` | 1st-level child | Board side (F.Cu = front, B.Cu = back) |
| `(attr smd)` | 1st-level child | SMD vs through-hole |
| `(path "/uuid")` | 1st-level child | Link to schematic symbol |
| `(sheetname "Power")` | 1st-level child | Source schematic sheet |
| `(pad ...)` | Nested children | Pads with net assignments |

### Courtyard Extraction

Courtyard shapes define the component's keep-out area:

```python
# From footprint block:
crtyd_lines = re.findall(
    r'\(fp_(?:line|rect)\s+\(start\s+([\d.-]+)\s+([\d.-]+)\)\s+'
    r'\(end\s+([\d.-]+)\s+([\d.-]+)\).*?'
    r'\(layer\s+"[FB]\.CrtYd"\)',
    fp['block'], re.DOTALL)
```

Build a bounding box from all courtyard primitives, then transform to absolute coordinates.

---

## Track and Via Extraction

### Tracks (Segments)

See the buffer accumulation pattern above. KiCad 7+ also has `(arc ...)` blocks with `(start)`, `(mid)`, `(end)` for curved tracks.

For arc length calculation:
```python
import math

def arc_length(sx, sy, mx, my, ex, ey):
    """Calculate arc length from start/mid/end points."""
    # Find circle center from 3 points
    ax, ay = sx - mx, sy - my
    bx, by = ex - mx, ey - my
    D = 2 * (ax * by - ay * bx)
    if abs(D) < 1e-10:
        return math.hypot(ex - sx, ey - sy)  # Degenerate: straight line
    ux = (by * (ax*ax + ay*ay) - ay * (bx*bx + by*by)) / D + mx
    uy = (ax * (bx*bx + by*by) - bx * (ax*ax + ay*ay)) / D + my
    radius = math.hypot(sx - ux, sy - uy)
    # Angle subtended
    a1 = math.atan2(sy - uy, sx - ux)
    a2 = math.atan2(ey - uy, ex - ux)
    angle = abs(a2 - a1)
    if angle > math.pi:
        angle = 2 * math.pi - angle
    return radius * angle
```

### Vias

```python
vias = []
buf = None
for line in lines:
    if '\t(via' in line and '(via' in line:
        buf = line
    elif buf:
        buf += line
        if line.strip() == ')':
            m_at = re.search(r'\(at\s+([\d.-]+)\s+([\d.-]+)\)', buf)
            m_sz = re.search(r'\(size\s+([\d.]+)\)', buf)
            m_dr = re.search(r'\(drill\s+([\d.]+)\)', buf)
            m_ly = re.search(r'\(layers\s+"([^"]+)"\s+"([^"]+)"\)', buf)
            # KiCad ≤9: (net 5) with numeric ID; KiCad 10: (net "NetName") with string
            m_n = re.search(r'\(net\s+(\d+)\)', buf)
            m_nn = re.search(r'\(net\s+"([^"]+)"\)', buf)
            via_type = 'through'
            if '(via blind' in buf: via_type = 'blind'
            elif '(via buried' in buf: via_type = 'buried'
            elif '(via micro' in buf: via_type = 'micro'
            if all([m_at, m_sz, m_dr]) and (m_n or m_nn):
                vias.append({
                    'x': float(m_at.group(1)), 'y': float(m_at.group(2)),
                    'size': float(m_sz.group(1)), 'drill': float(m_dr.group(1)),
                    'type': via_type,
                    'layers': (m_ly.group(1), m_ly.group(2)) if m_ly else ('F.Cu', 'B.Cu'),
                    'net': int(m_n.group(1)) if m_n else m_nn.group(1),
                    'free': '(free yes)' in buf
                })
            buf = None
```

### Annular Ring Check

```python
for via in vias:
    annular_ring = (via['size'] - via['drill']) / 2
    if annular_ring < 0.125:  # JLCPCB standard minimum
        print(f"Annular ring violation: {annular_ring:.3f}mm at ({via['x']}, {via['y']})")
```

---

## Zone Extraction

Zones are the trickiest part — they contain massive `filled_polygon` blocks. For most analyses, extract only the header:

```python
zones = []
in_zone = False
zone_info = {}
for line in lines:
    stripped = line.strip()
    if re.match(r'\(zone\s*$', stripped) or re.match(r'\(zone\s+\(', stripped):
        in_zone = True
        zone_info = {}
    elif in_zone:
        m = re.search(r'\(net\s+(\d+)\)', line)
        if m: zone_info['net'] = int(m.group(1))
        m = re.search(r'\(net_name\s+"([^"]*)"', line)
        if m: zone_info['net_name'] = m.group(1)
        m = re.search(r'\(layer\s+"([^"]+)"', line)
        if m: zone_info['layer'] = m.group(1)
        m = re.search(r'\(priority\s+(\d+)\)', line)
        if m: zone_info['priority'] = int(m.group(1))
        if '(keepout' in line:
            zone_info['is_keepout'] = True
        if '(polygon' in line or '(filled_polygon' in line:
            zones.append(zone_info)
            in_zone = False
```

### Zone Fill Polygon Extraction

Only extract filled polygon data when you actually need zone containment tests:

```python
def extract_zone_polygon(lines, zone_net, zone_layer):
    """Extract filled_polygon vertices for a specific zone."""
    in_target_zone = False
    in_filled_poly = False
    points = []
    depth = 0

    for line in lines:
        if '(zone' in line:
            in_target_zone = False
            # Check if this is our target zone
        if in_target_zone and '(filled_polygon' in line:
            if f'(layer "{zone_layer}")' in line:
                in_filled_poly = True
                depth = line.count('(') - line.count(')')
                continue
        if in_filled_poly:
            for m in re.finditer(r'\(xy\s+([\d.-]+)\s+([\d.-]+)\)', line):
                points.append((float(m.group(1)), float(m.group(2))))
            depth += line.count('(') - line.count(')')
            if depth <= 0:
                return points
    return points
```

---

## Board Outline

Extract graphical primitives on the `Edge.Cuts` layer:

```python
outline_segments = []
for line in lines:
    if 'Edge.Cuts' in line:
        # Check parent block for gr_line, gr_arc, gr_rect, gr_circle
        pass

# Simpler: use buffer accumulation for gr_line blocks
buf = None
for line in lines:
    if '(gr_line' in line or '(gr_arc' in line or '(gr_rect' in line:
        buf = line
    elif buf:
        buf += line
        if line.strip().endswith(')'):
            if 'Edge.Cuts' in buf:
                if '(gr_line' in buf:
                    m = re.search(r'\(start\s+([\d.-]+)\s+([\d.-]+)\).*?\(end\s+([\d.-]+)\s+([\d.-]+)\)', buf, re.DOTALL)
                    if m:
                        outline_segments.append({
                            'type': 'line',
                            'start': (float(m.group(1)), float(m.group(2))),
                            'end': (float(m.group(3)), float(m.group(4)))
                        })
            buf = None

# Bounding box from all outline segments
if outline_segments:
    all_x = [s['start'][0] for s in outline_segments] + [s['end'][0] for s in outline_segments]
    all_y = [s['start'][1] for s in outline_segments] + [s['end'][1] for s in outline_segments]
    width = max(all_x) - min(all_x)
    height = max(all_y) - min(all_y)
```

---

## Connectivity Analysis

### Unrouted Net Detection

Checking whether a net has *any* routing is insufficient — nets can be partially routed with breaks. A proper connectivity analysis builds a graph per net and checks if all pads are in a single connected component.

#### Algorithm

1. **Extract pad positions** (absolute coordinates) — transform relative pad coords using footprint position/angle
2. **Extract routing elements per net** — segments, vias, and zone filled polygons
3. **Build union-find graph** for each net:
   - Union segment endpoints (each segment connects its start and end)
   - Union coincident points within ~50µm tolerance on the same copper layer
   - Union pad-to-trace (segment endpoint within pad area)
   - Union via connections (vias exist on multiple layers)
   - Union zone connections (point-in-polygon for filled areas)
4. **Count connected components** among pad points:
   - All pads in same component → fully routed
   - Multiple components → net has breaks (ratsnest lines)

#### Common False Positives

- ESP32/QFN ground slug pads may appear disconnected if they're just outside the zone fill boundary
- Zone fills may need to be re-poured after component moves
- Nets named `unconnected-(...)` are explicitly marked no-connect — skip these

---

## KiCad 5 Legacy Format

KiCad 5 PCB files use `(module ...)` instead of `(footprint ...)`, and `(fp_text reference ...)` instead of `(property "Reference" ...)`.

### Key Differences

| Modern (KiCad 6+) | Legacy (KiCad 5) |
|--------------------|------------------|
| `(footprint "Lib:Name" ...)` | `(module "Lib:Name" ...)` |
| `(property "Reference" "U1" ...)` | `(fp_text reference "U1" ...)` |
| `(property "Value" "STM32" ...)` | `(fp_text value "STM32" ...)` |
| `(uuid "...")` | `(tstamp HEXID)` |
| Layer numbers: F.Cu=0, B.Cu=2 | Layer numbers: F.Cu=0, B.Cu=31 |

### Net Classes (KiCad 5 only)

KiCad 5 stores net classes directly in the PCB file:

```
(net_class Default "Default net class"
  (clearance 0.2)
  (trace_width 0.25)
  (via_dia 0.6)
  (via_drill 0.3)
  (uvia_dia 0.3)
  (uvia_drill 0.1)
  (add_net "GND")
  (add_net "+3V3")
)
```

### Dimension Annotations (KiCad 5)

```
(dimension 50.0
  (width 0.12)
  (layer "F.SilkS")
  (gr_text "50 mm" (at X Y ANGLE) ...)
  (feature1 (pts (xy X1 Y1) (xy X2 Y2)))
  (feature2 (pts (xy X3 Y3) (xy X4 Y4)))
  (crossbar (pts (xy X5 Y5) (xy X6 Y6)))
)
```

---

## Validation Methodology

When verifying analyzer output (or your own manual parse):

### Component Count Validation

1. Count all `(footprint ...)` or `(module ...)` top-level blocks
2. Compare against the analyzer's footprint count — should match exactly
3. Check for `(attr board_only)` or `(attr virtual)` components that may be excluded from counts

### Net Count Validation

1. Count all `(net N "name")` declarations (subtract net 0)
2. Compare against analyzer's net count
3. Spot-check 3-5 nets by finding all pads/segments/vias with that net ID

### Routing Completeness

1. Collect all unique net IDs from pads
2. For each net, check if it has at least one segment, via, or zone
3. Nets with multiple pads but no routing elements are unrouted
4. Nets with routing but disconnected islands need the full union-find analysis

### Known Edge Cases

- **Test points**: Single-pad footprints appear as "unrouted" nets — they only have one endpoint, which is correct
- **Mounting holes**: Non-plated holes (`np_thru_hole`) have no net and should be excluded
- **Board-only components**: Logos, fiducials with `(attr board_only)` may not have nets
- **Zone-only routing**: Some nets (especially GND) are routed entirely through copper pours with no tracks — check zone net assignments
- **Multi-layer zones**: A zone on F.Cu doesn't connect to the same zone on B.Cu unless there are vias between them
