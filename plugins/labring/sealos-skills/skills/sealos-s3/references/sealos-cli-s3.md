# sealos-cli S3 Reference

Use `sealos-cli s3` as the execution layer for Sealos object storage work. This reference is based on `zjy365/sealos-cli#28` (`feat: add s3 object storage commands`), which registered `s3` in `src/main.ts` and implemented it in `src/commands/s3/index.ts`.

## Install and Auth

Prefer an existing binary:

```bash
sealos-cli --version
sealos-cli whoami
sealos-cli s3 --help
```

Use one-off execution when the binary is missing:

```bash
npx -y sealos-cli@latest s3 --help
```

Authenticate and choose the workspace:

```bash
sealos-cli login https://usw-1.sealos.io
sealos-cli workspace list
sealos-cli workspace switch <workspace-id-or-team-name>
sealos-cli workspace current
```

`sealos-cli s3` reads the active kubeconfig and uses the current context namespace. If the context has no namespace, the CLI tells the user to run `sealos-cli login` or `sealos-cli workspace switch`.

## Implementation Model

Bucket and credential commands talk to Kubernetes custom resources in the active namespace:

- `ObjectStorageBucket` in API group `objectstorage.sealos.io/v1`
- `ObjectStorageUser` in API group `objectstorage.sealos.io/v1`

The object storage user name is derived from the namespace by removing a leading `ns-`. For example, namespace `ns-private` maps to user `private`.

Object operations use the AWS SDK S3 client against the S3-compatible endpoint returned in `ObjectStorageUser.status.external`, with `forcePathStyle: true` and region `us-east-1`.

## Bucket Names and Policies

Bucket CR names are stored without the workspace prefix. Formatted bucket names include the namespace-derived prefix:

```text
namespace ns-private + CR name assets -> bucket name private-assets
```

The CLI accepts either the displayed bucket name or the CR name for bucket CRD operations and normalizes away the namespace prefix.

Supported canonical policies:

- `private`
- `publicRead`
- `publicReadwrite`

Accepted aliases include `readonly`, `read`, `public-read`, `readwrite`, `read-write`, `public-readwrite`, and `public-read-write`. Do not use `public`; the PR tests require it to fail.

## Bucket Commands

Use JSON for automation:

```bash
sealos-cli s3 buckets -o json
sealos-cli s3 create-bucket <name> --policy private -o json
sealos-cli s3 get-bucket <name> -o json
sealos-cli s3 update-bucket <name> --policy publicRead -o json
sealos-cli s3 delete-bucket <name> -o json
```

Aliases:

```bash
sealos-cli s3 list-buckets -o json
sealos-cli s3 rm-bucket <name> -o json
```

`create-bucket` updates the policy if the bucket already exists. Ask before changing a bucket from `private` to `publicRead` or `publicReadwrite`.

Formatted bucket output includes:

```json
{
  "name": "private-assets",
  "crName": "assets",
  "policy": "private",
  "isComplete": true,
  "createdAt": "2026-05-27T00:00:00Z",
  "uid": "bucket-uid"
}
```

`buckets -o json` wraps the list as `{ "list": [...] }`.

## Credentials and Quota

Initialize or read credentials:

```bash
sealos-cli s3 secret -o json
```

JSON shape:

```json
{
  "secret": {
    "CONSOLE_ACCESS_KEY": "<access-key>",
    "CONSOLE_SECRET_KEY": "<secret-key>",
    "internal": "<internal-endpoint>",
    "external": "<external-endpoint>",
    "specVersion": 0,
    "version": 0
  }
}
```

Treat every field in `secret` as sensitive except endpoint hostnames. Do not print the access key or secret key in final answers.

Rotate credentials:

```bash
sealos-cli s3 rotate-secret -o json
```

The response is asynchronous:

```json
{
  "success": true,
  "action": "rotate-secret",
  "resource": "s3-user",
  "name": "<object-storage-user>",
  "specVersion": 123456789,
  "status": "updating"
}
```

After rotation, rerun `sealos-cli s3 secret -o json` and update dependent env values only after the new status is ready.

Check quota:

```bash
sealos-cli s3 quota -o json
```

Response shape:

```json
{
  "quota": {
    "total": 10737418240,
    "used": 1024,
    "count": 1
  }
}
```

Fields can be `null` if status is not populated.

## Object Commands

Object commands initialize Sealos credentials automatically unless all three overrides are provided:

```bash
--endpoint <url>
--access-key <key>
--secret-key <key>
```

Provide all three override flags together or none.

List objects:

```bash
sealos-cli s3 list <bucket> --prefix images/ --delimiter / --max-keys 100 --token <continuation-token> -o json
```

`--max-keys` must be a positive integer. JSON output:

```json
{
  "prefixes": ["images/"],
  "objects": [
    {
      "key": "images/logo.png",
      "size": 1234,
      "lastModified": "2026-05-27T00:00:00.000Z",
      "eTag": "\"etag\"",
      "storageClass": null
    }
  ],
  "isTruncated": false,
  "nextContinuationToken": null
}
```

Upload:

```bash
sealos-cli s3 upload <bucket> <file> --key <object-key> --content-type image/png -o json
```

If `--key` is omitted, the CLI uses the local file path as the object key. Prefer passing an explicit key for reproducible app assets.

Download:

```bash
sealos-cli s3 download <bucket> <key> <file> -o json
```

Delete an object:

```bash
sealos-cli s3 delete <bucket> <key> -o json
sealos-cli s3 rm <bucket> <key> -o json
```

Presign:

```bash
sealos-cli s3 presign <bucket> <key> --expires 3600 --method get -o json
sealos-cli s3 presign <bucket> <key> --expires 3600 --method put -o json
```

`--expires` must be a positive integer. `--method` must be `get` or `put`.

## Response Handling

Every registered action command defaults `-o, --output` to `json` in PR #28. Keep using JSON for automation and table only for human inspection.

Credential initialization and rotation are asynchronous around `ObjectStorageUser.status`. If `s3 secret` says the user secret is not ready, retry after a few seconds. If `rotate-secret` returns `status: "updating"`, poll `s3 secret` before updating applications.

## PR #28 Evidence Points

The PR tests assert:

- Top-level help exposes `s3`.
- `s3 --help` documents `create-bucket`, `rotate-secret`, and `presign`.
- Subcommands are `buckets`, `create-bucket`, `get-bucket`, `update-bucket`, `delete-bucket`, `secret`, `rotate-secret`, `quota`, `list`, `upload`, `download`, `delete`, and `presign`.
- Aliases are `list-buckets`, `rm-bucket`, and `rm`.
- All action commands default to JSON output.
- `public` is not a supported bucket policy alias.
