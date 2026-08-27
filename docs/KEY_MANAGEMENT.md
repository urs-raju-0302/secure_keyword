# Key Management

How keys are generated, stored, versioned, rotated, and revoked in Secure Keyword Search.

Related: [ARCHITECTURE.md](ARCHITECTURE.md), [SEARCHABLE_ENCRYPTION.md](SEARCHABLE_ENCRYPTION.md), [diagrams/10-key-lifecycle.md](diagrams/10-key-lifecycle.md), [diagrams/11-key-hierarchy.md](diagrams/11-key-hierarchy.md).

## Design goals

1. **Never** store plaintext DEKs or search keys in PostgreSQL.
2. Use **envelope encryption**: unique DEK per document; wrap under a KEK derived from master material.
3. Keep the **search key** cryptographically separate from DEKs/KEKs.
4. Support **versioning**, **rotation**, and **revocation** with audit events.
5. Be honest: env-based `MASTER_KEY` is **not** equivalent to AWS KMS / Vault / HSM.

## Key hierarchy

```text
MASTER_KEY (env secret, 32+ bytes / urlsafe base64)
    │
    ├─ HKDF-SHA256(info="dek-wrap:v{N}", salt=fixed) → KEK_vN
    │       └─ AES-256-GCM wrap → wrapped DEK (stored on document row)
    │               └─ DEK_doc → AES-256-GCM(document bytes)
    │
    └─ HKDF-SHA256(info="search-key-wrap:v{M}", ...) → search-wrap KEK
            └─ wraps SearchKey_vM (random 32 bytes)
                    └─ HMAC-SHA-256(SearchKey_vM, keyword) → index token
```

| Key | Length | Lifetime | Storage |
|-----|--------|----------|---------|
| `MASTER_KEY` | ≥32 bytes | Long-lived secret | Environment / secrets manager (demo: `.env`) |
| KEK_vN | 32 bytes derived | Per master version | Not stored (derived on demand) |
| DEK | 32 bytes random | Per document | Only wrapped (`documents.wrapped_dek`) |
| Search key | 32 bytes random | Per search version | Wrapped in `key_versions.wrapped_key_material` |
| JWT secret | ≥32 bytes | Long-lived | Environment (separate from master) |

## Master key material

- Loaded by `KeyManagementService` from `Settings.master_key`.
- Accepts urlsafe base64 (≥32 decoded bytes) or UTF-8 secret ≥32 characters.
- Rejects placeholders starting with `CHANGE_ME`.
- **MASTER** rows in `key_versions` track version/status only; they do **not** store the master secret.

### Educational “master rotation”

`rotate_master_key()` increments the MASTER version and retires the previous ACTIVE row. KEKs change because HKDF info includes the version (`dek-wrap:v{N}`). Existing documents are **re-wrapped** by `KeyRotationService.rotate_master_and_rewrap` without changing ciphertext blobs.

**Limitation:** the underlying env `MASTER_KEY` string typically stays the same in this educational build. Production should introduce new root secret material in KMS and re-wrap under a new CMK.

## Document DEK lifecycle

1. **Generate:** `secrets`/`os.urandom` 32 bytes (`generate_document_key`).
2. **Use once** to AES-GCM-encrypt the document (unique nonce).
3. **Wrap** under active master version; store `nonce‖ciphertext` + `dek_key_version`.
4. **Discard** plaintext DEK from memory after the request (GC; not formally zeroized).
5. **Unwrap** on download or reindex/rewrap paths only after authorization (download) or admin job (rotation).

## Search key lifecycle

1. Bootstrap creates SEARCH v1: random key → wrap → ACTIVE.
2. Upload/search use `get_search_key()` for the ACTIVE version.
3. **Rotate + reindex** (`POST /api/v1/keys/rotate/search`):
   - Capture old key/version
   - Create new SEARCH version (old → RETIRED)
   - For each document: decrypt → extract keywords → write new tokens under new version → delete old-version rows
   - Audit `KEY_ROTATION`
4. **Reindex only** rebuilds tokens for the current ACTIVE search key (admin).
5. **Revoke** retires non-ACTIVE versions to REVOKED (cannot revoke ACTIVE; rotate first).

## Status machine

```text
ACTIVE ──rotate──► RETIRED ──revoke──► REVOKED
                      ▲
                      └── still unwrappable for migration where implemented
```

Revoked search keys must not be used for new searches (`get_search_key(version=...)` rejects REVOKED).

## API surface (admin)

| Endpoint | Effect |
|----------|--------|
| `GET /api/v1/keys/status` | List type/version/status timestamps (no key bytes) |
| `POST /api/v1/keys/rotate/search` | New search key + full reindex |
| `POST /api/v1/keys/rotate/master` | New master version + DEK rewrap |
| `POST /api/v1/keys/reindex` | Rebuild index for active search key |
| `POST /api/v1/keys/revoke/{key_type}/{version}` | Mark REVOKED |

Details: [API_DESIGN.md](API_DESIGN.md).

## Compromise scenarios

| Compromised secret | Impact | Response |
|--------------------|--------|----------|
| Single DEK | One document | Re-upload / re-encrypt document; investigate storage access |
| Search key | Forge tokens; dictionary attack on tokens | Rotate search + reindex; revoke old version |
| `MASTER_KEY` | Unwrap all DEKs + search keys | Full incident: new master in KMS, rewrap/re-encrypt, rotate JWT, audit |
| `JWT_SECRET` | Impersonate users | Rotate JWT secret; invalidate sessions |

## Production recommendations

1. Store root keys in **AWS KMS / GCP KMS / Azure Key Vault / HashiCorp Vault / HSM**.
2. Use envelope encryption with KMS `Encrypt`/`Decrypt` for DEKs instead of long-lived app-hosted master bytes.
3. Separate duties: app role cannot export CMK.
4. Automate rotation runbooks with monitoring and canary decrypts.
5. Consider dual-control for revoke and admin endpoints.

## Student talking points

- Why a unique DEK per file? Blast-radius reduction and simpler selective re-encryption.
- Why wrap keys? So object storage never sees DEKs and DB never sees plaintext DEKs.
- Why separate search key? Different privilege and rotation cadence than content keys.
- Why is env master not enough for production? No hardware protection, easy exfiltration with A5.
