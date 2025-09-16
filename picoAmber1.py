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
# These functions are necessary to check the color's position on the CIE chart.
def srgb_to_linear(c):
    c_norm = c / 255.0
    return ((c_norm + 0.055) / 1.055)**2.4 if c_norm > 0.04045 else c_norm / 12.92

def rgb_to_xy(r, g, b):
    # Convert sRGB to linear RGB
    r_linear = srgb_to_linear(r)
    g_linear = srgb_to_linear(g)
    b_linear = srgb_to_linear(b)

    # Convert to XYZ (D65 white point assumed)
    x = 0.4124564 * r_linear + 0.3575761 * g_linear + 0.1804375 * b_linear
    y = 0.2126729 * r_linear + 0.7151522 * g_linear + 0.0721750 * b_linear
    z = 0.0193339 * r_linear + 0.1191920 * g_linear + 0.9503041 * b_linear

    # Avoid division by zero
    sum_xyz = x + y + z
    if sum_xyz == 0:
        return 0, 0
    
    return x / sum_xyz, y / sum_xyz

def is_in_amber_zone(r, g, b):
    """
    Checks if a given 8-bit RGB color falls within the legal amber zone.
    """
    x, y = rgb_to_xy(r, g, b)

    # Check against the four boundary conditions
    # This is a key part of the logic
    is_reddish_enough = y <= 0.390
    is_greenish_enough = y >= x - 0.120
    is_not_too_white = y <= 0.790 - 0.670 * x

    # Final check: is x also within a reasonable range for amber?
    # This helps filter out colors that might pass the above but are far off.
    is_x_in_range = x > 0.5 and x < 0.65

    return is_reddish_enough and is_greenish_enough and is_not_too_white and is_x_in_range

# --- MAIN LOOP ---
def display_amber_colors():
    """
    Loops through a range of colors and displays only those that are legal amber.
    """
    print("Beginning loop through the legal amber zone...")
    
    # We can optimize the loop by focusing on a specific part of the RGB cube
    # where amber-like colors are likely to be found.
    # Amber has high Red and Green, and low Blue.
    for r in range(150, 256, 5):
        for g in range(150, 256, 5):
            for b in range(0, 100, 5):
                if is_in_amber_zone(r, g, b):
                    set_rgb(r, g, b)
                    utime.sleep_ms(10)
    
    print("Loop finished.")
    set_rgb(0, 0, 0) # Turn LED off

while True:
    display_amber_colors()
    utime.sleep(2)
