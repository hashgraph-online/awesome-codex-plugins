# Sirv Dynamic Imaging - Profiles & Optimization

## Profiles

Profiles are reusable sets of options saved as JSON files in `/Profiles/`.

### Using Profiles

```
?profile=my-profile
?profile=thumbnail
?profile=watermarked
```

### Profile Location

Profiles are stored in your Sirv account at `/Profiles/profile-name` (no extension).

### Profile Structure

```json
{
  "image": {
    "scale": {
      "width": 800,
      "height": 600,
      "option": "fit"
    },
    "format": "webp",
    "quality": 80,
    "frame": {
      "style": "none"
    }
  },
  "spin": {
    "width": 400,
    "zoom": 2.5
  }
}
```

### Profile Examples

**Thumbnail profile:**
```json
{
  "image": {
    "scale": {
      "width": 200,
      "height": 200,
      "option": "fill"
    },
    "format": "webp",
    "quality": 75
  }
}
```

**Watermarked profile:**
```json
{
  "image": {
    "watermark": {
      "image": "/logo.png",
      "position": "southeast",
      "opacity": 40,
      "scale": {
        "width": "15%"
      }
    }
  }
}
```

**Text overlay profile:**
```json
{
  "image": {
    "scale": {
      "width": 1280
    },
    "text": {
      "text": "© My Company",
      "position": "southeast",
      "color": "white",
      "opacity": 50,
      "size": 20,
      "font": {
        "family": "Open Sans"
      }
    }
  }
}
```

### Profile Priority

Options are applied in this order (highest priority first):
1. URL parameters
2. Profile settings
3. Default profile

---

## Image Formats

| Format | Option | Best For |
|--------|--------|----------|
| JPEG | `?format=jpg` | Photos |
| PNG | `?format=png` | Transparency, graphics |
| WebP | `?format=webp` | Modern browsers, smaller files |
| AVIF | `?format=avif` | Best compression |
| Optimal | `?format=optimal` | Auto-select best format |
| Original | `?format=original` | Keep source format |

### Optimal Format

```
?format=optimal
```

Sirv auto-selects the best format based on:
- Browser support (AVIF > WebP > JPEG)
- Image content (photos vs graphics)

### Forced Formats

Use a forced format only when the consumer requires it:

```
?format=webp
?format=avif
?format=jpg
```

If forcing WebP/AVIF for browser delivery, verify current Sirv fallback behavior before relying on it. For most web pages, `format=optimal` or the account default is safer.

---

## Quality Settings

| Option | Default | Range | Description |
|--------|---------|-------|-------------|
| `q` | 80 | 0-100 | JPEG/WebP quality |
| `subsampling` | 4:2:0 | 4:4:4, 4:2:2, 4:2:0 | Chroma subsampling |
| `png.optimize` | false | true/false | PNG optimization |
| `gif.lossy` | 5 | 0-100 | GIF lossy compression |

```
?q=85                             # Higher quality
?q=60                             # Smaller file
?subsampling=4:4:4                # Better color (larger file)
?png.optimize=true                # Optimize PNG
```

---

## Automatic Optimizations

Sirv automatically:
- Strips metadata (EXIF, IPTC)
- Optimizes PNG encoding
- Converts WebP to JPEG/PNG for non-supporting browsers
- Applies default quality settings

---

## Caching

- First request: Image generated on-the-fly
- Subsequent requests: Served from CDN cache
- Cache duration: Until source image changes
- Unused variations: Deleted after 30 days

### Cache Invalidation

When you update the source image, all cached variations are invalidated.

**Note:** URL timestamps are ignored. To force refresh, either:
- Overwrite the source file
- Rename the file

---

## Download

Trigger file download:

```
?dl
?w=1200&format=jpg&q=90&dl
```

---

## PDF to Image

Convert PDF pages to images:

| Option | Default | Description |
|--------|---------|-------------|
| `page` | 0 | Page number (0-indexed) |

```
/document.pdf?w=800               # First page as image
/document.pdf?page=2&w=800        # Third page
/document.pdf?format=png&w=1200   # High-res PNG
```

---

## Clipping Paths

Apply Photoshop clipping paths:

```
?clippath=Path%201
```

---

## URL Encoding

Special characters must be URL-encoded:

| Character | Encoded |
|-----------|---------|
| Space | %20 |
| / | %2F |
| # | %23 |
| % | %25 |
| & | %26 |
| + | %2B |
| © | %A9 |

```
?text=50%25%20Off                 # "50% Off"
?text=Hello%20World               # "Hello World"
?text=%C2%A9%20Company            # "© Company"
```

---

## Master Image Recommendations

For best results, upload:
- 2500-4000px width
- 92%+ JPEG quality
- Uncompressed if possible

Large images (>16MB) are pre-processed for faster on-the-fly generation.

Maximum source image: 128MB

---

## Error Handling

Invalid URLs return JSON error:

```json
{
  "name": "ApiDataValidationError",
  "message": "Supplied data is not valid",
  "validationErrors": [...]
}
```

Common errors:
- Unknown option name
- Invalid value range
- Missing required parameter
