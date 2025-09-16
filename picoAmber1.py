import utime
from machine import Pin, PWM

# --- SETUP ---
# Adjust these pin numbers to match your RGB LED's connections.
PIN_R = 16
PIN_G = 17
PIN_B = 18

led_r = PWM(Pin(PIN_R))
led_g = PWM(Pin(PIN_G))
led_b = PWM(Pin(PIN_B))

PWM_FREQ = 1000
led_r.freq(PWM_FREQ)
led_g.freq(PWM_FREQ)
led_b.freq(PWM_FREQ)

# Helper function to set the LED color
def set_rgb(r, g, b):
    r = max(0, min(255, int(r)))
    g = max(0, min(255, int(g)))
    b = max(0, min(255, int(b)))
    
    led_r.duty_u16(int((255 - r) / 255 * 65535))
    led_g.duty_u16(int((255 - g) / 255 * 65535))
    led_b.duty_u16(int((255 - b) / 255 * 65535))

# --- MAIN LOOP ---
def display_amber_colors_direct_loop():
    """
    Directly loops through RGB values to show a variety of amber colors.
    """
    print("Beginning direct RGB loop to display amber colors...")

    # Iterate through high Red and Green values and low Blue values
    # This range is empirically chosen to produce amber colors
    for r in range(200, 256, 10):
        for g in range(150, 256, 10):
            for b in range(0, 51, 10):
                set_rgb(r, g, b)
                print(f"Displaying RGB({r}, {g}, {b})")
                utime.sleep_ms(50)
                
    print("Loop finished.")
    set_rgb(0, 0, 0) # Turn LED off

while True:
    display_amber_colors_direct_loop()
    utime.sleep(2)
