# Sirv Dynamic Imaging - Text & Watermarks

## Text Overlay

### Basic Text

| Option | Default | Description |
|--------|---------|-------------|
| `text` | - | Text to display (URL encoded) |
| `text.text64` | - | Base64 encoded text (alternative) |

```
?text=Hello%20World
?text=Sale%20-%2050%25%20Off
?text.text64=SGVsbG8gV29ybGQ=
```

### Font Settings

| Option | Default | Values |
|--------|---------|--------|
| `text.font.family` | Open Sans | Any Google Font |
| `text.font.size` | auto | px |
| `text.font.weight` | 400 | 300, 400, 600, 700, 800 |
| `text.font.style` | normal | normal, italic |

**Popular fonts:** Open Sans, Roboto, Lato, Montserrat, Playfair Display, Shadows Into Light Two

```
?text=Elegant&text.font.family=Playfair%20Display&text.font.weight=700
?text=Modern&text.font.family=Montserrat&text.font.style=italic
```

### Text Size & Position

| Option | Default | Values |
|--------|---------|--------|
| `text.size` | 25% | % of image width |
| `text.position` | southeast | position keyword |
| `text.position.x` | - | px or % from left |
| `text.position.y` | - | px or % from top |
| `text.position.gravity` | southeast | base position |
| `text.align` | center | left, center, right |

**Position keywords:** north, northeast, northwest, center, south, southeast, southwest, east, west

```
?text=Top%20Left&text.position=northwest
?text=Centered&text.position=center
?text=Custom&text.position.x=50&text.position.y=100
?text=Bottom%20Right&text.position=southeast&text.size=20%
```

### Text Color & Opacity

| Option | Default | Values |
|--------|---------|--------|
| `text.color` | grey | hex RGB/RGBA or name |
| `text.opacity` | 100 | 0-100 |

```
?text=White%20Text&text.color=ffffff
?text=Semi%20Transparent&text.color=000000&text.opacity=50
?text=With%20Alpha&text.color=ff000080
```

### Text Outline

| Option | Default | Values |
|--------|---------|--------|
| `text.outline.width` | 0 | px |
| `text.outline.color` | 000000 | hex or name |
| `text.outline.opacity` | 100 | 0-100 |
| `text.outline.blur` | 0 | px |

```
?text=Outlined&text.color=white&text.outline.width=2&text.outline.color=black
?text=Glow&text.outline.width=5&text.outline.blur=10&text.outline.color=ff0000
```

### Text Background

| Option | Default | Values |
|--------|---------|--------|
| `text.background.color` | - | hex or name |
| `text.background.opacity` | 100 | 0-100 |

```
?text=Label&text.background.color=000000&text.background.opacity=70&text.color=white
```

---

## Watermark

### Basic Watermark

| Option | Description |
|--------|-------------|
| `watermark` | Path to watermark image |

```
?watermark=/logo.png
?watermark=/watermarks/copyright.png
```

### Position

| Option | Default | Values |
|--------|---------|--------|
| `watermark.position` | center | position or 'tile' |
| `watermark.position.x` | - | px or % |
| `watermark.position.y` | - | px or % |
| `watermark.position.gravity` | northwest | base position |

```
?watermark=/logo.png&watermark.position=southeast
?watermark=/logo.png&watermark.position=tile            # Repeating pattern
?watermark=/logo.png&watermark.position.x=20&watermark.position.y=20
```

### Size

| Option | Default | Values |
|--------|---------|--------|
| `watermark.scale.width` | original | px or % |
| `watermark.scale.height` | original | px or % |
| `watermark.scale.option` | noup | noup, fit, fill, ignore |

```
?watermark=/logo.png&watermark.scale.width=20%
?watermark=/logo.png&watermark.scale.width=150&watermark.scale.height=50
```

### Appearance

| Option | Default | Values |
|--------|---------|--------|
| `watermark.opacity` | 100 | 0-100 |
| `watermark.rotate` | 0 | -180 to 180 |
| `watermark.layer` | front | front, back |

```
?watermark=/logo.png&watermark.opacity=30
?watermark=/logo.png&watermark.rotate=45
?watermark=/bg.png&watermark.layer=back
```

### Watermark Canvas

Add background behind watermark:

| Option | Values |
|--------|--------|
| `watermark.canvas.color` | hex or name |
| `watermark.canvas.opacity` | 0-100 |
| `watermark.canvas.width` | px or % |
| `watermark.canvas.height` | px or % |

```
?watermark=/logo.png&watermark.canvas.color=ffffff&watermark.canvas.opacity=80
```

### Crop Watermark

| Option | Values |
|--------|--------|
| `watermark.crop.x` | px or % |
| `watermark.crop.y` | px or % |
| `watermark.crop.width` | px or % |
| `watermark.crop.height` | px or % |

---

## Frame

| Option | Default | Values |
|--------|---------|--------|
| `frame.style` | none | solid, mirror, edge, dither, none |
| `frame.color` | - | hex or name |
| `frame.width` | 5% | px or % |

```
?frame.style=solid&frame.color=000000&frame.width=10
?frame.style=mirror&frame.width=50
```

### Frame Rim

| Option | Default | Values |
|--------|---------|--------|
| `frame.rim.color` | white | hex or name |
| `frame.rim.width` | 1 | px |

```
?frame.style=solid&frame.color=gold&frame.rim.color=black&frame.rim.width=2
```

---

## Common Overlay Patterns

### Copyright Text
```
?text=©%202024%20Company&text.position=southeast&text.size=15%&text.color=ffffff&text.opacity=50
```

### Logo Watermark
```
?watermark=/logo.png&watermark.position=southeast&watermark.scale.width=15%&watermark.opacity=40
```

### Price Tag
```
?text=$99.99&text.position=northeast&text.background.color=ff0000&text.color=white&text.size=20%
```

### Photo Credit
```
?text=Photo%20by%20John%20Doe&text.position=southwest&text.font.family=Lato&text.size=12%&text.color=white&text.opacity=70
```

### Tiled Watermark
```
?watermark=/logo.png&watermark.position=tile&watermark.opacity=10&watermark.scale.width=100
```

### Polaroid Frame
```
?frame.style=solid&frame.color=ffffff&frame.width=5%&canvas.border.height=15%
```
