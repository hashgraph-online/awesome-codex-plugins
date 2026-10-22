# Image Optimization Reference

## Table of Contents
1. [Lossy vs Lossless Compression](#lossy-vs-lossless-compression)
2. [Quality Settings Guide](#quality-settings-guide)
3. [Chroma Subsampling](#chroma-subsampling)
4. [Resizing Best Practices](#resizing-best-practices)
5. [Metadata Handling](#metadata-handling)
6. [Batch Optimization](#batch-optimization)
7. [Automation Pipelines](#automation-pipelines)
8. [Quality Assessment](#quality-assessment)

---

## Lossy vs Lossless Compression

### Lossy Compression
Permanently removes data to achieve smaller file sizes.

**Characteristics:**
- Significantly smaller files
- Quality degrades with repeated saves
- Cannot recover original data
- Visual quality loss at high compression

**Best for:**
- Photographs
- Complex images with many colors
- Web delivery where size matters

**Formats:** JPEG (lossy), WebP (lossy mode), AVIF (lossy mode)

### Lossless Compression
Reduces file size without losing any data.

**Characteristics:**
- Larger files than lossy
- Can be decompressed to exact original
- No quality loss ever
- Can be re-saved without degradation

**Best for:**
- Graphics with text
- Logos and icons
- Screenshots
- Source files for editing
- Medical/scientific imaging

**Formats:** PNG, WebP (lossless mode), AVIF (lossless mode), GIF

### Near-Lossless
Preprocessing that slightly modifies pixels to improve compression while maintaining near-perfect quality.

- WebP supports near-lossless mode
- Visually indistinguishable from original
- Better compression than true lossless
- Good for graphics that need small size

---

## Quality Settings Guide

### JPEG Quality Scale

| Quality | Use Case | File Size | Visual Quality |
|---------|----------|-----------|----------------|
| 95-100 | Archival, printing | Very large | Perfect |
| 85-94 | High-quality web | Large | Excellent |
| 75-84 | Standard web | Medium | Very good |
| 60-74 | Thumbnails, previews | Small | Good |
| 40-59 | Aggressive optimization | Very small | Acceptable |
| <40 | Not recommended | Tiny | Poor |

**Recommendation:** 80 for most web photos

### WebP Quality Scale

| Quality | Use Case | vs JPEG |
|---------|----------|---------|
| 85-100 | High-quality | ~85-95 JPEG equivalent |
| 75-84 | Standard web | ~80-90 JPEG equivalent |
| 60-74 | Good compression | ~70-80 JPEG equivalent |
| <60 | Aggressive | Visible artifacts |

**Recommendation:** 80 for photos, lossless for graphics

### AVIF Quality Scale

AVIF is more efficient, so use lower numbers:

| Quality | Use Case | vs JPEG |
|---------|----------|---------|
| 75-90 | High-quality | ~90-100 JPEG equivalent |
| 60-74 | Standard web | ~80-90 JPEG equivalent |
| 45-59 | Good compression | ~70-80 JPEG equivalent |
| 30-44 | Aggressive | ~60-70 JPEG equivalent |

**Recommendation:** 65-70 for most web photos

### Quality Comparison Chart

For equivalent visual quality:

| Target | JPEG | WebP | AVIF |
|--------|------|------|------|
| High | 90 | 85 | 75 |
| Standard | 80 | 75 | 65 |
| Compressed | 70 | 65 | 50 |

---

## Chroma Subsampling

Human eyes are more sensitive to brightness than color. Chroma subsampling reduces color resolution to save space.

### Subsampling Ratios

**4:4:4 (No subsampling)**
- Full color resolution
- Largest file size
- Best for graphics with sharp color edges

**4:2:2**
- Half horizontal color resolution
- Good balance of quality and size
- Suitable for high-quality photos

**4:2:0 (Most common)**
- Quarter color resolution (half horizontal and vertical)
- Significant size reduction
- Default for web photos
- May cause color fringing on sharp edges

### When to Use Each

| Scenario | Subsampling |
|----------|-------------|
| Photos for web | 4:2:0 |
| High-quality photos | 4:2:2 |
| Graphics with text | 4:4:4 |
| Red text on white | 4:4:4 |
| Print/archival | 4:4:4 |

---

## Resizing Best Practices

### Resolution Guidelines

| Device Type | Max Width | Reason |
|-------------|-----------|--------|
| Mobile | 750px | iPhone retina |
| Tablet | 1536px | iPad retina |
| Desktop | 1920px | Full HD |
| Large desktop | 2560px | QHD monitors |
| Hero images | 2560px | Cover full screens |

### Pixel Density (DPR)

Modern devices have 2x-3x pixel density. Account for this:

```
Displayed size × DPR = Image resolution needed

Example: 400px displayed width
- 1x devices: 400px image
- 2x devices: 800px image
- 3x devices: 1200px image
```

### Resizing Algorithms

**For downscaling (shrinking):**
- Lanczos - Sharpest, best for photos
- Mitchell - Good balance
- Catrom - Sharp, good for graphics

**For upscaling (enlarging):**
- Avoid when possible
- Lanczos for slight enlargement
- AI upscalers for significant enlargement

### Aspect Ratio

Always maintain aspect ratio when resizing:

```
new_height = original_height × (new_width / original_width)
```

Or use CSS `object-fit`:
```css
img {
  width: 100%;
  height: 300px;
  object-fit: cover; /* or contain */
}
```

---

## Metadata Handling

### Types of Metadata

**EXIF (Exchangeable Image File Format)**
- Camera settings (aperture, shutter speed, ISO)
- Date/time taken
- GPS coordinates (privacy concern!)
- Camera make/model
- Orientation

**IPTC (International Press Telecommunications Council)**
- Copyright information
- Caption/description
- Keywords
- Creator/author

**XMP (Extensible Metadata Platform)**
- Adobe's metadata format
- Can contain EXIF and IPTC
- Editing history

**ICC Color Profile**
- Color space information
- Important for color accuracy
- sRGB is web standard

### Metadata Decisions

**Remove for web (usually):**
- GPS coordinates (privacy!)
- Camera settings (unnecessary)
- Editing history
- Thumbnails

**Keep (sometimes):**
- Copyright information
- ICC profile (if using wide gamut)
- Orientation (or apply rotation)

**File size impact:**
- EXIF: 1-50KB typically
- ICC profile: 3-500KB
- Removing can save 10-20% on small images

### Stripping Metadata

Command-line examples:
```bash
# ExifTool - remove all metadata
exiftool -all= image.jpg

# Keep copyright only
exiftool -all= -tagsFromFile @ -Copyright image.jpg

# ImageMagick - strip
convert input.jpg -strip output.jpg

# jpegtran - lossless strip
jpegtran -copy none -optimize input.jpg > output.jpg
```

---

## Batch Optimization

### Directory Processing

Using ImageMagick:
```bash
# Convert all PNGs to WebP
mogrify -format webp -quality 80 *.png

# Resize all JPEGs to max 1920px wide
mogrify -resize '1920>' *.jpg
```

Using cwebp:
```bash
# Convert all JPEGs to WebP
for f in *.jpg; do cwebp -q 80 "$f" -o "${f%.jpg}.webp"; done
```

### Parallel Processing

```bash
# Using GNU parallel
find . -name "*.jpg" | parallel cwebp -q 80 {} -o {.}.webp

# Using xargs
find . -name "*.jpg" -print0 | xargs -0 -P 4 -I {} sh -c 'cwebp -q 80 "$1" -o "${1%.jpg}.webp"' _ {}
```

---

## Automation Pipelines

### Build Tool Integration

**Webpack (image-webpack-loader):**
```javascript
module.exports = {
  module: {
    rules: [{
      test: /\.(png|jpe?g|gif|webp)$/i,
      use: [
        {
          loader: 'image-webpack-loader',
          options: {
            mozjpeg: { quality: 80 },
            optipng: { enabled: true },
            webp: { quality: 80 }
          }
        }
      ]
    }]
  }
};
```

**Vite (vite-plugin-image-optimizer):**
```javascript
import { defineConfig } from 'vite';
import { ViteImageOptimizer } from 'vite-plugin-image-optimizer';

export default defineConfig({
  plugins: [
    ViteImageOptimizer({
      jpg: { quality: 80 },
      png: { quality: 80 },
      webp: { quality: 80 }
    })
  ]
});
```

### CI/CD Integration

GitHub Actions example:
```yaml
- name: Optimize images
  uses: calibreapp/image-actions@main
  with:
    githubToken: ${{ secrets.GITHUB_TOKEN }}
    jpegQuality: '80'
    pngQuality: '80'
    webpQuality: '80'
```

---

## Quality Assessment

### Objective Metrics

**SSIM (Structural Similarity Index)**
- Measures perceived quality
- Range: 0-1 (1 = identical)
- SSIM > 0.95 typically imperceptible difference
- Better than PSNR for perceptual quality

**PSNR (Peak Signal-to-Noise Ratio)**
- Measures difference in dB
- Higher = better quality
- 40+ dB typically excellent
- Not always correlated with perceived quality

**DSSIM (Structural Dissimilarity)**
- Inverse of SSIM
- Range: 0-1 (0 = identical)
- DSSIM < 0.015 typically acceptable

**VMAF (Video Multimethod Assessment Fusion)**
- Netflix's quality metric
- Machine learning based
- Range: 0-100
- Can be used for images

**Butteraugli**
- Google's perceptual metric
- Measures psychovisual difference
- Lower = better
- < 1.0 typically imperceptible

### Tools for Measurement

```bash
# SSIM with ImageMagick
compare -metric SSIM original.jpg compressed.jpg diff.png

# DSSIM
dssim original.png compressed.png

# Butteraugli
butteraugli original.png compressed.png
```

### Visual Inspection

Always verify with visual inspection:
1. Check edges and fine detail
2. Look for banding in gradients
3. Examine areas with text
4. Check skin tones in portraits
5. Look for mosquito noise around edges
6. Verify colors haven't shifted

### A/B Testing

For critical images:
1. Create multiple quality variants
2. Show to users randomly
3. Measure engagement/conversion
4. Find lowest quality users accept

---

## Practical Quality Thresholds

### SSIM Target Values by Use Case

| Use Case | Minimum SSIM | Recommended | Notes |
|----------|--------------|-------------|-------|
| E-commerce products | 0.97 | 0.98+ | Detail matters for purchases |
| Hero/marketing images | 0.95 | 0.96+ | Balance quality with impact |
| Blog post images | 0.92 | 0.94+ | Content > perfection |
| Thumbnails | 0.88 | 0.90+ | Small size hides artifacts |
| Background images | 0.85 | 0.90+ | Often blurred/overlaid |
| User avatars | 0.90 | 0.93+ | Face detail important |

### VMAF Thresholds

VMAF was designed for video but works for images:

| Rating | VMAF Score | Quality Level |
|--------|------------|---------------|
| Excellent | 95-100 | Visually lossless |
| Good | 85-94 | High quality, minor artifacts |
| Fair | 70-84 | Acceptable for most uses |
| Poor | 50-69 | Noticeable quality loss |
| Bad | <50 | Significant degradation |

**Target:** VMAF > 90 for product images, > 80 for general content

### Butteraugli Thresholds

Google's perceptual metric (lower = better):

| Score | Interpretation |
|-------|----------------|
| < 0.5 | Imperceptible difference |
| 0.5 - 1.0 | Barely perceptible |
| 1.0 - 1.5 | Subtle but visible |
| 1.5 - 2.0 | Clearly visible |
| > 2.0 | Obvious quality loss |

### Quality Settings to Achieve Targets

**For SSIM ≥ 0.95:**
| Format | Quality Setting |
|--------|-----------------|
| JPEG | 82-88 |
| WebP | 78-85 |
| AVIF | 62-72 |

**For SSIM ≥ 0.90:**
| Format | Quality Setting |
|--------|-----------------|
| JPEG | 72-78 |
| WebP | 68-75 |
| AVIF | 50-60 |

### Automated Quality Finding

Use binary search to find optimal quality:

```javascript
const sharp = require('sharp');
const ssim = require('ssim.js');

async function findOptimalQuality(input, targetSSIM = 0.95) {
  const original = await sharp(input).raw().toBuffer({ resolveWithObject: true });

  let low = 30, high = 95, best = high;

  while (low <= high) {
    const mid = Math.floor((low + high) / 2);

    const compressed = await sharp(input)
      .webp({ quality: mid })
      .toBuffer();

    const decompressed = await sharp(compressed)
      .raw()
      .toBuffer({ resolveWithObject: true });

    const score = ssim.ssim(original.data, decompressed.data, {
      width: original.info.width,
      height: original.info.height
    }).mssim;

    if (score >= targetSSIM) {
      best = mid;
      high = mid - 1;
    } else {
      low = mid + 1;
    }
  }

  return best;
}
```

### Content-Aware Quality

Different image content needs different quality:

| Content Type | Characteristics | Quality Adjustment |
|--------------|-----------------|-------------------|
| Flat graphics | Sharp edges, solid colors | Lower quality OK |
| Gradients | Smooth transitions | Higher quality needed |
| Text/logos | Fine detail | Higher quality needed |
| Faces | Important detail | Higher quality |
| Landscapes | Varied textures | Medium quality OK |
| Product shots | Detail matters | Higher quality |

### A/B Testing Framework

```javascript
// Quality variant testing
const variants = [
  { quality: 70, label: 'low' },
  { quality: 80, label: 'medium' },
  { quality: 90, label: 'high' }
];

function selectVariant(userId) {
  const hash = hashCode(userId) % variants.length;
  return variants[hash];
}

// Track metrics per variant
function trackImageMetric(variant, metric, value) {
  analytics.track('image_quality_test', {
    variant: variant.label,
    quality: variant.quality,
    metric, // 'engagement', 'conversion', 'bounce'
    value
  });
}
