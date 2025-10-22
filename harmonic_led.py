# harmonic_led_app.py
# A final, optimized version of the harmonic oscillator LED effect.
#
# This version is a self-contained "app" that can be imported by
# a main controller.
#
# CONTROLS:
# - Joystick Y-Axis: Selects the "rest" color's hue.
# - Joystick Button: "Plucks" the springs, causing a flare-up.
# - Joystick X-Axis (Left): Exits the application.

import machine
import utime
import math

# --- HARDWARE PINS (for standalone testing only) ---
R_PIN = 13
G_PIN = 14
B_PIN = 15
JOY_BUTTON_PIN = 22
JOY_X_PIN = 26
JOY_Y_PIN = 27

# --- CONFIGURATION (Tune These!) ---
# Physics (Slow, Bouncy, Visible)
PHYSICS_PARAMS = {'mass': 1.0, 'stiffness': 15.0, 'damping': 0.25}

# Pluck Force
PLUCK_FORCE = 700.0

# Joystick Settings
JOY_EXIT_THRESHOLD = 10000  # Value for "joystick left"
JOY_Y_DEAD_ZONE = 5000     # Tolerance for Y-axis center
DEBOUNCE_MS = 200

# --- HELPER FUNCTIONS ---

def set_led_color(pwm_pins, r, g, b):
    """Sets the RGB LED color, handling common anode inversion."""
    r = max(0, min(255, int(r)))
    g = max(0, min(255, int(g)))
    b = max(0, min(255, int(b)))
    
    pwm_pins['red'].duty_u16(65535 - (r * 257))
    pwm_pins['green'].duty_u16(65535 - (g * 257))
    pwm_pins['blue'].duty_u16(65535 - (b * 257))

def hsv_to_rgb(h, s, v):
    """Convert HSV (all 0.0-1.0) to RGB (all 0-255)."""
    if s == 0.0:
        r = g = b = int(v * 255)
        return (r, g, b)
    
    h = h * 6.0 # Scale h to 0-6
    i = int(h)
    f = h - i
    p = v * (1.0 - s)
    q = v * (1.0 - s * f)
    t = v * (1.0 - s * (1.0 - f))
    
    v = int(v * 255)
    t = int(t * 255)
    p = int(p * 255)
    q = int(q * 255)
    
    if i == 0:
        return (v, t, p)
    elif i == 1:
        return (q, v, p)
    elif i == 2:
        return (p, v, t)
    elif i == 3:
        return (p, q, v)
    elif i == 4:
        return (t, p, v)
    else:
        return (v, p, q)

# --- PHYSICS CLASS ---

class Oscillator:
    """Simulates a single 1D damped harmonic oscillator."""
    def __init__(self, mass, stiffness, damping, rest_position):
        self.mass = mass
        self.k = stiffness
        self.c = damping
        self.rest_pos = rest_position
        self.pos = rest_position
        self.vel = 0.0
        self.accel = 0.0

    def update(self, dt):
        """Update the oscillator's state using Euler integration."""
        if dt <= 0: return
        force_spring = -self.k * (self.pos - self.rest_pos)
        force_damping = -self.c * self.vel
        self.accel = (force_spring + force_damping) / self.mass
        self.vel += self.accel * dt
        self.pos += self.vel * dt
        
    def pluck(self, force):
        """Applies an instantaneous force."""
        self.vel += force / self.mass

# --- MAIN APPLICATION ---

def run_harmonic_app(joy_x, joy_y, joy_button):
    """Main application loop. Call this from your menu."""
    
    print("Starting Harmonic LED App...")
    
    # --- Hardware Setup (for this app) ---
    # We initialize the PWM objects here, assuming they are not
    # already initialized. If they are, you could pass them in.
    pwm_pins = {
        'red': machine.PWM(machine.Pin(R_PIN)),
        'green': machine.PWM(machine.Pin(G_PIN)),
        'blue': machine.PWM(machine.Pin(B_PIN))
    }
    for pin in pwm_pins.values():
        pin.freq(1000)

    # --- Initialize Physics ---
    # We'll use slightly different physics for each channel for a rich effect
    r_osc = Oscillator(PHYSICS_PARAMS['mass'] * 1.0, PHYSICS_PARAMS['stiffness'] * 1.0, PHYSICS_PARAMS['damping'] * 1.0, 0)
    g_osc = Oscillator(PHYSICS_PARAMS['mass'] * 0.9, PHYSICS_PARAMS['stiffness'] * 0.8, PHYSICS_PARAMS['damping'] * 1.1, 0)
    b_osc = Oscillator(PHYSICS_PARAMS['mass'] * 1.1, PHYSICS_PARAMS['stiffness'] * 1.2, PHYSICS_PARAMS['damping'] * 0.9, 0)
    
    last_pluck_time = -5000
    last_time_us = utime.ticks_us()
    current_hue = 0.0
    
    # Set initial dim color
    rest_r, rest_g, rest_b = hsv_to_rgb(current_hue, 1.0, 0.1) # Start at dim red
    r_osc.rest_pos, g_osc.rest_pos, b_osc.rest_pos = rest_r, rest_g, rest_b
    
    while True:
        current_time_us = utime.ticks_us()
        dt = utime.ticks_diff(current_time_us, last_time_us) / 1_000_000.0
        last_time_us = current_time_us
        
        # --- 1. Check for Exit (Joystick Left) ---
        if joy_x.read_u16() < JOY_EXIT_THRESHOLD:
            print("Exiting Harmonic App...")
            set_led_color(pwm_pins, 0, 0, 0)
            # De-init PWM pins to free them up
            for pin in pwm_pins.values():
                pin.deinit()
            utime.sleep(0.5)
            return  # Exit the function

        # --- 2. Check for Pluck (Joystick Button) ---
        current_ms = utime.ticks_ms()
        if joy_button.value() == 1 and utime.ticks_diff(current_ms, last_pluck_time) > DEBOUNCE_MS:
            print(f"Pluck! at Hue: {current_hue:.2f}")
            last_pluck_time = current_ms
            r_osc.pluck(PLUCK_FORCE)
            g_osc.pluck(PLUCK_FORCE)
            b_osc.pluck(PLUCK_FORCE)
            
        # --- 3. Check for Hue Change (Joystick Y-Axis) ---
        y_val = joy_y.read_u16()
        # Check if outside the dead zone
        if y_val > (32768 + JOY_Y_DEAD_ZONE) or y_val < (32768 - JOY_Y_DEAD_ZONE):
            # Map Y value (0-65535) to hue (0.0-1.0)
            current_hue = y_val / 65535.0
            
            # Set the "rest" position to this new hue, but keep it dim (Value=0.1)
            # The "pos" will oscillate around this, but will settle back here.
            rest_r, rest_g, rest_b = hsv_to_rgb(current_hue, 1.0, 0.1)
            r_osc.rest_pos = rest_r
            g_osc.rest_pos = rest_g
            b_osc.rest_pos = rest_b
            
        # --- 4. Update Physics ---
        r_osc.update(dt)
        g_osc.update(dt)
        b_osc.update(dt)
        
        # --- 5. Update LED ---
        set_led_color(pwm_pins, r_osc.pos, g_osc.pos, b_osc.pos)
        
        utime.sleep_ms(5)

# --- Standalone Testing Block ---
# This code only runs if you run this file directly.
# It will be IGNORED if you import this file from another script.
if __name__ == "__main__":
    try:
        # Initialize hardware just for this test
        print("Running in standalone test mode...")
        joy_x_pin = machine.ADC(machine.Pin(JOY_X_PIN))
        joy_y_pin = machine.ADC(machine.Pin(JOY_Y_PIN))
        joy_button_pin = machine.Pin(JOY_BUTTON_PIN, machine.Pin.IN, machine.Pin.PULL_DOWN)
        
        # Run the app
        run_harmonic_app(joy_x_pin, joy_y_pin, joy_button_pin)
        
    except Exception as e:
        print(f"An error occurred: {e}")
        # Clean up on error
        set_led_color({
            'red': machine.PWM(machine.Pin(R_PIN)),
            'green': machine.PWM(machine.Pin(G_PIN)),
            'blue': machine.PWM(machine.Pin(B_PIN))
        }, 0, 0, 0)
