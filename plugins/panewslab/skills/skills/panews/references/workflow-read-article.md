# Understand an Article

**Trigger**: The user provides a PANews article link or article ID.

## Identify the Article ID

PANews article URLs typically follow this format: `https://www.panewslab.com/{lang}/{id}`

Examples:
- `https://www.panewslab.com/zh/abc123def`
- `https://panewslab.com/en/abc123def`
- `https://www.panewslab.com/abc123def` (without a language prefix)

Extraction rule: use the last path segment of the URL as the article ID. Ignore the language prefix (`zh`, `en`, `ja`, etc.).
If the user provides a raw ID instead of a URL, use it directly.

## Steps

### 1. Fetch the full article

```bash
node cli.mjs get-article <articleId> --lang <lang>
```

The CLI returns the requested language when available, otherwise the original article. The body is already Markdown; preserve its links, tables, code, and media without another HTML conversion.

### 2. Output structure

- **Core takeaway**: one sentence
- **Main points**: 3 to 5 bullets
- **Key data**: if the article includes numbers or data, explain what they mean instead of just repeating them
- **Why it matters**: what new information or perspective the article provides
