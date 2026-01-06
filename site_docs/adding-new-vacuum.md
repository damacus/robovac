# Adding a New Vacuum Model

This guide explains how to add support for a new Eufy RoboVac model to the
integration.

## Prerequisites

Before adding a new model, you'll need:

1. **Model number** - The Tuya model identifier (e.g., `T2250`, `T2080`)
2. **DPS codes** - Data Point Service codes your vacuum uses
3. **Command values** - The actual values sent/received for each command

### Finding DPS Codes

DPS codes can be discovered by:

- Monitoring network traffic between the vacuum and the Eufy app
- Using Tuya debugging tools
- Checking existing similar models for reference

## File Structure

Each vacuum model is defined in its own file under
`custom_components/robovac/vacuums/`. The file naming convention is
`{MODEL_NUMBER}.py` (e.g., `T2250.py`).

## Step-by-Step Guide

### 1. Create the Model File

Create a new file in `custom_components/robovac/vacuums/` named after your
model:

```python
"""Model Name (MODEL_NUMBER)"""
from homeassistant.components.vacuum import VacuumEntityFeature
from .base import RoboVacEntityFeature, RobovacCommand, RobovacModelDetails


class T2XXX(RobovacModelDetails):
    homeassistant_features = (
        VacuumEntityFeature.CLEAN_SPOT
        | VacuumEntityFeature.FAN_SPEED
        | VacuumEntityFeature.LOCATE
        | VacuumEntityFeature.PAUSE
        | VacuumEntityFeature.RETURN_HOME
        | VacuumEntityFeature.SEND_COMMAND
        | VacuumEntityFeature.START
        | VacuumEntityFeature.STATE
        | VacuumEntityFeature.STOP
    )
    robovac_features = (
        RoboVacEntityFeature.CLEANING_TIME
        | RoboVacEntityFeature.CLEANING_AREA
        | RoboVacEntityFeature.DO_NOT_DISTURB
        | RoboVacEntityFeature.AUTO_RETURN
    )
    commands = {
        # Define commands here
    }
```

### 2. Define Home Assistant Features

The `homeassistant_features` attribute specifies which standard vacuum features
your model supports. Available features from `VacuumEntityFeature`:

| Feature        | Description              |
|----------------|--------------------------|
| `CLEAN_SPOT`   | Spot cleaning mode       |
| `FAN_SPEED`    | Adjustable suction power |
| `LOCATE`       | Find/locate the vacuum   |
| `PAUSE`        | Pause cleaning           |
| `RETURN_HOME`  | Return to charging dock  |
| `SEND_COMMAND` | Send custom commands     |
| `START`        | Start cleaning           |
| `STATE`        | Report current state     |
| `STOP`         | Stop cleaning            |
| `MAP`          | Map support              |

### 3. Define RoboVac Features

The `robovac_features` attribute specifies additional features specific to this
integration. Available features from `RoboVacEntityFeature`:

| Feature          | Description                  |
|------------------|------------------------------|
| `EDGE`           | Edge cleaning mode           |
| `SMALL_ROOM`     | Small room cleaning mode     |
| `CLEANING_TIME`  | Report cleaning duration     |
| `CLEANING_AREA`  | Report cleaned area          |
| `DO_NOT_DISTURB` | Do not disturb scheduling    |
| `AUTO_RETURN`    | Auto return when battery low |
| `CONSUMABLES`    | Consumable status reporting  |
| `ROOM`           | Room-specific cleaning       |
| `ZONE`           | Zone cleaning                |
| `MAP`            | Map features                 |
| `BOOST_IQ`       | BoostIQ auto-suction         |

### 4. Define Commands

The `commands` dictionary maps `RobovacCommand` enums to their DPS codes and
values. Available commands:

| Command          | Description              |
|------------------|--------------------------|
| `START_PAUSE`    | Start or pause cleaning  |
| `DIRECTION`      | Manual direction control |
| `MODE`           | Cleaning mode selection  |
| `STATUS`         | Current vacuum status    |
| `RETURN_HOME`    | Return to dock           |
| `FAN_SPEED`      | Suction power level      |
| `MOP_LEVEL`      | Mopping water level      |
| `LOCATE`         | Find the vacuum          |
| `BATTERY`        | Battery level            |
| `ERROR`          | Error codes              |
| `CLEANING_AREA`  | Cleaned area             |
| `CLEANING_TIME`  | Cleaning duration        |
| `AUTO_RETURN`    | Auto return setting      |
| `DO_NOT_DISTURB` | DND setting              |
| `BOOST_IQ`       | BoostIQ setting          |
| `CONSUMABLES`    | Consumable status        |

#### Command Structure

Each command entry has:

- **`code`** (required): The DPS code number
- **`values`** (optional): A dictionary mapping human-readable keys to device
  values

```python
RobovacCommand.FAN_SPEED: {
    "code": 102,
    "values": {
        "standard": "Standard",
        "turbo": "Turbo",
        "max": "Max",
        "boost_iq": "Boost_IQ",
    },
},
```

#### Naming Conventions

- **Keys** (left side): Use lowercase snake_case (e.g., `standard`, `boost_iq`)
- **Values** (right side): Use the exact value the device expects (often
  PascalCase)

### 5. Add Activity Mapping (Optional)

For models with complex status codes, add an `activity_mapping` to translate
status values to Home Assistant's `VacuumActivity` states:

```python
from homeassistant.components.vacuum import VacuumActivity

class T2XXX(RobovacModelDetails):
    # ... features and commands ...

    activity_mapping = {
        "Paused": VacuumActivity.PAUSED,
        "Auto Cleaning": VacuumActivity.CLEANING,
        "Charging": VacuumActivity.DOCKED,
        "Heading Home": VacuumActivity.RETURNING,
        "Standby": VacuumActivity.IDLE,
        "Error": VacuumActivity.ERROR,
    }
```

Available `VacuumActivity` states:

- `CLEANING` - Actively cleaning
- `DOCKED` - On the charging dock
- `PAUSED` - Cleaning paused
- `RETURNING` - Returning to dock
- `IDLE` - Idle/standby
- `ERROR` - Error state

### 6. Register the Model

Add your model to `custom_components/robovac/vacuums/__init__.py`:

1. Import your class:

   ```python
   from .T2XXX import T2XXX
   ```

2. Add to the `ROBOVAC_MODELS` dictionary:

   ```python
   ROBOVAC_MODELS: Dict[str, Type[RobovacModelDetails]] = {
       # ... existing models ...
       "T2XXX": T2XXX,
   }
   ```

### 7. Write Tests

Create a test file at `tests/test_vacuum/test_t2xxx_command_mappings.py`:

```python
"""Tests for T2XXX command mappings."""
import pytest
from custom_components.robovac.vacuums.T2XXX import T2XXX
from custom_components.robovac.vacuums.base import RobovacCommand


class TestT2XXXCommandMappings:
    """Test T2XXX command mappings."""

    def test_fan_speed_values(self):
        """Test FAN_SPEED command has expected values."""
        fan_speed = T2XXX.commands[RobovacCommand.FAN_SPEED]
        assert fan_speed["code"] == 102
        assert "standard" in fan_speed["values"]
        assert fan_speed["values"]["standard"] == "Standard"
```

Run tests with:

```bash
task test
```

## Complete Example

Here's a complete example for a basic model:

```python
"""G30 (T2250)"""
from homeassistant.components.vacuum import VacuumEntityFeature
from .base import RoboVacEntityFeature, RobovacCommand, RobovacModelDetails


class T2250(RobovacModelDetails):
    homeassistant_features = (
        VacuumEntityFeature.CLEAN_SPOT
        | VacuumEntityFeature.FAN_SPEED
        | VacuumEntityFeature.LOCATE
        | VacuumEntityFeature.PAUSE
        | VacuumEntityFeature.RETURN_HOME
        | VacuumEntityFeature.SEND_COMMAND
        | VacuumEntityFeature.START
        | VacuumEntityFeature.STATE
        | VacuumEntityFeature.STOP
    )
    robovac_features = (
        RoboVacEntityFeature.CLEANING_TIME
        | RoboVacEntityFeature.CLEANING_AREA
        | RoboVacEntityFeature.DO_NOT_DISTURB
        | RoboVacEntityFeature.AUTO_RETURN
    )
    commands = {
        RobovacCommand.START_PAUSE: {
            "code": 2,
        },
        RobovacCommand.DIRECTION: {
            "code": 3,
            "values": {
                "forward": "Forward",
                "back": "Back",
                "left": "Left",
                "right": "Right",
            },
        },
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
        RobovacCommand.STATUS: {
            "code": 15,
        },
        RobovacCommand.RETURN_HOME: {
            "code": 101,
        },
        RobovacCommand.FAN_SPEED: {
            "code": 102,
            "values": {
                "standard": "Standard",
                "turbo": "Turbo",
                "max": "Max",
                "boost_iq": "Boost_IQ",
            },
        },
        RobovacCommand.LOCATE: {
            "code": 103,
        },
        RobovacCommand.BATTERY: {
            "code": 104,
        },
        RobovacCommand.ERROR: {
            "code": 106,
            "values": {
                "0": "No error",
            },
        },
    }
```

## Tips

- **Start simple**: Begin with basic commands and add more as you verify them
- **Test incrementally**: Test each command as you add it
- **Document unknowns**: Use comments to note unverified features
- **Check similar models**: Look at existing models in the same series for
  reference
- **Use debug logging**: Enable debug logging in Home Assistant to see raw DPS
  values

## Submitting Your Model

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/add-t2xxx-support`
3. Add your model file and tests
4. Run linting: `task lint`
5. Run tests: `task test`
6. Submit a pull request with details about your vacuum model
