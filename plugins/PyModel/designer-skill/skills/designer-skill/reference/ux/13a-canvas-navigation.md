# Canvas Apps: Navigation & Interaction

Canvas-based interfaces provide an infinite 2D workspace where users can freely place, move, and manipulate objects. Found in design tools (Figma, Sketch), whiteboards (Miro, FigJam), maps, and diagramming apps.

---

## Canvas Navigation

### Coordinate Systems

A canvas app has two coordinate systems:

```javascript
// Screen coordinates: pixel position on display
const screenPoint = { x: 500, y: 300 };

// Canvas coordinates: position in the infinite canvas space
const canvasPoint = {
  x: (screenPoint.x - camera.x) / camera.zoom,
  y: (screenPoint.y - camera.y) / camera.zoom
};

// Camera state
const camera = {
  x: 0,      // Horizontal offset
  y: 0,      // Vertical offset
  zoom: 1    // Scale factor (1 = 100%)
};
```

### Zoom UI

Zoom should feel natural, focusing on the cursor position.

```javascript
function handleZoom(event) {
  event.preventDefault();

  const zoomFactor = event.deltaY > 0 ? 0.9 : 1.1;
  const newZoom = clamp(camera.zoom * zoomFactor, MIN_ZOOM, MAX_ZOOM);

  // Zoom toward cursor position
  const cursorX = event.clientX;
  const cursorY = event.clientY;

  // Calculate new camera position to keep cursor point fixed
  camera.x = cursorX - (cursorX - camera.x) * (newZoom / camera.zoom);
  camera.y = cursorY - (cursorY - camera.y) * (newZoom / camera.zoom);
  camera.zoom = newZoom;

  render();
}
```

#### Zoom Controls

```
┌──────────────────────────────┐
│  [−]  ━━━●━━━━━━━━━  [+]     │  Slider
│           100%               │  Current level
│  [Fit] [50%] [100%] [200%]   │  Presets
└──────────────────────────────┘
```

| Control | Action |
|---------|--------|
| Scroll wheel | Zoom in/out |
| Ctrl/Cmd + scroll | Zoom (alternative) |
| Pinch gesture | Zoom on touch devices |
| +/- keys | Step zoom |
| 0 or 1 | Reset to 100% |
| Shift + 1 | Fit all to view |
| Shift + 2 | Fit selection to view |

#### Zoom Levels

```
Typical range: 10% to 4000%+
Common presets: 25%, 50%, 75%, 100%, 150%, 200%, 400%

Semantic zooming (content changes at different levels):
- 10-25%   → Show only shapes/outlines
- 25-50%   → Show basic content, hide details
- 50-100%  → Full content visible
- 100-200% → Pixel-perfect editing
- 200%+    → Sub-pixel precision work
```

### Pan/Scroll

```javascript
// Space + drag to pan
let isPanning = false;
let lastPanPoint = { x: 0, y: 0 };

function handleKeyDown(event) {
  if (event.code === 'Space' && !isPanning) {
    isPanning = true;
    document.body.style.cursor = 'grab';
  }
}

function handleMouseMove(event) {
  if (isPanning && event.buttons === 1) {
    camera.x += event.clientX - lastPanPoint.x;
    camera.y += event.clientY - lastPanPoint.y;
    document.body.style.cursor = 'grabbing';
    render();
  }
  lastPanPoint = { x: event.clientX, y: event.clientY };
}
```

#### Pan Methods

| Method | Trigger | Notes |
|--------|---------|-------|
| Space + drag | Hold space, click and drag | Most common in design tools |
| Middle mouse | Middle click and drag | Power user shortcut |
| Two-finger drag | Trackpad gesture | Natural for laptop users |
| Scroll bars | Click and drag | Visible scroll position |
| Arrow keys | Keyboard navigation | Step-based movement |

### Minimap / Overview

Bird's-eye navigation for large canvases.

```html
<div class="minimap">
  <canvas id="minimap-canvas"></canvas>
  <div class="minimap__viewport"></div>
</div>
```

```css
.minimap {
  position: fixed;
  bottom: 16px;
  right: 16px;
  width: 200px;
  height: 150px;
  background: #f3f4f6;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  overflow: hidden;
}

.minimap__viewport {
  position: absolute;
  border: 2px solid #3b82f6;
  background: rgba(59, 130, 246, 0.1);
  cursor: move;
}
```

**Minimap Guidelines:**
- Show at 5-10% of actual canvas scale
- Highlight current viewport area
- Allow click-to-navigate
- Allow drag viewport rectangle
- Consider hiding when zoomed to fit all

---

## Object Selection

### Selection Modes

```javascript
// Click selection
function handleClick(event) {
  const hitObject = hitTest(event.x, event.y);

  if (event.shiftKey) {
    // Add to / remove from selection
    toggleSelection(hitObject);
  } else {
    // Replace selection
    clearSelection();
    if (hitObject) select(hitObject);
  }
}

// Marquee selection
function handleMarquee(startPoint, endPoint) {
  const rect = {
    x: Math.min(startPoint.x, endPoint.x),
    y: Math.min(startPoint.y, endPoint.y),
    width: Math.abs(endPoint.x - startPoint.x),
    height: Math.abs(endPoint.y - startPoint.y)
  };

  const contained = objects.filter(obj =>
    isContainedIn(obj.bounds, rect)
  );

  if (event.shiftKey) {
    addToSelection(contained);
  } else {
    setSelection(contained);
  }
}
```

### Selection Visuals

```css
/* Selected object */
.object--selected {
  outline: 2px solid #3b82f6;
  outline-offset: 2px;
}

/* Selection marquee */
.selection-marquee {
  position: absolute;
  border: 1px solid #3b82f6;
  background: rgba(59, 130, 246, 0.1);
  pointer-events: none;
}

/* Multi-selection bounding box */
.selection-bounds {
  position: absolute;
  border: 1px dashed #3b82f6;
}
```

### Selection Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Click | Select single object |
| Shift + Click | Add/remove from selection |
| Cmd/Ctrl + A | Select all |
| Escape | Deselect all |
| Tab | Select next object |
| Shift + Tab | Select previous object |
| Cmd/Ctrl + Click | Deep select (nested elements) |

---

## Object Manipulation

### Transform Controls

```
        ┌─────────────────────────────────┐
    ◯───┤                                 ├───◯  ← Rotation handle
        │                                 │
    ◻───┤         Selected Object         ├───◻  ← Resize handles
        │                                 │
    ◯───┤                                 ├───◯
        └─────────────────────────────────┘
              ◻                     ◻
```

```css
/* Resize handles */
.resize-handle {
  position: absolute;
  width: 8px;
  height: 8px;
  background: white;
  border: 1px solid #3b82f6;
  border-radius: 2px;
}

/* Corner handles - resize */
.resize-handle--nw { cursor: nwse-resize; top: -4px; left: -4px; }
.resize-handle--ne { cursor: nesw-resize; top: -4px; right: -4px; }
.resize-handle--sw { cursor: nesw-resize; bottom: -4px; left: -4px; }
.resize-handle--se { cursor: nwse-resize; bottom: -4px; right: -4px; }

/* Edge handles */
.resize-handle--n { cursor: ns-resize; top: -4px; left: 50%; }
.resize-handle--s { cursor: ns-resize; bottom: -4px; left: 50%; }
.resize-handle--e { cursor: ew-resize; right: -4px; top: 50%; }
.resize-handle--w { cursor: ew-resize; left: -4px; top: 50%; }

/* Rotation handle */
.rotate-handle {
  position: absolute;
  top: -30px;
  left: 50%;
  width: 10px;
  height: 10px;
  background: white;
  border: 1px solid #3b82f6;
  border-radius: 50%;
  cursor: grab;
}
```

### Drag and Drop

```javascript
function handleDrag(object, event) {
  // Show ghost/preview at cursor
  showDragPreview(object, event.x, event.y);

  // Check drop targets
  const dropTarget = findDropTarget(event.x, event.y);
  if (dropTarget) {
    highlightDropTarget(dropTarget);
  }
}

function handleDrop(object, event) {
  const dropTarget = findDropTarget(event.x, event.y);

  // Animate to final position
  animateTo(object, {
    x: snapToGrid(event.x),
    y: snapToGrid(event.y)
  }, { duration: 100 });

  hideDragPreview();
}
```

**Drag and Drop Guidelines:**
- Show visual feedback during drag (elevation, shadow)
- Animate other elements moving out of the way
- Use 100ms animation for drop
- Provide clear drop zone indicators
- Support keyboard alternatives (WCAG 2.5.7)

### Keyboard Movement

```javascript
const MOVE_STEP = 1;       // Arrow key
const MOVE_STEP_LARGE = 10; // Shift + Arrow

function handleArrowKey(key, shiftKey) {
  const step = shiftKey ? MOVE_STEP_LARGE : MOVE_STEP;

  selectedObjects.forEach(obj => {
    switch(key) {
      case 'ArrowUp':    obj.y -= step; break;
      case 'ArrowDown':  obj.y += step; break;
      case 'ArrowLeft':  obj.x -= step; break;
      case 'ArrowRight': obj.x += step; break;
    }
  });
}
```

---

## Key Metrics

| Metric | Value | Context |
|--------|-------|---------|
| Zoom range | 10% - 4000% | Typical design tools |
| Pan speed | 1:1 cursor ratio | Natural feeling |
| Touch target | 44×44px | Minimum for handles |
| Render target | 60fps | During pan/zoom |

---

## Anti-Patterns

1. **Fixed canvas size** - Limiting creativity with artificial boundaries
2. **Zoom at screen center** - Disorienting; zoom at cursor instead
3. **Sluggish pan/zoom** - Must feel instant and smooth
4. **Inconsistent shortcuts** - Differs from industry standard
5. **Poor touch support** - Gestures should match platform conventions

---

## Sources

- [Steve Ruiz - Creating a Zoom UI](https://www.steveruiz.me/posts/zoom-ui)
- [NN/g - Drag and Drop](https://www.nngroup.com/articles/drag-drop/)
- [Pencil & Paper - Drag & Drop UX Patterns](https://www.pencilandpaper.io/articles/ux-pattern-drag-and-drop)
- [Salesforce - 4 Patterns for Accessible Drag and Drop](https://medium.com/salesforce-ux/4-major-patterns-for-accessible-drag-and-drop-1d43f64ebf09)
