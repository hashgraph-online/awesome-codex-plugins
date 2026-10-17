# Canvas Apps: Objects, Performance & Patterns

This reference covers smart guides, layer management, canvas elements, performance optimization, whiteboard-specific patterns, and accessibility for canvas-based applications.

---

## Smart Guides & Snapping

### Alignment Guides

```javascript
function calculateAlignmentGuides(draggedObject, allObjects) {
  const guides = [];
  const threshold = 5; // Snap within 5px

  allObjects.forEach(other => {
    if (other === draggedObject) return;

    // Horizontal center alignment
    if (Math.abs(draggedObject.centerY - other.centerY) < threshold) {
      guides.push({
        type: 'horizontal',
        y: other.centerY,
        from: Math.min(draggedObject.left, other.left),
        to: Math.max(draggedObject.right, other.right)
      });
    }

    // Vertical center alignment
    if (Math.abs(draggedObject.centerX - other.centerX) < threshold) {
      guides.push({
        type: 'vertical',
        x: other.centerX,
        from: Math.min(draggedObject.top, other.top),
        to: Math.max(draggedObject.bottom, other.bottom)
      });
    }

    // Edge alignments (top, bottom, left, right)
    // ... similar checks for edges
  });

  return guides;
}
```

### Smart Guide Visuals

```css
/* Alignment guides */
.smart-guide {
  position: absolute;
  background: #f43f5e;
  pointer-events: none;
  z-index: 1000;
}

.smart-guide--horizontal {
  height: 1px;
  width: 100%;
}

.smart-guide--vertical {
  width: 1px;
  height: 100%;
}

/* Distance indicator */
.distance-indicator {
  position: absolute;
  padding: 2px 6px;
  background: #f43f5e;
  color: white;
  font-size: 11px;
  border-radius: 3px;
  white-space: nowrap;
}
```

### Grid Snapping

```javascript
const GRID_SIZE = 8; // 8px grid

function snapToGrid(value) {
  return Math.round(value / GRID_SIZE) * GRID_SIZE;
}

function snapPosition(x, y) {
  return {
    x: snapToGrid(x),
    y: snapToGrid(y)
  };
}
```

### Snapping Options

```
┌─────────────────────────────────────────────┐
│ Snapping (⌘;)                    [Toggle]   │
├─────────────────────────────────────────────┤
│ ✓ Snap to grid                              │
│ ✓ Snap to objects                           │
│ ✓ Snap to guides                            │
│   Snap to pixel                             │
├─────────────────────────────────────────────┤
│ Grid size: [8px ▼]                          │
└─────────────────────────────────────────────┘
```

---

## Layers & Hierarchy

### Layer Panel

```
┌─────────────────────────────────────────────────────┐
│ Layers                                    [+] [⋮]   │
├─────────────────────────────────────────────────────┤
│ ▼ 📁 Header                               👁 🔒     │
│   │ ├─ 📄 Logo                            👁 🔓     │
│   │ ├─ 📄 Navigation                      👁 🔓     │
│   │ └─ 📄 Search                          👁 🔓     │
│ ▶ 📁 Main Content                         👁 🔓     │
│ ▶ 📁 Footer                               👁 🔓     │
│   📄 Background                           👁 🔓     │
└─────────────────────────────────────────────────────┘
```

```css
/* Layer item */
.layer-item {
  display: flex;
  align-items: center;
  padding: 4px 8px;
  cursor: pointer;
}

.layer-item:hover {
  background: #f3f4f6;
}

.layer-item--selected {
  background: #dbeafe;
}

.layer-item--dragging {
  opacity: 0.5;
}

/* Indent for hierarchy */
.layer-item[data-depth="1"] { padding-left: 20px; }
.layer-item[data-depth="2"] { padding-left: 36px; }
.layer-item[data-depth="3"] { padding-left: 52px; }
```

### Z-Index Operations

| Shortcut | Action |
|----------|--------|
| Cmd/Ctrl + ] | Bring forward |
| Cmd/Ctrl + [ | Send backward |
| Cmd/Ctrl + Shift + ] | Bring to front |
| Cmd/Ctrl + Shift + [ | Send to back |

### Grouping

```javascript
function groupSelection() {
  const group = {
    type: 'group',
    id: generateId(),
    children: [...selectedObjects],
    bounds: calculateBounds(selectedObjects)
  };

  // Remove from root, add to group
  selectedObjects.forEach(obj => {
    removeFromCanvas(obj);
    obj.parent = group;
  });

  addToCanvas(group);
  setSelection([group]);
}

function ungroupSelection() {
  selectedObjects.forEach(group => {
    if (group.type !== 'group') return;

    group.children.forEach(child => {
      child.parent = null;
      addToCanvas(child);
    });

    removeFromCanvas(group);
  });
}
```

| Shortcut | Action |
|----------|--------|
| Cmd/Ctrl + G | Group selection |
| Cmd/Ctrl + Shift + G | Ungroup selection |
| Double-click | Enter group (edit children) |
| Escape | Exit group |

---

## Canvas Elements

### Sticky Notes

Common in whiteboard apps.

```html
<div class="sticky-note" style="--sticky-color: #fef08a;">
  <div class="sticky-note__content" contenteditable>
    Type your idea here...
  </div>
  <div class="sticky-note__author">Alice</div>
</div>
```

```css
.sticky-note {
  width: 200px;
  min-height: 200px;
  padding: 16px;
  background: var(--sticky-color);
  box-shadow: 2px 2px 8px rgba(0, 0, 0, 0.15);
  border-radius: 2px;
  font-family: 'Comic Sans MS', cursive; /* Classic sticky feel */
}

.sticky-note__content {
  font-size: 16px;
  line-height: 1.4;
  outline: none;
}

.sticky-note__author {
  position: absolute;
  bottom: 8px;
  right: 8px;
  font-size: 11px;
  opacity: 0.6;
}
```

**Sticky Note Colors:**
- Yellow (#fef08a) - General ideas
- Pink (#fbcfe8) - Questions
- Blue (#bfdbfe) - Insights
- Green (#bbf7d0) - Actions
- Orange (#fed7aa) - Concerns

### Connectors & Arrows

```javascript
// Simple line connector
function drawConnector(from, to, ctx) {
  // Calculate connection points (center of objects)
  const start = { x: from.centerX, y: from.centerY };
  const end = { x: to.centerX, y: to.centerY };

  // Draw line
  ctx.beginPath();
  ctx.moveTo(start.x, start.y);
  ctx.lineTo(end.x, end.y);
  ctx.stroke();

  // Draw arrowhead
  const angle = Math.atan2(end.y - start.y, end.x - start.x);
  drawArrowhead(end, angle, ctx);
}
```

### Shapes Library

```
┌─────────────────────────────────────────────────────┐
│ Shapes                                              │
├─────────────────────────────────────────────────────┤
│ Basic                                               │
│ ┌─┐  ○  ◇  △  ─  →  ⬭                              │
│                                                     │
│ Flowchart                                           │
│ ▭  ◇  ⬭  ▱  ⬡                                      │
│                                                     │
│ Arrows                                              │
│ →  ⇒  ↔  ↕  ↗                                       │
└─────────────────────────────────────────────────────┘
```

---

## Performance Optimization

### Viewport Culling

Only render objects visible in the current viewport.

```javascript
function getVisibleObjects(camera, objects) {
  const viewport = getViewportBounds(camera);

  return objects.filter(obj =>
    intersects(obj.bounds, viewport)
  );
}

function render() {
  const visibleObjects = getVisibleObjects(camera, allObjects);

  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.save();

  // Apply camera transform
  ctx.translate(camera.x, camera.y);
  ctx.scale(camera.zoom, camera.zoom);

  // Only render visible objects
  visibleObjects.forEach(obj => obj.render(ctx));

  ctx.restore();
}
```

### Level of Detail (LOD)

Simplify rendering at low zoom levels.

```javascript
function renderObject(obj, ctx, zoom) {
  if (zoom < 0.1) {
    // Very zoomed out: just show bounding box
    ctx.fillRect(obj.x, obj.y, obj.width, obj.height);
  } else if (zoom < 0.5) {
    // Moderately zoomed out: simplified render
    obj.renderSimplified(ctx);
  } else {
    // Normal/zoomed in: full detail
    obj.renderFull(ctx);
  }
}
```

### Performance Guidelines

| Technique | When to Apply |
|-----------|--------------|
| Viewport culling | Always for >100 objects |
| LOD rendering | Zoom levels <50% |
| Debounced render | Rapid camera movement |
| Canvas layering | Static vs. dynamic content |
| Web Workers | Heavy calculations |
| Virtual scrolling | Layer panel with 1000+ items |

### Canvas Size Limits

```
Practical limits:
- Browser canvas max: ~16,000 x 16,000 pixels
- Virtual canvas: Unlimited (render only visible portion)
- Object count: 10,000+ with proper culling
- Performance target: 60fps during pan/zoom
```

---

## Whiteboard-Specific Patterns

### Timer / Timeboxing

```html
<div class="timer">
  <div class="timer__display">5:00</div>
  <div class="timer__controls">
    <button class="timer__btn--start">▶</button>
    <button class="timer__btn--pause">⏸</button>
    <button class="timer__btn--reset">↺</button>
  </div>
</div>
```

### Voting Sessions

```javascript
const votingSession = {
  id: "vote-123",
  topic: "Which design do we prefer?",
  options: [
    { id: "a", label: "Option A", votes: [] },
    { id: "b", label: "Option B", votes: [] }
  ],
  anonymous: true,
  allowMultiple: false,
  endTime: new Date("2024-12-20T14:00:00")
};

function castVote(sessionId, optionId, userId) {
  const session = getSession(sessionId);
  const vote = session.anonymous ? "anonymous" : userId;

  session.options.find(o => o.id === optionId).votes.push(vote);
  broadcastVoteUpdate(session);
}
```

### Facilitation Mode

Presenter controls for workshops.

```
┌─────────────────────────────────────────────────────┐
│ Facilitation Tools                                  │
├─────────────────────────────────────────────────────┤
│ [Spotlight]  [Timer]  [Vote]  [Lock Canvas]         │
│                                                     │
│ Participants: 12 active                             │
│ [Mute all annotations]  [Bring everyone to me]      │
└─────────────────────────────────────────────────────┘
```

### Clustering / Affinity Mapping

```javascript
// Auto-cluster similar sticky notes
function clusterStickies(stickies) {
  const clusters = [];

  stickies.forEach(sticky => {
    // Find cluster by proximity or AI similarity
    const nearbyCluster = findNearbyCluster(sticky, clusters);

    if (nearbyCluster) {
      nearbyCluster.add(sticky);
    } else {
      clusters.push(new Cluster([sticky]));
    }
  });

  return clusters;
}
```

---

## Accessibility

### Keyboard Navigation

```javascript
// Full keyboard support for canvas
const keyboardControls = {
  'Tab': () => selectNextObject(),
  'Shift+Tab': () => selectPreviousObject(),
  'Enter': () => enterEditMode(),
  'Escape': () => exitEditMode(),
  'Delete': () => deleteSelection(),
  'ArrowUp': () => moveSelection(0, -1),
  'ArrowDown': () => moveSelection(0, 1),
  'ArrowLeft': () => moveSelection(-1, 0),
  'ArrowRight': () => moveSelection(1, 0),
  'Cmd+A': () => selectAll(),
  'Cmd+Z': () => undo(),
  'Cmd+Shift+Z': () => redo()
};
```

### Screen Reader Support

```html
<!-- Announce canvas state changes -->
<div role="application" aria-label="Design canvas">
  <div aria-live="polite" class="sr-only" id="canvas-announcer">
    <!-- Dynamic announcements -->
  </div>

  <div
    role="img"
    tabindex="0"
    aria-describedby="canvas-description"
  >
    <canvas></canvas>
  </div>
</div>

<script>
function announceSelection(objects) {
  const announcer = document.getElementById('canvas-announcer');
  announcer.textContent = `Selected ${objects.length} objects`;
}
</script>
```

### Drag and Drop Alternatives

Per WCAG 2.5.7, provide non-dragging alternatives:

```html
<!-- Context menu for move operations -->
<menu class="context-menu">
  <button>Move to...</button>
  <button>Bring to front</button>
  <button>Send to back</button>
  <button>Align left</button>
  <button>Align center</button>
  <button>Align right</button>
</menu>
```

---

## Key Metrics

| Metric | Value | Context |
|--------|-------|---------|
| Grid size | 4, 8, or 16px | Common options |
| Snap threshold | 2-8px | Distance before snapping |
| Undo stack | 100+ actions | Memory permitting |
| Object limit | 10,000+ | With culling |

---

## Anti-Patterns

1. **No keyboard navigation** - Excludes users who can't use mouse
2. **Missing undo** - Critical for experimental exploration
3. **No snapping controls** - Users need to disable snapping sometimes
4. **Invisible layers** - Hard to find/select hidden objects
5. **No minimap** - Lost on large canvases

---

## Sources

- [Figma Engineering Blog](https://www.figma.com/blog/category/engineering/)
- [Miro - Infinite Canvas](https://miro.com/online-canvas-for-design/)
- [Konva.js Documentation](https://konvajs.org/)
- [LogRocket - Drag and Drop UI](https://blog.logrocket.com/ux-design/drag-and-drop-ui-examples/)
- [Cloudscape - Drag and Drop Patterns](https://cloudscape.design/patterns/general/drag-and-drop/)
