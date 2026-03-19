# Home Assistant Custom Integrations & Add-ons

A collection of custom Home Assistant integrations (via HACS) and add-ons (via Supervisor).

---

## Contents

| Name | Type | Install via | Description |
|------|------|-------------|-------------|
| [PainCave](#paincave) | Integration | HACS | ANT+/Bluetooth sensor hub |
| [Intervals ICU](#intervals-icu) | Integration | HACS | Training analytics & wellness tracking |
| [MyWhoosh](#mywhoosh) | Integration | HACS | Indoor cycling platform stats |
| [Mermaid Live Editor](#mermaid-live-editor) | Add-on | Supervisor | Mermaid diagram editor in your browser |

---

## Add-ons

### Installing this repository as an Add-on source

> Requires Home Assistant OS or Supervised installation (Add-on Supervisor must be present).

1. Go to **Settings → Add-ons → Add-on Store**
2. Click **⋮ (menu) → Repositories**
3. Add: `https://github.com/MellowYingMarshmellow/home_assistant`
4. The add-ons from this repo will appear in the store

---

### Mermaid Live Editor

Run the [Mermaid Live Editor](https://github.com/mermaid-js/mermaid-live-editor) as a local
add-on. Create flowcharts, sequence diagrams, Gantt charts, ERDs, C4 diagrams, and every other
Mermaid diagram type — accessible from your browser on your local network.

**No cloud dependency. Runs entirely on your HA host.**

#### Install

1. Add this repository (instructions above)
2. Find **Mermaid Live Editor** in the Add-on Store
3. Click **Install** — the build takes ~2–3 minutes (clones source, builds with Node 22, packages with nginx)
4. Click **Start**
5. Open `http://homeassistant.local:8099` to confirm it's running

#### Sidebar

The addon uses HA's built-in ingress, so the **Mermaid Editor** entry appears automatically in the left sidebar after the addon starts. No `configuration.yaml` changes needed.

#### What runs inside

| | |
|---|---|
| Port | `8099` |
| Architectures | amd64, aarch64, armv7, armhf |
| Node.js | 22 (inside Docker — not required on your machine) |
| Java | Not required |
| Base image | `ghcr.io/home-assistant/amd64-base` (per arch) |
| Web server | nginx |

---

## Integrations (HACS)

### Installing via HACS

1. Open HACS in Home Assistant
2. Go to **Integrations → ⋮ → Custom repositories**
3. Add `https://github.com/MellowYingMarshmellow/home_assistant` as category **Integration**
4. Click **Download** on the repository
5. Restart Home Assistant
6. Go to **Settings → Devices & Services → Add Integration** and search for the integration you want

---

### PainCave

Connects your [PainCave](https://github.com/MellowYingMarshmellow/home_assistant/tree/main/custom_components/paincave) ANT+/Bluetooth sensor hub to Home Assistant.

#### What it creates

| Entity | Description |
|--------|-------------|
| `sensor` | One per saved sensor — power (W), heart rate (bpm), speed (km/h), cadence, etc. |
| `switch` | Enable/disable individual sensors, ANT+ scanning, BLE scanning |
| `binary_sensor` | ANT+ stick connected, BLE adapter active |

#### Setup

1. **Settings → Devices & Services → Add Integration → PainCave**
2. Enter:
   - **URL** — `http://<pi-ip>:5000`
   - **Email** — your PainCave account email
   - **Password** — your PainCave account password

Polling interval defaults to 5 seconds.

---

### Intervals ICU

Syncs your [Intervals.icu](https://intervals.icu) training data to Home Assistant sensors, and exposes HA services to push wellness data back.

#### What it creates

Sensors for your athlete metrics: fitness, fatigue, form (CTL/ATL/TSB), recent activity stats, and more.

#### Setup

1. **Settings → Devices & Services → Add Integration → Intervals ICU**
2. Enter:
   - **Athlete ID** — from your Intervals.icu profile URL (e.g. `i12345`)
   - **API Key** — from Settings → Developer Settings

#### Services

| Service | Description |
|---------|-------------|
| `intervals_icu.update_wellness` | Push weight, HRV, sleep, steps, mood, etc. for a date |
| `intervals_icu.create_manual_activity` | Create a manual activity entry |
| `intervals_icu.update_activity` | Update name, description, or RPE on an existing activity |
| `intervals_icu.update_athlete` | Update athlete profile fields |
| `intervals_icu.update_sport_settings` | Update FTP, LTHR, or threshold pace per sport |

---

### MyWhoosh

Pulls your [MyWhoosh](https://www.mywhoosh.com) indoor cycling stats into Home Assistant.

#### What it creates

Sensors for distance, ride count, fitness rank, and more. Number entities for adjustable bike settings.

#### Setup

1. **Settings → Devices & Services → Add Integration → MyWhoosh**
2. Enter your MyWhoosh **email** and **password**

Polling interval is 5 minutes at rest, 30 seconds when actively riding.

---

## Manual Installation (integrations, without HACS)

```bash
cp -r custom_components/paincave      /config/custom_components/
cp -r custom_components/intervals_icu /config/custom_components/
cp -r custom_components/mywhoosh      /config/custom_components/
```

Then restart Home Assistant.
