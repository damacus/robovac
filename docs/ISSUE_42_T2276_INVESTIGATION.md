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

**Good news**: You don't need to manually extract credentials! This integration already does that automatically when you enter your Eufy app email/password in the Home Assistant config flow.

If you have a T2276 vacuum, please help us debug the communication issue:

1. **Enable Debug Logging**:
   In Home Assistant, add to `configuration.yaml`:

   ```yaml
   logger:
     default: info
     logs:
       custom_components.robovac: debug
       custom_components.robovac.tuyalocalapi: debug
   ```

   Restart Home Assistant, then let it try to connect to your T2276 for a few minutes.

2. **Provide Debug Logs**:
   - Go to Settings → System → Logs
   - Download the full log
   - Share the relevant sections showing:
     - Connection attempts
     - "Incomplete read" errors
     - Any data point (DPS) values that do appear
     - The complete error sequence

3. **Device Information**:
   - Exact model name from Eufy app (confirm it's T2276/X8 Pro SES)
   - Firmware version (found in Eufy app settings)
   - Does the vacuum work in the Eufy app?

4. **Test Alternative Integration**:
   - Try kevinbird15's fork: <https://github.com/kevinbird15/robovac-ha-integration>
   - Report if it works differently
   - If it works, note any differences in behavior

5. **Optional - Advanced Users**:
   If you're comfortable with Python, you can try these tools to capture raw device data:
   - <https://github.com/markbajaj/eufy-device-id-python> - Gets device info from Eufy servers
   - `tinytuya scan` - Scans local network for Tuya devices (after you have credentials)

   But this is NOT required - debug logs are more helpful!

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
