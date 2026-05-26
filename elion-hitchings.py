from machine import Pin, PWM, ADC, I2C
import time
import urandom
from pico_i2c_lcd import I2cLcd 

# --- HARDWARE DEFINITIONS ---
PIN_R = 16
PIN_G = 17
PIN_B = 18

JOY_X = 26
JOY_Y = 27
JOY_SW = 22

I2C_SDA = 4
I2C_SCL = 5

# --- SYSTEM SETUP ---
# Initialize Joystick
joy_x = ADC(Pin(JOY_X))
joy_y = ADC(Pin(JOY_Y))
joy_btn = Pin(JOY_SW, Pin.IN, Pin.PULL_UP)

# Initialize I2C and LCD
i2c = I2C(0, sda=Pin(I2C_SDA), scl=Pin(I2C_SCL), freq=400000)
# Note: 0x27 is the most common I2C address, change to 0x3F if necessary
lcd = I2cLcd(i2c, 0x27, 2, 16)

# Custom Hexagonal Module Character (Homage to Elion-Hitchings)
hex_char = bytearray([
    0x00, #  
    0x0E, #  ***
    0x11, # *   *
    0x11, # *   *
    0x11, # *   *
    0x0E, #  ***
    0x00, #  
    0x00
])
lcd.custom_char(0, hex_char)

# --- THE ROUGE RADICAL PATTERN CLASS ---
class RougeChannel:
    def __init__(self, pin_num, name):
        self.pwm = PWM(Pin(pin_num))
        self.pwm.freq(1000)
        self.name = name
        
        # State variables
        self.current_val = urandom.randint(0, 65535)
        self.target_val = urandom.randint(0, 65535)
        
        # Non-blocking timing variables
        self.last_update = time.ticks_ms()
        # The 22.5 degree angle translated into a base timing offset
        self.update_interval = urandom.randint(10, 225) 
        self.step = 500

    def update(self, current_time, brutalism_factor):
        # Micro-loop timing independent of the main loop
        if time.ticks_diff(current_time, self.last_update) >= self.update_interval:
            self.last_update = current_time

            # Eccentrically load the step speed based on the joystick
            adjusted_step = int(self.step * brutalism_factor)

            # Transition toward the target value
            if self.current_val < self.target_val:
                self.current_val += adjusted_step
                if self.current_val > self.target_val: self.current_val = self.target_val
            elif self.current_val > self.target_val:
                self.current_val -= adjusted_step
                if self.current_val < self.target_val: self.current_val = self.target_val

            # Split-Mix Trigger: If target is reached, generate a new randomized state
            if self.current_val == self.target_val:
                self.target_val = urandom.randint(0, 65535)
                # Randomize the length of the next micro-loop
                self.update_interval = urandom.randint(5, max(10, int(225 / brutalism_factor)))

            # Apply to Common Anode (invert the logic: 0 = high/off, 65535 = low/on)
            self.pwm.duty_u16(65535 - int(self.current_val))

# --- INITIALIZE CHANNELS ---
# These are the individual "pools" in our split-mix synthesis
red_pool = RougeChannel(PIN_R, "R")
green_pool = RougeChannel(PIN_G, "G")
blue_pool = RougeChannel(PIN_B, "B")

def main():
    lcd.clear()
    lcd.putstr(chr(0) + " Split-Mix " + chr(0))
    lcd.move_to(0, 1)
    lcd.putstr("Synthesis Active")
    
    last_lcd_update = time.ticks_ms()
    
    while True:
        current_time = time.ticks_ms()
        
        # --- THE MAIN LOOP (The Structural S-Configuration) ---
        # Use joystick X-axis to dictate the "Brutalism Factor" (volatility of the transitions)
        # ADC reads 0 to 65535. Center is ~32768.
        x_val = joy_x.read_u16()
        
        # Calculate a multiplier between 0.5 (slow/smooth) and 5.0 (harsh/brutal)
        brutalism_factor = 0.5 + (x_val / 65535.0) * 4.5
        
        # --- THE MICRO-LOOPS (The Rouge Radical Patterns) ---
        # Each channel evaluates its own non-blocking timer independently
        red_pool.update(current_time, brutalism_factor)
        green_pool.update(current_time, brutalism_factor)
        blue_pool.update(current_time, brutalism_factor)
        
        # Update LCD with current state periodically (every 500ms) without blocking LED loops
        if time.ticks_diff(current_time, last_lcd_update) > 500:
            lcd.move_to(0, 1)
            # Display the "terraced floors" of the current RGB output targets
            lcd.putstr(f"R{red_pool.target_val//1000:02d} G{green_pool.target_val//1000:02d} B{blue_pool.target_val//1000:02d} ")
            last_lcd_update = current_time

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        # Cleanup on exit
        red_pool.pwm.duty_u16(65535)
        green_pool.pwm.duty_u16(65535)
        blue_pool.pwm.duty_u16(65535)
        lcd.clear()
        lcd.putstr("Synthesis Halted")
