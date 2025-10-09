# oklab_landscapes4.py
# --- A dynamic terrain version with decoupled Lightness and Hue. ---
# This is a complete, self-contained script.

import utime
import math
import random
from machine import Pin, PWM, I2C, ADC
import gc

# It's good practice to handle potential import errors for the LCD
try:
    from pico_i2c_lcd import I2cLcd 
except ImportError:
    print("Warning: pico_i2c_lcd library not found. LCD will be disabled.")
    class I2cLcd: # Dummy class to prevent errors if the library is missing
        def __init__(self, *args, **kwargs): pass
        def clear(self): pass
        def putstr(self, s): pass
        def move_to(self, col, row): pass

# --- HARDWARE & CONFIGURATION ---
PIN_R, PIN_G, PIN_B = 16, 17, 18
DEBOUNCE_DELAY_MS = 250
PWM_FREQ = 1000

# --- COLOR MODEL CONVERSIONS ---
# These functions handle the math to convert between RGB and the Oklab color space.
def xyz_to_rgb(x, y, z):
    r = +3.2406 * x - 1.5372 * y - 0.4986 * z
    g = -0.9689 * x + 1.8758 * y + 0.0415 * z
    b = +0.0557 * x - 0.2040 * y + 1.0570 * z
    r = 1.055 * (r ** (1/2.4)) - 0.055 if r > 0.0031308 else 12.92 * r
    g = 1.055 * (g ** (1/2.4)) - 0.055 if g > 0.0031308 else 12.92 * g
    b = 1.055 * (b ** (1/2.4)) - 0.055 if b > 0.0031308 else 12.92 * b
    return int(r * 255), int(g * 255), int(b * 255)

def oklab_to_xyz(L, a, b):
    l = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3
    m = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3
    s = (L - 0.0894841775 * a - 1.2914855480 * b) ** 3
    x = +4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s
    y = -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s
    z = -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s
    return x / 100, y / 100, z / 100

class TerrainObject:
    """ Represents a single, dynamic elevation feature like a hill or peak. """
    def __init__(self, base_L, height_range, width_range_ticks):
        self.base_L = base_L
        
        # Randomize the specific properties of this terrain feature
        self.height = random.uniform(*height_range)
        self.width_ticks = random.randint(*width_range_ticks)
        
        # Internal state
        self.current_tick = 0
        self.progress = 0.0 # From 0.0 to 1.0

    def update(self):
        """ Advances the traversal over this terrain object. Returns False when complete. """
        self.current_tick += 1
        if self.current_tick >= self.width_ticks:
            return False # We have finished crossing this terrain
        
        self.progress = self.current_tick / self.width_ticks
        return True # Still traversing

    def get_elevation(self):
        """ Calculates the current L value based on progress across the terrain. """
        # We use a sine half-wave for a smooth hill shape.
        # This makes it rise from 0 to peak and back to 0 over the duration.
        elevation_offset = self.height * math.sin(self.progress * math.pi)
        return self.base_L + elevation_offset

class LandscapeTraversal:
    """ Manages the state and logic for traversing dynamic Oklab landscapes. """
    def __init__(self, joy_x_pin, lcd):
        self.joy_x_pin = joy_x_pin
        self.lcd = lcd
        self.last_exit_time = 0
        
        # --- LED Setup ---
        self.led_r = PWM(Pin(PIN_R)); self.led_r.freq(PWM_FREQ)
        self.led_g = PWM(Pin(PIN_G)); self.led_g.freq(PWM_FREQ)
        self.led_b = PWM(Pin(PIN_B)); self.led_b.freq(PWM_FREQ)

        # --- State Management ---
        self.hue_time = 0.0  # Separate timer for hue/chroma evolution
        self.current_mode = 0
        
        # --- Terrain Management ---
        self.current_terrain = None # Holds the active TerrainObject, if any
        self.time_until_next_terrain = 0 # Countdown in ticks
        
        # --- MODE CONFIGURATION ---
        # Defines the rules for generating terrain in each region.
        self.LANDSCAPE_MODES = [
            {
                "name": "PLAINS",
                "base_L": 0.6,
                "terrain_height": (0.05, 0.1),  # Small, gentle hills
                "terrain_width": (150, 400), # Ticks (1.5 to 4 seconds)
                "wait_time": (300, 800)      # Long waits between hills
            },
            {
                "name": "PIEDMONT",
                "base_L": 0.4,
                "terrain_height": (0.15, 0.3), # Medium, rolling hills
                "terrain_width": (200, 500),
                "wait_time": (50, 200)       # Shorter waits, more frequent hills
            },
            {
                "name": "MOUNTAINS",
                "base_L": 0.3, # Valleys are still bright
                "terrain_height": (0.4, 0.6),  # High peaks
                "terrain_width": (400, 800), # Wide mountains
                "wait_time": (0, 50)         # Almost no waiting, continuous peaks
            },
        ]
        self._setup_new_mode()

    def set_rgb(self, r, g, b):
        """ Sets the color of a common anode RGB LED by inverting values. """
        duty_r = int((255 - max(0, min(255, int(r)))) / 255 * 65535)
        duty_g = int((255 - max(0, min(255, int(g)))) / 255 * 65535)
        duty_b = int((255 - max(0, min(255, int(b)))) / 255 * 65535)
        self.led_r.duty_u16(duty_r)
        self.led_g.duty_u16(duty_g)
        self.led_b.duty_u16(duty_b)

    def check_exit(self):
        """ Checks for a joystick left movement to exit. """
        current_time = utime.ticks_ms()
        if self.joy_x_pin.read_u16() < 32768 - 10000:
            if utime.ticks_diff(current_time, self.last_exit_time) > DEBOUNCE_DELAY_MS:
                self.last_exit_time = current_time
                return True
        return False

    def _get_random_wait_time(self):
        """ Gets a random wait time based on the current mode's rules. """
        wait_range = self.LANDSCAPE_MODES[self.current_mode]["wait_time"]
        return random.randint(*wait_range)

    def _create_new_terrain(self):
        """ Creates a new TerrainObject based on the current mode's rules. """
        mode_rules = self.LANDSCAPE_MODES[self.current_mode]
        self.current_terrain = TerrainObject(
            base_L=mode_rules["base_L"],
            height_range=mode_rules["terrain_height"],
            width_range_ticks=mode_rules["terrain_width"]
        )
        self.update_display() # Update the display to show we've encountered a feature

    def _setup_new_mode(self):
        """ Resets timers and randomizes parameters for the new mode. """
        self.hue_time = 0.0
        self.current_terrain = None
        self.time_until_next_terrain = self._get_random_wait_time()
        # Randomize hue parameters separately
        self.initial_hue_offset = random.uniform(0.0, 2 * math.pi)
        self.hue_speed = random.uniform(0.8, 1.2)
        # Total time in a mode before switching
        self.mode_duration_ticks = random.randint(2000, 3000) # 20-30 seconds
        self.mode_progress_ticks = 0
        self.update_display()
        
    def update_display(self):
        """ Updates the LCD with the current mode status. """
        if not self.lcd: return
        mode = self.LANDSCAPE_MODES[self.current_mode]
        self.lcd.clear()
        
        status = mode['name']
        if self.current_terrain:
            status += ": Peak" # We are on a feature
        else:
            status += ": Valley" # We are on flat ground
        
        self.lcd.putstr(status)
        self.lcd.move_to(0, 1)
        
        # Show mode progress
        progress = self.mode_progress_ticks / self.mode_duration_ticks
        bar_len = int(progress * 16)
        self.lcd.putstr("[" + "#" * bar_len + "-" * (15 - bar_len) + "]")

    def run(self):
        """ The main loop for the dynamic landscape traversal. """
        self.set_rgb(0, 0, 0)
        utime.sleep(1)

        try:
            while True:
                # --- ELEVATION (L) LOGIC ---
                L = 0.0
                if self.current_terrain:
                    L = self.current_terrain.get_elevation()
                    # Update the terrain and check if it's finished
                    if not self.current_terrain.update():
                        self.current_terrain = None
                        self.time_until_next_terrain = self._get_random_wait_time()
                        self.update_display()
                else:
                    # We are on "flat ground" between features
                    L = self.LANDSCAPE_MODES[self.current_mode]["base_L"]
                    self.time_until_next_terrain -= 1
                    if self.time_until_next_terrain <= 0:
                        self._create_new_terrain()
                
                L = max(0.0, min(1.0, L)) # Clamp L to valid range

                # --- HUE/CHROMA (a, b) LOGIC (Completely Independent) ---
                R = 0.15 + 0.05 * math.sin(self.hue_time * 0.2) # Slowly evolving chroma
                effective_hue_time = self.hue_time * self.hue_speed
                a = R * math.cos(effective_hue_time + self.initial_hue_offset)
                b = R * math.sin(effective_hue_time + self.initial_hue_offset)
                self.hue_time += 0.05 # Always advance hue time

                # --- CONVERT AND SET COLOR ---
                x, y, z = oklab_to_xyz(L, a, b)
                r, g, b_ = xyz_to_rgb(x * 100, y * 100, z * 100)
                self.set_rgb(r, g, b_)

                # --- MODE CHANGE LOGIC ---
                self.mode_progress_ticks += 1
                if self.mode_progress_ticks >= self.mode_duration_ticks:
                    self.current_mode = (self.current_mode + 1) % len(self.LANDSCAPE_MODES)
                    self._setup_new_mode()

                # --- EXIT & SLEEP ---
                if self.check_exit():
                    self.set_rgb(0, 0, 0)
                    return
                
                utime.sleep_ms(10)
                gc.collect()

        finally:
            self.set_rgb(0, 0, 0) # Ensure LED is off on exit


# --- MAIN RUNNER FUNCTION ---
# This is the function you will call from your `lights_app.py` file.
# It handles initializing the hardware and starting the main loop.
def run_landscape_traversal(joy_x_pin):
    """
    Initializes the necessary hardware and starts the landscape traversal application.
    """
    lcd = None
    try:
        # Standard I2C pins for Pico: GP4 (SDA), GP5 (SCL)
        i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)
        # Standard address for 1602 LCD shields
        I2C_ADDR = 0x27 
        if I2C_ADDR in i2c.scan():
            lcd = I2cLcd(i2c, I2C_ADDR, 2, 16) # 2 rows, 16 columns
        else:
            print(f"LCD not found at address {hex(I2C_ADDR)}.")
    except Exception as e:
        print(f"LCD Initialization Failed: {e}.")

    # Create an instance of the class and run it
    traversal_app = LandscapeTraversal(joy_x_pin, lcd)
    traversal_app.run()

# --- FOR STANDALONE TESTING ---
# If you want to run this file by itself for testing, uncomment the following lines.
# Make sure to define the correct joystick pin.
# if __name__ == '__main__':
#     print("Running OKLab Landscape Traversal in standalone mode.")
#     print("Move joystick left to exit.")
#     JOY_X_PIN = 26 
#     joy_x_adc = ADC(Pin(JOY_X_PIN))
#     run_landscape_traversal(joy_x_adc)
#     print("Program finished.")

