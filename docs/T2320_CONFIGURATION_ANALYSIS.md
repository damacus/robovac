# T2320 (Eufy X9 Pro with Auto-Clean Station) Configuration Analysis

This document reviews the T2320 vacuum configuration and identifies missing or incorrect features.

## Device Overview

The T2320 is the Eufy Robot Vacuum and Mop X9 Pro with Auto-Clean Station. It features:

- Auto-clean station with mop washing and drying
- Dust collection
- Water tank management (clean and dirty water)
- Advanced navigation with LiDAR, camera, and 3D TOF sensors

## Current Features

### Home Assistant Features (`VacuumEntityFeature`)

| Feature | Status | Notes |
|---------|--------|-------|
| FAN_SPEED | ✓ | Code 154 |
| LOCATE | ✓ | Code 160, Fixed - was conflicting with RETURN_HOME |
| PAUSE | ✓ | Via START_PAUSE code 2 |
| RETURN_HOME | ✓ | Code 153 with boolean |
| SEND_COMMAND | ✓ | |
| START | ✓ | Via START_PAUSE code 2 |
| STATE | ✓ | Code 173 with protobuf values |
| STOP | ✓ | |
| BATTERY | ❌ Missing | Command exists (code 172) but feature flag not set |
| CLEAN_SPOT | ❌ Missing | Device likely supports spot cleaning |

### RoboVac Features (`RoboVacEntityFeature`)

| Feature | Status | Notes |
|---------|--------|-------|
| DO_NOT_DISTURB | ✓ | |
| BOOST_IQ | ✓ | Code 159 |
| CLEANING_TIME | ✓ | Code 6 |
| CLEANING_AREA | ✓ | Code 7 |
| MAP | ✓ | |
| ROOM | ❌ Missing | Device supports room cleaning (status values exist) |
| ZONE | ❌ Missing | Device supports zone cleaning (status values exist) |
| CONSUMABLES | ❌ Missing | X9 Pro has consumables tracking |
| AUTO_RETURN | ❌ Missing | |

## Current Commands

| Command | DPS Code | Values | Status |
|---------|----------|--------|--------|
| START_PAUSE | 2 | start=True, pause=False | ✓ |
| MODE | 152 | auto, return, pause, small_room, single_room | ⚠️ String values |
| STATUS | 173 | Multiple protobuf-encoded values | ✓ |
| RETURN_HOME | 153 | return_home=True | ✓ |
| FAN_SPEED | 154 | quiet, standard, turbo, max, boost_iq | ✓ |
| LOCATE | 160 | locate=True | ✓ Fixed |
| BATTERY | 172 | - | ✓ |
| ERROR | 169 | - | ✓ |
| BOOST_IQ | 159 | - | ✓ |
| CLEANING_TIME | 6 | - | ✓ |
| CLEANING_AREA | 7 | - | ✓ |

## DPS Code Differences from Other Models

T2320 uses a different DPS code scheme than T2267/T2278:

| Command | T2267/T2278 | T2320 | Notes |
|---------|-------------|-------|-------|
| STATUS | 153 | 173 | Different code |
| FAN_SPEED | 158 | 154 | Different code |
| BATTERY | 163 | 172 | Different code |
| ERROR | 177 | 169 | Different code |
| RETURN_HOME | 152 (via MODE) | 153 (boolean) | Different approach |

## Issues Found

### 1. MODE uses string values instead of protobuf

T2320 uses plain string values for MODE:

```python
"values": {
    "auto": "auto",
    "return": "return",
    "pause": "pause",
    "small_room": "small_room",
    "single_room": "single_room"
}
```

This differs from T2267/T2278 which use protobuf-encoded values. This may be correct for T2320's firmware, but should be verified.

### 2. Missing STOP command

Unlike T2267 which has a dedicated STOP command with protobuf encoding, T2320 relies on `async_stop()` calling `async_return_to_base()`. Consider adding:

```python
RobovacCommand.STOP: {
    "code": 152,  # or appropriate code
    "values": {
        "stop": "stop",  # or protobuf value if supported
    },
},
```

### 3. Missing MOP_LEVEL command

The X9 Pro has mopping capabilities but no MOP_LEVEL command is defined. Based on T2080:

```python
RobovacCommand.MOP_LEVEL: {
    "code": 10,  # verify correct code for T2320
    "values": {
        "low": "low",
        "middle": "middle",
        "high": "high",
    },
},
```

### 4. Missing DIRECTION command

No remote control direction command is defined:

```python
RobovacCommand.DIRECTION: {
    "code": ???,  # needs discovery
    "values": {
        "forward": "forward",
        "back": "back",
        "left": "left",
        "right": "right",
        "brake": "brake",
    },
},
```

### 5. Missing CONSUMABLES command

The X9 Pro tracks consumables but no command is defined:

```python
RobovacCommand.CONSUMABLES: {
    "code": ???,  # needs discovery
},
```

## Missing Features Compared to T2080 (S1 Pro)

T2080 has these additional features that T2320 might support:

| Feature | T2080 Code | T2320 Status |
|---------|------------|--------------|
| MOP_LEVEL | 10 | ❌ Not implemented |
| DIRECTION | 176 | ❌ Not implemented |

## Error Codes Reference

From `error_code_list_t2320.proto`, the X9 Pro supports these error categories:

### Robot Errors (E001-E055)

| Code | Description |
|------|-------------|
| E001 | Crash buffer is stuck |
| E002 | Wheel is stuck |
| E003 | Side brush is stuck |
| E004 | Rolling brush is stuck |
| E005 | Host machine is trapped |
| E006 | Machine is trapped, move to start |
| E007 | Wheel is overhanging |
| E008 | Battery too low, shutting down |
| E013 | Host is tilted |
| E014 | Dust box/filter missing |
| E017 | Forbidden area detected |
| E018 | Laser protection cover stuck |
| E019 | Laser sensor stuck or tangled |
| E020 | Laser sensor blocked |
| E021 | Docking failed |
| E026 | Insufficient power for scheduled start |
| E031 | Foreign objects in suction port |
| E032 | Mop holder rotating motor stuck |
| E033 | Mop bracket lift motor stuck |
| E039 | Positioning failed |
| E040 | Mop cloth dislodged |
| E041 | Air drying heater abnormal |
| E050 | Accidentally on carpet |
| E051 | Camera blocked |
| E052 | Unable to leave station |
| E055 | Exploring station failed |

### Station Errors (E070-E083)

| Code | Description |
|------|-------------|
| E070 | Clean dust collector and filter |
| E071 | Wall sensor abnormal |
| E072 | Robot water tank insufficient |
| E073 | Station dirty tank full |
| E074 | Station clean water insufficient |
| E075 | Water tank absent |
| E076 | Camera abnormal |
| E077 | 3D TOF abnormal |
| E078 | Ultrasonic sensor abnormal |
| E079 | Station clean tray not installed |
| E080 | Robot-station communication abnormal |
| E081 | Sewage tank leaking |
| E082 | Clean station tray |
| E083 | Poor charging contact |

### Hardware Errors (E101-E119)

| Code | Description |
|------|-------------|
| E101 | Battery abnormal |
| E102 | Wheel module abnormal |
| E103 | Side brush module abnormal |
| E104 | Fan abnormal |
| E105 | Roller brush motor abnormal |
| E106 | Host pump abnormal |
| E107 | Laser sensor abnormal |
| E111 | Rotation motor abnormal |
| E112 | Lift motor abnormal |
| E113 | Water spraying device abnormal |
| E114 | Water pumping device abnormal |
| E117 | Ultrasonic sensor abnormal |
| E119 | WiFi or Bluetooth abnormal |

## Prompt Codes Reference

| Code | Description |
|------|-------------|
| P001 | Start scheduled cleaning |
| P003 | Battery low, returning to base |
| P004 | Positioning failed, rebuilding map |
| P005 | Positioning failed, mission ended |
| P006 | Some areas unreachable |
| P007 | Path planning failed |
| P009 | Base station exploration failed |
| P010 | Positioning successful |
| P011 | Task finished, returning |
| P012 | Cannot start task while on station |
| P013 | Scheduled cleaning failed (busy) |
| P014 | Map updating, try later |
| P015 | Mop washing complete, resuming |
| P016 | Low battery, charge first |
| P017 | Mop cleaning completed |

## Status Values Reference

T2320 supports these status values:

### Cleaning States

| Base64 Code | Human Readable |
|-------------|----------------|
| BgoAEAUyAA== | Auto Cleaning |
| BgoAEAVSAA== | Positioning |
| CgoAEAUyAhABUgA= | Auto Cleaning |
| CgoAEAkaAggBMgA= | Auto Cleaning |
| CAoCCAEQBTIA | Room Cleaning |
| CAoCCAEQBVIA | Room Positioning |
| CgoCCAEQBTICCAE= | Room Paused |
| CAoCCAIQBTIA | Zone Cleaning |
| CAoCCAIQBVIA | Zone Positioning |
| CgoCCAIQBTICCAE= | Zone Paused |

### Navigation States

| Base64 Code | Human Readable |
|-------------|----------------|
| BBAHQgA= | Heading Home |
| AgoA | Heading Home |
| CgoAEAcyAggBQgA= | Temporary Return |
| DAoCCAEQBzICCAFCAA== | Temporary Return |

### Docked/Station States

| Base64 Code | Human Readable |
|-------------|----------------|
| BBADGgA= | Charging |
| BhADGgIIAQ== | Completed |
| DAoCCAEQAxoAMgIIAQ== | Charge Mid-Clean |
| DAoAEAUaADICEAFSAA== | Adding Water |
| BhAJOgIQAg== | Drying Mop |
| BhAJOgIQAQ== | Washing Mop |
| AhAJ | Removing Dirty Water |
| BRAJ+gEA | Emptying Dust |
| DQoCCAEQCTICCAH6AQA= | Remove Dust Mid-Clean |

### Other States

| Base64 Code | Human Readable |
|-------------|----------------|
| CAoAEAUyAggB | Paused |
| AggB | Paused |
| AA== | Standby |
| BhAHQgBSAA== | Standby |
| AhAB | Sleeping |
| BhAGGgIIAQ== | Manual Control |
| BAoAEAY= | Remote Control |
| CAoAEAIyAggB | Error |

## Recommended Fixes

### Priority 1 - Critical

1. **Add BATTERY to homeassistant_features**

   ```python
   homeassistant_features = (
       ...
       | VacuumEntityFeature.BATTERY
   )
   ```

2. **Add CLEAN_SPOT feature and command** (if device supports it)

### Priority 2 - Feature Additions

3. **Add ROOM and ZONE features**

   ```python
   robovac_features = (
       ...
       | RoboVacEntityFeature.ROOM
       | RoboVacEntityFeature.ZONE
   )
   ```

4. **Add MOP_LEVEL command** (verify DPS code)

   ```python
   RobovacCommand.MOP_LEVEL: {
       "code": 10,
       "values": {
           "low": "low",
           "middle": "middle",
           "high": "high",
       },
   },
   ```

5. **Add CONSUMABLES command and feature**

### Priority 3 - Enhanced Features

6. **Add DIRECTION command** for remote control

7. **Add DO_NOT_DISTURB command with DPS code**

   Currently listed in features but no command defined with a code.

## Comparison with Similar Models

### T2080 (S1 Pro) Differences

| Feature | T2080 | T2320 |
|---------|-------|-------|
| STATUS code | 153 | 173 |
| FAN_SPEED code | 158 | 154 |
| BATTERY code | 163 | 172 |
| ERROR code | 106 | 169 |
| LOCATE code | 103 | 160 |
| MODE encoding | Protobuf | String |
| RETURN_HOME | Via MODE (152) | Boolean (153) |

### T2267 (L60) Differences

| Feature | T2267 | T2320 |
|---------|-------|-------|
| MODE encoding | Protobuf | String |
| START_PAUSE | Via MODE (152) | Boolean (2) |
| RETURN_HOME | Via MODE (152) | Boolean (153) |
| Station features | No | Yes (washing, drying, dust) |

## Notes

- T2320 uses a hybrid approach: some commands use protobuf-encoded STATUS values while MODE uses plain strings
- The DPS code scheme differs significantly from T2267/T2278 family
- Station-related status values are comprehensive for the auto-clean station features
- Error codes are specific to the X9 Pro model with station-related errors
