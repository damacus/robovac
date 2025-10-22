# Protocol 3.5 Support

## Overview

The RoboVac integration now supports Tuya protocol versions 3.4 and 3.5, which use HMAC-SHA256 for message authentication instead of CRC32. This is required for newer devices like the X8 Pro SES (T2276).

## Protocol Versions

| Version | Authentication | Encoding | Notes |
|---------|---------------|----------|-------|
| 3.1 | CRC32 (payload only) | Base64 | Legacy protocol |
| 3.2 | CRC32 (payload only) | Base64 | Same as 3.1 with type_0d |
| 3.3 | CRC32 (header + payload) | Raw | Most common |
| 3.4 | HMAC-SHA256 | Raw | Newer devices |
| 3.5 | HMAC-SHA256 | Raw | Latest protocol |

## Implementation Details

### HMAC-SHA256 (Protocol 3.4+)

For protocol versions 3.4 and above, messages use HMAC-SHA256 for authentication:

1. **Message Structure:**

   ```text
   [Header: 16 bytes] + [Payload: variable] + [HMAC: 32 bytes] + [Suffix: 4 bytes]
   ```

2. **HMAC Calculation:**
   - Key: Device local key (16 characters)
   - Data: Header + Payload
   - Algorithm: HMAC-SHA256
   - Output: 32 bytes

3. **Verification:**
   - Received messages are validated by computing HMAC and comparing
   - Invalid HMAC results in message rejection

### CRC32 (Protocol < 3.4)

Earlier protocols use CRC32 for checksums:

1. **Protocol 3.3:**
   - CRC32 calculated on: Header + Payload
   - 4-byte checksum

2. **Protocol < 3.3:**
   - CRC32 calculated on: Payload only
   - 4-byte checksum
   - Payload is base64 encoded

## Using Protocol 3.5

### In Code

The `TuyaDevice` class accepts a `version` parameter:

```python
from custom_components.robovac.tuyalocalapi import TuyaDevice

# Protocol 3.5
device = TuyaDevice(
    model_details=model,
    device_id="your_device_id",
    host="192.168.1.100",
    local_key="your_local_key",
    timeout=10.0,
    ping_interval=30.0,
    update_entity_state=callback,
    version=(3, 5)  # Specify protocol version
)
```

### For Model Definitions

Models can specify their required protocol version in the model file:

```python
# In custom_components/robovac/vacuums/T2276.py
class T2276(RobovacModelDetails):
    # Model uses protocol 3.5
    protocol_version = (3, 5)
```

Then in `RoboVac.__init__()`:

```python
# Get protocol version from model details
protocol_version = getattr(
    self.model_details,
    'protocol_version',
    (3, 3)  # Default to 3.3
)

# Pass to TuyaDevice
TuyaDevice.__init__(
    self,
    model_details=self.model_details,
    device_id=device_id,
    host=host,
    local_key=local_key,
    timeout=timeout,
    ping_interval=ping_interval,
    update_entity_state=update_entity_state,
    version=protocol_version,
    port=port,
)
```

## Troubleshooting

### "HMAC verification failed"

This error indicates:

- Wrong local key
- Protocol version mismatch
- Corrupted message

**Solution:** Verify the local key and protocol version for your device.

### "Incomplete read" errors

For devices that previously had incomplete read errors (like T2276), upgrading to protocol 3.5 should resolve the issue.

**Steps:**

1. Add `protocol_version = (3, 5)` to the model file
2. Update `RoboVac.__init__()` to use the protocol version
3. Test with your device

### Determining Protocol Version

To find the correct protocol version for your device:

1. **Check device documentation** - Newer devices typically use 3.4+
2. **Try incrementally:**
   - Start with 3.3 (most common)
   - If incomplete reads occur, try 3.4
   - If still issues, try 3.5
3. **Check logs** - Look for authentication or checksum errors

## Testing

All protocol versions are tested with the existing test suite:

```bash
task test
```

The implementation maintains backward compatibility, so existing devices using protocols 3.1-3.3 continue to work without changes.

## References

- [TinyTuya Protocol Documentation](https://github.com/jasonacox/tinytuya)
- [Tuya IoT Protocol](https://developer.tuya.com/)
- Issue #42: X8 Pro SES incomplete read errors
