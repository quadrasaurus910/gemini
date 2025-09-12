# This is the main file for the Pi Pico build.
# It handles the overall structure, initializes hardware, and
# controls the main menu system using an LCD display.

from machine import Pin, ADC, I2C
import time

# Import your existing LCD library files.
from pico_i2c_lcd import I2cLcd

# --- Hardware Setup (shared across all apps) ---

# For the LCD:
# Connect the Pico's GP0 (SDA) to the LCD's SDA pin.
# Connect the Pico's GP1 (SCL) to the LCD's SCL pin.
# Connect GND and VCC on the LCD to the Pico's GND and 3.3V pins.
I2C_SDA_PIN = 0
I2C_SCL_PIN = 1
# Check your LCD's I2C address, 0x27 is a common one.
I2C_ADDR = 0x27
NUM_LINES = 2
NUM_COLS = 16

i2c = I2C(0, sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN), freq=400000)
lcd = I2cLcd(i2c, I2C_ADDR, NUM_LINES, NUM_COLS)

# For the Joystick:
# Connect the Joystick's VRX pin to a Pico ADC pin (e.g., GP26).
# Connect the Joystick's VRY pin to another Pico ADC pin (e.g., GP27).
# Connect GND and VCC on the joystick to a Pico's GND and 3.3V pins.
JOYSTICK_X_PIN = 26
JOYSTICK_Y_PIN = 27
adc_x = ADC(Pin(JOYSTICK_X_PIN))
adc_y = ADC(Pin(JOYSTICK_Y_PIN))

# --- Startup Script Placeholder ---
def startup_script():
    """
    This function runs once on boot for any one-time initialization.
    """
    lcd.clear()
    lcd.putstr("  Pico Project  ")
    lcd.move_to(0, 1)
    lcd.putstr("    Starting...  ")
    time.sleep(3)

# --- Menu State Management ---
# A list of strings representing your menu items.
menu_items = [
    "Clock App",
    "Weather App",
    "Light Settings",
    "Display Settings",
    "Menu Settings",
]

# State variables for menu navigation.
current_menu_index = 0
last_y_state = 0
DEBOUNCE_DELAY = 0.2
last_menu_change_time = 0

def update_menu_display():
    """
    Updates the menu display on the LCD screen.
    """
    lcd.clear()
    
    # Display the current menu item with a '>' indicator.
    lcd.move_to(0, 0)
    lcd.putstr(f"> {menu_items[current_menu_index]}")
    
    # Display the next menu item on the bottom line.
    # This helps the user see what's coming next.
    lcd.move_to(0, 1)
    if current_menu_index + 1 < len(menu_items):
        lcd.putstr(f"  {menu_items[current_menu_index + 1]}")
    else:
        # Wrap around to the first item if at the end of the list.
        lcd.putstr(f"  {menu_items[0]}")

def main_loop():
    """
    The central main loop of the system. It handles menu navigation.
    """
    global current_menu_index, last_y_state, last_menu_change_time

    # Run the startup script once.
    startup_script()
    update_menu_display()
    
    while True:
        # Read the 16-bit value from the ADC pin for the Y-axis.
        y_val = adc_y.read_u16()
        
        # Determine joystick state based on thresholds.
        menu_y_state = 0
        if y_val < 3000:
            menu_y_state = -1 # Up
        elif y_val > 62000:
            menu_y_state = 1 # Down
        
        # Get the current time for debouncing.
        current_time = time.monotonic()
        
        # Check if the state has changed and if enough time has passed since the last change.
        if menu_y_state != last_y_state and (current_time - last_menu_change_time) > DEBOUNCE_DELAY:
            if menu_y_state == -1:
                # Move up in the menu, with wrap-around.
                current_menu_index = (current_menu_index - 1 + len(menu_items)) % len(menu_items)
            elif menu_y_state == 1:
                # Move down in the menu, with wrap-around.
                current_menu_index = (current_menu_index + 1) % len(menu_items)
            
            # Update the last state and time.
            last_y_state = menu_y_state
            last_menu_change_time = current_time
            
            # Update the display immediately after a change.
            update_menu_display()
        
        # Small delay to prevent the loop from running too fast.
        time.sleep(0.01)

if __name__ == "__main__":
    main_loop()
