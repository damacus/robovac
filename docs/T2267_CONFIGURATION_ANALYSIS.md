# T2267 (RoboVac L60) Configuration Analysis

This document analyzes the T2267 vacuum configuration against the proto-reference files to identify potentially missing settings and features.

## Current Configuration

### DPS Codes Defined

| Command | Code | Has Values |
|---------|------|------------|
| MODE | 152 | ✓ (auto, pause, Spot, return, Nosweep) |
| STATUS | 153 | ✓ (base64 encoded states) |
| DIRECTION | 155 | ✓ (brake, forward, back, left, right) |
| START_PAUSE | 156 | ✗ |
| DO_NOT_DISTURB | 157 | ✗ |
| FAN_SPEED | 158 | ✓ (quiet, standard, turbo, max, boost_iq) |
| BOOST_IQ | 159 | ✗ |
| LOCATE | 160 | ✗ |
| BATTERY | 163 | ✗ |
| CONSUMABLES | 168 | ✗ |
| RETURN_HOME | 173 | ✗ |
| ERROR | 177 | ✗ |

### Features Enabled

**Home Assistant Features:**
- `VacuumEntityFeature.FAN_SPEED`
- `VacuumEntityFeature.LOCATE`
- `VacuumEntityFeature.PAUSE`
- `VacuumEntityFeature.RETURN_HOME`
- `VacuumEntityFeature.SEND_COMMAND`
- `VacuumEntityFeature.START`
- `VacuumEntityFeature.STATE`
- `VacuumEntityFeature.STOP`

**RoboVac Features:**
- `RoboVacEntityFeature.DO_NOT_DISTURB`
- `RoboVacEntityFeature.BOOST_IQ`

---

## Missing Commands (from proto-reference)

### 1. CLEANING_TIME / CLEANING_AREA
**Source:** `work_status.proto`

The proto shows `elapsed_time` and `area` fields in cleaning status messages. The T2268 model has these features enabled, but T2267 does not.

Would require DPS codes for time/area tracking to be identified.

### 2. MOP_LEVEL
**Source:** `clean_param.proto`

If the model supports mopping, the following levels are available:
- LOW = 0
- MIDDLE = 1
- HIGH = 2

Not present in T2267 configuration.

### 3. AUTO_RETURN
**Source:** `control.proto`

Resume cleaning after charging (breakpoint continuation). The T2268 model has this feature; T2267 does not.

---

## Missing Features

### 1. VacuumEntityFeature.CLEAN_SPOT
T2267 has "Spot" mode value defined but doesn't expose the `CLEAN_SPOT` feature flag.

**Comparison:** T2268 has `VacuumEntityFeature.CLEAN_SPOT` enabled.

### 2. RoboVacEntityFeature.CLEANING_TIME
**Proto reference:** `elapsed_time` in WorkStatus message

Not enabled in T2267.

### 3. RoboVacEntityFeature.CLEANING_AREA
**Proto reference:** `area` field in cleaning status

Not enabled in T2267.

### 4. RoboVacEntityFeature.CONSUMABLES
T2267 has CONSUMABLES command defined (code 168) but the feature flag is not set in `robovac_features`.

**Proto reference** (`consumable.proto`) shows available consumables:
- Side brush
- Rolling brush
- Filter mesh
- Scraper
- Sensor
- Mop
- Dust bag

### 5. RoboVacEntityFeature.EDGE / SMALL_ROOM
T2267 MODE has "Nosweep" but no edge or small room modes.

Could potentially add edge cleaning support if the device supports it.

---

## Missing Mode Values

Based on `control.proto` ModeCtrlRequest:

| T2267 Mode | Proto Equivalent | Status |
|------------|------------------|--------|
| auto | START_AUTO_CLEAN | ✓ Present |
| pause | PAUSE_TASK | ✓ Present |
| Spot | START_SPOT_CLEAN | ✓ Present |
| return | START_GOHOME | ✓ Present |
| Nosweep | - | ✓ Present |
| - | edge | **Missing** |
| - | small_room | **Missing** |

### Additional Modes from Proto (if supported by hardware)

From `work_status.proto` WorkStatus.Mode:
- `AUTO` - Global auto cleaning
- `SELECT_ROOM` - Selected room cleaning
- `SELECT_ZONE` - Selected zone cleaning
- `SPOT` - Spot cleaning
- `FAST_MAPPING` - Fast mapping
- `GLOBAL_CRUISE` - Whole house cruise
- `ZONES_CRUISE` - Selected zones cruise
- `POINT_CRUISE` - Point cruise (precise arrival)
- `SCENE` - Scene cleaning
- `SMART_FOLLOW` - Smart follow

---

## Missing Activity Mapping

T2267 lacks an `activity_mapping` dictionary to translate STATUS values to `VacuumActivity` states.

Based on `work_status.proto`, a suggested mapping would be:

```python
activity_mapping = {
    "Standby": VacuumActivity.IDLE,
    "Sleep": VacuumActivity.IDLE,
    "Charging": VacuumActivity.DOCKED,
    "Cleaning": VacuumActivity.CLEANING,
    "GoHome": VacuumActivity.RETURNING,
    "Paused": VacuumActivity.PAUSED,
    "Fault": VacuumActivity.ERROR,
    "RemoteCtrl": VacuumActivity.CLEANING,
    "FastMapping": VacuumActivity.CLEANING,
    "Cruising": VacuumActivity.CLEANING,
}
```

**Note:** The T2267 uses base64-encoded protobuf STATUS values, so the mapping would need to decode these values first.

---

## Missing Settings (from unisetting.proto)

The following settings are available in the proto but not exposed in T2267:

| Setting | Description | Proto Field |
|---------|-------------|-------------|
| Child Lock | Prevent accidental button presses | `children_lock` |
| AI See | AI object recognition | `ai_see` |
| Pet Mode | Pet-specific cleaning behavior | `pet_mode_sw` |
| Poop Avoidance | Avoid pet waste | `poop_avoidance_sw` |
| Multi-map | Support multiple floor maps | `multi_map_sw` |
| Cruise Continue | Resume cruise after interruption | `cruise_continue_sw` |

---

## Summary

| Category | Missing Item | Priority | Notes |
|----------|--------------|----------|-------|
| Config | `activity_mapping` | **High** | Would improve state reporting |
| Feature | `CLEAN_SPOT` | Medium | Mode exists, feature flag missing |
| Mode | `edge` | Medium | Common cleaning mode |
| Mode | `small_room` | Medium | Common cleaning mode |
| Feature | `CONSUMABLES` flag | Low | Command exists, flag missing |
| Feature | `CLEANING_TIME` | Low | Requires DPS code discovery |
| Feature | `CLEANING_AREA` | Low | Requires DPS code discovery |
| Command | `AUTO_RETURN` | Low | Breakpoint continuation |
| Command | `MOP_LEVEL` | Unknown | Only if hardware supports mopping |

---

## Recommendations

1. **Add `activity_mapping`** - This would significantly improve Home Assistant state reporting. Requires decoding the base64 STATUS values to understand the state format.

2. **Enable `CLEAN_SPOT` feature** - The "Spot" mode already exists; just need to add the feature flag.

3. **Enable `CONSUMABLES` feature** - The command is already defined (code 168); add the feature flag to expose consumable data.

4. **Test edge/small_room modes** - Try adding these mode values to see if the device responds.

---

## References

- `proto-reference/work_status.proto` - Work status and state definitions
- `proto-reference/clean_param.proto` - Cleaning parameters (fan, mop, carpet strategy)
- `proto-reference/control.proto` - Mode control commands
- `proto-reference/consumable.proto` - Consumables tracking
- `proto-reference/unisetting.proto` - Device settings
- `proto-reference/error_code_list_t2265.proto` - T22xx series error codes
