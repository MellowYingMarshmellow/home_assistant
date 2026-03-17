"""Constants for the PainCave integration."""

DOMAIN = "paincave"

CONF_URL      = "url"
CONF_EMAIL    = "email"
CONF_PASSWORD = "password"

DEFAULT_SCAN_INTERVAL = 5  # seconds

# Primary state field and metadata per sensor type
SENSOR_TYPE_META = {
    "heart-rate":            {"state_key": "heartRate",   "unit": "bpm",  "device_class": None,    "icon": "mdi:heart-pulse"},
    "power":                 {"state_key": "power",        "unit": "W",    "device_class": "power", "icon": "mdi:lightning-bolt"},
    "speed":                 {"state_key": "speed",        "unit": "km/h", "device_class": "speed", "icon": "mdi:speedometer"},
    "cadence":               {"state_key": "cadence",      "unit": "rpm",  "device_class": None,    "icon": "mdi:rotate-right"},
    "stride-speed-distance": {"state_key": "speed",        "unit": "km/h", "device_class": "speed", "icon": "mdi:run"},
    "treadmill":             {"state_key": "speed",        "unit": "km/h", "device_class": "speed", "icon": "mdi:run"},
    "indoor-bike":           {"state_key": "power",        "unit": "W",    "device_class": "power", "icon": "mdi:bike"},
    "rower":                 {"state_key": "strokeRate",   "unit": "spm",  "device_class": None,    "icon": "mdi:rowing"},
    "csc":                   {"state_key": "cadence",      "unit": "rpm",  "device_class": None,    "icon": "mdi:bike"},
    "rsc":                   {"state_key": "speed",        "unit": "km/h", "device_class": "speed", "icon": "mdi:run"},
}
