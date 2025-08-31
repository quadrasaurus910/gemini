import time
from machine import Pin, PWM

# Pin definitions for the RGB LED
# The RGB pins on the Pico are connected to GPIOs 24 (R), 22 (G), and 21 (B)
r_pin = Pin(24)
g_pin = Pin(22)
b_pin = Pin(21)

# Set up PWM for each color pin
# The frequency can be set to a value like 1000 Hz
pwm_r = PWM(r_pin)
pwm_g = PWM(g_pin)
pwm_b = PWM(b_pin)

pwm_r.freq(1000)
pwm_g.freq(1000)
pwm_b.freq(1000)

# Function to set RGB color using PWM duty cycles
def set_rgb(r, g, b):
    # The duty cycle must be between 0 and 65535
    pwm_r.duty_u16(int(r * 65535 / 255))
    pwm_g.duty_u16(int(g * 65535 / 255))
    pwm_b.duty_u16(int(b * 65535 / 255))

# Function to fade between two colors
def fade_color(start_color, end_color, steps=100, delay=0.01):
    for i in range(steps):
        r = int(start_color[0] + (end_color[0] - start_color[0]) * i / steps)
        g = int(start_color[1] + (end_color[1] - start_color[1]) * i / steps)
        b = int(start_color[2] + (end_color[2] - start_color[2]) * i / steps)
        set_rgb(r, g, b)
        time.sleep(delay)

# Main loop to run the color fade sequence
while True:
    # Fade from Red to Green
    fade_color((255, 0, 0), (0, 255, 0))
    
    # Fade from Green to Blue
    fade_color((0, 255, 0), (0, 0, 255))
    
    # Fade from Blue to Red
    fade_color((0, 0, 255), (255, 0, 0))
    
    # Short pause to make the loop more visible
    time.sleep(0.5)
