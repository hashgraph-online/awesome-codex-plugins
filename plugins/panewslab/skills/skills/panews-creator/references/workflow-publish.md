# Publish a New Article

**Trigger**: User wants to publish an article to PANews.

## Steps

### 0. (Optional) Pre-publish research

If the panews skill is installed, search for similar articles before publishing to help the user find a differentiated angle:

```bash
node {panews}/scripts/cli.mjs search-articles "<article topic>" --take 3
```

Skip this step if panews is not installed.

### 1. Verify identity and confirm column

```bash
node cli.mjs validate-session --session <token>
```

From the result, pick the column:
- Only 1 column → use it by default, inform the user
- Multiple columns → list them for the user to choose
- No column → explain that one must be applied for first; see [workflow-apply-column](./workflow-apply-column.md)

### 2. Collect article info

Confirm the following fields with the user (skip if already provided):

| Field | Required | Notes |
|-------|----------|-------|
| Title | Yes | Recommended under 20 characters |
| Summary | Yes | 50–100 characters |
| Body | Yes | Path to a non-empty Markdown file; sent directly |
| Cover image | Recommended | Upload local images first, or provide a CDN URL |
| Tags | No | Up to 5 tag IDs |
| Language | Yes | Language of the article, e.g. zh or en |

Do not generate body content on behalf of the user. If they only have a topic, ask whether the body is already written.

### 3. Handle cover image (if local file)

```bash
node cli.mjs upload-image <file-path> --session <token>
```

Use the returned URL as the `--cover` value.

### 4. Handle tags (optional)

```bash
node cli.mjs search-tags "<keyword>"
```

Show results for the user to select tag IDs. Unlike write operations, this tag lookup does not require a session token.

### 5. Create article (save as draft first)

```bash
node cli.mjs create-article \
  --column-id <id> \
  --title "<title>" \
  --desc "<summary>" \
  --content-file <file.md> \
  --lang <lang> \
  --cover <url> \
  --tags <id1,id2> \
  --status DRAFT \
  --session <token>
```

### 6. Confirm and submit

Show a summary (title, summary, tags, column), then ask:
- Submit for review now → call `create-article --status PENDING`, or `update-article --status PENDING`
- Save as draft → done, inform the user of the article ID
