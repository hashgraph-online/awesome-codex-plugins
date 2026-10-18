# Revise and Resubmit

**Trigger**: The user wants to revise a draft or rejected article and submit it again.

## Steps

### 1. Identify the target article

If the user has not specified the article:

```bash
node cli.mjs list-articles --column-id <id> --status DRAFT --take 20 --session <token>
node cli.mjs list-articles --column-id <id> --status REJECTED --take 20 --session <token>
```

List the results and let the user choose.

### 2. Update the article

Update the relevant fields based on the user's requested changes:

```bash
node cli.mjs update-article \
  --column-id <id> \
  --article-id <id> \
  --title "<new title>" \
  --desc "<new summary>" \
  --content-file <new-content.md> \
  --session <token>
```

Edits save as `DRAFT` unless `--status PENDING` explicitly submits the article for review.

Pass only the fields that need to change.

### 3. Submit for review

Ask whether the user wants to submit it for review immediately:

```bash
node cli.mjs update-article \
  --column-id <id> \
  --article-id <id> \
  --status PENDING \
  --session <token>
```
