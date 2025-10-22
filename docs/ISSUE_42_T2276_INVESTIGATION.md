# T2276 (X8 Pro SES) Investigation

## Issue Summary

T2276 (X8 Pro SES) vacuum is experiencing connection issues with the following symptoms:

- Device connects to Home Assistant
- Repeated "Incomplete read" errors in logs
- Empty data points (`{}`) returned from vacuum
- No status updates received

## Current Status

**Model Support**: Partial
**Tests**: ✅ Passing
**Protocol**: ⚠️ Issues

## Technical Analysis

### Symptoms

From user logs:

```log
2025-10-22 13:10:04.065 DEBUG [custom_components.robovac.tuyalocalapi] Incomplete read
2025-10-22 13:10:22.225 DEBUG [custom_components.robovac.tuyalocalapi] Disconnected
2025-10-22 13:10:22.241 DEBUG [custom_components.robovac.tuyalocalapi] Connecting
```

The vacuum connects but doesn't respond to status requests, resulting in:

```log
2025-05-09 08:23:04.568 DEBUG [custom_components.robovac.vacuum] Updating entity values from data points: {}
```

### Current Configuration

T2276 is currently configured with the following DPS codes:

- MODE: 152
- STATUS: 173
- RETURN_HOME: 153
- FAN_SPEED: 154
- LOCATE: 153
- BATTERY: 172
- ERROR: 169

These codes are identical to T2275 and T2278 models.

### Possible Causes

1. **Incorrect DPS Codes**: T2276 may use different data point codes than T2275/T2278
2. **Protocol Version**: Device may use a different Tuya protocol version
3. **Encryption**: Device may require different encryption handling
4. **Timing Issues**: Device may need different timeout or retry settings

## Next Steps

### For Users

If you have a T2276 vacuum, please help us by providing:

1. **Device Information**:
   - Exact model name from Eufy app
   - Firmware version

2. **Get Local Key and Device ID**:
   Since your vacuum is connected to the Eufy app (not Tuya directly), you need to extract credentials using one of these methods:

   **Method 1: Eufy Security Web API (Recommended)**
   - Follow this guide: <https://github.com/matijse/eufy-ha-mqtt-bridge/wiki/Obtaining-your-Local-Key-and-Device-ID>
   - This extracts credentials from Eufy's servers without needing Tuya cloud access

   **Method 2: Network Traffic Capture**
   - Use Wireshark or similar to capture traffic between Eufy app and vacuum
   - Look for the local key in the initial handshake

3. **Raw Data Capture** (after getting credentials):
   Once you have the local key and device ID:

   ```bash
   # Scan for your device on local network
   python -m tinytuya scan
   
   # Create a snapshot file with your credentials
   # Then capture DPS values in different states
   ```

   Capture the DPS values when vacuum is in different states:
   - Idle/Standby
   - Cleaning
   - Returning to dock
   - Charging

4. **Alternative Integration**:
   - Try kevinbird15's fork: <https://github.com/kevinbird15/robovac-ha-integration>
   - Report if it works and what differences you notice

5. **Enable Debug Logging**:
   In Home Assistant, add to `configuration.yaml`:

   ```yaml
   logger:
     default: info
     logs:
       custom_components.robovac: debug
       custom_components.robovac.tuyalocalapi: debug
   ```

   Then provide the full debug logs showing the connection attempts

### For Developers

1. **Compare with Working Implementation**:
   - Review kevinbird15's implementation that reportedly works
   - Identify protocol or configuration differences

2. **Protocol Analysis**:
   - Add more detailed logging around message parsing
   - Capture raw Tuya messages for analysis

3. **Test Different Configurations**:
   - Try different DPS code combinations
   - Test with different protocol versions
   - Experiment with timeout values

## Related Issues

- GitHub Issue #42: <https://github.com/damacus/robovac/issues/42>
- kevinbird15's working fork: <https://github.com/kevinbird15/robovac-ha-integration>

## References

- User report from @Casper9228 (2025-04-29)
- User report from @peggleg (2025-10-22)
- User report from @kevinbird15 with alternative implementation (2025-09-18)

## Updates

- **2025-10-22**: Initial investigation documented
- Tests created and passing for T2276 command mappings
- Model file exists with standard configuration
- Issue appears to be at protocol/communication level, not configuration
