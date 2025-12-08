# turing.py
# Simulates 1D Reaction-Diffusion (Gray-Scott Model)
# Creates "Virtual Skin" patterns that are scanned by the LED.

import utime
import math
import random
from machine import Pin, PWM

# --- Configuration ---
COMMON_ANODE = True 
JOY_EXIT_THRESHOLD = 20000 
LED_PINS = [16, 17, 18] # R, G, B

# --- Hardware Init ---
pwm_r = PWM(Pin(LED_PINS[0]))
pwm_g = PWM(Pin(LED_PINS[1]))
pwm_b = PWM(Pin(LED_PINS[2]))
for pwm in [pwm_r, pwm_g, pwm_b]:
    pwm.freq(1000)

def set_rgb(r, g, b):
    # Clamp 0-255
    r = int(max(0, min(255, r)))
    g = int(max(0, min(255, g)))
    b = int(max(0, min(255, b)))
    
    if COMMON_ANODE:
        pwm_r.duty_u16(65535 - (r * 257))
        pwm_g.duty_u16(65535 - (g * 257))
        pwm_b.duty_u16(65535 - (b * 257))
    else:
        pwm_r.duty_u16(r * 257)
        pwm_g.duty_u16(g * 257)
        pwm_b.duty_u16(b * 257)

class Turing1D:
    def __init__(self, size=40):
        self.size = size
        # Chemical A (Food) starts everywhere
        self.A = [1.0] * size
        # Chemical B (Predator) starts at 0
        self.B = [0.0] * size
        
        # Seed a little "B" in the center to start the reaction
        mid = size // 2
        for i in range(mid-2, mid+2):
            self.B[i] = 1.0

        # Gray-Scott Parameters (The "DNA")
        # Standard "Spots" regime to start
        self.DA = 1.0   # Diffusion rate A
        self.DB = 0.5   # Diffusion rate B
        self.f = 0.055  # Feed rate
        self.k = 0.062  # Kill rate

    def mutate(self):
        """Slightly changes the feed/kill rates to evolve the pattern."""
        self.f += random.uniform(-0.002, 0.002)
        self.k += random.uniform(-0.002, 0.002)
        
        # Clamp to interesting "Life" boundaries
        self.f = max(0.01, min(0.1, self.f))
        self.k = max(0.03, min(0.07, self.k))
        
        # Reset Chemicals for new incubation
        self.A = [1.0] * self.size
        self.B = [0.0] * self.size
        mid = self.size // 2
        for i in range(mid-3, mid+3):
             self.B[i] = 1.0

    def incubate(self, steps=500):
        """Runs the simulation steps invisibly."""
        # Laplacian weights for 1D diffusion (Left, Center, Right)
        # Using a simple 1D kernel [1, -2, 1]
        
        for _ in range(steps):
            new_A = self.A[:]
            new_B = self.B[:]
            
            for i in range(self.size):
                # Wrap-around indices (Toroidal surface)
                left = (i - 1) % self.size
                right = (i + 1) % self.size
                
                # Diffusion (Laplacian)
                lap_a = self.A[left] + self.A[right] - (2 * self.A[i])
                lap_b = self.B[left] + self.B[right] - (2 * self.B[i])
                
                # Reaction
                # A becomes B (A + 2B -> 3B)
                reaction = self.A[i] * self.B[i] * self.B[i]
                
                # Updates
                # A: Diffusion - Reaction + Feed
                new_A[i] = self.A[i] + (self.DA * lap_a - reaction + self.f * (1.0 - self.A[i]))
                # B: Diffusion + Reaction - Kill
                new_B[i] = self.B[i] + (self.DB * lap_b + reaction - (self.k + self.f) * self.B[i])
                
                # Clamp (Chemistry breaks if values go negative or infinite)
                new_A[i] = max(0.0, min(1.0, new_A[i]))
                new_B[i] = max(0.0, min(1.0, new_B[i]))
            
            self.A = new_A
            self.B = new_B

def run_turing_loop(joy_x_pin):
    """
    Main loop: Incubate -> Display -> Mutate -> Repeat
    """
    # Create the virtual skin
    skin = Turing1D(size=60) # 60 "cells" wide
    
    generation = 1
    
    print("Starting Turing Evolution...")

    while True:
        # --- PHASE 1: INCUBATION (Red Glow) ---
        # Show a dim red "heartbeat" while calculating
        for brightness in range(0, 50, 5):
            set_rgb(brightness, 0, 0)
            utime.sleep(0.02)
        
        # Run the math (CPU intensive part)
        skin.incubate(steps=1000)
        
        set_rgb(0,0,0) # Off before reveal
        utime.sleep(0.2)

        # --- PHASE 2: SCANNING (Display) ---
        # Scan the pattern back and forth 4 times
        for scan in range(4):
            # Scan Left to Right
            for i in range(skin.size):
                # Check Exit
                if joy_x_pin.read_u16() < JOY_EXIT_THRESHOLD:
                    set_rgb(0,0,0)
                    return

                # Map Chemical B concentration to Color
                # B usually ranges 0.0 to 0.4 in this model
                chem_b = skin.B[i]
                
                # Amplify for visibility
                intensity = chem_b * 3.0 
                if intensity > 1.0: intensity = 1.0
                
                # Color Palette: Cyan for "Pattern", Dark Blue for "Background"
                r_val = 0
                g_val = int(intensity * 255)       # High Green
                b_val = int(intensity * 200 + 55)  # High Blue + base
                
                set_rgb(r_val, g_val, b_val)
                utime.sleep(0.04) # Scan speed

            # Scan Right to Left (Boomerang effect)
            for i in range(skin.size - 1, -1, -1):
                 # Check Exit
                if joy_x_pin.read_u16() < JOY_EXIT_THRESHOLD:
                    set_rgb(0,0,0)
                    return

                chem_b = skin.B[i]
                intensity = chem_b * 3.0
                if intensity > 1.0: intensity = 1.0
                
                r_val = 0
                g_val = int(intensity * 255)
                b_val = int(intensity * 200 + 55)
                
                set_rgb(r_val, g_val, b_val)
                utime.sleep(0.04)
        
        # --- PHASE 3: MUTATION ---
        # Flash White briefly to signal mutation
        set_rgb(50, 50, 50)
        utime.sleep(0.1)
        set_rgb(0,0,0)
        
        skin.mutate()
        generation += 1
        print("Mutating to Generation:", generation)
