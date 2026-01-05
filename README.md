# Eufy RobovVac control for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://github.com/custom-components/hacs)
[![Sponsor me on Github Sponsors](https://img.shields.io/badge/Sponsor-ea4aaa?style=for-the-badge&logo=github-sponsors&logoColor=%23EA4AAA&labelColor=white)](https://github.com/sponsors/damacus)

A Eufy RoboVac integration for Home Assistant that includes a Config Flow to add your RoboVac(s) and the local key and ID required. All you need to do is enter your Eufy app credentials and the Config Flow will look up the details for you. After the initial config use the configuration button on the Integration to enter the RoboVac IP address when prompted.

## ⚠️ Breaking Change in v2.0.0

**Version 2.0.0 includes significant protocol improvements that require you to
remove and re-add the integration.**

### What Changed

- Added support for Tuya protocol 3.4 (HMAC-SHA256 checksums)
- Improved encryption/decryption error handling
- Better detection and messaging for stale local keys

### Upgrade Instructions

1. Go to **Settings** → **Devices & Services**
2. Find the **Eufy Robovac** integration
3. Click the three dots menu → **Delete**
4. Click **Add Integration** → search for **Eufy Robovac**
5. Enter your Eufy account credentials
6. Configure the IP address for each vacuum

This re-add process fetches a fresh local key from the Tuya API, which is
required for the new protocol support.

## History

This work has evolved from the original work by [Richard Mitchell](https://github.com/mitchellrj) and the countless others who have contributed over the last couple of years. It also builds on the work done by [Andre Borie](https://gitlab.com/Rjevski/eufy-device-id-and-local-key-grabber) to get the required local ID and key.

This is yet another Eufy fork, this time based on work from [CodeFoodPixels](https://github.com/CodeFoodPixels).

## Installation

### Prerequisites

1. Make sure your Home Assistant Core is up to date
2. Remove any previous Eufy or RoboVac installation including entries in the configuration.yaml

### Using HACS

1. In HACS add this repo as an integration additional repository.
2. Then install it.
3. Restart Home Assistant
4. Go to the Integrations Page and Click +Add Integration button
5. Search for Eufy RoboVac and select it
6. Enter your Eufy username and password (The ones you use to login to the add with) and submit
7. If you've done it correctly you should get a success dialog and option to enter an Area for each RoboVac you have
8. Click Finish
9. On the Integrations Screen Locate your Eufy RoboVac card and click the configure button
10. Select the Radio button beside the Vacuum name and type its IP address in the box and press Submit
(You need to repeat steps 9 and 10 for each RoboVac you have)
11. Enjoy

Please note: You may have to get a new version of the access key for your vacuum from time to time if Eufy change it. Worst case you have to Delete the integration and re add it to get the new key.

## Debugging

The integration includes debug logging statements that can provide valuable insights into component operations. These logs can be accessed through the Home Assistant System Log.

For real-time log monitoring, consider using the Log Viewer Add-on available in the Home Assistant store.

To enable detailed debug logging, add the following configuration to your `configuration.yaml` file:

```yaml
logger:
  default: warning
  logs:
    custom_components.robovac.vacuum: debug
    custom_components.robovac.tuyalocalapi: debug
    custom_components.robovac.robovac: debug
```

## Model Validation

Before setting up the integration, you can validate if your RoboVac model is supported by using the included CLI tool:

```bash
python -m custom_components.robovac.model_validator_cli <YOUR_MODEL_CODE>
```

For example:

```bash
python -m custom_components.robovac.model_validator_cli T2278
```

To see a full list of all supported models, use the `--list` flag:

```bash
python -m custom_components.robovac.model_validator_cli --list
```

## Development

### Code Quality

This integration follows best practices for code quality and maintainability:

- **Case-Insensitive Matching**: Device responses are matched case-insensitively, handling variations in capitalization automatically.
- **Logging Strategy**: Debug logs provide diagnostic information for troubleshooting, while warnings are reserved for actual issues.
- **Type Hints**: Full type annotations throughout the codebase for improved IDE support and type checking.
- **Test Coverage**: Dedicated tests for each vacuum model with full coverage.

### Running Tests

```bash
# Run all tests
task test

# Run specific test file
pytest tests/test_vacuum/test_t2251_command_mappings.py -v

# Check code style
task lint

# Verify type hints
task type-check
```

### Command Mapping Conventions

All vacuum models follow consistent conventions for command mappings:

- **Keys**: Lowercase snake_case (e.g., `"auto"`, `"small_room"`)
- **Values**: PascalCase (e.g., `"Auto"`, `"SmallRoom"`)
- **Matching**: Device responses are matched case-insensitively

Example from `T2250.py`:

```python
RobovacCommand.MODE: {
    "code": 5,
    "values": {
        "auto": "Auto",
        "small_room": "SmallRoom",
        "spot": "Spot",
        "edge": "Edge",
        "nosweep": "Nosweep",
    },
},
```
