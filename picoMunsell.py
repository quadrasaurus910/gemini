# This script demonstrates the use of a lookup table for a perceptual color model.
# A simplified Munsell color table is pre-computed and stored here to be
# iterated through, showing how Hue, Value, and Chroma affect the final RGB color.

from machine import Pin, PWM
import time

# --- Hardware Setup ---
# Connect the RGB LED's Red pin to a GPIO pin (e.g., GP0).
# Connect the Green pin to another GPIO pin (e.g., GP1).
# Connect the Blue pin to a third GPIO pin (e.g., GP2).
# Use current-limiting resistors (e.g., 220 Ohm) on each pin.

RED_PIN = 0
GREEN_PIN = 1
BLUE_PIN = 2

pwm_r = PWM(Pin(RED_PIN))
pwm_g = PWM(Pin(GREEN_PIN))
pwm_b = PWM(Pin(BLUE_PIN))
pwm_r.freq(1000)
pwm_g.freq(1000)
pwm_b.freq(1000)

def set_rgb_color(r, g, b):
    """
    Sets the RGB LED color using 8-bit values (0-255).
    """
    pwm_r.duty_u16(r * 257)
    pwm_g.duty_u16(g * 257)
    pwm_b.duty_u16(b * 257)

# --- Munsell Lookup Table ---
# This is a simplified lookup table. The full Munsell system is vast and
# requires specific conditions and a massive dataset. This table is for
# educational purposes and demonstrates how the three dimensions of the
# Munsell color space (Hue, Value, and Chroma) relate to RGB.
# Each entry is a tuple: (Munsell Hue, Munsell Value, Munsell Chroma, R, G, B)

# The following data is a small sample for demonstration.
# The `Munsell` values are simplified representations.
MUNSELL_LOOKUP_TABLE = [
    # Hue: 5R (Red)
    ("5R", 2, 2, 85, 0, 0),       # Dark, low chroma red
    ("5R", 4, 4, 153, 0, 0),      # Medium, medium chroma red
    ("5R", 6, 8, 255, 0, 0),      # Bright, high chroma red
    ("5R", 8, 10, 255, 102, 102), # Very light, high chroma red
    
    # Hue: 5Y (Yellow)
    ("5Y", 6, 6, 255, 255, 0),    # Bright, high chroma yellow
    ("5Y", 8, 8, 255, 255, 102),  # Lighter, high chroma yellow
    ("5Y", 4, 4, 255, 128, 0),    # Darker, medium chroma yellow (orange-ish)
    
    # Hue: 5BG (Blue-Green)
    ("5BG", 4, 4, 0, 102, 102),   # Medium, medium chroma blue-green
    ("5BG", 6, 6, 0, 153, 153),   # Lighter, medium chroma blue-green
    ("5BG", 8, 2, 102, 204, 204), # Very light, low chroma blue-green
    
    # Hue: 5PB (Purple-Blue)
    ("5PB", 4, 4, 51, 0, 153),    # Medium, medium chroma purple-blue
    ("5PB", 6, 6, 102, 0, 204),   # Lighter, medium chroma purple-blue
    ("5PB", 8, 2, 178, 102, 255), # Very light, low chroma purple-blue
    
    # Neutral Scale (N) - Varying Value
    ("N", 0, 0, 0, 0, 0),         # Black
    ("N", 2, 0, 51, 51, 51),      # Dark gray
    ("N", 4, 0, 102, 102, 102),   # Medium gray
    ("N", 6, 0, 153, 153, 153),   # Light gray
    ("N", 8, 0, 204, 204, 204),   # Very light gray
    ("N", 10, 0, 255, 255, 255),  # White
]


def display_munsell_colors():
    """
    Iterates through the Munsell lookup table and displays each color.
    """
    print("Cycling through the Munsell lookup table...")
    for color in MUNSELL_LOOKUP_TABLE:
        hue, value, chroma, r, g, b = color
        print(f"Displaying Munsell: Hue={hue}, Value={value}, Chroma={chroma} (RGB: {r},{g},{b})")
        set_rgb_color(r, g, b)
        time.sleep(1) # Pause to see each color clearly

def main():
    """
    The main function that orchestrates the color model demonstrations.
    """
    while True:
        display_munsell_colors()
        time.sleep(2) # Pause before repeating the loop

if __name__ == "__main__":
    main()
