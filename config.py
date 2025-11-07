# config.py
#
# All user settings, credentials, and API keys go here.
# This keeps them separate from the main application logic.

# --- WiFi Settings ---
WIFI_SSID = 'NETGEAR93'
WIFI_PASSWORD = 'unevenbird552'

# --- NWS API Settings ---
# Your contact email for the API User-Agent
NWS_API_EMAIL = 'your-email@example.com'
# Your nearest NWS station (KILM is Wilmington/Oak Island)
NWS_STATION_ID = "KILM"

# --- Timezone Settings ---
# Current time is EST (after Nov 5th, 2025)
# Eastern Standard Time (EST) is -5 hours from UTC.
# Eastern Daylight Time (EDT) is -4 hours.
# You'll need to update this when daylight saving changes.
TIMEZONE_OFFSET_HOURS = -5

# --- Lighting Options (Placeholders) ---
# We can use these later to set LED colors from the config
# Example: (R, G, B) values from 0-255
LED_STARTUP_COLOR = (50, 0, 50)   # A dim purple
LED_WIFI_SUCCESS_COLOR = (0, 100, 0) # Green
LED_WIFI_FAIL_COLOR = (100, 0, 0)    # Red
LED_MENU_IDLE_COLOR = (0, 0, 30)     # A dim blue
