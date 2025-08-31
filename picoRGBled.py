import time
from machine import Pin
from pico_rgbled import RGBLED

# Pin definitions for the RGB LED
# The RGB LED is connected to GPIO pins 24 (R), 22 (G), and 21 (B)
rgb_led = RGBLED(24, 22, 21)

# Function to fade between two colors
def fade_color(start_color, end_color, steps=100, delay=0.01):
    for i in range(steps):
        r = int(start_color[0] + (end_color[0] - start_color[0]) * i / steps)
        g = int(start_color[1] + (end_color[1] - start_color[1]) * i / steps)
        b = int(start_color[2] + (end_color[2] - start_color[2]) * i / steps)
        rgb_led.set_rgb(r, g, b)
        time.sleep(delay)

# Main loop to run the color fade sequence
while True:
    # Red to Green fade
    fade_color((255, 0, 0), (0, 255, 0))
    
    # Green to Blue fade
    fade_color((0, 255, 0), (0, 0, 255))
    
    # Blue to Red fade
    fade_color((0, 0, 255), (255, 0, 0))
    
    # Pause for a moment at the end of the cycle
    time.sleep(0.5)
