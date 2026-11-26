# NotiBuddy Tool Examples

## 1. Custom Native UI Builder Screen (Inline `screen.template`, Local & Hosted MCP)
Combines status cards, KPI strip, readiness checklist gating the Face ID promote button, and a rollback toggle:
```json
{
  "title": "Promote api-gateway v2.4.1 to production",
  "sensitive": true,
  "screen": {
    "template": {
      "root": {
        "kind": "vstack",
        "spacing": "regular",
        "children": [
          {
            "kind": "card",
            "header": "Canary Telemetry",
            "children": [
              { "kind": "badge", "tone": "success", "label": "Canary Healthy" },
              {
                "kind": "kpiStrip",
                "items": [
                  { "label": "Success", "value": "99.98%" },
                  { "label": "Errors", "value": "0.02%" },
                  { "label": "P95", "value": "41 ms" }
                ]
              },
              {
                "kind": "keyValueList",
                "rows": [
                  { "key": "Commit", "value": "8f3c19a" },
                  { "key": "Environment", "value": "us-east / eu-central" }
                ]
              }
            ]
          },
          {
            "kind": "card",
            "header": "Pre-Flight Gate",
            "children": [
              {
                "kind": "checklist",
                "id": "checks",
                "items": ["Database snapshot verified", "Rollback image pinned"]
              },
              {
                "kind": "formField",
                "id": "reason",
                "fieldType": "text",
                "label": "Release note",
                "placeholder": "Optional deployment note"
              }
            ]
          }
        ]
      },
      "actions": [
        {
          "id": "promote",
          "label": "Promote to production",
          "role": "primary",
          "requireBio": true,
          "enabledWhen": [{ "op": "allChecked", "checklist": "checks" }]
        },
        { "id": "abort", "label": "Abort deploy", "role": "decline", "requireBio": false }
      ]
    }
  }
}
```

## 2. Certified Built-In Screen (`screen.templateId` + `slots`, Local & Hosted MCP)
```json
{
  "title": "Eval run #142 completed",
  "screen": {
    "templateId": "kpi_status_card",
    "slots": {
      "sectionTitle": "Evaluation summary",
      "heading": "Prompt v14 benchmark",
      "badge": "Pass +4.2%",
      "kpis": [
        { "label": "Pass rate", "value": "94.6%" },
        { "label": "P50 latency", "value": "620 ms" }
      ],
      "summary": "Accuracy improved with 18% fewer output tokens.",
      "detailsHeading": "Run details",
      "details": [
        { "key": "Dataset", "value": "agent-eval-500" },
        { "key": "Duration", "value": "11m 42s" }
      ],
      "primaryAction": "Promote v14",
      "secondaryAction": "Keep v13"
    }
  }
}
```

## 3. Face ID Binary Approval
```json
{
  "title": "Deploy v2.4.1 to production?",
  "message": "12 integration tests passed · commit a1b2c3d",
  "options": ["Approve", "Reject"],
  "decline_option": "Reject",
  "requires_auth": true,
  "sensitive": true,
  "timeout_seconds": 600,
  "wait_seconds": 25
}
```

## 4. Resume Pending Request
```json
{
  "resume_id": "req_...",
  "wait_seconds": 25
}
```

## 5. Code Diff Review
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
Approved only when `status === "resolved"`, `answer.action === "approve"`, and `answer.authenticated === true`.

## 6. Live Activity Progress
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

## 7. Collect iPhone Screenshot / File
```json
{ "action": "list" }
```
Then:
```json
{ "action": "receive", "id": "file_0123456789abcdef0123456789abcdef" }
```
