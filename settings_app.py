# settings_app.py
# Handles Wi-Fi scanning, text input, and saving to config.py

import network
import utime
import gc
import config

# --- Constants ---
# Character set for input: Uppercase, Lowercase, Numbers, Symbols
CHAR_SET = " abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-=[]{};:,.<>?"
DEBOUNCE_MS = 200

# --- Helper Functions ---

def save_wifi_config(ssid, password):
    """
    Reads config.py, replaces the SSID and Password lines, 
    and writes it back to disk.
    """
    lines = []
    try:
        with open("config.py", "r") as f:
            lines = f.readlines()
    except OSError:
        return False # File not found

    new_lines = []
    for line in lines:
        if line.startswith("WIFI_SSID ="):
            new_lines.append(f"WIFI_SSID = '{ssid}'\n")
        elif line.startswith("WIFI_PASSWORD ="):
            new_lines.append(f"WIFI_PASSWORD = '{password}'\n")
        else:
            new_lines.append(line)
            
    try:
        with open("config.py", "w") as f:
            for line in new_lines:
                f.write(line)
        return True
    except OSError:
        return False

def get_text_input(lcd, joy_x, joy_y, joy_button, prompt_text, initial_text=""):
    """
    A complex loop that allows typing with the joystick.
    Y-axis: Change Character
    X-axis: Move Cursor
    Button: Confirm
    """
    current_text = list(initial_text)
    if not current_text:
        current_text = ['a'] # Start with 'a' if empty
        
    cursor_pos = 0
    last_move = 0
    
    lcd.clear()
    lcd.putstr(prompt_text[:16]) # Show prompt on line 1
    
    # Enable hardware cursor so user sees where they are
    lcd.blink_cursor_on()
    
    while True:
        current_time = utime.ticks_ms()
        
        # --- Handle Button Press (Save/Exit) ---
        if joy_button.value() == 1: 
            # Simple debounce for button
            utime.sleep(0.2)
            lcd.blink_cursor_off()
            return "".join(current_text).strip()

        # --- Handle Joystick Navigation (Debounced) ---
        if utime.ticks_diff(current_time, last_move) > DEBOUNCE_MS:
            
            x_val = joy_x.read_u16()
            y_val = joy_y.read_u16()
            moved = False
            
            # X-Axis: Move Cursor
            if x_val > 50000: # Right
                cursor_pos += 1
                if cursor_pos >= len(current_text):
                    current_text.append('a') # Add new char at end
                moved = True
            elif x_val < 15000: # Left
                if cursor_pos > 0:
                    cursor_pos -= 1
                    moved = True
            
            # Y-Axis: Change Character
            if y_val > 50000: # Down (Next Char)
                char_index = CHAR_SET.find(current_text[cursor_pos])
                next_index = (char_index + 1) % len(CHAR_SET)
                current_text[cursor_pos] = CHAR_SET[next_index]
                moved = True
            elif y_val < 15000: # Up (Prev Char)
                char_index = CHAR_SET.find(current_text[cursor_pos])
                prev_index = (char_index - 1 + len(CHAR_SET)) % len(CHAR_SET)
                current_text[cursor_pos] = CHAR_SET[prev_index]
                moved = True
                
            if moved:
                last_move = current_time
                
                # --- Rendering Logic (The Viewport) ---
                # We can only show 16 chars. 
                # If cursor is at 18, we show indices 3 to 19.
                start_index = 0
                if cursor_pos > 15:
                    start_index = cursor_pos - 15
                
                display_slice = "".join(current_text)[start_index : start_index + 16]
                
                lcd.move_to(0, 1)
                lcd.putstr(display_slice.ljust(16)) # Pad with spaces to clear old text
                
                # Move physical cursor to correct spot on screen
                screen_cursor_x = cursor_pos - start_index
                lcd.move_to(screen_cursor_x, 1)

        utime.sleep_ms(20)

def scan_networks(lcd, wlan):
    """Scans for networks and returns a list of unique SSIDs."""
    lcd.clear()
    lcd.putstr("Scanning...")
    
    if not wlan:
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        
    try:
        scan_results = wlan.scan() # Returns list of tuples
        # Format: (ssid, bssid, channel, RSSI, authmode, hidden)
        # We sort by RSSI (signal strength), which is index 3
        scan_results.sort(key=lambda x: x[3], reverse=True)
        
        ssids = []
        for result in scan_results:
            ssid_str = result[0].decode('utf-8')
            if ssid_str and ssid_str not in ssids:
                ssids.append(ssid_str)
        return ssids
    except Exception as e:
        return []

# --- Main Settings Menu ---

def run_settings_app(lcd, joy_x, joy_y, joy_button, wlan):
    """Main menu for Settings."""
    options = ["Scan WiFi", "Manual WiFi", "Back"]
    current_idx = 0
    last_move = 0
    
    lcd.clear()
    lcd.putstr("> " + options[0])
    
    while True:
        # Joystick Navigation for Menu
        y_val = joy_y.read_u16()
        x_val = joy_x.read_u16()
        current_time = utime.ticks_ms()
        
        if utime.ticks_diff(current_time, last_move) > 250:
            if y_val > 50000: # Down
                current_idx = (current_idx + 1) % len(options)
                lcd.clear()
                lcd.putstr("> " + options[current_idx])
                last_move = current_time
            elif y_val < 15000: # Up
                current_idx = (current_idx - 1 + len(options)) % len(options)
                lcd.clear()
                lcd.putstr("> " + options[current_idx])
                last_move = current_time
                
            # Select Option (Right or Button)
            if x_val > 50000 or joy_button.value() == 1:
                selected = options[current_idx]
                
                if selected == "Back":
                    return # Go back to main menu
                    
                elif selected == "Manual WiFi":
                    # 1. Enter SSID
                    new_ssid = get_text_input(lcd, joy_x, joy_y, joy_button, "Enter SSID:", config.WIFI_SSID)
                    # 2. Enter Password
                    new_pass = get_text_input(lcd, joy_x, joy_y, joy_button, "Enter Pass:", "")
                    
                    # 3. Save
                    lcd.clear()
                    lcd.putstr("Saving Config...")
                    if save_wifi_config(new_ssid, new_pass):
                        lcd.move_to(0,1); lcd.putstr("Saved! Rebooting")
                        utime.sleep(2)
                        import machine
                        machine.reset() # Reboot to apply changes
                    else:
                        lcd.move_to(0,1); lcd.putstr("Save Error")
                        utime.sleep(2)
                        
                elif selected == "Scan WiFi":
                    ssids = scan_networks(lcd, wlan)
                    if not ssids:
                        lcd.clear(); lcd.putstr("No Networks"); utime.sleep(2)
                    else:
                        # Simple loop to scroll through SSIDs
                        ssid_idx = 0
                        while True:
                            lcd.clear()
                            lcd.putstr(f"Select Network:")
                            lcd.move_to(0,1)
                            lcd.putstr(f"> {ssids[ssid_idx][:14]}") # Truncate if too long
                            
                            utime.sleep(0.3)
                            
                            # Wait for input
                            while True:
                                jy = joy_y.read_u16()
                                jx = joy_x.read_u16()
                                btn = joy_button.value()
                                
                                if jy > 50000: # Next Network
                                    ssid_idx = (ssid_idx + 1) % len(ssids)
                                    break
                                elif jy < 15000: # Prev Network
                                    ssid_idx = (ssid_idx - 1 + len(ssids)) % len(ssids)
                                    break
                                elif btn == 1 or jx > 50000: # Select
                                    target_ssid = ssids[ssid_idx]
                                    # Go to Password Entry
                                    new_pass = get_text_input(lcd, joy_x, joy_y, joy_button, "Enter Pass:", "")
                                    # Save
                                    lcd.clear(); lcd.putstr("Saving...")
                                    save_wifi_config(target_ssid, new_pass)
                                    utime.sleep(1)
                                    import machine
                                    machine.reset()
                                    
                                elif jx < 15000: # Back to settings menu
                                    ssid_idx = -1 
                                    break
                                    
                            if ssid_idx == -1: break
                            
                # Restore Menu after action
                lcd.clear()
                lcd.putstr("> " + options[current_idx])
                last_move = utime.ticks_ms()

        utime.sleep_ms(50)
        gc.collect()
