# ssr — server-side rendering safety (React v7)

All UI Kit components are browser-only (they touch `window`/`document` on import). Rendering them on the server crashes. Prevent per framework:

- **Next.js App Router:** `dynamic(() => import("./ChatView"), { ssr: false })` is **NOT allowed in a Server Component** (App Router build error: *"ssr: false is not allowed with next/dynamic in Server Components"*). Put the `dynamic(...)` call inside a `"use client"` module — e.g. a small `"use client"` wrapper that does the `dynamic(..., { ssr: false })` and renders it, then import that wrapper from your server page/layout. (The chat file itself must also be `"use client"`.)
- **Next.js Pages Router:** `dynamic(() => import("../components/CometChatNoSSR"), { ssr: false })`.
- **Astro:** `<ChatPanel client:only="react" />` — prevents render during static build.
- **React Router v7 (SSR):** `React.lazy()` + `Suspense`, gated on a mounted flag (`useEffect(() => setMounted(true), [])`; `if (!mounted) return null`).
- **Vite / CRA:** no SSR — import and use directly.

Detail belongs to `cometchat-react-v7-patterns` (framework glue); this is the core-level safety summary.
