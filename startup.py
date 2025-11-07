# startup.py
#
# Handles the boot-up sequence for the Pico:
# 1. Imports configuration
# 2. Sets startup LED color
# 3. Connects to Wi-Fi
# 4. Reports connection status back to main.

import network
import utime
from machine import Pin # Assuming you need this for LEDs
# Import your RGB LED driver library here (e.g., neopixel)

# --- Placeholder for RGB LED ---
# TODO: Replace this with your actual RGB LED control function.
# This might involve initializing PWM pins or a NeoPixel strip.
def set_led_color(r, g, b):
    """Placeholder function to set the RGB LED color."""
    # Example (if you were using 3 PWM pins):
    # pwm_r.duty_u16(r * 257) # Scale 0-255 to 0-65535
    # pwm_g.duty_u16(g * 257)
    # pwm_b.duty_u16(b * 257)
    print(f"LED STUB: Set color to ({r}, {g}, {b})")

# --- End Placeholder ---


def connect_to_wifi(lcd, ssid, password, led_success, led_fail):
    """Attempts to connect to Wi-Fi using credentials from config."""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    if wlan.isconnected():
        return wlan
    
    lcd.clear()
    lcd.putstr("Connecting WiFi")
    wlan.connect(ssid, password)
    
    max_wait = 15
    while max_wait > 0:
        if wlan.status() >= 3 or wlan.status() < 0: # 3 = connected, <0 = fail
            break
        max_wait -= 1
        lcd.putstr(".")
        utime.sleep(1)
    
    if wlan.isconnected():
        lcd.clear()
        lcd.putstr("WiFi Connected!")
        set_led_color(*led_success) # Green for success
        utime.sleep(1.5)
        return wlan
    else:
        lcd.clear()
        lcd.putstr("WiFi Failed!")
        set_led_color(*led_fail) # Red for failure
        utime.sleep(2)
        wlan.active(False) # Turn off WiFi interface
        return None

def initialize(lcd):
    """
    Runs the main startup sequence.
    Returns the wlan object if connection is successful, else None.
    """
    wlan = None
    
    try:
        import config
        
        # 1. Set startup LED
        set_led_color(*config.LED_STARTUP_COLOR)
        lcd.clear()
        lcd.putstr("System Starting...")
        utime.sleep(1)

        # 2. Connect to Wi-Fi
        if config.WIFI_SSID and config.WIFI_PASSWORD:
            wlan = connect_to_wifi(
                lcd,
                config.WIFI_SSID,
                config.WIFI_PASSWORD,
                config.LED_WIFI_SUCCESS_COLOR,
                config.LED_WIFI_FAIL_COLOR
            )
        else:
            lcd.clear()
            lcd.putstr("No WiFi Config")
            utime.sleep(2)
    
    except ImportError:
        lcd.clear()
        lcd.putstr("ERROR:")
        lcd.move_to(0, 1)
        lcd.putstr("config.py missing")
        utime.sleep(3)
    
    except Exception as e:
        lcd.clear()
        lcd.putstr("Startup Error")
        lcd.move_to(0, 1)
        lcd.putstr(str(e)[:16]) # Show first 16 chars of error
        utime.sleep(3)
        
    # 3. Set idle menu LED color
    # We do this regardless of WiFi success
    try:
        set_led_color(*config.LED_MENU_IDLE_COLOR)
    except Exception:
        pass # Ignore if config/LED fails
    
    # 4. Return the connection object (or None)
    return wlan
