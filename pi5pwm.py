from gpiozero import RGBLED
from time import sleep

# active_high=False is crucial for Common Anode
led = RGBLED(red=17, green=27, blue=22, active_high=False)

def lerp(start, end, fraction):
    """Linear interpolation between two values."""
    return start + (end - start) * fraction

def fade_to_color(start_rgb, end_rgb, duration=2.0, steps=100):
    """
    start_rgb & end_rgb: Tuples of (r, g, b) from 0.0 to 1.0
    """
    for i in range(steps + 1):
        fraction = i / steps
        
        # Calculate new R, G, B
        new_r = lerp(start_rgb[0], end_rgb[0], fraction)
        new_g = lerp(start_rgb[1], end_rgb[1], fraction)
        new_b = lerp(start_rgb[2], end_rgb[2], fraction)
        
        # Apply Gamma Correction (optional but recommended for smoothness)
        gamma = 2.8
        led.value = (new_r**gamma, new_g**gamma, new_b**gamma)
        
        sleep(duration / steps)

# Example: Fade from Red to Cyan
try:
    while True:
        fade_to_color((1, 0, 0), (0, 1, 1), duration=3)
        fade_to_color((0, 1, 1), (1, 0, 0), duration=3)
except KeyboardInterrupt:
    led.close()
