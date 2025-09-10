# The following script demonstrates various color models by
# cycling through their full color spectrum and converting the
# values to RGB to drive a connected RGB LED.

# --- Hardware Setup ---
# Connect the RGB LED's Red pin to a GPIO pin (e.g., GP0).
# Connect the Green pin to another GPIO pin (e.g., GP1).
# Connect the Blue pin to a third GPIO pin (e.g., GP2).
# Connect the common cathode (long pin) to a GND pin on the Pico.
# Remember to use current-limiting resistors for each LED pin (e.g., 220 Ohm).

from machine import Pin, PWM
import time
import math

# Define the pins for the Red, Green, and Blue LEDs.
# These pins must support PWM. GP0, GP1, GP2 are excellent choices.
# For a common anode LED, the duty cycle values would be inverted (e.g., 65535 - value).
RED_PIN = 16
GREEN_PIN = 17
BLUE_PIN = 18

# Set up the PWM objects for each color channel.
# PWM frequency is set to 1000 Hz, which is a good default.
pwm_r = PWM(Pin(RED_PIN))
pwm_g = PWM(Pin(GREEN_PIN))
pwm_b = PWM(Pin(BLUE_PIN))
pwm_r.freq(1000)
pwm_g.freq(1000)
pwm_b.freq(1000)

def set_rgb_color(r, g, b):
    """
    Sets the RGB LED color using 8-bit values (0-255).
    The MicroPython PWM duty cycle is 16-bit (0-65535), so we scale the values.
    """
    # Scale 8-bit (0-255) to 16-bit (0-65535) for PWM.
    # We multiply by 257 because 255 * 257 = 65535, which provides a nice scaling.
    pwm_r.duty_u16(r * 257)
    pwm_g.duty_u16(g * 257)
    pwm_b.duty_u16(b * 257)

def hsv_to_rgb(h, s, v):
    """
    Converts a color from the HSV model to the RGB model.
    h: Hue (0-360), s: Saturation (0-1), v: Value (0-1)
    """
    if s == 0.0:
        # If saturation is 0, the color is a shade of gray.
        return int(v * 255), int(v * 255), int(v * 255)
    
    i = math.floor(h * 6.0)
    f = h * 6.0 - i
    
    p = v * (1.0 - s)
    q = v * (1.0 - f * s)
    t = v * (1.0 - (1.0 - f) * s)
    
    i = int(i) % 6
    
    if i == 0:
        r, g, b = v, t, p
    elif i == 1:
        r, g, b = q, v, p
    elif i == 2:
        r, g, b = p, v, t
    elif i == 3:
        r, g, b = p, q, v
    elif i == 4:
        r, g, b = t, p, v
    elif i == 5:
        r, g, b = v, p, q
        
    return int(r * 255), int(g * 255), int(b * 255)

def hsl_to_rgb(h, s, l):
    """
    Converts a color from the HSL model to the RGB model.
    h: Hue (0-360), s: Saturation (0-1), l: Lightness (0-1)
    """
    def hue_to_rgb(p, q, t):
        if t < 0: t += 1
        if t > 1: t -= 1
        if t < 1/6: return p + (q - p) * 6 * t
        if t < 1/2: return q
        if t < 2/3: return p + (q - p) * (2/3 - t) * 6
        return p

    if s == 0:
        # If saturation is 0, the color is a shade of gray.
        return int(l * 255), int(l * 255), int(l * 255)

    q = l * (1 + s) if l < 0.5 else l + s - l * s
    p = 2 * l - q
    
    r = hue_to_rgb(p, q, h + 1/3)
    g = hue_to_rgb(p, q, h)
    b = hue_to_rgb(p, q, h - 1/3)

    return int(r * 255), int(g * 255), int(b * 255)

def rgb_model_loop():
    """
    Cycles through the primary RGB color model.
    """
    print("Cycling through the RGB color model...")
    # Cycle Red
    for i in range(256):
        set_rgb_color(i, 0, 0)
        time.sleep(0.005)
    # Cycle Green
    for i in range(256):
        set_rgb_color(0, i, 0)
        time.sleep(0.005)
    # Cycle Blue
    for i in range(256):
        set_rgb_color(0, 0, i)
        time.sleep(0.005)
    # A full spectrum loop for RGB
    for i in range(256):
        set_rgb_color(255, i, 0)
        time.sleep(0.005)
    for i in range(255, -1, -1):
        set_rgb_color(i, 255, 0)
        time.sleep(0.005)
    for i in range(256):
        set_rgb_color(0, 255, i)
        time.sleep(0.005)

def hsv_model_loop():
    """
    Cycles through the HSV color model (Hue, Saturation, Value).
    """
    print("Cycling through the HSV color model...")
    for h in range(361): # Hue (0-360)
        # We can keep Saturation and Value constant for a simple color wheel effect.
        r, g, b = hsv_to_rgb(h / 360.0, 1.0, 1.0)
        set_rgb_color(r, g, b)
        time.sleep(0.01)

def hsl_model_loop():
    """
    Cycles through the HSL color model (Hue, Saturation, Lightness).
    """
    print("Cycling through the HSL color model...")
    for h in range(361): # Hue (0-360)
        # We can keep Saturation and Lightness constant for a simple color wheel effect.
        r, g, b = hsl_to_rgb(h / 360.0, 1.0, 0.5)
        set_rgb_color(r, g, b)
        time.sleep(0.01)

def conceptual_munsell_loop():
    """
    A simplified, conceptual loop based on the Munsell color model.
    The Munsell system is perceptual, not mathematical, so a full
    implementation requires complex lookup tables. This function
    demonstrates the three dimensions of Hue, Value, and Chroma.
    """
    print("Demonstrating a conceptual Munsell-like color loop...")
    # We will loop through some primary hues, vary the "Value" (lightness),
    # and then the "Chroma" (saturation).
    
    # Red (Hue)
    print("Munsell: Red Hue")
    for v in range(0, 256, 16): # Value (lightness)
        set_rgb_color(v, 0, 0)
        time.sleep(0.02)
    
    # Yellow (Hue) - Varies red and green.
    print("Munsell: Yellow Hue")
    for v in range(0, 256, 16): # Value (lightness)
        set_rgb_color(v, v, 0)
        time.sleep(0.02)
        
    # Blue (Hue)
    print("Munsell: Blue Hue")
    for v in range(0, 256, 16): # Value (lightness)
        set_rgb_color(0, 0, v)
        time.sleep(0.02)
        
    # Varying Chroma (Saturation) for a fixed Hue (e.g., Red)
    print("Munsell: Varying Chroma (Saturation)")
    for c in range(0, 256, 16): # Chroma (saturation)
        set_rgb_color(255, 255-c, 255-c)
        time.sleep(0.02)

def custom_warm_cool_model_loop():
    """
    A simple custom color model that cycles from warm to cool colors.
    """
    print("Cycling through a custom Warm-to-Cool color model...")
    # Warm Colors (Red, Orange, Yellow)
    for i in range(256):
        set_rgb_color(255, i, 0) # Red to Yellow
        time.sleep(0.01)
    
    # Cool Colors (Green, Cyan, Blue)
    for i in range(256):
        set_rgb_color(0, 255-i, i) # Yellowish-Green to Blue
        time.sleep(0.01)
        
    for i in range(255, -1, -1):
        set_rgb_color(0, i, 255) # Blue to Cyan
        time.sleep(0.01)
        
def main():
    """
    The main function that orchestrates the color model demonstrations.
    """
    while True:
        rgb_model_loop()
        time.sleep(1) # Pause before the next demonstration
        
        hsv_model_loop()
        time.sleep(1)
        
        hsl_model_loop()
        time.sleep(1)
        
        conceptual_munsell_loop()
        time.sleep(1)
        
        custom_warm_cool_model_loop()
        time.sleep(1)
        
if __name__ == "__main__":
    main()
