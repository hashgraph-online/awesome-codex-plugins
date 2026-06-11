# S3 Environment Integration

Use this reference when wiring Sealos object storage credentials into a development project.

## File Choice

Prefer the project's existing convention:

1. `.env.local` for Next.js and similar local-only app config.
2. `.env` when the repo already uses it for local development and it is ignored by git.
3. Framework-specific files such as `.dev.vars`, `.env.development`, or `apps/*/.env.local` when the code already reads them.
4. `.env.example` only for placeholder documentation. Never write real secrets into example files.

Before writing secrets, verify the file is ignored:

```bash
git check-ignore .env .env.local .env.development .dev.vars
```

If the target file is tracked or not ignored, stop and choose an ignored local env file instead.

## Env Key Mapping

Prefer keys already used by the app.

| App style | Common keys |
| --- | --- |
| Generic S3 | `S3_ENDPOINT`, `S3_ACCESS_KEY_ID`, `S3_SECRET_ACCESS_KEY`, `S3_BUCKET`, `S3_REGION` |
| AWS SDK | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, `AWS_ENDPOINT_URL_S3`, `S3_BUCKET` |
| MinIO-compatible | `MINIO_ENDPOINT`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`, `MINIO_BUCKET` |
| Rails Active Storage S3 | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, `AWS_BUCKET`, `AWS_ENDPOINT` |
| Laravel filesystem S3 | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_DEFAULT_REGION`, `AWS_BUCKET`, `AWS_ENDPOINT`, `AWS_USE_PATH_STYLE_ENDPOINT` |
| Django storages | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_STORAGE_BUCKET_NAME`, `AWS_S3_ENDPOINT_URL`, `AWS_S3_REGION_NAME` |

If multiple keys exist, update the one read by the runtime entry point or storage adapter config. Do not create extra aliases unless the app needs them.

## Values From `sealos-cli s3 secret`

Map fields conservatively:

```text
secret.CONSOLE_ACCESS_KEY -> access key env
secret.CONSOLE_SECRET_KEY -> secret key env
secret.external           -> local laptop endpoint
secret.internal           -> Sealos/Devbox internal endpoint
bucket name               -> bucket env
region                    -> us-east-1
path style                -> true, when the app exposes such a setting
```

`sealos-cli s3` itself uses the AWS SDK with `forcePathStyle: true` and region `us-east-1`. Prefer the same settings when a project asks for region or path-style options.

## Editing Rules

1. Preserve comments, blank lines, and unrelated keys.
2. Replace only the selected keys.
3. If a key exists and has a non-empty value, preserve the old value in chat as "replaced existing local value" without printing it.
4. Quote values only if the project's env files already use quotes or the value contains characters that the loader requires quoted.
5. Never print the full resulting credential set in the final answer.
6. Do not write `CONSOLE_ACCESS_KEY` and `CONSOLE_SECRET_KEY` unless the project already expects those exact names; they are CLI response field names, not generally app env names.

## Bucket and Endpoint Choices

Use a private bucket for app uploads unless the user explicitly wants public reads. Prefer presigned URLs for temporary sharing.

Use `secret.external` for local-machine development and `secret.internal` for apps running inside Sealos/Devbox when that runtime can reach the internal endpoint.

Do not switch a project from local MinIO to Sealos by editing Docker Compose unless the user asks. Updating local env keeps rollback easy.

## Verification

Use the project's own path when available:

- Next.js / Node: run the upload route test, storage service test, or smallest script that calls the configured S3 client.
- Rails: run the Active Storage smoke path or a targeted storage test.
- Django: run a storage backend smoke test or targeted test.
- Generic app: upload a small object, list it, download it to a temp path, then delete the test object.

Fallback CLI smoke test:

```bash
printf 'sealos-s3-smoke\n' > /tmp/sealos-s3-smoke.txt
sealos-cli s3 upload <bucket> /tmp/sealos-s3-smoke.txt --key smoke/sealos-s3-smoke.txt -o json
sealos-cli s3 list <bucket> --prefix smoke/ -o json
sealos-cli s3 download <bucket> smoke/sealos-s3-smoke.txt /tmp/sealos-s3-smoke.out -o json
sealos-cli s3 delete <bucket> smoke/sealos-s3-smoke.txt -o json
```

Do not leave temporary objects behind after verification.
