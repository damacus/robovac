# Configuration

## Adding the Integration

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for "RoboVac"
4. Follow the configuration wizard

## Required Information

You'll need the following information to configure your vacuum:

- **Device ID**: Your vacuum's unique identifier
- **Local Key**: The encryption key for local communication
- **IP Address**: Your vacuum's local IP address

## Supported Models

See the full list of [Supported Models](supported-models.md) with protocol
versions and model series information.

## Finding Your Local Key

The local key can be obtained using various methods:

1. **Tuya IoT Platform**: Register as a developer and link your device
2. **Third-party tools**: Use tools like `tuya-cli` to extract the key

## Protocol Version

Some vacuums require a specific protocol version:

- **Protocol 3.3**: Most older models
- **Protocol 3.4**: Newer models with enhanced security
- **Protocol 3.5**: Latest models

If you're unsure, start with 3.3 and adjust if needed.

## Troubleshooting

If you encounter issues, see the [Troubleshooting](troubleshooting.md) guide.
