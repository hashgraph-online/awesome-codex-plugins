# Independent Apps

Use this model for one V2 frontend that lives in its own ordinary git repository while its workflows, tables, files, configs, and integrations remain live Bifrost resources. Use a Solution instead when those definitions must be packaged, installed, versioned, and reconciled together.

## Source and binding

Create a project and remote App record together:

```bash
bifrost app create operations --name "Operations"
cd operations
npm install
```

The directory is a normal Vite project. Its only Bifrost-specific local state is a gitignored `.env`:

```dotenv
BIFROST_API_URL=https://bifrost.example.com
BIFROST_APP_ID=<uuid>
```

There is no Solution descriptor, `.bifrost` manifest, source YAML, `_repo` App directory, draft, preview, or publish step. A clean clone restores its local binding with:

```bash
bifrost app bind <app-id-or-slug> . --url https://bifrost.example.com
```

Never commit `.env`, access tokens, or refresh tokens.

## Connected development

Run the local App against the selected instance's live platform resources:

```bash
bifrost app start
```

`app start` runs Vite behind an authenticated Bifrost proxy. It does not execute local Python workflows. Workflow refs resolve against the live registered workflows visible to the App and selected organization. Tables, managed files, configs, integrations, and `_repo` modules are live as well; writes are real.

Run `app start` before the first standalone `npm run build` in a clean checkout. Start installs the selected instance's SDK into `node_modules` transiently; it is intentionally absent from the portable `package.json` and git history. Server deploy installs the same instance-matched SDK in its isolated build directory.

App identity and runtime organization scope are separate. The default organization is the current viewer's selected organization. An authorized provider/admin can troubleshoot another organization without rebinding or editing source:

```bash
bifrost app start --org "Customer Org"
```

This override does not bypass App, workflow, table, file, role, policy, or external-user authorization.

## Deploy

Deploy from the bound project root:

```bash
bifrost app deploy
```

The CLI excludes `.env`, ignored files, dependencies, and build output, then uploads source only for the duration of a durable server-side build. The server stores an immutable compiled artifact, atomically activates it, and discards uploaded source. A failed build leaves the previous deployment active.

Deploy changes only the App artifact. It does not capture or mutate live backing resources. Confirm required workflows and policies exist in every organization where the App will run.

## Global and organization-scoped Apps

Choose visibility when creating the remote record:

```bash
bifrost app create operations --org "Customer Org"
bifrost app create shared-portal --global
```

Both forms use the viewer's active organization as runtime data scope. The App record's organization controls visibility; it is not a hardcoded data-scope override. Verify the complete access tuple across the App and every resource it calls.

## Migrate a v1 App

Pull the legacy `_repo/apps/<slug>` source to a local directory, then create an independent V2 project with the deterministic import rewrite:

```bash
bifrost app migrate ./legacy-source ./operations-v2 \
  --name "Operations" --slug operations-v2
```

The command ports pages/components, rewrites v1 platform imports, installs detected UI and browser dependencies, binds the new App, and prints the remaining route/design/access checklist. It does not move backing entities because independent Apps intentionally continue using live resources.

After browser acceptance and deploy, preserve the live URL with an atomic slug swap:

```bash
bifrost app deploy ./operations-v2
bifrost app swap-slugs operations operations-v2
```

The old v1 App remains parked under the temporary slug for rollback. Do not delete it until the V2 App has been verified with realistic users and organizations.

## Acceptance

Before handoff:

- run tests, type checking, and `npm run build`;
- inspect every route through the `app start` proxy, including refresh/deep links;
- verify loading, empty, denied, error, disabled, and success states;
- exercise live workflow, table, and file behavior in the default organization;
- exercise `--org` with an authorized operator and confirm an unauthorized viewer cannot override scope;
- deploy, launch from the Apps UI, and verify the same resource behavior;
- intentionally fail a build once and confirm the previous deployment remains live;
- confirm `.env` and App source are absent from permanent platform storage.
