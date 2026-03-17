# Home Assistant Custom Integrations

A collection of custom Home Assistant integrations installable via [HACS](https://hacs.xyz).

---

## Integrations

| Integration | Type | Description |
|-------------|------|-------------|
| [PainCave](#paincave) | Local polling | ANT+/Bluetooth sensor hub integration |
| [Intervals ICU](#intervals-icu) | Cloud polling | Training analytics & wellness tracking |
| [MyWhoosh](#mywhoosh) | Cloud polling | Indoor cycling platform stats |

---

## Installation via HACS

1. Open HACS in Home Assistant
2. Go to **Integrations** → ⋮ (menu) → **Custom repositories**
3. Add `https://github.com/MellowYingMarshmellow/home_assistant` as category **Integration**
4. Click **Download** on the repository
5. Restart Home Assistant
6. Go to **Settings → Devices & Services → Add Integration** and search for the integration you want

---

## PainCave

Connects your [PainCave](https://github.com/MellowYingMarshmellow/home_assistant/tree/main/custom_components/paincave) ANT+/Bluetooth sensor hub to Home Assistant.

### What it creates

| Entity | Description |
|--------|-------------|
| `sensor` | One per saved sensor — power (W), heart rate (bpm), speed (km/h), cadence, etc. |
| `switch` | Enable/disable individual sensors, ANT+ scanning, BLE scanning |
| `binary_sensor` | ANT+ stick connected, BLE adapter active |

### Setup

1. **Settings → Devices & Services → Add Integration → PainCave**
2. Enter:
   - **URL** — `http://<pi-ip>:5000`
   - **Email** — your PainCave account email
   - **Password** — your PainCave account password

Polling interval defaults to 5 seconds (configurable in `const.py`).

---

## Intervals ICU

Syncs your [Intervals.icu](https://intervals.icu) training data to Home Assistant sensors, and exposes HA services to push wellness data back.

### What it creates

Sensors for your athlete metrics: fitness, fatigue, form (CTL/ATL/TSB), recent activity stats, and more.

### Setup

1. **Settings → Devices & Services → Add Integration → Intervals ICU**
2. Enter:
   - **Athlete ID** — from your Intervals.icu profile URL (e.g. `i12345`)
   - **API Key** — from Settings → Developer Settings

### Services

| Service | Description |
|---------|-------------|
| `intervals_icu.update_wellness` | Push weight, HRV, sleep, steps, mood, etc. for a date |
| `intervals_icu.create_manual_activity` | Create a manual activity entry |
| `intervals_icu.update_activity` | Update name, description, or RPE on an existing activity |
| `intervals_icu.update_athlete` | Update athlete profile fields |
| `intervals_icu.update_sport_settings` | Update FTP, LTHR, or threshold pace per sport |

---

## MyWhoosh

Pulls your [MyWhoosh](https://www.mywhoosh.com) indoor cycling stats into Home Assistant.

### What it creates

Sensors for distance, ride count, fitness rank, and more. Number entities for adjustable bike settings.

### Setup

1. **Settings → Devices & Services → Add Integration → MyWhoosh**
2. Enter your MyWhoosh **email** and **password**

Polling interval is 5 minutes at rest, 30 seconds when actively riding.

---

## Manual Installation (without HACS)

```bash
# Copy the component(s) you want into your HA config directory
cp -r custom_components/paincave      /config/custom_components/
cp -r custom_components/intervals_icu /config/custom_components/
cp -r custom_components/mywhoosh      /config/custom_components/
```

Then restart Home Assistant.
