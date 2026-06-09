# System Dependencies Mapping

## NPM Packages → System Libraries

### Image Processing

| Package | Debian/Ubuntu Packages |
|---------|----------------------|
| `sharp` | `libvips-dev` |
| `canvas` | `build-essential libcairo2-dev libpango1.0-dev libjpeg-dev libgif-dev librsvg2-dev` |
| `@napi-rs/canvas` | `build-essential libcairo2-dev libpango1.0-dev libjpeg-dev libgif-dev librsvg2-dev` |
| `jimp` | (none - pure JS) |
| `gm` | `graphicsmagick` |
| `imagemagick` | `imagemagick` |

### Database Clients (Native)

| Package | Debian/Ubuntu Packages |
|---------|----------------------|
| `better-sqlite3` | `python3 make g++` |
| `sqlite3` | `python3 make g++` |
| `pg-native` | `libpq-dev` |

### Cryptography

| Package | Debian/Ubuntu Packages |
|---------|----------------------|
| `bcrypt` | `python3 make g++` |
| `argon2` | `python3 make g++` |
| `sodium-native` | `python3 make g++` |

### General Native Addons

| Package | Debian/Ubuntu Packages |
|---------|----------------------|
| Any with `node-gyp` | `python3 make g++` |
| `@swc/*` | (prebuilt binaries, usually none) |
| `esbuild` | (prebuilt binaries, usually none) |

### PDF/Document

| Package | Debian/Ubuntu Packages |
|---------|----------------------|
| `pdf-lib` | (none - pure JS) |
| `pdfkit` | (none - pure JS) |
| `puppeteer` | `chromium-browser` (or use puppeteer with bundled chromium) |
| `playwright` | (use playwright install) |

---

## Python Packages → System Libraries

### Database

| Package | Debian/Ubuntu Packages |
|---------|----------------------|
| `psycopg2` | `libpq-dev` |
| `psycopg2-binary` | (none - uses bundled libs) |
| `mysqlclient` | `default-libmysqlclient-dev` |
| `pymssql` | `freetds-dev` |

### Image Processing

| Package | Debian/Ubuntu Packages |
|---------|----------------------|
| `Pillow` | `libjpeg-dev libpng-dev libtiff-dev libwebp-dev` |
| `opencv-python` | `libgl1-mesa-glx libglib2.0-0` |
| `opencv-python-headless` | `libgl1-mesa-glx libglib2.0-0` |

### Cryptography

| Package | Debian/Ubuntu Packages |
|---------|----------------------|
| `cryptography` | `libssl-dev libffi-dev` |
| `pynacl` | `libsodium-dev` |

### XML/HTML

| Package | Debian/Ubuntu Packages |
|---------|----------------------|
| `lxml` | `libxml2-dev libxslt-dev` |
| `beautifulsoup4` | (none - pure Python) |

### Scientific

| Package | Debian/Ubuntu Packages |
|---------|----------------------|
| `numpy` | (prebuilt wheels, usually none) |
| `scipy` | `libopenblas-dev` (optional, for building from source) |
| `pandas` | (prebuilt wheels, usually none) |

### ML/AI

| Package | Debian/Ubuntu Packages |
|---------|----------------------|
| `torch` | (prebuilt wheels) |
| `tensorflow` | (prebuilt wheels) |
| `onnxruntime` | (prebuilt wheels) |

---

## Go Packages → System Libraries

Go typically compiles to static binaries, but some packages require CGO:

| Package | Debian/Ubuntu Packages |
|---------|----------------------|
| `go-sqlite3` | `gcc` (for CGO build) |
| Most packages | (none - static compilation) |

For CGO-enabled builds:
```dockerfile
# Build stage needs:
RUN apk add --no-cache gcc musl-dev  # Alpine
RUN apt-get install -y gcc           # Debian
```

For static builds (recommended):
```dockerfile
RUN CGO_ENABLED=0 go build -a -installsuffix cgo -o main .
```

---

## Java → System Libraries

Most dependencies are handled by Maven/Gradle. Rare cases:

| Use Case | Debian/Ubuntu Packages |
|----------|----------------------|
| Native image (GraalVM) | `build-essential zlib1g-dev` |
| Fonts for PDF | `fontconfig fonts-dejavu` |

---

## Detection Script

Use this to detect which system packages are needed:

```bash
#!/bin/bash
# Scan package.json for known native dependencies

NATIVE_DEPS=""

if grep -q '"sharp"' package.json; then
  NATIVE_DEPS="$NATIVE_DEPS libvips-dev"
fi

if grep -q '"canvas"\|"@napi-rs/canvas"' package.json; then
  NATIVE_DEPS="$NATIVE_DEPS build-essential libcairo2-dev libpango1.0-dev libjpeg-dev libgif-dev librsvg2-dev"
fi

if grep -q '"better-sqlite3"\|"bcrypt"\|"argon2"' package.json; then
  NATIVE_DEPS="$NATIVE_DEPS python3 make g++"
fi

if grep -q '"pg-native"' package.json; then
  NATIVE_DEPS="$NATIVE_DEPS libpq-dev"
fi

echo "Required system packages: $NATIVE_DEPS"
```

---

## Alpine vs Debian/Slim

### When to use Debian Slim (Recommended)
- Projects with native dependencies (sharp, canvas, bcrypt)
- Next.js projects
- Complex Node.js applications

### When to use Alpine
- Simple Go applications (static binary)
- Minimal Python scripts without native deps
- Size is critical and no native deps

### Package Name Differences

| Debian | Alpine |
|--------|--------|
| `python3` | `python3` |
| `make` | `make` |
| `g++` | `g++` |
| `build-essential` | `build-base` |
| `libvips-dev` | `vips-dev` |
| `libcairo2-dev` | `cairo-dev` |
| `libpango1.0-dev` | `pango-dev` |
| `libpq-dev` | `postgresql-dev` |
