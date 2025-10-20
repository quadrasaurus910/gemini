# harmonic_led.py
# A standalone MicroPython script that simulates a damped harmonic
# oscillator for each RGB channel of a common anode LED.
#
# This demonstrates concepts from Newton's 2nd Law, Hooke's Law,
# and SHM, solved numerically using Euler integration.

import machine
import utime
import math

# --- HARDWARE SETUP ---
# RGB LED (Common Anode)
R_PIN = 13  # GPIO pin for Red
G_PIN = 14  # GPIO pin for Green
B_PIN = 15  # GPIO pin for Blue

# Joystick
JOY_BUTTON_PIN = 22  # GPIO pin for joystick button
JOY_X_PIN = 26       # ADC pin for joystick X-axis (for exiting)

# --- CONFIGURATION (Tune These!) ---
# Physics Parameters
# Stiffness (k): Higher = faster oscillation (like a guitar string)
# Mass (m): Higher = slower oscillation (like a bowling ball)
# Damping (c): Higher = faster decay (like a shock absorber)
#  - c = 0.0: No damping, oscillates forever
#  - c = 0.5: Underdamped, bounces for a while (Bouncy Spring 🤸)
#  - c = 2.0: Critically damped, returns fast with no bounce (Heavy Door 🚪)
#  - c = 5.0: Overdamped, returns very slowly

R_PHYSICS = {'mass': 1.0, 'stiffness': 50.0, 'damping': 0.4}
G_PHYSICS = {'mass': 1.0, 'stiffness': 40.0, 'damping': 0.6}
B_PHYSICS = {'mass': 1.0, 'stiffness': 60.0, 'damping': 0.5}

# Color "Rest" State (0-255)
# This is the "home" color the springs will settle back to.
# Try (0, 0, 0) for "off" or (20, 50, 180) for a "blue family" effect.
REST_R = 20
REST_G = 50
REST_B = 180

# Pluck Force
# How hard to "hit" the springs when the button is pressed
PLUCK_FORCE = 500.0

# Joystick Settings
JOY_EXIT_THRESHOLD = 10000  # Value for "joystick left"
DEBOUNCE_MS = 200            # Debounce for button press

# --- HARDWARE INITIALIZATION ---
red = machine.PWM(machine.Pin(R_PIN))
green = machine.PWM(machine.Pin(G_PIN))
blue = machine.PWM(machine.Pin(B_PIN))
red.freq(1000)
green.freq(1000)
blue.freq(1000)

joy_button = machine.Pin(JOY_BUTTON_PIN, machine.Pin.IN, machine.Pin.PULL_DOWN)
joy_x = machine.ADC(machine.Pin(JOY_X_PIN))

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

def map_value(x, in_min, in_max, out_min, out_max):
    """Maps a value from one range to another (like Arduino's map())."""
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

# --- PHYSICS CLASS ---

class Oscillator:
    """Simulates a single 1D damped harmonic oscillator."""
    def __init__(self, mass, stiffness, damping, rest_position):
        self.mass = mass
        self.k = stiffness  # Spring stiffness (Hooke's Law)
        self.c = damping    # Damping coefficient
        
        self.rest_pos = rest_position  # The "home" position
        self.pos = rest_position       # Current position
        self.vel = 0.0                 # Current velocity
        self.accel = 0.0               # Current acceleration

    def update(self, dt):
        """Update the oscillator's state using Euler integration."""
        # Calculate spring force (F = -kx) based on displacement from rest
        force_spring = -self.k * (self.pos - self.rest_pos)
        
        # Calculate damping force (F = -cv)
        force_damping = -self.c * self.vel
        
        # Calculate total force
        total_force = force_spring + force_damping
        
        # Calculate acceleration (Newton's 2nd Law: a = F/m)
        self.accel = total_force / self.mass
        
        # Integrate acceleration to get new velocity
        self.vel += self.accel * dt
        
        # Integrate velocity to get new position
        self.pos += self.vel * dt
        
    def pluck(self, force):
        """Applies an instantaneous force, changing the velocity."""
        # F = m*a => a = F/m.  v = a*t.
        # We simulate this by just "kicking" the velocity.
        self.vel += force / self.mass

# --- MAIN APPLICATION ---

def main():
    """Main application loop."""
    
    print("Harmonic LED script running...")
    print("Press joystick button to 'pluck' the springs.")
    print("Push joystick left to exit.")

    # Convert 0-255 rest color to our physics "position" (e.g., 0-1 range)
    # We'll map our physics space (e.g., -1.0 to 2.0) back to 0-255 later.
    # For simplicity, let's just use 0-255 as our physics "position" unit.
    r_osc = Oscillator(R_PHYSICS['mass'], R_PHYSICS['stiffness'], R_PHYSICS['damping'], REST_R)
    g_osc = Oscillator(G_PHYSICS['mass'], G_PHYSICS['stiffness'], G_PHYSICS['damping'], REST_G)
    b_osc = Oscillator(B_PHYSICS['mass'], B_PHYSICS['stiffness'], B_PHYSICS['damping'], REST_B)
    
    last_pluck_time = 0
    last_time_ns = utime.ticks_ns()

    while True:
        # --- Calculate Delta Time (dt) ---
        # This is crucial for a stable physics simulation!
        current_time_ns = utime.ticks_ns()
        dt = utime.ticks_diff(current_time_ns, last_time_ns) / 1_000_000_000.0  # Convert ns to s
        last_time_ns = current_time_ns

        # --- Check for Exit (Joystick Left) ---
        if joy_x.read_u16() < JOY_EXIT_THRESHOLD:
            print("Exiting...")
            set_led_color(0, 0, 0) # Turn off LED before exiting
            utime.sleep(0.5)
            return  # This breaks the loop and will exit the script

        # --- Check for Pluck (Joystick Button) ---
        current_ms = utime.ticks_ms()
        if joy_button.value() == 1 and utime.ticks_diff(current_ms, last_pluck_time) > DEBOUNCE_MS:
            print("Pluck!")
            last_pluck_time = current_ms
            r_osc.pluck(PLUCK_FORCE)
            g_osc.pluck(PLUCK_FORCE * 0.8) # Pluck channels by different amounts
            b_osc.pluck(PLUCK_FORCE * 1.2) # for more interesting effects
            
        # --- Update Physics ---
        r_osc.update(dt)
        g_osc.update(dt)
        b_osc.update(dt)
        
        # --- Update LED ---
        # The 'pos' is our raw physics position. We can use it directly
        # as the 0-255 brightness value. set_led_color will clamp it.
        set_led_color(r_osc.pos, g_osc.pos, b_osc.pos)
        
        # Short sleep to prevent the loop from hogging the CPU
        utime.sleep_ms(5)

# Run the main function
if __name__ == "__main__":
    main()
