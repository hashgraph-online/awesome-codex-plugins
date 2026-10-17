# Input Validation And Injection Defense

## Source-To-Sink Map

| Source | Trust Boundary | Sink | Data Class | Owner |
| --- | --- | --- | --- | --- |

## Per-Sink Control Matrix

| Source | Sink | Boundary Validation | Sink-Correct Defense | Verification Case |
| --- | --- | --- | --- | --- |

## Structured Input Binding

| Payload | Schema/Allowlist | Bound Fields | Rejected Fields | Failure Response |
| --- | --- | --- | --- | --- |

## File Upload Handling

| Upload | Authorization | Extension/Signature Check | Size/Post-Decompression Limit | File Count/Aggregate Quota | Archive/Decompression And Nesting/Parser-Work Bound | Quarantine/Scan/CDR | Storage Path Rule | Generated Name | Atomic Promotion | Safe Serving |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

## File And Path Resolution

| Operation | Allowed Root | Symlink/Hardlink Rule | Race-Safe Resolution | Archive Traversal Rule | Negative Test |
| --- | --- | --- | --- | --- | --- |

## Negative Test Plan

| Sink | Malicious Input | Expected Neutralization | Blocking Stage |
| --- | --- | --- | --- |

## Residual Risk

| Sink | Residual Risk | Compensating Control | Owner | Expiry |
| --- | --- | --- | --- | --- |
