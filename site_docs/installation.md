# Installation

## Prerequisites

- Home Assistant 2024.1.0 or later
- A Eufy RoboVac with local network access
- Your vacuum's local key and device ID

## Installation via HACS (Recommended)

1. Open HACS in Home Assistant
2. Click on "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add `https://github.com/damacus/robovac` as a custom repository
6. Select "Integration" as the category
7. Click "Add"
8. Search for "RoboVac" and install

## Manual Installation

1. Download the latest release from GitHub
2. Extract the `custom_components/robovac` folder
3. Copy it to your Home Assistant `custom_components` directory
4. Restart Home Assistant

## Next Steps

After installation, proceed to [Configuration](configuration.md) to set up
your vacuum.
