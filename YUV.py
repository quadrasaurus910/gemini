import utime
from machine import Pin, PWM

# --- SETUP ---
# Adjust these pin numbers to match your RGB LED's connections.
# The Pico W has pins 0-2 for on-board LED. Pins 16, 17, 18 are good for external.
PIN_R = 16
PIN_G = 17
PIN_B = 18

led_r = PWM(Pin(PIN_R))
led_g = PWM(Pin(PIN_G))
led_b = PWM(Pin(PIN_B))

# Set the PWM frequency
PWM_FREQ = 1000
led_r.freq(PWM_FREQ)
led_g.freq(PWM_FREQ)
led_b.freq(PWM_FREQ)

# Helper function to set the LED color
def set_rgb(r, g, b):
    # Clamp values to the 0-255 range
    r = max(0, min(255, int(r)))
    g = max(0, min(255, int(g)))
    b = max(0, min(255, int(b)))
    
    # Set the PWM duty cycle (0-65535)
    led_r.duty_u16(int(r / 255 * 65535))
    led_g.duty_u16(int(g / 255 * 65535))
    led_b.duty_u16(int(b / 255 * 65535))

# --- COLOR SPACE CONVERSIONS (YUV) ---
# The YUV formulas are based on the BT.601 standard for standard definition video.
# Y = Luma (brightness), U = Chrominance (Blue - Luma), V = Chrominance (Red - Luma)

def rgb_to_yuv(r, g, b):
    """Converts 8-bit RGB to normalized YUV."""
    r_norm = r / 255.0
    g_norm = g / 255.0
    b_norm = b / 255.0

    y = 0.299 * r_norm + 0.587 * g_norm + 0.114 * b_norm
    u = -0.147 * r_norm - 0.289 * g_norm + 0.436 * b_norm
    v = 0.615 * r_norm - 0.515 * g_norm - 0.100 * b_norm

    return y, u, v

def yuv_to_rgb(y, u, v):
    """Converts normalized YUV to 8-bit RGB."""
    r_norm = y + 1.140 * v
    g_norm = y - 0.395 * u - 0.581 * v
    b_norm = y + 2.032 * u

    r = int(r_norm * 255)
    g = int(g_norm * 255)
    b = int(b_norm * 255)

    return (r, g, b)

# --- EFFECT FUNCTIONS ---

def luma_fade_effect(target_rgb=(255, 105, 180)):
    """
    Fades a color in and out by manipulating its Luma (Y) value.
    The hue and saturation remain constant.
    """
    print("Running Luma Fade Effect...")
    
    # Convert the target RGB color to YUV
    y_base, u_base, v_base = rgb_to_yuv(*target_rgb)
    
    # Fade in
    for i in range(101):
        y_current = i / 100.0  # Luma from 0 (black) to 1 (full brightness)
        r, g, b = yuv_to_rgb(y_current, u_base, v_base)
        set_rgb(r, g, b)
        utime.sleep_ms(10)
    
    # Fade out
    for i in range(100, -1, -1):
        y_current = i / 100.0
        r, g, b = yuv_to_rgb(y_current, u_base, v_base)
        set_rgb(r, g, b)
        utime.sleep_ms(10)

def chrominance_desaturation_effect(target_rgb=(0, 255, 255)):
    """
    Desaturates a color by scaling its chrominance (U, V) values to zero.
    The brightness (Y) remains constant.
    """
    print("Running Chrominance Desaturation Effect...")

    y_base, u_base, v_base = rgb_to_yuv(*target_rgb)

    # Transition from full color to grayscale
    for i in range(101):
        scale = 1 - (i / 100.0) # Scale from 1 to 0
        u_current = u_base * scale
        v_current = v_base * scale
        r, g, b = yuv_to_rgb(y_base, u_current, v_current)
        set_rgb(r, g, b)
        utime.sleep_ms(10)

    # Transition from grayscale back to full color
    for i in range(101):
        scale = i / 100.0
        u_current = u_base * scale
        v_current = v_base * scale
        r, g, b = yuv_to_rgb(y_base, u_current, v_current)
        set_rgb(r, g, b)
        utime.sleep_ms(10)

def grayscale_cycle_effect():
    """
    Cycles through every possible shade of gray. This is a pure Luma ramp.
    This demonstrates the simplest application of the Luma component.
    """
    print("Running Grayscale Cycle...")

    # Fade from black to white
    for i in range(256):
        set_rgb(i, i, i)
        utime.sleep_ms(5)

    # Fade from white to black
    for i in range(255, -1, -1):
        set_rgb(i, i, i)
        utime.sleep_ms(5)

# --- MAIN LOOP ---
# This loop runs the effects continuously.
while True:
    luma_fade_effect((255, 105, 180)) # Example: Pink
    utime.sleep(1) # Pause between effects

    chrominance_desaturation_effect((0, 255, 255)) # Example: Cyan
    utime.sleep(1)

    grayscale_cycle_effect()
    utime.sleep(1)
