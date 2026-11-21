# NotiBuddy Tool Examples

## Custom Native Screen (Deployment Gate)
```json
{
  "title": "Promote v2.4.1 to production",
  "screen": {
    "template": {
      "root": {
        "kind": "vstack",
        "children": [
          { "kind": "alert", "severity": "success", "title": "Canary healthy", "body": "128/128 checks passed across us-east and eu-central." },
          { "kind": "kpiStrip", "items": [{ "label": "Canary", "value": "10%" }, { "label": "Errors", "value": "0.00%" }] }
        ]
      },
      "actions": [
        { "id": "promote", "label": "Promote to production", "role": "primary", "requireBio": true },
        { "id": "abort", "label": "Abort deploy", "role": "destructive", "requireBio": false }
      ]
    }
  },
  "wait_seconds": 55
}
```

## Face ID Deployment Approval
```json
{
  "title": "Deploy v2.4.1 to production?",
  "message": "12 integration tests passed · commit a1b2c3d",
  "options": ["Approve", "Reject"],
  "decline_option": "Reject",
  "requires_auth": true,
  "sensitive": true,
  "timeout_seconds": 600,
  "wait_seconds": 55
}
```

## Resume Pending Request
```json
{
  "resume_id": "req_...",
  "wait_seconds": 55
}
```

## Code Diff Review
```json
{
  "title": "Review auth timeout change",
  "diff": {
    "filename": "src/auth.ts",
    "language": "typescript",
    "original": "const ttl = 300;\n",
    "modified": "const ttl = 600;\n"
  },
  "requires_auth": true,
  "sensitive": true
}
```
Approved only when `status === "resolved"` and `answer.action === "approve"` (plus `answer.authenticated === true`).

## Live Activity Progress
```json
{
  "id": "build-release",
  "action": "start",
  "title": "Release Build",
  "status": "Running test suite",
  "step": 1,
  "total_steps": 4
}
```

## Collect iPhone Screenshot / File
```json
{ "action": "list" }
```
Then:
```json
{ "action": "receive", "id": "file_0123456789abcdef0123456789abcdef" }
```
