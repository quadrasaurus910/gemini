# The following script demonstrates a wide range of color models by
# cycling through their full color spectrum and converting the
# values to RGB to drive a connected RGB LED.

# --- Hardware Setup ---
# Connect the RGB LED's Red pin to a GPIO pin (e.g., GP0).
# Connect the Green pin to another GPIO pin (e.g., GP1).
# Connect the Blue pin to a third GPIO pin (e.g., GP2).
# Connect the common cathode (long pin) to a GND pin on the Pico.
# Remember to use current-limiting resistors for each LED pin (e.g., 220 Ohm).

from machine import Pin, PWM
import time
import math

# Define the pins for the Red, Green, and Blue LEDs.
# These pins must support PWM. GP0, GP1, GP2 are excellent choices.
RED_PIN = 16
GREEN_PIN = 17
BLUE_PIN = 18

# Set up the PWM objects for each color channel.
# PWM frequency is set to 1000 Hz, which is a good default.
pwm_r = PWM(Pin(RED_PIN))
pwm_g = PWM(Pin(GREEN_PIN))
pwm_b = PWM(Pin(BLUE_PIN))
pwm_r.freq(1000)
pwm_g.freq(1000)
pwm_b.freq(1000)

def set_rgb_color(r, g, b):
    """
    Sets the RGB LED color using 8-bit values (0-255).
    The MicroPython PWM duty cycle is 16-bit (0-65535), so we scale the values.
    """
    # Scale 8-bit (0-255) to 16-bit (0-65535) for PWM.
    # We multiply by 257 because 255 * 257 = 65535, which provides a nice scaling.
    pwm_r.duty_u16(r * 257)
    pwm_g.duty_u16(g * 257)
    pwm_b.duty_u16(b * 257)

# --- Color Conversion Functions ---

def hsv_to_rgb(h, s, v):
    """
    Converts a color from the HSV model to the RGB model.
    h: Hue (0-1), s: Saturation (0-1), v: Value (0-1)
    """
    if s == 0.0:
        return int(v * 255), int(v * 255), int(v * 255)
    
    i = math.floor(h * 6.0)
    f = h * 6.0 - i
    
    p = v * (1.0 - s)
    q = v * (1.0 - f * s)
    t = v * (1.0 - (1.0 - f) * s)
    
    i = int(i) % 6
    
    if i == 0:
        r, g, b = v, t, p
    elif i == 1:
        r, g, b = q, v, p
    elif i == 2:
        r, g, b = p, v, t
    elif i == 3:
        r, g, b = p, q, v
    elif i == 4:
        r, g, b = t, p, v
    elif i == 5:
        r, g, b = v, p, q
        
    return int(r * 255), int(g * 255), int(b * 255)

def hsl_to_rgb(h, s, l):
    """
    Converts a color from the HSL model to the RGB model.
    h: Hue (0-1), s: Saturation (0-1), l: Lightness (0-1)
    """
    def hue_to_rgb(p, q, t):
        if t < 0: t += 1
        if t > 1: t -= 1
        if t < 1/6: return p + (q - p) * 6 * t
        if t < 1/2: return q
        if t < 2/3: return p + (q - p) * (2/3 - t) * 6
        return p

    if s == 0:
        return int(l * 255), int(l * 255), int(l * 255)

    q = l * (1 + s) if l < 0.5 else l + s - l * s
    p = 2 * l - q
    
    r = hue_to_rgb(p, q, h + 1/3)
    g = hue_to_rgb(p, q, h)
    b = hue_to_rgb(p, q, h - 1/3)

    return int(r * 255), int(g * 255), int(b * 255)

def cmy_to_rgb(c, m, y):
    """
    Converts a CMY color (0-1) to RGB (0-255).
    """
    r = (1 - c) * 255
    g = (1 - m) * 255
    b = (1 - y) * 255
    return int(r), int(g), int(b)

def cmyk_to_rgb(c, m, y, k):
    """
    Converts a CMYK color (0-1) to RGB (0-255).
    """
    r = (1 - c) * (1 - k)
    g = (1 - m) * (1 - k)
    b = (1 - y) * (1 - k)
    return int(r * 255), int(g * 255), int(b * 255)

def xyz_to_rgb(x, y, z):
    """
    Converts XYZ color space values to sRGB.
    This is a linear transformation.
    Values are expected to be between 0 and 1.
    """
    # Inverse of the sRGB matrix (standard D65 illuminant).
    # This matrix is used to convert from XYZ to linear RGB.
    r = 3.2406 * x - 1.5372 * y - 0.4986 * z
    g = -0.9689 * x + 1.8758 * y + 0.0415 * z
    b = 0.0557 * x - 0.2040 * y + 1.0570 * z

    # Apply a gamma correction for sRGB, clamping values between 0 and 1.
    r = max(0, min(1, r))
    g = max(0, min(1, g))
    b = max(0, min(1, b))
    
    # Gamma correction
    r = r * 12.92 if r <= 0.0031308 else 1.055 * math.pow(r, 1/2.4) - 0.055
    g = g * 12.92 if g <= 0.0031308 else 1.055 * math.pow(g, 1/2.4) - 0.055
    b = b * 12.92 if b <= 0.0031308 else 1.055 * math.pow(b, 1/2.4) - 0.055
    
    return int(r * 255), int(g * 255), int(b * 255)

def cielab_to_rgb(l, a, b):
    """
    Converts CIELAB values to RGB.
    First converts CIELAB to XYZ, then XYZ to RGB.
    L: 0-100, a: -128-127, b: -128-127
    """
    # Reference white point (D65)
    xn, yn, zn = 0.95047, 1.0, 1.08883
    
    fy = (l + 16) / 116.0
    fx = a / 500.0 + fy
    fz = fy - b / 200.0
    
    # Calculate X, Y, Z from f(x), f(y), f(z)
    def f_inv(t):
        if t > 0.20689655: # (6/29)
            return t**3
        else:
            return 3 * (t**2) * 0.20689655 # Approximation of the linear part
    
    x = xn * f_inv(fx)
    y = yn * f_inv(fy)
    z = zn * f_inv(fz)

    return xyz_to_rgb(x, y, z)

def ryb_to_rgb(r, y, b):
    """
    A simplified conversion from RYB (Red, Yellow, Blue) to RGB.
    This model is conceptual and often used in art.
    Values are expected to be between 0 and 1.
    """
    ryb_matrix = [
        [1.0, 1.0, 0.0],
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
    ]
    
    # A simplified blend of RYB to RGB
    red = r - min(y, r) - min(b, r) + min(y, r, b)
    green = y - min(y, r) - min(y, b) + min(y, r, b)
    blue = b - min(b, r) - min(b, y) + min(y, r, b)
    
    # This is a very simple approximation.
    # A more accurate model is complex and relies on a cube mapping.
    # We will use the following blend as a conceptual model.
    r_out = r + 0.5 * y
    g_out = 0.5 * r + y + 0.5 * b
    b_out = 0.5 * y + b
    
    # Normalize values to 0-1 and convert to 0-255
    total = max(r_out, g_out, b_out, 1.0)
    r_out /= total
    g_out /= total
    b_out /= total

    return int(r_out * 255), int(g_out * 255), int(b_out * 255)

# --- Looping Functions for Each Model ---

def rgb_model_loop():
    print("Cycling through the RGB color model...")
    for i in range(256):
        set_rgb_color(i, 0, 0)
        time.sleep(0.005)
    for i in range(256):
        set_rgb_color(0, i, 0)
        time.sleep(0.005)
    for i in range(256):
        set_rgb_color(0, 0, i)
        time.sleep(0.005)
    print("RGB: Full spectrum loop")
    for i in range(256):
        set_rgb_color(255, i, 0)
        time.sleep(0.005)
    for i in range(255, -1, -1):
        set_rgb_color(i, 255, 0)
        time.sleep(0.005)
    for i in range(256):
        set_rgb_color(0, 255, i)
        time.sleep(0.005)

def hsv_model_loop():
    print("Cycling through the HSV color model...")
    print("HSV: Hue cycle with full Saturation and Value")
    for h in range(361): # Hue (0-360)
        r, g, b = hsv_to_rgb(h / 360.0, 1.0, 1.0)
        set_rgb_color(r, g, b)
        time.sleep(0.01)
    
    print("HSV: Saturation loop for a fixed Hue (Red)")
    for s in range(101): # Saturation (0-100)
        r, g, b = hsv_to_rgb(0, s / 100.0, 1.0)
        set_rgb_color(r, g, b)
        time.sleep(0.01)

    print("HSV: Value loop for a fixed Hue (Blue)")
    for v in range(101): # Value (0-100)
        r, g, b = hsv_to_rgb(240/360.0, 1.0, v / 100.0)
        set_rgb_color(r, g, b)
        time.sleep(0.01)

def hsl_model_loop():
    print("Cycling through the HSL color model...")
    print("HSL: Hue cycle with full Saturation and neutral Lightness")
    for h in range(361): # Hue (0-360)
        r, g, b = hsl_to_rgb(h / 360.0, 1.0, 0.5)
        set_rgb_color(r, g, b)
        time.sleep(0.01)

    print("HSL: Saturation loop for a fixed Hue (Green)")
    for s in range(101): # Saturation (0-100)
        r, g, b = hsl_to_rgb(120/360.0, s / 100.0, 0.5)
        set_rgb_color(r, g, b)
        time.sleep(0.01)
    
    print("HSL: Lightness loop for a fixed Hue (Yellow)")
    for l in range(101): # Lightness (0-100)
        r, g, b = hsl_to_rgb(60/360.0, 1.0, l / 100.0)
        set_rgb_color(r, g, b)
        time.sleep(0.01)

def cmyk_cmy_loop():
    print("Cycling through the CMY and CMYK color models...")
    print("CMY: Cyan to Magenta to Yellow loop")
    for i in range(256):
        c, m, y = i/255.0, 0, 0
        r, g, b = cmy_to_rgb(c, m, y)
        set_rgb_color(r, g, b)
        time.sleep(0.005)
    for i in range(256):
        c, m, y = 0, i/255.0, 0
        r, g, b = cmy_to_rgb(c, m, y)
        set_rgb_color(r, g, b)
        time.sleep(0.005)
    for i in range(256):
        c, m, y = 0, 0, i/255.0
        r, g, b = cmy_to_rgb(c, m, y)
        set_rgb_color(r, g, b)
        time.sleep(0.005)

    print("CMYK: Varying Black (K) value")
    for k in range(101): # Vary black ink from 0 to 100%
        c, m, y = 0.5, 0.5, 0.5 # A fixed CMY value
        r, g, b = cmyk_to_rgb(c, m, y, k / 100.0)
        set_rgb_color(r, g, b)
        time.sleep(0.01)

def xyz_cielab_loop():
    print("Cycling through the XYZ and CIELAB color models...")
    print("XYZ: Simple linear walk")
    for i in range(101):
        x, y, z = i/100.0, 0.5, 0.5
        r, g, b = xyz_to_rgb(x, y, z)
        set_rgb_color(r, g, b)
        time.sleep(0.01)

    print("CIELAB: Varying 'a' (Green to Red)")
    for a in range(-128, 128, 5):
        r, g, b = cielab_to_rgb(50, a, 0)
        set_rgb_color(r, g, b)
        time.sleep(0.05)

    print("CIELAB: Varying 'b' (Blue to Yellow)")
    for b in range(-128, 128, 5):
        r, g, b = cielab_to_rgb(50, 0, b)
        set_rgb_color(r, g, b)
        time.sleep(0.05)

def ryb_preucil_loop():
    print("Cycling through the RYB and Preucil models...")
    print("RYB: Primary and secondary color transition")
    # Red to Orange to Yellow
    for i in range(101):
        r, y, b = 1.0, i/100.0, 0
        r_out, g_out, b_out = ryb_to_rgb(r, y, b)
        set_rgb_color(r_out, g_out, b_out)
        time.sleep(0.01)
    
    # Yellow to Green
    for i in range(101):
        r, y, b = 0, 1.0, i/100.0
        r_out, g_out, b_out = ryb_to_rgb(r, y, b)
        set_rgb_color(r_out, g_out, b_out)
        time.sleep(0.01)

    print("Preucil Hue Circle: Conceptual walk")
    # This is a conceptual representation as the Preucil circle
    # is a specific, subtractive model for printing.
    # We will simulate a smooth transition through its major hues.
    hues = [(1.0, 0.0, 0.0), # Red
            (1.0, 0.5, 0.0), # Orange
            (1.0, 1.0, 0.0), # Yellow
            (0.0, 1.0, 0.0), # Green
            (0.0, 0.0, 1.0), # Blue
            (0.5, 0.0, 1.0)] # Violet
    
    for i in range(len(hues)):
        current = hues[i]
        next = hues[(i+1)%len(hues)]
        for j in range(101):
            r = current[0] + (next[0] - current[0]) * j/100.0
            g = current[1] + (next[1] - current[1]) * j/100.0
            b = current[2] + (next[2] - current[2]) * j/100.0
            set_rgb_color(int(r*255), int(g*255), int(b*255))
            time.sleep(0.01)

def ciecamo2_loop():
    print("Demonstrating a conceptual CIECAM02 loop...")
    # CIECAM02 is a perceptual model, so a direct mathematical loop is not practical.
    # This loop simulates the effect of changing "lightness" and "chroma"
    # on a specific hue, which is a core concept of CIECAM02.
    # We will use Red as our base hue.
    
    print("CIECAM02: Varying Chroma for Red")
    for c in range(0, 256, 16):
        # A simple approximation: increase red while desaturating other colors
        r = 255
        g = 255 - c
        b = 255 - c
        set_rgb_color(r, g, b)
        time.sleep(0.02)
    
    print("CIECAM02: Varying Lightness for Red")
    for l in range(0, 256, 16):
        # A simple approximation: increase lightness of a base red
        set_rgb_color(l, 0, 0)
        time.sleep(0.02)

def main():
    """
    The main function that orchestrates the color model demonstrations.
    """
    while True:
        rgb_model_loop()
        time.sleep(2)
        
        hsv_model_loop()
        time.sleep(2)
        
        hsl_model_loop()
        time.sleep(2)
        
        cmyk_cmy_loop()
        time.sleep(2)
        
        xyz_cielab_loop()
        time.sleep(2)
        
        ryb_preucil_loop()
        time.sleep(2)
        
        ciecamo2_loop()
        time.sleep(2)
        
if __name__ == "__main__":
    main()
