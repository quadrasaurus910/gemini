import time
from machine import Pin

# Pin definitions for the RGB LED
# The RGB pins are connected to GPIOs 24 (R), 22 (G), and 21 (B)
red_pin = Pin(24, Pin.OUT)
green_pin = Pin(22, Pin.OUT)
blue_pin = Pin(21, Pin.OUT)

# A function to turn all pins off
def all_off():
    # Since this is a common anode, we set all pins to HIGH to turn them off
    red_pin.on()
    green_pin.on()
    blue_pin.on()

# Test function for a single color
def test_pin(pin_object, color_name):
    print(f"--- Testing {color_name} LED pin... ---")
    all_off() # Ensure all LEDs are off before testing
    time.sleep(1)
    
    # Turn on the specific pin by setting it to LOW
    pin_object.off()
    
    print(f"Is the {color_name} LED on?")
    print("Please check the LED and then wait for the next test.")
    time.sleep(3) # Wait for 3 seconds for the user to observe
    
    # Turn off the pin by setting it back to HIGH
    pin_object.on()
    time.sleep(1)
    print(f"--- {color_name} test complete. ---")
    
# Main test sequence
try:
    print("Starting RGB LED test sequence...")
    # Initialize all pins to the "off" state for common anode
    all_off()
    time.sleep(1)
    
    test_pin(red_pin, "RED")
    test_pin(green_pin, "GREEN")
    test_pin(blue_pin, "BLUE")

    print("\n--- Test sequence complete. ---")
    print("If you saw the LED cycle through Red, Green, and Blue, all pins are working.")
    
except Exception as e:
    print(f"An error occurred: {e}")
    all_off()
