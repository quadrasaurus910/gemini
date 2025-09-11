import time
import math
from machine import Pin

# Standard D65 white point reference values
D65_X = 95.047
D65_Y = 100.000
D65_Z = 108.883

# Assume the RGB LED is connected to GPIO pins.
# Update these pin numbers to match your Pico 2 setup.
# pin_R = Pin(16, Pin.OUT)
# pin_G = Pin(17, Pin.OUT)
# pin_B = Pin(18, Pin.OUT)

# pwm_R = PWM(pin_R)
# pwm_G = PWM(pin_G)
# pwm_B = PWM(pin_B)

# Set the PWM frequency
# pwm_R.freq(1000)
# pwm_G.freq(1000)
# pwm_B.freq(1000)

def rgb_to_xyz(r, g, b):
    # Convert 8-bit RGB (0-255) to linear RGB (0-1)
    r_linear = r / 255.0
    g_linear = g / 255.0
    b_linear = b / 255.0

    # Apply sRGB gamma correction
    r_linear = ((r_linear + 0.055) / 1.055) ** 2.4 if r_linear > 0.04045 else r_linear / 12.92
    g_linear = ((g_linear + 0.055) / 1.055) ** 2.4 if g_linear > 0.04045 else g_linear / 12.92
    b_linear = ((b_linear + 0.055) / 1.055) ** 2.4 if b_linear > 0.04045 else b_linear / 12.92

    # Convert to XYZ
    x = r_linear * 0.4124 + g_linear * 0.3576 + b_linear * 0.1805
    y = r_linear * 0.2126 + g_linear * 0.7152 + b_linear * 0.0722
    z = r_linear * 0.0193 + g_linear * 0.1192 + b_linear * 0.9505

    return x * 100.0, y * 100.0, z * 100.0

def xyz_to_lab(x, y, z):
    # Normalize to white point
    x /= D65_X
    y /= D65_Y
    z /= D65_Z

    # Apply function to handle small values
    f = lambda t: t**(1.0/3.0) if t > 0.008856 else (7.787 * t) + (16.0 / 116.0)

    # Convert to L*a*b*
    l = (116.0 * f(y)) - 16.0
    a = 500.0 * (f(x) - f(y))
    b = 200.0 * (f(y) - f(z))

    return l, a, b

def lab_to_xyz(l, a, b):
    # Invert the conversion from xyz_to_lab
    fy = (l + 16.0) / 116.0
    fx = (a / 500.0) + fy
    fz = fy - (b / 200.0)

    # Apply inverse function
    f_inv = lambda t: t**3 if t**3 > 0.008856 else (t - 16.0 / 116.0) / 7.787

    # Convert back to XYZ
    x = D65_X * f_inv(fx)
    y = D65_Y * f_inv(fy)
    z = D65_Z * f_inv(fz)

    return x, y, z

def xyz_to_rgb(x, y, z):
    # Normalize XYZ values
    x /= 100.0
    y /= 100.0
    z /= 100.0

    # Convert to linear RGB
    r_linear = x * 3.2406 + y * -1.5372 + z * -0.4986
    g_linear = x * -0.9689 + y * 1.8758 + z * 0.0415
    b_linear = x * 0.0557 + y * -0.2040 + z * 1.0570

    # Apply inverse sRGB gamma correction
    r = (1.055 * r_linear**(1.0/2.4) - 0.055) if r_linear > 0.0031308 else r_linear * 12.92
    g = (1.055 * g_linear**(1.0/2.4) - 0.055) if g_linear > 0.0031308 else g_linear * 12.92
    b = (1.055 * b_linear**(1.0/2.4) - 0.055) if b_linear > 0.0031308 else b_linear * 12.92

    # Clamp and convert to 8-bit
    r = max(0, min(255, int(r * 255.0)))
    g = max(0, min(255, int(g * 255.0)))
    b = max(0, min(255, int(b * 255.0)))

    return r, g, b

# Main loop to demonstrate the smooth gradient
# Make sure to initialize the PWM objects for your LED first!
def create_smooth_gradient(start_rgb, end_rgb, n_steps=200, delay_ms=10):
    """
    Creates a smooth color gradient animation.
    
    Args:
        start_rgb (tuple): The starting color in (R, G, B) format.
        end_rgb (tuple): The ending color in (R, G, B) format.
        n_steps (int): The number of steps in the gradient.
        delay_ms (int): The delay in milliseconds between each step.
    """
    
    # 1. Convert start and end colors to CIELAB
    start_xyz = rgb_to_xyz(*start_rgb)
    start_lab = xyz_to_lab(*start_xyz)

    end_xyz = rgb_to_xyz(*end_rgb)
    end_lab = xyz_to_lab(*end_xyz)

    # 2. Calculate step size for each channel
    step_l = (end_lab[0] - start_lab[0]) / n_steps
    step_a = (end_lab[1] - start_lab[1]) / n_steps
    step_b = (end_lab[2] - start_lab[2]) / n_steps

    # 3. Loop and interpolate
    for i in range(n_steps + 1):
        # Linearly interpolate in CIELAB space
        current_l = start_lab[0] + step_l * i
        current_a = start_lab[1] + step_a * i
        current_b = start_lab[2] + step_b * i

        # 4. Convert back to RGB and update LED
        current_xyz = lab_to_xyz(current_l, current_a, current_b)
        current_rgb = xyz_to_rgb(*current_xyz)

        r, g, b = current_rgb
        
        # Uncomment and adapt these lines to control your specific LED
        # pwm_R.duty_u16(int(r/255 * 65535))
        # pwm_G.duty_u16(int(g/255 * 65535))
        # pwm_B.duty_u16(int(b/255 * 65535))
        
        # Optional: Print values for debugging
        print(f"Step {i+1}/{n_steps+1}: RGB({r}, {g}, {b})")

        time.sleep_ms(delay_ms)

# Example usage
# Define your start and end colors in 8-bit RGB
start_color = (255, 0, 0)  # Bright Red
end_color = (0, 0, 255)    # Bright Blue

create_smooth_gradient(start_color, end_color)
