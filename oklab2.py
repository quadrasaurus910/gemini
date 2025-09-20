import utime
import math
import random
from machine import Pin, PWM

# --- SETUP: Adjust these pin numbers to match your RGB LED's connections. ---
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

# --- COLOR SPACE CONVERSION FUNCTIONS ---
# Oklab to RGB is the same as the previous example
def oklab_to_rgb(L, a, b):
    l_prime = L + 0.3963377774 * a + 0.2158037573 * b
    m_prime = L - 0.1055613423 * a - 0.0638541728 * b
    s_prime = L - 0.0894841775 * a - 1.2914855480 * b

    def linear_from_prime(x):
        return x**3 if x > 0.0 else 0.0
    l = linear_from_prime(l_prime)
    m = linear_from_prime(m_prime)
    s = linear_from_prime(s_prime)

    r_linear = 4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s
    g_linear = -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s
    b_linear = -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s
    
    def srgb_from_linear(c):
        c = max(0, min(1, c))
        return (1.055 * c**(1.0/2.4) - 0.055) if c > 0.0031308 else c * 12.92
    
    r = int(srgb_from_linear(r_linear) * 255)
    g = int(srgb_from_linear(g_linear) * 255)
    b = int(srgb_from_linear(b_linear) * 255)
    return (r, g, b)

# New function: RGB to Oklab
def rgb_to_oklab(r, g, b):
    # Step 1: sRGB to linear RGB
    def linear_from_srgb(c):
        c_norm = c / 255.0
        return c_norm / 12.92 if c_norm <= 0.04045 else ((c_norm + 0.055) / 1.055)**2.4
    r_linear = linear_from_srgb(r)
    g_linear = linear_from_srgb(g)
    b_linear = linear_from_srgb(b)

    # Step 2: Linear RGB to L'M'S'
    l = 0.4121656120 * r_linear + 0.5363325264 * g_linear + 0.0515018616 * b_linear
    m = 0.2118591036 * r_linear + 0.6807189584 * g_linear + 0.1074219380 * b_linear
    s = 0.0883094610 * r_linear + 0.2818474174 * g_linear + 0.6298431216 * b_linear

    # Step 3: Cube root to get L_prime, m_prime, s_prime
    def prime_from_linear(x):
        return x**(1/3) if x > 0.0031308 else x * 7.787 + 16/116
    l_prime = prime_from_linear(l)
    m_prime = prime_from_linear(m)
    s_prime = prime_from_linear(s)
    
    # Step 4: L'M'S' to Oklab
    L_ok = 0.2104542553 * l_prime + 0.7936177850 * m_prime - 0.0040720468 * s_prime
    a_ok = 1.9779984950 * l_prime - 2.4285922055 * m_prime + 0.4505937105 * s_prime
    b_ok = 0.0259040371 * l_prime + 0.7827717662 * m_prime - 0.8086757983 * s_prime

    return (L_ok, a_ok, b_ok)

# --- Helper function for random, vibrant RGB colors ---
def get_random_saturated_rgb():
    """
    Generates a random RGB color that is guaranteed to be on the edge of the color cube.
    """
    options = [0, 255]
    r = random.choice(options)
    g = random.choice(options)
    b = random.choice(options)

    # Make sure at least one channel is a variable value to avoid black/white
    if sum((r, g, b)) == 0 or sum((r,g,b)) == 765:
        r = random.choice([0, 255])
        g = random.choice([0, 255])
        b = random.randint(0, 255)
    else:
        # One channel is 255, one is 0, one is random
        choices = [
            (255, 0, random.randint(0, 255)),
            (255, random.randint(0, 255), 0),
            (0, 255, random.randint(0, 255)),
            (random.randint(0, 255), 255, 0),
            (0, random.randint(0, 255), 255),
            (random.randint(0, 255), 0, 255),
        ]
        return random.choice(choices)
    
    return (r, g, b)

# --- MAIN GRADIENT LOOP ---
def run_continuous_gradients(steps=100, delay_ms=10):
    """
    Creates a continuous chain of random, vibrant gradients.
    """
    current_rgb = (0, 0, 0)
    set_rgb(*current_rgb)
    utime.sleep(1)
    
    while True:
        # The end of the previous path is the start of the new one
        start_rgb = current_rgb
        
        # Get a new random, saturated color for the end of the path
        end_rgb = get_random_saturated_rgb()
        
        # Convert start and end points to Oklab
        start_oklab = rgb_to_oklab(*start_rgb)
        end_oklab = rgb_to_oklab(*end_rgb)
        
        # Calculate step size for each Oklab component
        step_L = (end_oklab[0] - start_oklab[0]) / steps
        step_a = (end_oklab[1] - start_oklab[1]) / steps
        step_b = (end_oklab[2] - start_oklab[2]) / steps
        
        print(f"Gradient: from {start_rgb} to {end_rgb}")

        for i in range(steps + 1):
            # Linearly interpolate in Oklab space
            current_L = start_oklab[0] + step_L * i
            current_a = start_oklab[1] + step_a * i
            current_b = start_oklab[2] + step_b * i

            # Convert to RGB and display
            r, g, b = oklab_to_rgb(current_L, current_a, current_b)
            set_rgb(r, g, b)
            utime.sleep_ms(delay_ms)
            
        # Update the current color for the next loop
        current_rgb = end_rgb

# --- RUN THE PROGRAM ---
if __name__ == "__main__":
    run_continuous_gradients()
