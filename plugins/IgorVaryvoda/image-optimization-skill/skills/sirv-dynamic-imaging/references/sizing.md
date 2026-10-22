# Sirv Dynamic Imaging - Sizing & Cropping

## Width & Height

| Option | Default | Values | Description |
|--------|---------|--------|-------------|
| `w` | original | px or % | Width |
| `h` | original | px or % | Height |
| `s` | - | px | Longest dimension |
| `thumbnail` | 256 | px | Square thumbnail |

**Examples:**
```
?w=800                # 800px wide, auto height
?h=600                # Auto width, 600px tall
?w=800&h=600          # Both dimensions
?w=50%                # 50% of original
?s=1000               # Longest side = 1000px
?thumbnail=200        # 200x200 square
```

## Scale Options

| Option | Description |
|--------|-------------|
| `fit` | Fit within dimensions, maintain aspect ratio |
| `fill` | Fill dimensions, may crop |
| `ignore` | Stretch to exact dimensions |
| `noup` | No upscaling (never enlarge) |

**Examples:**
```
?w=800&h=600&scale.option=fit     # Fit within 800x600
?w=800&h=600&scale.option=fill    # Fill 800x600, crop overflow
?w=800&h=600&scale.option=ignore  # Force 800x600 (distort)
?w=2000&scale.option=noup         # Won't upscale if smaller
```

---

## Cropping

### Manual Crop

| Option | Default | Values | Description |
|--------|---------|--------|-------------|
| `cw` | - | px or % | Crop width |
| `ch` | - | px or % | Crop height |
| `cx` | 0 | px, %, or 'center' | Crop X start (from left) |
| `cy` | 0 | px, %, or 'center' | Crop Y start (from top) |

**Examples:**
```
?cw=500&ch=300                    # Crop 500x300 from top-left
?cw=500&ch=300&cx=100&cy=50       # Crop starting at 100,50
?cw=500&ch=300&cx=center&cy=center # Crop from center
?cw=50%&ch=50%                    # Crop 50% of image
```

### Auto Crop

| crop.type | Description |
|-----------|-------------|
| `trim` | Remove whitespace/solid edges |
| `poi` | Crop to point of interest |
| `face` | Face detection crop |

**Examples:**
```
?crop.type=trim                   # Trim whitespace
?crop.type=face&w=400             # Face crop, resize to 400px
?crop.type=poi&w=800&h=600        # POI crop to 800x600
```

### Crop Padding

| Option | Values | Description |
|--------|--------|-------------|
| `crop.pad.width` | px or % | Padding left/right |
| `crop.pad.height` | px or % | Padding top/bottom |

```
?crop.type=face&crop.pad.width=20%&crop.pad.height=20%
```

---

## Canvas

Add a canvas (background) around the image.

| Option | Default | Values | Description |
|--------|---------|--------|-------------|
| `canvas.width` | - | px or % | Canvas width |
| `canvas.height` | - | px or % | Canvas height |
| `canvas.color` | white | hex or name | Canvas color |
| `canvas.position` | center | position | Image position on canvas |
| `canvas.opacity` | 100 | 0-100 | Canvas opacity |
| `canvas.aspectratio` | - | W:H | Force aspect ratio |

**Position values:** north, northeast, northwest, center, south, southeast, southwest, east, west

**Examples:**
```
# White canvas, image centered
?w=800&canvas.width=1000&canvas.height=1000&canvas.color=white

# Letterbox to 16:9
?canvas.aspectratio=16:9&canvas.color=black

# Position image in corner
?canvas.width=1200&canvas.height=800&canvas.position=northwest
```

### Canvas Border

| Option | Default | Values |
|--------|---------|--------|
| `canvas.border.width` | 0 | px or % |
| `canvas.border.height` | 0 | px or % |
| `canvas.border.color` | lightgray | hex or name |
| `canvas.border.opacity` | 0 | 0-100 |

```
?canvas.width=800&canvas.border.width=20&canvas.border.color=red
```

---

## Transform

| Option | Default | Values | Description |
|--------|---------|--------|-------------|
| `rotate` | 0 | -180 to 180 | Rotation degrees |
| `flip` | no | yes/no | Flip vertical |
| `flop` | no | yes/no | Flip horizontal |

```
?rotate=90            # Rotate 90° clockwise
?rotate=-45           # Rotate 45° counter-clockwise
?flip=yes             # Flip vertically
?flop=yes             # Flip horizontally (mirror)
```

---

## Common Sizing Patterns

### E-commerce Product Grid
```
?w=400&h=400&scale.option=fit&canvas.width=400&canvas.height=400&canvas.color=white
```

### Hero Banner (16:9)
```
?w=1920&h=1080&scale.option=fill
```

### Square Social Media
```
?w=1080&h=1080&scale.option=fill&crop.type=face
```

### Thumbnail with Padding
```
?thumbnail=150&canvas.width=160&canvas.height=160&canvas.color=f5f5f5
```
