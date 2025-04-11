---
name: Add New RoboVac Model
about: Request support for a new Eufy RoboVac model
title: "[MODEL] Add support for RoboVac model XYZ"
labels: new model, enhancement
assignees: ''

---

## RoboVac Model Code

Please provide the exact model code for your RoboVac (e.g., T2103, T2250). You can usually find this in the Eufy app or on the device itself.

Model Code:

## RoboVac Series (if known)

Based on the [Contributing Guide](https://github.com/damacus/robovac/blob/main/README.md#adding-support-for-new-robovac-models), which series (C, G, L, X) do you believe this model belongs to, or what features does it seem similar to?

Estimated Series:

## Observed Features

What features have you observed working with this model in the Eufy app? (e.g., Edge cleaning, Boost IQ, Mapping, Room cleaning, Consumable tracking)

Features:

## Connection Details

Are you able to retrieve the `localKey` and `devId` for this device using methods like the [Eufy Security Web API](https://github.com/matijse/eufy-ha-mqtt-bridge/wiki/Obtaining-your-Local-Key-and-Device-ID)? (This helps confirm Tuya compatibility)

Connection Successful: [Yes/No/Unknown]

## Debug Logs

If possible, please enable debug logging for `custom_components.robovac` in Home Assistant, attempt to add the vacuum (even if it fails or doesn't fully work), and provide the relevant logs.

```log
PASTE LOGS HERE
```

## Additional Context

Add any other relevant information, such as links to product pages or observed behaviors.
