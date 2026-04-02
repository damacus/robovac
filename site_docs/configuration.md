# Configuration

## Adding the Integration

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for "RoboVac"
4. Follow the configuration wizard

## Required Information

You'll need the following information to configure your vacuum:

- **Email**: Your Eufy account email address
- **Password**: Your Eufy account password

The integration automatically retrieves your device ID, local key, model,
and other device details from Eufy's API after you log in. You do not need
to find these manually.

Optionally, you can provide a static **IP Address** if you disable
autodiscovery (see Options below).

## Supported Models

See the full list of [Supported Models](supported-models.md) with protocol
versions and model series information.

## Options

After setup, per-device options can be configured:

- **Autodiscovery** (default: enabled): Automatically detects your vacuum's
  IP address on the local network. Disable this if you want to specify a
  static IP address.
- **IP Address**: Manual IP address to use when autodiscovery is disabled.

## Troubleshooting

If you encounter issues, see the [Troubleshooting](troubleshooting.md) guide.
