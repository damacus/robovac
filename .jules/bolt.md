## 2026-03-03 - [Memoization] **Learning:** Repeatedly extracting and splitting model-specific DPS codes during the update cycle is an unnecessary overhead for static model configuration. **Action:** Memoize static model configurations in the entity instance to reduce redundant processing

## 2026-03-03 - [Python CRC32 Optimization]
**Learning:** Pure Python iterative implementations of standard algorithms like CRC32 are extremely slow and add overhead to network protocol processing (Tuya protocol).
**Action:** Always replace pure Python byte-iteration loops with standard library C-extensions (like `zlib.crc32`) when available for significant performance gains.

## 2026-03-03 - [Property Getter Optimization]
**Learning:** Property getters in Home Assistant are called extremely frequently on every read/update cycle. Placing inline list comprehensions (like `[activity.value for activity in VacuumActivity]`) inside these getters creates unnecessary O(n) overhead on every access.
**Action:** Pre-calculate static lists/sets into module-level constants (e.g., `VACUUM_ACTIVITY_VALUES = {activity.value for activity in VacuumActivity}`) to ensure property access remains O(1) and garbage collection overhead is minimized.

## 2026-03-03 - [Constant List Optimization False-Positive]
**Learning:** Checking membership against constant list literals (`x in [1, 2, 3]`) does NOT allocate a new list on every execution. Modern CPython compilers optimize these into constant tuples at compile-time.
**Action:** Do not waste effort refactoring constant lists into module-level sets for "performance" as it offers no measurable impact. Focus on heavier operations like `json.loads` or `base64.b64decode` instead.

## 2026-03-03 - [Parsing Memoization]
**Learning:** The integration was repeatedly running expensive `base64.b64decode` and `json.loads` calls on every state update loop for consumables data, even when the payload hadn't changed.
**Action:** Memoize raw payload strings (e.g., `self._last_consumable_data`) and conditionally skip decoding and parsing if the new string matches the old one. This provides a significant CPU and memory allocation saving during high-frequency Tuya updates.
