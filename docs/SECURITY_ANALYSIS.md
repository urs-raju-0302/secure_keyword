# Security Analysis

Maps threats to protections and **remaining residual risk**. Cross-links: [THREAT_MODEL.md](THREAT_MODEL.md), [SEARCHABLE_ENCRYPTION.md](SEARCHABLE_ENCRYPTION.md), [KEY_MANAGEMENT.md](KEY_MANAGEMENT.md).

## Threat / Protection / Remaining Risk

| Threat | Protection in this project | Remaining risk |
|--------|---------------------------|----------------|
| Cloud storage reads ciphertext | AES-256-GCM with unique DEK + nonce; plaintext never stored in MinIO | Size/timing leaks; A5 decrypts everything |
| DB dump of documents table | Bodies not in DB; only wrapped DEK + metadata | Metadata + wrapped keys valuable if master key also stolen |
| Plaintext keywords in index | HMAC-SHA-256 tokens under search key; never store keyword text | Deterministic tokens leak **equality**; offline dictionary if search key leaks |
| Search-pattern leakage (same keyword → same token) | Documented; response notes leakage | Unavoidable in deterministic SSE v1; enables frequency analysis |
| Access-pattern leakage (which docs matched / which objects fetched) | Search returns metadata only; download is separate | Curious operator still sees which objects are read over time |
| Metadata leakage (filename, size, owner, timestamps) | Minimal fields; no body | Filenames and sizes remain visible to DB attacker |
| Inference attacks with auxiliary info | Honest documentation; authz limits result sets | Powerful A1/A2 with side knowledge may infer keywords/topics |
| Password theft from DB | Argon2id (time=3, memory=64MiB, parallelism=4) | Weak user passwords still crackable offline |
| Credential stuffing / login brute force | In-memory rate limit on `/auth/login` (educational) | Not distributed; bypassable on multi-instance without Redis/WAF |
| Stolen access JWT | Short TTL (default 15 min); HTTPS assumed in prod | Valid until expiry; no server-side access denylist |
| Stolen refresh token | Stored hashed; rotated on use; logout revokes | Theft before rotation; race/reuse detection limited |
| IDOR on document UUID | Owner/admin checks; 404 on deny | Misconfigured admin role; bugs in new endpoints |
| Cross-user search hits | Post-match `can_search_document` filter | Admin sees all by design |
| Unauthorized admin key ops | `require_admin` → 403 | Compromised admin account is high impact |
| Ciphertext tampering | AES-GCM tag verification on download | Attacker can cause DoS (decrypt fail); cannot forge valid plaintext without DEK |
| Wrapped-DEK tampering | AES-GCM wrap authentication | Same: fail closed |
| SQL injection via search keyword | ORM parameterized queries; keyword becomes HMAC input | Always keep using ORM/bind params for new queries |
| Path traversal in filename | Sanitize to basename; length cap | Other upload surfaces must reuse sanitizer |
| Oversized upload | `MAX_UPLOAD_BYTES` check | Resource exhaustion below limit still possible |
| Nonce reuse under same DEK | Fresh `os.urandom`/secrets nonce per encrypt | Implementation bug would be catastrophic for GCM—tests assert distinct nonces |
| Key compromise without rotation story | Versioned keys; rotate search + reindex; rotate master + rewrap; revoke retired | Educational master rotation uses same env secret + HKDF version—not full HSM rekey |
| Secrets in logs/API | Audit strips sensitive keys; key status omits material; API responses omit DEKs | Mis-logging in future code; debug modes |
| Compromised client (A4) | Server-side secrets stay server-side; short JWT | Full account takeover for victim session |
| Compromised backend (A5) | **None cryptographically** | Fatal—treat as design limit |
| XSS / CSRF on SPA | Security headers (nosniff, frame deny, no-store); CORS allowlist | Not a full browser security program; JWT in JS storage is XSS-sensitive |
| Insider admin abuse | Audit of key rotation/reindex | Malicious admin can decrypt via reindex path by design |

## Leakage profile (SSE v1)

| Leakage class | Occurs? | Why |
|---------------|---------|-----|
| Keyword equality (search pattern) | **Yes** | Same normalized keyword → same HMAC under same search-key version |
| Result / access pattern | **Yes** | Matching document IDs returned; downloads fetch specific objects |
| Volume / size | **Yes** | `size_bytes`, ciphertext length |
| Forward privacy (new queries hide past) | **No** | Not provided by deterministic HMAC index |
| Backward privacy (deletes hide past) | **No** | Not claimed |
| Zero-knowledge | **No** | Do not claim |

## Positive security properties (what you can defend in a viva)

1. **Envelope encryption** isolates per-document keys; rotating master rewraps without re-encrypting all blobs.
2. **Authenticated encryption** detects tampering.
3. **Index does not store plaintext keywords.**
4. **Authorization is enforced after cryptographic matching** (defense in depth).
5. **Threat model states A5 is fatal**—credibility over hype.

## Recommended improvements (not implemented)

- Client-side encryption so A5 sees less plaintext (major UX/architecture change)
- Cloud KMS/HSM for master keys
- Stronger SSE (e.g., dynamic SSE with better leakage profiles) as a pluggable module—see [SEARCHABLE_ENCRYPTION.md](SEARCHABLE_ENCRYPTION.md)
- Redis/WAF rate limiting, distributed tracing redaction, secrets manager
- ORAM / padding for access-pattern hiding (expensive)

## Related tests

Security suite: `backend/tests/test_security.py`, `test_documents_search.py`, `test_crypto.py`, `test_auth.py`. Narrative: [TESTING.md](TESTING.md).
