import utime
import math
import random
from machine import Pin, PWM, ADC, I2C # Added I2C
import gc

# To fix 'I2cLcd' not defined, we need to import it.
# This assumes pico_i2c_lcd.py is in the same directory or available.
try:
    from pico_i2c_lcd import I2cLcd 
except ImportError:
    # Define a dummy class if not available to prevent crashes
    class DummyLcd:
        def clear(self): pass
        def putstr(self, s): pass
        def move_to(self, col, row): pass
    I2cLcd = DummyLcd


# --- SETUP: RGB LED Pins (Common Anode) ---
PIN_R = 16
PIN_G = 17
PIN_B = 18

# --- JOYSTICK/EXIT Configuration ---
DEBOUNCE_DELAY_MS = 250
last_exit_time = 0
current_mode = 0 # 0: Plains, 1: Piedmont, 2: Mountains

led_r = PWM(Pin(PIN_R))
led_g = PWM(Pin(PIN_G))
led_b = PWM(Pin(PIN_B))

PWM_FREQ = 1000
led_r.freq(PWM_FREQ)
led_g.freq(PWM_FREQ)
led_b.freq(PWM_FREQ)

# --- LANDSCAPE RANDOMNESS CONFIG ---
# Random parameters for each run of a mode
MAX_TRAVERSAL_TIME = 2 * math.pi * 5.0 # Max 't' before mode change
# A new random value will be chosen from this range when entering a new mode.
RANDOM_TRAVERSAL_TIME_RANGE = (2 * math.pi * 2.5, 2 * math.pi * 5.5) 
INITIAL_HUE_OFFSET = 0.0 # Will be a random value between 0 and 2*pi
L_delta_random_factor = 1.0 # Will be a random value for mountain steepness

# --- HELPER FUNCTION FOR COMMON ANODE LEDS ---
def set_rgb(r, g, b):
    """
    Sets the color of a common anode RGB LED by inverting the values.
    """
    r_inverted = 255 - max(0, min(255, int(r)))
    g_inverted = 255 - max(0, min(255, int(g)))
    b_inverted = 255 - max(0, min(255, int(b)))
    
    led_r.duty_u16(int(r_inverted / 255 * 65535))
    led_g.duty_u16(int(g_inverted / 255 * 65535))
    led_b.duty_u16(int(b_inverted / 255 * 65535))

# --- COLOR MODEL CONVERSIONS (From oklab2.py) ---
# ... (rgb_to_xyz, xyz_to_oklab, oklab_to_xyz, xyz_to_rgb remain the same) ...
# Note: Functions are kept for completeness, but not reprinted.
def rgb_to_xyz(r, g, b):
    r /= 255.0; g /= 255.0; b /= 255.0
    if r > 0.04045: r = ((r + 0.055) / 1.055) ** 2.4
    else: r = r / 12.92
    if g > 0.04045: g = ((g + 0.055) / 1.055) ** 2.4
    else: g = g / 12.92
    if b > 0.04045: b = ((b + 0.055) / 1.055) ** 2.4
    else: b = b / 12.92
    r *= 100; g *= 100; b *= 100
    x = r * 0.4124 + g * 0.3576 + b * 0.1805
    y = r * 0.2126 + g * 0.7152 + b * 0.0722
    z = r * 0.0193 + g * 0.1192 + b * 0.9505
    return x, y, z

def xyz_to_oklab(x, y, z):
    l = 0.4122 * x + 0.5363 * y + 0.0514 * z
    m = 0.2119 * x + 0.6866 * y + 0.1015 * z
    s = 0.0883 * x + 0.2880 * y + 0.6237 * z
    l = l**(1/3); m = m**(1/3); s = s**(1/3)
    L = 0.2104 * l + 0.7955 * m - 0.0059 * s
    a = 1.9779 * l - 2.4285 * m + 0.4506 * s
    b = 0.0328 * l + 0.0763 * m - 0.1091 * s
    return L, a, b

def oklab_to_xyz(L, a, b):
    l = L + 0.3963 * a + 0.2158 * b
    m = L - 0.1055 * a - 0.0639 * b
    s = L - 0.0264 * a + 0.1239 * b
    l = l**3; m = m**3; s = s**3
    x = 1.9015 * l - 1.1974 * m + 0.2969 * s
    y = 0.9904 * l + 0.0198 * m - 0.0099 * s
    z = 0.0557 * l - 0.1056 * m + 1.0404 * s
    return x, y, z

def xyz_to_rgb(x, y, z):
    x /= 100.0; y /= 100.0; z /= 100.0
    r = x * 3.2406 + y * -1.5372 + z * -0.4986
    g = x * -0.9689 + y * 1.8758 + z * 0.0415
    b = x * 0.0557 + y * -0.2040 + z * 1.0570
    if r > 0.0031308: r = 1.055 * (r**(1/2.4)) - 0.055
    else: r = 12.92 * r
    if g > 0.0031308: g = 1.055 * (g**(1/2.4)) - 0.055
    else: g = 12.92 * g
    if b > 0.0031308: b = 1.055 * (b**(1/2.4)) - 0.055
    else: b = 12.92 * b
    return int(r * 255), int(g * 255), int(b * 255)

# --- EXIT LOGIC (From oklab2.py) ---
def check_exit(joy_x_pin):
    """Checks for a joystick left movement to exit a loop."""
    global last_exit_time
    current_time = utime.ticks_ms()
    x_value = joy_x_pin.read_u16()
    
    if x_value < 32768 - 10000:
        if utime.ticks_diff(current_time, last_exit_time) > DEBOUNCE_DELAY_MS:
            last_exit_time = current_time
            return True
            
    return False

# ----------------------------------------------------------------------
# --- LANDSCAPE TRAVERSAL FUNCTIONS (Simulating Partial Derivatives) ---
# ----------------------------------------------------------------------

def traverse_plains(t, L_start, L_delta):
    """
    Mode 0: Constant Luminosity (Plains) - Path perpendicular to the L gradient.
    Hue changes based on t + a random offset. Chroma has a subtle sine wave variation.
    """
    global INITIAL_HUE_OFFSET
    
    L = L_start # L remains constant
    # Slowly increase/decrease chroma (R) for a slight saturation change
    R = 0.10 + 0.05 * math.sin(t / (2 * math.pi * 5))
    # Hue (angle) cycles through all colors, offset by the random initial hue
    a = R * math.cos(t + INITIAL_HUE_OFFSET)
    b = R * math.sin(t + INITIAL_HUE_OFFSET)
    return L, a, b

def traverse_piedmont(t, L_start, L_delta):
    """
    Mode 1: Gradual Luminosity Change (Piedmont/Rolling Hills) - Small L Delta.
    L changes slowly and cycles up/down to simulate rolling hills.
    """
    global INITIAL_HUE_OFFSET
    
    # L changes slowly and cycles up/down. The frequency of the hills changes randomly.
    hill_freq_factor = 2.0 + 1.0 * math.sin(t / (2 * math.pi * 5)) # Subtle random-like hill frequency
    L = L_start + 0.10 * math.sin(t / (2 * math.pi * hill_freq_factor))
    # Keep chroma (R) moderate for a saturated look
    R = 0.15
    # Hue changes, offset by the random initial hue
    a = R * math.cos(t + INITIAL_HUE_OFFSET)
    b = R * math.sin(t + INITIAL_HUE_OFFSET)
    return L, a, b

def traverse_mountains(t, L_start, L_delta):
    """
    Mode 2: Steep Luminosity Change (Mountains) - Large L Delta.
    L changes steeply in a linear fashion, with randomized steepness.
    """
    global L_delta_random_factor, INITIAL_HUE_OFFSET
    
    # L changes steeply, steepness randomized by L_delta_random_factor
    L = L_start + (L_delta * L_delta_random_factor) * t
    # Keep a moderate chroma (R)
    R = 0.15
    # Hue changes, offset by the random initial hue
    a = R * math.cos(t + INITIAL_HUE_OFFSET)
    b = R * math.sin(t + INITIAL_HUE_OFFSET)
    return L, a, b

# ----------------------------------------------------------------------
# --- MAIN RUNNER FUNCTION ---
# ----------------------------------------------------------------------

def run_landscape_traversal(joy_x_pin):
    """
    Cycles through three distinct Oklab color landscape traversals.
    """
    global current_mode, MAX_TRAVERSAL_TIME, INITIAL_HUE_OFFSET, L_delta_random_factor
    
    LANDSCAPE_MODES = [
        ("PLAINS: L=CONST", 0.5, 0.0),      # L_start, L_delta (unused)
        ("PIEDMONT: L=SIN", 0.3, 0.0),      # L_start, L_delta (unused)
        ("MOUNTAINS: L=STEEP", 0.2, 0.005) # L_start, L_delta (base steepness)
    ]
    
    # Initialize the LCD object here
    lcd = None
    try:
        i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)
        # Check if the LCD address (0x27) is present
        if 0x27 in i2c.scan():
            lcd = I2cLcd(i2c, 0x27, 2, 16)
        else:
            print("LCD not found. Running without LCD.")
    except Exception as e:
        print(f"LCD Initialization Failed: {e}. Running without LCD.")

    set_rgb(0, 0, 0)
    utime.sleep(1)

    t = 0.0 # Time/angle parameter for traversal
    
    # --- Function to setup new mode parameters ---
    def setup_new_mode(current_mode):
        global MAX_TRAVERSAL_TIME, INITIAL_HUE_OFFSET, L_delta_random_factor
        
        # 1. Randomize the overall traversal time for non-mountain modes
        MAX_TRAVERSAL_TIME = random.uniform(*RANDOM_TRAVERSAL_TIME_RANGE)
        
        # 2. Randomize the initial hue offset (0 to 2*pi)
        INITIAL_HUE_OFFSET = random.uniform(0.0, 2 * math.pi)
        
        # 3. Randomize the steepness for the mountain mode
        if current_mode == 2:
            L_delta_random_factor = random.uniform(0.5, 2.0) # 50% to 200% of base steepness
        else:
            L_delta_random_factor = 1.0 # Reset for other modes
            
    # Initial setup
    setup_new_mode(current_mode)
    
    try:
        while True:
            mode_name, L_start, L_delta = LANDSCAPE_MODES[current_mode]
            
            # Display current mode on LCD
            if lcd:
                lcd.clear()
                # Use a cleaner display for the mountain steepness
                display_delta = L_delta * L_delta_random_factor if current_mode == 2 else 0.0
                lcd.putstr(mode_name)
                lcd.move_to(0, 1)
                lcd.putstr("L:{:.3f} dL:{:.4f}".format(L_start, display_delta))

            # Choose the correct traversal function
            if current_mode == 0:
                L, a, b = traverse_plains(t, L_start, L_delta)
            elif current_mode == 1:
                L, a, b = traverse_piedmont(t, L_start, L_delta)
            elif current_mode == 2:
                L, a, b = traverse_mountains(t, L_start, L_delta)
            
            # Clamp L value to valid Oklab range [0, 1]
            L = max(0.0, min(1.0, L))

            # Convert to RGB and set color
            x, y, z = oklab_to_xyz(L, a, b)
            r, g, b = xyz_to_rgb(x, y, z)
            set_rgb(r, g, b)
            
            # Advance time/angle
            t += 0.05
            
            # Check for wrap-around and mode change
            mode_change = False
            if current_mode == 2 and L >= 1.0:
                # Mountain mode ends when luminosity hits the top
                mode_change = True
            elif current_mode != 2 and t >= MAX_TRAVERSAL_TIME: 
                # Non-linear modes run for a randomized time
                mode_change = True
            
            if mode_change:
                t = 0.0
                current_mode = (current_mode + 1) % len(LANDSCAPE_MODES)
                setup_new_mode(current_mode) # Setup new random parameters for the next mode

            # Check for exit condition
            if check_exit(joy_x_pin):
                set_rgb(0, 0, 0)
                return

            utime.sleep_ms(10)
            gc.collect()

    except KeyboardInterrupt:
        print("Landscape traversal stopped.")
        pass

    finally:
        set_rgb(0, 0, 0)
