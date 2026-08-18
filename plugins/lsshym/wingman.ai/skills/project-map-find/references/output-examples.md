# Project Map Find Output Examples

Use these examples only when shaping the final response.

## Found Existing Feature

```markdown
Found: Yes

Closest Matches:

- `Product Commission Batch Upload`: Excel upload with row-level validation and invalid-row review before submit.
  - Where: `src/pages/product-commission/import/ProductCommissionImport.tsx`
  - Traits: Excel parsing, row validation, error table, commission API contract
  - Decision: Reference
  - Evidence: `.wingman/project-map/features/product-commission-batch-upload.md`; source checked: `src/pages/product-commission/import/ProductCommissionImport.tsx`

Recommended Next Step:
Use the flow as a precedent, but create a new surface for the new domain.

Gaps:
No utility entry exists yet for the Excel parser. Consider `project-map-catalog` after verification.
```

## No Strong Match

```markdown
Found: No

Closest Matches:

- `Attachment Upload`: simple file upload only.
  - Where: `src/components/AttachmentUpload.tsx`
  - Traits: upload progress and retry, no row-level validation
  - Decision: Avoid
  - Evidence: `.wingman/project-map/components/attachment-upload.md`

Recommended Next Step:
Create a new feature after source search confirms there is no existing batch import flow.

Gaps:
Project map coverage for upload utilities is weak.
```
