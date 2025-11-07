# The central controller for all applications on the Pico build.
# ...

from machine import Pin, I2C, ADC
import utime
import gc

# Import LCD driver libraries
from pico_i2c_lcd import I2cLcd

# Import the new startup module
import startup

# Import the application modules
import clock_app
import lights_app
import weather_app # Make sure this is imported

# ... (Hardware Configuration remains the same) ...

# --- Global Variables ---
menu_items = ["Clock", "Weather", "Lights", "Settings"]
# ... (rest of the globals are fine) ...

# --- Hardware Initialization ---
# ... (All hardware init remains the same) ...

# --- Functions ---

# We can remove the old startup_script() function.

def get_lcd_object():
    # ... (This function remains the same) ...

def update_menu_display(lcd, menu_items, current_index):
    # ... (This function remains the same) ...
    
def execute_action(lcd, wlan, menu_item, joy_x, joy_y):
    """Executes the action for the selected menu item."""
    if menu_item == "Clock":
        print("Launching Clock App...")
        lcd.clear()
        # Pass the wlan object and joystick X-axis
        # We will need to update clock_app to accept 'wlan'
        clock_app.run_clock_app(lcd, joy_x, wlan)
        
    elif menu_item == "Weather":
        print("Launching Weather App...")
        lcd.clear()
        # Pass the wlan object and joystick X-axis
        # We will need to update weather_app to accept 'wlan'
        weather_app.run_weather_app(lcd, joy_x, wlan)
        
    elif menu_item == "Lights":
        print("Launching Lights App...")
        # Lights app probably doesn't need internet
        lights_app.run_lights_app(lcd, joy_x, joy_y)
        
    elif menu_item == "Settings":
        print("Launching Settings App...")
        lcd.clear()
        lcd.putstr("Settings coming!")
        utime.sleep(2)
        
    # Re-display the menu after returning from an app
    # Reset index to 0 so it's predictable
    global current_menu_index
    current_menu_index = 0
    update_menu_display(lcd, menu_items, current_menu_index)
    
def main_loop():
    """The main application loop for menu navigation and app launching."""
    global current_menu_index, last_move_time

    lcd = get_lcd_object()
    if not lcd:
        print("LCD not found. Skipping LCD display.")
        # We can still run, just without a display
    
    # --- Run the new startup sequence ---
    # This will connect to WiFi and return the connection object
    wlan = startup.initialize(lcd)
    # -------------------------------------

    # Initial display of the menu
    update_menu_display(lcd, menu_items, current_menu_index)

    while True:
        joy_x_val = joy_x.read_u16()
        joy_y_val = joy_y.read_u16()
        current_time = utime.ticks_ms()

        if utime.ticks_diff(current_time, last_move_time) > DEBOUNCE_DELAY_MS:
            # ... (Y-axis navigation logic remains the same) ...
                
            # X-axis for selecting/entering an app
            if joy_x_val > 32768 + JOY_DEAD_ZONE:
                # Pass the wlan object to the action function
                execute_action(lcd, wlan, menu_items[current_menu_index], joy_x, joy_y)
                last_move_time = current_time

        utime.sleep_ms(10)
        gc.collect()

# Run the main loop
main_loop()
