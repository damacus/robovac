## 2026-03-03 - [Memoization] **Learning:** Repeatedly extracting and splitting model-specific DPS codes during the update cycle is an unnecessary overhead for static model configuration. **Action:** Memoize static model configurations in the entity instance to reduce redundant processing

## 2026-03-03 - [Python CRC32 Optimization]
**Learning:** Pure Python iterative implementations of standard algorithms like CRC32 are extremely slow and add overhead to network protocol processing (Tuya protocol).
**Action:** Always replace pure Python byte-iteration loops with standard library C-extensions (like `zlib.crc32`) when available for significant performance gains.
