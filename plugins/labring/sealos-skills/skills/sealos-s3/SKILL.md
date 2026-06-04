---
name: sealos-s3
description: Provision, connect, and operate Sealos object storage through the sealos-cli s3 commands added in zjy365/sealos-cli#28. Use when the user needs S3-compatible storage for uploads, assets, backups, presigned URLs, bucket policy management, access credentials, quota checks, or wants to replace local MinIO/S3-compatible services with Sealos object storage in local development, Devbox, or app setup.
---

# Sealos S3

Use this skill to give a project real Sealos object storage through `sealos-cli s3`. The default outcome is: identify the app's object-storage need, create or reuse a bucket, initialize credentials only when needed, wire the smallest safe set of local env vars, and verify the project's upload/download or presigned URL path.

This skill is grounded in `zjy365/sealos-cli#28`, which registered the `s3` command and implemented bucket CRD operations plus S3-compatible object operations.

## Safety Rules

1. Never print secret keys, full S3 credential blocks, or copied env values in the final answer.
2. Do not overwrite an existing env value without confirming or preserving the old value.
3. Do not commit `.env`, `.env.local`, S3 access keys, secret keys, kubeconfig, or Sealos auth files.
4. Ask before making a bucket public. Default bucket policy is `private`.
5. Ask before destructive operations: `s3 delete-bucket`, `s3 delete`, credential rotation for an active app, or replacing app storage configuration.
6. Use JSON output from `sealos-cli` by default and parse it instead of scraping table output.
7. Treat `s3 secret` output as sensitive even though the CLI can print it.

## Workflow

### 1. Resolve the target project

Confirm the working directory with `pwd` or `git rev-parse --show-toplevel`.

Run the analyzer when a project directory is available:

```bash
node <SKILL_DIR>/scripts/analyze-project-s3.mjs <project-dir>
```

Use the analyzer result as a starting point, then inspect the real files it cites before editing anything. It intentionally avoids printing secret values.

### 2. Check `sealos-cli`

Prefer an existing `sealos-cli` binary:

```bash
sealos-cli --version
sealos-cli s3 --help
sealos-cli whoami
```

If it is not installed, use `npx -y sealos-cli@latest ...` for one-off commands. Ask before installing it globally.

If auth is missing or expired, run:

```bash
sealos-cli login <region>
sealos-cli workspace list
sealos-cli workspace current
```

Use the workspace the user expects. If multiple workspaces exist and the target is ambiguous, ask before provisioning. `sealos-cli s3` derives the object-storage user from the active kubeconfig namespace, so a wrong workspace means wrong buckets and credentials.

### 3. Choose create or reuse

List existing buckets first:

```bash
sealos-cli s3 buckets -o json
```

Reuse an existing bucket when its purpose and policy match. Create a new one when the project has no suitable bucket or the user asks for a fresh bucket:

```bash
sealos-cli s3 create-bucket <bucket-name> --policy private -o json
```

Use `private` unless the user explicitly needs public reads or writes. Bucket policies accepted by the PR are `private`, `publicRead`, and `publicReadwrite`; aliases such as `public-read` normalize to `publicRead`, but use canonical values in instructions and scripts.

### 4. Initialize credentials only when needed

For app env wiring or object operations, fetch credentials:

```bash
sealos-cli s3 secret -o json
```

The command creates the `ObjectStorageUser` if it does not exist, then waits briefly for status. If credentials are not ready, retry after a few seconds instead of creating raw CRDs by hand.

Use `references/sealos-cli-s3.md` for the current command contract and response handling.

### 5. Wire the development environment

Map only the keys the project already uses. Common targets:

| Project signal | Preferred env keys |
| --- | --- |
| AWS SDK / S3 generic | `S3_ENDPOINT`, `S3_ACCESS_KEY_ID`, `S3_SECRET_ACCESS_KEY`, `S3_BUCKET` |
| AWS-style config | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, `S3_BUCKET` |
| MinIO replacement | existing `MINIO_*` keys or migrate to existing S3 keys only if the app supports them |
| Upload libraries | the keys read by the adapter/config file |

Use endpoint from `secret.external` for local laptop development. Use `secret.internal` only when the app runs inside Sealos/Devbox and the runtime can reach the internal endpoint.

Read `references/env-integration.md` before editing env files.

### 6. Verify application storage behavior

Run the smallest real project path that proves object storage works:

1. Run a repo script or test that uploads and reads an object if available.
2. Otherwise upload a small local test file with `sealos-cli s3 upload`, list it, download it to a temp path, and delete the test object.
3. For presigned URL features, run `sealos-cli s3 presign <bucket> <key> --expires 3600 -o json` and verify the URL only when that is part of the requested workflow.

Use `--endpoint`, `--access-key`, and `--secret-key` together only when connecting to a non-Sealos S3-compatible endpoint. Do not mix partial overrides.

### 7. Report the result

Summarize:

1. Bucket name, policy, region/workspace, and readiness.
2. Env file and keys updated, without revealing secret values.
3. Verification command and outcome.
4. Any public policy, credential rotation, or cleanup follow-up.

## Common Tasks

### Connect an existing project to Sealos object storage

1. Run the analyzer.
2. Inspect the env/config files it cites.
3. List existing buckets.
4. Create or reuse the matching bucket.
5. Fetch credentials with `s3 secret`.
6. Write only the env keys the app reads.
7. Verify the app's storage path.

### Replace local MinIO for development

1. Identify the app service env vars that point at MinIO or an S3-compatible service.
2. Create or reuse a private Sealos bucket.
3. Update only the app's local env file, not the compose file, unless the user asks to remove MinIO.
4. Keep local Compose rollback simple: the original MinIO service remains available.

### Upload or share project assets

1. Confirm the target bucket and object key prefix.
2. Upload with `sealos-cli s3 upload <bucket> <file> --key <key> -o json`.
3. Use `presign` for temporary sharing instead of public bucket policy when possible.
4. Delete temporary test objects after verification.

## References

- `scripts/analyze-project-s3.mjs` - read-only project object-storage intent analyzer.
- `references/sealos-cli-s3.md` - PR #28 `sealos-cli s3` command contract.
- `references/env-integration.md` - safe env-file editing and S3 env-key mapping.
