# Vite Environment Patterns

Environment overlay for Vite-based projects. Used alongside the framework pattern file (react.md). Referenced by the frontend-dev skill when `vite.config.*` is detected.

---

## Review Standards (Additional)

- Vite config uses TypeScript (`vite.config.ts`)
- Environment variables use `VITE_` prefix for client exposure
- Imports use path aliases configured in both `vite.config.ts` and `tsconfig.json`
- No `process.env` — use `import.meta.env`
- Lazy loading with dynamic `import()` for code splitting

---

## Configuration

### vite.config.ts

```typescript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 3000,
    proxy: {
      "/api": {
        target: "http://localhost:8080",
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: "dist",
    sourcemap: true,
  },
});
```

### Path Aliases (keep in sync)

```json
// tsconfig.json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

---

## Environment Variables

```bash
# .env
VITE_API_URL=https://api.example.com
VITE_APP_TITLE=My App

# .env.local (gitignored, local overrides)
VITE_API_URL=http://localhost:8080
```

```typescript
// Access in code
const apiUrl = import.meta.env.VITE_API_URL;
const isDev = import.meta.env.DEV;
const isProd = import.meta.env.PROD;

// Type safety
/// <reference types="vite/client" />
interface ImportMetaEnv {
  readonly VITE_API_URL: string;
  readonly VITE_APP_TITLE: string;
}
```

**Rule:** Only variables prefixed with `VITE_` are exposed to client code. Server-only secrets must NOT use this prefix.

---

## Project Structure

```
├── public/                 # Static assets (copied as-is)
├── src/
│   ├── main.tsx            # Entry point
│   ├── App.tsx             # Root component
│   ├── components/
│   ├── hooks/              # (React)
│   ├── types/
│   └── vite-env.d.ts       # Vite type declarations
├── index.html              # HTML entry (Vite uses this as entry)
├── vite.config.ts
├── tsconfig.json
└── package.json
```

---

## Build & Development

Run package.json scripts via the project's detected package manager — see [../../../shared/package-manager.md](../../../shared/package-manager.md). The placeholder `<PM> run <script>` resolves to `npm run <script>` / `pnpm <script>` / `yarn <script>` / `bun run <script>`.

```bash
# Development with HMR
<PM> run dev          # vite

# Type checking (Vite does NOT type-check)
<PM> run typecheck    # tsc --noEmit

# Production build
<PM> run build        # vite build

# Preview production build locally
<PM> run preview      # vite preview
```

**Important:** Vite does NOT run TypeScript type checking during `vite build`. Always run `tsc --noEmit` (or framework equivalent) separately.

---

## Code Splitting

```typescript
// Lazy loading routes (React Router example)
const Dashboard = lazy(() => import("./pages/Dashboard"));
const Settings = lazy(() => import("./pages/Settings"));

// Dynamic imports
const module = await import("./heavy-module");
```

---

## What NOT to Do

| Anti-Pattern | Instead |
|--------------|---------|
| `process.env.X` | `import.meta.env.VITE_X` |
| Secrets with `VITE_` prefix | Use server-only env vars (no `VITE_` prefix) |
| Skip type checking | Run `tsc --noEmit` alongside `vite build` |
| Mismatched path aliases | Keep `vite.config.ts` and `tsconfig.json` in sync |
| Import everything eagerly | Use dynamic `import()` for large modules |
