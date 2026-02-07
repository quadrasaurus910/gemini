# cosmic_sim.py
# Simulates planetary sunsets using Wien's Displacement Law and Atmospheric Filtering.
# Displays real-time astrophysics calculations on the LCD.

import utime
import math
import random
from machine import Pin, PWM

# --- Hardware Setup ---
# LCD is passed in from main, but we need PWM for LED
pwm_r = PWM(Pin(16))
pwm_g = PWM(Pin(17))
pwm_b = PWM(Pin(18))
for p in [pwm_r, pwm_g, pwm_b]:
    p.freq(1000)

COMMON_ANODE = True 

# --- Astrophysics Database ---

# Format: ("Name", Temperature_Kelvin)
STARS = [
    ("Sun", 5778),            # G-Type (White/Yellow)
    ("Betelgeuse", 3500),     # Red Supergiant
    ("Rigel", 12100),         # Blue Supergiant
    ("Proxima Cen", 3042),    # Red Dwarf
    ("Sirius A", 9940),       # A-Type (White/Blue)
    ("Arcturus", 4290),       # K-Type (Orange)
    ("Trappist-1", 2566),     # Ultra-Cool Dwarf
    ("Vega", 9602),           # A-Type (Blueish)
    ("Kepler-186", 3755),     # M-Dwarf (Red/Orange)
]

# Format: ("Name", (R, G, B) - Approximate Atmospheric Absorption/Reflection)
# These colors represent what the atmosphere *lets through* or *scatters*.
PLANETS = [
    ("Earth", (200, 200, 255)),     # Rayleigh Scattering (Blue Sky)
    ("Mars", (255, 100, 50)),       # Iron Oxide dust (Red/Orange)
    ("Venus", (255, 240, 200)),     # Sulfur clouds (Yellow/White)
    ("HD189733b", (10, 50, 255)),   # Silicate rain (Deep Azure Blue)
    ("Kepler-22b", (50, 255, 200)), # Ocean World (Cyan/Teal)
    ("WASP-12b", (20, 0, 0)),       # Pitch Black (Absorbs 94% light)
    ("55 Cancri e", (255, 180, 180)),# Diamond Planet (Sparkling Pinkish)
    ("Titan", (255, 140, 0)),       # Hydrocarbon haze (Orange)
    ("Neptune", (50, 50, 255)),     # Methane (Deep Blue)
]

# --- Physics Functions ---

def wiens_displacement(temp_k):
    """
    Returns peak wavelength in nanometers.
    Constant b ≈ 2.898 x 10^6 nm*K
    """
    if temp_k == 0: return 0
    return 2898000 / temp_k

def kelvin_to_rgb(temp):
    """
    Approximates RGB color of a blackbody at Temperature K.
    Based on Tanner Helland's algorithm.
    """
    temp = temp / 100
    r, g, b = 0, 0, 0

    # Red
    if temp <= 66:
        r = 255
    else:
        r = temp - 60
        r = 329.698727446 * (r ** -0.1332047592)
        r = max(0, min(255, r))

    # Green
    if temp <= 66:
        g = temp
        g = 99.4708025861 * (math.log(g)) - 161.1195681661
        g = max(0, min(255, g))
    else:
        g = temp - 60
        g = 288.1221695283 * (g ** -0.0755148492)
        g = max(0, min(255, g))

    # Blue
    if temp >= 66:
        b = 255
    else:
        if temp <= 19:
            b = 0
        else:
            b = temp - 10
            b = 138.5177312231 * (math.log(b)) - 305.0447927307
            b = max(0, min(255, b))
    
    return int(r), int(g), int(b)

def calculate_interaction(star_rgb, planet_rgb, intensity):
    """
    Simulates light passing through atmosphere.
    Multiply star color by planet atmosphere color.
    """
    # Normalize 0-1
    sr, sg, sb = star_rgb[0]/255, star_rgb[1]/255, star_rgb[2]/255
    pr, pg, pb = planet_rgb[0]/255, planet_rgb[1]/255, planet_rgb[2]/255
    
    # Atmospheric filtering (Multiplication)
    r = sr * pr
    g = sg * pg
    b = sb * pb
    
    # Apply Intensity (Inverse Square Law Simulation)
    r *= intensity
    g *= intensity
    b *= intensity
    
    return int(r * 255), int(g * 255), int(b * 255)

def set_rgb(r, g, b):
    # Gamma correction for better eye perception
    r = int((r/255)**2 * 255)
    g = int((g/255)**2 * 255)
    b = int((b/255)**2 * 255)

    if COMMON_ANODE:
        pwm_r.duty_u16(65535 - (r * 257))
        pwm_g.duty_u16(65535 - (g * 257))
        pwm_b.duty_u16(65535 - (b * 257))
    else:
        pwm_r.duty_u16(r * 257)
        pwm_g.duty_u16(g * 257)
        pwm_b.duty_u16(b * 257)

# --- Main Simulation Loop ---

def run_cosmic_loop(lcd, joy_x_pin):
    print("Starting Cosmic Simulation...")
    lcd.clear()
    
    # Initial State
    current_star = random.choice(STARS)
    current_planet = random.choice(PLANETS)
    
    # Animation Variables
    t = 0
    orbit_speed = 0.05
    transition_timer = 0
    TRANSITION_INTERVAL = 200 # Cycles before switching targets
    
    while True:
        # 1. Physics Calculations
        star_name, star_temp = current_star
        planet_name, planet_atm = current_planet
        
        # Calculate Star's Base Color (Blackbody)
        star_rgb = kelvin_to_rgb(star_temp)
        
        # Calculate Wien's Peak Wavelength
        peak_nm = wiens_displacement(star_temp)
        
        # 2. Orbit Simulation (Sine Wave Distance)
        # Intensity varies between 0.2 (Far/Aphelion) and 1.0 (Close/Perihelion)
        orbit_pos = (math.sin(t) + 1) / 2 # 0.0 to 1.0
        intensity = 0.2 + (orbit_pos * 0.8)
        
        # 3. Determine Final Color
        final_rgb = calculate_interaction(star_rgb, planet_atm, intensity)
        set_rgb(*final_rgb)
        
        # 4. Update LCD (Only every 20 ticks to reduce flicker)
        if t % 5 < 0.1: # Approximate check
            lcd.move_to(0,0)
            # Row 1: "Sun->Earth"
            s_name = star_name[:7] # Truncate for space
            p_name = planet_name[:7]
            lcd.putstr(f"{s_name}>{p_name:<16}") # Pad with spaces
            
            lcd.move_to(0,1)
            # Row 2: "5778K w:501nm"
            lcd.putstr(f"{star_temp}K w:{int(peak_nm)}nm  ")

        # 5. Logic Updates
        t += orbit_speed
        transition_timer += 1
        
        # Switch targets smoothly? 
        # For now, we do a hard cut logic, but the sine wave makes it feel like a "fade out/in"
        # if we switch when intensity is low.
        if transition_timer > TRANSITION_INTERVAL and intensity < 0.3:
            current_star = random.choice(STARS)
            current_planet = random.choice(PLANETS)
            transition_timer = 0
            # Clear line to prevent text artifacts
            lcd.clear() 

        # 6. Exit Check
        if joy_x_pin.read_u16() < 20000:
            set_rgb(0,0,0)
            lcd.clear()
            lcd.putstr("Exiting Cosmos...")
            utime.sleep(1)
            return

        utime.sleep_ms(50)
