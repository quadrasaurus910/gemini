# lorenz.py
# A light pattern based on the Lorenz Attractor (Chaos Theory)
# Maps the X, Y, Z chaotic coordinates to R, G, B LED brightness.

import utime
import math
from machine import Pin, PWM

# --- LED Configuration ---
# UPDATE THESE PINS to match your specific wiring!
PIN_RED = 16
PIN_GREEN = 17
PIN_BLUE = 18

# Initialize PWM
pwm_r = PWM(Pin(PIN_RED))
pwm_g = PWM(Pin(PIN_GREEN))
pwm_b = PWM(Pin(PIN_BLUE))

# Set PWM frequency (1kHz is usually good for LEDs)
pwm_r.freq(1000)
pwm_g.freq(1000)
pwm_b.freq(1000)

# --- Lorenz System Constants ---
# These are the standard constants used in the Lorenz equations
SIGMA = 10.0
RHO = 28.0
BETA = 8.0 / 3.0

# Time step (delta t) - controls the speed of the simulation
DT = 0.015 

def map_value(value, min_val, max_val):
    """
    Maps a value from the Lorenz range to the PWM range (0-65535).
    Includes clamping to ensure we don't exceed limits.
    """
    # Normalize to 0.0 - 1.0
    normalized = (value - min_val) / (max_val - min_val)
    if normalized < 0: normalized = 0
    if normalized > 1: normalized = 1
    
    # Convert to 16-bit integer
    duty = int(normalized * 65535)
    return duty

def set_rgb(r, g, b):
    """
    Sets the LED brightness.
    HANDLES COMMON ANODE INVERSION HERE.
    If your LED is Common Cathode, remove the '65535 -' part.
    """
    pwm_r.duty_u16(65535 - r)
    pwm_g.duty_u16(65535 - g)
    pwm_b.duty_u16(65535 - b)

def run_lorenz_loop(joy_x_pin):
    """
    The main loop for the chaos generator.
    Accepts joy_x_pin to handle the exit condition.
    """
    
    # Initial State (starting slightly off-center is crucial for chaos)
    x = 0.1
    y = 0.0
    z = 0.0
    
    # Exit threshold (Joystick Left)
    JOY_EXIT_THRESHOLD = 22000 

    while True:
        # --- 1. Calculate the Lorenz System (Euler Method) ---
        # dx/dt = sigma * (y - x)
        # dy/dt = x * (rho - z) - y
        # dz/dt = x * y - beta * z
        
        dx = (SIGMA * (y - x)) * DT
        dy = (x * (RHO - z) - y) * DT
        dz = (x * y - BETA * z) * DT
        
        x = x + dx
        y = y + dy
        z = z + dz
        
        # --- 2. Map Coordinates to Colors ---
        # The Lorenz attractor typically stays within these bounds:
        # x: [-20, 20], y: [-30, 30], z: [0, 50]
        
        # We map them creatively to RGB to get good color mixing.
        # You can tweak the min/max values to change the color palette focus.
        r_val = map_value(x, -20, 20)
        g_val = map_value(y, -25, 25)
        b_val = map_value(z, 5, 45)
        
        # Update LED
        set_rgb(r_val, g_val, b_val)

        # --- 3. Check Exit Condition ---
        # Check if joystick is pushed left to go back
        if joy_x_pin.read_u16() < JOY_EXIT_THRESHOLD:
            # Turn off LEDs before leaving
            set_rgb(0, 0, 0)
            return

        # --- 4. Speed Control ---
        # A short sleep keeps the math running smoothly without being too jittery
        utime.sleep_ms(10)
