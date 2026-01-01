# bio_cycle.py
# Simulates a cyclic "Rock-Paper-Scissors" chemical reaction (predator-prey).
# R eats G, G eats B, B eats R.
# The "DNA" (Reaction Rates) mutates every generation.

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

class BioSystem:
    def __init__(self):
        # Initial Population (0.0 to 1.0)
        self.r = 0.5
        self.g = 0.5
        self.b = 0.5
        
        # The "DNA" - Reaction Rates
        # How fast does R eat G? etc.
        self.rate_rg = 0.05
        self.rate_gb = 0.05
        self.rate_br = 0.05
        
        # Natural decay (death rate)
        self.decay = 0.01
        # Natural growth (feed rate)
        self.growth = 0.02
        
        self.generation_count = 0

    def mutate(self):
        """Randomizes the reaction rates to change the balance of power."""
        self.generation_count += 1
        
        # Mutate the predation rates
        self.rate_rg = random.uniform(0.01, 0.08)
        self.rate_gb = random.uniform(0.01, 0.08)
        self.rate_br = random.uniform(0.01, 0.08)
        
        # Sometimes huge mutation (Catalyst event)
        if random.random() > 0.8:
            self.growth = random.uniform(0.01, 0.04)
        
        # Re-seed populations slightly to prevent extinction
        self.r += 0.2
        self.g += 0.2
        self.b += 0.2

    def update(self):
        """Calculates the next moment in time (Euler integration)."""
        # Calculate interactions
        # R grows, but is eaten by B, and eats G
        # Equation: New = Old + (Growth - Death - EatenByPredator + EatingPrey)
        
        # We use a simplified Lotka-Volterra cyclic model
        
        dr = (self.r * self.growth) - (self.r * self.decay) + (self.r * self.g * self.rate_rg) - (self.r * self.b * self.rate_br)
        dg = (self.g * self.growth) - (self.g * self.decay) + (self.g * self.b * self.rate_gb) - (self.g * self.r * self.rate_rg)
        db = (self.b * self.growth) - (self.b * self.decay) + (self.b * self.r * self.rate_br) - (self.b * self.g * self.rate_gb)
        
        self.r += dr
        self.g += dg
        self.b += db
        
        # Clamp to 0.0 - 1.0
        self.r = max(0.0, min(1.0, self.r))
        self.g = max(0.0, min(1.0, self.g))
        self.b = max(0.0, min(1.0, self.b))
        
        return self.r, self.g, self.b

def run_bio_loop(joy_x_pin):
    """
    Main Loop:
    Run the simulation -> Display Color -> Occasionally Mutate
    """
    system = BioSystem()
    
    # Timing
    steps = 0
    GENERATION_LENGTH = 500 # How many ticks before mutation
    
    print("Starting Bio-Cycle...")

    while True:
        # 1. Update Chemistry
        r_float, g_float, b_float = system.update()
        
        # 2. Display
        # Map 0.0-1.0 to 0-255
        set_rgb(r_float * 255, g_float * 255, b_float * 255)
        
        # 3. Check for Mutation
        steps += 1
        if steps > GENERATION_LENGTH:
            steps = 0
            
            # Flash White to indicate new generation
            set_rgb(100, 100, 100)
            utime.sleep(0.1)
            
            system.mutate()
            print(f"Gen {system.generation_count}: rg={system.rate_rg:.3f} gb={system.rate_gb:.3f} br={system.rate_br:.3f}")

        # 4. Check Exit
        if joy_x_pin.read_u16() < JOY_EXIT_THRESHOLD:
            set_rgb(0,0,0)
            return

        # 5. Speed
        utime.sleep_ms(15)
