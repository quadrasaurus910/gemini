# This script uses a joystick to control an RGB LED in the HSL color space.
# The joystick's X-axis controls the hue, and the Y-axis controls the saturation.

from machine import Pin, PWM, ADC
import time
import math

# --- Hardware Setup ---
# For the RGB LED:
# Connect the RGB LED's Red pin to a GPIO pin (e.g., GP0).
# Connect the Green pin to another GPIO pin (e.g., GP1).
# Connect the Blue pin to a third GPIO pin (e.g., GP2).
# Use current-limiting resistors (e.g., 220 Ohm) on each pin.

# For the Joystick:
# Connect the Joystick's VRX pin to a Pico ADC pin (e.g., GP26).
# Connect the Joystick's VRY pin to another Pico ADC pin (e.g., GP27).
# Connect GND and VCC on the joystick to a GND and 3.3V pin on the Pico.

RED_PIN = 0
GREEN_PIN = 1
BLUE_PIN = 2
JOYSTICK_X_PIN = 26
JOYSTICK_Y_PIN = 27

# Set up the PWM objects for each color channel.
pwm_r = PWM(Pin(RED_PIN))
pwm_g = PWM(Pin(GREEN_PIN))
pwm_b = PWM(Pin(BLUE_PIN))
pwm_r.freq(1000)
pwm_g.freq(1000)
pwm_b.freq(1000)

# Set up the ADC objects for the joystick axes.
adc_x = ADC(Pin(JOYSTICK_X_PIN))
adc_y = ADC(Pin(JOYSTICK_Y_PIN))

def set_rgb_color(r, g, b):
    """
    Sets the RGB LED color using 8-bit values (0-255).
    """
    pwm_r.duty_u16(r * 257)
    pwm_g.duty_u16(g * 257)
    pwm_b.duty_u16(b * 257)

def hsl_to_rgb(h, s, l):
    """
    Converts a color from the HSL model to the RGB model.
    h: Hue (0-1), s: Saturation (0-1), l: Lightness (0-1)
    """
    def hue_to_rgb(p, q, t):
        if t < 0: t += 1
        if t > 1: t -= 1
        if t < 1/6: return p + (q - p) * 6 * t
        if t < 1/2: return q
        if t < 2/3: return p + (q - p) * (2/3 - t) * 6
        return p

    if s == 0:
        return int(l * 255), int(l * 255), int(l * 255)

    q = l * (1 + s) if l < 0.5 else l + s - l * s
    p = 2 * l - q
    
    r = hue_to_rgb(p, q, h + 1/3)
    g = hue_to_rgb(p, q, h)
    b = hue_to_rgb(p, q, h - 1/3)

    return int(r * 255), int(g * 255), int(b * 255)

def main():
    """
    Main loop to read joystick values, convert to HSL, and set the LED color.
    """
    # A constant lightness value to keep the colors vibrant.
    # You can change this to 0.0 (black) or 1.0 (white) for different effects.
    lightness = 0.5
    
    print("Using joystick to control HSL color space...")
    print("X-axis: Hue (wraps around)")
    print("Y-axis: Saturation")
    
    while True:
        # Read the 16-bit values from the ADC pins.
        x_val = adc_x.read_u16()
        y_val = adc_y.read_u16()
        
        # Map the joystick's X-axis value (0-65535) to the Hue range (0.0-1.0).
        # This mapping naturally creates the "wrap around" effect.
        hue = x_val / 65535.0
        
        # Map the joystick's Y-axis value (0-65535) to the Saturation range (0.0-1.0).
        saturation = y_val / 65535.0
        
        # Convert the HSL values to RGB.
        r, g, b = hsl_to_rgb(hue, saturation, lightness)
        
        # Set the LED color.
        set_rgb_color(r, g, b)
        
        # Print the current values for feedback.
        print(f"Hue: {hue:.2f}, Saturation: {saturation:.2f}, Lightness: {lightness} -> RGB: ({r},{g},{b})")
        
        # Small delay to prevent the loop from running too fast.
        time.sleep(0.01)

if __name__ == "__main__":
    main()
