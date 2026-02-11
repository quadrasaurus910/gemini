# spectral_shift.py
# Combines Periodic Table data with Relativistic Doppler Shift and Gravitational Lensing.

import utime
import math
import random
from machine import Pin, PWM

# --- Hardware Setup ---
pwm_r = PWM(Pin(16))
pwm_g = PWM(Pin(17))
pwm_b = PWM(Pin(18))
for p in [pwm_r, pwm_g, pwm_b]:
    p.freq(1000)

COMMON_ANODE = True 

# --- The Periodic Table Database ---
# Format: "Element": { "mass": Atomic_Weight, "wl": Rest_Wavelength_nm }
# We use the strongest visible emission line for the "Rest Color".
ELEMENTS = {
    "Hydrogen":   {"mass": 1.008,  "wl": 656}, # H-alpha (Red)
    "Helium":     {"mass": 4.002,  "wl": 587}, # Yellow
    "Lithium":    {"mass": 6.94,   "wl": 670}, # Deep Red
    "Oxygen":     {"mass": 15.999, "wl": 470}, # Blueish
    "Sodium":     {"mass": 22.99,  "wl": 589}, # Famous Sodium D (Orange)
    "Neon":       {"mass": 20.18,  "wl": 640}, # Red-Orange
    "Magnesium":  {"mass": 24.30,  "wl": 518}, # Green
    "Argon":      {"mass": 39.95,  "wl": 420}, # Violet
    "Krypton":    {"mass": 83.79,  "wl": 557}, # Green-Yellow
    "Xenon":      {"mass": 131.29, "wl": 467}, # Blue
    "Mercury":    {"mass": 200.59, "wl": 546}, # Green
    "Uranium":    {"mass": 238.02, "wl": 500}, # Hypothetical/Green glow
}

# --- Physics Functions ---

def wavelength_to_rgb(wavelength, gamma=0.8):
    """
    Converts a wavelength (nm) to an RGB value (0-255).
    Ranges outside 380-750nm return Black (invisible to human eye).
    """
    wavelength = float(wavelength)
    if wavelength >= 380 and wavelength <= 440:
        attenuation = 0.3 + 0.7 * (wavelength - 380) / (440 - 380)
        R = (-(wavelength - 440) / (440 - 380)) * attenuation
        G = 0.0
        B = 1.0 * attenuation
    elif wavelength >= 440 and wavelength <= 490:
        R = 0.0
        G = (wavelength - 440) / (490 - 440)
        B = 1.0
    elif wavelength >= 490 and wavelength <= 510:
        R = 0.0
        G = 1.0
        B = -(wavelength - 510) / (510 - 490)
    elif wavelength >= 510 and wavelength <= 580:
        R = (wavelength - 510) / (580 - 510)
        G = 1.0
        B = 0.0
    elif wavelength >= 580 and wavelength <= 645:
        R = 1.0
        G = -(wavelength - 645) / (645 - 580)
        B = 0.0
    elif wavelength >= 645 and wavelength <= 750:
        attenuation = 0.3 + 0.7 * (750 - wavelength) / (750 - 645)
        R = 1.0 * attenuation
        G = 0.0
        B = 0.0
    else:
        R = 0.0
        G = 0.0
        B = 0.0
    
    R = int(R * 255)
    G = int(G * 255)
    B = int(B * 255)
    return R, G, B

def set_rgb(r, g, b, brightness=1.0):
    # Apply master brightness
    r = int(r * brightness)
    g = int(g * brightness)
    b = int(b * brightness)
    
    # Cap at 255
    r = min(255, max(0, r))
    g = min(255, max(0, g))
    b = min(255, max(0, b))

    if COMMON_ANODE:
        pwm_r.duty_u16(65535 - (r * 257))
        pwm_g.duty_u16(65535 - (g * 257))
        pwm_b.duty_u16(65535 - (b * 257))
    else:
        pwm_r.duty_u16(r * 257)
        pwm_g.duty_u16(g * 257)
        pwm_b.duty_u16(b * 257)

def run_spectral_loop(lcd, joy_x_pin):
    print("Initializing Relativistic Spectroscopy...")
    lcd.clear()
    
    # Simulation Parameters
    element_names = list(ELEMENTS.keys())
    current_element_idx = 0
    
    t = 0.0
    
    while True:
        # 1. Get Element Data
        name = element_names[current_element_idx]
        data = ELEMENTS[name]
        mass = data["mass"]
        rest_wl = data["wl"]
        
        # 2. Calculate Orbit Speed based on Atomic Mass
        # Heavier elements (High Mass) orbit slower due to inertia.
        # Lighter elements orbit frantically.
        orbit_speed = 0.15 * (10 / mass) # Simple inverse relationship
        orbit_speed = max(0.02, min(0.3, orbit_speed)) # Clamp speed limits
        
        t += orbit_speed
        
        # 3. Simulate Relativistic Velocity (v/c) using Sine Wave
        # We simulate moving away (+v) and towards (-v)
        # Max velocity is 20% speed of light (0.2c)
        velocity_c = math.sin(t) * 0.2
        
        # 4. Calculate Doppler Shift (Relativistic Formula)
        # observed_wl = rest_wl * sqrt((1+v/c) / (1-v/c))
        # Simplified: wl * (1 + v/c) for low relativistic speeds
        shifted_wl = rest_wl * (1 + velocity_c)
        
        # 5. Gravitational Lensing (Brightness Boost)
        # When velocity is near 0 (crossing the perpendicular plane), 
        # we simulate a "Lens Event" where gravity magnifies the light.
        # We use a Gaussian bell curve centered at v=0.
        lensing_factor = math.exp(-15 * velocity_c**2) 
        brightness = 0.3 + (lensing_factor * 0.7) # Base 30%, Peak 100%
        
        # 6. Output to LED
        r, g, b = wavelength_to_rgb(shifted_wl)
        set_rgb(r, g, b, brightness)
        
        # 7. Output to LCD (Update periodically)
        # We show the Shift (Z) and the current Color Wavelength
        if int(t * 10) % 5 == 0:
            lcd.move_to(0,0)
            lcd.putstr(f"{name[:10]} {mass:.0f}u   ")
            
            lcd.move_to(0,1)
            # Display Velocity (v) and Lambda (wl)
            direction = "+" if velocity_c > 0 else "-"
            lcd.putstr(f"v:{direction}{abs(velocity_c):.2f}c L:{int(shifted_wl)}nm ")

        # 8. Element Switching Logic
        # Change element every ~1000 ticks (approx 20-30 seconds)
        if t > 60: 
            t = 0
            current_element_idx = (current_element_idx + 1) % len(element_names)
            lcd.clear()
            
        # 9. Exit Check
        if joy_x_pin.read_u16() < 20000:
            set_rgb(0,0,0)
            lcd.clear()
            lcd.putstr("Exiting Lab...")
            utime.sleep(1)
            return
            
        utime.sleep(0.05)
