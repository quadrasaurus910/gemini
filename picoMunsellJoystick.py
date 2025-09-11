# This script demonstrates how to use a joystick to navigate a lookup table
# for the Munsell color model. The joystick's X and Y axes control which
# color is selected from the pre-computed table.

from machine import Pin, PWM, ADC
import time

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

pwm_r = PWM(Pin(RED_PIN))
pwm_g = PWM(Pin(GREEN_PIN))
pwm_b = PWM(Pin(BLUE_PIN))
pwm_r.freq(1000)
pwm_g.freq(1000)
pwm_b.freq(1000)

adc_x = ADC(Pin(JOYSTICK_X_PIN))
adc_y = ADC(Pin(JOYSTICK_Y_PIN))

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

# The data is sorted by Hue and then by a combined Value/Chroma for
# easier navigation with the joystick.
MUNSELL_LOOKUP_TABLE = [
    # Red Hues (R)
    ("5R", 2, 2, 85, 0, 0),
    ("5R", 4, 4, 153, 0, 0),
    ("5R", 6, 8, 255, 0, 0),
    ("5R", 8, 10, 255, 102, 102),
    
    # Yellow Hues (Y)
    ("5Y", 6, 6, 255, 255, 0),
    ("5Y", 8, 8, 255, 255, 102),
    ("5Y", 4, 4, 255, 128, 0),
    
    # Blue-Green Hues (BG)
    ("5BG", 4, 4, 0, 102, 102),
    ("5BG", 6, 6, 0, 153, 153),
    ("5BG", 8, 2, 102, 204, 204),
    
    # Purple-Blue Hues (PB)
    ("5PB", 4, 4, 51, 0, 153),
    ("5PB", 6, 6, 102, 0, 204),
    ("5PB", 8, 2, 178, 102, 255),
    
    # Neutral Scale (N)
    ("N", 0, 0, 0, 0, 0),
    ("N", 2, 0, 51, 51, 51),
    ("N", 4, 0, 102, 102, 102),
    ("N", 6, 0, 153, 153, 153),
    ("N", 8, 0, 204, 204, 204),
    ("N", 10, 0, 255, 255, 255),
]


def main():
    """
    The main function that reads joystick input and updates the LED color
    based on the Munsell lookup table.
    """
    num_colors = len(MUNSELL_LOOKUP_TABLE)
    
    print("Use the joystick to explore the Munsell color space.")
    
    while True:
        # Read the 16-bit values from the ADC pins. The Pico ADC is 12-bit
        # internally, but the read_u16() function returns a 16-bit value.
        x_val = adc_x.read_u16()
        y_val = adc_y.read_u16()
        
        # Map the joystick's X and Y values to an index in the lookup table.
        # We can use the X-axis for one dimension of the lookup table
        # and the Y-axis for another, or combine them to get a single index.
        # Here, we use a simple linear mapping.
        
        # Combine X and Y values to get a single index.
        # This mapping treats the table as a single 1D array.
        # The joystick range is approx. 0-65535.
        # We will use the X-axis for the main index.
        index = int((x_val / 65535) * num_colors)
        
        # Ensure the index is within the valid range of the list.
        index = max(0, min(index, num_colors - 1))
        
        # Look up the color from the table using the calculated index.
        hue, value, chroma, r, g, b = MUNSELL_LOOKUP_TABLE[index]
        
        # Set the LED to the new color.
        set_rgb_color(r, g, b)
        
        # Print the current color details to the console for feedback.
        print(f"Joystick Index: {index} -> Hue: {hue}, Value: {value}, Chroma: {chroma} (RGB: {r},{g},{b})")
        
        # Small delay to prevent the loop from running too fast.
        time.sleep(0.01)

if __name__ == "__main__":
    main()
