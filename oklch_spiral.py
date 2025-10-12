# MicroPython script for Raspberry Pi Pico W
# Drives a common anode RGB LED using the OKLCH color space
# Creates a "chroma spiral" effect, cycling hue while pulsing chroma.

import machine
import time
import math

# --- Pin Configuration ---
# Connect the R, G, B pins of the common anode LED to these GPIOs.
# The common pin goes to 3.3V.
R_PIN = 16
G_PIN = 17
B_PIN = 18

# --- PWM & Animation Parameters ---
PWM_FREQ = 1000  # PWM frequency in Hz, 1000 is good to avoid flicker

# --- OKLCH Animation Settings (Tweak these!) ---
LIGHTNESS = 0.7       # Constant Lightness (L): 0.0 (black) to 1.0 (white). 0.7 is bright.
CHROMA_MIN = 0.02     # Minimum Chroma (C): How desaturated the color gets.
CHROMA_MAX = 0.15     # Maximum Chroma (C): How vibrant the color gets. Max is ~0.37.
HUE_SPEED = 0.5       # Speed of hue rotation (degrees per step).
CHROMA_OSC_SPEED = 2  # How many chroma pulses per full hue cycle. Higher is faster.
STEP_DELAY_MS = 10    # Milliseconds between each step. Lower is faster animation.

# --- Hardware Setup ---
# Initialize PWM for each pin
r_pwm = machine.PWM(machine.Pin(R_PIN))
g_pwm = machine.PWM(machine.Pin(G_PIN))
b_pwm = machine.PWM(machine.Pin(B_PIN))

r_pwm.freq(PWM_FREQ)
g_pwm.freq(PWM_FREQ)
b_pwm.freq(PWM_FREQ)

def set_rgb(r, g, b):
    """
    Sets the color of a common anode RGB LED.
    0-255 values are inverted for the PWM duty cycle.
    0 = full brightness, 255 = off.
    """
    # Scale 0-255 to 0-65535 and invert for common anode
    # 65535 is the max duty cycle value for 16-bit PWM
    r_duty = 65535 - int(r * 257)
    g_duty = 65535 - int(g * 257)
    b_duty = 65535 - int(b * 257)
    
    # Clamp values to ensure they are within the valid range
    r_pwm.duty_u16(max(0, min(65535, r_duty)))
    g_pwm.duty_u16(max(0, min(65535, g_duty)))
    b_pwm.duty_u16(max(0, min(65535, b_duty)))

# --- Color Space Conversion Functions ---

def oklch_to_oklab(l, c, h):
    """Converts OKLCH (cylindrical) to OKLAB (cartesian)."""
    h_rad = math.radians(h)
    a = c * math.cos(h_rad)
    b = c * math.sin(h_rad)
    return l, a, b

def oklab_to_linear_srgb(l, a, b):
    """Converts OKLAB to linear sRGB using standard matrices."""
    # OKLAB to LMS (cone space)
    l_ = l + 0.3963377774 * a + 0.2158037573 * b
    m_ = l - 0.1055613458 * a - 0.0638541728 * b
    s_ = l - 0.0894841775 * a - 1.2914855480 * b

    l_ = l_**3
    m_ = m_**3
    s_ = s_**3

    # LMS to linear sRGB
    r_linear = +4.0767416621 * l_ - 3.3077115913 * m_ + 0.2309699292 * s_
    g_linear = -1.2684380046 * l_ + 2.6097574011 * m_ - 0.3413193965 * s_
    b_linear = -0.0041960863 * l_ - 0.7034186147 * m_ + 1.7076147010 * s_
    
    return r_linear, g_linear, b_linear

def linear_to_srgb_gamma(c):
    """Applies gamma correction to a single linear channel."""
    if c > 0.0031308:
        return 1.055 * (c**(1.0/2.4)) - 0.055
    else:
        return 12.92 * c

def oklch_to_rgb(l, c, h):
    """Full conversion from OKLCH to a 24-bit RGB tuple (r, g, b)."""
    # Step 1: Convert OKLCH to OKLAB
    l_oklab, a_oklab, b_oklab = oklch_to_oklab(l, c, h)
    
    # Step 2: Convert OKLAB to linear sRGB
    r_lin, g_lin, b_lin = oklab_to_linear_srgb(l_oklab, a_oklab, b_oklab)
    
    # Step 3: Apply gamma correction and scale to 0-255
    r = int(max(0, min(255, linear_to_srgb_gamma(r_lin) * 255)))
    g = int(max(0, min(255, linear_to_srgb_gamma(g_lin) * 255)))
    b = int(max(0, min(255, linear_to_srgb_gamma(b_lin) * 255)))
    
    return r, g, b

# --- Main Animation Loop ---

def main_loop():
    """Runs the main animation logic."""
    print("Starting OKLCH Chroma Spiral...")
    hue = 0.0
    
    # Calculate chroma constants for the oscillation
    chroma_amplitude = (CHROMA_MAX - CHROMA_MIN) / 2
    chroma_midpoint = CHROMA_MIN + chroma_amplitude
    
    while True:
        # Oscillate Chroma using a sine wave based on the hue angle.
        # This makes the saturation pulse in and out as the color changes.
        oscillation_angle = math.radians(hue * CHROMA_OSC_SPEED)
        chroma = chroma_midpoint + chroma_amplitude * math.sin(oscillation_angle)
        
        # Convert the current OKLCH color to RGB
        r, g, b = oklch_to_rgb(LIGHTNESS, chroma, hue)
        
        # Set the LED color
        set_rgb(r, g, b)
        
        # Increment hue for the next step, wrapping around at 360 degrees
        hue += HUE_SPEED
        if hue >= 360.0:
            hue -= 360.0
        
        time.sleep_ms(STEP_DELAY_MS)

# --- Run the script ---
if __name__ == "__main__":
    try:
        main_loop()
    except KeyboardInterrupt:
        print("Script stopped.")
        # Turn off the LED
        set_rgb(0, 0, 0)
