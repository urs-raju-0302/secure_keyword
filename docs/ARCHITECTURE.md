# Architecture

Cross-references: [LOW_LEVEL_DESIGN.md](LOW_LEVEL_DESIGN.md) · [THREAT_MODEL.md](THREAT_MODEL.md) · [diagrams/](diagrams/)

## Problem

Store sensitive files encrypted in less-trusted cloud object storage while allowing keyword search without sending plaintext keywords to the index and without decrypting every document.

## Containers

| Container | Role |
|-----------|------|
| React frontend | Auth UI, upload, search, admin (no secret display) |
| FastAPI backend | Authz, encrypt/decrypt, token generation, KMS abstraction |
| PostgreSQL | Users, metadata, wrapped keys, search tokens, audit |
| MinIO | Ciphertext blobs (S3 API) |

## Trust boundaries

**Trusted:** browser (limited), backend, key-management code, `MASTER_KEY` source.

**Less trusted:** MinIO/S3, PostgreSQL contents, network.

A fully compromised backend can observe plaintext during legitimate processing — see [THREAT_MODEL.md](THREAT_MODEL.md).

## Data flows

**Upload:** authenticate → generate DEK → AES-GCM encrypt → extract/normalize keywords → HMAC tokens → wrap DEK → store ciphertext → store metadata/index → audit.

**Search:** authenticate → normalize → HMAC → index lookup → authorization filter → metadata (no bulk decrypt).

**Download:** authorize → unwrap DEK → AES-GCM decrypt (fail closed on tag mismatch).

## Crypto hierarchy

```
MASTER_KEY --HKDF(v)--> KEK_v --wrap--> DEK --AES-GCM--> ciphertext
MASTER_KEY --wrap--> SearchKey_v --HMAC--> keyword_token
```

## Modularity

Crypto primitives live in `app/crypto/`. Business services orchestrate. Storage is abstracted (`LocalStorageProvider` / `S3CompatibleStorageProvider`).
