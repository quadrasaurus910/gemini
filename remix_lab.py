# remix_lab.py
# A "Remix Engine" that combines math generators with dynamic effects.
# It creates unique, random combinations every few seconds.

import utime
import math
import random
from machine import Pin, PWM, ADC

# --- Configuration ---
COMMON_ANODE = True  # Set to True for your Common Anode LED
RED_PIN = 16
GREEN_PIN = 17
BLUE_PIN = 18

# Joystick Exit Config
JOY_EXIT_THRESHOLD = 20000 

# --- Hardware Init ---
pwm_r = PWM(Pin(RED_PIN))
pwm_g = PWM(Pin(GREEN_PIN))
pwm_b = PWM(Pin(BLUE_PIN))
pwm_r.freq(1000)
pwm_g.freq(1000)
pwm_b.freq(1000)

def set_rgb(r, g, b):
    """Writes color to LED, handling Common Anode inversion."""
    # Clamp to 0-255
    r = int(max(0, min(255, r)))
    g = int(max(0, min(255, g)))
    b = int(max(0, min(255, b)))
    
    # Scale to 16-bit duty cycle
    if COMMON_ANODE:
        pwm_r.duty_u16(65535 - (r * 257))
        pwm_g.duty_u16(65535 - (g * 257))
        pwm_b.duty_u16(65535 - (b * 257))
    else:
        pwm_r.duty_u16(r * 257)
        pwm_g.duty_u16(g * 257)
        pwm_b.duty_u16(b * 257)

# ==========================================
# 1. GENERATORS (The Source of the Signal)
# ==========================================
# These classes calculate the "next" color frame.

class GenLorenz:
    """Generates colors based on the Chaos Theory Lorenz Attractor."""
    def __init__(self):
        self.name = "Chaos Lorenz"
        self.x, self.y, self.z = 0.1, 0.0, 0.0
        self.dt = 0.02
        self.sigma, self.rho, self.beta = 10.0, 28.0, 8.0/3.0

    def next(self):
        dx = (self.sigma * (self.y - self.x)) * self.dt
        dy = (self.x * (self.rho - self.z) - self.y) * self.dt
        dz = (self.x * self.y - self.beta * self.z) * self.dt
        self.x += dx
        self.y += dy
        self.z += dz
        
        # Map chaotic coordinates to RGB
        r = max(0, min(255, (self.x + 20) * 6))
        g = max(0, min(255, (self.y + 25) * 5))
        b = max(0, min(255, self.z * 5))
        return r, g, b

class GenSineWave:
    """Generates smooth, overlapping sine waves for a soothing effect."""
    def __init__(self):
        self.name = "Sine Ocean"
        self.t = 0
    
    def next(self):
        self.t += 0.05
        r = (math.sin(self.t) + 1) * 127
        g = (math.sin(self.t * 1.3) + 1) * 127
        b = (math.sin(self.t * 0.7) + 1) * 127
        return r, g, b

class GenPlasma:
    """Simulates old-school demo scene plasma effect."""
    def __init__(self):
        self.name = "Plasma"
        self.t = 0

    def next(self):
        self.t += 0.03
        v1 = math.sin(self.t * 2)
        v2 = math.sin(self.t + v1)
        r = (math.sin(v1) + 1) * 127
        g = (math.cos(v2) + 1) * 127
        b = (math.sin(v1 + v2) + 1) * 127
        return r, g, b

# ==========================================
# 2. MODIFIERS ( The Filters )
# ==========================================
# These classes take an RGB value and change it.

class ModNone:
    """Does nothing. Pure signal."""
    def __init__(self): self.name = "Pure"
    def apply(self, r, g, b): return r, g, b

class ModStrobe:
    """Rapidly flashes the light on and off."""
    def __init__(self):
        self.name = "Strobe"
        self.frame = 0
        
    def apply(self, r, g, b):
        self.frame += 1
        # Flash every 5th frame
        if self.frame % 5 < 2: 
            return r, g, b
        else:
            return 0, 0, 0

class ModJitter:
    """Adds digital noise/glitches to the signal."""
    def __init__(self):
        self.name = "Glitch"
        
    def apply(self, r, g, b):
        # 10% chance to randomize color completely
        if random.random() > 0.90:
            return random.randint(0,255), random.randint(0,255), random.randint(0,255)
        return r, g, b

class ModBreathe:
    """Slowly fades the brightness up and down."""
    def __init__(self):
        self.name = "Breathe"
        self.t = 0
        
    def apply(self, r, g, b):
        self.t += 0.05
        factor = (math.sin(self.t) + 1) / 2 # 0.0 to 1.0
        # Ensure minimum brightness so it doesn't go fully black
        factor = 0.2 + (factor * 0.8) 
        return r * factor, g * factor, b * factor

# ==========================================
# 3. THE DIRECTOR ( The Main Loop )
# ==========================================

def run_remix_engine(joy_x_pin):
    """
    Randomly selects a Generator and a Modifier, runs them for a while,
    then switches to a new random combination.
    """
    
    # Lists of available modules
    generators = [GenLorenz, GenSineWave, GenPlasma]
    modifiers = [ModNone, ModNone, ModStrobe, ModJitter, ModBreathe] # ModNone added twice to make it more likely
    
    current_gen = None
    current_mod = None
    
    # Timing variables
    last_switch_time = 0
    SWITCH_INTERVAL = 5000 # Change effects every 5 seconds
    
    print("Entering Remix Lab...")

    while True:
        now = utime.ticks_ms()
        
        # --- 1. Check for Scene Switch ---
        if current_gen is None or utime.ticks_diff(now, last_switch_time) > SWITCH_INTERVAL:
            # Pick random new modules
            GenClass = random.choice(generators)
            ModClass = random.choice(modifiers)
            
            current_gen = GenClass()
            current_mod = ModClass()
            
            last_switch_time = now
            print(f"Mix: {current_gen.name} + {current_mod.name}")
            
            # Optional: Flash white to indicate switch
            set_rgb(50, 50, 50)
            utime.sleep(0.1)

        # --- 2. Calculate Frame ---
        # Get base color
        r, g, b = current_gen.next()
        
        # Apply effect
        r, g, b = current_mod.apply(r, g, b)
        
        # Output to LED
        set_rgb(r, g, b)

        # --- 3. Check Exit (Joystick Left) ---
        val = joy_x_pin.read_u16()
        if val < JOY_EXIT_THRESHOLD:
            set_rgb(0, 0, 0)
            print("Exiting Remix Lab.")
            utime.sleep(0.5) # Debounce
            return

        # --- 4. Speed Control ---
        utime.sleep_ms(20)
