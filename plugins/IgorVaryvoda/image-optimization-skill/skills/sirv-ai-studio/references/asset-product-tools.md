# Sirv AI Studio Asset (DAM) & Product (PIM) MCP Tools

Full parameters and semantics for the asset-management and product-catalog tools on the sirv-ai MCP server, verified against the server source (July 2026). Processing tools live in [mcp-tools.md](mcp-tools.md).

Shared conventions:
- Every tool accepts optional `orgId` (UUID); omitted = default organization.
- Schemas are strict — unknown keys are rejected.
- None of these consume credits, with one exception: `sirv_generate_asset_alt_text` runs AI and persists the result.

## Table of Contents

1. [Asset Tools (DAM)](#asset-tools-dam)
2. [Asset Semantics](#asset-semantics)
3. [Product Tools (PIM)](#product-tools-pim)
4. [Product Semantics](#product-semantics)
5. [Destructive Operations](#destructive-operations)

## Asset Tools (DAM)

| Tool | Parameters | Returns |
|------|------------|---------|
| `sirv_list_assets` | `search` (filename), `favorite`, `tags` (comma-sep tag IDs), `folderId` (`'root'` = root), `productId`, `sortBy` (created_at/filename), `sortOrder`, `limit` (1-100, default 20), `offset` | `{assets, total}` |
| `sirv_get_asset` | `id` | Asset |
| `sirv_search_assets` | `q` (required), `limit` (1-50), `offset`, `mimeType`, `sourceTool`, `isFavorite` | `{hits, total, query}` |
| `sirv_find_similar_assets` | `assetId`, `limit` (1-50) | `{results: [{asset, score}], sameOrg}` |
| `sirv_import_asset_url` | `url`, `filename` (must include extension), `fileSize` (bytes) | imported Asset |
| `sirv_update_asset` | `id`, `filename`, `altText`, `isFavorite` | updated Asset |
| `sirv_delete_asset` | `id` | soft-deleted (restorable) |
| `sirv_get_asset_metadata` | `id` | `{metadata: {key: {value, type}}, templateId, template}` |
| `sirv_update_asset_metadata` | `id`, `metadata` (record of `{value, type}`), `templateId` | updated metadata |
| `sirv_generate_asset_alt_text` | `id`, `detailLevel` (caption/detailed-caption/more-detailed-caption, default caption), `model` (default florence) | `{altText}` — **saved to the asset**; uses credits |
| `sirv_bulk_asset_operation` | `assetIds` (1-500), `operation`, `tagIds` (for tag ops), `folderId` (null = root) | `{success, count}` |

Bulk operations: `favorite`, `unfavorite`, `delete`, `restore`, `addTags`, `removeTags`, `moveToFolder`, `copyToFolder`.

## Asset Semantics

- **Asset shape:** id, url, thumbnailUrl, filename, mimeType, width/height, fileSize, altText, isFavorite, source/sourceTool, folderId, tags, timestamps.
- **Two search paradigms:** `sirv_search_assets` is full-text ranked matching over filenames/text fields; `sirv_find_similar_assets` is the visual-similarity index (seed with an asset ID, results ranked by `score`). Visual similarity requires workspace access to that feature — handle "not available" gracefully.
- **Deletes are soft:** single delete and bulk `delete` are restorable via bulk `restore` or the app's trash.
- **Alt text:** `sirv_generate_asset_alt_text` both generates AND saves alt text on the asset (contrast `sirv_alt_text` in mcp-tools.md, which only returns text for an arbitrary URL).
- `sirv_import_asset_url` pulls an external URL into Assets — use it to bring processed outputs (which are result URLs) into the DAM.

## Product Tools (PIM)

| Tool | Parameters | Returns |
|------|------------|---------|
| `sirv_list_products` | `search` (name/SKU), `status` (active/draft/archived), `externalSource` (shopify/woocommerce/manual/csv), `limit` (1-100), `offset`, `sortBy` (createdAt/name/sku/updatedAt), `sortOrder` (default desc) | `{products, total}` |
| `sirv_get_product` | `id` | Product |
| `sirv_search_products` | `q` (1-100 chars, name/SKU, fuzzy), `limit` (1-50) | `{products}` — no total |
| `sirv_create_product` | `sku` (required, unique), `name` (required), `description` (≤5000), `status` (default active), `externalId`, `externalSource`, `externalUrl` | created Product |
| `sirv_update_product` | `id` + any of: `sku`, `name`, `description`, `status`, `brand`, `productCategory`, `productType` (nullable fields clear on `null`), `tags` (≤50) | updated Product |
| `sirv_delete_product` | `id` | **hard delete** |
| `sirv_link_assets_to_product` | `productId`, `assetIds` (1-100), `role` (main/gallery/lifestyle/detail/swatch) | `{linked}` |
| `sirv_list_products_with_assets` | `search`, `limit`, `offset`, `sortBy` (name/createdAt/assetCount, default name), `sortOrder` (default asc), `hideEmpty` (default true) | `{products (with assets[]), total, hasMore}` |
| `sirv_bulk_product_action` | `action`, `productIds` (not needed for deleteAll), `status`, `assetIds` + `role` (for linkAssets), `fields` (for updateFields), `tagMode` (merge/replace, default merge) | action result |

Bulk actions: `delete`, `deleteAll`, `updateStatus`, `linkAssets`, `updateFields`.

## Product Semantics

- **Product shape:** id, sku, name, description, status, brand, productCategory, productType, tags, external linkage (externalId/Source/Url), timestamps. With-assets responses add per-asset `role`, `position`, `variantSku`.
- **Linking is additive:** `sirv_link_assets_to_product` appends (re-linking is a no-op); there is no replace flag and no position parameter — ordering is managed in the app.
- **Field clearing:** `sirv_update_product` nullable fields (`description`, `brand`, `productCategory`, `productType`) clear when passed `null` — don't pass `null` casually.
- **Tags on bulk updateFields:** `tagMode: merge` (default) adds to existing tags; `replace` overwrites the set.
- Query quirks: `sirv_search_products` returns no `total`; `sirv_list_products_with_assets` defaults to name/asc and hides asset-less products (`hideEmpty: true`) — set it false when auditing coverage.

## Destructive Operations

Treat these as requiring explicit user confirmation:

- `sirv_delete_product` and bulk `delete` are **permanent** — there is no restore for products (unlike assets).
- `sirv_bulk_product_action` with `action: "deleteAll"` **ignores `productIds` and hard-deletes every product in the organization**. Never run it without the user explicitly asking for a full catalog wipe, and restate what it will do before calling it.
- Asset deletes are soft, but bulk `delete` on 500 assets is still disruptive — state the count first.
