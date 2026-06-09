# Biome

Linting + formatting replacement for ESLint and Prettier.

## Install

```bash
<pm> add -D @biomejs/biome
```

## Config

Create `biome.json`:

```json
{
  "$schema": "./node_modules/@biomejs/biome/configuration_schema.json",
  "vcs": {
    "enabled": true,
    "clientKind": "git",
    "useIgnoreFile": true
  },
  "files": {
    "ignoreUnknown": true
  },
  "formatter": {
    "enabled": true,
    "indentStyle": "space",
    "indentWidth": 2
  },
  "linter": {
    "enabled": true,
    "rules": {
      "recommended": true
    }
  },
  "javascript": {
    "formatter": {
      "quoteStyle": "double"
    }
  },
  "assist": {
    "enabled": true,
    "actions": {
      "source": {
        "organizeImports": "on"
      }
    }
  }
}
```

## Scripts

Add to `package.json`:

```json
{
  "scripts": {
    "check": "biome check",
    "format": "biome check --write"
  }
}
```

## Migration

If ESLint or Prettier are detected, suggest:

```bash
pnx @biomejs/biome migrate eslint
pnx @biomejs/biome migrate prettier
```
