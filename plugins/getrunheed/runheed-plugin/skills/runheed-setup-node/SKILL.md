---
name: runheed-setup-node
description: Add Runheed error reporting to a Node.js or TypeScript app (Express, Next.js, Fastify, Bun, serverless) so production errors reach the coding agent over MCP. Use when the user asks to "add error tracking", "set up Runheed", "report production errors", "add Sentry-style monitoring" to a JavaScript or TypeScript project.
---

# Set up Runheed in a Node.js app

Full reference, kept current: https://runheed.com/SETUP.txt (read it if anything here doesn't match the project).

## 1. The DSN (needs the user)
Ask the user to sign in at https://runheed.com/login, create a project under Projects and paste the DSN (`runheed://pk_...@runheed.com/<project-id>`). Save it as `RUNHEED_DSN` in `.env` or `.env.local` (or the host's secrets). Never commit it. Next.js and Bun read `.env` on their own; plain Node doesn't, so use `node --env-file=.env` or the host's environment settings.

## 2. Install
```bash
npm install https://runheed.com/dl/runheed-0.1.7.tgz
```
(or `bun add` / `pnpm add` with the same URL). The package installs from runheed.com; the URL is written to package.json, so deploys get it too.

## 3. Initialize, by framework
**Next.js:** don't use the snippet below. Report from `onRequestError` in `instrumentation.ts` and await `flush()` there, exactly as https://runheed.com/for/nextjs shows (it keeps Node-only imports out of the Edge build).

**Express and other Node servers:** in the earliest-loaded server file:
```ts
import runheed, { expressErrorHandler } from 'runheed';
runheed.init({ dsn: process.env.RUNHEED_DSN, environment: process.env.NODE_ENV, release: process.env.GIT_SHA });
```
Express: add `app.use(expressErrorHandler());` after all routes.

**Bun.serve:** report from its `error()` option and flush on SIGTERM: https://runheed.com/for/bun

**Serverless (Vercel, Lambda, Netlify, Cloudflare Workers):** the SDK batches events for up to 5 seconds and the function can freeze as soon as it responds, so `await runheed.flush()` after `captureException` and before returning. Per-platform pages: https://runheed.com/for/vercel, https://runheed.com/for/aws-lambda, https://runheed.com/for/cloudflare-workers

**Render or Railway:** flush on SIGTERM; on Railway also set `RAILWAY_DEPLOYMENT_DRAINING_SECONDS`. See https://runheed.com/for/render and https://runheed.com/for/railway

Errors the code catches and swallows aren't reported on their own: `runheed.captureException(err, { context: 'checkout' })`.

Optional, recommended: `runheed.setAgent({ name: 'claude-code', sessionId: process.env.AGENT_SESSION_ID })` records which agent session shipped the code.

## 4. Verify
Add a temporary route or script that throws, hit it once, and confirm the error appears at https://runheed.com/dashboard/errors. Remove the test code. Worker threads and child processes need their own `init()`.

## 5. Connect the agent
```bash
claude mcp add --transport http runheed https://runheed.com/api/mcp
```
Then `/mcp` > runheed > Authenticate. Cursor: `{"mcpServers": {"runheed": {"url": "https://runheed.com/api/mcp"}}}` in `.cursor/mcp.json`. Other clients: https://runheed.com/connect

Then use the runheed-fix-production-errors skill to work through what it records.
