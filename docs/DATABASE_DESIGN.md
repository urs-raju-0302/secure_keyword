# Database Design

PostgreSQL stores **metadata, wrapped keys, search tokens, and audit**—never plaintext document bodies.

ORM models: `backend/app/models/__init__.py`  
Migrations: `backend/migrations/versions/001_initial.py`  
ER diagram: [diagrams/16-er-diagram.md](diagrams/16-er-diagram.md)

## Entity overview

| Table | Purpose |
|-------|---------|
| `users` | Accounts, Argon2id hashes, roles |
| `documents` | Encrypted-doc metadata + wrapped DEK + nonce |
| `search_index` | HMAC tokens ↔ documents |
| `key_versions` | MASTER/SEARCH version lifecycle |
| `refresh_tokens` | Hashed refresh tokens with rotation |
| `audit_logs` | Security events |

## Tables

### users

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| email | VARCHAR(320) UNIQUE | Indexed; stored lowercased |
| password_hash | VARCHAR(255) | Argon2id |
| role | ENUM-like string | `USER` / `ADMIN` |
| is_active | BOOLEAN | Soft disable |
| created_at / updated_at | TIMESTAMPTZ | |

### documents

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| owner_id | UUID FK → users | Indexed |
| original_filename | VARCHAR(512) | Sanitized basename; also used as GCM AAD |
| content_type | VARCHAR(128) | |
| size_bytes | INT | Plaintext size |
| storage_key | VARCHAR(1024) UNIQUE | Object path in MinIO |
| wrapped_dek | BYTEA | `wrap_nonce ‖ wrapped_dek` |
| dek_key_version | INT | MASTER KEK version used to wrap |
| encryption_algorithm | VARCHAR(64) | `AES-256-GCM` |
| encryption_nonce | BYTEA | 12-byte GCM nonce for document |
| created_at / updated_at | TIMESTAMPTZ | |

**Not stored:** plaintext body, plaintext DEK, keywords.

### search_index

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| document_id | UUID FK → documents ON DELETE CASCADE | |
| keyword_token | VARCHAR(128) | 64-char hex HMAC |
| search_key_version | INT | Ties token to SEARCH key version |
| created_at | TIMESTAMPTZ | |

**Constraints / indexes:**

- UNIQUE `(keyword_token, document_id, search_key_version)`
- INDEX `(keyword_token, search_key_version)` for lookup

### key_versions

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| key_type | `MASTER` / `SEARCH` | |
| version | INT | |
| status | `ACTIVE` / `RETIRED` / `REVOKED` | |
| wrapped_key_material | BYTEA NULL | SEARCH: wrapped key; MASTER: NULL |
| created_at / activated_at / retired_at | TIMESTAMPTZ | |

UNIQUE `(key_type, version)`; INDEX `(key_type, status)`.

### refresh_tokens

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| user_id | UUID FK | |
| token_hash | VARCHAR(128) UNIQUE | SHA-256 of opaque token |
| expires_at | TIMESTAMPTZ | |
| revoked | BOOLEAN | Rotation sets true |
| created_at | TIMESTAMPTZ | |

### audit_logs

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| user_id | UUID NULL FK | |
| action | VARCHAR(64) | Indexed |
| resource_type / resource_id | VARCHAR | Optional |
| success | BOOLEAN | |
| ip_hash | VARCHAR(128) | SHA-256 of IP |
| metadata_json | JSON | Sanitized |
| created_at | TIMESTAMPTZ | Indexed |

## Relationships

```text
users 1──* documents
documents 1──* search_index
users 1──* refresh_tokens
users 1──* audit_logs (nullable user)
key_versions  (standalone lifecycle registry)
```

## Why this schema supports security goals

1. **Separation of ciphertext and metadata** — blobs in object storage; DB holds keys wrapped + index tokens.  
2. **Version columns** — enable search reindex and DEK rewrap without ambiguous crypto context.  
3. **Cascade delete** — removing a document removes its index rows.  
4. **Hashed refresh tokens** — DB leak does not yield raw refresh secrets.  
5. **No keyword plaintext column** — by design.

## Migration & seed

```bash
# From backend with DATABASE_URL set
alembic upgrade head
python -m app.seed   # prints demo credentials once; do not commit secrets
```

Compose typically runs migrations on backend start (see Dockerfile/entrypoint if present).

## Operational notes

- Back up PostgreSQL and MinIO together for restore consistency.  
- DB backups are sensitive (wrapped keys + tokens + hashes)—encrypt backups.  
- Index growth ≈ O(documents × tokens_per_doc); cap per document helps bound abuse.
