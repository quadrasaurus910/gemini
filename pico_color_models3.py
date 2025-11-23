# colorModels.py
# Updated to handle instant joystick exit and Common Anode logic

from machine import Pin, PWM
import time
import math

# --- Configuration ---
# Set this to True if using a Common Anode LED (Shared 3.3V/5V pin)
COMMON_ANODE = True

# Joystick Configuration
JOY_DEAD_ZONE = 5000
JOY_EXIT_THRESHOLD = 32768 - JOY_DEAD_ZONE

# --- Hardware Setup ---
RED_PIN = 16
GREEN_PIN = 17
BLUE_PIN = 18

pwm_r = PWM(Pin(RED_PIN))
pwm_g = PWM(Pin(GREEN_PIN))
pwm_b = PWM(Pin(BLUE_PIN))
pwm_r.freq(1000)
pwm_g.freq(1000)
pwm_b.freq(1000)

# --- Helper Class for Exiting ---
class ExitApp(Exception):
    """Custom exception to break out of nested loops instantly."""
    pass

def check_exit(joy_pin):
    """Checks joystick. Raises ExitApp if moved left."""
    if joy_pin:
        val = joy_pin.read_u16()
        if val < JOY_EXIT_THRESHOLD:
            raise ExitApp()

def set_rgb_color(r, g, b):
    """Sets RGB color, handling Common Anode inversion automatically."""
    # Scale 0-255 to 0-65535
    r_val = r * 257
    g_val = g * 257
    b_val = b * 257

    if COMMON_ANODE:
        # Invert for Common Anode
        pwm_r.duty_u16(65535 - r_val)
        pwm_g.duty_u16(65535 - g_val)
        pwm_b.duty_u16(65535 - b_val)
    else:
        # Normal for Common Cathode
        pwm_r.duty_u16(r_val)
        pwm_g.duty_u16(g_val)
        pwm_b.duty_u16(b_val)

def turn_off_leds():
    set_rgb_color(0, 0, 0)

# --- Color Conversion Functions (Same as before, stripped for brevity) ---
# (We keep the logic but focus on the loops below)

def hsv_to_rgb(h, s, v):
    if s == 0.0: return int(v * 255), int(v * 255), int(v * 255)
    i = int(h * 6.0)
    f = (h * 6.0) - i
    p, q, t = v * (1.0 - s), v * (1.0 - f * s), v * (1.0 - (1.0 - f) * s)
    i = i % 6
    if i == 0: r, g, b = v, t, p
    elif i == 1: r, g, b = q, v, p
    elif i == 2: r, g, b = p, v, t
    elif i == 3: r, g, b = p, q, v
    elif i == 4: r, g, b = t, p, v
    else: r, g, b = v, p, q
    return int(r * 255), int(g * 255), int(b * 255)

# --- Loop Functions with Joystick Checks ---

def rgb_model_loop(joy_pin):
    print("RGB Loop")
    # Red Fade
    for i in range(256):
        check_exit(joy_pin)
        set_rgb_color(i, 0, 0)
        time.sleep(0.005)
    for i in range(255, -1, -1):
        check_exit(joy_pin)
        set_rgb_color(i, 0, 0)
        time.sleep(0.005)
        
    # Green Fade
    for i in range(256):
        check_exit(joy_pin)
        set_rgb_color(0, i, 0)
        time.sleep(0.005)
    for i in range(255, -1, -1):
        check_exit(joy_pin)
        set_rgb_color(0, i, 0)
        time.sleep(0.005)

def hsv_model_loop(joy_pin):
    print("HSV Loop")
    # Rainbow Cycle
    for h in range(360):
        check_exit(joy_pin)
        r, g, b = hsv_to_rgb(h / 360.0, 1.0, 1.0)
        set_rgb_color(r, g, b)
        time.sleep(0.01)

def cmy_loop(joy_pin):
    print("CMY Loop")
    # Cyan mix
    for i in range(256):
        check_exit(joy_pin)
        # Cyan is Green + Blue
        set_rgb_color(0, i, i) 
        time.sleep(0.01)
    time.sleep(0.5)
    # Magenta mix
    for i in range(256):
        check_exit(joy_pin)
        set_rgb_color(i, 0, i)
        time.sleep(0.01)

# --- Main Entry Point ---

def main(joy_x_pin):
    """
    The main entry point called by lights_app.
    """
    try:
        while True:
            rgb_model_loop(joy_x_pin)
            time.sleep(0.5)
            
            hsv_model_loop(joy_x_pin)
            time.sleep(0.5)
            
            cmy_loop(joy_x_pin)
            time.sleep(0.5)
            
    except ExitApp:
        # This block catches the "Bump Left" event from anywhere deep in the loops
        turn_off_leds()
        print("Exiting Color Models...")
        return
