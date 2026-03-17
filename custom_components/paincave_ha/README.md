# PainCave — Home Assistant Integration

Custom integration that connects your [PainCave v2](../paincave_v2) ANT+/Bluetooth sensor hub to Home Assistant.

## What it creates

| Entity type     | Entity                              | Description                                               |
|-----------------|-------------------------------------|-----------------------------------------------------------|
| `sensor`        | One per saved sensor                | Primary metric (power W, heart rate bpm, speed km/h…)     |
| `sensor`        | Secondary fields per sensor type    | e.g. cadence on a power meter, inclination on a treadmill |
| `switch`        | `{Sensor name} Active`              | Enable / disable a sensor (controls is_active + MQTT)     |
| `switch`        | ANT+ Scanning                       | Start / stop ANT+ scan                                    |
| `switch`        | Bluetooth Scanning                  | Start / stop BLE scan                                     |
| `binary_sensor` | ANT+ Stick                          | Whether the USB dongle is connected                       |
| `binary_sensor` | Bluetooth Adapter                   | Whether the BLE adapter is active                         |

All sensor and switch entities are grouped under their **device** in HA (e.g. "Tacx NEO 2") with the hub as the parent device.

Sensors become **unavailable** (greyed out) when disabled or when the device stops transmitting, and come back automatically.

## Installation

### Option A — HACS (manual repository)
1. In HACS → Integrations → ⋮ → Custom repositories
2. Add `https://github.com/your-repo/paincave_ha` as an **Integration**
3. Install "PainCave"
4. Restart HA

### Option B — Manual copy
```bash
# From this folder
cp -r custom_components/paincave /config/custom_components/
```
Then restart Home Assistant.

## Setup

1. **Settings → Devices & Services → Add Integration → PainCave**
2. Enter:
   - **URL** — `http://<pi-ip>:5000` (the PainCave server address)
   - **Email** — your PainCave account email
   - **Password** — your PainCave account password
3. Click Submit

HA will authenticate, pull your saved sensor list, and start polling every 5 seconds.

## Automations

Example — alert when power drops to zero mid-ride:
```yaml
trigger:
  - platform: numeric_state
    entity_id: sensor.tacx_neo_2
    below: 5
    for: "00:00:30"
action:
  - service: notify.mobile_app
    data:
      message: "Power dropped — check your trainer connection"
```

Example — turn off scanning when everyone leaves home:
```yaml
trigger:
  - platform: state
    entity_id: group.family
    to: not_home
action:
  - service: switch.turn_off
    target:
      entity_id:
        - switch.ant_scanning
        - switch.bluetooth_scanning
```

## Polling interval

Default is 5 seconds. To change it, edit `const.py`:
```python
DEFAULT_SCAN_INTERVAL = 5  # seconds
```
