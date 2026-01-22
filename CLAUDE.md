# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

RoboVac is a Home Assistant custom integration for controlling Eufy RoboVac vacuum cleaners via local network (no cloud dependency). It supports 40+ models using Tuya protocol versions 3.3, 3.4, and 3.5.

## Common Commands

All commands use [Task](https://taskfile.dev/) as the task runner:

```bash
task install-dev      # Install development dependencies with uv
task test             # Run pytest with coverage (generates coverage.xml)
task lint             # Run flake8 on custom_components and tests
task type-check       # Run mypy type checking
task markdownlint     # Lint and auto-fix markdown files
task all              # Run install-dev, test, type-check, lint, markdownlint
```

Run a single test:
```bash
pytest tests/test_vacuum/test_t2251_command_mappings.py -v
pytest tests/test_vacuum/ -k "mode" -v  # Pattern matching
```

List supported vacuum models:
```bash
python -m custom_components.robovac.model_validator_cli --list
```

## Architecture

### Core Components

- **`custom_components/robovac/robovac.py`**: `RoboVac` class - core logic extending `TuyaDevice`, handles model-specific features and command translation
- **`custom_components/robovac/tuyalocalapi.py`**: `TuyaDevice` class - Tuya local protocol implementation with encryption (AES, HMAC-SHA256)
- **`custom_components/robovac/vacuum.py`**: `RoboVacEntity` - Home Assistant vacuum entity with state management and command execution
- **`custom_components/robovac/config_flow.py`**: Configuration flow for Home Assistant UI setup

### Model System

Each vacuum model has a file in `custom_components/robovac/vacuums/T*.py` defining:
- `homeassistant_features`: Home Assistant vacuum capabilities (battery, start, stop, fan_speed, etc.)
- `robovac_features`: Custom features (cleaning_time, cleaning_area, etc.)
- `commands`: Dict mapping `RobovacCommand` enum to DPS codes and value mappings
- Optional `dps_codes`, `protocol_version`, `activity_mapping`

Models are registered in `custom_components/robovac/vacuums/__init__.py` via the `ROBOVAC_MODELS` dict.

### Command Mapping Pattern

Commands translate between three levels:
- **DPS Code**: Numeric identifier from Tuya protocol (e.g., "5", "102")
- **Command Name**: Enum value (e.g., `RobovacCommand.MODE`)
- **Command Value**: User-friendly string (e.g., "auto" -> "Auto")

```python
RobovacCommand.MODE: {
    "code": 5,
    "values": {
        "auto": "Auto",           # Key: input (snake_case), Value: output (PascalCase)
        "small_room": "SmallRoom",
    },
},
```

Device responses use case-insensitive matching - "AUTO", "auto", "Auto" all resolve correctly.

## Adding a New Vacuum Model

1. Create `custom_components/robovac/vacuums/TXXX.py` with features and commands
2. Import and register in `custom_components/robovac/vacuums/__init__.py`
3. Create tests in `tests/test_vacuum/test_txxx_command_mappings.py`

Test fixture pattern:
```python
@pytest.fixture
def mock_txxx_robovac():
    with patch("custom_components.robovac.robovac.TuyaDevice.__init__", return_value=None):
        return RoboVac(model_code="TXXX", device_id="test", host="192.168.1.1", local_key="key")
```

## Commit Guidelines

Follow [Conventional Commits](https://www.conventionalcommits.org/): `feat:`, `fix:`, `refactor:`, `test:`, `docs:`, `chore:`

## Dev Container

The project includes a dev container with Home Assistant for live testing:
```bash
task ha-start         # Start Home Assistant
task ha-logs          # View robovac logs
task ha-restart       # Restart Home Assistant
```
