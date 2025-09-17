from machine import Pin, I2C
from utime import sleep
from pico_i2c_lcd import I2cLcd
import random

# LCD configuration
# The I2C settings here are a common setup for the Pico W.
# Check your specific wiring if this doesn't work.
I2C_ADDR = 0x27
I2C_NUM_ROWS = 2
I2C_NUM_COLS = 16

i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)
lcd = I2cLcd(i2c, I2C_ADDR, I2C_NUM_ROWS, I2C_NUM_COLS)

# Common Anode RGB LED configuration
# The LED is common anode, so 0 is ON and 1 is OFF.
# The pins are set for a common setup. Adjust these to your wiring.
PIN_RED = Pin(16, Pin.OUT)
PIN_GREEN = Pin(17, Pin.OUT)
PIN_BLUE = Pin(18, Pin.OUT)

# Function to set RGB LED color
def set_color(r, g, b):
    # Common Anode logic: 0 = on, 1 = off
    PIN_RED.value(1 - r)
    PIN_GREEN.value(1 - g)
    PIN_BLUE.value(1 - b)

# Main loop
try:
    while True:
        # Display first message
        lcd.clear()
        lcd.move_to(3, 0)
        lcd.putstr("It's your")
        lcd.move_to(4, 1)
        lcd.putstr("Birthday")
        
        # Animate the LED
        for _ in range(30):  # Play the effect for a few seconds
            r = random.randint(0, 1)
            g = random.randint(0, 1)
            b = random.randint(0, 1)
            set_color(r, g, b)
            sleep(0.1) # Short delay for a cool effect

        # Display second message
        lcd.clear()
        lcd.move_to(4, 0)
        lcd.putstr("Brittany")
        lcd.move_to(6, 1)
        lcd.putstr("Long")

        # Animate the LED again
        for _ in range(30):  # Play the effect for a few seconds
            r = random.randint(0, 1)
            g = random.randint(0, 1)
            b = random.randint(0, 1)
            set_color(r, g, b)
            sleep(0.1)
            
except KeyboardInterrupt:
    print("Script stopped.")
    lcd.clear()
    set_color(1, 1, 1)  # Turn off the LED
    
