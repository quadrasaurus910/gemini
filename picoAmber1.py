import utime
from machine import Pin, PWM
import math

# --- SETUP ---
# Adjust these pin numbers to match your RGB LED's connections.
PIN_R = 16
PIN_G = 17
PIN_B = 18

led_r = PWM(Pin(PIN_R))
led_g = PWM(Pin(PIN_G))
led_b = PWM(Pin(PIN_B))

PWM_FREQ = 1000
led_r.freq(PWM_FREQ)
led_g.freq(PWM_FREQ)
led_b.freq(PWM_FREQ)

# Helper function to set the LED color
def set_rgb(r, g, b):
    r = max(0, min(255, int(r)))
    g = max(0, min(255, int(g)))
    b = max(0, min(255, int(b)))
    
    led_r.duty_u16(int(r / 255 * 65535))
    led_g.duty_u16(int(g / 255 * 65535))
    led_b.duty_u16(int(b / 255 * 65535))

# --- COLOR SPACE CONVERSIONS ---
def srgb_to_linear(c):
    c_norm = c / 255.0
    if c_norm > 0.04045:
        return ((c_norm + 0.055) / 1.055)**2.4
    else:
        return c_norm / 12.92

def rgb_to_xy(r, g, b):
    r_linear = srgb_to_linear(r)
    g_linear = srgb_to_linear(g)
    b_linear = srgb_to_linear(b)

    x = 0.4124564 * r_linear + 0.3575761 * g_linear + 0.1804375 * b_linear
    y = 0.2126729 * r_linear + 0.7151522 * g_linear + 0.0721750 * b_linear
    z = 0.0193339 * r_linear + 0.1191920 * g_linear + 0.9503041 * b_linear

    sum_xyz = x + y + z
    if sum_xyz == 0:
        return 0, 0
    
    return x / sum_xyz, y / sum_xyz

def is_in_amber_zone(r, g, b):
    x, y = rgb_to_xy(r, g, b)
    
    # Tolerance to account for floating-point inaccuracies
    TOLERANCE = 0.005 

    is_reddish_enough = y <= 0.390 + TOLERANCE
    is_greenish_enough = y >= (x - 0.120) - TOLERANCE
    is_not_too_white = y <= (0.790 - 0.670 * x) + TOLERANCE
    is_x_in_range = x > 0.5 - TOLERANCE and x < 0.65 + TOLERANCE

    return is_reddish_enough and is_greenish_enough and is_not_too_white and is_x_in_range

# --- HSV to RGB Conversion (remains unchanged) ---
def hsv_to_rgb(h, s, v):
    if s == 0.0: return v, v, v
    
    i = math.floor(h*6.0)
    f = h*6.0 - i
    p = v*(1.0 - s)
    q = v*(1.0 - s*f)
    t = v*(1.0 - s*(1.0 - f))

    i %= 6
    if i == 0: r, g, b = v, t, p
    if i == 1: r, g, b = q, v, p
    if i == 2: r, g, b = p, v, t
    if i == 3: r, g, b = p, q, v
    if i == 4: r, g, b = t, p, v
    if i == 5: r, g, b = v, p, q

    return int(r*255), int(g*255), int(b*255)

# --- NEW TEST FUNCTION ---
def test_amber_detection():
    print("--- Running Amber Detection Test ---")
    test_color = (255, 191, 0) # A known amber RGB color
    if is_in_amber_zone(*test_color):
        print("SUCCESS: The known amber color was correctly detected. The main loop should now work.")
    else:
        print("FAILURE: The known amber color was NOT detected. Please re-check the conversion formulas or increase the tolerance.")
    print("------------------------------------")
    utime.sleep(2)

# --- MAIN LOOP ---
def explore_amber_zone_hsv():
    print("Beginning HSV loop through the legal amber zone...")

    for hue_deg in range(40, 61, 1):
        h = hue_deg / 360.0
        s = 1.0
        v = 1.0
        
        r, g, b = hsv_to_rgb(h, s, v)
        
        if is_in_amber_zone(r, g, b):
            set_rgb(r, g, b)
            utime.sleep_ms(50)
            
    print("HSV loop finished.")
    set_rgb(0, 0, 0)

while True:
    test_amber_detection()
    explore_amber_zone_hsv()
    utime.sleep(2)
