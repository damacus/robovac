## 2025-03-01 - Cross-Session Data Leakage
**Vulnerability:** Global `eufyheaders` dictionary was being mutated with user-specific `token` and `id` during Eufy API requests.
**Learning:** In Home Assistant integrations where multiple instances or concurrent requests may occur, mutating global module-level dictionaries causes sensitive user data (tokens/IDs) to leak across sessions.
**Prevention:** Always create a local copy (`headers = global_headers.copy()`) before adding user-specific or sensitive request headers.

## 2025-03-06 - Missing timeouts on Tuya API requests
**Vulnerability:** External HTTP requests to Tuya Web API using `requests.Session.post` lacked a explicit `timeout` configuration.
**Learning:** Missing timeout parameters on external network requests can lead to thread exhaustion and DoS if the external server hangs, especially critical in a Home Assistant integration.
**Prevention:** Always add a `timeout=` parameter to `requests` calls (e.g. `timeout=10`).
