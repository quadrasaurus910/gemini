# blackbody.py
# Simulates the color temperature of a heating blackbody radiator (Kelvin).

import utime
import math
from machine import Pin, PWM

# --- Config ---
COMMON_ANODE = True 
JOY_EXIT_THRESHOLD = 22000

# Pins
RED_PIN = 16
GREEN_PIN = 17
BLUE_PIN = 18

pwm_r = PWM(Pin(RED_PIN))
pwm_g = PWM(Pin(GREEN_PIN))
pwm_b = PWM(Pin(BLUE_PIN))
pwm_r.freq(1000)
pwm_g.freq(1000)
pwm_b.freq(1000)

def set_rgb(r, g, b):
    # Clamp values
    r = max(0, min(255, int(r)))
    g = max(0, min(255, int(g)))
    b = max(0, min(255, int(b)))
    
    if COMMON_ANODE:
        pwm_r.duty_u16(65535 - (r * 257))
        pwm_g.duty_u16(65535 - (g * 257))
        pwm_b.duty_u16(65535 - (b * 257))
    else:
        pwm_r.duty_u16(r * 257)
        pwm_g.duty_u16(g * 257)
        pwm_b.duty_u16(b * 257)

def kelvin_to_rgb(temp):
    """
    Approximation algorithm for converting Kelvin (K) to RGB.
    Valid roughly from 1000K to 40000K.
    """
    temp = temp / 100.0

    # RED
    if temp <= 66:
        r = 255
    else:
        r = temp - 60
        r = 329.698727446 * (r ** -0.1332047592)
        
    # GREEN
    if temp <= 66:
        g = temp
        g = 99.4708025861 * math.log(g) - 161.1195681661
    else:
        g = temp - 60
        g = 288.1221695283 * (g ** -0.0755148492)
    
    # BLUE
    if temp >= 66:
        b = 255
    elif temp <= 19:
        b = 0
    else:
        b = temp - 10
        b = 138.5177312231 * math.log(b) - 305.0447927307

    return r, g, b

def run_blackbody_loop(joy_x_pin):
    """
    Cycles heat from 1000K (Ember) to 12000K (Blue Star) and back.
    """
    temp = 1000
    direction = 100 # Increment step
    
    while True:
        r, g, b = kelvin_to_rgb(temp)
        set_rgb(r, g, b)
        
        # Move temperature
        temp += direction
        if temp >= 12000 or temp <= 1000:
            direction *= -1 # Reverse direction
            
        # Check Exit
        if joy_x_pin.read_u16() < JOY_EXIT_THRESHOLD:
            set_rgb(0,0,0)
            return

        # Speed of simulation
        utime.sleep_ms(10) 
