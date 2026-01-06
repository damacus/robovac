# Adding a New Vacuum Model

## Quick Start: Try an Existing Model First

**Before creating a new model file**, check if a similar model already works:

1. Look at the [Supported Models](supported-models.md) page
2. Find a model from the **same series** (e.g., G30, X8, L35)
3. Try configuring your vacuum using that model's settings

Models in the same series often share identical DPS codes. If basic functions
work (start, stop, battery), you may not need a new model file at all!

## When You Need a New Model

Create a new model file only if:

- No existing model from your series works
- Your vacuum has different DPS codes than similar models
- You want to add features not in the existing model

## Three Simple Steps

### Step 1: Copy a Similar Model

Find the most similar model in `custom_components/robovac/vacuums/` and copy it:

```bash
cp T2250.py T2XXX.py
```

Edit the file:

- Change the class name to match your model (e.g., `T2XXX`)
- Update the docstring with your model name
- Adjust DPS codes if needed (see [Finding DPS Codes](#finding-dps-codes))

### Step 2: Register Your Model

Edit `custom_components/robovac/vacuums/__init__.py`:

```python
from .T2XXX import T2XXX

ROBOVAC_MODELS: Dict[str, Type[RobovacModelDetails]] = {
    # ... existing models ...
    "T2XXX": T2XXX,
}
```

### Step 3: Test It

1. Restart Home Assistant
2. Add your vacuum using the new model
3. Test basic functions: start, stop, return home, battery level

## Finding DPS Codes

If your vacuum uses different codes than similar models:

- **Enable debug logging** in Home Assistant to see raw DPS values
- **Monitor network traffic** between the vacuum and Eufy app
- **Check the Tuya IoT Platform** if you have developer access

---

## Reference

### Commands Reference

| Command       | Typical Code | Description    |
|---------------|--------------|----------------|
| `START_PAUSE` | 2            | Start or pause |
| `DIRECTION`   | 3            | Manual control |
| `MODE`        | 5            | Cleaning mode  |
| `STATUS`      | 15           | Current status |
| `RETURN_HOME` | 101          | Go to dock     |
| `FAN_SPEED`   | 102          | Suction level  |
| `LOCATE`      | 103          | Find vacuum    |
| `BATTERY`     | 104          | Battery level  |
| `ERROR`       | 106          | Error codes    |

**Note**: Codes vary by model. Newer models (protocol 3.4+) often use different
codes (e.g., 152, 153, 158).

### Complete Example

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
        RobovacCommand.START_PAUSE: {"code": 2},
        RobovacCommand.MODE: {
            "code": 5,
            "values": {
                "auto": "Auto",
                "spot": "Spot",
                "edge": "Edge",
            },
        },
        RobovacCommand.STATUS: {"code": 15},
        RobovacCommand.RETURN_HOME: {"code": 101},
        RobovacCommand.FAN_SPEED: {
            "code": 102,
            "values": {
                "standard": "Standard",
                "turbo": "Turbo",
                "max": "Max",
            },
        },
        RobovacCommand.LOCATE: {"code": 103},
        RobovacCommand.BATTERY: {"code": 104},
        RobovacCommand.ERROR: {"code": 106},
    }
```

## Submitting Your Model

1. Fork the repository
2. Create a branch: `git checkout -b feat/add-t2xxx-support`
3. Add your model file
4. Run `task lint` and `task test`
5. Submit a pull request
