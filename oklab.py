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

# --- Oklab to RGB Conversion Functions ---
def oklab_to_rgb(L, a, b):
    """
    Converts Oklab to sRGB. This is the core of the gradient logic.
    """
    # Step 1: Oklab to L'a'b' (CIELAB-like space)
    l_prime = L + 0.3963377774 * a + 0.2158037573 * b
    m_prime = L - 0.1055613423 * a - 0.0638541728 * b
    s_prime = L - 0.0894841775 * a - 1.2914855480 * b

    # Step 2: Invert the power function to get linear color components
    def linear_from_prime(x):
        return x**3 if x > 0.0 else 0.0

    l = linear_from_prime(l_prime)
    m = linear_from_prime(m_prime)
    s = linear_from_prime(s_prime)

    # Step 3: Convert L'M'S' to Linear RGB
    r_linear = 4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s
    g_linear = -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s
    b_linear = -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s
    
    # Step 4: Apply inverse sRGB gamma correction to get 8-bit values
    def srgb_from_linear(c):
        c = max(0, min(1, c)) # Clamp values
        return (1.055 * c**(1.0/2.4) - 0.055) if c > 0.0031308 else c * 12.92
    
    r = int(srgb_from_linear(r_linear) * 255)
    g = int(srgb_from_linear(g_linear) * 255)
    b = int(srgb_from_linear(b_linear) * 255)

    return (r, g, b)

# --- Helper function to generate a random Oklab color ---
def get_random_oklab_color():
    """
    Generates a random Oklab color within a reasonable,
    visible range.
    L: Lightness (0.0 to 1.0)
    a: Green-Red axis (-0.1 to 0.2)
    b: Blue-Yellow axis (-0.2 to 0.2)
    """
    l = random.uniform(0.3, 0.8)  # Mid-range brightness for good visibility
    a = random.uniform(-0.1, 0.2)  # A reasonable range for 'a'
    b = random.uniform(-0.2, 0.2)  # A reasonable range for 'b'
    return (l, a, b)

# --- Main function to run a single random gradient ---
def show_random_oklab_gradient(steps=100, delay_ms=20):
    """
    Generates a random Oklab gradient and displays it.
    """
    start_oklab = get_random_oklab_color()
    end_oklab = get_random_oklab_color()
    
    print(f"Starting gradient from Oklab {start_oklab} to {end_oklab}")

    # Calculate step size for each component
    step_L = (end_oklab[0] - start_oklab[0]) / steps
    step_a = (end_oklab[1] - start_oklab[1]) / steps
    step_b = (end_oklab[2] - start_oklab[2]) / steps

    for i in range(steps + 1):
        # Linearly interpolate in Oklab space
        current_L = start_oklab[0] + step_L * i
        current_a = start_oklab[1] + step_a * i
        current_b = start_oklab[2] + step_b * i

        # Convert to RGB and update LED
        r, g, b = oklab_to_rgb(current_L, current_a, current_b)
        set_rgb(r, g, b)
        utime.sleep_ms(delay_ms)
    
    utime.sleep(1) # Pause before the next gradient

# --- MAIN PROGRAM LOOP ---
while True:
    show_random_oklab_gradient()
