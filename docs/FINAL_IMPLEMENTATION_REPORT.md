# Final Implementation Report

## Architecture summary

The system is a modular FastAPI + React application that encrypts documents with per-document AES-256-GCM DEKs before storing ciphertext in MinIO/S3-compatible object storage. Metadata, wrapped DEKs, HMAC search tokens, key versions, and audit events live in PostgreSQL. Search converts keywords to deterministic HMAC-SHA-256 tokens so the index never stores plaintext keywords; authorization filters results before any decrypt.

## Implemented modules

| Area | Location |
|------|----------|
| Auth (Argon2id, JWT, refresh rotation) | `backend/app/services/auth_service.py`, `security/` |
| Encryption | `backend/app/crypto/encryption.py`, `services/encryption_service.py` |
| Key wrapping / KMS | `backend/app/crypto/key_wrapping.py`, `services/key_management_service.py` |
| Keywords / HMAC SSE | `keyword_service.py`, `crypto/hmac_search.py`, `search_service.py` |
| Documents | `document_service.py`, `storage/` |
| Key rotation / reindex | `key_rotation_service.py` |
| Audit | `audit_service.py` |
| API routes | `api/routes/{auth,documents,search,keys}.py` |
| Frontend | `frontend/src/pages/*` |
| Tests | `backend/tests/` |
| Docs / diagrams | `docs/`, `docs/diagrams/` |

## Cryptographic algorithms

- AES-256-GCM for document encryption and key wrapping
- HKDF-SHA256 for versioned KEK derivation from `MASTER_KEY`
- HMAC-SHA256 for searchable tokens
- Argon2id for password hashing
- JWT (HS256) for access tokens; opaque hashed refresh tokens

## Key-management model

```
MASTER_KEY (env) --HKDF--> KEK_vN --wraps--> DEK
MASTER_KEY --wraps--> SearchKey_vM --HMAC--> tokens
```

Statuses: ACTIVE → RETIRED → REVOKED. Search-key rotation reindexes; master-version rotation rewraps DEKs.

## Search design

`normalize → HMAC(search_key, keyword) → index lookup → authorization → metadata`

Decrypt is a separate download path.

## Threat model

Honest-but-curious cloud/DB; unauthorized users; compromised client; **fully compromised backend is out of scope for confidentiality**. See `docs/THREAT_MODEL.md`.

## Security properties

- Confidentiality of document plaintext vs storage/DB (assuming trusted backend + master key)
- Integrity/authenticity via AES-GCM tags (tamper rejected)
- Keyword plaintext not stored in searchable index
- Authorization on every document access and after search matching

## Known leakage

- Deterministic token equality (search-pattern)
- Result/access patterns
- Metadata (filename, size, timestamps)
- Timing (not mitigated)

## Limitations

- Not forward/backward private SSE
- Not ORAM/PIR
- Env-based master key ≠ HSM
- Simple rate limiter is in-memory (not multi-instance safe)
- Keyword extraction is UTF-8 text oriented (PDF text layer limited)

## Test results

```
20 passed (unit + integration + security) — pytest
```

Includes: crypto roundtrip, tamper fail, IDOR, admin gate, SQLi-safe search, path traversal filename sanitize, search-key rotation/reindex, refresh rotation.

## Performance results

See `docs/PERFORMANCE_ANALYSIS.md` and `docs/PERFORMANCE_RAW.json` from `scripts/benchmark.py` (100 / 1k / 10k document micro-benchmarks for encrypt, extract, index, search lookup, decrypt).

## Deployment instructions

1. Copy `.env.example` → `.env` and set secrets
2. `docker compose up --build`
3. Open http://localhost:5173 and http://localhost:8000/docs

## Future improvements

AWS KMS/Vault, TLS termination, stronger SSE module, Redis rate limits, immutable audit, multi-tenant isolation, penetration testing.

## Exact files created (high level)

- `backend/` application, migrations, tests, Dockerfile
- `frontend/` React app, Dockerfile, nginx
- `docker-compose.yml`, `.env.example`, `Makefile`, `scripts/`
- `docs/*` including diagrams 01–16 and this report
- `README.md`
