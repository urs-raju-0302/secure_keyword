# Viva / Interview Questions (50+)

1. **Why encrypt cloud data?** Because cloud operators and DB thieves may be untrusted; encryption limits plaintext exposure.
2. **Why can’t normal encrypted data be searched?** Ciphertext is designed to be indistinguishable; equality/search needs special constructions or decrypt-everything.
3. **What is searchable encryption?** Cryptographic methods enabling keyword queries over encrypted data with controlled leakage.
4. **What is a search token?** Opaque value derived from a keyword (here HMAC) used for index lookup.
5. **What is HMAC?** Keyed-hash message authentication code; here HMAC-SHA-256.
6. **Why not SHA-256 alone?** Unkeyed hashes allow offline keyword guessing against the index.
7. **What is AES-GCM?** AES in Galois/Counter Mode — confidentiality + authenticity.
8. **Why use a unique nonce?** Reusing nonce+key in GCM breaks security catastrophically.
9. **What is a DEK?** Data Encryption Key encrypting one document.
10. **What is a KEK?** Key Encryption Key wrapping DEKs (envelope encryption).
11. **Why separate search key from encryption key?** Different purpose and lifecycle; rotating search keys shouldn’t require new document ciphertext.
12. **What is envelope encryption?** Encrypt data with DEK; encrypt DEK with KEK/KMS.
13. **What is key rotation?** Introducing new key versions and migrating wraps/indexes.
14. **What if a key is compromised?** Revoke/retire, rotate, rewrap/reindex; assess blast radius.
15. **What is an honest-but-curious server?** Follows protocol but tries to learn from observed data.
16. **What is search-pattern leakage?** Linking repeated identical queries via identical tokens.
17. **What is access-pattern leakage?** Observing which records are accessed/returned.
18. **Does the server know the keyword?** Not the plaintext if only tokens are stored/queried at the index — backend does know during query generation.
19. **Does the server know which documents matched?** The DB/index observer sees matching IDs.
20. **Can the object store decrypt files?** Not without DEKs/master key.
21. **If PostgreSQL is compromised?** Attacker gets tokens, wraps, metadata — not plaintext passwords/DEKs if crypto holds.
22. **If the backend is compromised?** Attacker can decrypt during processing and access keys — fatal.
23. **If the user’s device is compromised?** Credentials and plaintext downloads can leak.
24. **Why Argon2id?** Memory-hard password hashing resistant to GPU/ASIC cracking.
25. **Why JWT?** Stateless access credentials with expiry; pair with refresh rotation.
26. **What is authorization?** Deciding whether an authenticated subject may access a resource.
27. **What is IDOR?** Insecure Direct Object Reference — accessing others’ IDs without checks.
28. **How prevent unauthorized search results?** Filter by ownership after token match.
29. **How is integrity protected?** AES-GCM authentication tags.
30. **Why not encrypt DB and search locally?** Doesn’t scale; defeats cloud search goals; still needs client trust.
31. **What is metadata leakage?** Filenames, sizes, timestamps revealing information.
32. **What is key revocation?** Marking a key version unusable (REVOKED).
33. **Why is key management hard?** Lifecycle, backup, rotation, access control, disaster recovery.
34. **What is the threat model?** Honest-but-curious storage/DB + unauthorized users; trusted backend.
35. **Primary security property?** Confidentiality of docs/keywords vs untrusted storage/index (with stated leakage).
36. **Biggest limitation?** Deterministic SSE leakage + trusted backend assumption.
37. **How improve SSE?** Forward/backward private schemes, ORAM/PIR, TEEs — as separate modules.
38. **How integrate AWS KMS?** Replace local master material with KMS Encrypt/Decrypt for wraps.
39. **How scale the search index?** Composite indexes, sharding, partitioning by tenant/version.
40. **Millions of documents?** Async workers, horizontal DB, careful reindex strategy.
41. **Multi-tenant isolation?** Tenant IDs in authz + possibly separate keys/indexes.
42. **Disaster recovery?** Secure backup of master key material; ciphertext backups alone are useless without keys.
43. **How rotate search keys?** New version → recompute tokens → validate → activate → retire old.
44. **Why is deterministic search useful?** Simple, fast equality queries, easy to teach.
45. **Why is deterministic search dangerous?** Linkability and frequency leakage.
46. **What is forward privacy?** Past queries shouldn’t easily link to newly added documents (advanced).
47. **What is backward privacy?** Updates shouldn’t reveal which prior queries match new docs (advanced).
48. **What is SSE?** Searchable Symmetric Encryption.
49. **Encryption vs access control?** Encryption protects confidentiality of data at rest; access control enforces who may decrypt/use.
50. **If the master key is lost?** Wrapped DEKs become permanently undecryptable.
51. **Why HKDF for KEK versions?** Derive distinct wrap keys from one master secret per version.
52. **What does associated data (AAD) do in GCM?** Binds extra context (e.g., filename) into the auth tag.
53. **Why hash refresh tokens in DB?** Limits damage if DB leaks (still rotate on use).
54. **Why return 404 on IDOR?** Avoid confirming resource existence to unauthorized users.
55. **Does this project provide zero knowledge?** No.
