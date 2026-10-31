# Map camera

X8-Pro-class devices (tested on a T2276) expose a `camera.<name>_map`
entity: a PNG render of the robot's current cloud floor-plan, one color
per room. This document covers enabling it and wiring it up to an
interactive, tap-to-clean room map in Lovelace.

## Enabling the camera

The camera needs a logged-in Eufy cloud session, separate from the local
Tuya connection the rest of the integration uses. There's no config-flow
UI for this yet (see "Limitations" below) -- add the credentials directly
to the vacuum's entry in `.storage/core.config_entries`:

```json
{
  "id": "...",
  "ip_address": "...",
  "local_key": "...",
  "model": "T2276",
  "name": "Freddy",
  "username": "you@example.com",
  "password": "your-eufy-password",
  "client_id": "your-eufy-client-id",
  "region": "EU",
  "country_code": "31"
}
```

Stop Home Assistant core before editing this file and start it again
after -- it's loaded into memory at startup and periodically flushed
back to disk, so an edit made while core is running can get silently
overwritten.

`camera.<name>_map` only gets created for vacuums that have both
`username` and `password` set; everything else about the integration
works the same with or without this.

## Interactive room map in Lovelace

The camera entity alone is a static image. For tap-to-clean rooms, pair
it with [lovelace-xiaomi-vacuum-map-card][card], which supports a
generic/non-Xiaomi camera entity plus manually defined room polygons --
no vacuum-reported room data or pixel/millimetre calibration needed.

[card]: https://github.com/PiotrMachowski/lovelace-xiaomi-vacuum-map-card

### 1. Find each room's pixel outline

The camera renders at 4x the raw map resolution (see `map_fetch.py` /
`camera.py` for the render scale). Open the map image at full size and
note each room's rectangle in pixel coordinates, or compute it from a
raw `lay.bin` capture -- for each room id, the min/max x and y of pixels
whose `byte >> 2` equals that id, then multiply by the render scale.

### 2. Card config

```yaml
type: custom:xiaomi-vacuum-map-card
entity: vacuum.freddy
map_source:
  camera: camera.freddy_map
calibration_source:
  identity: true
map_modes:
  - name: Clean room
    icon: mdi:home-floor-1
    selection_type: ROOM
    service_call_schema:
      service: script.turn_on
      service_data:
        entity_id: script.freddy_clean_[[room]]
    predefined_selections:
      - id: 1
        outline: [[368, 8], [712, 8], [712, 192], [368, 192]]
        label:
          text: Kitchen
          x: 540
          y: 100
        variables:
          room: kitchen
      # one predefined_selections entry per room, same shape
```

Key points:

- `calibration_source: identity` means outline/label coordinates are
  plain image pixels -- no vacuum-coordinate calibration step, which is
  normally the card's most error-prone part.
- `service_call_schema` is templated once and reused for every room;
  each room's own `variables` fill in `[[room]]` (or whatever variable
  names you use) at tap time. This example calls a per-room script
  (`script.<vacuum>_clean_<room>`) rather than the vacuum's own
  `room_clean` command directly, so it can also apply per-room options
  (fan speed, mop mode, etc.) if you have any.
- The card ships no editor support for this generic mode -- write the
  YAML by hand (Edit Dashboard → Add Card → Manual).

## Limitations

- No config-flow UI for the Eufy credentials yet; see "Enabling the
  camera" above.
- The camera updates on a 15-minute interval by default, or on demand
  via `homeassistant.update_entity` -- it's a floor-plan snapshot, not a
  live feed.
- Only tested against a T2276 (X8 Pro SES). The `lay.bin` format and
  storage-config API are expected to be the same across the X8-Pro
  class, but that's unverified on other models.
