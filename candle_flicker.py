# Standalone script for a realistic common-anode RGB LED candle flicker effect.

from machine import Pin, PWM, I2C
import utime
import urandom
import gc

# --- 1. HARDWARE CONFIGURATION (Adjust Pins) ---
# NOTE: The Pico has a 16-bit PWM system (0 to 65535).
# For a COMMON ANODE LED: 0 = Full Brightness, 65535 = OFF.

# Replace these pins with the actual GPIO pins your RGB LED is connected to.
RED_PIN = 16
GREEN_PIN = 17
BLUE_PIN = 18

# I2C Configuration for the LCD (Used only to turn off the backlight)
I2C_ADDR = 0x27
I2C_SDA_PIN = 4
I2C_SCL_PIN = 5

# --- 2. CANDLE COLOR RANGES (Common Anode Duty Cycle) ---

# Candle flicker is primarily deep/medium orange (High Red, Medium Green, Low Blue)
# Duty Cycle (0=Bright, 65535=Dim)

# RED: Brightest (low duty cycle) for the core orange/red flame.
R_MIN = 0
R_MAX = 15000

# GREEN: Medium Brightness for the orange/yellow mix.
G_MIN = 15000
G_MAX = 40000

# BLUE: Very dim/off for the slight hint of whiter tone in the flame tips.
B_MIN = 50000
B_MAX = 65535

# TIME: Random delay for a natural flicker (in milliseconds)
TIME_MIN_MS = 10
TIME_MAX_MS = 50 
PWM_FREQUENCY = 1000 # Set a high frequency for smooth color changes

# --- 3. HELPER FUNCTIONS ---

def init_pwm(pin_num):
    """Initializes and returns a PWM object for the given pin."""
    pwm = PWM(Pin(pin_num))
    pwm.freq(PWM_FREQUENCY)
    return pwm

def set_rgb_color_u16(r_pwm, g_pwm, b_pwm, r_val, g_val, b_val):
    """Sets the common-anode RGB LED color using 16-bit duty cycles."""
    r_pwm.duty_u16(r_val)
    g_pwm.duty_u16(g_val)
    b_pwm.duty_u16(b_val)

def disable_lcd_backlight():
    """Initializes I2C and attempts to turn off the LCD backlight."""
    try:
        # Import the library inside the function to keep the main code cleaner
        from pico_i2c_lcd import I2cLcd
        
        # Initialize I2C bus using configuration from mainTest2.py
        i2c = I2C(0, sda=Pin(I2C_SDA_PIN), scl=Pin(I2C_SCL_PIN), freq=400000)
        devices = i2c.scan()

        if I2C_ADDR in devices:
            lcd = I2cLcd(i2c, I2C_ADDR, 2, 16)
            # This is the command to turn off the backlight
            lcd.backlight_off() 
            gc.collect() # Clean up memory after using the LCD object
            return True
        else:
            print("LCD not found. Skipping backlight disable.")
            return False
    except ImportError:
        print("Warning: pico_i2c_lcd library not found. Cannot turn off backlight.")
        return False
    except Exception as e:
        print(f"Error initializing LCD for backlight control: {e}")
        return False

# --- 4. MAIN CANDLE EFFECT LOOP ---

def run_candle_flicker():
    """Initializes hardware and runs the candle flicker loop."""
    
    # Initialize PWM outputs
    r_pwm = init_pwm(RED_PIN)
    g_pwm = init_pwm(GREEN_PIN)
    b_pwm = init_pwm(BLUE_PIN)

    print("RGB PWM initialized. Starting candle flicker...")
    
    # Randomly seed the generator for more unpredictable flicker
    try:
        urandom.seed(utime.ticks_us())
    except:
        # If urandom.seed() is not available, just proceed
        pass

    try:
        while True:
            # Generate random duty cycles within the flame color ranges
            r_val = urandom.randint(R_MIN, R_MAX)
            g_val = urandom.randint(G_MIN, G_MAX)
            b_val = urandom.randint(B_MIN, B_MAX)
            
            # Set the new color
            set_rgb_color_u16(r_pwm, g_pwm, b_pwm, r_val, g_val, b_val)
            
            # Random delay for the flicker rate
            utime.sleep_ms(urandom.randint(TIME_MIN_MS, TIME_MAX_MS))
            
            gc.collect() # Perform garbage collection periodically
            
    except KeyboardInterrupt:
        print("Candle flicker stopped.")
    finally:
        # Turn off the LED when the script exits
        set_rgb_color_u16(r_pwm, g_pwm, b_pwm, 65535, 65535, 65535)
        # Deinitialize PWM
        r_pwm.deinit()
        g_pwm.deinit()
        b_pwm.deinit()

# --- 5. APPLICATION ENTRY POINT ---

if __name__ == "__main__":
    # 1. Disable LCD Backlight
    disable_lcd_backlight()
    
    # 2. Run the candle effect
    run_candle_flicker()
