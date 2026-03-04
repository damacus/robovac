## 2024-05-24 - DoS Risk in API Clients
**Vulnerability:** External HTTP requests (via `requests`) lacked timeouts in `eufywebapi.py` and `tuyawebapi.py`.
**Learning:** By default, `requests` operations hang indefinitely if the server doesn't respond, which can freeze the Home Assistant integration's worker threads causing a Denial of Service.
**Prevention:** Always specify a `timeout` parameter for all external network requests to fail securely and release resources.
