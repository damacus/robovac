## 2025-03-01 - Cross-Session Data Leakage
**Vulnerability:** Global `eufyheaders` dictionary was being mutated with user-specific `token` and `id` during Eufy API requests.
**Learning:** In Home Assistant integrations where multiple instances or concurrent requests may occur, mutating global module-level dictionaries causes sensitive user data (tokens/IDs) to leak across sessions.
**Prevention:** Always create a local copy (`headers = global_headers.copy()`) before adding user-specific or sensitive request headers.

## 2025-03-06 - Missing timeouts on Tuya API requests
**Vulnerability:** External HTTP requests to Tuya Web API using `requests.Session.post` lacked a explicit `timeout` configuration.
**Learning:** Missing timeout parameters on external network requests can lead to thread exhaustion and DoS if the external server hangs, especially critical in a Home Assistant integration.
**Prevention:** Always add a `timeout=` parameter to `requests` calls (e.g. `timeout=10`).

## 2025-03-08 - Use of `ast.literal_eval` on external data
**Vulnerability:** `ast.literal_eval` was used to parse base64-encoded consumables data from Tuya devices.
**Learning:** While safer than `eval()`, `ast.literal_eval` on untrusted external data can still be risky (e.g., DoS via complex structures) and is not the standard way to handle JSON data.
**Prevention:** Use `json.loads` for parsing JSON data from external sources and ensure appropriate type checking (e.g., `isinstance(data, dict)`) before accessing keys.
