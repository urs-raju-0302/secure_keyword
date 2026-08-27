# API Design

Base URL (local Compose): `http://localhost:8000`  
API prefix: `/api/v1`  
Interactive docs: `/docs` (OpenAPI), `/redoc`

Related: [ARCHITECTURE.md](ARCHITECTURE.md), [DATABASE_DESIGN.md](DATABASE_DESIGN.md), [DEPLOYMENT.md](DEPLOYMENT.md).

## Conventions

| Topic | Rule |
|-------|------|
| Auth | `Authorization: Bearer <access_jwt>` on protected routes |
| Errors | Generic messages; avoid leaking whether a resource exists to unauthorized users (documents → 404) |
| Secrets | Responses never include DEKs, master/search keys, or password hashes |
| Versioning | `/api/v1` path prefix |
| Content | JSON except multipart upload and binary download |

## Authentication — `/api/v1/auth`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/auth/register` | No | Create USER; password ≥10 chars; Argon2id |
| POST | `/auth/login` | No | Returns `access_token` + `refresh_token` |
| POST | `/auth/refresh` | No | Rotate refresh; new access + refresh |
| POST | `/auth/logout` | Yes | Revoke refresh |
| GET | `/auth/me` | Yes | Current user profile |

### Register request

```json
{ "email": "alice@example.com", "password": "SecurePass99" }
```

### Token response

```json
{
  "access_token": "<jwt>",
  "refresh_token": "<opaque>",
  "token_type": "bearer"
}
```

Access JWT claims (typical): `sub` (user id), `role`, `email`, `type=access`, `iat`, `exp`.

## Documents — `/api/v1/documents`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/documents` | Yes | Multipart file upload → encrypt + index |
| GET | `/documents` | Yes | List own docs (admin: all) |
| GET | `/documents/{id}` | Yes | Metadata if authorized |
| DELETE | `/documents/{id}` | Yes | Delete metadata + best-effort storage object |
| GET | `/documents/{id}/download` | Yes | Decrypt and return file bytes |

### Upload

- Form field: `file`
- Limits: `MAX_UPLOAD_BYTES`, `ALLOWED_CONTENT_TYPES`
- Response: `DocumentResponse` (id, filename, content_type, size_bytes, encryption_algorithm, dek_key_version, created_at)

### Download

- `Content-Type` = original content type  
- `Content-Disposition: attachment; filename="..."`  
- Body = plaintext bytes after successful GCM decrypt  

## Search — `/api/v1/search`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/search` | Yes | Keyword → HMAC token → authorized hits |

### Request

```json
{ "keyword": "security" }
```

### Response

```json
{
  "keyword_normalized_length": 8,
  "result_count": 1,
  "documents": [ { "id": "...", "original_filename": "notes.txt", "...": "..." } ],
  "note": "Search used an HMAC-SHA-256 token; ... Deterministic tokens leak equality..."
}
```

Does **not** return plaintext body or the HMAC token itself.

## Keys (admin) — `/api/v1/keys`

All require `ADMIN` role (else 403).

| Method | Path | Description |
|--------|------|-------------|
| GET | `/keys/status` | Key versions/status |
| POST | `/keys/rotate/search` | Rotate search key + reindex |
| POST | `/keys/rotate/master` | Rotate master version + rewrap DEKs |
| POST | `/keys/reindex` | Rebuild index for active search key |
| POST | `/keys/revoke/{key_type}/{version}` | Revoke non-active key (`MASTER` or `SEARCH`) |

## Audit — `/api/v1/audit`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/audit` | Admin | Recent audit rows (limit 1–500) |
| GET | `/audit/me` | User | Own audit rows (limit 1–200) |

Fields: action, resource_type/id, success, metadata_json (sanitized), timestamps. IP stored as hash only.

## Health

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/health` | No | `{ "status": "ok" }` |

## Middleware / cross-cutting

- **CORS:** allowlist from `CORS_ORIGINS`
- **Security headers:** `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`, `Cache-Control: no-store`
- **Rate limit (educational):** in-memory buckets on login (~10/min) and search (~30/min) per client IP; disabled in `ENVIRONMENT=test`

## Example curl flows

```bash
# Register & login
curl -s -X POST localhost:8000/api/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"demo@example.com","password":"SecurePass99"}'

curl -s -X POST localhost:8000/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"demo@example.com","password":"SecurePass99"}'

# Upload
curl -s -X POST localhost:8000/api/v1/documents \
  -H "Authorization: Bearer $ACCESS" \
  -F file=@notes.txt;type=text/plain

# Search
curl -s -X POST localhost:8000/api/v1/search \
  -H "Authorization: Bearer $ACCESS" \
  -H 'Content-Type: application/json' \
  -d '{"keyword":"security"}'
```

## Frontend consumption

React SPA (`frontend/`) calls these endpoints via Axios (`VITE_API_BASE_URL`). The browser never receives master/search keys—only JWTs and document metadata/plaintext on authorized download.
