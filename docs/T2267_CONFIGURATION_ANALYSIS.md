# T2267 (RoboVac L60) Configuration Analysis

This document reviews the T2267 vacuum configuration and identifies missing or incorrect features.

## Current Features

### Home Assistant Features (`VacuumEntityFeature`)

| Feature | Status | Notes |
| ------- | ------ | ----- |
| CLEAN_SPOT | ✓ | |
| FAN_SPEED | ✓ | |
| LOCATE | ✓ | |
| PAUSE | ✓ | Fixed - uses code 152 with "AggN" |
| RETURN_HOME | ✓ | Fixed - uses code 152 with "AggG" |
| SEND_COMMAND | ✓ | |
| START | ✓ | |
| STATE | ✓ | |
| STOP | ✓ | Fixed - uses code 152 with "AggM" |
| BATTERY | ✓ Via Sensor | Command exists (code 163), exposed via dedicated sensor entity (HA 2025.8+ compliant) |

### RoboVac Features (`RoboVacEntityFeature`)

| Feature | Status | Notes |
| ------- | ------ | ----- |
| DO_NOT_DISTURB | ✓ | Code 157 |
| BOOST_IQ | ✓ | Code 159 |
| CLEANING_TIME | ❌ Missing | T2278 has this |
| CLEANING_AREA | ❌ Missing | T2278 has this |
| ROOM | ❌ Missing | Device supports room cleaning (status values exist) |
| ZONE | ❌ Missing | Device supports zone cleaning (status values exist) |
| MAP | ❌ Missing | |
| CONSUMABLES | ⚠️ Partial | Command exists (code 168) but feature flag not set |

## Current Commands

| Command | DPS Code | Values | Status |
| ------- | -------- | ------ | ------ |
| MODE | 152 | auto, pause, spot, return, nosweep | ⚠️ Issues |
| STATUS | 153 | Multiple protobuf-encoded values | ✓ |
| DIRECTION | 155 | brake, forward, back, left, right | ✓ |
| START_PAUSE | 152 | pause, resume | ✓ Fixed |
| STOP | 152 | stop | ✓ Fixed |
| DO_NOT_DISTURB | 157 | - | ✓ |
| FAN_SPEED | 158 | quiet, standard, turbo, max, boost_iq | ✓ |
| BOOST_IQ | 159 | - | ✓ |
| LOCATE | 160 | - | ⚠️ Missing value |
| BATTERY | 163 | - | ✓ |
| CONSUMABLES | 168 | - | ✓ |
| RETURN_HOME | 152 | return | ✓ Fixed |
| ERROR | 177 | - | ✓ |

## Issues Found

### 1. MODE "spot" value is incorrect

**Current:**

```python
"spot": "AA=="  # WRONG - AA== decodes to standby/empty
```

**Should be:**

```python
"spot": "AggD"  # Correct - encodes START_SPOT_CLEAN (method=3)
```

The value "AA==" (base64) decodes to a zero byte, which represents standby, not spot cleaning. The correct encoding for `ModeCtrlRequest.Method.START_SPOT_CLEAN` (value 3) is "AggD".

### 2. MODE "nosweep" is misleading

**Current:**

```python
"nosweep": "AggO"  # Encodes RESUME_TASK (14), not a cleaning mode
```

The value "AggO" encodes `ModeCtrlRequest.Method.RESUME_TASK` (value 14), which resumes a paused task. This should either be:

- Renamed to "resume" for clarity, or
- Replaced with proper mop-only mode encoding if that's the intent

### 3. LOCATE missing value

**T2278 has:**

```python
RobovacCommand.LOCATE: {
    "code": 160,
    "values": {"locate": "true"},
}
```

**T2267 has:**

```python
RobovacCommand.LOCATE: {
    "code": 160,
}
```

The LOCATE command should have a value defined.

### 4. FAN_SPEED missing MAX_PLUS

Protobuf defines these fan suction levels:

- QUIET = 0
- STANDARD = 1
- TURBO = 2
- MAX = 3
- MAX_PLUS = 4

T2267 is missing MAX_PLUS if the device hardware supports it.

## Missing Commands

| Command | Expected Code | Notes |
| ------- | ------------- | ----- |
| CLEANING_TIME | 6 | For tracking cleaning duration |
| CLEANING_AREA | 7 | For tracking cleaning area (m²) |

## Protobuf Methods Reference

From `control.proto` - `ModeCtrlRequest.Method`:

| Method | Value | Base64 Encoding | T2267 Status |
| ------ | ----- | --------------- | ------------ |
| START_AUTO_CLEAN | 0 | BBoCCAE= | ✓ ("auto") |
| START_SELECT_ROOMS_CLEAN | 1 | Complex* | ❌ Not implemented |
| START_SELECT_ZONES_CLEAN | 2 | Complex* | ❌ Not implemented |
| START_SPOT_CLEAN | 3 | AggD | ❌ Wrong value (uses AA==) |
| START_GOTO_CLEAN | 4 | AggE | ❌ Not implemented |
| START_RC_CLEAN | 5 | AggF | ❌ Not implemented |
| START_GOHOME | 6 | AggG | ✓ ("return") |
| START_SCHEDULE_AUTO_CLEAN | 7 | AggH | ❌ Not implemented |
| START_SCHEDULE_ROOMS_CLEAN | 8 | AggI | ❌ Not implemented |
| START_FAST_MAPPING | 9 | AggJ | ❌ Not implemented |
| START_GOWASH | 10 | AggK | ❌ Not implemented |
| STOP_TASK | 12 | AggM | ✓ (STOP command) |
| PAUSE_TASK | 13 | AggN | ✓ ("pause") |
| RESUME_TASK | 14 | AggO | ✓ (labeled "nosweep") |
| STOP_GOHOME | 15 | AggP | ❌ Not implemented |
| STOP_RC_CLEAN | 16 | AggQ | ❌ Not implemented |

*Complex methods require additional parameters (room IDs, zone coordinates, etc.)

## Base64 Encoding Pattern

The simple method-only commands follow this pattern:

- 2 bytes length prefix + field 1 (method) as varint
- Example: Method 13 (PAUSE_TASK) = `02 08 0D` = "AggN"

| Method Value | Hex Bytes | Base64 |
| ------------ | --------- | ------ |
| 0 | 02 08 00 | AggA |
| 3 | 02 08 03 | AggD |
| 6 | 02 08 06 | AggG |
| 12 | 02 08 0C | AggM |
| 13 | 02 08 0D | AggN |
| 14 | 02 08 0E | AggO |

## Recommended Fixes

### Priority 1 - Critical Fixes

1. **Fix spot mode encoding**

   ```python
   "spot": "AggD"  # START_SPOT_CLEAN (method=3)
   ```

2. **Rename "nosweep" to "resume"** (or implement proper mop-only mode)

   ```python
   "resume": "AggO"  # RESUME_TASK (method=14)
   ```

### Priority 2 - Feature Additions

1. **~~Add BATTERY to homeassistant_features~~** ✅ COMPLETED (2025-01)

   `VacuumEntityFeature.BATTERY` was deprecated in Home Assistant 2025.8 and will stop working in 2026.8. Instead, the integration now uses a dedicated battery sensor entity with `SensorDeviceClass.BATTERY`.

   **Changes made:**
   - `sensor.py`: Updated to use model-specific DPS codes via `vacuum_entity._get_dps_code("BATTERY_LEVEL")` instead of hardcoded `TuyaCodes.BATTERY_LEVEL`
   - T2267 correctly defines `RobovacCommand.BATTERY` with code `163`
   - Battery level is now exposed as a separate sensor entity linked to the vacuum device

   See: [Vacuum battery properties are deprecated](https://developers.home-assistant.io/blog/2025/07/02/vacuum-battery-properties-deprecated/)

2. **Add LOCATE value**

   ```python
   RobovacCommand.LOCATE: {
       "code": 160,
       "values": {"locate": True},
   },
   ```

### Priority 3 - Enhanced Features

1. **Add CLEANING_TIME and CLEANING_AREA**

   ```python
   robovac_features = (
       ...
       | RoboVacEntityFeature.CLEANING_TIME
       | RoboVacEntityFeature.CLEANING_AREA
   )

   # Commands
   RobovacCommand.CLEANING_TIME: {"code": 6},
   RobovacCommand.CLEANING_AREA: {"code": 7},
   ```

2. **Add ROOM and ZONE features** if device supports room/zone cleaning

   ```python
   robovac_features = (
       ...
       | RoboVacEntityFeature.ROOM
       | RoboVacEntityFeature.ZONE
   )
   ```

## Status Values Reference

T2267 currently supports these status values:

| Base64 Code | Human Readable | Activity |
| ----------- | -------------- | -------- |
| BgoAEAUyAA== | Cleaning | CLEANING |
| BgoAEAVSAA== | Positioning | CLEANING |
| CAoAEAUyAggB | Paused | PAUSED |
| AggB | Paused | PAUSED |
| CAoCCAEQBTIA | Room Cleaning | CLEANING |
| CAoCCAEQBVIA | Room Positioning | CLEANING |
| CgoCCAEQBTICCAE= | Room Paused | PAUSED |
| CAoCCAIQBTIA | Zone Cleaning | CLEANING |
| CAoCCAIQBVIA | Zone Positioning | CLEANING |
| CgoCCAIQBTICCAE= | Zone Paused | PAUSED |
| BAoAEAY= | Remote Control | CLEANING |
| BBAHQgA= | Heading Home | RETURNING |
| BBADGgA= | Charging | DOCKED |
| BhADGgIIAQ== | Completed | DOCKED |
| AA== | Standby | IDLE |
| AhAB | Sleeping | IDLE |
| BQgNEIsB | Off Ground | ERROR |

## Comparison with Similar Models

### T2278 (L60 Hybrid SES) has additional

- CLEANING_TIME feature
- CLEANING_AREA feature
- AUTO_RETURN feature
- ROOM feature
- ZONE feature
- MAP feature
- STOP command in MODE values

### T2080 (S1 Pro) has additional

- Station-related status values (Adding Water, Drying Mop, Washing Mop, etc.)
- MOP_LEVEL command
- More comprehensive error handling

## Additional Features

### Status Patterns

T2267 implements `status_patterns` for matching dynamic protobuf-encoded status values:

```python
status_patterns = [
    ("DA", "FSAA==", "Positioning"),  # Matches positioning codes with embedded timestamps
]
```

### Error Patterns

T2267 implements `error_patterns` to filter false error states:

```python
error_patterns = [
    ("DA", "FSAA==", "no_error"),  # Positioning status sent on ERROR DPS
]
```

## Notes

- Battery level is exposed via a dedicated sensor entity (Home Assistant 2025.8+ pattern) using model-specific DPS code 163
- T2267 uses protobuf-encoded values for MODE commands
- Both T2267 and T2320 now use protobuf encoding for control commands
