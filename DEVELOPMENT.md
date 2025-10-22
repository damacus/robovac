# Development Guide

This document provides guidance for developers working on the RoboVac integration.

## Project Structure

```text
custom_components/robovac/
├── __init__.py                 # Integration initialization
├── config_flow.py              # Configuration flow for setup
├── robovac.py                  # Core RoboVac class with command logic
├── vacuum.py                   # Home Assistant vacuum entity
├── sensor.py                   # Sensor entities
├── tuyalocalapi.py             # Tuya device communication
├── tuyalocaldiscovery.py       # Device discovery
├── vacuums/
│   ├── base.py                 # Base classes and enums
│   ├── T2250.py through T2262.py  # Model-specific command mappings
│   └── ... (other models)
└── strings.json                # Localization strings

tests/
├── test_vacuum/
│   ├── test_t2251_command_mappings.py  # Model-specific tests
│   ├── test_get_robovac_human_readable_value.py
│   ├── test_get_robovac_command_value.py
│   └── ... (other tests)
└── conftest.py                 # Pytest configuration and fixtures
```

## Key Concepts

### Command Mappings

Each vacuum model defines command mappings in `vacuums/T*.py` files. These mappings translate between:

- **Device codes**: Numeric DPS codes used by the Tuya protocol
- **Command names**: Enum values like `RobovacCommand.MODE`, `RobovacCommand.FAN_SPEED`
- **Command values**: User-friendly strings like `"auto"`, `"turbo"`, `"Standard"`

Example structure:

```python
RobovacCommand.MODE: {
    "code": 5,  # DPS code for this command
    "values": {
        "auto": "Auto",           # Key: input value, Value: output value
        "small_room": "SmallRoom",
        "spot": "Spot",
    },
},
```

### Naming Conventions


- **Keys** (input values): Lowercase snake_case (e.g., `"auto"`, `"small_room"`)
- **Values** (output values): PascalCase (e.g., `"Auto"`, `"SmallRoom"`)
- **Case-insensitive matching**: Device responses are matched case-insensitively


### Case-Insensitive Matching

Device responses are matched case-insensitively, so `"AUTO"`, `"auto"`, and `"Auto"` all map to the same value. This eliminates the need for duplicate bidirectional mappings and simplifies the command mapping definitions.

## Development Workflow

### Setting Up Development Environment

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Install development dependencies: `pip install -r requirements-dev.txt`
4. Run tests to verify setup: `task test`

### Running Tests

```bash
# Run all tests
task test

# Run specific test file
pytest tests/test_vacuum/test_t2251_command_mappings.py -v

# Run with coverage
task test  # Already includes coverage report

# Run tests matching a pattern
pytest tests/test_vacuum/ -k "mode" -v
```

### Code Quality Checks

```bash
# Check code style and formatting
task lint

# Verify type hints
task type-check

# Both lint and type-check
task lint && task type-check
```

### Markdown Documentation

```bash
# Check markdown formatting
task markdownlint

# Fix markdown issues
task markdownlint --fix
```

## Adding a New Vacuum Model

### 1. Create Model File

Create `custom_components/robovac/vacuums/TXXX.py`:

```python
"""Model name (TXXX)"""
from homeassistant.components.vacuum import VacuumEntityFeature
from .base import RoboVacEntityFeature, RobovacCommand, RobovacModelDetails


class TXXX(RobovacModelDetails):
    homeassistant_features = (
        VacuumEntityFeature.BATTERY
        | VacuumEntityFeature.START
        | VacuumEntityFeature.STOP
        | VacuumEntityFeature.PAUSE
        | VacuumEntityFeature.RETURN_HOME
        | VacuumEntityFeature.FAN_SPEED
        | VacuumEntityFeature.LOCATE
    )
    robovac_features = (
        RoboVacEntityFeature.CLEANING_TIME
        | RoboVacEntityFeature.CLEANING_AREA
    )
    commands = {
        RobovacCommand.START_PAUSE: {
            "code": 2,
        },
        RobovacCommand.MODE: {
            "code": 5,
            "values": {
                "auto": "Auto",
                "small_room": "SmallRoom",
            },
        },
        # ... other commands
    }
```

### 2. Register Model

Add to `custom_components/robovac/vacuums/__init__.py`:

```python
from .TXXX import TXXX

ROBOVAC_MODELS = {
    # ... existing models
    "TXXX": TXXX,
}
```

### 3. Create Tests

Create `tests/test_vacuum/test_txxx_command_mappings.py`:

```python
"""Tests for TXXX command mappings."""

import pytest
from unittest.mock import patch

from custom_components.robovac.robovac import RoboVac
from custom_components.robovac.vacuums.base import RobovacCommand


@pytest.fixture
def mock_txxx_robovac():
    """Create a mock TXXX RoboVac instance for testing."""
    with patch("custom_components.robovac.robovac.TuyaDevice.__init__", return_value=None):
        robovac = RoboVac(
            model_code="TXXX",
            device_id="test_id",
            host="192.168.1.100",
            local_key="test_key",
        )
        return robovac


def test_txxx_model_has_required_commands(mock_txxx_robovac):
    """Test that TXXX model has required commands defined."""
    commands = mock_txxx_robovac.model_details.commands

    assert RobovacCommand.MODE in commands
    assert RobovacCommand.FAN_SPEED in commands
    # ... other assertions
```

## Logging Strategy

### Log Levels

- **DEBUG**: Diagnostic information for troubleshooting (e.g., value lookups, state changes)
- **INFO**: General informational messages (e.g., "Data points now available")
- **WARNING**: Actual problems that need attention (e.g., initialization failures, update failures)
- **ERROR**: Serious errors (e.g., vacuum not initialized for critical operations)

### Examples

```python
# DEBUG: Diagnostic information
_LOGGER.debug("Successfully updated vacuum %s", self._attr_name)

# WARNING: Actual problem
_LOGGER.warning("Cannot update vacuum %s: IP address not set", self._attr_name)

# ERROR: Serious issue
_LOGGER.error("Cannot locate vacuum: vacuum not initialized")
```

## Testing Best Practices

### Test Structure

Follow the pattern from `test_t2251_command_mappings.py`:

1. Create a fixture for the mock RoboVac instance
2. Test command value mappings
3. Test case-insensitive matching
4. Test model structure (commands present)

### Test Coverage

- Aim for 100% coverage of modified code
- Test both success and failure paths
- Use mocking to isolate units under test
- Follow TDD: write tests before implementation
- Run `task test` to verify coverage

### Running Tests with Coverage

```bash
# View coverage report
task test

# Generate HTML coverage report
pytest --cov=custom_components.robovac --cov-report=html
```

## Commit Guidelines

Follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` New feature
- `fix:` Bug fix
- `refactor:` Code refactoring without behavior change
- `test:` Adding or updating tests
- `docs:` Documentation updates
- `chore:` Maintenance tasks

Examples:

```text
feat: add T2250 command mappings
fix: handle "No error" status correctly
test: add T2251 command mapping tests
refactor: improve value lookup logic
docs: update development guide
```

## Common Tasks

### Debugging a Failing Test

```bash
# Run with verbose output
pytest tests/test_vacuum/test_t2251_command_mappings.py -v -s

# Run with pdb debugger
pytest tests/test_vacuum/test_t2251_command_mappings.py --pdb

# Run specific test
pytest tests/test_vacuum/test_t2251_command_mappings.py::test_t2251_mode_has_values -v
```

### Checking Type Hints

```bash
# Run type checker
task type-check

# Check specific file
mypy custom_components/robovac/robovac.py
```

### Formatting Code

```bash
# Run linter
task lint

# Auto-fix formatting issues
black custom_components/robovac/
```

## Resources

- [Home Assistant Developer Documentation](https://developers.home-assistant.io/)
- [Tuya Local API Documentation](https://github.com/jasonacox/tinytuya)
- [Pytest Documentation](https://docs.pytest.org/)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)

## Getting Help

- Check existing issues and PRs
- Review the troubleshooting guide
- Enable debug logging to diagnose issues
- Create detailed issue reports with logs

---

**Last Updated**: October 2025
**Maintained By**: RoboVac Integration Team
