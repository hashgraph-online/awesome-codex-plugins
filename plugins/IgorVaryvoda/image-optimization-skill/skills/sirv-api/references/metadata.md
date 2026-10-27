# Sirv API - Metadata & Search Reference

## Get All Metadata

**GET** `/v2/files/meta?filename={path}`

```bash
curl "https://api.sirv.com/v2/files/meta?filename=/images/photo.jpg" \
  -H "Authorization: Bearer $TOKEN"
```

**Response:**
```json
{
  "title": "Product Shot",
  "description": "Main product image",
  "tags": ["product", "featured"],
  "product": {
    "id": "SKU-123",
    "name": "Blue Widget",
    "brand": "Acme",
    "category1": "Widgets",
    "category2": "Blue"
  },
  "approval": {
    "approved": true,
    "comment": "Ready for production"
  }
}
```

---

## Set Multiple Metadata Fields

**POST** `/v2/files/meta?filename={path}`

```bash
curl -X POST "https://api.sirv.com/v2/files/meta?filename=/images/photo.jpg" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Product Shot",
    "description": "Main product image",
    "tags": ["product", "featured"]
  }'
```

---

## Individual Metadata Fields

### Title

```bash
# Get
curl "https://api.sirv.com/v2/files/meta/title?filename=/images/photo.jpg" \
  -H "Authorization: Bearer $TOKEN"

# Set
curl -X POST "https://api.sirv.com/v2/files/meta/title?filename=/images/photo.jpg" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "New Title"}'
```

### Description

```bash
# Get
curl "https://api.sirv.com/v2/files/meta/description?filename=/images/photo.jpg" \
  -H "Authorization: Bearer $TOKEN"

# Set
curl -X POST "https://api.sirv.com/v2/files/meta/description?filename=/images/photo.jpg" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"description": "Product description text"}'
```

### Tags

```bash
# Get
curl "https://api.sirv.com/v2/files/meta/tags?filename=/images/photo.jpg" \
  -H "Authorization: Bearer $TOKEN"

# Add tags
curl -X POST "https://api.sirv.com/v2/files/meta/tags?filename=/images/photo.jpg" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"tags": ["new-tag", "another-tag"]}'

# Remove tags
curl -X DELETE "https://api.sirv.com/v2/files/meta/tags?filename=/images/photo.jpg" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"tags": ["tag-to-remove"]}'
```

### Product Metadata

```bash
# Get
curl "https://api.sirv.com/v2/files/meta/product?filename=/images/photo.jpg" \
  -H "Authorization: Bearer $TOKEN"

# Set
curl -X POST "https://api.sirv.com/v2/files/meta/product?filename=/images/photo.jpg" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "SKU-123",
    "name": "Blue Widget",
    "brand": "Acme",
    "category1": "Widgets",
    "category2": "Blue"
  }'
```

### Approval Status

```bash
# Get
curl "https://api.sirv.com/v2/files/meta/approval?filename=/images/photo.jpg" \
  -H "Authorization: Bearer $TOKEN"

# Set
curl -X POST "https://api.sirv.com/v2/files/meta/approval?filename=/images/photo.jpg" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"approved": true, "comment": "Approved by John"}'
```

---

## File Search

**POST** `/v2/files/search`

```bash
curl -X POST "https://api.sirv.com/v2/files/search" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "extension:.jpg AND mtime:[now-30d TO now]",
    "size": 50
  }'
```

**Request Body:**
```json
{
  "query": "search expression",
  "sort": {"mtime": "desc"},
  "from": 0,
  "size": 50,
  "scroll": false
}
```

**Response:**
```json
{
  "hits": [
    {
      "filename": "/images/photo.jpg",
      "mtime": "2024-01-15T10:30:00Z",
      "size": 245678,
      "contentType": "image/jpeg"
    }
  ],
  "total": 150,
  "scrollId": "scroll_token_if_scroll_enabled"
}
```

### Search Query Syntax

**Field searches:**
```
filename:photo.jpg
dirname:/images
extension:.jpg
basename:photo
contentType:image/jpeg
isDirectory:false
```

**Date ranges:**
```
mtime:[now-7d TO now]           # Modified in last 7 days
ctime:[2024-01-01 TO 2024-12-31] # Created in 2024
mtime:[now-1h TO now]           # Modified in last hour
```

**Size ranges:**
```
size:[0 TO 1000000]             # Up to 1MB
size:[1000000 TO *]             # Larger than 1MB
```

**Metadata fields:**
```
meta.title:product
meta.description:widget
meta.tags:featured
meta.product.id:SKU-123
meta.product.brand:Acme
meta.approval.approved:true
```

**Operators:**
```
AND    # Both conditions
OR     # Either condition
NOT    # Exclude
-      # Exclude (prefix)
*      # Wildcard
```

**Examples:**
```
# JPEGs modified this week, not in trash
extension:.jpg AND mtime:[now-7d TO now] AND -dirname:/.Trash

# Images with product metadata
meta.product.id:* AND contentType:image/*

# Large files
size:[10000000 TO *] AND extension:.jpg

# Approved product images
meta.approval.approved:true AND meta.product.brand:Acme
```

### Search with Scrolling (>1000 results)

```bash
# Initial search with scroll enabled
curl -X POST "https://api.sirv.com/v2/files/search" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "extension:.jpg", "size": 100, "scroll": true}'

# Continue with scroll ID
curl -X POST "https://api.sirv.com/v2/files/search/scroll" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"scrollId": "scroll_token_from_previous_response"}'
```
