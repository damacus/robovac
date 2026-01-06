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

The following Eufy RoboVac models are currently supported:

- **T1250**: RoboVac G40
- **T2080**: RoboVac G40 Hybrid
- **T2103**: RoboVac 11S
- **T2117**: RoboVac 35C
- **T2118**: RoboVac 30C
- **T2119**: RoboVac 11S Max
- **T2120**: RoboVac 15C
- **T2123**: RoboVac 25C
- **T2128**: RoboVac 15C Max
- **T2130**: RoboVac 30C Max
- **T2132**: RoboVac 25C Max
- **T2150**: RoboVac G10 Hybrid
- **T2181**: RoboVac G20
- **T2190**: RoboVac G30
- **T2192**: RoboVac G30 Edge
- **T2193**: RoboVac G30 Verge
- **T2194**: RoboVac L35 Hybrid
- **T2250**: RoboVac G30
- **T2251**: RoboVac G30 Edge
- **T2252**: RoboVac G30 Verge
- **T2253**: RoboVac G30 Hybrid
- **T2254**: RoboVac G20 Hybrid
- **T2255**: RoboVac G35+
- **T2259**: RoboVac G40+
- **T2261**: RoboVac X8
- **T2262**: RoboVac X8 Hybrid
- **T2267**: RoboVac LR30 Hybrid
- **T2268**: RoboVac LR30 Hybrid+
- **T2270**: RoboVac G32 Pro
- **T2272**: RoboVac G20
- **T2273**: RoboVac G30
- **T2275**: RoboVac L35 Hybrid
- **T2276**: RoboVac L35 Hybrid+
- **T2277**: RoboVac G40 Hybrid
- **T2278**: RoboVac G40+
- **T2320**: RoboVac X8 Pro

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
