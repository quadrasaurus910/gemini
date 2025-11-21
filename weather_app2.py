# weather_app.py
# Minimal update to support startup.py and config.py

import utime
import gc
import urequests
import config # Import the configuration file

# --- Global variables ---
last_exit_time = 0
DEBOUNCE_DELAY_MS = 500
DISPLAY_DURATION_SECONDS = 4
REFRESH_INTERVAL_SECONDS = 15 * 60 

# --- Helper Functions ---

def c_to_f(celsius):
    return (celsius * 9/5) + 32 if celsius is not None else None

def mps_to_mph(mps):
    return mps * 2.23694 if mps is not None else None

def degrees_to_cardinal(d):
    if d is None: return ""
    dirs = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    ix = round(d / (360. / len(dirs)))
    return dirs[ix % len(dirs)]

def check_exit(joy_x_pin):
    global last_exit_time
    current_time = utime.ticks_ms()
    if joy_x_pin.read_u16() < 20000:
        if utime.ticks_diff(current_time, last_exit_time) > DEBOUNCE_DELAY_MS:
            last_exit_time = current_time
            return True
    return False

# --- Core Weather Functions ---

def fetch_and_process_weather(lcd, wlan):
    """Fetches weather data using the existing wlan connection."""
    if not wlan or not wlan.isconnected():
        lcd.clear()
        lcd.putstr("No WiFi!")
        utime.sleep(2)
        return None

    weather_data = []
    response = None
    
    # Build URL from Config
    url = f"https://api.weather.gov/stations/{config.NWS_STATION_ID}/observations/latest"
    headers = {'User-Agent': f'(Pico Build, {config.NWS_API_EMAIL})'}

    try:
        lcd.clear()
        lcd.putstr("Fetching Data...")
        response = urequests.get(url, headers=headers)
        
        if response.status_code == 200:
            lcd.clear()
            lcd.putstr("Data Received!")
            utime.sleep(1)
            
            data = response.json()['properties']
            
            # Define properties to display
            display_properties = [
                "station", "textDescription", "temperature", "windSpeed", 
                "windGust", "relativeHumidity", "timestamp"
            ]

            for prop in display_properties:
                if prop == "station":
                    station_id = data.get('station', '').split('/')[-1]
                    weather_data.append({'name': 'Station ID', 'value': station_id})

                elif prop == "temperature":
                    temp_f = c_to_f(data.get('temperature', {}).get('value'))
                    weather_data.append({'name': 'Temperature', 'value': f"{temp_f:.1f} F" if temp_f is not None else "N/A"})
                
                elif prop == "windSpeed":
                    speed_mph = mps_to_mph(data.get('windSpeed', {}).get('value'))
                    direction_deg = data.get('windDirection', {}).get('value')
                    cardinal_dir = degrees_to_cardinal(direction_deg)
                    display_val = f"{speed_mph:.1f} mph {cardinal_dir}".strip() if speed_mph is not None else "N/A"
                    weather_data.append({'name': 'Wind', 'value': display_val})

                elif prop == "windGust":
                    gust_mph = mps_to_mph(data.get('windGust', {}).get('value'))
                    if gust_mph and gust_mph > 0: # Only show if there is actually a gust
                        weather_data.append({'name': 'Wind Gust', 'value': f"{gust_mph:.1f} mph"})

                elif prop == "relativeHumidity":
                    humidity = data.get('relativeHumidity', {}).get('value')
                    weather_data.append({'name': 'Humidity', 'value': f"{humidity:.1f}%" if humidity is not None else "N/A"})

                elif prop == "textDescription":
                     desc = data.get('textDescription')
                     if desc:
                         weather_data.append({'name': 'Conditions', 'value': desc})

                elif prop == "timestamp":
                    # Simplified timestamp logic
                    ts_str = data.get('timestamp', '')
                    if 'T' in ts_str:
                        time_part = ts_str.split('T')[1].split('+')[0] # HH:MM:SS
                        # Just show the raw UTC time for now to keep this update minimal
                        # (The Clock app will handle complex time logic)
                        weather_data.append({'name': 'Updated (UTC)', 'value': time_part})

        else:
            lcd.clear()
            lcd.putstr("API Error"); lcd.move_to(0, 1); lcd.putstr(f"Status: {response.status_code}")
            utime.sleep(3)
            return None
            
    except Exception as e:
        lcd.clear()
        lcd.putstr("Request Failed"); lcd.move_to(0, 1); lcd.putstr(str(e)[:16])
        utime.sleep(3)
        return None
        
    finally:
        if response:
            response.close()
        gc.collect()

    return weather_data

# --- Main App Entry Point ---

def run_weather_app(lcd, joy_x_pin, wlan):
    """The main loop for the weather app. Now accepts wlan object."""
    last_refresh_time = 0
    weather_display_list = []

    while True:
        current_time = utime.time()

        if not weather_display_list or (current_time - last_refresh_time) > REFRESH_INTERVAL_SECONDS:
            new_data = fetch_and_process_weather(lcd, wlan)
            if new_data:
                weather_display_list = new_data
                last_refresh_time = current_time
            elif not weather_display_list:
                lcd.clear()
                lcd.putstr("Initial fetch"); lcd.move_to(0, 1); lcd.putstr("failed. Exiting")
                utime.sleep(3)
                return 

        for item in weather_display_list:
            lcd.clear()
            lcd.putstr(item['name'])
            lcd.move_to(0, 1)
            lcd.putstr(item['value'])

            for _ in range(DISPLAY_DURATION_SECONDS * 10):
                if check_exit(joy_x_pin):
                    lcd.clear(); lcd.putstr("Back to Menu..."); utime.sleep(1)
                    return
                utime.sleep_ms(100)
