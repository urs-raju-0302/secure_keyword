# Student Explanation Guide

## Level 1 — 30 seconds

We encrypt each file with its own key before putting it in cloud storage. To search without giving the cloud your real keywords, we turn keywords into secret “tokens” with HMAC and search those tokens instead.

## Level 2 — 2 minutes

**Cloud problem:** storage operators might be curious.  
**Encryption:** AES-GCM locks file contents.  
**Search problem:** encrypted blobs aren’t searchable.  
**Searchable index:** store HMAC tokens → document IDs.  
**Key management:** a master key wraps per-file keys; a separate search key makes tokens.

## Level 3 — Technical

- **AES-GCM:** authenticated encryption; unique nonce per encryption.
- **DEK:** random 256-bit key per document.
- **KEK/master:** wraps DEKs (envelope encryption) via HKDF-versioned AES-GCM wrap.
- **HMAC-SHA-256:** keyed hash → search token.
- **Authorization:** after token match, only return docs the user owns.
- **Rotation:** new search key requires reindexing; new master version requires rewrapping DEKs.
- **Threat model:** honest-but-curious storage/DB; compromised app server is fatal.

## Level 4 — Cybersecurity discussion

- **Honest-but-curious:** follows protocol but inspects data.
- **Search-pattern leakage:** same keyword → same token.
- **Access-pattern leakage:** which documents are returned/fetched.
- **Metadata leakage:** names, sizes, timestamps.
- **Inference:** auxiliary info may still reveal topics.
- **Compromised backend / key compromise:** full break of confidentiality goals.
- **Forward/backward privacy:** advanced SSE goals **not** provided by this deterministic design.

Continue with [VIVA_QUESTIONS.md](VIVA_QUESTIONS.md) and [THREAT_MODEL.md](THREAT_MODEL.md).
