## 2025-03-01 - Cross-Session Data Leakage
**Vulnerability:** Global `eufyheaders` dictionary was being mutated with user-specific `token` and `id` during Eufy API requests.
**Learning:** In Home Assistant integrations where multiple instances or concurrent requests may occur, mutating global module-level dictionaries causes sensitive user data (tokens/IDs) to leak across sessions.
**Prevention:** Always create a local copy (`headers = global_headers.copy()`) before adding user-specific or sensitive request headers.
