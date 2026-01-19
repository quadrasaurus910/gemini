# circadian.py
# Syncs RGB lighting with local sunrise/sunset times.
# Uses 3 distinct color palettes that stretch/compress based on day length.

import network
import urequests
import ujson
import utime
import machine
from machine import Pin, PWM, ADC

# --- User Configuration ---
# Fallback Fixed Times (in case WiFi fails)
FALLBACK_SUNRISE = 7  # 7:00 AM
FALLBACK_SUNSET = 19  # 7:00 PM
# Joystick Configuration
JOY_EXIT_THRESHOLD = 20000 
JOY_X_PIN = 26

# --- Color Palettes ---
# Format: (R, G, B) tuples
# The code will interpolate between these points evenly within their time block.

# 1. Night (Midnight -> Astronomical Dawn)
# Deep blues, purples, essentially "moonlight"
COLORS_NIGHT = [
    (5, 0, 15),     # Deepest Midnight
    (10, 5, 30),    # Starlight
    (20, 0, 40),    # Deep Violet
    (5, 0, 15),     # Return to dark
]

# 2. Twilight (Dawn -> Sunrise AND Sunset -> Dusk)
# dramatic pinks, purples, oranges
COLORS_TWILIGHT = [
    (20, 0, 50),    # Pre-dawn purple
    (100, 20, 50),  # Red horizon
    (200, 100, 0),  # Orange glow
    (255, 150, 50), # Golden Hour
]

# 3. Day (Sunrise -> Sunset)
# Bright whites, Azures, Warm Yellows
COLORS_DAY = [
    (255, 200, 100), # Morning warm
    (255, 255, 220), # Noon bright white
    (200, 240, 255), # Afternoon blue-white
    (255, 180, 50),  # Late afternoon gold
]

# --- Hardware Init ---
pwm_r = PWM(Pin(16))
pwm_g = PWM(Pin(17))
pwm_b = PWM(Pin(18))
for pwm in [pwm_r, pwm_g, pwm_b]:
    pwm.freq(1000)

def set_rgb(r, g, b):
    # Common Anode (Inverted)
    pwm_r.duty_u16(65535 - (int(r) * 257))
    pwm_g.duty_u16(65535 - (int(g) * 257))
    pwm_b.duty_u16(65535 - (int(b) * 257))

def connect_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        wlan.connect(ssid, password)
        # Wait max 10 seconds
        for _ in range(10):
            if wlan.isconnected(): return True
            utime.sleep(1)
    return wlan.isconnected()

def get_solar_data(lcd):
    """
    1. Gets Lat/Lng from IP.
    2. Gets Solar times from sunrise-sunset.org.
    """
    try:
        # Step 1: Get Location (IP-based)
        lcd.clear()
        lcd.putstr("Locating...")
        r = urequests.get("http://ip-api.com/json/")
        loc_data = r.json()
        r.close()
        lat = loc_data['lat']
        lon = loc_data['lon']
        
        # Step 2: Get Sun Data
        lcd.move_to(0, 1)
        lcd.putstr("Fetching Sun...")
        url = f"https://api.sunrise-sunset.org/json?lat={lat}&lng={lon}&formatted=0"
        r = urequests.get(url)
        sun_data = r.json()['results']
        r.close()
        
        # Parse ISO8601 strings (2023-01-01T07:23:10+00:00) to simple local hour floats
        def parse_iso_hour(iso_str):
            # Extract HH:MM:SS part
            time_part = iso_str.split('T')[1].split('+')[0]
            h, m, s = map(int, time_part.split(':'))
            # Convert to decimal hour (e.g., 7.5 = 7:30)
            # NOTE: API returns UTC. You might need to adjust for your timezone manually
            # or rely on the simple shift below.
            return h + (m/60)

        # Apply simple timezone offset (e.g., -5 for EST)
        # For a robust solution, you'd use a timezone API, but hardcoding offset is easier for Pico.
        TZ_OFFSET = -4 # ADJUST THIS FOR YOUR LOCATION
        
        sunrise = (parse_iso_hour(sun_data['sunrise']) + TZ_OFFSET) % 24
        sunset = (parse_iso_hour(sun_data['sunset']) + TZ_OFFSET) % 24
        
        # Approximate twilight duration (civil start)
        twilight_am = (parse_iso_hour(sun_data['civil_twilight_begin']) + TZ_OFFSET) % 24
        twilight_pm = (parse_iso_hour(sun_data['civil_twilight_end']) + TZ_OFFSET) % 24
        
        return twilight_am, sunrise, sunset, twilight_pm

    except Exception as e:
        print("API Error:", e)
        return None

def interpolate_color(color_list, progress):
    """
    Returns an (r,g,b) tuple based on progress (0.0 to 1.0) through a list of colors.
    """
    # Ensure progress is 0-1
    progress = max(0.0, min(1.0, progress))
    
    # Map progress to an index in the list
    max_idx = len(color_list) - 1
    pos = progress * max_idx
    idx = int(pos)
    remainder = pos - idx
    
    if idx >= max_idx: return color_list[-1]
    
    c1 = color_list[idx]
    c2 = color_list[idx+1]
    
    r = c1[0] + (c2[0] - c1[0]) * remainder
    g = c1[1] + (c2[1] - c1[1]) * remainder
    b = c1[2] + (c2[2] - c1[2]) * remainder
    
    return (int(r), int(g), int(b))

def run_circadian_loop(lcd, joy_x_pin):
    # Import main settings for WiFi
    import clock_app 
    
    lcd.clear()
    lcd.putstr("Syncing Solar...")
    
    has_net = connect_wifi(clock_app.WIFI_SSID, clock_app.WIFI_PASSWORD)
    
    times = None
    if has_net:
        times = get_solar_data(lcd)
    
    if times:
        t_dawn, t_sunrise, t_sunset, t_dusk = times
        lcd.clear()
        lcd.putstr(f"Day: {int(t_sunrise)}-{int(t_sunset)}")
        utime.sleep(2)
    else:
        # Fallback
        t_dawn, t_sunrise, t_sunset, t_dusk = (FALLBACK_SUNRISE-1, FALLBACK_SUNRISE, FALLBACK_SUNSET, FALLBACK_SUNSET+1)
        lcd.clear()
        lcd.putstr("Using Default")
        utime.sleep(1)

    # TURN OFF BACKLIGHT (Stealth Mode)
    lcd.backlight_off()
    lcd.clear() # Clear text so it's fully dark

    print(f"Solar Schedule: Dawn {t_dawn:.2f}, Rise {t_sunrise:.2f}, Set {t_sunset:.2f}, Dusk {t_dusk:.2f}")

    while True:
        # 1. Get Current Time (Decimal Hour)
        now = utime.localtime()
        current_hour = now[3] + (now[4]/60) + (now[5]/3600)
        
        # 2. Determine Phase
        if current_hour >= t_sunrise and current_hour < t_sunset:
            # DAY PHASE
            duration = t_sunset - t_sunrise
            progress = (current_hour - t_sunrise) / duration
            rgb = interpolate_color(COLORS_DAY, progress)
            
        elif current_hour >= t_dawn and current_hour < t_sunrise:
            # MORNING TWILIGHT
            duration = t_sunrise - t_dawn
            progress = (current_hour - t_dawn) / duration
            rgb = interpolate_color(COLORS_TWILIGHT, progress)
            
        elif current_hour >= t_sunset and current_hour < t_dusk:
            # EVENING TWILIGHT
            # We reverse the twilight array for sunset
            duration = t_dusk - t_sunset
            progress = (current_hour - t_sunset) / duration
            # Invert progress to go from Light -> Dark
            rgb = interpolate_color(COLORS_TWILIGHT, 1.0 - progress)
            
        else:
            # NIGHT PHASE
            # Handling the midnight wrap-around is tricky.
            # We map the 24h clock onto a normalized "Night Axis"
            if current_hour >= t_dusk:
                # Pre-midnight
                night_start = t_dusk
                night_end = t_dawn + 24
                curr_adjusted = current_hour
            else:
                # Post-midnight
                night_start = t_dusk - 24
                night_end = t_dawn
                curr_adjusted = current_hour
                
            duration = night_end - night_start
            if duration == 0: duration = 1 # Safety
            progress = (curr_adjusted - night_start) / duration
            rgb = interpolate_color(COLORS_NIGHT, progress)

        # 3. Set Color
        set_rgb(*rgb)
        
        # 4. Check Exit / Wake Up
        if joy_x_pin.read_u16() < JOY_EXIT_THRESHOLD:
            set_rgb(0,0,0)
            lcd.backlight_on() # Wake up screen
            lcd.clear()
            lcd.putstr("Exiting...")
            utime.sleep(1)
            return

        # Update slowly
        utime.sleep(1)
