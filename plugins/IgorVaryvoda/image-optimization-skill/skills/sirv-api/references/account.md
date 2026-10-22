# Sirv API - Account & Stats Reference

## Account Information

**GET** `/v2/account`

```bash
curl "https://api.sirv.com/v2/account" \
  -H "Authorization: Bearer $TOKEN"
```

**Response:**
```json
{
  "alias": "myaccount",
  "cdnURL": "https://myaccount.sirv.com",
  "domains": ["myaccount.sirv.com", "images.mydomain.com"],
  "dateCreated": "2023-01-15T10:00:00Z",
  "fetching": {
    "enabled": true,
    "type": "http",
    "http": {
      "url": "https://origin.example.com"
    }
  },
  "minify": {
    "js": true,
    "css": true
  }
}
```

---

## Update Account Settings

**POST** `/v2/account`

```bash
curl -X POST "https://api.sirv.com/v2/account" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "minify": {"js": true, "css": true},
    "fetching": {
      "enabled": true,
      "type": "http",
      "http": {"url": "https://origin.example.com"}
    }
  }'
```

---

## Storage Usage

**GET** `/v2/account/storage`

```bash
curl "https://api.sirv.com/v2/account/storage" \
  -H "Authorization: Bearer $TOKEN"
```

**Response:**
```json
{
  "used": 5368709120,
  "limit": 10737418240,
  "files": 12500
}
```

---

## API Limits

**GET** `/v2/account/limits`

```bash
curl "https://api.sirv.com/v2/account/limits" \
  -H "Authorization: Bearer $TOKEN"
```

**Response:**
```json
{
  "api": {
    "requests": {
      "used": 5000,
      "limit": 100000,
      "reset": "2024-02-01T00:00:00Z"
    }
  },
  "storage": {
    "used": 5368709120,
    "limit": 10737418240
  },
  "transfer": {
    "used": 21474836480,
    "limit": 107374182400
  }
}
```

---

## Users

**GET** `/v2/account/users`

List all users on the account.

```bash
curl "https://api.sirv.com/v2/account/users" \
  -H "Authorization: Bearer $TOKEN"
```

**GET** `/v2/account/users/{userId}`

Get specific user details.

---

## Statistics

### HTTP Transfer Stats

**GET** `/v2/stats/http`

```bash
curl "https://api.sirv.com/v2/stats/http?from=2024-01-01&to=2024-01-31" \
  -H "Authorization: Bearer $TOKEN"
```

**Response:**
```json
{
  "stats": [
    {
      "date": "2024-01-15",
      "transfer": 1073741824,
      "requests": 50000
    }
  ]
}
```

### Storage Stats

**GET** `/v2/stats/storage`

```bash
curl "https://api.sirv.com/v2/stats/storage?from=2024-01-01&to=2024-01-31" \
  -H "Authorization: Bearer $TOKEN"
```

### Spin View Stats

**POST** `/v2/stats/spins/views`

Get spin view counts (max 5 day range).

```bash
curl -X POST "https://api.sirv.com/v2/stats/spins/views" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "/spins/product.spin",
    "from": "2024-01-10",
    "to": "2024-01-15"
  }'
```

---

## Billing

**GET** `/v2/billing/plan`

```bash
curl "https://api.sirv.com/v2/billing/plan" \
  -H "Authorization: Bearer $TOKEN"
```

**Response:**
```json
{
  "name": "Business",
  "storage": {
    "included": 107374182400,
    "price": 0.02
  },
  "transfer": {
    "included": 536870912000,
    "price": 0.04
  }
}
```

---

## Account Events

### List Events

**GET** `/v2/account/events`

```bash
curl "https://api.sirv.com/v2/account/events?type=error&from=0&size=50" \
  -H "Authorization: Bearer $TOKEN"
```

**Query parameters:**
- `type`: error, warning, info
- `module`: filter by module
- `filename`: filter by filename
- `from`, `size`: pagination

### Search Events

**POST** `/v2/account/events/search`

```bash
curl -X POST "https://api.sirv.com/v2/account/events/search" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "type:error AND module:upload",
    "from": 0,
    "size": 50
  }'
```

### Mark Events as Seen

**POST** `/v2/account/events/seen`

```bash
curl -X POST "https://api.sirv.com/v2/account/events/seen" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"ids": ["event_id_1", "event_id_2"]}'
```

---

## Folder Options

**GET** `/v2/files/options?dirname={path}`

Get folder-specific settings.

```bash
curl "https://api.sirv.com/v2/files/options?dirname=/products" \
  -H "Authorization: Bearer $TOKEN"
```

**POST** `/v2/files/options?dirname={path}`

Set folder options.

```bash
curl -X POST "https://api.sirv.com/v2/files/options?dirname=/products" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "scanSpins": true,
    "spinNamePattern": "{name}.spin",
    "allowListing": false
  }'
```

**Options:**
- `scanSpins`: Auto-detect 360 spins in folder
- `spinNamePattern`: Naming pattern for generated spins
- `allowListing`: Allow public directory listing
- `locked`: Lock folder (Enterprise only)
