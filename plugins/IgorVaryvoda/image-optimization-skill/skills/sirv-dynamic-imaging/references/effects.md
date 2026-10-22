# Sirv Dynamic Imaging - Effects & Filters

## Color Adjustments

| Option | Default | Range | Description |
|--------|---------|-------|-------------|
| `brightness` | 0 | -100 to 100 | Brightness |
| `contrast` | 0 | -100 to 100 | Contrast |
| `exposure` | 0 | -100 to 100 | Exposure |
| `hue` | 0 | -100 to 100 | Hue shift |
| `saturation` | 0 | -100 to 100 | Saturation |
| `lightness` | 0 | -100 to 100 | Lightness |
| `shadows` | 0 | -100 to 100 | Shadow levels |
| `highlights` | 0 | -100 to 100 | Highlight levels |

**Examples:**
```
?brightness=20                    # Brighter
?contrast=30&saturation=20        # More punch
?saturation=-100                  # Desaturated
?hue=50                           # Shift colors
```

## Black & White

| Option | Values | Description |
|--------|--------|-------------|
| `grayscale` | true/false | Convert to grayscale |

```
?grayscale=true
?grayscale=true&contrast=20       # High contrast B&W
```

## Color Levels

| Option | Default | Range | Description |
|--------|---------|-------|-------------|
| `colorlevel.black` | 0 | 0-254 | Black point |
| `colorlevel.white` | 255 | 1-255 | White point |

```
?colorlevel.black=20&colorlevel.white=240   # Increase contrast
```

---

## Blur & Sharpen

| Option | Default | Range | Description |
|--------|---------|-------|-------------|
| `blur` | 0 | 0-100 | Gaussian blur |
| `sharpen` | 0 | 0-100 | Sharpen |

```
?blur=5                           # Subtle blur
?blur=50                          # Heavy blur (background effect)
?sharpen=30                       # Sharpen details
```

---

## Color Tones (Presets)

| Preset | Description |
|--------|-------------|
| `sepia` | Classic sepia |
| `warm` | Warm tones |
| `cold` | Cool/blue tones |
| `sunset` | Orange sunset |
| `purpletan` | Purple/tan |
| `texas` | Warm vintage |
| `aurora` | Northern lights |
| `blackberry` | Deep purple |
| `coffee` | Brown tones |
| `clearwater` | Cyan/teal |
| `dusk` | Evening tones |
| `stereo` | Vintage stereo |

```
?colortone=sepia
?colortone=warm
?colortone=sunset
```

### Custom Color Tone

| Option | Default | Description |
|--------|---------|-------------|
| `colortone.color` | 000000 | Hex color |
| `colortone.level` | 100 | Blend level 0-100 |
| `colortone.mode` | solid | solid, highlights, shadows |

```
?colortone.color=ff6600&colortone.level=50
?colortone.color=0066ff&colortone.mode=shadows
```

---

## Colorize (Overlay)

| Option | Default | Description |
|--------|---------|-------------|
| `colorize.color` | black | Overlay color |
| `colorize.opacity` | 100 | Opacity 0-100 |

```
?colorize.color=ff0000&colorize.opacity=30   # Red tint
?colorize.color=0000ff&colorize.opacity=20   # Blue tint
```

---

## Vignette

| Option | Default | Description |
|--------|---------|-------------|
| `vignette.value` | 20 | Intensity 0-100 |
| `vignette.color` | 000000 | Edge color |

```
?vignette.value=40                           # Dark edges
?vignette.value=30&vignette.color=ffffff     # White vignette
```

---

## Opacity

| Option | Default | Range | Description |
|--------|---------|-------|-------------|
| `opacity` | 100 | 0-100 | Image opacity (PNG only) |

```
?opacity=50&format=png            # 50% transparent
```

---

## Histogram

| Option | Values | Description |
|--------|--------|-------------|
| `histogram` | r, g, b, rgb | Display color histogram |

```
?histogram=rgb                    # Show RGB histogram
```

---

## Effect Combinations

### Vintage Photo
```
?colortone=sepia&vignette.value=40&contrast=10
```

### High Impact
```
?contrast=30&saturation=20&sharpen=20
```

### Dreamy/Soft
```
?blur=3&brightness=10&saturation=-20
```

### Moody B&W
```
?grayscale=true&contrast=40&vignette.value=50
```

### Warm Sunset
```
?colortone=sunset&brightness=10&saturation=15
```

### Cool Night
```
?colortone=cold&contrast=20&brightness=-10
```
