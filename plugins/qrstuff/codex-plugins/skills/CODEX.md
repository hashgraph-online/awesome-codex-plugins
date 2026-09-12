# QRStuff AI Assistant Skills & Instructions for OpenAI Codex

This document provides system instructions for OpenAI Codex on how to use the QRStuff MCP server tools and render the responses to the user.

---

## 1. What is QRStuff MCP Server?

The QRStuff MCP server exposes tools to interact with the QRStuff platform. You can generate QR codes, manage projects, retrieve scan analytics, restore deleted assets, and perform customer support tasks.

---

## 2. Core Tool Groups

### A. QR Code Management

- `generate_qr_code`: Use this to create a new QR code (e.g. URL, TEXT, SMSTO, EMAIL). Always check if styled is required. For custom logos/backgrounds, use `upload_file` first to get a file ID, then pass it to this tool.
- `get_qr_code_by_id`: Retrieve detail fields for a specific QR code by ID.
- `update_qr_code`: Update content, format, styling, or shapes of an existing QR code. _Note: Retrieve it first using `get_qr_code_by_id`, merge edits, and pass the updated payload._
- `list_qrcodes`: Retrieve a paginated list of QR codes.

### B. Project Management

- `list_projects`: Retrieve all active user projects.
- `list_deleted_projects`: Retrieve deleted projects that can be restored.
- `restore_deleted_project`: Restore a project to active state.

### C. File Uploads

- `upload_file`: Upload a base64 encoded image asset (logo, foreground, or background) for QR code customization. Returns a file ID.

### D. Analytics

- `get_total_scans` & `get_unique_users`: Get total scan events or unique scanning users over a date range.
- `get_top_performing_date` & `get_top_performing_location`: Find the date or country with the highest scan count.
- `get_project_scans` & `get_qrcode_scans`: Retrieve paginated event-level scan logs.

---

## 3. Rendering Prefab UI Components

The QRStuff MCP server returns responses structured using the **`prefab-ui`** layout schema (e.g. `Column`, `Row`, `DataTable`, `BarChart`, `Heading`, `Text`, `Image`, `Button`).

When displaying these responses to the user, **do not print the raw JSON**. Format them into clean, human-friendly markdown interfaces:

- **DataTable:** Render as a standard GitHub Markdown table with clear headers.
- **BarChart:** Represent scan statistics in a clean list or markdown visual structure.
- **Heading:** Use markdown headers (`###` or `####`).
- **Image:** Render inline using standard markdown syntax: `![alt](src)`.
- **Button:** Render as inline links or bullet points showing action options: `[label](url)`.
- **Column & Row:** Lay out the nested elements sequentially, grouping related row elements together.

---

## 4. Troubleshooting & Authentication

If a tool returns an authentication error (e.g., `Authentication required`), explain to the user that the server expects an active OAuth 2.1 authentication flow or a valid `QRSTUFF_ACCESS_TOKEN` set in the environment variables.
