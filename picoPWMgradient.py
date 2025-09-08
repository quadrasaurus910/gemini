import machine
import time

# Pin definitions for common anode RGB LED
RED_PIN = 16
GREEN_PIN = 17
BLUE_PIN = 18

# Create PWM objects for each color
pwm_red = machine.PWM(machine.Pin(RED_PIN))
pwm_green = machine.PWM(machine.Pin(GREEN_PIN))
pwm_blue = machine.PWM(machine.Pin(BLUE_PIN))

# Set the PWM frequency
frequency = 1000  # Hz
pwm_red.freq(frequency)
pwm_green.freq(frequency)
pwm_blue.freq(frequency)

def set_color(r_val, g_val, b_val):
    """
    Sets the duty cycle for each color.
    For common anode, a higher value means dimmer.
    """
    # Invert the values because 0 is on and 65535 is off for common anode
    pwm_red.duty_u16(65535 - r_val)
    pwm_green.duty_u16(65535 - g_val)
    pwm_blue.duty_u16(65535 - b_val)

def lerp(start, end, progress):
    """
    Linear interpolation function to calculate intermediate values.
    """
    return int(start + (end - start) * progress)

def color_transition(start_rgb, end_rgb, duration_ms):
    """
    Transitions the LED color smoothly from start_rgb to end_rgb.
    start_rgb and end_rgb are tuples of (R, G, B) values (0-65535).
    """
    steps = 100  # Number of steps in the transition
    delay_ms = duration_ms / steps
    
    start_r, start_g, start_b = start_rgb
    end_r, end_g, end_b = end_rgb

    for i in range(steps + 1):
        progress = i / steps
        r = lerp(start_r, end_r, progress)
        g = lerp(start_g, end_g, progress)
        b = lerp(start_b, end_b, progress)
        
        set_color(r, g, b)
        time.sleep_ms(int(delay_ms))
        
    print(f"Transition complete: {start_rgb} -> {end_rgb}")

# --- Main loop to demonstrate the gradient effect ---
try:
    while True:
        # Example 1: Transition from Red to Blue
        print("Transitioning from Red to Blue...")
        color_transition((65535, 0, 0), (0, 0, 65535), 2000) # 2-second transition

        # Example 2: Transition from Blue to Green
        print("Transitioning from Blue to Green...")
        color_transition((0, 0, 65535), (0, 65535, 0), 2000)

        # Example 3: Transition from Green to Yellow
        print("Transitioning from Green to Yellow...")
        color_transition((0, 65535, 0), (65535, 65535, 0), 2000)

        # Pause before repeating
        time.sleep(1)

except KeyboardInterrupt:
    print("Gradient effect stopped.")
finally:
    # Clean up by turning off all LEDs
    set_color(0, 0, 0)
    pwm_red.deinit()
    pwm_green.deinit()
    pwm_blue.deinit()

