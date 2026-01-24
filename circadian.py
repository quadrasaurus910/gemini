# circadian_v2.py
# Uses "Rubber Band" time to map a 24-step color chart to variable day lengths.
# Features dedicated high-res Sunrise/Sunset sequences.

import network
import urequests
import ujson
import utime
import math
from machine import Pin, PWM

# --- User Configuration ---
# Your default "Ideal" times (used if WiFi fails)
FALLBACK_SUNRISE = 6.0
FALLBACK_SUNSET = 18.0
TWILIGHT_DURATION = 0.75  # 45 minutes of dedicated sunrise/sunset transition

# --- The 24-Hour Master Palette (The "Ideal" Day) ---
# Index 0 = Midnight, Index 12 = High Noon.
# Adjusted for more saturation during day, better brightness at night.
HOURLY_COLORS = [
    (5, 0, 20),      # 00:00 Midnight (Deep Blue/Purple)
    (5, 0, 25),      # 01:00
    (8, 0, 30),      # 02:00
    (10, 0, 40),     # 03:00
    (15, 5, 60),     # 04:00 (Faint pre-dawn)
    (30, 10, 80),    # 05:00 (Blue hour)
    (255, 100, 50),  # 06:00 (Sunrise Placeholder - Overridden by Sequence)
    (255, 160, 80),  # 07:00 (Morning Gold)
    (255, 200, 100), # 08:00
    (200, 220, 255), # 09:00 (Brightening Sky)
    (180, 240, 255), # 10:00 (Clear Blue Sky)
    (200, 255, 255), # 11:00 (Noon White)
    (220, 255, 255), # 12:00 (High Noon)
    (200, 255, 255), # 13:00
    (180, 240, 255), # 14:00
    (200, 220, 255), # 15:00
    (255, 200, 120), # 16:00 (Afternoon Gold)
    (255, 150, 50),  # 17:00 (Late Sun)
    (200, 50, 20),   # 18:00 (Sunset Placeholder - Overridden by Sequence)
    (100, 0, 100),   # 19:00 (Post-Sunset Purple - Brighter than before)
    (60, 0, 140),    # 20:00 (Deep Twilight)
    (40, 0, 100),    # 21:00
    (20, 0, 80),     # 22:00
    (10, 0, 40),     # 23:00
]

# --- Special Event Sequences ---
# These play exactly at sunrise/sunset, overriding the hourly list.
SEQ_SUNRISE = [
    (10, 0, 60),    # Dark Blue
    (40, 0, 80),    # Violet
    (120, 20, 60),  # Deep Pink
    (255, 80, 20),  # Red-Orange
    (255, 180, 50), # Gold
    (255, 220, 150) # Bright Morning
]

SEQ_SUNSET = [
    (255, 200, 100), # Late Afternoon
    (255, 140, 20),  # Golden Hour
    (200, 50, 10),   # Deep Orange
    (150, 20, 80),   # Purple/Pink
    (60, 0, 120),    # Twilight Blue
    (20, 0, 80)      # Night Fall
]

# --- Hardware Init ---
pwm_r = PWM(Pin(16))
pwm_g = PWM(Pin(17))
pwm_b = PWM(Pin(18))
for pwm in [pwm_r, pwm_g, pwm_b]:
    pwm.freq(1000)

def set_rgb(r, g, b):
    # Common Anode Inversion
    pwm_r.duty_u16(65535 - (int(r) * 257))
    pwm_g.duty_u16(65535 - (int(g) * 257))
    pwm_b.duty_u16(65535 - (int(b) * 257))

def interpolate_color(color1, color2, factor):
    r = color1[0] + (color2[0] - color1[0]) * factor
    g = color1[1] + (color2[1] - color1[1]) * factor
    b = color1[2] + (color2[2] - color1[2]) * factor
    return (r, g, b)

def get_color_from_sequence(seq, progress):
    # Maps 0.0-1.0 to a list of colors
    idx_float = progress * (len(seq) - 1)
    idx_int = int(idx_float)
    factor = idx_float - idx_int
    if idx_int >= len(seq) - 1: return seq[-1]
    return interpolate_color(seq[idx_int], seq[idx_int+1], factor)

def get_solar_times(lcd):
    """Fetches solar data or returns fallback."""
    try:
        # IP Geolocation
        r = urequests.get("http://ip-api.com/json/")
        loc = r.json()
        r.close()
        lat, lon = loc['lat'], loc['lon']
        
        # Solar Data
        lcd.move_to(0, 1)
        lcd.putstr("Fetching Sun...")
        url = f"https://api.sunrise-sunset.org/json?lat={lat}&lng={lon}&formatted=0"
        r = urequests.get(url)
        data = r.json()['results']
        r.close()
        
        # Parse ISO Time
        def parse_h(iso):
            t = iso.split('T')[1].split('+')[0]
            h, m, s = map(int, t.split(':'))
            return h + (m/60)

        # ADJUST YOUR TIMEZONE HERE
        TZ = -4 
        
        rise = (parse_h(data['sunrise']) + TZ) % 24
        set_ = (parse_h(data['sunset']) + TZ) % 24
        
        return rise, set_
    except:
        return FALLBACK_SUNRISE, FALLBACK_SUNSET

def get_virtual_hour(current_h, rise, set_):
    """
    The Elastic Time Engine.
    Maps real world time to the 'Ideal Day' (0-23) based on phase.
    """
    
    # 1. Sunrise Sequence Window
    # If we are within the transition window of sunrise
    if abs(current_h - rise) <= (TWILIGHT_DURATION / 2):
        # Return a special flag or handle logic outside
        return "SUNRISE"
        
    # 2. Sunset Sequence Window
    if abs(current_h - set_) <= (TWILIGHT_DURATION / 2):
        return "SUNSET"
        
    # 3. Day Phase (Between Rise and Set)
    if current_h > rise and current_h < set_:
        # We need to map [Rise -> Set] to [Ideal 6 -> Ideal 18]
        day_progress = (current_h - rise) / (set_ - rise)
        # Map 0.0-1.0 to 6.0-18.0
        return 6.0 + (day_progress * 12.0)
        
    # 4. Night Phase
    else:
        # We need to map [Set -> Rise] to [Ideal 18 -> Ideal 6] (wrapping 24)
        
        # Calculate time since sunset
        if current_h >= set_:
            time_passed = current_h - set_
        else:
            time_passed = (24 - set_) + current_h
            
        night_length = (24 - set_) + rise
        night_progress = time_passed / night_length
        
        # Map 0.0-1.0 to 18.0 - 30.0 (where 30 is 6am next day)
        virtual = 18.0 + (night_progress * 12.0)
        return virtual % 24

def run_circadian_loop(lcd, joy_x_pin):
    import clock_app # For WiFi credentials
    
    lcd.clear()
    lcd.putstr("Syncing Solar v2")
    
    # Connect WiFi
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        wlan.connect(clock_app.WIFI_SSID, clock_app.WIFI_PASSWORD)
        utime.sleep(5)
        
    rise, set_ = get_solar_times(lcd)
    
    lcd.clear()
    lcd.putstr(f"Rise:{rise:.1f} Set:{set_:.1f}")
    utime.sleep(2)
    lcd.backlight_off()
    lcd.clear()
    
    while True:
        # Get Time
        t = utime.localtime()
        current_h = t[3] + (t[4]/60) + (t[5]/3600)
        
        mode = get_virtual_hour(current_h, rise, set_)
        
        rgb = (0,0,0)
        
        if mode == "SUNRISE":
            # Determine progress through sunrise window
            # Window starts at rise - (duration/2)
            start_w = rise - (TWILIGHT_DURATION/2)
            prog = (current_h - start_w) / TWILIGHT_DURATION
            rgb = get_color_from_sequence(SEQ_SUNRISE, prog)
            
        elif mode == "SUNSET":
            start_w = set_ - (TWILIGHT_DURATION/2)
            prog = (current_h - start_w) / TWILIGHT_DURATION
            rgb = get_color_from_sequence(SEQ_SUNSET, prog)
            
        else:
            # Standard Hourly Interpolation
            idx = int(mode)
            next_idx = (idx + 1) % 24
            factor = mode - idx
            
            c1 = HOURLY_COLORS[idx]
            c2 = HOURLY_COLORS[next_idx]
            rgb = interpolate_color(c1, c2, factor)
            
        set_rgb(*rgb)
        
        # Exit Check
        if joy_x_pin.read_u16() < 20000:
            set_rgb(0,0,0)
            lcd.backlight_on()
            lcd.clear()
            lcd.putstr("Exiting...")
            utime.sleep(1)
            return
            
        utime.sleep(1)
