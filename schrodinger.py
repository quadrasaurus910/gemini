# schrodinger.py
# Based on "Theorie der Pigmente von größter Leuchtkraft" (1920)
# Simulates "Optimal Colors" by sliding a binary spectral window 
# across the visible spectrum.

import utime
import math
from machine import Pin, PWM

# --- Configuration ---
COMMON_ANODE = True 
JOY_EXIT_THRESHOLD = 20000 
LED_PINS = [16, 17, 18] # R, G, B

# --- Hardware Init ---
pwm_r = PWM(Pin(LED_PINS[0]))
pwm_g = PWM(Pin(LED_PINS[1]))
pwm_b = PWM(Pin(LED_PINS[2]))
for pwm in [pwm_r, pwm_g, pwm_b]:
    pwm.freq(1000)

def set_rgb(r, g, b):
    # Gamma correction (Human eye is non-linear)
    # Schrödinger's work dealt heavily with perception.
    # We square the values to approximate gamma 2.0
    r = int((r/255)**2 * 255)
    g = int((g/255)**2 * 255)
    b = int((b/255)**2 * 255)

    if COMMON_ANODE:
        pwm_r.duty_u16(65535 - (r * 257))
        pwm_g.duty_u16(65535 - (g * 257))
        pwm_b.duty_u16(65535 - (b * 257))
    else:
        pwm_r.duty_u16(r * 257)
        pwm_g.duty_u16(g * 257)
        pwm_b.duty_u16(b * 257)

def get_spectral_overlap(led_peak_nm, window_center, window_width):
    """
    Calculates how much of the LED's specific color falls inside
    Schrödinger's theoretical 'Optimal Window'.
    """
    # LED emitters aren't single lines, they are bell curves (Gaussian).
    # We check if the LED's peak is inside the window.
    
    # 1. Define the Window (Start and End)
    w_start = window_center - (window_width / 2)
    w_end = window_center + (window_width / 2)
    
    # 2. Handle Wrapping (The Line of Purples)
    # If the window goes past 700nm, it wraps to 400nm
    # (Schrödinger defined this topology).
    
    is_inside = False
    
    # Normalize range to 0-100 (representing 400nm-700nm)
    # Blue ~ 460nm (20), Green ~ 520nm (40), Red ~ 620nm (73)
    # We use relative positions for the Pico's generic LED
    
    if w_start < w_end:
        # Normal window (e.g., Green)
        if w_start <= led_peak_nm <= w_end:
            is_inside = True
    else:
        # Split window (Purple: Red + Blue)
        # e.g. Start 80, End 20. 
        if led_peak_nm >= w_start or led_peak_nm <= w_end:
            is_inside = True
            
    # Soften the edges (Anti-aliasing the binary step)
    # If we strictly did 0 or 1, it would flicker. 
    # We calculate a 'distance' factor for smoothness.
    distance = 0
    if is_inside:
        return 255
    else:
        # Basic falloff for smoothness
        return 0

def run_schrodinger_loop(joy_x_pin):
    """
    Cycles through the 'Optimal Color Solid'.
    Varies the Center (Hue) and the Width (Luminosity).
    """
    print("Starting Schrodinger's Optimal Colors...")
    
    # Approximate peak wavelengths of a standard RGB LED 
    # Mapped to a 0-100 scale (400nm to 700nm)
    PEAK_B = 20  # ~460nm
    PEAK_G = 45  # ~535nm
    PEAK_R = 75  # ~625nm (Red is tricky, eye sensitivity varies)

    center = 0.0
    width = 10.0
    
    # Animation Physics
    center_speed = 0.3
    width_speed = 0.1
    width_direction = 1
    
    while True:
        # 1. Update Physics
        # Move the center of the spectrum window
        center += center_speed
        if center > 100: center = 0
        
        # Breathe the width (Luminosity Pulse)
        # Narrow width = Saturated Colors
        # Wide width = Bright Pastels (High Luminosity)
        width += (width_speed * width_direction)
        
        # Schrödinger Limit: Width oscillates between 5% and 50% of spectrum
        if width > 60 or width < 5:
            width_direction *= -1
            
        # 2. Calculate Overlap (The Integral)
        r = get_spectral_overlap(PEAK_R, center, width)
        g = get_spectral_overlap(PEAK_G, center, width)
        b = get_spectral_overlap(PEAK_B, center, width)
        
        # 3. Output
        set_rgb(r, g, b)
        
        # 4. Check Exit
        if joy_x_pin.read_u16() < JOY_EXIT_THRESHOLD:
            set_rgb(0,0,0)
            return

        utime.sleep_ms(10)
