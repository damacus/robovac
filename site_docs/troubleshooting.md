# Troubleshooting

## Common Issues

### Vacuum Not Responding

**Symptoms**: Commands are sent but the vacuum doesn't respond.

**Solutions**:

1. Verify the IP address is correct and reachable
2. Check that the local key is correct
3. Ensure the vacuum is on the same network as Home Assistant
4. Try a different protocol version

### Invalid Local Key

**Symptoms**: Authentication errors in the logs.

**Solutions**:

1. Re-extract the local key from the Tuya platform
2. Ensure no extra spaces or characters in the key
3. Verify the device ID matches

### Connection Timeout

**Symptoms**: Timeout errors when trying to connect.

**Solutions**:

1. Check your network connectivity
2. Verify the vacuum is powered on
3. Ensure no firewall is blocking the connection
4. Try restarting the vacuum

### Wrong Protocol Version

**Symptoms**: Decryption errors or garbled responses.

**Solutions**:

1. Try protocol version 3.4 instead of 3.3
2. For newer models, try protocol 3.5
3. Check the logs for specific error messages

## Getting Help

If you're still having issues:

1. Check the [GitHub Issues](https://github.com/damacus/robovac/issues)
2. Enable debug logging and review the logs
3. Open a new issue with your logs and configuration
