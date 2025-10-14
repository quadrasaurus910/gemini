# led_physics_transitions.py
# A standalone MicroPython script to demonstrate color transitions
# based on physical system responses (control theory).

import machine
import utime
import math

# --- HARDWARE SETUP (Common Anode RGB LED) ---
# Connect R, G, B pins to GPIOs, and the common anode to 3.3V.
# NOTE: For common anode, a 0% duty cycle is full brightness.
# We will handle this inversion in the set_led_color function.
R_PIN = 13
G_PIN = 14
B_PIN = 15

# Initialize PWM for each color channel
red = machine.PWM(machine.Pin(R_PIN))
green = machine.PWM(machine.Pin(G_PIN))
blue = machine.PWM(machine.Pin(B_PIN))
red.freq(1000)
green.freq(1000)
blue.freq(1000)

# --- CONFIGURATION ---
# Change these colors to experiment!
START_COLOR = (255, 0, 80)   # A vibrant pink
END_COLOR = (0, 255, 170)    # A nice teal

# Timing settings
TRANSITION_DURATION_S = 3.0  # How long each transition takes
PAUSE_BETWEEN_MODES_S = 2.0  # How long to wait on the final color

# --- PHYSICS PARAMETERS for Easing Functions ---
# Tune these to change the "feel" of the effects!

# For Damped Door (Critically Damped System) 🚪
DAMPED_OMEGA_N = 1.5  # Natural frequency. Higher = faster response.

# For Bouncy Spring / Resonant Circuit 🤸
BOUNCY_OMEGA_N = 10.0 # Natural frequency. Higher = faster, tighter bounces.
BOUNCY_ZETA = 0.15    # Damping ratio. Lower = more bouncy, higher = less bouncy.

# --- HELPER FUNCTIONS ---

def set_led_color(r, g, b):
    """Sets the RGB LED color, handling common anode inversion."""
    # Clamp values to the valid 0-255 range
    r = max(0, min(255, int(r)))
    g = max(0, min(255, int(g)))
    b = max(0, min(255, int(b)))
    
    # Invert for common anode and scale to 16-bit duty cycle (0-65535)
    red.duty_u16(65535 - (r * 257))
    green.duty_u16(65535 - (g * 257))
    blue.duty_u16(65535 - (b * 257))

def lerp(a, b, t):
    """Linear interpolation between 'a' and 'b' by factor 't'."""
    return a + (b - a) * t

# --- EASING FUNCTIONS (The Core Behavior Math) ---

def linear_ease(t_norm):
    """The most basic transition. A straight line."""
    return t_norm

def damped_ease(t_norm):
    """Models a critically damped system (like a smooth, heavy door).
    It reaches the target value as fast as possible without overshooting."""
    # We scale t_norm to get a better visual effect over the duration
    t = t_norm * 5 
    omega_n = DAMPED_OMEGA_N
    # Equation for critically damped second-order system response
    return 1 - (1 + omega_n * t) * math.exp(-omega_n * t)

def bouncy_ease(t_norm):
    """Models an underdamped system (bouncy spring, resonant circuit).
    It overshoots the target and oscillates before settling."""
    # We scale t_norm to get a good number of bounces
    t = t_norm * 8 
    zeta = BOUNCY_ZETA
    omega_n = BOUNCY_OMEGA_N
    omega_d = omega_n * math.sqrt(1 - zeta**2) # Damped frequency
    
    # Equation for underdamped second-order system response
    e_term = math.exp(-zeta * omega_n * t)
    cos_term = math.cos(omega_d * t)
    sin_term = (zeta * omega_n / omega_d) * math.sin(omega_d * t)
    
    return 1 - e_term * (cos_term + sin_term)


# --- MAIN TRANSITION CONTROLLER ---

def run_transition(start_rgb, end_rgb, duration_s, easing_function):
    """
    Handles the color transition over time using a specified easing function.
    
    Args:
        start_rgb (tuple): The starting (r, g, b) color.
        end_rgb (tuple): The target (r, g, b) color.
        duration_s (float): The total time the transition should take.
        easing_function (function): The function that defines the transition's curve.
    """
    start_time = utime.ticks_ms()
    
    while True:
        elapsed_ms = utime.ticks_diff(utime.ticks_ms(), start_time)
        
        # Check if the transition is complete
        if elapsed_ms >= duration_s * 1000:
            set_led_color(end_rgb[0], end_rgb[1], end_rgb[2])
            break
            
        # Calculate normalized time (a value from 0.0 to 1.0)
        normalized_time = elapsed_ms / (duration_s * 1000)
        
        # Get the progress value from the provided easing function
        progress = easing_function(normalized_time)
        
        # Calculate the current color for each channel using interpolation
        current_r = lerp(start_rgb[0], end_rgb[0], progress)
        current_g = lerp(start_rgb[1], end_rgb[1], progress)
        current_b = lerp(start_rgb[2], end_rgb[2], progress)
        
        set_led_color(current_r, current_g, current_b)
        
        utime.sleep_ms(10) # Small delay to prevent busy-looping

# --- MAIN LOOP ---

def main():
    """The main application loop that cycles through the behaviors."""
    
    behaviors = [
        ("Linear", linear_ease),
        ("Damped Door", damped_ease),
        ("Bouncy Spring", bouncy_ease)
    ]
    
    current_behavior_index = 0
    
    while True:
        # Get the current behavior's name and function
        name, ease_func = behaviors[current_behavior_index]
        
        print(f"--- Starting Transition: {name} ---")
        
        # Run the transition from start to end color
        run_transition(START_COLOR, END_COLOR, TRANSITION_DURATION_S, ease_func)
        utime.sleep(PAUSE_BETWEEN_MODES_S)
        
        print(f"--- Returning to Start: {name} ---")
        
        # Run the transition from end back to start color
        run_transition(END_COLOR, START_COLOR, TRANSITION_DURATION_S, ease_func)
        utime.sleep(PAUSE_BETWEEN_MODES_S)
        
        # Move to the next behavior for the next loop
        current_behavior_index = (current_behavior_index + 1) % len(behaviors)

# Run the main loop
main()

