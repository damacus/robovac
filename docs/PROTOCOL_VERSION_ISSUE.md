# Troubleshooting: Decryption Failed / Local Key Issues

## Problem Summary

The vacuum is failing to communicate with Home Assistant due to a **local key
mismatch**. The device responds to connections but encrypted data cannot be
decrypted.

## Symptoms

```log
ERROR: Decryption failed - the local key may be incorrect or has changed.
       Try removing and re-adding the integration to refresh the key.
DEBUG: Failed to decrypt message from <device_id>
WARNING: Failed to update vacuum RoboVac. Failure count: X/3
ERROR: Maximum update retries reached for vacuum RoboVac. Marking as unavailable
```

## Root Cause

The **local key** stored in Home Assistant doesn't match the key the device
expects. This typically happens when:

1. **Key rotation**: Eufy/Tuya rotated the local key on their servers
2. **Device reset**: The vacuum was factory reset and got a new key
3. **App re-pairing**: The vacuum was re-paired in the Eufy app
4. **Stale configuration**: The integration was set up long ago and the key expired

## Evidence

- Device IS responding (ping/pong heartbeats work)
- GET command responses are received but decryption produces garbage
- The decrypted data is not valid UTF-8 or JSON

## Solution

### Remove and Re-add the Integration

1. Go to **Settings** → **Devices & Services** in Home Assistant
2. Find the **Eufy Robovac** integration
3. Click the three dots menu → **Delete**
4. Click **Add Integration** → search for **Eufy Robovac**
5. Enter your Eufy account credentials
6. The integration will fetch a fresh local key from the Tuya API

### Alternative: Manual Key Update

If you have access to the new local key (e.g., from tinytuya or similar tools):

1. Stop Home Assistant
2. Edit `.storage/core.config_entries` and find the robovac entry
3. Update the `access_token` field with the new 16-character local key
4. Start Home Assistant

## Protocol Version Support

The integration supports:

- **Protocol 3.3**: AES-ECB encryption with CRC32 checksum (most devices)
- **Protocol 3.4**: AES-ECB encryption with HMAC-SHA256 checksum (newer devices)

Protocol version is auto-detected based on device responses. If you need to
force a specific version, add `protocol_version = (3, 4)` to the model class.

## References

- [Tuya Protocol Documentation](https://developer.tuya.com/en/docs/iot/device-connection-protocol)
- [tinytuya](https://github.com/jasonacox/tinytuya) - Reference implementation
