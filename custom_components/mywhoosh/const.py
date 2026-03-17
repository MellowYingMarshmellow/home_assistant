"""Constants for the MyWhoosh integration."""

DOMAIN = "mywhoosh"
DEFAULT_SCAN_INTERVAL = 300   # 5 minutes
ACTIVE_SCAN_INTERVAL  = 30    # 30 s when player is online/riding

PUBLIC_API   = "https://services.mywhoosh.com"
MAIN_API     = f"{PUBLIC_API}/http-service/v1"
LOGIN_URL    = f"{PUBLIC_API}/http-service/api/login"
PLAYER_DATA_URL      = f"{MAIN_API}/player/player-data"
PLAYER_DISTANCE_URL  = f"{MAIN_API}/player/player-distance"
FRIENDS_URL          = f"{MAIN_API}/player/my-friends"

PLATFORM         = "Android"
ACTION_LOGIN     = 1001
ACTION_GET_DATA  = 1052
